# Ecosystem: Servers, Mocks, Custom, Migration

The pieces beyond client/SDK/types/validators/state. All are plugins added to the `plugins` array. All are compatible with the core features.

## Web framework (server) plugins

Generate server-side code from the same spec — route handlers, controllers, or contracts. Useful for spec-first backends or for keeping server and client in lockstep.

| Plugin name | Generates |
| --- | --- |
| `fastify` | Fastify v5 route handler types/registration |
| `nest` | NestJS v11 controller methods |
| `hono` | Hono route types |
| `express` | Express handlers |
| `koa` | Koa handlers |
| `elysia` | Elysia routes |
| `adonis` | AdonisJS bindings |
| `orpc` | oRPC v1 contracts |
| `angular` | Angular v19/v20 HTTP requests + resources (client + plugin) |
| `tanstack-start` | TanStack Start bindings |

Example (Fastify):

```ts
export default {
  input: './openapi.yaml',
  output: 'src/server',
  plugins: ['fastify'],
};
```

Then wire the generated route types into your Fastify instance. Per-framework option names and registration patterns are on each plugin's page under `https://heyapi.dev/docs/openapi/typescript/plugins/<name>`. Read the specific page before writing the integration — registration differs per framework.

## Mock plugins

For testing and local development.

| Plugin name | Purpose |
| --- | --- |
| `msw` | MSW request handlers — intercept SDK calls in tests/Storybook/browser |
| `faker` | Faker-based fake data generators matching your schemas |
| `chance` | Chance-based fake data |
| `falso` | Falso-based fake data |
| `nock` | Nock interceptors (Node HTTP mocking) |
| `supertest` | Supertest helpers for endpoint testing |

Common combo: `msw` (handlers) + `faker` (data) to stand up a full mock API:

```ts
export default {
  input: 'my-org/my-api',
  output: 'src/client',
  plugins: ['@hey-api/client-fetch', 'msw', 'faker'],
};
```

The MSW plugin emits handlers you register in a worker (browser) or server (node) setup. Faker emits per-schema factories. Overview: `https://heyapi.dev/docs/openapi/typescript/mocks`.

## Custom plugins and clients

If no built-in fits:

- **Custom plugin** — write your own generator that runs over the parsed spec. Guide: `https://heyapi.dev/docs/openapi/typescript/plugins/custom`. The `Resolvers` concept page explains how plugins reference each other's output: `https://heyapi.dev/docs/openapi/typescript/plugins/concepts/resolvers`.
- **Custom client** — implement a client against a different HTTP library. Guide: `https://heyapi.dev/docs/openapi/typescript/clients/custom`.

## Migration and integrations

- **Migrating** between versions (the package is pre-1.0 and ships breaking minors): `https://heyapi.dev/docs/openapi/typescript/migrating`. Always read this before bumping a minor.
- **Hey API platform / registry** — host specs and generate from a slug (`my-org/my-api`) with automated client generation and a GitHub integration: `https://heyapi.dev/docs/openapi/typescript/integrations`.

## Quick coverage map

If asked about something not detailed in a reference file, the page URL pattern is:

```
https://heyapi.dev/docs/openapi/typescript/<section>/<name>
```

and the machine-readable index of every page is `https://heyapi.dev/llms.txt`. The exhaustive option reference is the `UserConfig` type in the source: `https://github.com/hey-api/openapi-ts/blob/main/packages/openapi-ts/src/config/types.ts`.
