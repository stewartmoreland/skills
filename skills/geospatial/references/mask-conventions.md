# Mask Conventions

## When to use

Use when reading rasters, creating raster windows, serving tiles, performing raster algebra, smoothing arrays, computing distance transforms, conditioning DEMs, or preserving nodata through hydrology workflows.

## Canonical model

StormwaterIQ uses GDAL/Rasterio-style masks internally:

| Convention | Meaning of `true` or nonzero | Used by |
|------------|-------------------------------|---------|
| `valid_nonzero` | Valid data | GDAL valid data masks, Rasterio dataset masks |
| `invalid_true` | Invalid or missing data | `numpy.ma.MaskedArray.mask` |

Internal envelope value: `metadata.maskSemantics = "valid_nonzero"`.

## Conversion snippets

Convert Rasterio/GDAL valid mask to `numpy.ma`:

```python
import numpy as np

def to_numpy_ma(data: np.ndarray, valid_mask: np.ndarray) -> np.ma.MaskedArray:
    return np.ma.array(data, mask=(valid_mask == 0))
```

Convert `numpy.ma` back to internal valid mask:

```python
import numpy as np

def to_internal_mask(masked: np.ma.MaskedArray) -> np.ndarray:
    return np.where(np.ma.getmaskarray(masked), 0, 255).astype("uint8")
```

## Known gotchas

- `numpy.ma` flips the semantic meaning of truth compared with GDAL/Rasterio masks.
- Nodata is a value; a mask is validity state. Preserve both when available.
- Resampling can smear nodata into valid pixels if nodata is not declared to the resampler.
- Hydrology conditioning should keep a terrain-validity mask separate from DEM values.
- Categorical rasters should not use interpolation kernels that invent class values.

## Validation checklist

- [ ] Output envelope declares `maskSemantics`.
- [ ] Nodata value and mask are both preserved or intentionally derived.
- [ ] `numpy.ma` conversions happen at boundaries only.
- [ ] Resampling method documents nodata treatment.
- [ ] Mask dtype and shape match the raster data shape.
