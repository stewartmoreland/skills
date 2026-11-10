# Mapbox APIs

## When to use

Use for Mapbox tiles, terrain-dem, geocoding, static images, directions/isochrones, style URLs, access tokens, and map-derived UI services.

## Canonical data model

```ts
type MapboxApiArtifact = {
  source: "Mapbox";
  endpointFamily: "geocoding" | "isochrone" | "static_images" | "tiles" | "terrain_dem";
  tokenClass: "public_pk" | "secret_sk";
  requestParams: Record<string, unknown>;
  geometry?: GeoJSON.Geometry | GeoJSON.Feature | GeoJSON.FeatureCollection;
  tile?: { z: number; x: number; y: number; tileset: string };
  styleId?: string;
  tilesetId?: string;
  crs: "EPSG:4326" | "EPSG:3857" | "endpoint_specific";
  retrievedAt: string;
};
```

## CRS, units, precision

Mapbox tiles render in Web Mercator (`EPSG:3857`), while API GeoJSON coordinates are longitude/latitude (`EPSG:4326`) unless documented otherwise.

Geocoding and Isochrone return geographic GeoJSON features. Static Images are rendered artifacts. Terrain-DEM is raster-dem tile infrastructure where `{z}/{x}/{y}` tile identity is part of the data model.

## Endpoint-family contracts

| Endpoint family | Geometry semantics | Token rule |
|-----------------|--------------------|------------|
| Geocoding | Geographic coordinates and GeoJSON features | Public token can be browser-side when scopes permit; secret operations server-side only. |
| Isochrone | GeoJSON FeatureCollection | Keep profile, contours, minutes/meters, and generalization parameters. |
| Static Images | Rendered image, not source geometry | Pin style, overlays, dimensions, and scale. |
| Tiles | Web Mercator tile pyramid | Preserve tileset/style IDs and zoom/x/y. |
| Terrain-DEM | Raster-dem Web Mercator tiles | Use tile semantics, not lat/lon point-sample assumptions. |

## Idiomatic call patterns

- Use public `pk` tokens only for public scopes and browser/mobile-safe operations.
- Keep secret `sk` tokens server-side.
- Pin style URLs and tileset IDs for reproducible compliance exhibits.
- Preserve endpoint family; Mapbox is a platform layer, not a single homogeneous data source.

## Return contract

Return endpoint family, source URL/style ID, tileset ID when relevant, token class used (public vs secret, never token value), CRS, bounds or tile identity, units, request params, and cache policy.

## Known gotchas

- Treat `EPSG:3857` as display-only.
- Never put secret Mapbox tokens in mobile or browser bundles.
- Style and tileset versions should be pinned for reproducible compliance exhibits.
- Terrain-DEM is a tiled raster-dem workflow, not a point-query elevation service.
- Geocoding outputs should not overwrite platform addresses/geometries without reconciliation.

## Integration with StormwaterIQ

Mapbox powers derived map UI for web and mobile. Supabase/PostGIS remains the source of record.

## Validation checklist

- [ ] Token class is correct for runtime.
- [ ] Secret-token workflows are server-side only.
- [ ] Endpoint family is recorded.
- [ ] Style URL/version is pinned when reproducibility matters.
- [ ] CRS is declared when converting API output to persisted geometry.
- [ ] Cache policy respects Mapbox API terms and product needs.

## References

- https://docs.mapbox.com/api/
- https://docs.mapbox.com/mapbox-gl-js/
- Accessed: 2026-05-08
