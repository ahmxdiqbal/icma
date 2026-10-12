# Audit of the 'Ubada "khudhu 'anni" chains

Date: 2026-10-11. Author: claude audit agent (unreviewed).
Input: `data/derived/ubada-khudhu-anni.json` (meaning group 730), 98 hadith entries and 141 chains, with the chain 32757 correction already applied.
Outputs in this directory: `ubada-audit-2026-10-11.json` (26 proposed corrections, passes `load_corrections`), `ubada-audit-verdicts.jsonl` (141 lines, one per chain).

Every entry was read against its Arabic text, in order, with the chains rendered as names. Doubtful identities, carried-over isnads and collector records were checked in `hadith-kg.db`.

## Verdicts

| Verdict | Chains |
|---|---|
| verified | 111 |
| corrected | 27 (26 proposed here, plus 32757 from the existing correction file) |
| uncertain | 3 |
| not_this_tradition | 0 |

The meaning-group clustering was clean. All 98 entries carry the "khudhu 'anni" saying or its Salama b. al-Muhabbiq version. That includes al-Hasan's mursal in 'Abd al-Razzaq (chain 257797) and the fragment quoted from al-Bukhari's Tarikh in Tarikh Dimashq (519676 to 519680).

## Corrections proposed

| Chain(s) | Hadith | Source | Problem | Op |
|---|---|---|---|---|
| 75751 | 58360 | Musnad Ahmad 22186 | Zawa'id of 'Abd Allah b. Ahmad ("حدثنا عبد الله، حدثنا شيبان") credited to Ahmad | replace 488 with 4657 |
| 91342 | 70555 | Ibn Hibban 4517 | Homonym: Ibn al-Junayd al-Busti (d. 303) replaced by Ibn al-Junayd al-Razi (d. 347), who could not have heard Qutayba (d. 240). The text mention already has the right id | replace 29727 with 29676 |
| 415225 | 418334 | al-Tamhid 1432 | Tahwil: Muhammad b. al-Jahm's route hung under 'Abd al-Warith instead of Ahmad b. Qasim | replace 46153 with 9658 |
| 185630, 185631, 185632 | 145632 | Ma'rifat al-Sunan 4442 | al-Hasan to 'Ubada with no break marker | set_links, add inqita |
| 392492 | 398184 | Sharh al-Sunna 2584 | same | set_links, add inqita |
| 325756 | 315707 | Juz' Abi al-Tahir 32 | same | set_links, add inqita |
| 247747 | 203777 | Musnad al-Shafi'i (Sanjar) 956 | al-Shafi'i missing as collector, no break marker | set_links |
| 433470 | 490451 | al-Wasit 203 | al-Wahidi missing, no break marker | set_links |
| 339290 | 327236 | Amali Ibn Bishran 836 | Ibn Bishran missing as collector | set_links, append 43982 |
| 350750, 350751 | 344019, 344020 | al-I'tibar 375, 376 | al-Hazimi missing | set_links, append 68171 |
| 421701, 421702 | 423603, 423604 | al-Tahqiq 1903, 1904 | Ibn al-Jawzi missing | set_links, append 44890 |
| 433469 | 490450 | al-Wasit 202 | al-Wahidi missing | set_links, append 75250 |
| 450327 | 517964 | al-Anwar 23 | al-Baghawi missing | set_links, append 75058 |
| 423855, 423856 | 425692 | al-Istidhkar 879 | Text corruption "الحسن بن حطان" made al-Hasan disappear; Ibn 'Abd al-Barr missing | set_links |
| 519675 | 627864 | Tarikh Dimashq 52057 | Ibn 'Asakir missing; al-Hasan absent between al-Fadl b. Dalham and Qabisa | set_links |
| 519676 to 519680 | 627870 | Tarikh Dimashq 52063 | al-Bukhari quotes al-Fadl b. Dalham with no informant, so a taliq is needed; Ibn 'Asakir missing | set_links |
| 257833 | 222430 | Musannaf 'Abd al-Razzaq 12990 | 'Abd Allah b. Muharrar (t7) shown hearing Hittan (t2, d. 71) | set_links, add inqita |

Two of these rest on parallels outside the entry's own text. Chain 519675 restores al-Hasan because every other copy of the Waki' to al-Fadl isnad has him, including Ibn al-Jawzi's quotation through the identical Hibat Allah, Ibn al-Mudhhib, al-Qati'i, 'Abd Allah route. Chains 423855 and 423856 rely on the same author's isnad in al-Tamhid. A reviewer who wants the chains to follow the stored text literally should drop those insertions and keep the collector fix.

## Error patterns

A chain can show more than one pattern, so the counts overlap.

1. **Collector missing (18 chains, 9 books).** For al-Shafi'i via Sanjar (57), Ibn Bishran's second Amali (139), al-Hazimi (164), Ibn al-Jawzi (237), al-Istidhkar (241), al-Jassas (242), al-Wahidi (255), al-Baghawi's al-Anwar (272) and Tarikh Dimashq (303), `sanad_rawis.pos = 0` holds the author's informant and never the author. The chain stops one link short and the informant becomes the collector in the bundle. 17 chains are fixed. Al-Jassas has no `rawis` record, so 424600 stays uncertain.
2. **Unmarked break between al-Hasan and 'Ubada (7 chains).** The dataset marks this break with inqita in 9 other chains of the same tradition, including the identical al-Shafi'i, 'Abd al-Wahhab, Yunus route. Al-Shafi'i's own comment in several entries says al-Hasan put Hittan between himself and 'Ubada.
3. **Unmarked suspension (5 chains).** Al-Bukhari's "قال: الفضل بن دلهم ... سمع الحسن" in his Tarikh is a ta'liq. The dataset joined al-Bukhari to al-Fadl directly.
4. **Narrator dropped after a defective text (3 chains).** In two, "عن الحسن عن حطان" was corrupted to "الحسن بن حطان" and one mention span covers both names. In the third, the stored Tarikh Dimashq text omits al-Hasan.
5. **Wrong identity (2 chains, plus 32757).** One homonym and one zawa'id collector.
6. **Route misassignment in multi-route entries (1 chain, plus 32757).** A narrator from one route was placed in another.
7. **Unmarked chronological break (1 chain).**

