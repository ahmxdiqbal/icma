# Wording per chain

An entry in a collection can name several chains and give one or more matns. This document fixes,
for every chain the dataset lists for an entry, which words of the entry are that chain's matn.
The rules are strict on purpose: words count as a chain's matn only if the collector gives them for
that chain. A paraphrase is never treated as the same wording. Code implements these rules in
`pipeline/src/icma/analysis/wording.py`; labelled examples are in `eval/gold/chain-wording/`.

The number of chains is never decided here. It comes from the dataset (one row per chain in
`sanads`).

## The record for each chain

| Field | Meaning |
|---|---|
| `basis` | How the entry ties words to this chain (table below). |
| `wording` | Verbatim words from the entry: the whole matn for `own`, `shared` and `lafz`; only the words quoted for this chain for `partial`; none otherwise. |
| `refers_to` | For `same`, `similar`, `meaning`, `reference` and `partial`: the chain whose whole wording the collector points at. Always a chain that has a whole wording. Empty for a `partial` when no chain in the entry has a whole wording. |
| `formula` | The collector's words that link this chain to another one, verbatim, such as بهذا الإسناد مثله. |

| Basis | When | Wording |
|---|---|---|
| `own` | The matn follows a chain that no other chain shares at that point. | whole |
| `shared` | Several chains lead to one matn: teachers joined by و ("حدثنا فلان وفلان"), chains joined by ح, or "كلاهما عن". Nothing says whose words they are. | whole, the same for each |
| `lafz` | Shared, and the collector says the words are this chain's: واللفظ له، واللفظ لفلان، هذا حديث فلان، هذا لفظ فلان، لفظ فلان. | whole |
| `same` | No words; the collector says they are identical: مثله، بمثله، مثل حديث فلان، مثل ذلك. | none (the wording of `refers_to` applies) |
| `similar` | No words; the collector says they are close: نحوه، بنحوه، نحو حديث فلان. Also every other chain of a shared matn whose words the collector gives as another chain's (`lafz`). | none |
| `meaning` | No words; the collector says the sense is the same: بمعناه، ومعناه، بمعنى حديث فلان. | none |
| `partial` | Only some words are given for this chain (see "Partial wordings"). | the words quoted |
| `reference` | The chain is cited without words and without a claim about them: بهذا الحديث، فذكر الحديث، بهذا الإسناد or به on its own, or a chain the collector cites in his own comment. | none |
| `none` | The chain cannot be found in the text. | none |

Only `own`, `shared` and `lafz` give a chain words of its own. Only `same` lets a chain take
another chain's words. `similar`, `meaning`, `partial` and `reference` chains have no complete
wording.

## Where a matn starts

The matn starts after the chain's last narrator, after skipping, in order:

1. Blessings and epithets of the narrator: رضي الله عنه، رحمه الله، زوج النبي ﷺ، من أصحاب
   رسول الله ﷺ.
2. A note on the narrator that ends where "أن رسول الله" begins, such as
   "وكان عقبيا بدريا أحد نقباء الأنصار".
3. The link to the Prophet: "قال: قال رسول الله ﷺ:"، "أن رسول الله ﷺ قال:"، "عن النبي ﷺ قال:"،
   "عن النبي ﷺ أنه"، "سمعت رسول الله ﷺ يقول"، "أن النبي ﷺ"، "أن نبي الله ﷺ كان يقول".
   Without such a link, a single leading قال، قالت، قالوا، أنه قال، أخبرته.

A closing قال with an addressee and no colon stays: "أن النبي ﷺ قال لمعاوية" gives
"قال لمعاوية ...". A story that mentions the Prophet stays: in "قال: كان رسول الله ﷺ إذا نزل
عليه ..." the matn is "كان رسول الله ﷺ إذا نزل عليه ...".

