# icma

Isnad-cum-matn analysis (ICMA) of hadith at corpus scale: build isnad bundles from a large
multi-collection corpus, run model-assisted ICMA on them, and collect reviewed analyses as training
data for specialised models.

## Layout

| Path | What it is |
|---|---|
| `pipeline/` | Python: source readers, chain corrections, bundle construction, model ICMA stages, scoring. See `pipeline/README.md`. |
| `web/` | Next.js viewer for tradition packages: bundle graph, narrator panel, variant texts. See `web/README.md`. |
| `docs/tradition-package.md` | The JSON contract between pipeline and web app. |
| `corrections/` | Evidence-backed fixes to source chains (`hadith-kg.json`, applied), audit proposals (`proposed/`), and scholarly judgements awaiting review (`pending/`). |
| `eval/gold/` | Gold standards from published ICMA studies and scoring keys. |

## Status

Milestone 1 covers one tradition end to end: 'Ubada b. al-Samit, "khudhu 'anni", scored against
Pavlovitch, *JAIS* 11 (2011). Source data: the Hadith Knowledge Graph (hadith-kg, CC BY 4.0),
downloaded into the git-ignored `data/` directory (instructions in `pipeline/README.md`).

## Attribution

Hadith texts, chains, and narrator data come from Emad Jumaah, *Hadith Knowledge Graph* (2026),
https://huggingface.co/datasets/emadjumaah/hadith-kg, licensed CC BY 4.0. Bundle structure,
corrections, and analyses are derived from that data.
