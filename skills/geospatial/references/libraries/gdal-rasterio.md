# GDAL And Rasterio

## When to use

Use for raster inspection, COG validation, format translation, reprojection, nodata handling, windowed reads, affine transforms, masked arrays, and workflows named `inspect_raster_asset`, `translate_or_reproject_raster`, or `read_raster_window`.

## Canonical data model

TODO: Define raster asset, raster window, band profile, and COG validation result schemas.

## CRS, units, precision

Read CRS, transform, dtype, nodata, bounds, block size, and masks from dataset metadata. TODO: document target CRS selection and per-domain resampling policies.

## Idiomatic call patterns

TODO: Add examples for:
- `gdalinfo`/GDAL dataset inspection
- `gdal driver cog validate`
- `gdalwarp`/Rasterio reprojection with explicit `srcnodata` and `dstnodata`
- Rasterio windowed read returning `window_transform`

## Return contract

Return artifact plus CRS, bounds, affine transform, dtype, nodata, mask semantics, block/window details, source path/URL, and processing command/options.

## Known gotchas

- Updating a COG can break layout optimization; revalidate after writes.
- Windowed reads need window-relative transforms.
- Continuous and categorical rasters need different resampling kernels.
- GDAL/Rasterio valid masks use nonzero for valid; `numpy.ma` masks use `True` for invalid.

## Integration with StormwaterIQ

GDAL/Rasterio workflows split across `services/terrain-worker` (DEM, hillshade, contours, hydrology prep) and `services/imports-worker` (FileGDB analyze + extract + import_prepare).

## Validation checklist

- [ ] Raster metadata is inspected before processing.
- [ ] COG outputs are validated.
- [ ] Nodata and mask behavior are explicit.
- [ ] Windowed outputs include window transform and bounds.
- [ ] Reprojection command/options are stored in provenance.

## References

- https://gdal.org/
- https://rasterio.readthedocs.io/
