# PMTiles

## When to use

Use for single-file tile archives, offline overlays, static storage tile distribution, HTTP range-request tile reads, PMTiles metadata, and PMTiles v3 compatibility.

## Canonical data model

TODO: Define PMTiles archive metadata, tile type, bounds, min/max zoom, vector layer metadata, storage path, and cache policy schemas.

## CRS, units, precision

PMTiles stores tiled data addressed by Z/X/Y. Preserve source tiling scheme, bounds, min/max zoom, and metadata. Rendering commonly assumes Web Mercator tiles; source data CRS must be declared separately if encoded in vector tile attributes or metadata.

## Idiomatic call patterns

TODO: Add examples for generating archives, validating headers/metadata, serving from Supabase Storage or static object storage, and using JS readers with Mapbox/MapLibre-style clients.

## Return contract

Return archive path/URL, spec version, tile type, bounds, min/max zoom, metadata JSON, source provenance, and cache invalidation tag.

## Known gotchas

- PMTiles is read-only; updating requires rewriting the archive.
- Current PMTiles specification version is v3; the archive version byte is `0x03`.
- Range request support is required for efficient remote reads.
- Use PostGIS + `ST_AsMVT` or a database when transactional tile updates are required.

## Integration with StormwaterIQ

Use for offline overlays and derived tile products in Supabase Storage or static object storage. Treat PMTiles as derived artifacts over Supabase/PostGIS records.

## Validation checklist

- [ ] Archive spec version, bounds, and min/max zoom are recorded.
- [ ] Hosting supports HTTP range requests.
- [ ] Source data provenance is attached.
- [ ] Rebuild/invalidation policy is documented.

## References

- https://docs.protomaps.com/pmtiles
- https://github.com/protomaps/PMTiles/blob/main/spec/v3/spec.md
- Accessed: 2026-05-08
