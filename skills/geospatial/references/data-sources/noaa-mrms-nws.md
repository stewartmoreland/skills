# NOAA MRMS And NWS Weather.gov

## When to use

Use for real-time radar QPE, precipitation estimates, NWS forecasts, watches/warnings/advisories, weather alerts, and storm-event context.

## Canonical data model

Treat MRMS and Weather.gov as related but separate contracts:

```ts
type MrmsRasterProduct = {
  source: "NOAA MRMS";
  productName: string;
  validTime: string;
  accumulationWindow?: string;
  nativeFormat: "GRIB2" | "GeoTIFF" | "other";
  crs: string;
  bounds?: [number, number, number, number];
  units: Record<string, string>;
  retrievedAt: string;
};

type WeatherGovFeature = {
  source: "NWS Weather.gov";
  endpoint: "points" | "forecast" | "forecastHourly" | "alerts" | "stations" | "observations" | string;
  point?: { longitude: number; latitude: number; crs: "EPSG:4326" };
  office?: string;
  gridX?: number;
  gridY?: number;
  zoneId?: string;
  alertId?: string;
  contentType: "geojson" | "json-ld" | "cap" | "atom" | "xml";
  issuedAt?: string;
  retrievedAt: string;
};
```

## CRS, units, precision

MRMS CRS and units are product metadata; do not infer them from the product family. Weather.gov point discovery uses `EPSG:4326`; forecast grid identity is office/grid coordinates discovered through `/points`. Alert geometries are GeoJSON when requested as GeoJSON.

Declare rainfall, snow, probability, temperature, wind, and forecast units per endpoint before combining with hydrology or inspection workflows.

## Service contracts

| Source | Contract |
|--------|----------|
| MRMS | High-cadence multi-radar/multi-sensor raster products, operational materials commonly use GRIB2 and some GeoTIFF products; public descriptions cite about two-minute product updates. |
| Weather.gov API | Forecast/alert/observation API requiring a meaningful User-Agent header. Defaults many endpoints to GeoJSON and supports JSON-LD, CAP, Atom, and NOAA XML variants. |

## Idiomatic call patterns

- For Weather.gov, first call `/points/{lat},{lon}` to resolve forecast office and grid coordinates, then call the grid/forecast endpoint.
- Treat `/points` resolution as a discovery step, not a permanent identity. Refresh it periodically because office/grid mappings can change.
- Do not attempt to fetch radar display data from `api.weather.gov`; use MRMS or other radar/tile services for raster precipitation.
- For MRMS, select by product name and valid time. Cache based on the product cadence and always keep source valid time separate from retrieval time.

Example Weather.gov provenance shape:

```ts
const nwsRequest = {
  endpoint: "points",
  userAgent: "StormwaterIQ contact@example.com",
  point: { longitude: -84.39, latitude: 33.75, crs: "EPSG:4326" as const },
};
```

## Return contract

Return artifact plus source (`NOAA MRMS` or `NWS Weather.gov`), endpoint/product name, CRS, time window or valid time, issue time when available, unit declarations, source URL, retrieval timestamp, and transformation steps.

## Known gotchas

- NWS APIs require a meaningful User-Agent header.
- Radar QPE is time-sensitive; never cache as if it were static reference data.
- Forecast grids, alert polygons, and radar rasters have different spatial models.
- `/points` maps lat/lon to an office/grid identity that can change.
- Weather.gov can provide GeoJSON/JSON-LD/CAP/Atom/XML response variants; preserve `contentType`.
- MRMS source valid time and retrieval time are different audit fields.

## Integration with StormwaterIQ

Weather data informs risk intelligence, inspection timing, event context, and rainfall-derived compliance workflows. Persist derived summaries with source timestamp and tenant/site scope.

## Validation checklist

- [ ] Source timestamp and retrieval timestamp are both recorded.
- [ ] Units are declared before joining with hydrology calculations.
- [ ] Alert polygons and raster grids include CRS/bounds metadata.
- [ ] Cache TTL matches product refresh cadence.
- [ ] Weather.gov requests include a meaningful User-Agent.
- [ ] `/points` discovery output is not treated as permanent identity.

## References

- https://www.weather.gov/documentation/services-web-api
- https://mrms.nssl.noaa.gov/
- Accessed: 2026-05-08
