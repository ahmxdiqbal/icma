# Current state

The project's memory between sessions: the goal, the decisions made, what exists, results, open
decisions and next steps. `CLAUDE.md` imports this file, so every session starts with it. The rules
for keeping it current are in `CLAUDE.md`.

Last updated: 2026-10-20.

## Goal

A hadith ICMA app over a very large multi-collection corpus with full chains. It draws each hadith's
chains as a bundle, has models carry out the ICMA steps, and collects reviewed analyses as training
data. The end goal is small specialist models, one per step where that helps, that are cheaper and
faster than general models and at least as good.

Milestone 1, still in progress, is one hadith end to end: ʿUbāda b. al-Ṣāmit, "خذوا عني", scored
against Pavlovitch, *JAIS* 11 (2011) (`eval/gold/ubada-pavlovitch-2011.*`).

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-10-11 | Ground truth: Ahmed plus frontier models first, academics later. Ahmed has contacts among prominent hadith scholars. | Start fast, raise the standard later. |
| 2026-10-11 | Milestone 1 is one well-studied hadith end to end before any scaling. | Prove the pipeline first. |
| 2026-10-11 | Train on rented cloud GPUs, open-weight models, LoRA. | Full control over the weights. |
| 2026-10-11 | English interface. Hadith shown in Arabic with English translations; machine translations are marked as such. | Most hadith outside the six books have no published translation. |
| 2026-10-11 | Research and free use only, never commercial, so non-commercial sources and licences are usable. | Ahmed's choice. |
| 2026-10-11 | hadith-kg (CC BY 4.0) is the data backbone. Shamela's official full database download (dev.shamela.ws, 13.3 GB) comes later for authoritative text. Never bulk-scrape shamela.ws or turath.io. | Licence and site terms. |
| 2026-10-11 | Vercel hosts the UI and API only. Ingestion and training run elsewhere. | Vercel limits. |
| 2026-10-11 | Code computes structure: the bundle, common link candidates, key figures, dives, single strands. Models make the judgements. | Structure can be checked; judgement cannot. |
| 2026-10-17 | No American models in the pipeline. Chinese open-weight models through OpenRouter; the default is DeepSeek V4 Pro (`eval/model-selection-2026-10-17.md`). Check open-weight status on Hugging Face: Qwen Max/Plus and ByteDance Seed 2.x are closed. | Ahmed's preference and cost; Opus is too expensive for the pipeline. |
| 2026-10-17 | Sign-in stays minimal: email plus a per-reviewer passcode, a 400-day cookie. Do not add auth features. | Ahmed found more sign-in work excessive. |
| 2026-10-17 | Scholarly calls Ahmed does not want to make, such as disputed chain corrections, are settled by independent reviewer agents plus Claude's adjudication. Corrections that make a chain match its own text are applied; the 11 judgement calls are settled in `corrections/review/decision.md`. | Ahmed is not an ICMA authority and asked for this. |
| 2026-10-18 | ICMA is a pipeline of separate steps: chains, wording per chain, bundle, common links, false attribution, dating. Deterministic code where possible, a specialist model per step where needed. | Small models do one narrow job well, and each step can be checked on its own. |
| 2026-10-18 | The number of chains comes from the dataset (`sanads`), never from a model. Wording per chain follows `docs/chain-wording.md`: only مثله lets a chain take another chain's words, and a paraphrase never counts as the same wording. | Definitive counts; strict rules. |
| 2026-10-18 | Check pipeline steps against blind labels from Claude subagents that never see the code's output, not against cheaper models. Fix on one set, measure on a fresh one. Use only as many examples as needed, and stop to reevaluate when progress stalls. Claude as a reference labeller is allowed although it is American. | Ahmed's request; the cheaper models were already shown to be wrong. |
| 2026-10-18 | Words used with Ahmed follow `GLOSSARY.md` and `learning/KNOWN.md` (rules in `CLAUDE.md`). | Ahmed is learning ICMA. |
| 2026-10-20 | This file is the single record of project state. Claude's auto-memory holds only a pointer to it. | Context must survive any new session or machine. |
| standing | Commit and push only when Ahmed asks. | |

