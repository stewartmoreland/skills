# USGS Water Data

## When to use

Use for NWIS/Water Data streamflow, gage observations, water-quality observations, site metadata, hydrograph context, and upstream/downstream monitoring.

## Canonical data model

```ts
type UsgsWaterObservation = {
  source: "USGS Water Data";
  endpointFamily: "continuous" | "daily" | "field_measurements" | "metadata" | "monitoring_locations" | "time_series";
  monitoringLocationId: string;
  parameterCode: string;
  statisticCode?: string;
  observedAt: string;
  value: number | string | null;
  unit: string;
  qualifier?: string;
  approvalStatus?: "provisional" | "approved" | "unknown";
  timeWindow: { start: string; end: string };
  retrievedAt: string;
};
```

## CRS, units, precision

Monitoring locations are geographic point features unless endpoint metadata says otherwise. Preserve parameter codes, statistic codes, units, qualifiers, and approval/provisional status. Do not replace parameter codes with display labels.

## Endpoint families

| Endpoint family | Contract |
|-----------------|----------|
| Continuous values | Sensor-driven observations; often high-frequency but telemetry can lag. Query bounded windows. |
| Daily values | Aggregated daily statistics keyed by parameter/statistic. |
| Field measurements | Discrete field visit measurements. |
| Metadata | Site, parameter, and time-series descriptions. |
| Monitoring locations | Station discovery and geometry. |
| Time-series discovery | Finds available observation series for a location/parameter. |

## Idiomatic call patterns

- Query `/continuous` in bounded windows. Split large spans; model three years as a maximum guidance for continuous requests.
- Treat `latest available` as latest published by USGS, not same-minute real time.
- Store telemetry/approval status and qualifiers alongside values.
- Use monitoring-location and time-series discovery before assuming a parameter exists at a gage.

## Return contract

Return endpoint family, site ID, parameter code, statistic code, units, value qualifier, approval status, observed time, time window, CRS, source URL, and retrieval timestamp.

## Known gotchas

- USGS parameter codes are part of the data model, not display labels.
- Gage time zones and provisional/approved status matter for audit use.
- Water quality and streamflow endpoints have different schemas.
- High-frequency observations are not equivalent to same-minute real time.
- Telemetry can be hourly at many sites and more frequent during flood/emergency transmission.

## Integration with StormwaterIQ

USGS observations support watershed context, baseline hydrology, water-quality risk intelligence, and event validation near customer sites.

## Validation checklist

- [ ] Parameter code and unit are stored with every observation.
- [ ] Observation timestamp and timezone are preserved.
- [ ] Provisional/approved status is not dropped.
- [ ] Site geometry includes CRS and source metadata.
- [ ] Continuous queries use bounded windows.
- [ ] Large spans are split instead of requested as one unbounded query.

## References

- https://waterservices.usgs.gov/
- https://api.waterdata.usgs.gov/
- Accessed: 2026-05-08
