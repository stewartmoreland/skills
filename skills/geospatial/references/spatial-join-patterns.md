# Spatial Join Patterns

## When to use

Use when joining parcels, sites, outfalls, BMPs, subcatchments, HUCs, impaired waters, soils, land-cover extracts, or any GeoDataFrames by spatial predicate.

## Canonical pattern

```python
left = left.to_crs("EPSG:5070") if left.crs != "EPSG:5070" else left
right = right.to_crs(left.crs)

joined = left.sjoin(
    right[["source_id", "quality_flag", "geometry"]],
    how="left",
    predicate="intersects",
)

joined = joined.rename(columns={"index_right": "matched_feature_index"})
```

Pick a projected CRS appropriate for the operation when area, distance, or buffering matters. For pure topological predicates, an aligned CRS is still required.

## Join behavior to remember

| Join | Geometry retained |
|------|-------------------|
| `how="left"` | Left geometry |
| `how="inner"` | Left geometry |
| `how="right"` | Right geometry |

GeoPandas adds right-side lineage as `index_right` by default. Preserve or rename it; do not drop it before validation.

## Attribute merge rule

Keep the GeoDataFrame on the left side:

```python
result = parcels_gdf.merge(scores_df, on="parcel_id", how="left")
```

Putting a plain pandas DataFrame on the left can return a DataFrame without GeoDataFrame behavior.

## Known gotchas

- GeoPandas operations are planar and do not account for Z.
- Iterating over geometries can lose CRS metadata; preserve GeoSeries/GeoDataFrame containers.
- Invalid geometries can make predicates behave unexpectedly. Validate and repair before joins.
- `contains` vs `covers` matters for boundary points; outfalls on polygon edges often need `covers`.
- `sjoin_nearest` needs a projected CRS for meaningful distance values.

## Validation checklist

- [ ] Both inputs have known CRS.
- [ ] Both inputs are in the same CRS before join.
- [ ] Predicate matches the compliance question (`intersects`, `covers`, `within`, etc.).
- [ ] Right-side lineage is preserved.
- [ ] Geometry validity is checked before and after repair/simplification.
- [ ] Output envelope declares CRS, predicate, source row counts, and match counts.
