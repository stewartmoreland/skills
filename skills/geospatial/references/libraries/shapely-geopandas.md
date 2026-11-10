# Shapely And GeoPandas

## When to use

Use for geometry validity, repair, simplification, buffering, overlay, GeoDataFrame CRS handling, spatial joins, attribute joins, and workflows named `validate_and_clean_geometry` or `spatial_join_geodataframes`.

## Canonical data model

TODO: Define geometry validation report, repair provenance, GeoDataFrame join result, and lineage-column schemas.

## CRS, units, precision

Shapely is planar and does not track CRS. GeoPandas stores CRS on GeoSeries/GeoDataFrames. Keep CRS-bearing containers intact and avoid bare geometry iteration where CRS metadata can be lost.

## Idiomatic call patterns

TODO: Add examples for `is_valid`, `buffer(0)` repair caveat, topology-preserving simplify, `to_crs`, `sjoin`, and left-side GeoDataFrame merge.

## Return contract

Return cleaned geometry or joined GeoDataFrame plus CRS, validity before/after, repair strategy, predicate, match lineage, row counts, and source feature IDs.

## Known gotchas

- Shapely ignores Z in planar analysis; drop or preserve Z out-of-band with a warning.
- Geometry constructors do not guarantee validity.
- `simplify(..., preserve_topology=False)` can create invalid geometry.
- GeoPandas joins retain left geometry for left/inner joins and right geometry for right joins.

## Integration with StormwaterIQ

Use for worker-side vector cleaning and import preparation before persistence to Supabase/PostGIS. Server-side PostGIS remains preferred for authoritative tenant-scoped spatial joins at scale.

## Validation checklist

- [ ] CRS is known before operations.
- [ ] Validity is checked before and after repair/simplification.
- [ ] Z-coordinate behavior is documented.
- [ ] Join predicate and lineage columns are preserved.
- [ ] Output includes source row counts and match counts.

## References

- https://shapely.readthedocs.io/
- https://geopandas.org/
