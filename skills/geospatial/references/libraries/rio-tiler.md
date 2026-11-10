# rio-tiler

## When to use

Use for reading XYZ tiles, points, parts, and features from COGs or other GDAL-readable rasters, especially workflows named `read_xyz_tile`.

## Canonical data model

TODO: Define tile request, `ImageData` response, tile matrix set, min/max zoom, band expression, and resampling policy schemas.

## CRS, units, precision

Default slippy-map tiles use Web Mercator tile bounds. Preserve source raster CRS separately from tile bounds and output tile matrix set.

## Idiomatic call patterns

TODO: Add examples for `Reader.tile(x, y, z)`, `Reader.point()`, custom TileMatrixSet, `resampling_method`, and `xy_bounds`.

## Return contract

Return tile bytes or image data plus tile bounds, tile matrix set, source CRS, source URL, zoom, resampling method, dtype, nodata, and mask semantics.

## Known gotchas

- XYZ and TMS y-axis conventions can be confused; declare the tile matrix set.
- Use nearest-neighbor for categorical tiles; smoother kernels only for continuous visualizations.
- Read options and expression evaluation affect dtype and nodata semantics.

## Integration with StormwaterIQ

rio-tiler can serve derived raster previews from GDAL-worker-compatible COGs. Persist authoritative summaries separately; tiles are display artifacts.

## Validation checklist

- [ ] Tile matrix set and tile bounds are recorded.
- [ ] Source raster metadata is not lost.
- [ ] Resampling method matches data type.
- [ ] Output mask/nodata semantics are declared.

## References

- https://cogeotiff.github.io/rio-tiler/
