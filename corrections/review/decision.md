# Pending corrections: review and decision (2026-10-17)

Two reviewers assessed the 11 held-back proposals independently (`reviewer-a.json`, `reviewer-b.json`).

| Chains | A | B | Decision |
|---|---|---|---|
| 185630, 185631, 185632, 392492, 247747, 433470 (break between al-Hasan and 'Ubada) | accept | accept | applied |
| 325756 (same break, consistency only) | accept | accept | applied, with the reason corrected |
| 423855, 423856 (restore al-Hasan; text reads "الحسن بن حطان") | accept | accept | applied |
| 519675 (restore al-Hasan from parallels) | accept | accept | applied; flagged as parallel-based, exclude from text-extraction training |
| 257833 (break between Ibn Muharrar and Hittan, on dates) | accept | reject | rejected, see `rejected.json` |

Rule applied: a chain records the claim its entry makes, labelled the way hadith-kg labels the same
claim elsewhere. A break marker is added when the source marks the same narrator pair as broken in
comparable chains, not on dates alone (the source leaves about 98% of large-tabaqa-gap links
unmarked). A narrator is restored only when the entry keeps a trace of him or the same route
through the same people names him.

Both reviewers found that the audit's evidence for 185630-185632 quoted words that are not in that
entry; the evidence was rewritten from the entry's actual text before applying. Side effect noted by
reviewer A: five applied chains now show a break while their source grade (`hukum`) still says
"إسناده متصل".
