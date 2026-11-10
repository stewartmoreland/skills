# USGS 3DEP

## When to use

Use for DEM ingestion, elevation sampling, slope, terrain derivatives, flow accumulation, watershed delineation, COG reads, and any task mentioning 1m, 1/3 arc-second, 1 arc-second, S1M, or The National Map.

## Canonical data model

Minimum normalized DEM metadata:

```ts
type ThreeDepDemAsset = {
  source: "USGS 3DEP";
  sourceProvider: "USGS_TNM" | "USGS_dynamic_service" | "OpenTopography";
  productClass: "project_1m" | "1_9_arc_second" | "1_3_arc_second" | "1_arc_second" | "alaska_5m" | "S1M" | "other";
  url: string;
  crs: string;
  resolution: { x: number; y: number; unit: string };
  verticalUnit: "meters" | "feet" | "unknown";
  bounds: [number, number, number, number];
  nodata: number | null;
  acquiredAt?: string;
  sourceVersion?: string;
};
```

## CRS, units, precision

Read CRS, transform, nodata, vertical units, and resolution from the asset metadata. 3DEP is not one CRS:

| Product/access mode | CRS rule |
|---------------------|----------|
| Project-based 1m DEM | Often UTM/project-specific; read metadata |
| 1/9 arc-second | Geographic coordinates |
| 1/3 arc-second and 1 arc-second | Read product metadata |
| Alaska 5m | Albers Equal Area |
| S1M COG tiles | Cloud Optimized GeoTIFF tiles; read metadata |
| Dynamic WMS/WCS | Service-advertised CRS |

Elevation calculations should use meters internally and convert to feet only for exhibits or user-facing deliverables. Reproject with GDAL/Rasterio or PostGIS-derived vector products, not app code.

## Access modes

| Access mode | Auth | Request shape | Notes |
|-------------|------|---------------|-------|
| USGS/TNM download | None | product/tile download | Preferred default when direct product access is sufficient. |
| USGS dynamic services | None | WMS/WCS | Useful for display or service-based extraction; keep service CRS separate from product CRS. |
| S1M COG tiles | None | range-readable COG tile | New seamless 1m product path; coverage is published as tiles become available. |
| OpenTopography wrapper | API key | bbox/API request | Convenience layer with request-size limits, free-key limits, and 3DEP 1m eligibility constraints. |

## Idiomatic call patterns

Use range-readable COGs when available:

```python
import rasterio

with rasterio.open(dem_url) as src:
    profile = src.profile
    window = src.window(*query_bounds)
    data = src.read(1, window=window, masked=True)
    transform = src.window_transform(window)
```

Use `bilinear` for continuous elevation resampling. Do not use `nearest` for DEM interpolation unless preserving exact pixel identity for QA.

## Return contract

Return raster outputs with `sourceProvider`, `productClass`, `crs`, `bounds`, `transform`, `dtype`, `nodata`, `maskSemantics`, `units.elevation`, and provenance. Include the USGS product page or asset URL, wrapper endpoint when used, and access date.

## Known gotchas

- The plan's older "~60% urban only" 1m caveat is stale as a universal claim. USGS launched the Seamless 1-Meter DEM (S1M) product, with production beginning in 2025 and tiles published as available. Confirm coverage for the site using USGS availability viewers.
- 1m coverage is not guaranteed everywhere. For CONUS-wide default coverage, fall back to 1/3 arc-second or 1 arc-second as appropriate.
- Requester-pays and cloud bucket access can matter for bulk reads.
- COG byte-range access is preferred for remote reads; downloading whole DEMs for small windows is a performance smell.
- Vertical units and datums matter for engineering exhibits; preserve them in provenance.
- Do not treat OpenTopography and direct USGS/TNM retrieval as operationally interchangeable; auth, quotas, limits, and eligibility differ.

## Integration with StormwaterIQ

The terrain worker (`services/terrain-worker`) owns DEM inspection, windowing, and hydrology preparation; geodatabase ingest belongs in `services/imports-worker`. Derived vector outputs land in PostGIS tables such as `subcatchments`, `sites`, and terrain summary tables; source rasters should remain in object storage or external COG URLs unless a migration explicitly imports them.

## Validation checklist

- [ ] CRS, transform, resolution, nodata, dtype, and vertical unit came from raster metadata.
- [ ] `sourceProvider` and `productClass` are recorded.
- [ ] Coverage was checked for the requested project area.
- [ ] Continuous elevation resampling uses `bilinear` or another documented continuous kernel.
- [ ] Windowed reads return the window-relative affine transform.
- [ ] Derived vectors include the source DEM URL/version and processing steps.

## References

- https://www.usgs.gov/3d-elevation-program
- https://www.usgs.gov/faqs/what-coverage-3d-elevation-program-3dep-dems
- https://www.usgs.gov/3d-elevation-program/new-product-3d-elevation-program-seamless-1-meter-digital-elevation-model-s1m
- Accessed: 2026-05-08
