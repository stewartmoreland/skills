# HTTP Clients

The client is the layer that sends the actual request. Pick one; Fetch is the default. All clients are compatible with validators, transformers, and the SDK. Installing a client generates a `client.gen.ts` exporting a configured `client` instance plus a `createClient` factory and a `CreateClientConfig` type.

## Available clients and when to use them

| Plugin | Use when |
| --- | --- |
| `@hey-api/client-fetch` | Default. Plain TS, Node 22+, browsers, anything Fetch-capable. |
| `@hey-api/client-axios` | The project already standardizes on Axios (interceptors, instances). |
| `@hey-api/client-next` | Next.js — supports `next: { revalidate, tags }` and server-component fetching. |
| `@hey-api/client-nuxt` | Nuxt 3 — integrates with Nuxt's data fetching. |
| `@hey-api/client-angular` | Angular (v19/v20) — uses `HttpClient`. |
| `@hey-api/client-ky` | Ky-based projects. |
| `@hey-api/client-ofetch` | ofetch-based projects. |
| Effect / Got | Community-voted, check docs for status. |

Install the client and add it to `plugins`. Fetch is implied if you list no client, but listing it explicitly is clearer.

## Configuring the client instance

Three approaches. You almost always need at least `baseUrl`.

### 1. `setConfig()` — simplest

Call it once at app startup (or whenever config changes):

```ts
import { client } from './client/client.gen';

client.setConfig({
  baseUrl: 'https://api.example.com',
});
```

Accepts any underlying-client option (for Fetch, any Fetch option) plus a custom fetch implementation. Caveat: code may call the client before `setConfig` runs. If that's a risk, use the runtime API.

### 2. Runtime API — config resolved before first use

Point the config at a file that exports `createClientConfig()`:

```ts
// openapi-ts.config.ts
export default {
  input: 'my-org/my-api',
  output: 'src/client',
  plugins: [
    {
      name: '@hey-api/client-fetch',
      runtimeConfigPath: './src/hey-api.ts',
    },
  ],
};
```

```ts
// src/hey-api.ts
import type { CreateClientConfig } from './client/client.gen';

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseUrl: process.env.API_BASE_URL ?? 'https://api.example.com',
});
```

`client.gen.ts` calls `createClientConfig()` before initializing the instance, so config is guaranteed set on first use. You can still `setConfig` later.

### 3. `createClient()` — your own instance

```ts
import { createClient } from './client/client';

const myClient = createClient({ baseUrl: 'https://other.example.com' });
```

Pass it to any SDK call to override the default instance:

```ts
const res = await getFoo({ client: myClient });
```

### 4. Per-call config (no instance)

For one-offs, pass client options straight into the SDK call:

```ts
const res = await getFoo({ baseUrl: 'https://other.example.com' });
```

## Auth

Preferred: let the SDK handle it via the client's `auth()` callback (works with the SDK plugin's `auth` option, see sdk-and-types.md):

```ts
import { client } from './client/client.gen';

client.setConfig({
  auth: () => '<token>',          // sync or async; return the token
});
```

The SDK serializes/encodes per the spec's security scheme (currently `bearer` and `basic` are supported built-in). For other schemes, or if you're not generating auth, use interceptors.

## Interceptors

Hook into requests/responses (Fetch client shown; Axios uses Axios interceptors):

```ts
import { client } from './client/client.gen';

client.interceptors.request.use((request) => {
  request.headers.set('Authorization', `Bearer ${getToken()}`);
  return request;
});

client.interceptors.response.use((response) => {
  // inspect / transform / throw on non-2xx if you want throwing behavior
  return response;
});
```

Interceptors are the common way to attach auth for arbitrary schemes, add tracing headers, or convert the default non-throwing behavior into throws.

## Custom fetch / instance

Supply your own underlying implementation through `setConfig` (e.g. a wrapped `fetch`, or a preconfigured Axios instance for the Axios client). See the per-client page under `https://heyapi.dev/docs/openapi/typescript/clients/...` for the exact shape.

## Return shape

SDK calls resolve (they don't throw by default) to:

```ts
const { data, error, request, response } = await getFoo({ path: { id: 1 } });
```

`data` is the typed success body, `error` the typed error body, and `request`/`response` are the originals. Check `error` rather than relying on try/catch.