## Uncertain chains

- **113242** (Abu 'Awana, hadith 87552). The text reads "قثنا المبارك عن قتادة ... كلاهما عن الحسن", and the chain follows it. Three other copies of Yunus b. Habib, Tayalisi, Mubarak go straight to al-Hasan with no Qatada: Tayalisi 581 and Ibn Abi Hatim 5028 and 13384.
- **355174** (al-Marwazi, al-Sunna 297). "قال: وحدث الحسن" follows a Qatada tafsir passed down by Shayban (no. 296). The speaker is probably Qatada, which would replace the dataset's taliq with Marwazi, 'Ubayd Allah b. Sa'd, al-Husayn b. Muhammad, Shayban, Qatada. The wording "نكّس أصحابه" matches Qatada's students. That is likely but not proven.
- **424600** (al-Jassas). The links match the text, but the collector cannot be added because al-Jassas has no narrator record.

## Routes the dataset never built

The available ops cannot add these:

- Ma'rifat al-Sunan 4442 (hadith 145632): al-Shafi'i's second route "أخبرنا الثقة من أهل العلم عن يونس بن عبيد عن الحسن عن حطان" has no chain. Its mentions are unannotated, and the text carries `/18` and `L2415` artifacts from broken source links. The same route through al-Hazimi (350750) is present.
- Collector comments with no route of their own, such as Ibn Hazm's "ورواه أيضا شعبة وهشام", al-Bukhari's "وقال قتادة وسلام", al-Bazzar's al-Fadl remark and al-Bayhaqi's "رُوّينا عن يزيد بن زريع". Leaving these out is correct.

## Systematic issues a script can find

Counts below are over the whole of `hadith-kg.db`. Scripts are in the session scratchpad (`corpus_checks.py`, `corpus_checks2.py`, `corpus_inversion_isnad.py`).

1. **Author missing at pos 0.** In 85,415 of the 563,234 chains where both dates are known, the pos-0 narrator died at least 40 years before the book's author. These fall in 297 books, led by Tarikh Dimashq (15,256), Tahdhib al-Kamal (8,533), Ithaf al-Khiyara (7,308) and al-Matalib al-'Aliya (4,473). A weaker test, no single pos-0 narrator covering half a book's chains, flags 78 of 423 books and 127,133 chains. Zawa'id and takhrij compilations quote other collectors on purpose, so the fix has to be decided book by book. It also needs a books-to-rawis author mapping, which the schema lacks, and some authors (al-Jassas) have no record at all.
2. **Zawa'id of 'Abd Allah b. Ahmad.** 850 Musnad Ahmad entries open "حدثنا عبد الله" with no following "حدثني أبي". 908 of their 967 chains end at Ahmad, which makes Ahmad the student of his son's teachers. 32 of the entries are wijada ("وجدت في كتاب أبي") and need separate handling.
3. **Unmarked breaks.** Corpus-wide, al-Hasan is linked straight to 'Ubada in 12 chains and through inqita in 16. More generally, 10,565 edges (in 10,561 chains) have a t1 teacher with a t6+ student, or a t2 teacher with a t7+ student, and no gap. That list is a candidate set, because tabaqa labels are noisy. A better source is the `aqwal` table: critics' statements of the form "لم يسمع من" can be parsed into a list of known non-hearing pairs.
4. **Route misassignment in tahwil entries.** In the isnad section (mentions before `matn_start`), a teacher should be mentioned after his student at least once. 730 chains break this rule, 643 of them in multi-chain entries. In this tradition the check flags exactly 415225. Spot checks elsewhere found real errors: sanads 3107 and 3113 (Bukhari, hadith 2480) turn "وأفهمني بعضه أحمد" into Ahmad being taught by Abu al-Rabi', and sanad 3603 (hadith 2879) puts Muhammad b. Jubayr between al-Zuhri and Malik b. Aws on the strength of an aside. False positives also occur (sanad 1062), so precision is unmeasured. Running the check over the whole isnad text gives 4,622 hits and is too noisy, because "تابعه" back-references trigger it.
5. **Homonyms and chain/mention disagreement.** In 91342 the text mention has the right narrator and the chain has a namesake. Ibn Hibban alone has 52 chains with record 29727 (d. 347) directly under Qutayba (d. 240). Seventeen of those texts say "ببست", which names the Busti shaykh. Two checks catch this: compare each chain narrator with the mention at the same position in the text (skipping entries that open with a carried isnad: "وعن", "وبه", "قال"), and flag edges where the student died more than 100 years after the teacher (13,650 edges, 13,372 chains, again a candidate set).
6. **Carried isnads are usually right.** Entries opening "وعن منصور" (Tabarani's Awsat) or "قال أحمد" (Ibn al-Jawzi) had the right prefix filled in from the earlier entry. One case (al-Marwazi 297) became a taliq instead, so the carry-over logic is worth testing on texts that open with a bare "قال".
