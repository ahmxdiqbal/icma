# ICMA web viewer

A read-only viewer for tradition packages: the isnad bundle of one hadith (every transmission
chain across the collections, merged into one graph), the variant texts, and the structural facts
the pipeline computed. It renders; it does not analyse. Labels say "convergence point" and
"structural CL/PCL candidate" because whether a node is a genuine common link is decided by matn
analysis, not by the bundle.

## Run

Requires Node 22 and pnpm.

```sh
source ~/.nvm/nvm.sh && nvm use 22
pnpm install
pnpm dev            # http://localhost:3000
```

## Check

```sh
pnpm lint           # ESLint, zero warnings allowed
pnpm typecheck      # next typegen + tsc --noEmit (strict)
pnpm test           # vitest unit tests
pnpm build          # production build; prerenders every tradition
pnpm exec playwright install chromium   # once
pnpm test:e2e       # builds, starts on :3200, runs the Playwright smoke test
```

## Data

Each file in `data/traditions/<id>.json` is one tradition package, copied from
`../data/derived/` where `pipeline/src/icma/export.py` writes it. The contract is described in
`../docs/tradition-package.md`; the serializer is the source of truth.

To add or refresh a tradition, copy the package here and rebuild. `src/lib/schema.ts` mirrors the
contract with strict zod objects plus cross-reference checks, so a missing, renamed or extra field,
or an id that does not resolve, fails the build with a report naming the path. When the contract
changes, update the schema first.

The source dataset is Emad Jumaah's Hadith Knowledge Graph (hadith-kg, CC BY 4.0). Every page
shows the package's attribution in its footer; keep it there.

## How it fits together

- `src/lib/load.ts` reads and validates packages (server only, synchronous reads).
- `src/lib/bundle-graph.ts` turns the bundle into display nodes and edges: labels, structural
  emphasis, collector books, edge widths, dive-only edges.
- `src/lib/layout.ts` lays the graph out with ELK (layered, top to bottom, the Prophet first,
  collectors without students on the last row). It runs on the server inside a cached function, so
  the browser receives coordinates and never loads ELK.
- `src/lib/text-segments.ts` splits each text into isnad, matn and trailing parts and marks
  narrator mentions.
- `src/components/tradition/` holds the client UI: summary strip, React Flow graph, node panel and
  texts tab, coordinated by a small reducer in `explorer-state.ts`.

Unit tests sit next to the code (`*.test.ts`) and run against both the real Ubada package and small
synthetic packages from `src/lib/test-fixtures.ts`. The e2e smoke test is in `e2e/`.
