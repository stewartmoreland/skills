# NOAA Atlas 14 PFDS

## When to use

Use for precipitation frequency, IDF/DDF values, recurrence intervals, storm depth tables, NOAA PFDS point queries, and tasks mentioning Atlas 14 or Atlas 15 migration.

## Canonical data model

```ts
type Atlas14DepthTable = {
  source: "NOAA Atlas 14 PFDS";
  queryPoint: { longitude: number; latitude: number; crs: "EPSG:4326" };
  unit: "inches";
  volume: string;
  version?: string;
  series: "partial_duration" | "annual_maximum" | "unknown";
  csvExportType: "estimates" | "upper_confidence" | "lower_confidence" | "combined";
  recurrenceIntervalYears: 1 | 2 | 5 | 10 | 25 | 50 | 100 | 200 | 500 | 1000;
  durations: Record<string, number | null>;
  confidence?: {
    lower?: Record<string, number | null>;
    upper?: Record<string, number | null>;
  };
  accessedAt: string;
};
```

Durations span short-duration storm events through multi-day values; preserve PFDS duration labels rather than inventing local names. Preserve `volume`, `version`, `series`, and CSV export type because the same point can be represented as estimates, upper bounds, lower bounds, or combined outputs.

## Service contract

| Field | Contract |
|-------|----------|
| `auth_mode` | None |
| `request_shape` | Decimal-degree lat/lon point query |
| `native_format` | PFDS table and CSV export |
| `native_crs` | `EPSG:4326` point query |
| `freshness_model` | Published design-storm source, not real-time weather |
| `stable_ids` | Volume, version, series, recurrence interval, duration |
| `provenance_granularity` | Query point plus Atlas volume/version/series |

## CRS, units, precision

PFDS point queries use latitude/longitude (`EPSG:4326`). Native precipitation depth is inches. Convert explicitly when downstream calculations require millimeters.

## Idiomatic call patterns

Call PFDS by point, parse CSV/table responses into typed durations, and store the original query coordinate:

```ts
const point = { longitude: -84.39, latitude: 33.75, crs: "EPSG:4326" as const };
// Query PFDS, parse rows into recurrence interval x duration depth table.
```

Keep recurrence interval and duration as separate dimensions; do not flatten them into ambiguous column names without metadata.

## Return contract

Return query point, PFDS URL or request parameters, volume, version, series, CSV export type, recurrence interval, duration labels, units, confidence bounds when available, and access date.

## Known gotchas

- Atlas 14 remains the PFDS-backed standard in many workflows, but NOAA Atlas 15 is under development and is intended to replace Atlas 14.
- NOAA's Atlas 15 information page says preliminary CONUS estimates are expected by September 2026; do not assume Atlas 15 values are production inputs until the project requirement explicitly switches.
- Atlas 14 is a published design-storm source. It is not MRMS, Weather.gov, or a real-time precipitation feed.
- Atlas 14 depths are inches. Unit mistakes immediately break the StormwaterIQ +/-2% parity target.
- Some locations have region/volume-specific metadata. Preserve volume or station metadata when returned.

## Integration with StormwaterIQ

Atlas 14 feeds design storm depths, hydrology calculations, watershed/subcatchment analysis, risk intelligence, and report exhibits. Store PFDS-derived values with access date and query coordinate so changes in future NOAA standards can be audited.

## Validation checklist

- [ ] Query point is `EPSG:4326` and preserved.
- [ ] Depth unit is explicitly inches or explicitly converted.
- [ ] Recurrence intervals and durations remain separate dimensions.
- [ ] Volume, version, series, and CSV export type are recorded.
- [ ] Access date and PFDS request parameters are recorded.
- [ ] Atlas 15 migration assumptions are not silently mixed into Atlas 14 outputs.

## References

- https://hdsc.nws.noaa.gov/pfds/
- https://water.noaa.gov/about/atlas15
- Accessed: 2026-05-08
