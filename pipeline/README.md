# pipeline

Python code that turns hadith sources into tradition packages (see `../docs/tradition-package.md`).

## Setup

```bash
/opt/homebrew/bin/python3.13 -m venv .venv && .venv/bin/pip install -e . pytest ruff mypy
```

Download the source dataset (1.63 GB, CC BY 4.0) into `../data/raw/hadith-kg/`:

```bash
curl -L --fail -o ../data/raw/hadith-kg/hadith-kg.db https://huggingface.co/datasets/emadjumaah/hadith-kg/resolve/main/hadith-kg.db
```

## Export a tradition

```bash
.venv/bin/python -m icma.cli export --db ../data/raw/hadith-kg/hadith-kg.db --group 730 --anchors 4153,3495,1239 --corrections ../corrections/hadith-kg.json --id ubada-khudhu-anni --title "'Ubada b. al-Samit: khudhu 'anni" --out ../data/derived/ubada-khudhu-anni.json
```

`--group` is a hadith-kg meaning group; `--anchors` keeps only chains through at least one of those
narrators, because meaning groups cluster by legal content and mix unrelated traditions.

## Run the model ICMA pass

Uses OpenRouter by default (`OPENROUTER_API_KEY` in `pipeline/.env`, model `deepseek/deepseek-v4-pro`,
strict JSON schema output, high reasoning effort; see `../eval/model-selection-2026-10-17.md`). `--provider anthropic` uses the Anthropic API directly
(`ANTHROPIC_API_KEY`); `--model` picks another model, e.g. an open-weight baseline on OpenRouter.

```bash
.venv/bin/python -m icma.cli analyze --db ../data/raw/hadith-kg/hadith-kg.db --group 730 --anchors 4153,3495,1239 --corrections ../corrections/hadith-kg.json --id ubada-khudhu-anni --title "'Ubada b. al-Samit: khudhu 'anni" --work-dir ../data/analyses/ubada-khudhu-anni --out ../data/derived/ubada-khudhu-anni.analysis.json
```

Stages (`src/icma/analysis/`):

1. `chain_matns` (model): for entries citing several routes, the wording attributed to each route.
2. Variants (code): every chain gets a matn; identical normalized matns share a variant id.
3. `matn_inventory` (model): shared content elements, per-variant readings, English translations.
4. Correlation (code): element rates in each independent branch below every CL candidate.
5. `icma_synthesis` (model): CL/PCL verdicts, dives, clusters, correlation, reconstruction, dating.

Every model call is cached in `--work-dir` under a hash of its exact prompt and input, together
with the model, usage, and prompt version, so reruns are free and every output is reproducible
training data. Model references to unknown chains, nodes, or variants are reported as warnings.

## Publish for review

Review data lives in Postgres (Neon in production). Migrations are in `../db/migrations/`.

```bash
.venv/bin/python -m icma.cli migrate --database-url "$DATABASE_URL_UNPOOLED"
.venv/bin/python -m icma.cli publish --analysis ../data/derived/ubada-khudhu-anni.analysis.json --database-url "$DATABASE_URL_UNPOOLED"
```

`publish` stores the analysis and splits it into reviewable judgements (CL and PCL verdicts,
dives, clusters, reconstructions, dating, per-chain matn extractions, matn elements, variant
readings). Publishing the same file twice is a no-op. Reviews are append-only rows, so the full
review history is kept as training signal.

Give someone access (prints a passcode once; only its hash is stored):

```bash
.venv/bin/python -m icma.cli reviewer add --email someone@example.org --database-url "$DATABASE_URL_UNPOOLED"
.venv/bin/python -m icma.cli reviewer passcode --email someone@example.org   # issue a new passcode
.venv/bin/python -m icma.cli reviewer remove --email someone@example.org    # revoke
```

Database tests run against a throwaway database when `ICMA_TEST_DATABASE_URL` is set:

```bash
docker run -d --name icma-pg -e POSTGRES_USER=icma -e POSTGRES_PASSWORD=icma -e POSTGRES_DB=icma -p 54329:5432 postgres:17
ICMA_TEST_DATABASE_URL=postgresql://icma:icma@localhost:54329/icma .venv/bin/pytest -q
```

## Compare models

```bash
.venv/bin/python -m icma.cli compare-models <selection args> --models a,b,c --key ../eval/gold/ubada-pavlovitch-2011.key.json --work-dir ../data/model-eval/<run> --out ../eval/<report>.md
```

`--seed-from <a model's work dir>` reuses that model's extraction and inventory for every model,
so they differ only in the final ICMA judgement.

## Score against a published study

```bash
.venv/bin/python -m icma.cli score --analysis ../data/derived/ubada-khudhu-anni.analysis.json --key ../eval/gold/ubada-pavlovitch-2011.key.json
```

The key maps Pavlovitch's verdicts (JAIS 11, 2011) to node keys: common links, rejected and
unresolved figures, partial common links, and the expected verdict on the convergence point.
Dating is compared by hand against `../eval/gold/ubada-pavlovitch-2011.json`. Treat scores with
care: a frontier model may have read the study, so a high score can reflect memory.

## Modules

- `arabic.py`: normalization for search and comparison (never applied to stored text).
- `models.py`: source-agnostic records.
- `sources/hadith_kg.py`: reader for the hadith-kg SQLite file.
- `corrections.py`: evidence-backed chain fixes from `../corrections/`.
- `bundle.py`: graph construction and the deterministic ICMA structure (CL candidates, spiders,
  dives, paths above the CL).
- `export.py`, `cli.py`: package serialization and command line.
- `analysis/`: the model ICMA stages, their schemas, prompts, and deterministic correlation.
- `db.py`: migrations and publishing analyses as reviewable judgements.
- `evaluate.py`: scoring a synthesis against a key built from a published study.

## Checks

```bash
.venv/bin/pytest -q && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy src tests
```

## Known source limitations

- hadith-kg has structured chains only for Prophetic reports; its 310K companion and successor
  reports have none.
- Chain gaps are stored as pseudo-narrators graded "fabricator" (code 12); the reader converts them
  to gap links.
- Chains are not audited upstream. The 'Ubada audit found 27 of 141 chains needing fixes (see
  `../corrections/proposed/ubada-audit-report.md`). Fixes are in `../corrections/hadith-kg.json`;
  how the 11 judgement calls were settled is in `../corrections/review/decision.md`.
