# Return Contract

## When to use

Use for every geospatial function, worker job, import task, API procedure, or script that emits a raster, vector table, GeoJSON, tile, spatial aggregate, or derived hydrology result.

## Canonical envelope

Return both the artifact and metadata:

```ts
type GeoArtifactEnvelope<TArtifact> = {
  artifact: TArtifact;
  metadata: {
    crs: {
      value: string;
      authority?: "EPSG" | "WKT" | "PROJJSON" | "unknown";
      isNative: boolean;
      transformedFrom?: string;
    };
    bounds?: [number, number, number, number];
    transform?: [number, number, number, number, number, number];
    tileBounds?: [number, number, number, number];
    dtype?: string;
    nodata?: {
      value: number | string | null;
      source: "source" | "derived" | "none" | "unknown";
    };
    maskSemantics?: "valid_nonzero" | "invalid_true" | "none";
    units: Record<string, string>;
    provenance: {
      source: string;
      sourceVersion?: string;
      retrievedAt?: string;
      processedAt?: string;
      processingSteps: string[];
    };
  };
};
```

## Required metadata by artifact

| Artifact | Required metadata |
|----------|-------------------|
| Raster file/window | `crs`, `bounds`, `transform`, `dtype`, `nodata`, `maskSemantics`, `units`, `provenance` |
| GeoJSON/vector table | `crs`, `bounds`, `units`, `provenance` |
| XYZ tile | `crs`, `tileBounds`, `dtype`, `nodata`, `maskSemantics`, `provenance` |
| Spatial SQL result | `crs`, `units`, `provenance`, and source table/query lineage |
| Hydrology result | all spatial metadata plus rainfall/flow/elevation units and method name |

## Idiomatic call pattern

```ts
return {
  artifact: catchmentGeojson,
  metadata: {
    crs: { value: "EPSG:4326", authority: "EPSG", isNative: false, transformedFrom: "EPSG:4269" },
    bounds: [-84.42, 33.72, -84.31, 33.81],
    units: { area: "square_meters", elevation: "meters" },
    provenance: {
      source: "USGS 3DEP DEM",
      sourceVersion: "source metadata",
      retrievedAt: new Date().toISOString(),
      processedAt: new Date().toISOString(),
      processingSteps: ["read_raster_window", "condition_dem", "delineate_watershed"],
    },
  },
};
```

## Known gotchas

- A GeoJSON object without CRS metadata still needs an envelope declaring that StormwaterIQ treats it as `EPSG:4326`.
- A raster window must return its window-relative affine transform, not only the parent dataset transform.
- Tiles need tile bounds because XYZ indices alone are easy to confuse across tile matrix sets.
- Source version can be a product release, dataset timestamp, API response version, or `source metadata` when no stable release string exists.

## Validation checklist

- [ ] The artifact can be interpreted without hidden global state.
- [ ] CRS and units are present even for "obvious" WGS84 GeoJSON.
- [ ] Raster outputs distinguish nodata from mask semantics.
- [ ] Provenance includes enough source and processing detail for an audit trail.
