# Configuration

The config file lives in the project root. `@hey-api/openapi-ts` loads any supported filename (via the jiti loader): `openapi-ts.config.ts`, `.cjs`, `.mjs`, or `.js`. TypeScript is the common choice because `defineConfig` gives you autocomplete and type-checking on the options.

## Minimal config

```ts
// openapi-ts.config.ts
import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: './openapi.json',
  output: 'src/client',
  plugins: ['@hey-api/client-fetch'], // types + sdk are on by default
});
```

`defineConfig` is optional — a plain object export works too — but prefer it for the types.

## Input

`input` tells the tool where to load the spec. Forms:

```ts
// local path
input: './path/to/openapi.json'

// URL
input: 'https://get.heyapi.dev/my-org/my-api'

// Hey API registry slug (after signing up at app.heyapi.dev)
input: 'my-org/my-api'

// object form, for extra options
input: {
  path: './openapi.yaml',
  // ...filters, watch, etc.
}

// inline spec object
input: {
  openapi: '3.1.1',
  // ...rest of the spec
}
```

All valid OpenAPI versions and both JSON and YAML are accepted. Swagger 2.0 specs are upconverted.

**Self-signed HTTPS in dev:** set `NODE_TLS_REJECT_UNAUTHORIZED=0` in the environment or the fetch of the spec will fail on the certificate.

## Output

`output` is where files are written. String shorthand or object:

```ts
output: 'src/client'

output: {
  path: 'src/client',
  // format, lint, indexFile, clean, etc.
}
```

Treat the output folder as a dependency / build artifact. Do not modify its contents — the next run erases changes. Add it to `.gitignore` if you regenerate in CI, or commit it if you prefer reproducible diffs (both are valid; teams differ).

## Plugins

`plugins` is an array. Each entry is either a string (plugin name, default options) or an object (`{ name, ...options }`):

```ts
plugins: [
  '@hey-api/client-fetch',
  {
    name: '@hey-api/sdk',
    validator: 'zod',
  },
  'zod',
  '@tanstack/react-query',
]
```

By default, even without listing them, you get `@hey-api/typescript` (types) and `@hey-api/sdk` (SDK). Listing a client is what makes the output actually callable.

## Parser

Parsing happens before plugins run and is the place to filter or patch the spec. Configuring it is optional. Use it to include/exclude operations, rename things, or validate the input. See `https://heyapi.dev/docs/openapi/typescript/configuration/parser`.

## Multiple jobs, job matrix, merging

**Independent jobs** — array of configs:

```ts
export default [
  { input: 'foo.yaml', output: 'src/foo' },
  { input: 'bar.yaml', output: 'src/bar' },
];
```

**Job matrix** — parallel `input`/`output` arrays of equal length generate one job per pair:

```ts
export default {
  input: ['foo.yaml', 'bar.yaml'],
  output: ['src/foo', 'src/bar'],
};
```

**Merging inputs** — many inputs, one output, combines specs into a single client:

```ts
export default {
  input: ['foo.yaml', 'bar.yaml'],
  output: 'src/client',
};
```

## Running

CLI (after adding `"openapi-ts": "openapi-ts"` to `package.json` scripts):

```bash
npm run openapi-ts
```

One-off without a config:

```bash
npx @hey-api/openapi-ts -i ./openapi.json -o src/client -c @hey-api/client-fetch
```

Common flags: `-i` input, `-o` output, `-c` client.

## Programmatic API

Generate from a script instead of the CLI:

```ts
import { createClient } from '@hey-api/openapi-ts';

await createClient({
  input: 'my-org/my-api',
  output: 'src/client',
});
```

(Note: this `createClient` from the *generator* package generates files. It's different from the `createClient` exported by a *client* package, which creates a runtime HTTP client instance.)

## Vite plugin

For Vite 5/6/7/8, run codegen as part of the build instead of a separate script:

```ts
// vite.config.ts
import { heyApiPlugin } from '@hey-api/vite-plugin';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    heyApiPlugin({
      config: {
        input: 'my-org/my-api',
        output: 'src/client',
      },
    }),
  ],
});
```

Install `@hey-api/vite-plugin` alongside the main package. Full options: `https://heyapi.dev/docs/openapi/typescript/configuration/vite`.

## Versioning

The package is in initial development (pre-1.0 semantics): pin exact versions (`-E`) so you upgrade deliberately. Migration notes ship with every breaking release at `https://heyapi.dev/docs/openapi/typescript/migrating`.

The complete option list is the `UserConfig` interface: `https://github.com/hey-api/openapi-ts/blob/main/packages/openapi-ts/src/config/types.ts`.
