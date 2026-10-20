# Model selection for the ICMA pipeline (2026-10-17)

Constraint: Chinese open-weight models only (weights confirmed on Hugging Face), through OpenRouter.
Test: the full three-stage analysis of the 'Ubada "khudhu 'anni" tradition (141 chains, 24 entries
citing several routes), scored against Pavlovitch, *JAIS* 11 (2011). Raw outputs are in
`data/model-eval/run-2026-10-17b/` (git-ignored); the table is `model-comparison-2026-10-17b.md`.

## Results (second run, after harness fixes)

| Model | Cost per tradition | Time | Wording quoted verbatim | CL recall / precision | Notes on the ICMA judgement |
|---|---|---|---|---|---|
| deepseek/deepseek-v4-pro (Apr 2026) | **$0.08** | 29 min | 48/49 | 0.33 / 0.67 | Coherent, Juynboll-style reading: al-Hasan as CL, Qatada, Sa'id, Shu'ba, Hushaym as CLs; 4 clusters; no warnings. Coarse element list (7). |
| moonshotai/kimi-k3 | $2.35 | 23 min | 44/44 | 0.33 / 0.40 | Most scholarly matn analysis: 12 recensions (Shu'ba, Sa'id, Hushaym, Yazid b. Harun, Jarir's frame, al-Fadl's family), close to Pavlovitch's breakdown, but still backs al-Hasan. Output tokens cost $11.94/M. |
| xiaomi/mimo-v2.6-pro | $0.18 | 82 min | 43/43 | 0.17 / 0.50 | Clusters follow isnad branches well and it doubts the convergence point, but its element inventory was degenerate (one element per variant). |
| deepseek/deepseek-v4-pro-0813 | $0.85 | 67 min | 46/46 | 0.67 / 0.44 | Lists 11 CLs including Hittan; over-generous. |
| deepseek/deepseek-v4.1-flash | $0.25 | 27 min | 48/48 | 0 / 0 | Good extraction; incoherent judgement (no CLs, yet dates the text to Hittan). |
| z-ai/glm-5.3 | - | - | - | - | Did not finish: account credit ran out mid-run. |
| qwen/qwen3.8-2.4t-a95b | - | - | - | - | Ignores the JSON schema on every call (returns a bare list). |
| qwen/qwen3.8-27b | - | - | - | - | Provider returned empty replies. |
| minimax/minimax-m3 | - | - | - | - | Final answer truncated mid-JSON. |

Pavlovitch's common links are Shu'ba, Hushaym, al-Qattan, Waki', Jarir b. Hazim and Yazid b. Harun,
and he rejects al-Hasan as the source of the maxim. No model reached that reading zero-shot: all
follow the isnad convergence. That gap is what fine-tuning on reviewed analyses should close.

## Recommendation

1. Default model: **DeepSeek V4 Pro** (`deepseek/deepseek-v4-pro`). It is the cheapest model that
   completed every stage cleanly, extracts wording faithfully, and produces a coherent analysis. At
   about $0.08 per tradition, all ~20,700 hadith-kg meaning groups would cost roughly $1,700, before
   batch discounts. It is slow (about 30 minutes per tradition), which matters little when many
   traditions run in parallel.
2. Kimi K3 as an optional second opinion on a small, high-value set (for example the gold-standard
   traditions): its matn analysis is the best of the group, at about 30 times the price.
3. Fine-tuning base: Qwen3.8-27B is open and small enough to fine-tune on rented GPUs; its hosted
   endpoints were unreliable here, which does not affect self-hosted fine-tuning.

## Caveats

- One tradition, one run per model: differences of one or two common links are within noise.
- OpenRouter routes open models to different providers (and quantizations); pin providers before
  large runs so results are reproducible.
- The run cost $9.21 in total, about three times the estimate, mostly reasoning tokens on Kimi K3,
  GLM-5.3 and DeepSeek V4 Pro 0813. Large runs should cap reasoning effort or output tokens per model.

## Harness changes made during the evaluation

- Per-route wording is extracted one entry per request (24 small calls), not in one 67-route call,
  which several models had answered with one or two items.
- Extracted wording is accepted only if it occurs in its source entry (ignoring diacritics,
  punctuation, and spacing); contradictory relation labels are reported as warnings.
- Markdown-fenced JSON is unwrapped, a failed parse is retried once, and output caps were raised.
- Each analysis records the model that produced it (`analyses.model`).
