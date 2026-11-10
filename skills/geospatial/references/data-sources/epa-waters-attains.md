# EPA WATERS And ATTAINS

## When to use

Use for NHDPlus, catchments, flowlines, HUC8/HUC10/HUC12, impaired waters, 303(d), assessment units, and tasks mentioning EPA WATERS or ATTAINS.

## Canonical data model

Preserve WATERS and ATTAINS as separate sub-contracts inside this compatibility reference:

```ts
type WatersFeature = {
  source: "EPA WATERS";
  endpointFamily: "nhdplus" | "huc" | "program_layer" | "mapping_service";
  comid?: string;
  reachcode?: string;
  huc?: string;
  hucLevel?: "HUC8" | "HUC10" | "HUC12" | string;
  layerId?: string;
  geometry?: GeoJSON.Geometry;
  crs: string;
  retrievedAt: string;
};

type AttainsAssessment = {
  source: "EPA ATTAINS";
  assessmentUnitId: string;
  organizationId?: string;
  cycleYear: number;
  finalActionStatus?: string;
  impairmentStatus?: string;
  causes?: string[];
  tmdlStatus?: string;
  retrievedAt: string;
};
```

## CRS, units, precision

WATERS/NHDPlus services can expose JSON/GeoJSON and WMS/WFS layers; mapping-service documentation includes preprojected Web Mercator layers for performance. ATTAINS is JSON REST assessment/TMDL cycle data. Confirm CRS per endpoint and preserve advertised CRS in the envelope.

## Service contracts

| Source | Contract |
|--------|----------|
| WATERS | REST-like services built on NHDPlus and indexed program data; also mapping layers via WMS/WFS, including NPDES, 303(d), 305(b), and TMDL layers. |
| ATTAINS | State assessment/TMDL system; public JSON REST today, with April 2026 guidance that web services will soon require a free API key. |

## Idiomatic call patterns

- Use WATERS for reach-indexed hydrography, HUC context, and indexed program layers.
- Use ATTAINS for assessment-unit, impairment, TMDL, cycle-year, and EPA final-action status.
- Keep WATERS feature IDs (`comid`, `reachcode`, HUC) separate from ATTAINS assessment-unit IDs.
- Treat ATTAINS auth as an operational watch item; do not hard-code an API-key cutover until EPA finalizes it.

## Return contract

Return source sub-contract (`EPA WATERS` or `EPA ATTAINS`), feature identifiers, HUC level, assessment unit ID when relevant, impairment/TMDL status, final-action status, CRS, reporting cycle, source endpoint, auth mode/watch item, and access date.

## Known gotchas

- HUC8/HUC10/HUC12 are not interchangeable; preserve the level.
- ATTAINS endpoint schemas can differ by reporting cycle and geography.
- NHDPlus feature IDs and assessment-unit IDs serve different purposes.
- WATERS mapping layers may be preprojected to Web Mercator for performance; do not assume analytics CRS.
- ATTAINS geospatial data can update twice per assessment cycle and periodically as exports.
- ATTAINS API-key requirements are a watch item as of April 2026 guidance.

## Integration with StormwaterIQ

EPA WATERS/ATTAINS supports watershed context, impaired-water proximity, regulatory risk, and compliance reporting. Persist derived intersections with HUC level and reporting cycle.

## Validation checklist

- [ ] HUC level is explicit.
- [ ] Reporting cycle is stored with impairment data.
- [ ] CRS is confirmed from endpoint response.
- [ ] Feature IDs are not conflated across NHDPlus and ATTAINS.
- [ ] ATTAINS final-action status is preserved.
- [ ] Auth transition status is documented when implementing live calls.

## References

- https://www.epa.gov/waterdata/waters-web-services
- https://www.epa.gov/waterdata/attains
- Accessed: 2026-05-08
