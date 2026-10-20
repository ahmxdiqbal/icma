# Span tagging versus generation for typed, verbatim segmentation of hadith entries

Scope: fine-tuned models under about 8B parameters, facts as of 2026-10-19. Vocabulary follows
`GLOSSARY.md`: in prose, "chain" means the task's `isnad` span type, and "entry" means the whole
string being segmented. Each finding carries a flag for how much of the source I read:
**[full text]** means I read the relevant part of the paper or docs. **[abstract only]** means I saw
only the abstract or listing page. **[search summary]** means I saw only a search-engine summary,
so check those numbers before reusing them.

## 1. Head-to-head: fine-tuned encoder token classifiers versus fine-tuned small decoder LLMs

### Takeaway
On supervised span labelling, encoders match or beat generative decoders many times their size. A
decoder clearly wins only when it is turned into a bidirectional token classifier, with the causal
mask removed and a labelling head added. Even then the gain on CoNLL03 is 2 to 3 F1, from a 7B
decoder against the 355M RoBERTa-large. Generative decoders lead mainly in zero-shot or very
low-data settings, and on essay segmentation scored with tolerant metrics. I found no study that
plots where the two approaches cross over as training data grows.

### Cited Findings

**Controlled comparison of the two architectures**
- Ettin trained 5 encoder/decoder pairs (17M to 1B parameters) on the same data, architecture and
  recipe. Encoders did best on classification and retrieval, and decoders on generation.
  Continued training on the other objective did worse than training with the right one from the
  start. A 400M encoder beat a 1B decoder on MNLI. The material I read has no token-level task.
  [abstract only] ([Weller et al., arXiv 2507.11412](https://arxiv.org/abs/2507.11412);
  [ICLR 2026 poster](https://www.iclr.cc/virtual/2026/poster/10006491))

**Decoders fine-tuned as token classifiers (no generation)**
- CoNLL03 test micro-F1, using QLoRA (rank 64 on query and value matrices) and a softmax labelling
  head:
  - RoBERTa-base 0.883, RoBERTa-large 0.900.
  - Llama2-7B: 0.744 with the causal mask kept, 0.908 with it removed in all layers, 0.920 with
    the best layer-wise setting.
  - Mistral-7B: 0.756 with the mask kept, 0.927 with it removed.
  - The best decoders beat RoBERTa-large by 2.0 points (Llama2) and 2.7 points (Mistral). With
    the mask kept, they trail it by 14 to 16 points.
  
  [full text] ([Dukić and Šnajder, arXiv 2401.14556](https://arxiv.org/html/2401.14556v1)). Review
  listings give the published title as "Looking Right is Sometimes Right"
  ([review page](https://www.themoonlight.io/en/review/looking-right-is-sometimes-right-investigating-the-capabilities-of-decoder-only-llms-for-sequence-labeling)).
  I did not verify the venue.
- LS-LLaMA: removing the causal mask raised NER F1 by 18.43% on CoNLL03 and 14.69% on OntoNotes
  compared with the masked model. The unmasked LLaMA-2-7B beat BERT-large and RoBERTa-large on NER.
  [search summary] ([Li et al., arXiv 2310.01208](https://arxiv.org/pdf/2310.01208))
- BioNLP 2026: the authors took seven decoders from the Gemma, Qwen2.5, Llama3.1 and Llama3.2
  families, replaced causal attention with full attention, and trained them with label
  supervision. With a suitable LoRA setup they beat BERT, RoBERTa and DeBERTa baselines, but did
  not reach state of the art on BC5CDR or CoNLL2003. Model sizes and F1 values were not retrievable
  because the PDF could not be read. [abstract only]
  ([Yano and Takamura, BioNLP 2026](https://aclanthology.org/2026.bionlp-1.25/))

**Decoders fine-tuned as generators, compared with encoders**
- Naamapadam covers 11 Indian languages and uses strict CoNLL span-level F1.
  - mBERT and XLM-R beat every generative architecture in 10 of the 11 languages.
  - Four decoders were fine-tuned with LoRA on 4-bit NF4 weights.
  - The strongest generative competitor, Gemma-2-2B, averaged F1 0.427. Encoders led by 7.5 to
    40 points.
  - The best few-shot result reached about 28% of the encoder baseline.
  - This is a preprint (30 August 2026) and not peer reviewed. [abstract only]
    ([Mahesh et al., arXiv 2608.29959](https://arxiv.org/abs/2608.29959))
- GNER paper tables:
  - Supervised average F1: GNER-T5-xxl (11B) 86.15, GNER-LLaMA-7B 86.09, UniNER-7B 85.07,
    InstructUIE (11B) 81.53.
  - Zero-shot average F1: GNER-T5-xxl 69.1, GNER-LLaMA-7B 66.1, GLiNER-L 63.2, GoLLIE-7B 59.9,
    UniNER-7B 53.4, ChatGPT 47.5.
  
  [full text] ([Ding et al., Findings of ACL 2024, arXiv 2402.16602](https://arxiv.org/html/2402.16602v2))
- GLiNER is a compact bidirectional encoder that extracts entities in parallel. Its abstract
  claims it outperforms "both ChatGPT and fine-tuned LLMs in zero-shot evaluations". [abstract
  only] ([Zaratiana et al., arXiv 2311.08526](https://arxiv.org/abs/2311.08526)). A search
  summary of its out-of-domain table puts UniNER-7B ahead on CoNLL03 (72.2 vs 64.6). It puts
  GLiNER-L ahead on MIT Movie (57.2 vs 42.4) and FindVehicle (41.9 vs 22.2). [search summary]
- UniversalNER distils ChatGPT's NER ability into LLaMA. Zero-shot, it beats ChatGPT by 7 to 9 F1
  on average across 43 datasets. In the supervised setting it beats InstructUIE "by a large
  margin". [abstract only] ([Zhou et al., ICLR 2024](https://arxiv.org/abs/2308.03279))
- GoLLIE is fine-tuned to follow annotation guidelines. It improves zero-shot results on unseen
  information extraction tasks, and the authors find that detailed guidelines are key. [abstract
  only] ([Sainz et al., ICLR 2024](https://arxiv.org/abs/2310.03668))
- A biomedical benchmark of 12 datasets found that conventional fine-tuning of BERT or BART beat
  zero-shot and few-shot LLMs on most tasks. Open LLMs needed fine-tuning to close the gap. I did
  not retrieve per-task NER numbers. [abstract only]
  ([Chen et al., Nature Communications 2025, arXiv 2305.16326](https://arxiv.org/abs/2305.16326);
  [journal listing](https://www.doaj.org/article/532d4c7fbb00466d816e9724cc0ff599)). An AMIA
  abstract says an instruction-tuned LLaMA2-7B (BioNER-LLaMA) matched fine-tuned PubMedBERT.
  [search summary] ([AMIA abstract](https://amia.secure-platform.com/symposium/gallery/rounds/82001/details/11230))
- Two clinical studies. I could not see whether the decoders in either were fine-tuned.
  - Japanese clinical concept recognition: token-classification encoders were more effective than
    instruction-tuned decoders. [search summary] ([JMIR 2026](https://www.jmir.org/2026/1/e78681))
  - Lung-cancer reports: instruction-based LLM NER had much lower F1, caused by low recall
    despite high precision. [search summary]
    ([Computers in Biology and Medicine 2025](https://www.sciencedirect.com/science/article/pii/S0010482525010169))
- Financial NER: fine-tuned RoBERTa reached weighted F1 of about 0.879. LLaMA-8B under direct
  prompting, with no fine-tuning, reached about 0.784. [search summary]
  ([arXiv 2501.02237](https://arxiv.org/pdf/2501.02237))

**Segmentation and argument mining**
- Essay argument segmentation:
  - QLoRA (r=16, 4-bit) on Qwen2.5-7B, Llama-3.1-8B and Gemma-2-9B, trained on 3,353 essays
    (29,440 arguments).
  - Llama-3.1-8B reached 87.52 macro token-level F1 (BIO). That is 18.05 points above a
    Longformer token classifier, which implies about 69.5.
  - The Longformer was trained "following Ding et al. (2023)". The paper does not say plainly
    whether it was retrained on the same split.
  
  [full text] ([Favero et al., arXiv 2502.14389](https://arxiv.org/html/2502.14389v2))
- Small open LLMs fine-tuned on a paired-tag scheme segment argument components at quality
  "comparable to human expert annotators" on several benchmarks. Downstream classification on
  their segments matches pipelines built on human segments. I saw no encoder comparison and no
  numbers. [abstract only] ([Caputo et al., Findings of EACL 2026](https://aclanthology.org/2026.findings-eacl.272/))
- Legal argument types: neither fine-tuning nor prompting LLMs beat a domain-pretrained encoder.
  [search summary] ([NLLP 2025](https://preview.aclanthology.org/ingest-emnlp/2025.nllp-1.20.pdf))
- An LLM argument-mining system improves substantially when given gold components, so finding
  spans is its main bottleneck. Its authors note that exact span matching punishes small
  deviations heavily. [search summary] ([arXiv 2605.13793](https://arxiv.org/pdf/2605.13793))
- Sentence segmentation (the LLMs here were prompted, not fine-tuned):
  - On clean text averaged over 81 languages, a 3-layer XLM-R tagger (SaT+SM) scored 91.6 F1,
    prompted Llama 3 8B 79.1, and Command R 55.6.
  - On short sequences, Llama 3 8B (77.8) beat SaT+SM (71.3). After LoRA adaptation, SaT scored
    81.8 and took the lead.
  
  [full text] ([Frohmann et al., EMNLP 2024, arXiv 2406.16678](https://arxiv.org/html/2406.16678v2))
- The DISRPT 2025 discourse shared task capped closed-track models at 4B parameters
  ([DISRPT 2025 site](https://sites.google.com/view/disrpt2025)). Search summaries show the
  decoder entries targeted relation classification. I found no decoder-based segmentation entry.
  [search summary]

**Training-data size**
- GPT-NER prompts GPT-3 and marks entities inline. It is comparable to supervised baselines on full
  data and much better when training data is extremely scarce. This is a large API model, outside
  the size limit, and it was the only data-size contrast I found. [abstract only]
  ([Wang et al., arXiv 2304.10428](https://arxiv.org/abs/2304.10428))
- SaT+LoRA trains about 1% of the parameters (rank 16). With only 16 sentences it improves markedly
  on the unadapted model and beats WtP-PUNCT by almost 10 F1. [full text]
  ([arXiv 2406.16678](https://arxiv.org/html/2406.16678v2))

### Inferences
- For six fixed span types with supervised data, the evidence makes an encoder tagger the default.
  An unmasked 7B decoder gains 2 to 3 F1 over RoBERTa-large on English news NER at about 20 times
  the parameters. For classical Arabic, how well the pretraining matches the domain is likely to
  matter more than that gain, and none of these studies test it.
- A middle path keeps exact offsets and still uses a decoder's multilingual pretraining: fine-tune
  a small decoder (0.5B to 3B) as a bidirectional token classifier. The BioNLP 2026 work covers
  the Qwen2.5 and Llama3.2 families, which include small sizes, but I did not see which sizes it
  tested.
- The strongest result for generative segmentation (Favero et al.) uses a tolerant metric
  (token-level BIO F1) and a weakly documented baseline. It does not carry over to a requirement
  of verbatim spans with exact boundaries.
- The project's own evaluation points the same way.
  - On unseen multi-chain entries, the project's rules get 61% of chains right, and a prompted
    DeepSeek V4 Pro gets 63% on 30 entries.
  - Most errors are where a matn starts or ends, because collectors' phrasing is open-ended
    ([eval/chain-wording-2026-10-18.md](/Users/ahmediqbal/Documents/icma/eval/chain-wording-2026-10-18.md)).
  - Placing boundaries from context is what a token tagger is trained to do, and prompting a large
    general model did not help. The evidence favours a trained boundary model over a bigger
    prompted one.
- The gold set has about 186 entries (24 'Ubāda, 81 in round 1, 81 in round 2). That is small for
  six types plus rare structures. The studies above train on thousands of examples (3,353 essays;
  CoNLL03). Expect to need silver labels from the rules plus corrected samples.

### Gaps
- No controlled study compares encoders with fine-tuned small decoders across training-set sizes
  on span extraction or segmentation.
- No comparison exists on classical Arabic or hadith data.
- I could not retrieve F1 tables for BioNLP 2026, NER numbers for Chen et al. 2025, or JMIR 2026
  details. The PDF or landing pages failed to load.
- I did not verify the parameter counts of GLiNER-L and UniNER as used in the GNER tables.

## 2. Output formats for generative span extraction and their failure modes

### Takeaway
Free generation never guarantees verbatim output. Models asked to copy their input still drop,
add and "correct" words, even after fine-tuning. Character offsets are the weakest format, because
subword models do not see characters. Generative pipelines that work either align the output back
to the input and discard what does not align, or constrain decoding so that the only legal output
is the input's own words in order (with tags inserted) or indices into those words.

### Cited Findings

**Verbatim span strings, then alignment to the input**
- LangExtract:
  - It asks for exact text and maps each extraction to a character interval.
  - It sets `char_interval = None` when the text cannot be found, and users filter those out.
  - It warns that models sometimes extract from the few-shot examples instead of the input.
  - It chunks long inputs (`max_char_buffer=1000`) and runs several passes
    (`extraction_passes=3`) for recall.
  
  [README] ([google/langextract](https://github.com/google/langextract))
- An information-extraction study with GPT-style models found that predicted spans often enclose
  the gold span or sit inside it. It replaced strict start/end matching with a difflib similarity
  threshold of 0.5. [search summary] ([arXiv 2305.14450](https://arxiv.org/pdf/2305.14450))

**Inline tagging: rewrite the input with markers**
- GPT-NER wraps entities in `@@`/`##` markers ("@@Columbus## is a city"). It adds a
  self-verification step because LLMs confidently label non-entities. [abstract only]
  ([arXiv 2304.10428](https://arxiv.org/abs/2304.10428))
- GNER regenerates every input word followed by its label, as `word(label)`.
  - Generated words still differ from the input. Among the mismatches:
    - Omissions: 39% (LLaMA) and 23% (T5).
    - Additions: 3% and 2%.
    - Substitutions: 58% and 75%.
  - Examples: "Manattan" corrected to "manhattan", "brontë" cut to "bront", and words repeated
    through exposure bias.
  - A Hunt-Szymanski LCS matcher (O(N log N), 17.3x faster than naive LCS on inputs of 100 to 200
    tokens) maps the output back to the input.
  - Keeping the non-entity words in the output raised F1 from 59.0 to 61.8 in a pilot study, but
    lengthens the output.
  
  [full text] ([arXiv 2402.16602](https://arxiv.org/html/2402.16602v2))
- In SaT's LLM baselines, Llama 3 8B and Command R were told to add newlines and change nothing
  else. They still altered about 1.5% and 2% of the characters in song lyrics. The authors aligned
  outputs with Needleman-Wunsch, and chunks that failed to align got no boundaries. [full text]
  ([arXiv 2406.16678](https://arxiv.org/html/2406.16678v2))
- Fine-tuned 7B to 9B models in the essay study:
  - They were asked to insert `<SEP>` and to "Preserve all original words, spacing, and order".
  - They still added or omitted words and inserted extra separators. The authors spell-corrected
    the essays beforehand to reduce this.
  - Fine-tuned models needed more retries and failed more often than few-shot ones. Each item got
    up to five retries and was then discarded.
  - Some configurations have no results because of repeated failures.
  
  [full text] ([Favero et al., arXiv 2502.14389](https://arxiv.org/html/2502.14389v2))
- Caputo et al. replaced a single separator with paired tags that mark relevant versus surrounding
  content, citing the single-separator approach's limits. [abstract only]
  ([Findings of EACL 2026](https://aclanthology.org/2026.findings-eacl.272/))

**Character offsets and pointer indices**
- I found no study that measures how often small LLMs emit wrong character offsets. Two pieces of
  related evidence:
  - An MT error-annotation dataset built a "tag-to-span" protocol to keep LLM-predicted span
    indices consistent with character positions. [search summary]
    ([SiniticMTError, arXiv 2509.20557](https://arxiv.org/pdf/2509.20557))
  - An ACL 2025 paper argues that byte-pair encoding hides the characters inside tokens, and
    trains character-position prediction to compensate. [search summary]
    ([ACL 2025](https://preview.aclanthology.org/setup/2025.acl-long.194))
- Yan et al. use BART to generate each entity as a sequence of pointer indices into the input. One
  format covers flat, nested and discontinuous NER. [search summary]
  ([ACL-IJCNLP 2021, arXiv 2106.01223](https://arxiv.org/abs/2106.01223))

**Constrained decoding**
- Grammar-constrained decoding with input-dependent grammars (Geng et al.):
  - For constituency parsing, the grammar "reproduces the input... in left-to-right order",
    adding labels and brackets.
  - With LLaMA-33B, 8-shot and not fine-tuned, valid outputs rose from 64.2% to 100% and F1 from
    42.9 to 54.6. On entity disambiguation, accuracy rose from 54.1 unconstrained to 80.3. A valid
    output is not necessarily a correct one.
  - Problems:
    - BPE can tokenize the same string in several ways, which the authors patched with ad hoc
      spacing.
    - Constrained beam search tends to pick the empty string unless outputs are
      length-normalized.
    - Their CPU implementation added 11 to 44 ms per token.
  
  [full text] ([Geng et al., EMNLP 2023](https://aclanthology.org/2023.emnlp-main.674);
  [arXiv HTML](https://arxiv.org/html/2305.13971v6))
- vLLM structured outputs:
  - Constraints are set per request: `choice`, `regex`, `json`, `grammar` (EBNF) and
    `structural_tag`.
  - Backends are xgrammar and guidance. Outlines and lm-format-enforcer are named for their regex
    dialects.
  - Constraints are passed as `extra_body={"structured_outputs": ...}` online or
    `SamplingParams(structured_outputs=...)` offline.
  - The old `guided_*` fields were removed in v0.12.0. The docs call grammar constraints "the
    hardest option to use".
  
  [docs] ([vLLM structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs.html))
- XGrammar claims up to 100x speedup over earlier engines and near-zero overhead for grammar-
  constrained generation in serving. [abstract only]
  ([Dong et al., MLSys 2025, arXiv 2411.15100](https://arxiv.org/abs/2411.15100))

### Inferences
- Format ranking for hadith entries, given the verbatim requirement:
  1. **Copy-with-tags under a hard constraint.** At each step, allow only the next token of the
     pre-tokenized input, or a tag token at a word boundary. This guarantees verbatim output and
     exact offsets by construction. Forcing the input's own token sequence also avoids the BPE
     ambiguity Geng et al. hit. It can be built as a per-entry EBNF grammar in vLLM or as a custom
     logits processor. Output length is about the input length.
  2. **Indices over pre-numbered words (pointer style).** The prompt numbers the words, and the
     output is "type start-end" per segment under a regex. The output is tiny. Whether the ranges
     are in order and cover the entry is checked after decoding. How reliably a small model reads
     the numbers is not benchmarked in anything I found.
  3. **Verbatim strings plus alignment.** This is the simplest, but it needs fuzzy alignment and
     a reject path. Arabic spelling variation (hamza forms, tā' marbūṭa, alif maqṣūra, diacritics)
     gives the model room for the "corrections" GNER and SaT observed.
  4. **Character offsets.** Avoid them.
- Removing diacritics before tagging, as the hadith-segmentation-bert card advises, is safe only if
  the pipeline keeps a map from normalized to original character positions.

### Gaps
- No study compares formats head-to-head for fine-tuned small decoders on one task.
- I found no figures for the compile cost of a per-request grammar with about 1,000 literals in
  XGrammar or guidance.
- I found no measured offset-error rates.

## 3. Text segmentation: methods and inputs longer than 512 tokens

### Takeaway
Typed, contiguous segmentation is well served by per-token tagging: BIO labels, or a
begin-of-segment flag plus a type. A CRF or constrained Viterbi pass can forbid invalid label
sequences, but it changes accuracy by about 1 F1 or less, in either direction. Its value is
stability and well-formed output. Entries longer than 512 tokens need either an encoder with a
native 8,192-token context (mmBERT, AraModernBERT) or sliding windows with overlap. The one
published hadith chain/matn tagger simply truncates at 512.

### Cited Findings
- SaT design:
  - XLM-R, 3 layers by default, predicting a sentence-boundary probability per token.
  - Decision thresholds of 0.025 (limited lookahead) and 0.25 (SaT+SM).
  - Attention lookahead limited to 48 tokens in total across layers.
  - Trained on 256-token windows and run at XLM-R's 512-token context.
  
  [full text] ([arXiv 2406.16678](https://arxiv.org/html/2406.16678v2))
- CATS stacks two Transformers, one over tokens and one over sentences, and trains them jointly on
  boundaries and a coherence objective ([Glavaš and Somasundaran, AAAI 2020](https://ojs.aaai.org/index.php/AAAI/article/view/6284)).
  A follow-up found that full fine-tuning overfits to Wikipedia-style training data, and that
  adapter-based fine-tuning transfers much better. [search summary]
  ([BEA 2021](https://preview.aclanthology.org/fix_video/2021.bea-1.11.pdf))
- CRF versus softmax heads. All of these are [search summary]:
  - Across languages, BERT-CRF performed about the same as BERT or slightly worse, with lower
    variance across runs ([arXiv 2103.12312](https://arxiv.org/pdf/2103.12312)).
  - PharmaCoNER with BioBERT: softmax about 91.15 vs CRF about 90.00
    ([BMC Bioinformatics table](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-021-04260-y/tables/7)).
  - Chinese word segmentation: about equal, and the authors recommend softmax for simplicity
    ([arXiv 1909.09292](https://arxiv.org/pdf/1909.09292)).
  - Portuguese NER: the CRF improved or matched results ([arXiv 1909.10649](https://arxiv.org/pdf/1909.10649)).
  - Judicial NER: +0.36 F1 with a CRF ([arXiv 2404.09416](https://arxiv.org/pdf/2404.09416)).
- Hugging Face fast tokenizers return `(char_start, char_end)` per token through
  `return_offsets_mapping`. Slow tokenizers raise `NotImplementedError` instead. `stride` with
  `return_overflowing_tokens` produces overlapping windows. [docs]
  ([Transformers tokenizer docs](https://huggingface.co/docs/transformers/main_classes/tokenizer))
- Long-context encoders:
  - ModernBERT: native 8,192-token context, trained "primarily" on English, and its paper
    "focuses exclusively on the English language". [full text]
    ([Warner et al., arXiv 2412.13663](https://arxiv.org/html/2412.13663))
  - mmBERT: 140M and 307M parameters, 8,192-token context, more than 3T training tokens across
    1,833 languages. XLM-R and MiniLM cannot go past 512 tokens. [search summary]
    ([arXiv 2509.06888](https://arxiv.org/pdf/2509.06888); [GitHub](https://github.com/JHU-CLSP/mmBERT/))
  - AraModernBERT adapts ModernBERT to Arabic, initializing its embeddings by transtokenization.
    It has native context up to 8,192 tokens and is evaluated on Arabic NER among other tasks.
    The abstract gives no size, no NER scores and no word on classical Arabic. [abstract only]
    ([Elshehy et al., AbjadNLP at EACL 2026, arXiv 2603.09982](https://arxiv.org/abs/2603.09982))
- CAMeLBERT-CA was pre-trained on OpenITI 2020.1.2 (6GB, 847M words) with a 512-token maximum.
  Its card reports no classical-text NER. Its NER score of 67.9 on ANERcorp is for modern news.
  [model card] ([CAMeL-Lab/bert-base-arabic-camelbert-ca](https://huggingface.co/CAMeL-Lab/bert-base-arabic-camelbert-ca))
- Hadith-specific prior work:
  - `SHK4K/hadith-segmentation-bert`:
    - Fine-tuned from AraBERTv02, with labels `B-SANAD`/`I-SANAD` (chain) and `B-MATN`/`I-MATN`.
    - Its usage code truncates at 512 tokens.
    - The card gives no metrics and no training-data size, and advises removing extra
      diacritics.
    
    [model card] ([Hugging Face](https://huggingface.co/SHK4K/hadith-segmentation-bert))
  - A bigram-based chain/matn splitter reached 92.5% accuracy on six collections. [search summary]
    ([Altammami et al., 2019](https://aclweb.org/anthology/W19-5605.pdf))
  - PPM compression reached 92.76% trained and tested on one corpus (NAH), and 90.10% trained on
    NAH and tested on another (LK). [search summary]
    ([Tarmom et al., ICON 2020](https://eprints.whiterose.ac.uk/172041/7/2020.icon-main.4.pdf))
  - SALAH finds chains of narrators with regular expressions, builds a narrator graph and outputs
    XML. [search summary] ([Roma Tre](https://iris.uniroma3.it/handle/11590/279085))

### Inferences
- Label design: the six span types are contiguous and together cover the whole entry. A
  begin-of-segment flag plus a type per word is therefore enough, with no "outside" label needed.
  Collectors vary the order (the evaluation lists a matn given before its chain), so learn
  allowed transitions from gold rather than hard-coding one order.
- Segment-level classification is an alternative: rules propose cut points at transmission words
  and formulas, then an encoder labels each piece. Offsets are exact by construction, but the
  model cannot place a boundary the rules did not propose. The project's evaluation finds
  open-ended phrasing at matn boundaries, which suggests the rules would miss some of the cut
  points needed.
- A few thousand characters of Arabic is probably 500 to 1,500 subword tokens (an assumption I did
  not measure). That exceeds 512 for AraBERT and CAMeLBERT. The options are an 8k-context encoder,
  or windows with a stride of about 128 tokens where each token keeps the prediction from the
  window in which it sits most centrally.
- With an encoder tagger, character offsets come free from the offset mapping. That removes the
  verbatim problem entirely.

### Gaps
- I found no classical Arabic token-classification results for mmBERT or AraModernBERT, and no
  size or training-data details for AraModernBERT.
- Typical token counts of hadith entries under Arabic and multilingual tokenizers are not measured
  anywhere I found.
- I found no work on segmenting hadith into more than the two parts (chain and matn).

## 4. Hybrid designs: rules plus a learned tagger, boundaries only, confidence and routing

### Takeaway
Rules should cover the formulaic language: transmission verbs, links to the Prophet, and
collector formulas such as مثله, نحوه and واللفظ له. A learned tagger should cover the decisions
that need context, mainly where a matn ends and a collector's comment or narrator's remark begins.
Disagreement between rules and model is a strong, free confidence signal. In the project's own
data, chains where the two agreed were right 93% of the time, against 61 to 63% overall. Research
on cascades finds per-token uncertainty a better reason to defer than whole-sequence probability,
which is biased by output length.

### Cited Findings
- The project's rules (`docs/chain-wording.md`) set where a matn starts, after skipping blessings
  and epithets, notes on the narrator, and the link to the Prophet. They map closed lists of
  collector formulas (مثله, بمثله, نحوه, بنحوه, بمعناه, واللفظ له, بهذا الإسناد) to bases (`same`,
  `similar`, `meaning`, `lafz`, `reference`) ([docs/chain-wording.md](/Users/ahmediqbal/Documents/icma/docs/chain-wording.md)).
- The project's evaluation:
  - The rules get the basis right for 150 of 172 unseen chains. Most errors are where a matn
    starts or ends, because of open-ended phrasing: يرفعه إلى النبي ﷺ قال, كذا قال, متن غريب,
    قال شيخنا. One round of fixes raised accuracy on unseen entries from 41% to 61%.
  - Rules and DeepSeek agreed on 42 of 79 chains and were right on 39 of them (93%). Of the other
    37, only the rules were right on 10, only the model on 11, and neither on 19.
  - Two blind labellers agree on 92% of chains.
  - DeepSeek V4 Pro cost $0.014 and one to four minutes per entry.
  
  ([eval/chain-wording-2026-10-18.md](/Users/ahmediqbal/Documents/icma/eval/chain-wording-2026-10-18.md))
- Grammar-constrained decoding turns rule knowledge into hard output constraints. The resulting
  outputs are valid "but not necessarily correct". [full text]
  ([Geng et al., arXiv 2305.13971](https://arxiv.org/html/2305.13971v6))
- LangExtract's grounding check, `char_interval = None` for text it cannot find, works as a cheap
  validator that rejects ungrounded output. [README] ([google/langextract](https://github.com/google/langextract))
- Language-model cascades: deferring on predicted sequence uncertainty suffers from length bias.
  Deferral rules learned from token-level uncertainty "can significantly outperform" simple
  aggregation (tested with FLAN-T5). [abstract only]
  ([Gupta et al., arXiv 2404.10136](https://arxiv.org/abs/2404.10136))
- When several small models' outputs agree in meaning, that consensus is a better reliability
  signal than token-level confidence. The method needs no training and was tested from 500M to
  70B parameters. [search summary]
  ([Semantic agreement cascades, arXiv 2509.21837](https://arxiv.org/html/2509.21837v3))
- Conformal cascades accept the answer when a calibrated prediction set shrinks to one option and
  defer otherwise, with a finite-sample accuracy guarantee. The authors note that thresholds need
  tuning per model pair and domain. Preprint. [search summary]
  ([alphaXiv 2607.25018](https://www.alphaxiv.org/abs/2607.25018.md))
- CRF heads lower the variance across training runs, which helps a routing threshold stay stable
  between retrains. [search summary] ([arXiv 2103.12312](https://arxiv.org/pdf/2103.12312))

### Inferences
- A design that fits the evidence:
  1. **Normalize.** Remove diacritics and unify letter variants, keeping a map back to the
     original character positions.
  2. **Run the rules.** They propose candidate boundaries and type the closed-list spans
     (formulas, links to the Prophet).
  3. **Run the encoder tagger** over the whole entry. Give it the rule output as inline marker
     tokens, or train it on rule-made silver labels plus a corrected gold sample.
  4. **Validate the structure.** Spans tile the entry exactly, every chain span contains
     transmission words, and an `own` chain has a non-empty matn.
  5. **Route** entries where the rules and the tagger disagree, or where the token-level margin
     at any boundary is low. Send them first to a constrained generative fallback (copy-with-tags)
     or a stronger model, then to human review in the existing review UI.
- The 93% accuracy where rules and DeepSeek agreed suggests agreement-based routing will work. But
  with a prompted model, 47% of chains disagreed, which is too many to route. A trained tagger
  should disagree with the rules less often. Measure this on round 2 before choosing thresholds.
- Routing cost at the measured DeepSeek price: routing 5% of 400,000 entries (20,000) costs about
  $280, against about $5,600 for sending everything.
- Rule-made silver labels teach the tagger the rules' blind spots. A stratified, hand-corrected
  sample of matn-boundary cases (or one labelled blind by Opus, as the project already does for
  gold) should go into training as well.

### Gaps
- I found no published hybrid rules-plus-tagger study for typing hadith spans.
- I found no quantitative study of routing rates or calibration for span-extraction cascades. The
  cascade papers cover generation and multiple-choice tasks.
- I found no direct evidence on weak-supervision frameworks (labelling functions) for Arabic
  segmentation. I did not search this deeply.

## 5. Inference cost and speed for about 400,000 entries on one GPU or CPU

### Takeaway
An encoder tagger processes the whole corpus in roughly 15 to 70 minutes on one RTX 4090-class
GPU. A small decoder that rewrites each entry with tags needs roughly 7 to 28 hours, because
decoding produces one token at a time. A pointer or index output brings decoding down to about 0.5
to 2 hours plus prompt processing. For decoders, output length matters more than model size. I
found no measured CPU figures.

### Cited Findings
- Encoder throughput in thousands of tokens per second on one RTX 4090. The four columns are
  512-token fixed length, 512 variable length, 8,192 fixed and 8,192 variable. A dash means the
  model cannot take that length.
  - BERT-base: 180.4 / 90.2 / - / -
  - RoBERTa-base: 179.9 / 89.9 / - / -
  - DeBERTaV3-base: 70.2 / 35.1 / - / -
  - ModernBERT-base: 148.1 / 147.3 / 123.7 / 133.8
  - ModernBERT-large: 52.3 / 52.9 / 46.8 / 49.8
  
  Unpadding keeps ModernBERT's variable-length throughput close to its fixed-length figure, while
  BERT halves. [full text] ([Warner et al., arXiv 2412.13663](https://arxiv.org/html/2412.13663))
- SaT (3 layers) segments 1,000 sentences in about 0.5 seconds on one RTX 2080 Ti. [full text]
  ([arXiv 2406.16678](https://arxiv.org/html/2406.16678v2))
- Generative NER throughput in instances per second: GNER-T5-large 11.5, GNER-LLaMA-7B 4.0,
  InstructUIE 3.4, UniNER-7B 1.6. I did not capture the hardware. [full text]
  ([arXiv 2402.16602](https://arxiv.org/html/2402.16602v2))
- Small-decoder throughput with vLLM. These figures are only indicative, and they cannot be
  compared directly because the models, GPUs, concurrency and lengths differ:
  - Qwen2.5-0.5B on an L40S: about 2,273 generated tokens/s (llama.cpp: 1,312). Batch size
    unclear. ([NYU HPC docs](https://services.rt.nyu.edu/docs/hpc/ml_ai_hpc/LLM%20inference/vLLM/))
  - Gemma3-4B on an A100 40GB: about 3,386 output tokens/s.
    ([DatabaseMart](https://www.databasemart.com/blog/vllm-gpu-benchmark-a100-40gb))
  - Llama 3.1 8B on an H200, 128 input and 128 output tokens: about 8,955 tokens/s.
    ([E2E Networks](https://docs.e2enetworks.com/docs/tir/benchmarks/inference_benchmarks/))
  - Qwen2-0.5B and Qwen2-1.5B at batch size 1: about 270 and 176 tokens/s.
    ([Qwen docs](https://qwen.readthedocs.io/en/v2.0/benchmark/speed_benchmark.html))
  
  [search summary]
- Encoder token classification labels every token in one parallel pass, while decoder extraction
  depends on slower step-by-step generation. [search summary] ([JMIR 2026](https://www.jmir.org/2026/1/e78681))
- Constraint overhead has fallen sharply: 11 to 44 ms per token in Geng et al.'s 2023 CPU
  implementation ([arXiv 2305.13971](https://arxiv.org/html/2305.13971v6)), against near-zero
  overhead claimed by XGrammar ([arXiv 2411.15100](https://arxiv.org/abs/2411.15100)).
- Prompted DeepSeek V4 Pro through an API cost $0.014 and one to four minutes per entry. The
  project estimates about $1,350 for its 96,163 multi-chain entries
  ([eval/chain-wording-2026-10-18.md](/Users/ahmediqbal/Documents/icma/eval/chain-wording-2026-10-18.md)).

### Inferences
- These estimates rest on unverified assumptions: a mean entry of 1,500 characters, about 4
  characters per token for an Arabic-specific tokenizer (375 tokens per entry, 150M tokens in
  total), and 1.5 times as many tokens for a multilingual decoder tokenizer (about 560 per entry).
  - **Encoder:**
    - At ModernBERT-base's variable-length speed (147.3K tokens/s), 150M tokens take about 17
      minutes.
    - At ModernBERT-large speed (52.9K) they take about 47 minutes, and at DeBERTaV3-base speed
      (35.1K) about 71 minutes.
    - mmBERT-base shares ModernBERT's design but has a larger vocabulary, which adds little
      compute to token classification. I did not verify its speed.
  - **Decoder rewriting the entry with tags:** about 575 output tokens per entry, or 230M in
    total. At 2,273 to 8,955 tokens/s that is about 7 to 28 hours of decoding, plus prompt
    processing of a similar number of input tokens.
  - **Decoder emitting word indices:** about 40 output tokens per entry, or 16M in total, which is
    about 0.5 to 2 hours of decoding plus prompt processing.
  - **Anchor from GNER:** at 4.0 entries/s (GNER-LLaMA-7B), 400,000 entries take about 28 hours.
    At 11.5 entries/s (GNER-T5-large) they take about 10 hours. Those instances are NER sentences,
    which are shorter than most hadith entries.
- **CPU, a rough calculation:** a base encoder needs about 2 × 86M non-embedding parameters × 150M
  tokens ≈ 2.6 × 10^16 floating-point operations. If a CPU sustains 0.5 to 1 trillion operations
  per second on these matrix products (an assumption, not a measurement), that is about 7 to 14
  hours. A 1.5B decoder rewriting every entry needs about 50 times more compute, and decoding on a
  CPU is limited by memory bandwidth, so it is impractical without a GPU.
- **Cost of routing the hard cases:** at the measured DeepSeek price, routing 5% of entries costs
  about $280. Processing the whole corpus through an API would cost about $5,600 and needs heavy
  parallelism at one to four minutes per entry.

### Gaps
- I found no measured CPU or Apple Silicon (MPS) throughput for encoder token classification or
  small decoders.
- I found no batched vLLM throughput for 0.5B to 3B models on one consumer GPU with
  input-sized outputs.
- I found no throughput figures for constrained copy-with-tags decoding, or for per-request
  grammar compilation.
