---
name: geospatial
description: "Use when ingesting, reprojecting, tiling, querying, or modeling StormwaterIQ geospatial data: DEMs, soils, land cover, precipitation, NHD/HUC, MS4 permits, spatial joins, PostGIS schema design, Mapbox, turf.js, PMTiles, GDAL, Rasterio, rio-tiler, Shapely, or GeoPandas. Use for any hydrologic terrain analysis with PySheds or TauDEM, including DEM conditioning, flow direction/accumulation, pour-point snapping, watershed and subcatchment delineation, stream extraction and Strahler ordering, HAND, TWI, flow distance, and time-of-concentration inputs."
disable-model-invocation: false
---

# StormwaterIQ Geospatial

This skill is the data-model authority for StormwaterIQ geospatial work. Use it before changing spatial schemas, ingesting external geo data, computing hydrology, generating tiles, or writing client-side map logic.

## Reliability Contract

Every geospatial workflow must return both an artifact and a metadata envelope. Do not pass around bare rasters, GeoJSON, tiles, or database rows without the metadata needed to audit their spatial meaning.

Required envelope fields:
- `crs`: EPSG code or WKT, plus whether it is native or transformed.
- `bounds`: `[minX, minY, maxX, maxY]` with the CRS declared.
- `transform`: affine transform for raster/window outputs, when applicable.
- `tile_bounds`: XYZ/TMS bounds for tile outputs, when applicable.
- `dtype`: band or attribute type, including promoted output dtype.
- `nodata`: nodata value and whether it came from source metadata or processing.
- `mask_semantics`: use `valid_nonzero` internally unless a reference says otherwise.
- `units`: measurement units for every numeric domain field.
- `provenance`: source URL, product version, retrieval time, processing step, and code path.

For details, read `references/return-contract.md`.

## Mask Convention

Use GDAL/Rasterio-style masks internally: nonzero means valid data, zero means invalid or nodata. Convert `numpy.ma` masks only at the boundary because `numpy.ma` uses `True` to mean invalid. Always declare the convention in `metadata.mask_semantics`.

Read `references/mask-conventions.md` before writing raster algebra, hydrology, or tiling code.

## CRS Canon

Read `references/crs-and-units.md` before any reprojection or spatial join.

Core rules:
- Store operational vector data as PostGIS `geometry(*, 4326)` unless a reference gives a stronger reason.
- Reproject in PostGIS, GDAL, Rasterio, or the worker service. Do not reproject in UI code.
- Treat Mapbox/Web Mercator (`EPSG:3857`) as a rendering projection, not the source of record.
- Known native CRS values: USGS 3DEP often uses `EPSG:4269`, MRLC NLCD uses Albers Equal Area (`EPSG:5070`), Mapbox tiles use `EPSG:3857`, and most REST point/vector APIs use `EPSG:4326`.

## Unit Canon

Declare units at every boundary:
- Flow: CFS for user-facing exhibits, cubic meters per second internally when doing scientific calculations.
- Rainfall depth: inches from NOAA Atlas 14/PFDS; convert explicitly when storing or combining with metric sources.
- Elevation: meters internally; feet for stamped or customer-facing exhibits when required.
- Distances/areas: prefer meters/square meters internally; specify turf.js unit strings exactly (`meters`, `kilometers`, `miles`).
- StormwaterIQ parity target: hydrology outputs that mirror hand calculations should stay within +/-2% unless the product requirement says otherwise.

## StormwaterIQ Product Constraints

Supabase/PostGIS-backed platform data is the system of record. External GIS tools and map clients consume derived views. Preserve tenant boundaries, raw inspection/media protection, audit metadata, and validation trails. Never tune scoring or inspection logic for "more issues found"; optimize for accuracy, consensus, and validated outcomes.

## Task Routing

Start with `references/_index.md` when unsure. For external services, read `references/data-sources/_registry.md` before the individual source reference. Common routes:
- Raster inspection, reprojection, COG QA, and windowed reads: `references/libraries/gdal-rasterio.md`
- XYZ tiles from COGs or rasters: `references/libraries/rio-tiler.md`
- DEM conditioning, flow direction (D8/D-inf/MFD), accumulation, pour-point snapping, watershed/subcatchment delineation, stream extraction and Strahler ordering, HAND, TWI, flow distance/time-of-concentration inputs, and TauDEM MPI scale-up: `references/libraries/pysheds-taudem.md`
- Geometry validity and GeoDataFrame joins: `references/libraries/shapely-geopandas.md` and `references/spatial-join-patterns.md`
- PostGIS schema design and spatial SQL: `references/libraries/postgis.md` and `references/postgis-data-model.md`
- Client-side GeoJSON math: `references/libraries/turfjs.md`
- 3DEP DEMs: `references/data-sources/usgs-3dep.md`
- SSURGO soils and hydrologic soil group: `references/data-sources/nrcs-ssurgo.md`
- NLCD land cover: `references/data-sources/mrlc-nlcd.md`
- NOAA Atlas 14 precipitation frequency: `references/data-sources/noaa-atlas14.md`
- MRMS and Weather.gov forecasts/alerts: `references/data-sources/noaa-mrms-nws.md`
- Tomorrow.io premium weather: `references/data-sources/tomorrow-io.md`
- OSM/TIGER basemap, geocoding, and context: `references/data-sources/osm-tiger.md`

## Validation Checklist

Before declaring geospatial work complete:
- [ ] Every output has CRS, units, bounds, provenance, and mask/nodata semantics.
- [ ] No geometry rows have `NULL` SRID or invalid geometry.
- [ ] Spatial joins use aligned CRS and preserve lineage columns.
- [ ] Rasters preserve nodata and dtype intentionally.
- [ ] User-facing conversions between metric and US customary units are explicit.
- [ ] Tenant scope is enforced before reading or writing Supabase-backed data.
- [ ] Time-sensitive source versions include an access date in the reference or code comment.
