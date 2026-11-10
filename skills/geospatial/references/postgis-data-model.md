# PostGIS Data Model

## When to use

Use when designing or reviewing StormwaterIQ spatial tables, indexes, constraints, materialized views, migrations, or tRPC procedures backed by Supabase/PostGIS.

## Geometry vs geography

| Use | Type |
|-----|------|
| Most stored platform features | `geometry(<type>, 4326)` |
| Long-distance meters-based filters where exact spheroidal distance matters | `geography` expression or generated column |
| Local engineering measurements | Transform to a suitable projected CRS inside the query |
| Map display | Derived GeoJSON/vector tiles from canonical geometry |

Default to `geometry` for storage and index behavior. Use `geography` deliberately for distance semantics, not as a blanket replacement.

## Canonical table shapes

These are conceptual shapes, not a migration to apply blindly.

```sql
sites (
  id uuid primary key,
  organization_id uuid not null,
  name text not null,
  boundary geometry(MultiPolygon, 4326),
  centroid geometry(Point, 4326) generated or maintained,
  metadata jsonb not null default '{}'
)
```

```sql
parcels (
  id uuid primary key,
  organization_id uuid not null,
  external_id text,
  site_id uuid,
  geom geometry(MultiPolygon, 4326) not null,
  source text not null,
  source_version text,
  metadata jsonb not null default '{}'
)
```

```sql
outfalls (
  id uuid primary key,
  organization_id uuid not null,
  site_id uuid,
  geom geometry(Point, 4326) not null,
  status text not null,
  metadata jsonb not null default '{}'
)
```

```sql
subcatchments (
  id uuid primary key,
  organization_id uuid not null,
  outlet_id uuid,
  geom geometry(MultiPolygon, 4326) not null,
  area_sq_m numeric,
  method text not null,
  metadata jsonb not null default '{}'
)
```

```sql
bmps (
  id uuid primary key,
  organization_id uuid not null,
  site_id uuid,
  geom geometry(Geometry, 4326) not null,
  bmp_type text not null,
  metadata jsonb not null default '{}'
)
```

```sql
sensors (
  id uuid primary key,
  organization_id uuid not null,
  site_id uuid,
  geom geometry(Point, 4326) not null,
  observed_property text not null,
  metadata jsonb not null default '{}'
)
```

## Indexing and constraints

```sql
create index on parcels using gist (geom);
create index on outfalls using gist (geom);
create index on subcatchments using gist (geom);

alter table parcels
  add constraint parcels_geom_srid check (st_srid(geom) = 4326),
  add constraint parcels_geom_valid check (st_isvalid(geom));
```

Use partial indexes for status-heavy tables and tenant-scoped btree indexes for `organization_id` plus common filters.

## Large geometry policy

- Use `ST_Subdivide` before expensive joins on large polygons.
- Store the authoritative polygon once; materialize subdivided helper views when needed.
- Keep raster products in object storage or PMTiles unless a PostGIS raster is clearly required.
- Store vector-derived summaries and audit metadata in PostGIS.

## Tenant safety

Every table that stores customer data needs explicit organization scoping and RLS policy coverage. Service-role code must still scope by `organization_id` before any spatial operation; do not rely on client-side filters.

## Validation checklist

- [ ] Every spatial column has declared type and SRID.
- [ ] Every spatial column has a GIST index or an intentional exception.
- [ ] Geometry validity and SRID checks exist for persisted geometries.
- [ ] Queries scope tenant/org before spatial filters.
- [ ] Large polygons are subdivided for joins rather than brute-forced.
