# EPA ECHO

## When to use

Use for NPDES facility lookup, permit status, compliance history, enforcement context, regulated outfall/facility discovery, and tasks mentioning EPA ECHO.

## Canonical data model

```ts
type EchoPermitFacility = {
  source: "EPA ECHO";
  endpointFamily: "facility_search" | "permit_lookup" | "compliance_report" | "enforcement_report" | "bulk_download";
  registryId?: string;
  npdesId?: string;
  rawPermitId?: string;
  facilityName?: string;
  program?: "ICIS-NPDES" | string;
  receivingWaterContext?: string;
  complianceStatus?: string;
  reportPeriod?: string;
  refreshDate?: string;
  coordinate?: { longitude: number; latitude: number; crs: "EPSG:4326"; quality?: string };
  retrievedAt: string;
};
```

## CRS, units, precision

ECHO facility coordinates are generally longitude/latitude when present. Preserve coordinate quality, nullability, and estimated-location flags when an endpoint returns them.

## Service contract

| Field | Contract |
|-------|----------|
| `auth_mode` | None for public web services |
| `request_shape` | Public GET-only REST-like search/report API |
| `native_format` | XML, JSON, or JSONP |
| `freshness_model` | Warehouse/reporting refresh, typically weekly |
| `stable_ids` | EPA registry ID, NPDES ID, facility/program identifiers |
| `usage_constraints` | Use bulk downloads for large-volume analytics; avoid hammering web services |

## Idiomatic call patterns

- Use facility lookup, permit lookup, and report endpoints for interactive enrichment.
- Redirect bulk analytical needs to ECHO bulk downloads.
- Preserve ICIS-NPDES identity and receiving-water context from ATTAINS where included.
- Store refresh/report period separately from retrieval time.

## Return contract

Return facility identity, raw and normalized permit identifiers, coordinate CRS/quality, program metadata, compliance status, receiving-water context, refresh/report period, source endpoint, query parameters, and access date.

## Known gotchas

- NPDES identifiers can appear in multiple formats; preserve raw and normalized values.
- Facility coordinates may be approximate or missing.
- Compliance status is time-sensitive; store access date and reporting period.
- ECHO is an API in front of a warehouse. Do not treat it as a live operational feed.
- Large-volume retrieval through web services can be throttled or banned for misuse; use bulk downloads.

## Integration with StormwaterIQ

ECHO supports compliance intelligence, permit context, adjacent facility discovery, and customer site enrichment. Derived records should be tenant-scoped when attached to a customer workflow.

## Validation checklist

- [ ] Raw permit ID and normalized permit ID are both retained.
- [ ] Coordinate quality/nullability is represented.
- [ ] Compliance status includes period/access date.
- [ ] External facility data is not treated as tenant-owned inspection data.
- [ ] Endpoint family is recorded.
- [ ] Bulk analytical needs are routed to bulk downloads.

## References

- https://echo.epa.gov/tools/web-services
- Accessed: 2026-05-08