## What exists

### Data

- hadith-kg SQLite at `data/raw/hadith-kg/hadith-kg.db` (1.6 GB, git-ignored; download command in
  `pipeline/README.md`). Open it read-only with `file:<path>?immutable=1`. It holds 715,790 entries
  and 20,745 meaning groups. Only Prophetic hadith have chains: 403,368 entries have chains and
  96,163 have several.
- Known dataset problems:
  - `matn_start`/`matn_end` often cut off the start of the matn, such as the revelation scene in
    the ʿUbāda hadith. They are exact on 11 of 21 test entries.
  - 85K chains are missing their collector.
  - 908 chains in the Musnad credit Aḥmad with his son ʿAbd Allāh's additions.
  - About 10.5K teacher and student links are implausible.
  - There are namesake errors, 52 of them in Ibn Ḥibbān.
  - Gaps are stored as pseudo-narrators (ids 30000 to 30002 and 1131) with a fake grade.
- Corrections: `corrections/hadith-kg.json`, 26 applied fixes to ʿUbāda chains. The audit found 27 of
  141 chains needing fixes (`corrections/proposed/`).
- Shamela is not downloaded yet.

### Pipeline (`pipeline/`, Python 3.13 in `.venv`)

- **Reading data and building the bundle:**
  - `sources/hadith_kg.py` reads entries by meaning group plus anchor narrators (`load_tradition`)
    or by entry id (`load_entries`).
  - `corrections.py` applies the corrections layer.
  - `bundle.py` builds the bundle, common link candidates, key figures, the convergence point,
    dives and single strands.
  - `export.py` writes the JSON package (`docs/tradition-package.md`).
- **Model steps (`analysis/`):** `chain_matns` (model), then wordings grouped by identical
  normalized text (code), then `matn_inventory` (model), correlation (code) and `icma_synthesis`
  (model). Every call is cached by an input hash, together with the model, usage and cost.
  Providers are OpenRouter (the default) and Anthropic.
- **Wording per chain by rules (2026-10-18):**
  - Code: `analysis/wording.py` and `analysis/wording_vocab.py`; spec: `docs/chain-wording.md`;
    scorer: `icma.cli score-wording`.
  - Not wired into the runner yet. The runner still uses the model's `chain_matns` step for
    multi-chain entries and hadith-kg's matn spans for single-chain entries.
- **Publishing (`db.py`):** splits an analysis into reviewable judgements. Reviews are append-only.
- **CLI** (`python -m icma.cli`): `export`, `analyze`, `migrate`, `publish`, `reviewer`,
  `compare-models`, `score`, `score-wording`.
- **Checks:** 98 tests pass, and 10 database tests skip without `ICMA_TEST_DATABASE_URL`. ruff and
  mypy are clean.

### Web (`web/`, Next.js 16.4, React 19.3, pnpm, Node 22)

- A viewer for packages (bundle drawing, narrator panel, wordings) and a review UI (accept, reject or
  revise each judgement, with history).
- Sign-in uses an email plus a passcode issued by `icma.cli reviewer passcode`, with a signed cookie.
  The reviewers table is checked on every request.
- Local preview: the "web" entry in `.claude/launch.json`, port 3100.

### Infrastructure

- **GitHub:** private repo `ahmxdiqbal/icma`.
- **Vercel:**
  - Project `icma` in team ahmxdiqbals-projects, root `web`, git deploys from `main`; production at
    icma-lovat.vercel.app.
  - Vercel Authentication covers previews only; production relies on the app's own sign-in.
  - `vercel curl` created an automation-bypass secret on the project.
- **Neon Postgres** `icma-db`: free plan, iad1, Postgres 18, provisioned through the Vercel
  Marketplace. Migrations 0001 to 0004 are applied. `DATABASE_URL` (pooled) serves the app and
  `DATABASE_URL_UNPOOLED` runs migrations. Neon Auth was provisioned but is unused.
