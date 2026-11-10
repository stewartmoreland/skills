# State MS4 Registry

## When to use

Use for delegated NPDES/MS4 permit data from state agencies, state-specific facility registries, permit boundaries, compliance portals, and heterogeneous state GIS APIs.

## Canonical data model

```ts
type StateStormwaterAdapterRecord = {
  source: "State MS4 Registry";
  adapterId: `state_stormwater_${string}`;
  state: string;
  agency: string;
  permittingAuthority: "state" | "epa" | "tribal" | "territory" | "mixed" | "unknown";
  datasetScope: "municipal_ms4" | "industrial_stormwater" | "construction_stormwater" | "npdes_general" | "other";
  endpointType: "arcgis_rest" | "ogc_wfs" | "download" | "html_table" | "api" | "other";
  auth: "none" | "api_key" | "account" | "unknown";
  rawPermitId?: string;
  normalizedNpdesId?: string;
  permittee?: string;
  geometryType?: "Point" | "LineString" | "Polygon" | "MultiPolygon" | "none" | "mixed";
  updateDate?: string;
  refreshCycle?: string;
  adapterVersion: string;
  retrievedAt: string;
  rawProperties: Record<string, unknown>;
};
```

## CRS, units, precision

State GIS services vary by agency and platform. Each adapter must record advertised CRS, geometry type, transformation into StormwaterIQ canonical geometry, and whether geometry is permit boundary, facility point, jurisdiction, or display-only.

## Idiomatic call patterns

- Build one adapter record per state/source/dataset scope; do not assume a nationwide API schema.
- Declare EPA/state/tribal/territory permitting authority because NPDES authorization varies by jurisdiction and permit component.
- Preserve raw source fields in `rawProperties` and map only stable fields into the normalized model.
- Treat refresh cycle as source-specific. Example patterns from research: New York municipal storm sewer system layer through ArcGIS REST with five-year update language; California stormwater permit mapping with annual, non-real-time industrial stormwater layers.

## Adapter metadata requirements

| Field | Why it matters |
|-------|----------------|
| `permittingAuthority` | EPA may still issue permits in some jurisdictions or permit components. |
| `datasetScope` | Municipal, industrial, and construction stormwater layers are not interchangeable. |
| `geometryType` | Some sources are points, some polygons, some non-spatial tables. |
| `updateDate` and `refreshCycle` | State layers can be annual, five-year, event-driven, or stale. |
| `auth` and `endpointType` | ArcGIS REST, downloads, and custom APIs have different limits and schemas. |
| `adapterVersion` | State-specific field mappings must be auditable. |

## Return contract

Return raw source record, normalized permit fields, geometry, CRS, agency, source URL, adapter version, and access date.

## Known gotchas

- State agencies use inconsistent permit identifiers and lifecycle statuses.
- Some state GIS services expose Web Mercator features; convert deliberately before storage.
- Auth, rate limits, and data freshness vary by state.
- A single national schema encourages fabricated freshness and fields. Use an adapter family.
- Dataset scope must be explicit before comparing permits across states.

## Integration with StormwaterIQ

State MS4 registries enrich permit intelligence and jurisdiction workflows. Treat state data as external reference data unless linked to tenant-owned inspections or remediation records.

## Validation checklist

- [ ] Adapter declares state, agency, CRS, auth, and refresh cadence.
- [ ] Raw and normalized permit IDs are preserved.
- [ ] Geometry source and quality are documented.
- [ ] State-specific assumptions do not leak into other states.
- [ ] Permitting authority and dataset scope are recorded.
- [ ] Adapter version is included in provenance.

## References

- https://www.epa.gov/npdes/npdes-state-program-information
- Adapter source links should be added per state as each connector is implemented.
- Accessed: 2026-05-08
