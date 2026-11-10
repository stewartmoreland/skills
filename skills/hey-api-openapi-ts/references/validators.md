# Validators and Transformers

Validators generate runtime schemas from the spec so request/response data can be checked at runtime. Transformers reshape response data. Both are optional and have a runtime cost, so they're off until you enable them.

## Available validators

| Plugin name | Notes |
| --- | --- |
| `zod` | Default choice for most. **Zod v4 is the default** (`/plugins/zod`); Zod v3 is available at `/plugins/zod/v3`, and Zod Mini at `/plugins/zod/mini`. |
| `valibot` | Lightweight, tree-shakeable; good for bundle-sensitive frontends. |
| `arktype`, `typebox`, `yup`, `joi`, `superstruct`, `ajv` | Supported; some are community-voted. Pick what the project already uses. |

Each emits schema definitions (for Zod, prefixed `z...`; for Valibot, `v...`) into a generated file, one per type/operation.

## Two ways to enable

**A) Through the SDK (recommended).** This is what actually wires validation into request/response handling:

```ts
plugins: [
  { name: '@hey-api/sdk', validator: 'zod' }, // auto-adds zod with defaults
]
```

Setting `validator` to a name (or `true`) auto-adds that validator plugin. To customize the generated schemas, also add the plugin explicitly and set `validator: true`:

```ts
plugins: [
  { name: '@hey-api/sdk', validator: true },
  { name: 'zod', /* customization options */ },
]
```

**B) Validator plugin alone.** Add e.g. `'zod'` to plugins to generate schemas you import and use yourself, without SDK wiring. Useful for form validation reusing the API's types.

## Request-only or response-only

Validating both directions doubles the cost. Often you trust your own request shapes (TypeScript already guards them) and only want to validate responses:

```ts
{ name: '@hey-api/sdk', validator: { response: 'zod' } }
```

Or the reverse:

```ts
{ name: '@hey-api/sdk', validator: { request: 'zod' } }
```

Under the hood the SDK attaches a `requestValidator` / `responseValidator` that parses with the chosen library:

```ts
// generated (valibot example)
export const addPet = (options: Options<AddPetData>) =>
  (options.client ?? client).post<AddPetResponses, AddPetErrors>({
    requestValidator: async (data) => await v.parseAsync(vAddPetData, data),
    responseValidator: async (data) => await v.parseAsync(vAddPetResponse, data),
    /* ... */
  });
```

## Transformers

Transformers run on **responses only** and use the `transformer` option (same enable pattern as validators). The classic use is converting JSON date strings into `Date` objects, or otherwise normalizing payloads:

```ts
plugins: [
  { name: '@hey-api/sdk', transformer: true }, // or 'valibot', 'zod', etc.
]
```

This attaches a `responseTransformer` that runs the data through the generated transform before you receive it.

## Using generated schemas directly

```ts
import { zPet } from './client/zod.gen';

const result = zPet.safeParse(unknownInput);
if (!result.success) { /* result.error */ }
```

This is handy for validating data that didn't come through the SDK (form input, webhook payloads, cached values) against the same source-of-truth schema.

Overview page: `https://heyapi.dev/docs/openapi/typescript/validators`.
