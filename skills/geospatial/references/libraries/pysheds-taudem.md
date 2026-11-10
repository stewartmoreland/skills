# PySheds And TauDEM

Authority for hydrologic terrain analysis: DEM conditioning, flow routing, accumulation, pour-point snapping, watershed/subcatchment delineation, stream-network extraction and ordering, and the derived terrain metrics that feed StormwaterIQ runoff and compliance workflows.

## Contents

1. When to use
2. Tool selection: PySheds vs TauDEM (vs others)
3. Canonical data model
4. CRS, units, precision for hydrology
5. DEM conditioning (the part most delineation bugs live in)
6. Flow direction (D8, D-infinity, MFD) and the dirmap trap
7. Flow accumulation (uniform and weighted)
8. Pour-point snapping (the #1 source of wrong watersheds)
9. Watershed and subcatchment delineation — PySheds
10. Stream network extraction and ordering
11. Other pertinent hydrology (HAND, TWI, flow distance, longest flow path, slope, drainage density)
12. Stormwater synthesis: terrain to peak flow
13. TauDEM command reference and end-to-end pipeline
14. Performance, scaling, and MPI
15. Return contract
16. Known gotchas
17. Integration with StormwaterIQ
18. Validation checklist
19. References

---

## 1. When to use

Use whenever a task involves conditioning a DEM, deriving flow direction or accumulation, snapping outlets, delineating a watershed or nested subcatchments, extracting or ordering a stream network, computing height above nearest drainage (HAND) for inundation, topographic wetness index (TWI), flow distance / time-of-concentration inputs, or scaling any of the above to large grids with MPI.

Upstream of this reference, source and condition the DEM via `data-sources/usgs-3dep.md` and `libraries/gdal-rasterio.md`. Downstream, persist vector results via `postgis-data-model.md` and join terrain to land cover / soils / rainfall via `data-sources/mrlc-nlcd.md`, `data-sources/nrcs-ssurgo.md`, and `data-sources/noaa-atlas14.md`.

## 2. Tool selection: PySheds vs TauDEM (vs others)

These tools overlap but are not interchangeable. Pick deliberately and record the choice in provenance.

| Dimension | PySheds | TauDEM |
|-----------|---------|--------|
| Execution model | In-process Python, single machine, Numba-accelerated | Standalone MPI executables (`mpiexec -n N ...`) |
| Best at | Interactive single-outlet delineation, HAND, fast iteration inside a worker | Large grids, full stream-network topology, subwatershed-per-reach, objective thresholds |
| Routing | D8, D-infinity, MFD | D8, D-infinity (with slope outputs) |
| Stream network output | GeoJSON line features (`extract_river_network`) | `streamnet` with Strahler order, drainage area, length, slope, topology (`tree.dat`/`coord.dat`), plus per-reach watershed grid |
| Objective stream threshold | Manual / accumulation-percentile | `dropanalysis` (constant drop statistic) and Peuker-Douglas |
| Multiple outlets / nested basins | Loop `catchment` per outlet | `gagewatershed` (one labeled basin per outlet) or `streamnet -w` |
| Conditioning | `fill_pits`, `fill_depressions`, `resolve_flats` (fill only) | `pitremove` (flooding), plus `-4way` and depression-mask options |
| Scaling ceiling | Tens of millions of cells per machine, RAM-bound | Cluster-scale via MPI; designed for very large DEMs |
| Operational fit | Default for StormwaterIQ per-site requests | Fallback for regional/batch jobs or when full network topology is required |

Decision rule for StormwaterIQ: default to **PySheds** for a single site / single outlet within the interactive runtime envelope (see §14). Escalate to **TauDEM** when the grid is too large for the envelope, when you need per-reach subwatersheds and stream attributes, or when you need an objective channel-initiation threshold rather than a hand-picked one.

Honorable mentions (do not add as dependencies without a reason): **WhiteboxTools** and **RichDEM** provide depression *breaching* (carving) as an alternative to filling, which PySheds does not offer. If filling distorts a low-relief urban DEM unacceptably, breaching is the principled alternative — note it explicitly rather than silently switching tools.

## 3. Canonical data model

```ts
type Routing = "D8" | "DINF" | "MFD";

type WatershedDelineation = {
  sourceDem: string;                 // URL or artifact ID of the input DEM
  routing: Routing;
  conditioning: Array<"fill_pits" | "fill_depressions" | "resolve_flats" | "pitremove" | "breach">;
  streamThreshold: { value: number; unit: "cells" | "square_meters"; method: "constant" | "drop_analysis" | "peuker_douglas" | "percentile" };
  originalPourPoint: { x: number; y: number; crs: string };
  snappedPourPoint: { x: number; y: number; crs: string; snapDistanceM?: number };
  catchment: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>;
  areaSqM: number;
  derivatives?: {
    streamNetwork?: GeoJSON.FeatureCollection<GeoJSON.LineString>;
    strahlerMaxOrder?: number;
    handRaster?: string;
    twiRaster?: string;
    longestFlowPathM?: number;
    timeOfConcentrationMin?: number;
  };
  intermediates: {
    pitFilledDem?: string;
    depressionFilledDem?: string;
    flatResolvedDem?: string;
    flowDirection?: string;
    accumulation?: string;
  };
};
```

## 4. CRS, units, precision for hydrology

Read `crs-and-units.md` first. The hydrology-specific rules:

- **Run conditioning and routing in the DEM's native raster grid.** Reprojecting a DEM before flow analysis resamples elevations and can introduce artificial pits/flats. Condition first, transform vector outputs after.
- **Area and length must come from a projected (equal-area or local) CRS.** Cell counts are unitless; multiply by true cell area. A DEM in a geographic CRS (`EPSG:4269`/`4326`) has cells whose ground area varies with latitude — do **not** assume a constant cell area there. Either reproject to an appropriate projected CRS before measuring, or use TauDEM's geographic-coordinate support / `grid.cell_area` which accounts for the affine, and document which path you took.
- **Vertical units matter.** 3DEP rasters are typically meters; engineering exhibits may want feet. Keep meters internally; convert only at presentation. Never mix vertical-unit assumptions across conditioning and slope.
- **Output catchments transform to `EPSG:4326`** for platform storage, with the source DEM CRS retained in provenance.
- **Parity target:** delineated area and derived peak flow that mirror hand calculations should stay within +/-2% unless a product requirement says otherwise.

## 5. DEM conditioning (the part most delineation bugs live in)

A raw DEM has three artifacts that break routing. Treat them as distinct problems, applied in order:

1. **Pits** — single cells lower than all neighbors. Cheap to fix. `fill_pits`.
2. **Depressions** — multi-cell sinks with no outlet. More expensive. `fill_depressions`.
3. **Flats** — regions with no gradient (filled areas, lakes) where flow direction is undefined. `resolve_flats` imposes a drainable gradient (Garbrecht & Martz).

The correct PySheds order is **`fill_pits` -> `fill_depressions` -> `resolve_flats`**, then routing. Skipping `resolve_flats` after filling is the classic mistake: filled depressions become flats, and flow direction over a flat is undefined, producing parallel "rake" artifacts in accumulation.

```python
from pysheds.grid import Grid
import numpy as np

grid = Grid.from_raster("dem.tif")
dem = grid.read_raster("dem.tif")

pit_filled = grid.fill_pits(dem)
depression_filled = grid.fill_depressions(pit_filled)
inflated_dem = grid.resolve_flats(depression_filled)

# Verify conditioning actually worked before trusting downstream results.
assert not grid.detect_pits(inflated_dem).any(), "pits remain after conditioning"
assert not grid.detect_depressions(inflated_dem).any(), "depressions remain after conditioning"
assert not grid.detect_flats(inflated_dem).any(), "flats remain after conditioning"
```

> Callout — fill vs breach: PySheds and TauDEM `pitremove` both *fill* (raise sink cells). In flat urban terrain, filling can create long artificial flats and push drainage divides off real culverts/storm drains. If filling visibly distorts drainage, breaching (carving a path through the obstruction, via WhiteboxTools/RichDEM) is the principled alternative. Choose deliberately and record it in `conditioning`.

> Callout — stream burning: "Burning" a known stream/storm-drain vector into the DEM (lowering elevations along it) can force routing to match a published network. It is powerful and dangerous — an inaccurate burn line produces a confidently wrong watershed. Only burn from an authoritative hydrography layer (e.g., NHD via `data-sources/epa-waters-attains.md`), keep the burn magnitude documented, and never burn silently.

Preserve `nodata` and the validity mask through every conditioning step (see `mask-conventions.md`). Do not let nodata be treated as real elevation; it will swallow flow.

> TauDEM conditioning options: `pitremove` fills (with `-4way` and depression-mask variants). `FlowDirCond` (CLI, since v5.3.7) instead conditions by enforcing flow directions from a supplied hydro grid — useful when you have an authoritative drainage layer and want to honor it without bulk-filling. As with burning, only use an authoritative source and record it.

## 6. Flow direction (D8, D-infinity, MFD) and the dirmap trap

```python
# ESRI/pysheds default dirmap, clockwise from North:
#        N    NE   E   SE   S   SW   W   NW
dirmap = (64, 128,  1,   2,  4,   8, 16, 32)

fdir_d8   = grid.flowdir(inflated_dem, dirmap=dirmap, routing="d8")    # integer codes
fdir_dinf = grid.flowdir(inflated_dem, routing="dinf")                 # float radians, E=0 CCW
```

- **D8** routes all flow to the single steepest downslope neighbor. Deterministic, simple to validate, the right default for catchment delineation and crisp drainage divides. Tends to produce parallel flow lines on planar hillslopes.
- **D-infinity** apportions flow between the two downslope neighbors bracketing the steepest descent direction. Better for divergent/dispersive flow and specific-catchment-area work (TWI). Outputs a continuous angle, not a code, so `accumulation`/`catchment` must be called with `routing="dinf"` and the matching `fdir`.
- **MFD** (multiple flow direction) spreads flow to all downslope neighbors; useful for diffuse hillslope processes, rarely needed for compliance delineation.

The **dirmap trap:** the integer codes are a convention, not a law. PySheds defaults to the ESRI scheme above, but rasters produced elsewhere (GRASS, some TauDEM intermediates) use different encodings. If you read a pre-computed flow-direction raster, pass the dirmap that *produced* it — a mismatched dirmap silently routes flow in wrong directions. When in doubt, recompute flow direction from the conditioned DEM rather than trusting an external code grid.

## 7. Flow accumulation (uniform and weighted)

```python
acc = grid.accumulation(fdir_d8, dirmap=dirmap, routing="d8")   # upstream cell count per cell
```

Uniform accumulation counts upstream cells. Multiply by true cell area for contributing area (mind §4 CRS rules).

**Weighted accumulation** routes a per-cell quantity instead of a unit count — the lever for stormwater realism:

```python
# Example: accumulate effective impervious contribution rather than raw cell count.
# weights is a Raster aligned to the grid (e.g., NLCD percent-impervious / 100).
acc_imperv = grid.accumulation(fdir_d8, weights=impervious_fraction, dirmap=dirmap, routing="d8")
```

Use weights to accumulate rainfall excess, impervious fraction, or runoff coefficients so downstream accumulation reflects generated runoff, not just drainage area. Always declare the weight's units in the envelope.

## 8. Pour-point snapping (the #1 source of wrong watersheds)

A pour point clicked from a map almost never lands exactly on the modeled channel cell. Delineating from an off-channel cell returns a tiny sliver or a hillslope fragment. Snap to a high-accumulation cell first, and **report both the original and snapped location plus the snap distance** so reviewers can catch a bad snap.

```python
x, y = -97.294, 32.737            # outlet in DEM coordinate CRS
stream_threshold = 1000           # cells; tune per §10

x_snap, y_snap = grid.snap_to_mask(acc > stream_threshold, (x, y))
snap_dist_m = ((x_snap - x) ** 2 + (y_snap - y) ** 2) ** 0.5   # only meaningful in a projected CRS
```

Snap-distance guardrail: if the snap distance exceeds a few cell widths, the outlet was probably digitized far from any real channel, or the threshold is wrong. Surface this rather than silently delineating. TauDEM's equivalent is `moveoutletstostrm` with a `-md` maximum-distance limit (§13).

## 9. Watershed and subcatchment delineation — PySheds

Single outlet, current (functional) API:

```python
catch = grid.catchment(
    x=x_snap, y=y_snap, fdir=fdir_d8,
    dirmap=dirmap, routing="d8", xytype="coordinate",
)

grid.clip_to(catch)                       # crop the viewfinder to the catchment
catch_view = grid.view(catch, nodata=np.nan)

# Vectorize the catchment boundary to GeoJSON-ready polygons.
shapes = grid.polygonize()                # yields (geometry, value) using the current mask
area_sq_m = float(grid.cell_area[catch].sum())   # projected CRS assumed; see §4
```

> API-generation warning: most blog/tutorial code online uses the **older stateful** PySheds API (`grid.flowdir(data='dem', out_name='dir', ...)`, `recursionlimit=`, `grid.view('name')`). The current API is **functional** — methods take and return `Raster` objects, as above. Do not mix the two; `out_name=` will fail on current versions.

Nested subcatchments (one polygon per outlet, e.g., per inlet or per monitoring point):

```python
subcatchments = []
for oid, (ox, oy) in enumerate(outlets_in_dem_crs):
    sx, sy = grid.snap_to_mask(acc > stream_threshold, (ox, oy))
    c = grid.catchment(x=sx, y=sy, fdir=fdir_d8, dirmap=dirmap, routing="d8", xytype="coordinate")
    grid.clip_to(c)
    for geom, _ in grid.polygonize():
        subcatchments.append({"outlet_id": oid, "geometry": geom})
    grid.viewfinder = dem.viewfinder       # reset the viewfinder before the next outlet
```

For many outlets or true topological nesting (each reach's incremental drainage), prefer TauDEM `gagewatershed` or `streamnet -w` (§13) — looping `catchment` recomputes overlapping areas and does not give incremental subwatersheds.

## 10. Stream network extraction and ordering

PySheds extracts channel lines wherever accumulation exceeds the channel-initiation threshold:

```python
branches = grid.extract_river_network(fdir_d8, acc > stream_threshold, dirmap=dirmap, routing="d8")
# branches is a GeoJSON FeatureCollection of LineString reaches.
```

**Choosing the threshold** is a real modeling decision, not a magic number. Options, in increasing rigor:

- **Constant cell count** (e.g., `acc > 1000`): fast, defensible for consistent terrain, but drainage density then depends on cell size and relief.
- **Accumulation percentile**: threshold at a percentile of the accumulation distribution to normalize across DEMs.
- **Objective drop analysis** (TauDEM `dropanalysis`): selects the smallest threshold for which the constant-drop statistical test still holds, i.e., the finest network that is statistically channel-like. This is the defensible method when the network feeds compliance work.

**Strahler ordering** and per-reach attributes (drainage area, length, slope, upstream/downstream topology) come from TauDEM `streamnet`, which writes them to the output network shapefile and `tree.dat`/`coord.dat`. PySheds gives you the geometry; TauDEM gives you the ordered, attributed, topologically connected network.

## 11. Other pertinent hydrology

### Height Above Nearest Drainage (HAND) — inundation and wet-area mapping

HAND is the vertical drop from each cell to the channel cell it drains to. It is the backbone of fast inundation mapping and riparian/wet-area delineation.

```python
channel_mask = acc > 200
hand = grid.compute_hand(fdir_d8, inflated_dem, channel_mask)     # meters above nearest drainage
# Inundation at a given stage: cells whose HAND is below the stage height are "wet".
inundated = (hand < stage_height_m)
```

HAND gives a binary wet/dry surface at a stage. For an inundation **depth** raster (depth of water per cell, not just extent), TauDEM's `InunDepth` (renamed from `InunMap` in v5.4.0) computes depths from HAND/catchment inputs directly — prefer it when the deliverable is a depth grid rather than a wet mask, and pair it with `CatchHydroGeo` for per-catchment stage/area/volume attributes.

### Topographic Wetness Index (TWI)

TWI = ln(a / tan(beta)), where `a` is specific catchment area (upslope area per unit contour width) and `beta` is local slope. PySheds has no single TWI call; compute it as raster algebra (see `libraries/numpy-scipy.md`):

```python
import numpy as np

cell = abs(grid.affine.a)                       # cell width (projected CRS units)
spec_catch_area = (np.asarray(acc) + 1) * cell  # a = upslope cells * cell_area / contour width ~= acc * cell

# Local slope from the conditioned DEM (downslope gradient); guard against zero slope.
gy, gx = np.gradient(np.asarray(inflated_dem), cell, cell)
slope = np.sqrt(gx ** 2 + gy ** 2)
slope = np.where(slope <= 0, 1e-4, slope)

twi = np.log(spec_catch_area / slope)
```

(PySheds also exposes `grid.cell_slopes(...)` for a flow-direction-aligned gradient; the numpy form above is library-agnostic and explicit about cell size.)

### Flow distance, longest flow path, time-of-concentration inputs

```python
dist = grid.distance_to_outlet(
    x=x_snap, y=y_snap, fdir=fdir_d8,
    dirmap=dirmap, routing="d8", xytype="coordinate",
)
longest_flow_path_m = float(np.nanmax(grid.view(dist, nodata=np.nan)))
```

`distance_to_outlet` accepts a `weights` raster, so you can weight by channel-vs-overland travel (e.g., faster routing where accumulation is high) to approximate travel time rather than pure geometric distance — useful scaffolding for time of concentration.

### Slope and drainage density

Slope drives runoff velocity and erosion potential; compute from the conditioned DEM (numpy gradient above) or `grid.cell_slopes`. Drainage density = total channel length / catchment area, computed from the extracted network and the delineated catchment; report it as a sanity check on threshold choice.

## 12. Stormwater synthesis: terrain to peak flow

Terrain analysis is the front of a chain, not the deliverable. For StormwaterIQ the typical flow is:

1. **Contributing area** — delineate catchment (§9), area in a projected CRS (§4).
2. **Land cover** — overlay NLCD for impervious fraction / runoff coefficient / curve number (`data-sources/mrlc-nlcd.md`).
3. **Soils** — overlay SSURGO hydrologic soil group and Ksat (`data-sources/nrcs-ssurgo.md`).
4. **Rainfall** — pull design-storm depth/intensity for the recurrence interval from NOAA Atlas 14 (`data-sources/noaa-atlas14.md`).
5. **Timing** — longest flow path + channel slope (§11) -> time of concentration.
6. **Peak flow** — Rational Method (Q = CiA) for small urban catchments, or an NRCS/TR-55 curve-number approach for larger/mixed land cover.

> Callout — method, not magic: the chain above is scaffolding. Curve numbers, Rational-Method C values, and Tc formulas are governed by the applicable engineering standard and local jurisdiction. Surface the assumptions, keep unit conversions explicit (CFS vs m3/s, inches vs mm — see `crs-and-units.md`), and hold to the +/-2% parity target against hand calculations. Never tune thresholds or coefficients toward a desired result; optimize for accuracy and an auditable trail.

## 13. TauDEM command reference and end-to-end pipeline

TauDEM ships as MPI executables invoked as `mpiexec -n <processes> <Tool> <flags>`. Treat filenames and suffixes as part of the contract; downstream tools consume specific outputs.

| Step | Tool | Key flags | Produces |
|------|------|-----------|----------|
| Pit/depression removal (flooding) | `pitremove` | `-z dem` `-fel demfel` `[-4way]` `[-depmask]` | filled elevation `-fel` |
| D8 flow direction + slope | `d8flowdir` | `-fel demfel` `-p demp` `-sd8 demsd8` | direction `-p`, slope `-sd8` |
| D-infinity flow direction + slope | `dinfflowdir` | `-fel demfel` `-ang demang` `-slp demslp` | angle `-ang`, slope `-slp` |
| D8 contributing area | `aread8` | `-p demp` `-ad8 demad8` `[-nc]` `[-o outlets]` `[-wg weight]` | accumulation `-ad8` |
| D-infinity contributing area | `areadinf` | `-ang demang` `-sca demsca` `[-nc]` | specific catchment area `-sca` |
| Grid network / lengths / order | `gridnet` | `-p demp` `-plen` `-tlen` `-gord` | path/total length, grid order |
| Peuker-Douglas valley cells | `peukerdouglas` | `-fel demfel` `-ss demss` `[-par]` | smoothed source candidates |
| Objective threshold selection | `dropanalysis` | `-p -fel -ad8 -ssa -drp drp.txt -o outlets -par 5 500 10 0` | drop statistic table |
| Stream raster by threshold | `threshold` | `-ssa demad8` `-src demsrc` `-thresh 1000` | stream raster `-src` |
| Snap outlets to streams | `moveoutletstostrm` | `-p demp` `-src demsrc` `-o outlets` `-om moved` `[-md maxdist]` | moved outlets |
| Stream network + subwatersheds | `streamnet` | `-fel -p -ad8 -src -ord -tree tree.dat -coord coord.dat -net net.shp -w w.tif [-o outlets]` | ordered network, topology, per-reach watershed grid |
| Watershed per outlet/gage | `gagewatershed` | `-p demp` `-o outlets` `-gw gw.tif` `-id id.txt` | labeled watershed grid |
| Inundation depth (HAND-based) | `inundepth` | catchment + HAND + flow inputs (see tool docs) | inundation-depth raster |
| Per-catchment hydro/geo attributes | `catchhydrogeo` | `catchlistfile` CSV of outlets/catchments | catchment attribute table |
| Flow-direction conditioning (alt. to filling) | `flowdircond` | enforce flow directions from a hydro-conditioning grid | conditioned flow direction |

Canonical end-to-end (D8, single set of outlets), suitable for a containerized worker:

```bash
NP=8   # MPI processes; see §14

mpiexec -n $NP pitremove   -z dem.tif -fel demfel.tif
mpiexec -n $NP d8flowdir   -fel demfel.tif -p demp.tif -sd8 demsd8.tif
mpiexec -n $NP aread8      -p demp.tif -ad8 demad8.tif            # add -nc for clipped/edge DEMs
mpiexec -n $NP threshold   -ssa demad8.tif -src demsrc.tif -thresh 1000
mpiexec -n $NP moveoutletstostrm -p demp.tif -src demsrc.tif -o outlets.shp -om outlets_moved.shp -md 50
mpiexec -n $NP streamnet   -fel demfel.tif -p demp.tif -ad8 demad8.tif -src demsrc.tif \
                           -ord demord.tif -tree tree.dat -coord coord.dat \
                           -net net.shp -w demw.tif -o outlets_moved.shp
```

- `-nc` ("no edge contamination check") disables the default flag that marks contributing areas potentially affected by the DEM edge. Leave the check **on** unless you have a deliberate reason; an edge-contaminated area is silently too small.
- For an objective channel threshold, run `peukerdouglas` -> `aread8` (weighted by the source grid) -> `dropanalysis`, then feed the chosen value to `threshold`.
- Record TauDEM version, process count, every tool invocation, and all filenames in provenance — the suffixes ARE the data lineage.
- Run TauDEM via the maintained Docker image (multi-stage build as of v5.5.0) or the conda bundle (which now ships GDAL CLI tools) for reproducible GDAL/MPI versions; pin the image tag.

> Version note: the latest tagged release is **v5.5.0 (2026-05-23)**, preceded by **v5.4.0** (uses current GDAL/MPI; renamed `InunMap` to `InunDepth` for inundation-depth rasters; `CatchHydroGeo` takes a CSV `catchlistfile`; first Dockerfile + CI). v5.5.0 is mostly packaging/robustness: multi-stage Docker build, GDAL CLI tools in the conda bundle, better argument checking/error handling, ArcGIS tooling for `CatchHydroGeo`/`InunDepth`, Windows silent installs, and a `GDALGetRasterUnitType` band-vs-dataset bugfix. No new core routing algorithms in 5.5.0. Pin and record the exact version your worker image contains.

## 14. Performance, scaling, and MPI

- **PySheds envelope:** flow direction over ~10M cells in a few seconds; accumulation over tens of millions in tens of seconds; RAM-bound on one machine. Product target is roughly 10 seconds for catchments up to ~10 sq mi. Measure against this; if a request blows the envelope, tile or escalate to TauDEM.
- **When PySheds stalls:** clip the DEM to a generous bounding box around the outlet before conditioning (read a window via `libraries/gdal-rasterio.md`), rather than conditioning a continental DEM to delineate one site.
- **TauDEM MPI:** scales across cores/nodes. Match `-n` to available physical cores; oversubscribing past core count usually hurts. Very large grids benefit from more processes, but IO and the edge-contamination passes set a floor on runtime.
- **Reproducibility:** pin DEM source/version, tool versions, process count, threshold, and routing. Two "correct" runs with different thresholds produce different networks — the parameters are part of the result.

## 15. Return contract

Hydrology results are the strictest artifact class in `return-contract.md`: return all spatial metadata **plus** the method. Specifically:

- Original and snapped pour points (with CRS and snap distance), routing algorithm, conditioning steps applied, stream threshold value/unit/method.
- Catchment geometry (`EPSG:4326` for storage) and area with explicit unit, computed in a documented projected CRS.
- DEM source URL/version, transform, nodata, mask semantics, vertical unit.
- Any derivative artifacts (stream network, HAND, TWI) as their own enveloped outputs, not bare rasters.
- Provenance `processingSteps` listing each conditioning and routing operation in order, plus tool + version (PySheds version or TauDEM version + MPI process count).

API callers receive catchment geometry plus the metadata envelope — not raw intermediate rasters, unless explicitly debugging.

## 16. Known gotchas

- Conditioning order is `fill_pits` -> `fill_depressions` -> `resolve_flats`; skipping flat resolution after filling yields rake-pattern accumulation artifacts.
- PySheds has two API generations. Tutorial code with `out_name=`/`recursionlimit=`/`grid.view('name')` is the **old stateful** API and will not run on current functional versions. Match the installed version.
- A mismatched `dirmap` on a pre-computed direction raster routes flow wrongly with no error. Recompute from the conditioned DEM when unsure.
- Cell counts are unitless. Area/length in a geographic CRS is **not** a constant per cell; reproject or use affine-aware area, and document it.
- Outlets must snap to the channel before delineation; report original, snapped, and distance. A large snap distance means a bad outlet or wrong threshold.
- TauDEM `-nc` silently shrinks edge-affected areas; keep edge-contamination checking on by default.
- Filling distorts low-relief urban DEMs; consider breaching (WhiteboxTools/RichDEM) and never stream-burn from a non-authoritative line.
- Stream threshold is a modeling choice that sets drainage density; prefer drop analysis when results feed compliance.
- nodata is not elevation. If nodata leaks into conditioning it swallows flow and corrupts the watershed.
- D-infinity `accumulation`/`catchment` must use a `fdir` computed with `routing="dinf"`; passing a D8 code grid produces garbage.

## 17. Integration with StormwaterIQ

Hydrology preparation belongs in `services/terrain-worker`: DEM windowing, conditioning, routing, delineation, and derivative rasters. Derived catchments and subcatchments persist as tenant-scoped PostGIS vectors (`subcatchments`, related to `sites`) per `postgis-data-model.md`; source DEMs and intermediate rasters stay in object storage / external COG URLs with provenance, not in the database unless a migration explicitly imports them. Stream networks persist as line tables with Strahler order and per-reach attributes when produced by TauDEM. Keep raw terrain inputs and validated outputs separated by the platform's audit and tenant-boundary rules; optimize for accuracy, consensus, and validated outcomes — never for "more issues found."

## 18. Validation checklist

- [ ] DEM CRS, transform, resolution, nodata, mask, and vertical unit recorded before conditioning.
- [ ] Conditioning ran in the DEM's native grid (no pre-routing reprojection) and `detect_*` asserts pass.
- [ ] Conditioning steps recorded in order (and fill-vs-breach choice justified if relevant).
- [ ] Routing method (D8/DINF/MFD) explicit and matched between `flowdir`, `accumulation`, and `catchment`.
- [ ] `dirmap` matches any external direction raster, or direction was recomputed.
- [ ] Stream threshold value, unit, and selection method recorded; drop analysis used where rigor is required.
- [ ] Pour-point snapping reports original, snapped, and snap distance; large snaps surfaced.
- [ ] Catchment area computed in a documented projected CRS; geographic-cell-area trap avoided.
- [ ] Edge-contamination check left on (TauDEM) unless a `-nc` decision is justified.
- [ ] Runtime measured against the envelope, or TauDEM/MPI escalation justified.
- [ ] Derivative artifacts (stream network, HAND, TWI) each returned with their own envelope.
- [ ] Tool + version (PySheds version or TauDEM version + MPI process count) in provenance.

## 19. References

- PySheds docs and API (functional generation): https://mattbartos.com/pysheds/
- PySheds source / README: https://github.com/mdbartos/pysheds
- PySheds HAND example: https://mattbartos.com/pysheds/hand.html
- TauDEM site and tool documentation: https://hydrology.usu.edu/taudem/taudem5/
- TauDEM source and releases: https://github.com/dtarb/TauDEM and https://github.com/dtarb/TauDEM/releases
- TauDEM v5.5.0 release (latest, 2026-05-23): https://github.com/dtarb/TauDEM/releases/tag/v5.5.0
- Accessed: 2026-05-29
