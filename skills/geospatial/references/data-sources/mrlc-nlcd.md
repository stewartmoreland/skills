# MRLC NLCD

## When to use

Use for land cover, impervious surface, runoff coefficient, SCS Curve Number inputs, land-cover summaries, categorical raster extraction, and tasks mentioning MRLC or NLCD.

## Canonical data model

Normalized land-cover extract:

```ts
type NlcdExtract = {
  source: "MRLC NLCD";
  product: "Annual NLCD" | "Legacy NLCD";
  productYear: number;
  collection: string;
  legendVersion: string;
  classDomain: "legacy_16_class" | "annual_modified_anderson" | "other";
  classCode: number;
  classLabel: string;
  pixelAreaSqM: number;
  imperviousFraction?: number | null;
  runoffCoefficientC?: number | null;
  curveNumber?: number | null;
  crs: "EPSG:5070";
  resolutionMeters: 30;
};
```

## CRS, units, precision

NLCD land-cover rasters use a 30-meter grid and Albers Equal Area (`EPSG:5070`). Keep categorical extraction in the native grid when possible. Reproject derived vectors or summaries after extraction, not before, unless the workflow is explicitly display-only.

## Class model

Use official NLCD class codes and labels for the selected product, collection, and legend version. StormwaterIQ hydrology mappings should keep the raw `classCode` and attach derived values such as runoff coefficient `C` and curve number by lookup table keyed by land-cover class and hydrologic soil group.

Common codes include:

| Code | Label |
|------|-------|
| 11 | Open Water |
| 21 | Developed, Open Space |
| 22 | Developed, Low Intensity |
| 23 | Developed, Medium Intensity |
| 24 | Developed, High Intensity |
| 31 | Barren Land |
| 41 | Deciduous Forest |
| 42 | Evergreen Forest |
| 43 | Mixed Forest |
| 52 | Shrub/Scrub |
| 71 | Grassland/Herbaceous |
| 81 | Pasture/Hay |
| 82 | Cultivated Crops |
| 90 | Woody Wetlands |
| 95 | Emergent Herbaceous Wetlands |

## Idiomatic call patterns

- Use WMS or rendered tiles for display only.
- Use WCS, COG, or downloaded raster access for pixel extraction and hydrology summaries.
- Extract in `EPSG:5070`, tabulate class counts/area, then convert areas to requested units.
- Treat "current NLCD" as ambiguous until the workflow names `productYear`, `collection`, `legendVersion`, and `classDomain`.

## Return contract

Return class counts, pixel area, CRS, product year, collection, legend version, class domain, lookup table version, and derived hydrology parameters. Preserve raw class codes even when storing summaries.

## Known gotchas

- Do not assume WGS84. NLCD's native Albers CRS is the most common trip-up.
- Categorical rasters require nearest-neighbor only when resampling is unavoidable.
- Annual NLCD is newer than legacy NLCD. The MRLC page states Annual NLCD Collection 1.0 covers 1985-2023, while search results showed Collection 1.1 and products through 2024 are available. Confirm the exact product year at download time.
- A 30m pixel can cross parcel edges; area summaries near boundaries need uncertainty tolerance.
- NLCD is product-year-driven, not a live operational feed.
- Legacy national land cover and Annual NLCD can have different class domains and legends.

## Integration with StormwaterIQ

NLCD feeds runoff coefficient and curve number derivation, impervious area summaries, risk intelligence, and compliance reporting. Store raw class summaries and lookup versions so future coefficient changes can be audited.

## Validation checklist

- [ ] Source product, collection, and year are recorded.
- [ ] `productYear`, `legendVersion`, and `classDomain` are explicit.
- [ ] Extraction acknowledges `EPSG:5070` and 30m pixels.
- [ ] Categorical resampling uses nearest-neighbor only.
- [ ] Derived `C` and Curve Number values cite a lookup version.
- [ ] Output stores both raw class code and derived hydrology values.

## References

- https://www.mrlc.gov/data/project/annual-nlcd
- https://www.mrlc.gov/data
- Accessed: 2026-05-08
