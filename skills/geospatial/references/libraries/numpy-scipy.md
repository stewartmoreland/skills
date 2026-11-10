# NumPy And SciPy

## When to use

Use for masked raster math, dtype promotion, raster algebra, smoothing, morphology, distance transforms, proximity rasters, and workflows named `masked_raster_math` or `filter_distance_and_proximity`.

## Canonical data model

TODO: Define array artifact, mask, dtype policy, nodata policy, and proximity raster schemas.

## CRS, units, precision

Array operations inherit spatial meaning from raster metadata. Always pass CRS, transform, bounds, units, nodata, and mask semantics alongside arrays.

## Idiomatic call patterns

TODO: Add examples for masked arithmetic, accumulator dtype selection, `gaussian_filter` output dtype, and `distance_transform_edt` distance/index outputs.

## Return contract

Return array artifact plus inherited raster metadata, output dtype, mask semantics, unit changes, and numerical operation provenance.

## Known gotchas

- `numpy.ma` uses `True` for invalid mask entries.
- NumPy dtype promotion can overflow or lose precision if output dtype is not chosen intentionally.
- SciPy filters may store intermediate arrays in output dtype.
- Distance transforms return distances in pixel units unless sampling is provided.

## Integration with StormwaterIQ

Use inside GDAL worker and hydrology pipelines for derived rasters and proximity metrics. Persist derived summaries or COG/PMTiles artifacts with metadata envelopes.

## Validation checklist

- [ ] Input and output dtype are declared.
- [ ] Mask semantics are converted correctly.
- [ ] Spatial transform and pixel size are preserved.
- [ ] Distance outputs declare units and sampling.

## References

- https://numpy.org/doc/stable/
- https://docs.scipy.org/doc/scipy/
