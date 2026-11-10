# CRS And Units

## When to use

Use before any geospatial task that reads, writes, transforms, joins, buffers, tiles, or displays spatial data.

## Canonical CRS model

| Domain | Native/source CRS | StormwaterIQ canonical CRS | Notes |
|--------|-------------------|----------------------------|-------|
| Platform vector records | Varies | `EPSG:4326` geometry | Store as `geometry(*, 4326)` unless spatial measurement accuracy requires a projected working CRS. |
| Mapbox display | `EPSG:3857` | Derived only | Web Mercator is for tiles/rendering. Do not persist it as source of record. |
| USGS 3DEP DEM | commonly `EPSG:4269` or product metadata | Preserve native in raster metadata; transform outputs explicitly | Read CRS from dataset metadata, not from product name. |
| MRLC NLCD | `EPSG:5070` Albers Equal Area | Reproject extracts explicitly | This is the common projection trap. Do not assume `EPSG:4326`. |
| NOAA Atlas 14 PFDS | `EPSG:4326` point query | `EPSG:4326` | Lat/lon input. Returned rainfall table is non-spatial but should retain query point. |
| EPA/USGS/NRCS REST point/vector APIs | Usually `EPSG:4326` or `EPSG:4269` | `EPSG:4326` | Confirm per endpoint and preserve source CRS in metadata. |

## Reprojection rules

- Reproject in PostGIS (`ST_Transform`), GDAL/Rasterio, or the GDAL worker service.
- Do not reproject in UI code. UI maps consume transformed, derived data.
- For spatial joins, reproject both inputs to the same CRS before the operation and record which side moved.
- For measurement, use a projected CRS suitable for the local area or geography where appropriate; do not measure Web Mercator distances.
- Preserve original source CRS in provenance even when outputs are transformed.

## Unit canon

| Domain | Internal default | User-facing default | Gotcha |
|--------|------------------|---------------------|--------|
| Rainfall depth | Store with explicit unit; prefer mm for calculations | inches for Atlas 14/PFDS and US exhibits | Atlas 14 returns inches. |
| Flow | cubic meters per second for scientific workflows | CFS | Never combine CFS and m3/s without an explicit conversion. |
| Elevation | meters | feet where exhibits require it | 3DEP source products can appear in meter-based rasters even when users expect feet. |
| Area | square meters | acres or square feet | Always state area unit in reports and DB columns. |
| Distance | meters | feet or miles as requested | Turf unit strings are exact words (`meters`, `kilometers`, `miles`). |
| Slope | unitless ratio or percent, explicitly named | percent | Do not mix degrees and percent slope. |

## Precision and parity

Hydrology outputs that mirror hand calculations should stay within +/-2% unless a product requirement gives a different threshold. Rounding should happen only at presentation boundaries; keep intermediate calculations at floating precision suitable for the input data.

## Known gotchas

- NLCD is Albers (`EPSG:5070`), not WGS84.
- Web Mercator (`EPSG:3857`) distorts distance/area and should not drive compliance measurements.
- `EPSG:4269` and `EPSG:4326` are close but not identical; do not silently relabel one as the other.
- GeoJSON is conventionally WGS84 longitude/latitude. If a library accepts arbitrary coordinates, still declare the CRS in the metadata envelope.

## Validation checklist

- [ ] Input and output CRS are declared.
- [ ] Reprojection step and tool are documented in provenance.
- [ ] Unit conversions are explicit and tested with fixtures.
- [ ] No UI code performs authoritative CRS transformation.
- [ ] Spatial joins and measurements use an appropriate CRS.
