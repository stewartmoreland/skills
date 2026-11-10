# Tomorrow.io

## When to use

Use for premium weather augmentation, commercial forecast/weather-map access, resiliency beyond NOAA sources, higher feature coverage, or SLA-driven weather workflows.

## Canonical data model

```ts
type TomorrowIoWeatherResult = {
  source: "Tomorrow.io";
  endpointFamily: "weather_json" | "weather_maps";
  location?: { longitude: number; latitude: number; crs: "EPSG:4326" };
  tile?: { z: number; x: number; y: number; layer: string };
  fields: string[];
  timestep?: string;
  issuedAt?: string;
  retrievedAt: string;
  planOrAccessClass?: string;
  units: Record<string, string>;
};
```

## CRS, units, precision

JSON weather endpoints use explicit locations, typically longitude/latitude. Weather Maps are tiled products, so reason in `{z}/{x}/{y}` and preserve tile layer, zoom, and bounds. Units, cadence, available fields, and history/forecast ranges can vary by endpoint and plan; record them in provenance.

## Service contract

| Field | Contract |
|-------|----------|
| `auth_mode` | API key |
| `request_shape` | point/location JSON queries or weather map tiles |
| `native_format` | JSON and map tiles |
| `freshness_model` | commercial forecast/observation products; plan dependent |
| `stable_ids` | location, field, timestep, layer, issued time |
| `usage_constraints` | plan, quota, and product access constraints apply |

## Idiomatic call patterns

- Use Tomorrow.io as a named provider, never as an unnamed NOAA fallback.
- Store endpoint family, fields requested, timestep, issued time, retrieved time, and plan/access class.
- Keep Weather Maps as display or derived map products unless separately validated for analytics.
- Reconcile units before combining Tomorrow.io data with Atlas 14, MRMS, or USGS Water Data.

## Return contract

Return weather values or tile references with provider, endpoint family, auth class, location/tile identity, field list, units, issue time, retrieval time, and plan/access constraints.

## Known gotchas

- Do not normalize Tomorrow.io forecast outputs into NOAA forecast semantics without source attribution.
- Forecast issuance time and retrieval time are different audit fields.
- Commercial plan limits are part of the data model because they determine available fields, cadence, and permitted use.
- Weather Maps are tile products, not point-query grids.

## Integration with StormwaterIQ

Tomorrow.io is a premium supplemental provider for weather resiliency, commercial SLA needs, or product experiences that NOAA sources do not cover. NOAA remains the default public-source path unless product requirements explicitly choose Tomorrow.io.

## Validation checklist

- [ ] API key use is server-side or otherwise appropriate for the runtime.
- [ ] Provider, endpoint family, fields, and plan/access class are preserved.
- [ ] Issued time and retrieved time are both recorded when available.
- [ ] Units are declared before combining with NOAA or hydrology data.
- [ ] Tomorrow.io data is not silently substituted for NOAA data.

## References

- https://docs.tomorrow.io/
- https://www.tomorrow.io/weather-api/
- Accessed: 2026-05-08
