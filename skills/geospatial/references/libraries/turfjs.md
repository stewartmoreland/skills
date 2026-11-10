# turf.js

## When to use

Use for lightweight client-side GeoJSON geometry operations: display buffers, approximate distances, quick intersections, bounding boxes, centroids, and map interaction helpers.

## Canonical data model

Turf inputs must be GeoJSON in longitude/latitude (`EPSG:4326`):

```ts
type TurfInput = GeoJSON.Feature | GeoJSON.FeatureCollection | GeoJSON.Geometry;
```

Attach metadata outside the GeoJSON object when the operation feeds persisted platform data.

## CRS, units, precision

Turf assumes GeoJSON coordinate order `[longitude, latitude]`. Use exact Turf unit strings such as `meters`, `kilometers`, `miles`, `feet`, and `acres` as supported by the called function.

Do not pass Web Mercator tile coordinates, projected PostGIS coordinates, or local engineering coordinates into Turf unless the function explicitly supports planar coordinates and the reference documents why it is safe.

## Idiomatic call patterns

```ts
import { area, buffer, centroid } from "@turf/turf";

const center = centroid(siteBoundary);
const inspectionRadius = buffer(center, 100, { units: "meters" });
const siteAreaSqM = area(siteBoundary);
```

Use Turf for UI responsiveness and lightweight approximations. Round-trip to PostGIS for authoritative compliance measurements, tenant-scoped joins, large datasets, or audit-grade outputs.

## Return contract

If Turf output is persisted or used in reports, wrap it with CRS, units, source feature IDs, Turf function name, parameters, and a note that the operation ran client-side.

## Known gotchas

- `EPSG:4326` GeoJSON is the silent killer: Turf will happily process wrong coordinate systems and return plausible nonsense.
- Units are strings and not interchangeable. Be explicit in every call.
- Turf is not a substitute for PostGIS on large feature sets or tenant-sensitive data.
- Client-side results can drift from server-side calculations if simplification, projection, or precision differs.
- Do not expose privileged or cross-tenant geometry to the browser just to use Turf.

## Integration with StormwaterIQ

Use Turf in web or mobile clients for interaction affordances, previews, and non-authoritative derived UI. Persist authoritative geometry, spatial joins, compliance summaries, and report values from API/PostGIS/worker paths.

## Validation checklist

- [ ] Inputs are confirmed `EPSG:4326` GeoJSON.
- [ ] Unit strings are explicit.
- [ ] Result is labeled approximate unless server-side verified.
- [ ] Large or tenant-sensitive operations are pushed to PostGIS/API.
- [ ] Persisted outputs include provenance and source feature IDs.

## References

- https://turfjs.org/
- https://turfjs.org/docs/
