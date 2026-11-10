# Mapbox Maps SDK For React Native

## When to use

Use for Expo/React Native map rendering, offline map packs, native location display, style URL pinning, mobile map interactions, and field inspection map UI.

## Canonical data model

TODO: Define offline pack manifest, style URL, source/layer, region bounds, and field-inspection map state schemas.

## CRS, units, precision

Mobile map rendering is Web Mercator display over longitude/latitude data. Offline regions should store bounds in `EPSG:4326` and rendered tiles in the SDK's native tile system.

## Idiomatic call patterns

TODO: Add examples for offline pack setup, style URL pinning, camera bounds, and safe token injection in Expo.

## Return contract

Return offline manifest, style ID/version, region bounds, source/layer IDs, token class, and cache/update policy.

## Known gotchas

- Never embed privileged tokens in mobile bundles.
- Offline packs must be versioned with style and tileset assumptions.
- Field workflows need deterministic retries and conflict-safe sync; maps should consume queued/local data without privileged credentials.

## Integration with StormwaterIQ

Use in `apps/inspector-native` for field inspection context. Privileged spatial operations should route through API or worker services.

## Validation checklist

- [ ] Token is mobile-safe.
- [ ] Offline manifest includes style and bounds.
- [ ] Local/offline data has provenance and sync status.
- [ ] Map display does not perform privileged server operations.

## References

- https://docs.mapbox.com/ios/maps/
- https://docs.mapbox.com/android/maps/
- https://rnmapbox.github.io/
