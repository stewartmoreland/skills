# PostGIS

## When to use

Use when writing spatial SQL, Supabase migrations, RLS-safe spatial procedures, geometry/geography choices, GIST indexes, `ST_DWithin`, `ST_Transform`, `ST_Subdivide`, vector tile SQL, or canonical spatial table models.

## Canonical data model

Read `../postgis-data-model.md` first for table shapes. Store StormwaterIQ authoritative vectors as `geometry(<type>, 4326)` with:
- `organization_id` or equivalent tenant key
- `metadata jsonb` for source/provenance
- GIST index on every persisted spatial column
- SRID and validity constraints where feasible

## CRS, units, precision

Use `ST_Transform` for authoritative transformations. Use local projected CRS for area/distance calculations, or geography expressions where spheroidal distance is the product requirement.

```sql
select
  id,
  st_area(st_transform(geom, 26916)) as area_sq_m
from parcels
where organization_id = $1;
```

## Idiomatic call patterns

Prefer indexed proximity filters:

```sql
select o.*
from outfalls o
where o.organization_id = $1
  and st_dwithin(o.geom::geography, st_setsrid(st_makepoint($2, $3), 4326)::geography, $4);
```

Use `ST_DWithin` for filtering and `ST_Distance` for returned distance values.

Subdivide large polygons before joins:

```sql
with parcel_parts as (
  select id, organization_id, (st_dump(st_subdivide(geom, 256))).geom as geom
  from parcels
  where organization_id = $1
)
select p.id, count(*) as outfall_count
from parcel_parts p
join outfalls o
  on o.organization_id = p.organization_id
 and st_intersects(p.geom, o.geom)
group by p.id;
```

## Return contract

Spatial SQL results must include CRS, unit metadata, source table lineage, tenant scope, and processing SQL or procedure name in provenance.

## Known gotchas

- `ST_Distance` alone may skip indexes; pair indexed filters with distance calculations.
- `geometry` is faster and more flexible for stored features; `geography` is useful for meter-based global distance semantics.
- `ST_Buffer` on `EPSG:4326` degrees is usually wrong for engineering distance.
- Invalid polygons can poison joins and overlays.
- RLS does not replace explicit service-role scoping.

## Integration with StormwaterIQ

PostGIS is the platform record for vector geometries and derived spatial intelligence. Supabase data is tenant-scoped and should be accessed through RLS-first clients or explicitly scoped service-role code. Raster source products generally stay outside PostGIS unless a task specifically requires raster-in-database behavior.

## Validation checklist

- [ ] Spatial queries scope by tenant/org before joining or filtering.
- [ ] Stored spatial columns have declared SRID and GIST indexes.
- [ ] Distance/area calculations use an appropriate CRS or geography.
- [ ] Large polygon joins use `ST_Subdivide` or a materialized helper.
- [ ] Query outputs declare CRS and units in their API contract.

## References

- https://postgis.net/documentation/
- https://postgis.net/docs/ST_DWithin.html
- https://postgis.net/docs/ST_Subdivide.html