When the last narrator is named inside the story of the narrator before him, the matn starts where
the story starts: "عن سعيد بن جبير قال: كنت عند ابن عمر ..." gives "كنت عند ابن عمر ...", and
"عن رجل من أهل مصر قال: سألت أبا الدرداء ..." gives "سألت أبا الدرداء ...".

## Where a matn ends

At the first of:

- The next chain, including the words that introduce it: وحدثنا، حدثنا، أخبرنا، ونا، ح، كما قد
  حدثنا، فحدثنيه.
- The collector's own comment: قال أبو داود، قال أبو عيسى، قال الشافعي، هذا حديث ...، هذا غريب،
  غريب من ...، هذا هو الصحيح، رواه ...، أخرجاه، تابعه، قد احتج ...، لم يخرجاه، لم يذكر ...، لم يرو
  هذا الحديث ...، تفرد به ...، واللفظ ل...، لفظ فلان، قلت followed by a comment on the chain.
- A closing formula: ثم ذكر مثله، فذكر الحديث، or a final "الحديث".
- Words given for only one of the chains that share the matn (see "Partial wordings").

Comments made by a narrator inside the chain stay in the matn, because the chain passes them on:
"قال الحسن: فلا أدري أمن الحديث هو أم لا" is part of what al-Hasan's students received.

## Partial wordings

A chain is `partial` when the entry gives only some of its words:

- The differences after a formula: "بهذا الإسناد غير أن في حديثهما ..."، "ومعناه، قال: ...". After
  مثله، نحوه or بمعناه, only words introduced as this chain's (غير أن، إلا أن، وزاد، قال) count;
  anything else is the collector's comment.
- The start of the matn followed by a closing formula: "... ثم ذكر مثل حديث فلان", "... وذكر
  الحديث". `refers_to` is empty when no chain in the entry has the whole wording.
- One teacher's words in a shared matn: "وفي رواية فلان: ..."، "وفي حديث فلان ..."، "وقال فلان في
  حديثه: ..."، "وزاد فلان ..."، or a bare "قال فلان: ..." when فلان is one of the joined teachers and
  not someone in the story. That teacher's chain is `partial` with those words; the shared matn
  ends before them. If the words are given for every chain of the matn, nothing is split.
- A chain the collector introduces with وزاد فلان, for what it adds.

## What a formula points at

- A formula that names a narrator ("مثل حديث ابن جعفر"، "بإسناد يحيى") points at the chain
  through that narrator. A name may be his nisba ("لفظ الحماني").
- Otherwise it points at the nearest earlier whole wording.
- If that chain is itself `same` or `partial`, follow it back to a chain with a whole wording.

## Chains with nothing after them

- A chain followed directly by ح or a new "حدثنا" shares what follows the next chain (a tahwil).
- So does a chain followed by another chain before any matn has been given, as in al-Ṭayālisī's
  "حدثنا جرير ... قال أبو داود: وذكره ابن فضالة ...".
- After a matn, a chain followed by nothing is `reference`: "قال سفيان: ثم لقيت فلانا فحدثنيه
  عن ... عن النبي ﷺ".

## Chains in the collector's comment

After the first matn, a marker such as "قال أبو داود" starts the collector's comment. A chain first
named there keeps words the collector gives for it ("تابعه سليمان ... لعن النبي ﷺ من مثل
بالحيوان"). It is `reference` when it has no words and no formula, or when the words that follow
are about chains ("روى وكيع أول هذا الحديث ... وإنما هذا إسناد حديث ابن المحبق").

## Known limits

- A collector's comment with no marker, such as al-Naḥḥās's "فبين بقول رسول الله ..." directly
  after the matn, is kept in the matn.
- One span holds one stretch of words: a chain whose words come in two pieces ("... ثم ذكر مثله
  إلا أنه قال فيه: ...") gets the first piece.
- The rules read the narrator names the dataset marks in the text (`hadith_rawis`). A chain whose
  narrators are not marked, or are marked wrongly, can be misplaced or get `none`.
- Editors' insertions in the source text, such as "سورة النساء آية 15", stay in the wording.
