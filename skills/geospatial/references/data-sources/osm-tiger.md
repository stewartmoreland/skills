# OpenStreetMap And TIGER

## When to use

Use for basemap supplements, geocoding/context, address/place lookup, road and boundary context, Census TIGER/TIGERweb reference layers, and tasks mentioning OSM, Nominatim, TIGERweb, TIGER/Line, GeoServices REST, shapefiles, geodatabases, or GeoPackages.

## Canonical data model

```ts
type BasemapContextFeature = {
  source: "OpenStreetMap" | "Census TIGER";
  provider: string;
  service: "nominatim" | "osm_tiles" | "osm_data" | "tigerweb" | "tiger_line_download";
  stableId?: string;
  layer?: string;
  vintage?: string;
  geometry?: GeoJSON.Geometry;
  crs: string;
  usagePolicy?: string;
  retrievedAt: string;
};
```

## CRS, units, precision

OSM data and geocoding outputs are typically longitude/latitude. OSM public tiles are Web Mercator display tiles. TIGERweb services expose CRS through ArcGIS REST metadata, while TIGER/Line download products publish their own dataset metadata. Preserve service CRS and vintage.

## Service contract

| Source | Contract |
|--------|----------|
| OSM data | Open data, can be core product input when licensed and sourced correctly |
| OSM public tiles | Public shared infrastructure, not a general-purpose production CDN |
| Nominatim public service | Public shared geocoding service with explicit usage policy |
| TIGERweb | Census GeoServices REST reference layers |
| TIGER/Line | Full-detail downloadable source products such as shapefiles, geodatabases, and GeoPackages |

## Idiomatic call patterns

- Distinguish data license/source from hosted public service policy.
- Use self-hosted, commercial, or policy-compliant geocoding/tiles for production load.
- Preserve OSM object IDs (`osm_type`, `osm_id`) where provided.
- Preserve Census `GEOID`, layer, and vintage for TIGER-derived features.

## Return contract

Return features with source, provider/service, stable ID, CRS, layer/vintage, usage policy boundary, endpoint, and retrieval time.

## Known gotchas

- Public OSM tile servers and Nominatim are not default production infrastructure.
- The Nominatim public-server policy is not the same as running your own Nominatim instance.
- TIGERweb services and TIGER/Line downloads are different products with different freshness and completeness.
- Basemap/context data should not overwrite Supabase/PostGIS platform records without an explicit reconciliation workflow.

## Integration with StormwaterIQ

Use OSM/TIGER for context, supplemental basemaps, geocoding, and reference layers. Treat Supabase/PostGIS as the platform source of record for customer and compliance data.

## Validation checklist

- [ ] Source and hosted provider are named separately.
- [ ] Usage policy constraints are documented for public OSM services.
- [ ] OSM IDs or Census GEOIDs are preserved when available.
- [ ] TIGER vintage/layer is recorded.
- [ ] Data is not promoted to platform source of record without reconciliation.

## References

- https://www.openstreetmap.org/
- https://operations.osmfoundation.org/policies/tiles/
- https://operations.osmfoundation.org/policies/nominatim/
- https://tigerweb.geo.census.gov/
- https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- Accessed: 2026-05-08
