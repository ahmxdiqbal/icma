# Tradition package (schema v1)

One JSON file per tradition, written by `pipeline/src/icma/export.py` and read by the web app. The
pipeline is the source of truth for every structural fact; the web app only renders.

Example: `data/derived/ubada-khudhu-anni.json` (regenerate with the command in `pipeline/README.md`).

## Top level

| Field | Type | Notes |
|---|---|---|
| `schema_version` | `1` | |
| `id`, `title_en` | string | |
| `generated_at` | ISO 8601 string | |
| `source` | object | dataset, url, license, attribution, `selection: {group_id, anchor_narrator_ids}`. The attribution must be shown in the UI (CC BY 4.0). |
| `corrections_applied` | Correction[] | Manual fixes applied to source chains (`op`: `replace` with `from_narrator_id`/`to_narrator_id`, `set_links` with the full corrected `links`, `exclude`), with reason, evidence, author, date. Unused fields are null. Authors ending in `(unreviewed)` were proposed by a model. |
| `books` | Book[] | `id, title_ar, author_ar, author_death_ah, category_ar, edition{publisher_ar, city_ar, printing_ar}` |
| `narrators` | Narrator[] | `id, name_ar, display_name_ar, tabaqa, grade_code, grade_ar, death_ah, death_ah_raw, residence_ar, has_tadlis, has_ikhtilat, in_bukhari, in_muslim, is_stub` |
| `hadiths` | Hadith[] | `id, book_id, number_in_book, page, type (qudsi/marfu/mawquf/maqtu), grade_ar, text_ar, matn_span [start,end] or null, mentions[{start,end,narrator_id or null}], translation_en, translation_source` |
| `chains` | Chain[] | `id, hadith_id, grade_ar, in_bundle, links[]`, links ordered earliest authority first, collector last. A link is `{kind:"narrator", narrator_id}` or `{kind:"gap", gap}` with gap in `irsal, inqita, taliq, mubham`. |
| `bundle` | Bundle | See below. |

Text offsets are Unicode code point indices into `text_ar`. All hadith-kg text is in the Basic
Multilingual Plane, so they equal JavaScript string indices.

One hadith entry can carry several chains (a collector citing more than one route for the same
text). `grade_code` 1 is a companion; higher numbers are weaker grades, as listed in `grade_ar`.

## Bundle

Node keys: `prophet`, `n:<narrator_id>`, `g:<gap>:<chain_id>:<index>`. Gap nodes are unique per
chain position, because two unnamed or missing links are never the same person.

| Field | Meaning |
|---|---|
| `root` | Always `prophet`. Chains of non-Prophetic reports have no root link. |
| `nodes[]` | `key, kind (prophet/narrator/gap), narrator_id?, gap?, chain_ids, min_depth, student_keys, collector_keys, independent_branch_count, corroborated_branch_count, single_strand_branch_count` |
| `edges[]` | `source` (teacher) to `target` (student), with `chain_ids` |
| `cl_candidates` | Narrator keys with at least two corroborated independent branches, most chains first |
| `suggested_cl` | The convergence point: the candidate with the most chains, or null. Not a judgement. In the Ubada test case the published study (Pavlovitch 2011) rejects this node and places the common links lower, on matn grounds. Label it as a convergence point in any UI. |
| `spiders` | Seeming common links: at least two long single strands and no corroborated branch |
| `dives[]` | Chains that reach an authority above the suggested CL without passing through it: `chain_id, departs_from, rejoins_at` |
| `upper_paths[]` | Distinct paths above the suggested CL (gaps grouped by kind as `g:<gap>`), with `chain_ids` |
| `warnings[]` | `code, message, chain_ids`. Codes: `repeated_narrator`, `too_short` (chain excluded), `reversed_edge` |

Definitions (from `bundle.py`): a node's branches are the chains leading to each of its students. Two
branches are dependent if they share any transmitter below the node; meeting only at the final
collector keeps them independent. A group of branches is corroborated if it splits again below the
node, and a single strand if it is one path with at least two transmitters before its collector.
