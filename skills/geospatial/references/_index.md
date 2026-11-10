# Geospatial Reference Index

Use this file to route a StormwaterIQ geospatial task to the smallest necessary reference. Always keep `SKILL.md`'s reliability contract in force.

## Cross-Cutting References

| Need | Read |
|------|------|
| CRS, projection, or unit conversions | `crs-and-units.md` |
| Metadata envelope for raster/vector/tile outputs | `return-contract.md` |
| Raster nodata or mask conversions | `mask-conventions.md` |
| Canonical PostGIS tables and indexes | `postgis-data-model.md` |
| GeoPandas joins, lineage, and CRS alignment | `spatial-join-patterns.md` |

## Data Source Routing

| Task or phrase | Read |
|----------------|------|
| External source integration, auth/freshness/CRS/transport contract | `data-sources/_registry.md` |
| DEM, elevation, slope, terrain, 1m, 1/3 arc-second, 3DEP | `data-sources/usgs-3dep.md` |
| Soil hydrologic group, Ksat, SSURGO, mapunit, component, horizon | `data-sources/nrcs-ssurgo.md` |
| NLCD, land cover, impervious surface, runoff coefficient, curve number | `data-sources/mrlc-nlcd.md` |
| Atlas 14, PFDS, rainfall depth, IDF, recurrence interval | `data-sources/noaa-atlas14.md` |
| MRMS raster QPE/QPF, GRIB2, GeoTIFF, high-cadence radar products | `data-sources/noaa-mrms-nws.md` |
| Weather.gov API, forecasts, alerts, `/points`, CAP, Atom, JSON-LD | `data-sources/noaa-mrms-nws.md` |
| Tomorrow.io, premium weather API, weather maps, commercial weather SLA | `data-sources/tomorrow-io.md` |
| NWIS, streamflow, water quality, gage observations | `data-sources/usgs-water-data.md` |
| Mapbox tiles, terrain-dem, geocoding, static images, isochrones | `data-sources/mapbox-apis.md` |
| OSM, Nominatim, public OSM tiles, TIGERweb, TIGER/Line | `data-sources/osm-tiger.md` |
| EPA ECHO, NPDES facility, permit lookup | `data-sources/epa-echo.md` |
| EPA WATERS, NHDPlus, reach-indexed hydrography, HUC | `data-sources/epa-waters-attains.md` |
| EPA ATTAINS, impaired waters, assessment units, TMDL, cycle year | `data-sources/epa-waters-attains.md` |
| State-delegated MS4 permit registries | `data-sources/state-ms4-registry.md` |

## Library And Capability Routing

| Task or phrase | Read |
|----------------|------|
| Inspect raster, validate COG, translate raster, reproject raster, read raster window | `libraries/gdal-rasterio.md` |
| Serve or read XYZ tiles from rasters/COGs | `libraries/rio-tiler.md` |
| Condition DEM, delineate watershed/subcatchments, snap pour point, flow accumulation, stream ordering, HAND, TWI, time of concentration, TauDEM MPI | `libraries/pysheds-taudem.md` |
| Validate geometry, clean polygons, simplify, GeoDataFrame operations | `libraries/shapely-geopandas.md` |
| Spatial SQL, PostGIS schema, GIST, ST_DWithin, ST_Subdivide, geography vs geometry | `libraries/postgis.md` |
| Browser/client GeoJSON math, buffers, distances, areas | `libraries/turfjs.md` |
| Raster algebra, masked arrays, smoothing, distance transform | `libraries/numpy-scipy.md` |
| Web Mapbox GL source/layer/expression model | `libraries/mapbox-gl-js.md` |
| React Native Mapbox offline maps or styles | `libraries/mapbox-sdk-rn.md` |
| Offline tiled overlays, single-file tile archive, range requests | `libraries/pmtiles.md` |

## Default Read Order

1. `crs-and-units.md`
2. `return-contract.md`
3. `data-sources/_registry.md`, if ingesting or querying an external product
4. The specific data-source reference
5. The specific library reference, if writing implementation code
6. `postgis-data-model.md` or `spatial-join-patterns.md` when persisting or joining platform data