- **Secrets, never committed:** `pipeline/.env` (`OPENROUTER_API_KEY`), `web/.env.local`
  (`DATABASE_URL`, `SESSION_SECRET`).
- **OpenRouter credit:** $0.29 left of $10 on 2026-10-20. Any further model run needs a top-up.

## Results so far

- **Model selection, 2026-10-17** (`eval/model-selection-2026-10-17.md`):
  - DeepSeek V4 Pro was the cheapest model to finish every step: about $0.08 and 30 minutes per
    hadith, common link recall 0.33 and precision 0.67.
  - No model reached Pavlovitch's reading. All accept the convergence point al-Ḥasan, whom he
    rejects. His common links are Shuʿba, Hushaym, al-Qaṭṭān, Wakīʿ, Jarīr b. Ḥāzim and Yazīd b.
    Hārūn.
  - Found later: the matn comparison ran on hadith-kg spans that drop the opening of many matns, so
    the comparison of matns was weaker than it should have been.
- **Wording per chain, 2026-10-18** (`eval/chain-wording-2026-10-18.md`), on unseen entries:
  - The rules get 61% of chains in multi-chain entries exactly right (92 of 151), and 16 of 21
    single-chain entries.
  - DeepSeek V4 Pro, given the same rules, gets 63% (50 of 79).
  - Where the rules and DeepSeek agree (42 of 79 chains), they are right on 39.
  - Two blind Claude labellers agree on 92%.
  - Most errors are where a matn starts and ends. The structure (the basis) is right for 87% of
    chains.
- **Small-model research, 2026-10-19** (`reports/Small models for hadith segmentation.md`):
  - The best fit is a 0.1B to 0.3B Arabic encoder that labels every word as chain, link to the
    Prophet, matn, formula or comment. Candidates:
    - CAMeLBERT-CA: classical Arabic; NYU Abu Dhabi.
    - Rawi: Algeria; 8K tokens; non-commercial licence.
    - NeoAraBERT: Qatar and Lebanon; reads vowel marks.
  - The fallback decoder is Qwen3.5-4B-Base (China).
  - Strip vowel marks before the model and keep the offset map; `arabic.normalize_with_offsets`
    does this.
  - Labels are the limit. A tagger ends up near its labeller's accuracy. Blind Claude labels cost
    about $180 per 10,000 entries through the batch API, and a first test needs 1,000 to 2,000
    labelled entries.

## Open decisions, waiting on Ahmed

1. May blind Claude labels serve as training data for the tagger? That puts an American model in
   the training step, though the deployed tagger would not be American.
2. Who can hand-check 100 to 200 chains? Two Claude labellers can share the same mistakes. One of
   Ahmed's academic contacts is an option.
3. Start the first tagger experiment?
4. Wire the wording rules into the pipeline in place of the model's `chain_matns` step and
   hadith-kg's spans?
5. Top up the OpenRouter credit?

## Next steps (proposed)

1. Wire the rules into `analysis/variants.py` and the runner, then rerun the ʿUbāda analysis with
   full matns.
2. First tagger experiment:
   - Label 1,000 to 2,000 entries blind.
   - Repair hadith-kg's spans with the rules.
   - Fine-tune CAMeLBERT-CA and Rawi.
   - Score against the rules on held-out meaning groups.
3. Grow the frozen test set to about 850 chains, so that 5-point differences can be measured.

## Git

Everything was committed and pushed to `main` on 2026-10-20; a push to `main` deploys the web app to
production. Model outputs under `data/` are git-ignored local files.

## Commands

```bash
cd pipeline && .venv/bin/pytest -q && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy src tests
cd pipeline && .venv/bin/python -m icma.cli score-wording --db ../data/raw/hadith-kg/hadith-kg.db ../eval/gold/chain-wording/*.json
```

The rest are in `pipeline/README.md` and `web/README.md`.
