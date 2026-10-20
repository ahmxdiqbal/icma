# Training a small span-segmentation model from frontier labels, noisy silver labels and a small gold set

Notes compiled 2026-10-19. Every number carries its setting. "Vendor claim" marks results published only by the model's maker. "Project" numbers come from this repository's own evaluation files. Prices were read from live pricing pages on 2026-10-19. In prose, "chain" means isnad, following `GLOSSARY.md`.

## 1. Distilling frontier-model labels into small models: how small, how close to the teacher

### Takeaway
On a narrow task, a student of 0.05B to 4B parameters trained on LLM labels usually matches the LLM that made the labels, and on held-out data it often beats that LLM used through prompting. A 50M-parameter GLiNER beat ChatGPT, whose labels it was trained on, at zero-shot NER. A 3.8B NuExtract beat its 70B labeller (vendor claim). T5 students from 220M parameters beat few-shot 540B PaLM. The students also copy their teacher's systematic errors. Labels alone trained a weaker model than human labels did in one controlled test. Almost all of this evidence is English, and I found no peer-reviewed distillation result for Arabic span extraction.

### Cited Findings
**UniversalNER (targeted distillation)**
- The distillation set came from 50K Pile passages of at most 256 tokens, labelled by gpt-3.5-turbo-0301 at temperature 0 and filtered to 45,889 passages with 240,725 entity mentions and 13,020 entity types. ([UniversalNER, ICLR 2024, arXiv 2308.03279](https://arxiv.org/html/2308.03279))
- The students were LLaMA 7B and 13B. Zero-shot average F1 on a 43-dataset, 9-domain benchmark: UniNER-7B 41.7, UniNER-13B 43.4, ChatGPT (the teacher) 34.9. ChatGPT led Vicuna by over 20 points. ([arXiv 2308.03279](https://arxiv.org/html/2308.03279))
- In the supervised setting (20 datasets), UniNER-7B averaged 84.78 F1, against 81.16 for InstructUIE-11B and 80.09 for BERT-base. ([arXiv 2308.03279](https://arxiv.org/html/2308.03279))
- Data-design ablations:
  - Frequency-based negative sampling (asking for types absent from the passage) beat no negative sampling by 21.9 F1 (53.4 vs 31.5) and uniform sampling by 5.7.
  - Definition-style prompts scored 11.8 points below plain type names.
  - Asking for all types in one query cost 3.3 points.
  - ([arXiv 2308.03279](https://arxiv.org/html/2308.03279))

**GLiNER (span-based encoder)**
- The backbone is DeBERTa-v3 (large for English, mDeBERTa-v3-base for the multilingual model). Sizes: GLiNER-S about 50M, M about 90M, L about 0.3B. All were trained on UniNER's ChatGPT-labelled Pile-NER (44,889 passages, about 240k spans, about 13k types). ([GLiNER, arXiv 2311.08526](https://arxiv.org/html/2311.08526v1); I did not confirm the peer-reviewed venue)
- Zero-shot average F1 on CrossNER + MIT (7 datasets): ChatGPT 47.5, InstructUIE-11B 47.2, UniNER-7B 53.7, UniNER-13B 55.6, GoLLIE-7B 58.0, GLiNER-S 52.7, GLiNER-M 55.4, GLiNER-L 60.9. Even the 50M model beat its teacher. ([arXiv 2311.08526](https://arxiv.org/html/2311.08526v1))
- Multilingual zero-shot on MultiCoNER (11 languages, Arabic not among them): GLiNER-Multi averaged 32.9 against ChatGPT's 29.9. It won 9 of 11 languages by the paper's table; the text says "8 of 10". ([arXiv 2311.08526](https://arxiv.org/html/2311.08526v1))
- In the supervised setting (20 datasets, up to 10,000 samples each), GLiNER-L scored 82.9 with Pile-NER pre-training and 82.1 without. UniNER-7B scored 84.8 and InstructUIE 81.2. ([arXiv 2311.08526](https://arxiv.org/html/2311.08526v1))
- GLiNER-L trained for about 5 hours on one A100 (up to 30k steps). ([arXiv 2311.08526](https://arxiv.org/html/2311.08526v1))
- GLiNER2 (Fastino) puts NER, classification and structured extraction in one model of about 205M parameters; secondary sources give 205M to 340M depending on the checkpoint. ([HF model card](https://huggingface.co/fastino/gliner2-large-v1); [EMNLP 2025 demos](https://aclanthology.org/2025.emnlp-demos.10))

**NuNER (encoder pre-trained on LLM labels)**
- gpt-3.5-turbo-0301 labelled 1.35M C4 sentences. After filtering, about 1M remained, with 4.38M entity annotations and about 200k concept types. The base model is RoBERTa-base; the paper gives both 125M and 155M parameters. ([NuNER, arXiv 2402.15343](https://arxiv.org/html/2402.15343))
- k-shot macro-F1 averaged over 4 datasets, where k is examples per entity type:

  | k | RoBERTa-base | NuNER |
  |---|---|---|
  | 1 | 24.46 | 39.37 |
  | 4 | 44.65 | 59.60 |
  | 16 | 58.12 | 67.84 |
  | 64 | 65.42 | 71.53 |

  ([arXiv 2402.15343](https://arxiv.org/html/2402.15343))
- Against UniversalNER-7B, which is about 56 times larger: at k about 8 to 16, UniNER 57.89 vs NuNER 58.75; at k about 64 to 128, UniNER 71.02 vs NuNER 70.30. ([arXiv 2402.15343](https://arxiv.org/html/2402.15343))
- Growing the pre-training set from 1K to 1M examples raised the k=8 score from 60.3 to 64.8. Growing the number of concept types from 4 to 80k raised it from 59.35 to 63.43 (100k examples). The authors conclude that diversity of label types matters more than diversity of text. ([arXiv 2402.15343](https://arxiv.org/html/2402.15343))

**NuExtract (small structured-extraction decoders; vendor claims)**
- NuExtract 1.0 (June 2024):
  - Llama 3 70B labelled 300k C4 texts against extraction templates. 50k examples survived filtering for template-following and for values present in the text. Half had part of the text deleted to teach empty fields.
  - Students: Qwen1.5-0.5B, Phi-3-mini (3.8B) and Phi-3-small (7B).
  - Claims: the 0.5B beat GPT-3.5; the 3.8B beat Llama3-70B, its own labeller, at about 35 times smaller; the 7B reached "GPT-4o levels". The benchmark had a few hundred examples, which the authors call indicative.
  - Fine-tuning on 40 examples per fold (5-fold, chemistry reaction extraction) made the 0.5B slightly better than zero-shot GPT-4o.
  - ([NuMind blog](https://numind.ai/blog/nuextract-a-foundation-model-for-structured-extraction))
- NuExtract 1.5 (Oct 2024):
  - Base: Phi-3.5-mini (3.8B), trained on English, French, German, Spanish, Italian and Portuguese. Arabic is not listed.
  - Fine-tuned on 45 examples per problem (12 problems), it was slightly worse than GPT-4o given the same 45 examples in its prompt.
  - The authors say a 0.5B model was "too small to be multilingual".
  - ([NuMind blog](https://numind.ai/blog/nuextract-1-5-multilingual-infinite-context); [model card](https://huggingface.co/numind/NuExtract-1.5))
- NuExtract 2.0 (July 2025):
  - Sizes: 2B (Qwen2-VL), 4B (Qwen2.5-VL-3B) and 8B.
  - The 8B scored 73 F on an internal benchmark of over 1,000 examples, about level with non-reasoning frontier models. The API-only PRO beat GPT-4.1 by more than 9 points.
  - The benchmark is unreleased and the training data is undisclosed.
  - ([NuMind blog](https://numind.ai/blog/outclassing-frontier-llms-nuextract-2-0))
- NuExtract3 (May 2026): built on Qwen3.5-4B. It scored 0.651 on an internal benchmark of about 600 documents, against 0.417 for base Qwen3.5-4B. The card does not mention Arabic or describe the training data. ([HF model card](https://huggingface.co/numind/NuExtract3))

**Distilling step-by-step and Self-Instruct**
- Distilling step-by-step (Findings of ACL 2023):
  - PaLM 540B produced labels plus rationales, used as multi-task targets for T5 students on e-SNLI, ANLI, CQA and SVAMP.
  - Smallest students that beat few-shot PaLM: 220M T5 on e-SNLI, 770M on ANLI and SVAMP, 1B on CQA.
  - The 770M T5 beat PaLM on ANLI with 80% of the data. Standard fine-tuning did not match PaLM with 100%.
  - ([Google Research blog](https://research.google/blog/distilling-step-by-step-outperforming-larger-language-models-with-less-training-data-and-smaller-model-sizes/); [arXiv 2305.02301](https://arxiv.org/abs/2305.02301))
- In the unlabelled setting, the student saw only teacher labels and rationales. It needed 12.5% of the data to beat standard label-only distillation on 100% (e-SNLI), and it beat the teacher LLM on 3 of 4 datasets. ([ar5iv 2305.02301](https://ar5iv.labs.arxiv.org/html/2305.02301))
- Self-Instruct (ACL 2023): GPT-3 generated and filtered its own instructions, inputs and outputs, then was fine-tuned on them. This gave a 33% absolute gain on Super-NaturalInstructions, on par with InstructGPT-001. ([arXiv 2212.10560](https://arxiv.org/abs/2212.10560))

**LLM-as-labeller pipelines**
- Across NLU and NLG tasks, GPT-3 labels reached equal downstream performance at 50% to 96% lower cost than human labels. Mixing GPT-3 and human labels did better under a fixed budget. ([Wang et al., Findings of EMNLP 2021](https://arxiv.org/abs/2108.13487))
- LLMaAA put an LLM labeller inside an active-learning loop. It used k-NN demonstrations and learnable per-example weights to down-weight noisy labels, on NER and relation extraction. Students "can outperform the teacher within only hundreds of annotated examples". ([Findings of EMNLP 2023, arXiv 2310.19596](https://arxiv.org/abs/2310.19596))
- A controlled CoNLL-2003 test (single-author arXiv preprint):
  - GPT-4 labelled 1,000 sentences; its labels scored 0.73 micro-F1 with chain-of-thought prompting and 0.65 without.
  - BERT-base trained only on those 1,000 GPT-4-labelled sentences scored 0.683 F1. Trained on 1,000 human-labelled sentences, it scored 0.850.
  - Training on 1,966 GPT-4-labelled sentences, then on the 1,000 human ones, scored 0.869. Blending all data every epoch scored 0.792.
  - ([Huang 2024, arXiv 2402.09282](https://arxiv.org/html/2402.09282v2))
- Many-shot in-context labelling (ACL 2026 Findings):
  - DeepSeek-V3 appears to be the labeller; GPT-4o was the best labeller, with DeepSeek-V3 and Qwen-72B close behind and Qwen-7B well behind.
  - BERT fine-tuned on these labels beat prior low-resource NER results by about 10 absolute F1.
  - ([Zhang et al., arXiv 2606.21890](https://arxiv.org/html/2606.21890))
- Weak-to-strong generalisation (OpenAI preprint):
  - Strong students fine-tuned on a weak supervisor's labels consistently beat the supervisor. Naive fine-tuning recovers more than 20% of the gap to the strong model's ceiling, often over 50% for the largest students. An auxiliary confidence loss raises median recovery from about 25% to nearly 80% on NLP tasks.
  - Students imitate the supervisor: agreement with the supervisor is "often noticeably higher than weak supervisor accuracy", and "systematic errors that are easy to learn" get imitated.
  - ([Burns et al., arXiv 2312.09390](https://arxiv.org/html/2312.09390))

**Arabic and hadith-specific evidence**
- AdabNER (ACL 2026) has about 876K tokens of Modern Standard Arabic literary text from 138 books, with 78,530 mentions under 21 nested tags. Fine-tuned AraBERTv2 scored F1 0.86 on stratified splits and 0.83 leaving whole books out. The best few-shot LLM, Gemini 3 Pro, scored 0.59. ([ACL Anthology](https://aclanthology.org/2026.acl-long.1541/))
- WojoodNER 2024 (Arabic fine-grained NER): winning F1 was about 91% flat and 92% nested. ([overview, arXiv 2407.09936](https://arxiv.org/abs/2407.09936)) A Command R in-context system scored F1 0.737 on fine-grained Wojood-Fine NER. ([DRU, ArabicNLP 2024](https://aclanthology.org/2024.arabicnlp-1.106/))
- The Rezwan corpus (arXiv preprint, Oct 2025) used unnamed LLMs for segmentation and chain/matn separation over 1.2M hadiths (the paper says "narrations"). Six experts rated 1,213 sampled hadiths: 9.33/10 for chain/matn separation, and 8.46/10 overall against 3.66 for the Noor corpus. No boundary-level accuracy is reported. ([arXiv 2510.03781](https://arxiv.org/abs/2510.03781))
- Earlier chain/matn segmentation work reports 92.5% accuracy with bigram features. ([Altammami, Atwell & Alsalka 2019](https://aclweb.org/anthology/W19-5605.pdf); [Altammami thesis](https://etheses.whiterose.ac.uk/id/eprint/32802/)) A PPM-compression method reports about 92.76% on one corpus and 90.10% on another. Its Anthology URL contains "retraction", so its status is unverified. ([ICON 2020](https://preview.aclanthology.org/retraction/2020.icon-main.4)) I read both only through search summaries, so the metric definitions are unchecked.
- A vendor blog reports 95% average chain-extraction accuracy on 20 hadiths from the Muwaṭṭaʾ, with 15 of 20 extracted perfectly. ([GTAF blog](https://gtaf.org/blog/evaluating-the-performance-of-our-narrator-chain-extraction-system-for-hadith-analysis/))

### Inferences
- Size: encoders of 0.05B to 0.4B already match or beat LLM teachers on span tasks when the labels are consistent (GLiNER, NuNER), and fine-tuned Arabic encoders beat prompted frontier LLMs by wide margins (AdabNER, Wojood). A 0.5B to 4B decoder earns its cost mainly when the output must be generated text. NuMind found 0.5B too small for multilingual extraction, which argues for an encoder pre-trained on Arabic over a tiny multilingual decoder.
- The "student beats teacher" results compare a fine-tuned student with a prompted teacher. The more reliable expectation for this project is that the student matches the Claude labels and copies their systematic errors. The 8% of chains where two blind Claude labellers disagreed mark where the student will be least reliable.
- Data-design lessons that transfer directly:
  - Include entries where a span type is absent, such as no comment or no formula (UniNER negative sampling, NuExtract's deleted-text examples).
  - Favour variety of structures and collections over raw volume (NuNER).
  - Mechanically reject labels whose spans are not exact substrings or do not tile the entry (NuExtract's filter).
- The Huang result suggests Claude labels should be followed by a final pass on the most trusted labels, not mixed in as one pool.
- Rationales helped on reasoning-classification tasks. No study found tests them for boundary placement. A cheap analogue here is a short reason code per boundary, naming which formula or link phrase decided it.

### Gaps
- No peer-reviewed study distils LLM labels into an Arabic or classical-Arabic span model. GLiNER-Multi's evaluation excludes Arabic, and NuExtract 1.5 does not list it.
- The teacher and training data for NuExtract 2.0 and 3 are undisclosed, and their benchmarks are unreleased.
- I did not retrieve cost figures from "Is GPT-3 a good data annotator?" (ACL 2023, [arXiv 2212.10450](https://arxiv.org/abs/2212.10450)).
- The Rezwan corpus does not name its models or give boundary accuracy.

## 2. How much labelled data a fine-tuned small model needs before it plateaus, and encoders vs LoRA decoders

### Takeaway
For token-level extraction with a pre-trained encoder, published curves rise steeply over the first few hundred to 2,000 labelled sentences. One 2026 study of BERT trained on LLM labels found a plateau around 2,500 sentences. Task-specific pre-training on LLM labels matters most at the smallest sizes, about 100 examples or fewer. Segmentation adapters improve with 10 to 100 examples. A fine-tuned 7B decoder (UniNER) scored about 2 to 5 F1 above 0.1B to 0.3B encoders in supervised multi-dataset NER, at 20 to 60 times the parameters. Decoders need their causal attention mask removed to label sequences well. I found no clean side-by-side learning curve at 100, 500, 1,000, 5,000 and 10,000 examples.

### Cited Findings
**Learning curves and data sizes**
- BERT trained on LLM-labelled data (CrossNER AI and Literature domains, 0.5k to 5k sentences in 0.5k steps) improved "rapidly with the first 1.5k-2k annotated examples, but plateaus after around 2.5k samples". The authors recommend 1.5k to 2.5k sentences. ([Zhang et al., ACL 2026 Findings](https://arxiv.org/html/2606.21890))
- In the same study, the LLM labeller's quality rose as its human-labelled prompt examples grew to about 75 to 100, with marginal gains after. ([arXiv 2606.21890](https://arxiv.org/html/2606.21890))
- GLiNER's Pre-training on LLM labels added 5.6 F1 at 100 training samples per dataset, and "the gap shrinks as data grows". Full supervision used up to 10,000 samples per dataset. ([arXiv 2311.08526](https://arxiv.org/html/2311.08526v1))
- NuNER's k-shot curve (Section 1 table) shows RoBERTa-base rising from 24.46 to 65.42 macro-F1 between 1 and 64 examples per type. The pre-training advantage narrows from about 15 points to about 6 over that range. ([arXiv 2402.15343](https://arxiv.org/html/2402.15343))
- BERT-base trained on 1,000 human-labelled CoNLL-2003 sentences scored 0.850 F1. ([arXiv 2402.09282](https://arxiv.org/html/2402.09282v2)) Fully supervised RoBERTa on CoNLL-2003 scored 90.11 in the BOND paper's table; its README lists 91.21. ([BOND, ar5iv](https://ar5iv.labs.arxiv.org/html/2006.15509); [README](https://github.com/cliang1453/BOND))
- With active learning, a CNN-CNN-LSTM tagger reached 99% of the best full-data deep model's F1 using 24.9% of OntoNotes-5.0 English (1,088,503 training words) and 30.1% of Chinese (756,063 words). It started from 1% random data and added 20,000 words per round. ([Shen et al., arXiv 1707.05928](https://ar5iv.labs.arxiv.org/html/1707.05928))
- Segment-any-Text sentence segmentation can be adapted with LoRA from "10-100 segmented training sentences", per the project docs. The paper reports adaptation to lyrics and legal documents. ([SaT, arXiv 2406.16678](https://arxiv.org/html/2406.16678v2); [GitHub](https://github.com/bminixhofer/wtpsplit))
- NuExtract students fine-tuned on 40 to 45 examples per problem reached about GPT-4o level on vendor benchmarks. ([NuMind blog 1.0](https://numind.ai/blog/nuextract-a-foundation-model-for-structured-extraction); [1.5](https://numind.ai/blog/nuextract-1-5-multilingual-infinite-context))
- AdabNER's 876K tokens support F1 0.86 with AraBERTv2. Joint multi-domain training cut the out-of-domain loss to under 1 F1. ([ACL 2026](https://aclanthology.org/2026.acl-long.1541/))
- Under a fixed budget for domain adaptation, "spending all funds on annotation leads to the best performance" at small budgets. Larger budgets favour adding in-domain pre-training. ([Bai, Ritter & Xu, EMNLP 2021](https://arxiv.org/abs/2109.04711)) A search summary put the small-budget line below $800; the abstract page gives no figure.
- A general annotation handbook places the start of a plateau near 2,000 examples in a classification example. It notes that one trained model gives only one point on an unknown curve. I read this only through a search summary. ([arXiv 2310.11780](https://arxiv.org/pdf/2310.11780))
- Fine-tuned BERT-like models beat zero-shot GPT-3.5, GPT-4 and Claude Opus on every classification task tested (news, tweets, speeches). ([Bucher & Martini, arXiv 2406.08660](https://arxiv.org/abs/2406.08660))

**Encoders vs LoRA-tuned decoders**
- Supervised NER over 20 datasets: UniNER-7B scored 84.78, GLiNER-L (0.3B encoder) 82.9 and BERT-base 80.09. ([UniNER](https://arxiv.org/html/2308.03279); [GLiNER](https://arxiv.org/html/2311.08526v1))
- Ettin trained paired encoders and decoders from 17M to 1B parameters on the same data (up to 2T tokens). Encoders were better at classification and retrieval, and a 400M encoder beat a 1B decoder on MNLI. Continued training to switch objective did worse than training with the native objective. ([Ettin, ICLR 2026, arXiv 2507.11412](https://arxiv.org/abs/2507.11412))
- Removing the causal mask in selected layers makes fine-tuned decoder LLMs competitive with state-of-the-art sequence labelling, and better than MLM encoders per the abstract. ([Dukić & Šnajder, Findings of ACL 2024](https://arxiv.org/abs/2401.14556))
- Seven decoder LLMs (Gemma, Qwen2.5, Llama 3.1, Llama 3.2) were given full attention and label-supervised training. With a suitable LoRA setup they beat BERT, RoBERTa and DeBERTa, though not the state of the art on BC5CDR or CoNLL-2003. ([Yano & Takamura, BioNLP 2026](https://aclanthology.org/2026.bionlp-1.25/))
- Eight open LLMs tuned with parameter-efficient methods and structured outputs (inline brackets or XML) were "competitive with traditional encoder-based models" and beat in-context learning. ([Zhan, Wang & Huang, EMNLP 2026 Findings, arXiv 2601.17898](https://arxiv.org/abs/2601.17898)) A search snippet says LoRA beat full fine-tuning by 0.1 to 0.5 F1 for Llama3.1-8B and Qwen2.5-7B on CoNLL-2003 and GENIA. I did not verify this.
- At large scale in code and maths (100K instruction pairs, or 20B tokens of continued pre-training), LoRA "substantially underperforms" full fine-tuning but forgets less. ([Biderman et al., TMLR 2024](https://arxiv.org/abs/2405.09673))
- On materials-science extraction (128 abstracts), fine-tuned GPT-4o beat BERT-CRF in one domain. BERT-CRF became comparable once more examples from the second domain were added. ([IMMI 2025, arXiv 2504.03979](https://arxiv.org/abs/2504.03979))

**Project**
- One round of rule fixes on 81 entries raised accuracy on unseen entries from 41% to 61% of chains. "Each new sample brings forms the vocabulary lacks." ([eval/chain-wording-2026-10-18.md](/Users/ahmediqbal/Documents/icma/eval/chain-wording-2026-10-18.md))

### Inferences
- The general NER evidence puts the knee of an encoder's curve at 1,000 to 3,000 sentences. A hadith entry holds several boundary decisions over hundreds of tokens, so a labelled entry carries more supervision than a CoNLL sentence. The binding constraint is coverage of rare structures, which the project's own curve shows still growing: Bukhārī's nested chains, a matn placed before its chain, split wording, and open-ended collector formulas.
- Run the learning curve at roughly 250, 500, 1k, 2k, 5k and 10k Claude-labelled entries, with 3 seeds each, on a frozen test set.
  - Stratify training samples by collection.
  - Report accuracy per structure as well as overall, because the overall curve can flatten while rare structures still improve.
- Start with an Arabic encoder doing token classification. Try a LoRA decoder (with bidirectional attention, or generating inline-tagged output) only if the encoder plateaus below target. Published gaps for a fine-tuned 7B decoder are about 2 to 5 F1, at 20 to 60 times the parameters. I did not check whether UniNER used LoRA or full fine-tuning.

### Gaps
- No study compares an encoder with a LoRA decoder on one span task at 100, 500, 1k, 5k and 10k examples. The per-size F1 values in arXiv 2606.21890 appear only in figures.
- I found no learning-curve study for classical Arabic segmentation, and no study at all for chain/matn boundaries with neural models.
- A JMIR AI 2024 sample-size study of BERT and GPT NER ([JMIR AI](https://ai.jmir.org/2024/1/e52095)) did not load, so its numbers are unknown.

## 3. Weak supervision and noisy silver labels: can a model trained on noisy rule labels beat the rules?

### Takeaway
Often it can, by a few to about 13 F1. That held when the noise was mostly missing labels and the model was pre-trained (BOND, Snorkel). On WRENCH's sequence-tagging average, though, end models only matched the aggregated labels and stayed about 18 F1 below gold-trained models. Students copy errors that are systematic and easy to learn, which describes the dataset's habit of cutting off the start of the matn. The most reliable gain is to train on the small clean set as a final stage, not to hold it back only for validation.

### Cited Findings
- Snorkel (VLDB 2017) improved predictive performance by 132% on average over prior heuristic approaches. It came within about 3.6% of large hand-labelled training sets. In a user study, experts built models 2.8 times faster than with seven hours of hand labelling, and 45.5% better on average. ([arXiv 1711.10160](https://arxiv.org/abs/1711.10160))
- WRENCH (NeurIPS 2021 Datasets & Benchmarks) covers 22 datasets, 8 of them sequence tagging, and over 120 method variants. ([arXiv 2109.11377](https://arxiv.org/abs/2109.11377)) Sequence-tagging averages ([ar5iv](https://ar5iv.labs.arxiv.org/html/2109.11377)):

  | Training labels | Model | Avg F1 |
  |---|---|---|
  | Weak, aggregated | CHMM label model (best) | 66.32 |
  | Weak, from CHMM | BERT end model | 66.50 |
  | Weak | LSTM-CNN-CRF | 62.97 |
  | Gold | BERT | 84.36 |
  | Gold | LSTM-CNN-CRF | 79.83 |

  Neural end models trained on weak labels "does not guarantee" a gain, especially when the labelling functions are poor.
- BOND (KDD 2020) used knowledge-base matching to label NER data. Those labels were high-precision and low-recall: on CoNLL03, precision 81.13 and recall 63.75. BOND results, all F1 ([ar5iv 2006.15509](https://ar5iv.labs.arxiv.org/html/2006.15509)):

  | Dataset | KB-matching labels | BOND | Supervised RoBERTa |
  |---|---|---|---|
  | CoNLL03 | 71.40 | 81.48 | 90.11 |
  | Tweet | 35.83 | 48.01 | 52.19 |
  | OntoNotes5 | 59.51 | 68.35 | 86.20 |
  | Webpage | 52.45 | 65.74 | 72.39 |
  | Wikigold | 47.76 | 60.07 | 86.43 |

- BOND's first stage alone (fine-tuning on the distant labels with early stopping) beat the labels by 4 to 11 F1. Its second stage is self-training. Removing early stopping dropped CoNLL03 from 75.61 to 72.11. ([ar5iv 2006.15509](https://ar5iv.labs.arxiv.org/html/2006.15509))
- With a small strongly labelled set and a large weakly labelled one, naive or weighted mixing "does not necessarily improve, or even deteriorate" performance. NEEDLE's fix has three stages: complete the weak labels, train with a noise-aware loss, then fine-tune on the strong data. It reported F1 of 93.74 on BC5CDR-chem, 90.69 on BC5CDR-disease and 92.28 on NCBI-disease. ([Jiang et al., ACL 2021](https://arxiv.org/abs/2106.08977))
- The gains of sophisticated weakly supervised methods are "significantly overestimated", because they rely on clean validation samples. Training on those samples directly removes most of the advantage, even with five samples per class. ([Zhu et al., ACL 2023](https://arxiv.org/abs/2305.17442))
- LLM labels first, then human labels, scored 0.869 F1, against 0.850 for human labels alone. Blending everything scored 0.792. ([arXiv 2402.09282](https://arxiv.org/html/2402.09282v2))
- Weak-to-strong training ([arXiv 2312.09390](https://arxiv.org/html/2312.09390)):
  - Students imitate easy-to-learn systematic supervisor errors.
  - With a large gap between supervisor and student, performance can peak and then decline before one epoch ends.
  - Early stopping on ground-truth labels added about 15 points of gap recovery in NLP over training to the end. The authors note this is not a valid method, since it uses test labels.
- Confident learning estimates the joint distribution of given and true labels, assuming class-conditional noise. It then prunes, counts and ranks examples. It is the basis of the open-source cleanlab. ([Northcutt, Jiang & Chuang, JAIR 2021](https://arxiv.org/abs/1911.00068))
- For token classification, 11 methods that score sentences from per-token predicted probabilities were compared on real CoNLL-2003 label errors. One simple method consistently found the sentences containing errors. ([Wang & Mueller, NeurIPS 2022 InterNLP workshop](https://arxiv.org/abs/2210.03920))
- CrossWeigh trains models on k folds to flag likely label mistakes in each held-out fold, then re-weights them. It found mistakes in about 5.38% of CoNLL03 test sentences. ([arXiv 1909.01441](https://arxiv.org/abs/1909.01441))
- On MNIST, networks kept over 90% test accuracy with 100 random labels per clean label. Robustness held under several noise patterns, including bias toward confusable classes. Higher noise needs a larger dataset. ([Rolnick et al., arXiv 1705.10694](https://arxiv.org/abs/1705.10694))
- Project: on round-2 single-chain entries, the dataset's own matn boundaries were right on 11 of 21 and the rules on 16 of 21. ([eval/chain-wording-2026-10-18.md](/Users/ahmediqbal/Documents/icma/eval/chain-wording-2026-10-18.md))

### Inferences
- The silver errors are systematic: the matn start is cut off in a learnable way. A model trained on raw silver will learn the cut. BOND's gains came from labels that were incomplete but precise, a different noise type from wrong boundaries.
- The documented remedies:
  - Repair silver with the rules where the rules are known to be better.
  - Or mask the uncertain region from the loss, treating tokens between the dataset boundary and the rule boundary as unlabelled. This is the role of NEEDLE's label completion and noise-aware loss.
  - Or keep only silver entries where independent signals agree.
- Recommended order: (1) optionally pre-fine-tune on repaired or filtered silver with early stopping; (2) fine-tune on Claude labels; (3) do a final short pass on human-checked or doubly agreed labels; (4) choose stopping points on a clean dev set that is separate from the test set.
- A self-training loop is cheap at this scale:
  - Label all 400k entries with the student.
  - Keep confident, rule-consistent predictions, retrain, and watch the clean dev set for drift.
  - Run cleanlab-style ranking on the silver and Claude labels, and send the worst-ranked entries back to Claude or a human.
- The student can beat the rules on the structures where the rules fail only if Claude labels cover those structures. Silver data alone teaches the rules' and the dataset's blind spots.

### Gaps
- I found no weak-supervision study for Arabic or classical-Arabic segmentation, and none that isolates systematic boundary-shift noise in span segmentation.
- WRENCH does not compare end models with the accuracy of individual labelling functions on one scale.

## 4. Active learning and disagreement-based selection for the expensive labeller

### Takeaway
Uncertainty-based active learning matched full-data NER with about 25 to 30% of the labels in a classic study. Uncertainty-based routing between humans and an LLM beat random routing by up to 21%. But gains are inconsistent across models, and they can vanish when the model that picks examples differs from the model later trained. Disagreement between independent systems is a cheap selector. In this project, rules and DeepSeek agreed on 53% of chains and were right on 93% of those, so most errors sat in the disagreements.

### Cited Findings
- Shen et al. compared least confidence, length-normalised log-probability (MNLP), BALD and random sampling. They reached 99% of full-data F1 with 24.9% (English) and 30.1% (Chinese) of OntoNotes-5.0, and beat a shallow baseline with 12.0% and 16.9%. ([ar5iv 1707.05928](https://ar5iv.labs.arxiv.org/html/1707.05928))
- "The benefits of current approaches do not generalize reliably across models and tasks". Training a later model on actively acquired data "does not consistently outperform training on i.i.d. sampled data", because active learning ties the dataset to the model that chose it. ([Lowell, Lipton & Wallace, arXiv 1807.04801](https://arxiv.org/abs/1807.04801))
- Survey of active learning for NLP ([Zhang, Strubell & Hovy, EMNLP 2022](https://arxiv.org/html/2210.10109v2)):
  - Committee strategies measure disagreement by vote entropy, KL divergence or variation ratio.
  - For structured outputs, "full-match can be too strict", so partial disagreement scored by F1 is used, and selection can be "choosing uncertain tokens from uncertain sentences".
  - Active learning picks harder instances that cost more to label, and annotation time is "probably the best cost measurement".
  - A mismatch between the selecting model and the final model "may make the gains from AL be negligible or even negative". A smaller distilled model used for selection loses little.
- CoAnnotating assigns each instance to humans or ChatGPT according to the LLM's uncertainty. It gained up to 21% over random allocation. ([EMNLP 2023, arXiv 2310.15638](https://arxiv.org/abs/2310.15638))
- LLMaAA students trained on actively selected LLM labels beat the LLM teacher within hundreds of examples. ([arXiv 2310.19596](https://arxiv.org/abs/2310.19596))
- GPT-3 labels cut labelling cost by 50 to 96% at equal performance, and mixing them with human labels helped under a fixed budget. ([arXiv 2108.13487](https://arxiv.org/abs/2108.13487))
- LLM cascades that escalate to a bigger model only when needed matched GPT-4 with up to 98% cost reduction, or beat it by 4% at equal cost. ([FrugalGPT, arXiv 2305.05176](https://arxiv.org/abs/2305.05176))
- Project, rules vs DeepSeek V4 Pro on 79 round-2 chains:
  - They agreed on 42 and were right on 39 (93%; Wilson 95% interval about 81% to 98%, my calculation).
  - On the 37 where they disagreed, only the rules were right on 10 and only the model on 11.
  - The file says "neither on 19", but the counts add up only if 19 is the total across all 79 chains: 3 agreed-wrong chains plus 16 among the disagreements. The totals confirm this reading: rules 49/79 = 39 + 10, and model 50/79 = 39 + 11.
  - A second blind Claude labeller matched the first on 55 of 60 chains (92%).
  - ([eval/chain-wording-2026-10-18.md](/Users/ahmediqbal/Documents/icma/eval/chain-wording-2026-10-18.md))

### Inferences
- A practical selector for Claude labelling ranks entries by a committee of cheap signals:
  - The rules and the student disagree on a boundary.
  - The rules and the dataset's matn boundary disagree.
  - The student's margin at the predicted boundary tokens is low.
  - The entry contains a formula missing from the rules' vocabulary.
- On the project's 79-chain sample, labelling only the disagreements would have covered 47% of chains while catching most errors. It would have caught 37 of the 40 chains that the rules or the model got wrong, and 27 of the rules' 30 errors. That is a small sample, and the 93% figure has a wide interval.
- Mix in a random slice, about 10 to 20% of each labelling batch. It keeps accuracy estimates unbiased and guards against Lowell et al.'s selection coupling.
- Select with the architecture that will be deployed, or a distilled copy of it.
- Count cost in tokens per entry, not chains. Selected entries will be longer and harder, so they will cost more per entry and Claude's agreement on them will likely fall below 92%. Two independent Claude labels plus adjudication are worth considering for that slice.

### Gaps
- I found no study measuring label savings from rule-vs-model disagreement selection specifically, and no active-learning study on Arabic segmentation.
- CoAnnotating's datasets and cost figures are not on its abstract page.

## 5. Cost and compute

### Takeaway
Frontier labelling, not GPU time, sets the budget. Claude Opus 5.5 through the Batch API costs $2 per million input tokens and $10 per million output tokens. Under the assumptions below, that is about 2 cents per entry, or roughly $180 per 10,000 entries, and output tokens dominate. The project measured DeepSeek V4 Pro at $0.014 per entry. A training run on 10,000 labelled entries costs cents to about a dollar on one rented GPU at $1 to $4 per hour. One epoch over all 400k silver entries is an estimated 1 to 8 GPU-hours, under $15.

### Cited Findings
- Claude API prices per million tokens (docs read 2026-10-19):

  | Model | Input | Output | Cache hits |
  |---|---|---|---|
  | Opus 5.5 | $4 | $20 | $0.20 |
  | Sonnet 5.5 | $2 | $10 | $0.10 |
  | Haiku 5.5 (prompts up to 100k tokens) | $0.10 | $0.50 | $0.01 |
  | Opus 5 and 4.5 to 4.8 | $5 | $25 | |
  | Fable 5.1 and Mythos 5.1 | $10 | $50 | |

  Opus 5.5 5-minute cache writes cost $5. ([Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing))
- The Batch API gives "a 50% discount on both input and output tokens": Opus 5.5 $2/$10, Sonnet 5.5 $1/$5, Haiku 5.5 $0.05/$0.25. Caching multipliers "stack with other pricing modifiers, including the Batch API discount". ([Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing))
- Project costs:
  - DeepSeek V4 Pro cost $0.014 and one to four minutes per entry on the chain-wording task. All 96,163 multi-chain entries would cost about $1,350. ([eval/chain-wording-2026-10-18.md](/Users/ahmediqbal/Documents/icma/eval/chain-wording-2026-10-18.md))
  - A full ICMA analysis cost $2.35 per hadith on Kimi K3, whose output tokens cost $11.94 per million. The comparison run cost three times its estimate, mostly reasoning tokens. ([eval/model-selection-2026-10-17.md](/Users/ahmediqbal/Documents/icma/eval/model-selection-2026-10-17.md))
- Lambda on-demand single-GPU prices per hour: H100 SXM $4.29, H100 PCIe $3.29, GH200 $2.29, A100 40GB $1.99, A10 $1.29, A6000 $1.09, B200 $6.99. ([Lambda pricing](https://lambda.ai/pricing))
- RunPod prices per hour (community / secure): H100 SXM $2.69/$3.99, H100 PCIe $1.99/$2.89, A100 80GB PCIe $1.19/$1.79, A100 SXM $1.39/$1.79, L40S $0.79/$1.09, RTX 4090 $0.34/$0.89, RTX 5090 $0.69/$1.19, L4 $0.44/$0.59, H200 $3.59/$5.29. ([RunPod pricing](https://www.runpod.io/pricing))
- Training compute is about C = 6PD floating-point operations, with forward about 2PD and backward about 4PD, for P parameters and D tokens. About 120 TFLOP/s per A100 is a rule-of-thumb achievable rate in large-model training; GPT-NeoX reached 150 to 180. Mixed-precision AdamW needs about 2 bytes per parameter for weights, 12 for optimiser states and 2 to 4 for gradients, before activations. ([EleutherAI, Transformer Math 101](https://blog.eleuther.ai/transformer-math/))
- The H100 SXM is rated 1,979 BF16 TFLOPS "with sparsity", about 990 dense. ([NVIDIA H100](https://www.nvidia.com/en-us/data-center/h100/))
- Training-time anchors:
  - GLiNER-L (0.3B) trained in about 5 hours on one A100. ([arXiv 2311.08526](https://arxiv.org/html/2311.08526v1))
  - QLoRA fine-tunes a 65B model on one 48GB GPU, and its best model family needed "24 hours of finetuning on a single GPU". ([arXiv 2305.14314](https://arxiv.org/abs/2305.14314))
  - LoRA Land fine-tuned 310 4-bit LoRA models across 31 tasks. On average they beat their base models by 34 points and GPT-4 by 10, and 25 adapters were served from one A100 80GB. ([arXiv 2405.00732](https://arxiv.org/abs/2405.00732))

### Inferences
These are my own arithmetic under stated assumptions; measure real token counts with the token-counting API before budgeting.
- Labelling cost per entry. Assume a 10k-token cached rules prompt, a 1k-token entry and 1.5k output tokens, on Opus 5.5 Batch with a cache-hit price of $0.10 per million after the batch discount:

  | Item | Tokens | Cost |
  |---|---|---|
  | Cached rules prompt | 10,000 | $0.001 |
  | Entry text | 1,000 | $0.002 |
  | Output | 1,500 | $0.015 |
  | Total per entry | | about $0.018 |

  - That is about $18 per 1k entries, $180 per 10k, $900 per 50k and $7,200 for all 400k.
  - 4k extra thinking tokens per entry add about $0.04, giving about $0.058 per entry.
  - Sonnet 5.5 Batch halves these figures, and Haiku 5.5 Batch costs about $0.0005 per entry.
  - Output is about 80% of the cost. Asking for boundary positions or the first and last words of each span, instead of re-quoting each span, cuts cost the most.
- Training compute per epoch over all 400k entries. Assume 500 tokens per entry, so D = 2e8 tokens:

  | Model | Approx. FLOPs | Assumed rate | Time on one A100 | Cost at $1.19 to $1.99/h |
  |---|---|---|---|---|
  | 0.15B encoder, full fine-tune | 1.8e17 | 60 TFLOP/s | 0.8 h | $1 to $1.7 |
  | 0.4B encoder, full fine-tune | 4.8e17 | 60 TFLOP/s | 2.2 h | $2.6 to $4.4 |
  | 1.5B decoder, LoRA | about 1.2e18 | 120 TFLOP/s | 2.8 h | $3.3 to $5.5 |
  | 4B decoder, LoRA | about 3.2e18 | 120 TFLOP/s | 7.4 h | $9 to $15 |

  - The 60 TFLOP/s rate for small models is half the large-model rule of thumb, an assumption.
  - The LoRA rows assume about 4PD, since the frozen weights need no weight gradients. That is my approximation, not a sourced figure.
  - Training on 10k labelled entries (5e6 tokens) takes minutes per run, so a 20-run hyperparameter sweep stays under about $20.
- Memory at 16 bytes per parameter: full fine-tuning of a 4B model needs about 64GB before activations, so an 80GB card. LoRA on a 4B model needs about 8GB of bf16 weights plus activations, which fits 24 to 48GB cards. A 0.15B to 0.4B encoder fits anything listed.
- Under these assumptions, labelling 10k entries with Opus 5.5 ($180 to $580) costs 10 to 100 times more than the fine-tuning runs that use them. Labelling choices dominate the budget.

### Gaps
- Claude's token count per Arabic word is not published, so it needs measuring.
- I did not verify whether prompt-cache hits are guaranteed inside Batch API jobs.
- I found no controlled published cost report for LoRA-tuning 0.5B to 4B models on a few thousand extraction examples, and no sourced utilisation figures for sub-1B models. The training estimates above are arithmetic, not measurements.

## 6. Evaluation practice: held-out sets, agreement ceilings, leakage

### Takeaway
Freeze a test set that no rule, prompt, threshold or checkpoint choice has touched. Split it by hadith group or collection, not by entry, and size it for the gap you need to detect. At about 150 chains, a 95% interval on 61% accuracy is about ±8 points. Agreement between two Claude labellers (92%) is neither a ceiling on student accuracy nor a measure of label accuracy, because models from the same family share errors. A human-checked slice is needed to calibrate both.

### Cited Findings
- Gorman & Bedrick (ACL 2019, Outstanding Paper) re-ran nine part-of-speech taggers from 2000 to 2018. Results replicated on the standard split, but on random splits some rankings could not be reproduced. They recommend random and multiple splits plus significance tests. ([ACL Anthology P19-1267](https://aclanthology.org/P19-1267/))
- Most comparisons on GLUE-sized test sets are underpowered. Machine-translation test sets of 2,000 sentences have about 75% power to detect a 1 BLEU difference. ([Card et al., EMNLP 2020](https://arxiv.org/abs/2010.06595))
- Ten common test sets average at least 3.3% label errors; ImageNet validation has at least 6%. When test labels are corrected, ResNet-18 overtakes ResNet-50 if the prevalence of originally mislabelled test examples rises by 6%. ([Northcutt et al., NeurIPS 2021 D&B](https://arxiv.org/abs/2103.14749))
- About 5.38% of CoNLL03 test sentences contain label mistakes, at a time when top F1 was about 93%. ([CrossWeigh, arXiv 1909.01441](https://arxiv.org/abs/1909.01441))
- Inter-annotator agreement is not a ceiling on machine performance; many real systems exceed it. ([Boguslav & Cohen, MEDINFO 2017](https://ebooks.iospress.nl/pdf/doi/10.3233/978-1-61499-830-3-298)) Simulations show a well-specified model can beat agreement, "especially if" the annotators are noisy. ([Richie, Grover & Tsui, BioNLP 2022](https://aclanthology.org/2022.bionlp-1.26))
- Across over 350 LLMs, when two models both erred on one leaderboard dataset, they chose the same wrong answer about 60% of the time. Larger, more accurate models have more correlated errors, even across providers. ([Kim et al., ICML 2025](https://arxiv.org/abs/2506.07962); [PMLR](https://proceedings.mlr.press/v267/kim25e.html))
- GPT-4 annotation across 27 tasks and 11 datasets was "highly contingent on both the dataset and the type of annotation task". Any LLM annotation should be validated against human labels. ([Pangakis et al., arXiv 2306.00176](https://arxiv.org/abs/2306.00176))
- Leakage errors affected 329 papers across 17 fields, in 8 types. The authors propose model info sheets. In civil-war prediction, every claim that complex models beat logistic regression failed once leakage was fixed. ([Kapoor & Narayanan, arXiv 2207.07048](https://arxiv.org/abs/2207.07048))
- Clean validation data used for model selection inflates the apparent gains of weak-supervision methods. ([Zhu et al., ACL 2023](https://arxiv.org/abs/2305.17442)) Early stopping on test labels inflated weak-to-strong results by about 10 to 15 points of gap recovery. ([arXiv 2312.09390](https://arxiv.org/html/2312.09390))
- AdabNER scored 0.86 F1 with stratified splits and 0.83 leaving whole books out, so grouped splits lower the measured score. ([ACL 2026](https://aclanthology.org/2026.acl-long.1541/))
- Project: the rules were built on ʿUbāda (67 chains), fixed on round 1 (185 chains), then frozen. "Round 2 is the only fair test": 81 entries and 172 chains. ([eval/chain-wording-2026-10-18.md](/Users/ahmediqbal/Documents/icma/eval/chain-wording-2026-10-18.md)) hadith-kg groups entries into about 20,700 meaning groups. ([eval/model-selection-2026-10-17.md](/Users/ahmediqbal/Documents/icma/eval/model-selection-2026-10-17.md))

### Inferences
- Statistical precision (my calculations):

  | Measure | Point estimate | 95% interval |
  |---|---|---|
  | Rules on 151 unseen multi-chain chains | 92/151 = 61% | ±7.8 points (SE 0.040) |
  | Labeller agreement on 60 chains | 55/60 = 92% | about 82% to 96% (Wilson) |

  - Chains cluster within entries (60 multi-chain entries), which widens both intervals.
  - Detecting a 5-point gap between two systems at 80% power needs about 1,450 chains if the test sets are independent. Scoring both systems on the same chains with McNemar's test, at the 27% discordance seen between rules and DeepSeek, needs about 850.
- Keep three disjoint sets, split by meaning group so that versions of one hadith never straddle train and test:
  - Training: Claude labels and silver.
  - Dev: Claude-labelled, for early stopping, thresholds and prompt or rule changes.
  - Test: frozen, double-labelled, with an adjudicated or human-checked core.
  - Once decisions have been made from the test set, label a fresh one, as the project did with round 2. Also hold out whole collections to measure transfer to unseen collectors' styles.
- The 92% agreement between two Claude Opus labellers overstates label accuracy whenever they share mistakes, which Kim et al. find likely for strong same-family models. To bound the true error rate, have a human expert check a random slice of about 100 to 200 chains, and use a different model family as a second labeller. The student should be scored against adjudicated gold, with student-teacher agreement reported separately, because a student can exceed teacher-labeller agreement (Richie et al.) or merely copy the teacher.
- Report:
  - Chain-level exact match (the project's strict metric) and entry-level exact match.
  - Boundary error in words, so near-misses are visible.
  - Breakdowns by structure type and by collection.
  - Intervals on every number.

### Gaps
- No source says how many human-checked items are needed to validate LLM labels; the Pangakis abstract gives no number.
- Claude's accuracy against human experts on classical Arabic chain/matn boundaries is unmeasured; no published study was found.
