# NRCS SSURGO

## When to use

Use for hydrologic soil group, Ksat, soil texture, mapunit/component/horizon joins, curve number inputs, infiltration estimates, and tasks mentioning SSURGO or Soil Data Access.

## Canonical data model

Normalized soil response at a point or polygon:

```ts
type SsurgSoilSummary = {
  source: "NRCS SSURGO";
  serviceVariant: "post.rest" | "SOAP" | "WMS" | "WFS";
  queryLanguage?: "sql";
  responseShape: "rowset" | "feature" | "map" | "xml";
  optionalPAoiToken?: string;
  queryGeometry: GeoJSON.Geometry;
  mukey: string;
  mapunitSymbol?: string;
  mapunitName?: string;
  components: Array<{
    cokey: string;
    componentName: string;
    comppct_r: number;
    hydgrp: "A" | "B" | "C" | "D" | "A/D" | "B/D" | "C/D" | null;
    ksat_um_per_s?: number | null;
  }>;
  weightedHydrologicGroup?: string | null;
  sourceVersion?: string;
};
```

## CRS, units, precision

Soil Data Access exposes the same soils through multiple service variants. Spatial services can be available in WGS84 (`EPSG:4326`), NAD83 (`EPSG:4269`), and Web Mercator (`EPSG:3857`). Preserve `spatialServiceVariant` and CRS in the return envelope instead of assuming all SDA responses are WGS84.

Ksat appears in SSURGO horizon/component fields with source-specific units; normalize to an explicitly named unit before combining with hydrology formulas. `comppct_r` is a percentage weight.

## Service family

| Variant | Contract |
|---------|----------|
| `post.rest` | SQL-over-HTTP rowset service; JSON or XML responses; can create persistent AOIs. |
| SOAP | Legacy/service-integration path; use only when needed by existing clients. |
| WMS | Map rendering path, not canonical analytics. |
| WFS | Spatial feature path with CRS variant choice. |

## Idiomatic call patterns

Use SQL-over-HTTP through Soil Data Access for tabular model data. Prefer explicit column lists:

```sql
select
  mu.mukey,
  mu.musym,
  mu.muname,
  co.cokey,
  co.compname,
  co.comppct_r,
  co.hydgrp
from mapunit mu
join component co on co.mukey = mu.mukey
where mu.mukey in (:mukeys)
order by mu.mukey, co.comppct_r desc
```

For horizon-level properties, join `component -> chorizon` and aggregate by component before aggregating to mapunit.

Fail closed on unbounded national queries. `post.rest` documents large rowset constraints; model a 100,000-row cap and use bounded AOIs or mapunit lists. Persistent AOIs should be treated as temporary tokens that last at least 24 hours, not permanent identifiers.

## Return contract

Return service variant, query language, response shape, optional persistent AOI token, query geometry, matched mapunits, component percentages, hydrologic group classification, unit-declared soil properties, row count, and retrieval provenance.

## Known gotchas

- `hydgrp` is not always a single letter. Dual classes (`A/D`, `B/D`, `C/D`) mean drained versus undrained behavior.
- Do not pick the first component blindly. Aggregate by `comppct_r` or preserve all components when uncertainty matters.
- Horizon values require depth-aware aggregation before they can be mapunit-level values.
- Mapunit boundaries and component percentages are generalized; expose uncertainty rather than presenting false precision.
- SSURGO refreshes on an NRCS cycle; include access date/source version in derived records.
- SDA can return JSON or XML depending on request. Preserve response shape.
- WMS is for display; do not use rendered maps as the analytics source.

## Integration with StormwaterIQ

SSURGO feeds curve number lookup, infiltration/risk scoring, site summaries, and subcatchment hydrology parameters. Persist derived summaries in tenant-scoped PostGIS tables or JSON metadata, not raw SDA response blobs unless audit requirements need them.

## Validation checklist

- [ ] `mukey`, `cokey`, `hydgrp`, and `comppct_r` are preserved.
- [ ] Dual hydrologic groups are handled explicitly.
- [ ] Weighted aggregation documents the chosen weighting rule.
- [ ] Soil property units are declared.
- [ ] Source query and access date are stored in provenance.
- [ ] Service variant, CRS, row count, and AOI token behavior are recorded.
- [ ] Unbounded national queries are rejected or explicitly batched.

## References

- https://sdmdataaccess.sc.egov.usda.gov/
- https://sdmdataaccess.nrcs.usda.gov/
- Accessed: 2026-05-08
