# Wording per chain: rules or a model (2026-10-18)

Question: can code decide which words of an entry are each chain's matn, or does this step need a
model? The rules are in `docs/chain-wording.md`; the code is
`pipeline/src/icma/analysis/wording.py`.

## Method

- Gold labels come from Claude Opus 5.5 labellers that read the rules document and never saw the
  code's output (`eval/gold/chain-wording/`). A chain counts as right only if its basis, its exact
  words and the chain it refers to all match.
- Three sets: the 'Ubada hadith (24 entries with several chains, 67 chains), round 1 (81 entries
  sampled from the 20 collections with the most multi-chain entries, 185 chains) and round 2
  (81 fresh entries, 172 chains).
- The rules were built on 'Ubada, then fixed on round 1, then frozen. Round 2 is the only fair
  test.
- DeepSeek V4 Pro got the same rules document as its prompt and labelled 30 of the round 2
  multi-chain entries before the OpenRouter credit ran out.
- A second blind labeller relabelled one round 2 packet to measure how consistent the rules allow
  labelling to be.

## Results

| | Chains right | Entries fully right |
|---|---|---|
| Rules on 'Ubada (built on it) | 67/67 | 24/24 |
| Rules on round 1, first run | 83/185 | |
| Rules on round 1, after fixes | 159/185 | 68/81 |
| **Rules on round 2, multi-chain entries (unseen)** | **92/151 (61%)** | **34/60** |
| **Rules on round 2, single-chain entries (unseen)** | **16/21** | |
| Dataset's own matn boundaries, round 2 single-chain entries | 11/21 | |
| Rules on the 30 entries DeepSeek finished | 49/79 (62%) | 17/30 |
| DeepSeek V4 Pro on the same 30 entries | 50/79 (63%) | 19/30 |
| Second labeller against the first, round 2 packet a | 55/60 (92%) | 25/27 |

On the 79 chains both methods labelled:

- They agree on 42 chains and are right on 39 of them (93%).
- On the other 37 they disagree: only the rules are right on 10, only the model on 11, and neither on
  16. Across all 79 chains, neither is right on 19 (16 disagreements plus 3 shared errors).

DeepSeek cost $0.014 and one to four minutes per entry. All 96,163 multi-chain entries in
hadith-kg would cost about $1,350.

## What fails

The rules place chains and formulas well: the basis is right for 150 of 172 round 2 chains.

Most errors are where a matn starts or ends. The collectors' phrasing is open-ended: links to the
Prophet ("يرفعه إلى النبي ﷺ قال"), comment markers ("كذا قال"، "متن غريب"، "قال شيخنا"، "قال
البزار"), and remarks that introduce further chains ("فحدثت بذلك ابن عباس وأبا هريرة فقالا صدق").
Each new sample brings forms the vocabulary lacks. One round of fixes raised accuracy on unseen
entries from 41% to 61%.

The rest are structures that are rare but real:
- Bukhārī's nested chains.
- A matn given before its chain.
- Words for one chain split into two pieces.
- Dataset chains that do not match the text.

## Conclusions

1. The number of chains is never in question; it comes from the dataset. This step only decides
   wording.
2. A general open-weight model is no better than the rules here, at real cost. Switching this step
   to DeepSeek is not worth it.
3. Both are far below the 92% consistency two careful labellers reach under the same rules, so the
   rules document is precise enough. What is missing is coverage of the collectors' phrasing.
4. The dataset's matn boundaries drop the start of many matns (often the revelation scene), so the
   rules should replace them for single-chain entries too.
