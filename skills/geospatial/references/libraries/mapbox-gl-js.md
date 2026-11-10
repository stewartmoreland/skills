# Mapbox GL JS

## When to use

Use for web map sources, layers, expressions, interactions, controls, style URLs, custom sources, PMTiles rendering, and Mapbox GL JS v3 behavior.

## Canonical data model

TODO: Define canonical source, layer, expression, style URL, feature-state, and event-handler patterns for `apps/web`.

## CRS, units, precision

Mapbox GL JS renders in Web Mercator. Source GeoJSON should be longitude/latitude. Do not use rendered coordinates as authoritative stored geometry.

## Idiomatic call patterns

TODO: Add examples for source/layer creation, expression typing, hover/click feature IDs, and style URL pinning. Mapbox GL JS current major version is v3; latest observed release during authoring was v3.23.x.

## Return contract

For generated map config, return style ID/version, source definitions, layer IDs, data CRS assumptions, token class, and interaction behavior.

## Known gotchas

- Layer order and source/layer IDs are part of the API contract for UI tests.
- Mapbox expressions are typed; invalid expression shapes fail at runtime.
- Web Mercator display is not measurement truth.

## Integration with StormwaterIQ

Use in `apps/web` map UI. Consume derived GeoJSON/vector tiles from API/PostGIS; do not make the map client the system of record.

## Validation checklist

- [ ] Source/layer IDs are stable.
- [ ] Token class is browser-safe.
- [ ] Style URL/version is pinned where reproducibility matters.
- [ ] Data CRS assumptions are documented.

## References

- https://docs.mapbox.com/mapbox-gl-js/
- Accessed: 2026-05-08
