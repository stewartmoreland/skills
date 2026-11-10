# State Management plugins

These generate state-management bindings from the spec on top of the SDK. They don't replace the SDK — they wrap its functions in your library's primitives and generate consistent query keys.

| Plugin name | Library | Frameworks |
| --- | --- | --- |
| `@tanstack/react-query` | TanStack Query v5 | React (also vue/angular/svelte/solid/preact variants — pick the matching framework string) |
| `swr` | SWR | React |
| `pinia-colada` | Pinia Colada v0 | Vue |
| `zustand` | Zustand | any |

## TanStack Query

Add the plugin matching the framework:

```ts
// openapi-ts.config.ts
export default {
  input: 'my-org/my-api',
  output: 'src/client',
  plugins: [
    '@hey-api/client-fetch',
    '@tanstack/react-query',
  ],
};
```

### What it generates

For each operation it emits helpers (names follow the operation):

- **Query options** — `xOptions()` returning a `queryOptions` object (queryKey + queryFn) to spread into `useQuery`.
- **Infinite query options** — `xInfiniteOptions()` for paginated endpoints, plus infinite query keys.
- **Mutations** — `xMutation()` returning options to spread into `useMutation`.
- **Query keys** — key factories built following TanStack best practices, so caching/invalidation is consistent.

### Usage

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getPetByIdOptions,
  addPetMutation,
  getPetByIdQueryKey,
} from './client/@tanstack/react-query.gen';

function Pet({ id }: { id: number }) {
  const { data, error, isPending } = useQuery(
    getPetByIdOptions({ path: { petId: id } }),
  );

  const qc = useQueryClient();
  const add = useMutation({
    ...addPetMutation(),
    onSuccess: () => qc.invalidateQueries({ queryKey: getPetByIdQueryKey({ path: { petId: id } }) }),
  });

  // ...
}
```

(Exact export names mirror your `operationId`s — check the generated `.gen.ts` for the precise identifiers in your project.)

### Reactivity

Frameworks with reactive params (Vue, Angular signals, Solid) are supported — pass reactive values into the options and the query tracks them. See the Reactivity section at `https://heyapi.dev/docs/openapi/typescript/plugins/tanstack-query`.

## SWR

```ts
plugins: ['@hey-api/client-fetch', 'swr']
```

Generates SWR keys and fetchers per operation. Use the generated key + fetcher with `useSWR`. Details: `https://heyapi.dev/docs/openapi/typescript/plugins/swr`.

## Pinia Colada (Vue)

```ts
plugins: ['@hey-api/client-fetch', 'pinia-colada']
```

Generates query functions and query keys for Pinia Colada v0. Details: `https://heyapi.dev/docs/openapi/typescript/plugins/pinia-colada`.

## Zustand

Generates store-friendly bindings. Details: `https://heyapi.dev/docs/openapi/typescript/plugins/zustand`.

Overview page: `https://heyapi.dev/docs/openapi/typescript/state-management`.
