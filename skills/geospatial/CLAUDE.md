# StormwaterIQ Geospatial

## Structure

```
geospatial/
  SKILL.md       # Main skill file - read this first
  AGENTS.md      # This navigation guide
  CLAUDE.md      # Mirror of AGENTS.md
  references/    # Detailed reference files
```

## Usage

1. Read `SKILL.md` for the reliability contract, CRS/unit canon, and routing table.
2. Read `references/_index.md` when selecting a source, library, or workflow.
3. Browse `references/` for detailed data models and call patterns. Reference files are loaded on demand; read only what the task requires.

## When to Apply

Reference these guidelines when:
- Ingesting or modeling NOAA, USGS, EPA, NRCS, MRLC, Mapbox, or state MS4 geospatial data
- Working with GDAL, Rasterio, rio-tiler, PySheds, TauDEM, Shapely, GeoPandas, NumPy/SciPy raster math, PostGIS, turf.js, PMTiles, or Mapbox SDKs
- Designing PostGIS spatial schemas, indexes, materialized views, or tenant-scoped spatial queries
- Computing watershed delineation, terrain derivatives, land-cover summaries, soil hydrologic groups, precipitation frequency, or spatial joins
- Reviewing a geospatial change for CRS, unit, nodata, mask, provenance, or validation risks

## Reference Categories

| Category | Path | Purpose |
|----------|------|---------|
| Index | `references/_index.md` | Route common tasks to the right reference |
| Cross-cutting | `references/*.md` | CRS, units, metadata envelopes, masks, PostGIS models, spatial joins |
| Data sources | `references/data-sources/*.md` | External API/product schemas and ingestion rules |
| Libraries | `references/libraries/*.md` | Library-specific call patterns and gotchas |

## References

- https://gdal.org/
- https://rasterio.readthedocs.io/
- https://cogeotiff.github.io/rio-tiler/
- https://mattbartos.com/pysheds/
- https://hydrology.usu.edu/taudem/
- https://shapely.readthedocs.io/
- https://geopandas.org/
- https://postgis.net/documentation/
