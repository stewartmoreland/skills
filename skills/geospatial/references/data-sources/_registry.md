# External Data Source Registry

This registry is the first stop for external geospatial service integration. Each record describes a materially different access mode; do not collapse sources that differ by authentication, transport, CRS, freshness, or operational limits.

## Required Contract Fields

Every source or adapter record must declare:

```yaml
source_name: string
official_base_endpoint: string
auth_mode: none | user_agent | public_token | secret_token | api_key | varies
request_shape: point | bbox | polygon | tile | rowset_sql | report | bulk_download | adapter_specific
native_format: csv | json | geojson | json_ld | cap | atom | xml | grib2 | geotiff | wms | wcs | wfs | arcgis_rest | mixed
native_crs: string
advertised_crs: string
freshness_model: string
operational_latency_model: string
stable_ids: string[]
pagination_windowing: string
usage_constraints: string[]
provenance_granularity: string
provenance_fields: string[]
reference_file: string
```

## Registry Records

```yaml
- id: noaa_pfds
  source_name: NOAA Atlas 14 PFDS
  official_base_endpoint: https://hdsc.nws.noaa.gov/pfds/
  auth_mode: none
  request_shape: point
  native_format: csv
  native_crs: EPSG:4326 point query
  advertised_crs: EPSG:4326
  freshness_model: published design-storm volumes, not live weather
  operational_latency_model: static lookup; changes only by NOAA publication/version
  stable_ids: [volume, version, series, duration, recurrence_interval]
  pagination_windowing: none
  usage_constraints: [preserve confidence interval export type, do not treat as real-time feed]
  provenance_granularity: query point plus Atlas volume/version/series
  provenance_fields: [volume, version, series, units, duration, recurrence_interval, csv_export_type, accessed_at]
  reference_file: noaa-atlas14.md

- id: noaa_mrms
  source_name: NOAA MRMS
  official_base_endpoint: https://mrms.nssl.noaa.gov/
  auth_mode: none
  request_shape: raster_product
  native_format: grib2
  native_crs: product metadata
  advertised_crs: product metadata
  freshness_model: high-cadence operational raster products, often about two minutes
  operational_latency_model: near-real-time but product/time dependent
  stable_ids: [product_name, valid_time, accumulation_window]
  pagination_windowing: product/time window selection
  usage_constraints: [do not confuse with Weather.gov forecasts, preserve product time]
  provenance_granularity: product name plus valid time
  provenance_fields: [product_name, valid_time, accumulation_window, format, source_url, retrieved_at]
  reference_file: noaa-mrms-nws.md

- id: nws_api_weathergov
  source_name: NWS Weather.gov API
  official_base_endpoint: https://api.weather.gov/
  auth_mode: user_agent
  request_shape: point_discovery_then_grid_or_alert
  native_format: mixed
  native_crs: EPSG:4326 for point inputs and GeoJSON geometries
  advertised_crs: GeoJSON, JSON-LD, CAP, Atom, NOAA XML depending on endpoint
  freshness_model: forecast/alert lifecycle, not radar display
  operational_latency_model: office/grid mapping may change; refresh /points resolution periodically
  stable_ids: [office, gridX, gridY, alert_id, zone_id]
  pagination_windowing: endpoint-specific paging and time filters
  usage_constraints: [meaningful User-Agent required, radar display data not served by API]
  provenance_granularity: point resolution plus endpoint response timestamp
  provenance_fields: [point, office, gridX, gridY, endpoint, content_type, issued_at, retrieved_at]
  reference_file: noaa-mrms-nws.md

- id: tomorrow_io
  source_name: Tomorrow.io
  official_base_endpoint: https://api.tomorrow.io/
  auth_mode: api_key
  request_shape: point_or_tile
  native_format: mixed
  native_crs: EPSG:4326 for JSON locations; Web Mercator tile coordinates for weather maps
  advertised_crs: endpoint-specific
  freshness_model: commercial forecast and map-tile products, plan dependent
  operational_latency_model: premium augmentation path; SLA and cadence depend on plan
  stable_ids: [location, timestep, field, layer, issued_time]
  pagination_windowing: endpoint and plan dependent
  usage_constraints: [do not silently substitute for NOAA, preserve plan constraints]
  provenance_granularity: provider, endpoint, issue time, plan/access class
  provenance_fields: [provider, endpoint, fields, timestep, issued_at, retrieved_at, plan_or_access_class]
  reference_file: tomorrow-io.md

- id: usgs_3dep_tnm
  source_name: USGS 3DEP via The National Map
  official_base_endpoint: https://www.usgs.gov/3d-elevation-program
  auth_mode: none
  request_shape: raster_product
  native_format: geotiff
  native_crs: product-class-specific
  advertised_crs: product metadata, WMS, WCS
  freshness_model: product publication, not live feed
  operational_latency_model: availability depends on product class and coverage
  stable_ids: [product_class, tile_id, acquisition_date, publication_date]
  pagination_windowing: tile/product selection
  usage_constraints: [read CRS from metadata, reject single-CRS assumptions]
  provenance_granularity: product class plus asset URL
  provenance_fields: [source_provider, product_class, asset_url, crs, resolution, vertical_unit, accessed_at]
  reference_file: usgs-3dep.md

- id: usgs_3dep_opentopography
  source_name: USGS 3DEP via OpenTopography
  official_base_endpoint: https://portal.opentopography.org/apidocs/
  auth_mode: api_key
  request_shape: bbox
  native_format: geotiff
  native_crs: product-class-specific
  advertised_crs: endpoint-specific
  freshness_model: wrapper over source products
  operational_latency_model: request-size, quota, and eligibility constrained
  stable_ids: [demtype, bbox, output_format]
  pagination_windowing: request bounds and API limits
  usage_constraints: [free-key limits, some 1m access restricted by eligibility, preserve source_provider]
  provenance_granularity: wrapper request plus underlying product class
  provenance_fields: [source_provider, demtype, bbox, api_endpoint, quota_class, retrieved_at]
  reference_file: usgs-3dep.md

- id: nrcs_ssurgo_sda
  source_name: NRCS SSURGO Soil Data Access
  official_base_endpoint: https://sdmdataaccess.nrcs.usda.gov/
  auth_mode: none
  request_shape: rowset_sql
  native_format: mixed
  native_crs: WGS84, NAD83, or Web Mercator depending on service variant
  advertised_crs: EPSG:4326, EPSG:4269, EPSG:3857
  freshness_model: NRCS publication/refresh cycle
  operational_latency_model: query and row-count bounded
  stable_ids: [mukey, cokey, chkey]
  pagination_windowing: 100000-row cap; persistent AOIs last at least 24 hours
  usage_constraints: [fail closed on unbounded national queries, preserve SQL and service variant]
  provenance_granularity: SQL query plus service variant
  provenance_fields: [query_language, response_shape, pAOI_token, spatial_service_variant, sql, retrieved_at]
  reference_file: nrcs-ssurgo.md

- id: mrlc_nlcd
  source_name: MRLC NLCD
  official_base_endpoint: https://www.mrlc.gov/
  auth_mode: none
  request_shape: raster_product
  native_format: mixed
  native_crs: EPSG:5070
  advertised_crs: WMS/WCS advertised CRS list
  freshness_model: product-year-driven annual or multi-year publication
  operational_latency_model: not a live feed
  stable_ids: [product_year, collection, legend_version, class_code]
  pagination_windowing: WMS/WCS or product download limits
  usage_constraints: [preserve product_year, collection, legend_version, class_domain]
  provenance_granularity: product year and collection
  provenance_fields: [product_year, collection, legend_version, class_domain, service_type, retrieved_at]
  reference_file: mrlc-nlcd.md

- id: osm_public_services
  source_name: OpenStreetMap Public Services
  official_base_endpoint: https://www.openstreetmap.org/
  auth_mode: varies
  request_shape: tile_or_geocoding
  native_format: mixed
  native_crs: EPSG:3857 tiles and EPSG:4326 geocoding outputs
  advertised_crs: service-specific
  freshness_model: public shared infrastructure, not a production SLA
  operational_latency_model: policy-limited public service
  stable_ids: [osm_id, osm_type]
  pagination_windowing: usage-policy constrained
  usage_constraints: [respect tile and Nominatim policies, prefer self-hosting/commercial services for production load]
  provenance_granularity: OSM object ID plus provider/service
  provenance_fields: [provider, endpoint, osm_id, osm_type, usage_policy, retrieved_at]
  reference_file: osm-tiger.md

- id: census_tiger
  source_name: Census TIGER/TIGERweb
  official_base_endpoint: https://tigerweb.geo.census.gov/
  auth_mode: none
  request_shape: arcgis_rest
  native_format: mixed
  native_crs: service-specific
  advertised_crs: ArcGIS REST service metadata
  freshness_model: Census product release cycle
  operational_latency_model: reference basemap/context, not tenant source of record
  stable_ids: [geoid, layer_id, vintage]
  pagination_windowing: ArcGIS REST query limits and downloadable product bounds
  usage_constraints: [distinguish TIGERweb services from full TIGER/Line products]
  provenance_granularity: layer, vintage, and GEOID
  provenance_fields: [layer, vintage, geoid, endpoint, retrieved_at]
  reference_file: osm-tiger.md

- id: mapbox_platform
  source_name: Mapbox APIs
  official_base_endpoint: https://api.mapbox.com/
  auth_mode: public_token_or_secret_token
  request_shape: mixed
  native_format: mixed
  native_crs: EPSG:4326 for GeoJSON APIs; EPSG:3857 for tiles
  advertised_crs: endpoint-specific
  freshness_model: platform service; source freshness depends on endpoint/tileset
  operational_latency_model: API SLA and cache dependent
  stable_ids: [tileset_id, style_id, feature_id, endpoint_family]
  pagination_windowing: endpoint-specific
  usage_constraints: [secret tokens server-side only, pin style/tileset versions for exhibits]
  provenance_granularity: endpoint family and token class
  provenance_fields: [endpoint_family, token_class, style_id, tileset_id, request_params, retrieved_at]
  reference_file: mapbox-apis.md

- id: usgs_water_data
  source_name: USGS Water Data API
  official_base_endpoint: https://api.waterdata.usgs.gov/
  auth_mode: none
  request_shape: time_window
  native_format: json
  native_crs: EPSG:4326 for monitoring locations unless endpoint says otherwise
  advertised_crs: OGC API metadata
  freshness_model: sensor-driven observations with telemetry latency
  operational_latency_model: high frequency but not guaranteed same-minute real time
  stable_ids: [monitoring_location_id, parameter_code, statistic_code, time_series_id]
  pagination_windowing: bounded windows; split large spans; continuous endpoint max guidance is three years
  usage_constraints: [preserve provisional/approved status, do not treat latest as same-minute]
  provenance_granularity: site, parameter, statistic, and time window
  provenance_fields: [monitoring_location_id, parameter_code, statistic_code, time_window, qualifier, retrieved_at]
  reference_file: usgs-water-data.md

- id: epa_echo
  source_name: EPA ECHO
  official_base_endpoint: https://echo.epa.gov/tools/web-services
  auth_mode: none
  request_shape: report
  native_format: mixed
  native_crs: EPSG:4326 for facility coordinates where present
  advertised_crs: endpoint-specific
  freshness_model: warehouse refresh, typically weekly
  operational_latency_model: interactive search/report API, not bulk analytics
  stable_ids: [registry_id, npdes_id, facility_id]
  pagination_windowing: endpoint-specific; use bulk downloads for large-volume retrieval
  usage_constraints: [avoid hammering web services, preserve refresh date/report period]
  provenance_granularity: facility/permit/report endpoint
  provenance_fields: [registry_id, npdes_id, endpoint, report_period, refresh_date, retrieved_at]
  reference_file: epa-echo.md

- id: epa_waters
  source_name: EPA WATERS
  official_base_endpoint: https://www.epa.gov/waterdata/waters-web-services
  auth_mode: none
  request_shape: reach_or_layer_query
  native_format: mixed
  native_crs: NHDPlus and service-specific; mapping layers may be Web Mercator
  advertised_crs: JSON/GeoJSON, WMS, WFS
  freshness_model: program-indexed hydrography/reference services
  operational_latency_model: reference service, not live observations
  stable_ids: [comid, reachcode, huc, layer_id]
  pagination_windowing: service/layer limits
  usage_constraints: [keep reach-indexed hydrography separate from ATTAINS assessment cycle data]
  provenance_granularity: hydro feature and service layer
  provenance_fields: [comid, reachcode, huc_level, endpoint, layer_id, retrieved_at]
  reference_file: epa-waters-attains.md

- id: epa_attains
  source_name: EPA ATTAINS
  official_base_endpoint: https://www.epa.gov/waterdata/attains
  auth_mode: public_now_api_key_watch
  request_shape: assessment_query
  native_format: json
  native_crs: endpoint-specific
  advertised_crs: JSON REST and export metadata
  freshness_model: state assessment/TMDL cycle and periodic exports
  operational_latency_model: cycle-driven; watch API-key transition
  stable_ids: [assessment_unit_id, organization_id, cycle_year]
  pagination_windowing: endpoint-specific
  usage_constraints: [preserve cycle year, final-action status, and auth transition watch item]
  provenance_granularity: assessment unit plus cycle
  provenance_fields: [assessment_unit_id, cycle_year, organization_id, final_action_status, endpoint, retrieved_at]
  reference_file: epa-waters-attains.md

- id: state_stormwater_adapter
  source_name: State MS4 and delegated stormwater adapters
  official_base_endpoint: adapter-specific
  auth_mode: varies
  request_shape: adapter_specific
  native_format: mixed
  native_crs: adapter-specific
  advertised_crs: adapter-specific
  freshness_model: state- and dataset-specific
  operational_latency_model: adapter-specific; often annual, multi-year, or non-real-time
  stable_ids: [state, agency, permit_id, dataset_scope]
  pagination_windowing: adapter-specific
  usage_constraints: [do not invent national schema fields, declare permitting authority and dataset scope]
  provenance_granularity: state agency dataset plus adapter version
  provenance_fields: [state, agency, permitting_authority, dataset_scope, update_date, refresh_cycle, adapter_version, retrieved_at]
  reference_file: state-ms4-registry.md
```

## Non-Negotiable Rules

- Check this registry before adding a new external geospatial source.
- Preserve freshness and latency semantics; do not call a product-year source "current" without the product year.
- Preserve source provider and access path when wrappers change auth or limits.
- Treat public shared services as policy-bound infrastructure, not default production infrastructure.
- Add a new registry record when auth, transport, CRS, or freshness differs materially from an existing record.

## References

- Source contracts summarized from `# External Geospatial Service Research.md`.
- Accessed: 2026-05-08
