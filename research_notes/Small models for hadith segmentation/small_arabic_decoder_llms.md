# Small open-weight decoder LLMs with strong Arabic, as base models for a classical Arabic hadith segmenter (state as of 19 October 2026)

Scope: decoder models of about 0.3B to 4B parameters, with notes up to about 9B, that could be fine-tuned (LoRA or full) to mark typed spans in one hadith entry: the chain of narrators (isnad), the link to the Prophet, the matn, the collector's formulas (مثله، نحوه، بمعناه، بهذا الإسناد), the collector's own comments, and narrators' remarks. Research and non-commercial use, with a possible public release of the derived model.

Method: six parallel web research passes (Chinese, Gulf and Arabic-centric, American and European families; benchmarks; tokenization; fine-tuning and tooling), all on 2026-10-19, plus three local checks. (1) Token counts on 20,000 entries of the project's own hadith-kg database, using the Qwen3 and Qwen3.5 tokenizer files already in the local Hugging Face cache. (2) Pre-tokenizer rules read from published tokenizer files. (3) A results table decoded from the QIMMA leaderboard paper PDF. Country of origin is given for every family; American models are marked "American". Where a figure comes from the developer rather than an independent evaluator, the bullet says so.

## 1. Which small model families have strong Arabic as of October 2026, and what are their sizes, dates, licences, origins, context lengths and tokenizers?

### Takeaway
Under 4B, the non-American families with open weights, permissive licences and measured Arabic ability are Qwen3.5 (0.8B, 2B, 4B, March 2026) and Qwen3 (0.6B, 1.7B, 4B, April 2025), both Apache 2.0 from Alibaba (China). Falcon-H1 (UAE) is the main Arabic-world alternative at 1.5B to 3B, but its Arabic-tuned version (Falcon-H1-Arabic) has no public weights. At 7B to 9B, Jais-2-8B (UAE), ALLaM-7B (Saudi Arabia) and Fanar-1-9B (Qatar) are the strongest Arabic-centric options, each with a short context (8K, 4K and 4K). The American options with Arabic listed (Gemma 4, Phi-4-mini, Granite, LFM2/2.5) are usable but carry no Arabic advantage at small sizes, except that Gemma 4 E2B and E4B are now Apache 2.0.

### Cited Findings

#### Master table of candidates (details and conflicts in the bullets below)

| Family and sizes | Developer, country | Release | Licence | Context | Tokenizer, vocab | Arabic claim |
|---|---|---|---|---|---|---|
| Qwen3.5 0.8B, 2B, 4B, 9B (each with -Base) | Alibaba Qwen, China | 2026-03-02 | Apache 2.0 | 262,144 native, up to 1,010,000 with YaRN | byte-level BPE, 248,044 BPE tokens, config vocab 248,320 (padded) | "201 languages and dialects"; Arabic not named on pages read |
| Qwen3 0.6B, 1.7B, 4B, 8B (dense) | Alibaba Qwen, China | 2025-04-29 | Apache 2.0 | 32K native (0.6B, 1.7B); 4B 32K or 128K (sources conflict); 8B 32,768 native, 131,072 with YaRN | byte-level BPE, 151,669 tokens, config vocab 151,936 | 119 languages; Arabic (Standard and 7 dialects) named |
| Qwen3-4B-Instruct-2507 | Alibaba Qwen, China | 2025 (date not on card) | Apache 2.0 | 262,144 | as Qwen3 | as Qwen3 |
| Falcon-H1 0.5B, 1.5B, 1.5B-Deep, 3B, 7B, 34B | TII, UAE | 2025-05 | TII Falcon License (Apache-2.0-based, plus AUP and attribution) | 16K (0.5B), 128K (1.5B to 3B), 256K (7B, 34B) | BPE; 32,768 or 32,778 (0.5B), 65,536 (1.5B to 3B), 130,048 or 131,048 (7B) | 18 languages incl. Arabic in one section, 17 without Arabic in another |
| Falcon-H1-Arabic 3B, 7B, 34B | TII, UAE | 2026-01-05 | not stated | 128K (3B), 256K (7B, 34B) | not described | Arabic-specialised; no public weights found |
| Jais family 590M, 1.3B, 2.7B, 6.7B (also 13B, 30B; adapted 7B to 70B) | Inception (G42), MBZUAI, Cerebras, UAE | 2024 | Apache 2.0 | 2,048 (small sizes) | 84,992 | Arabic-English bilingual |
| Jais 2 8B (and 70B) | Inception, Cerebras, MBZUAI, UAE | 2025-12-09 | Apache 2.0, gated (contact details) | 8,192 | 150,272 (card) or 150,222 (EACL26 paper) | Arabic-centric, trained from scratch |
| ALLaM-7B-Instruct-preview | SDAIA NCAI, hosted by HUMAIN, Saudi Arabia | 2025-02 | Apache 2.0 | 4,096 | Llama-2 SentencePiece extended, 64,000 | Arabic-English, trained from scratch |
| Fanar-1-9B, Fanar-1-9B-Instruct | QCRI at HBKU, Qatar | 2025-01 | card says Apache 2.0; base is Gemma-2-9B | 4,096 | Gemma-2 vocab pruned to 128,256 | Arabic-English |
| SILMA-Kashif-2B, SILMA-9B | SILMA.AI (country not verified) | 2025-01, 2024-08 | Gemma terms | n/a | Gemma-based (version not verified) | Arabic |
| Hala 350M, 700M, 1.2B, 9B | KAUST team, Saudi Arabia | 2025-09 | 9B is CC-BY-NC-4.0; small sizes reportedly on LFM2 bases | n/a | as base | Arabic instruction and translation tuned |
| Tiny Aya 3.35B | Cohere Labs, Canada | 2026-02 | CC-BY-NC 4.0 plus AUP, gated | 8K in, 8K out | n/a | 70 languages incl. Arabic |
| Ministral 3 3B, 8B, 14B | Mistral AI, France | 2025-12 (repo suffix 2512) | Apache 2.0 | 256K | via mistral-common; size not stated | Arabic listed |
| EuroLLM-1.7B | EU consortium led from Portugal | 2024 | Apache 2.0 | 4,096 | n/a | 35 languages incl. Arabic |
| Gemma 4 E2B, E4B (American) | Google, USA | 2026-04-02 | Apache 2.0 | 128K | 262K | 140+ languages; Arabic not named |
| Gemma 3 270M, 1B, 4B (American) | Google, USA | 2025-03 (270M 2025-08-14) | Gemma Terms of Use | 32K (270M, 1B), 128K (4B) | SentencePiece, 262K (256K in some places) | 140+ languages; Arabic not named |
| Phi-4-mini-instruct 3.8B (American) | Microsoft, USA | 2025-02 | MIT | 128K | 200,064 | Arabic listed |
| LFM2 350M to 2.6B, LFM2.5 1.2B and later (American) | Liquid AI, USA | 2025 to 2026 | LFM Open License v1.0 (USD 10M revenue threshold) | 32,768 | byte-level BPE, 65,536 | Arabic listed |
| Granite 4.0 Nano 350M, 1B; Granite 4.1 3B, 8B (American) | IBM, USA | 2025-10-28; 2026-04-29 | Apache 2.0 | 32K or 128K (Nano); 131,072 (4.1) | n/a | Arabic among 12 languages |
| Llama 3.2 1B, 3B (American) | Meta, USA | 2024-09-25 | Llama 3.2 Community License | 128K | 128,256 | Arabic not officially supported |
| SmolLM3-3B (American) | Hugging Face, New York and Paris | 2025-07 | Apache 2.0 | 64K, 128K with YaRN | Llama-3-style (not verified) | 6 official languages; small amount of Arabic in pretraining |

Sources for each row are in the bullets that follow.

#### Qwen (Alibaba, China)
- Qwen3 dense 0.6B, 1.7B, 4B and 8B were released on 2025-04-29 under Apache 2.0, with 119 languages and dialects. Arabic is listed explicitly as Standard plus Najdi, Levantine, Egyptian, Moroccan, Mesopotamian, Ta'izzi-Adeni and Tunisian. ([Qwen3 blog](https://qwenlm.github.io/blog/qwen3/))
- The Qwen3 tokenizer is byte-level BPE with 151,669 tokens ([Qwen3 technical report](https://arxiv.org/abs/2505.09388)). The config pads `vocab_size` to 151,936 ([Qwen3-1.7B config.json](https://huggingface.co/Qwen/Qwen3-1.7B/blob/main/config.json)). The cached tokenizer file has 151,643 BPE entries plus 26 added tokens ([Qwen3-8B-MLX-4bit tokenizer, read locally](https://huggingface.co/Qwen/Qwen3-8B-MLX-4bit)).
- Context, sources conflict. The blog gives 32K for 0.6B, 1.7B and 4B and 128K for 8B ([Qwen3 blog](https://qwenlm.github.io/blog/qwen3/)). The technical report gives 128K for 4B and 8B ([Qwen3 technical report](https://arxiv.org/html/2505.09388v1)). The 8B card says 32,768 native and 131,072 with YaRN, with `max_position_embeddings` set to 40,960 ([Qwen3-8B card, cached copy of the official card](https://huggingface.co/Qwen/Qwen3-8B-MLX-4bit)).
- Qwen3-4B-Instruct-2507 has 4.0B parameters (3.6B non-embedding), 36 layers, 262,144 native context and non-thinking mode only, under Apache 2.0 ([model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)).
- The Qwen3.5 small models (0.8B, 2B, 4B, 9B, each with a -Base checkpoint) "became available" on 2026-03-02 ([Qwen3.5 GitHub](https://github.com/QwenLM/Qwen3.5); [Artificial Analysis, 2026-03-05](https://artificialanalysis.ai/articles/qwen3-5-small-models)). Licence: Apache 2.0 ([Qwen3.5-9B card](https://huggingface.co/Qwen/Qwen3.5-9B)).
- Qwen3.5 small models are vision-language checkpoints, described as a "Causal Language Model with Vision Encoder", class `Qwen3_5ForConditionalGeneration` ([Qwen3.5-9B card](https://huggingface.co/Qwen/Qwen3.5-9B); [Qwen3.5-4B config](https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/config.json)).
- The text stack repeats a block of three Gated DeltaNet linear-attention layers and one gated full-attention layer. In the cached configs:
  - 0.8B: 24 layers (18 linear, 6 full), hidden size 1,024, tied embeddings.
  - 4B: 32 layers (24 linear, 8 full), hidden size 2,560, tied embeddings.
  - 9B: 32 layers (24 linear, 8 full), hidden size 4,096, untied embeddings.
  - All three: `max_position_embeddings` 262,144 and `vocab_size` 248,320.

  ([configs read locally from the Hugging Face cache](https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/config.json))
- Qwen3.5 context is 262,144 tokens native, extensible to 1,010,000. The vocabulary is 248,320 (padded), with "expanded support to 201 languages and dialects" ([Qwen3.5-9B card](https://huggingface.co/Qwen/Qwen3.5-9B)). No page read names Arabic among the 201 ([Qwen3.5 GitHub](https://github.com/QwenLM/Qwen3.5)).
- Sources conflict on mixture-of-experts. The family README highlights "Gated Delta Networks combined with sparse Mixture-of-Experts", but the small-model card layout and configs show a dense FFN ([Qwen3.5 GitHub](https://github.com/QwenLM/Qwen3.5); [Qwen3.5-4B card](https://huggingface.co/Qwen/Qwen3.5-4B)). The 4B card says 4B, while the Hugging Face safetensors widget shows about 5B parameters including the vision encoder ([Qwen3.5-4B card](https://huggingface.co/Qwen/Qwen3.5-4B)).
- No newer small Qwen exists as of 2026-10-19:
  - Qwen3.6 open weights are 35B-A3B and a dense 27B (April 2026).
  - Qwen3.7 is proprietary.
  - Qwen3.8 releases are 27B and larger; some later licences are not Apache.
  - 2026 sub-10B Qwen repositories are task-specific (ASR, TTS, embedding).

  ([Hugging Face API listing for Qwen](https://huggingface.co/api/models?author=Qwen); [Marktechpost on Qwen3.6-27B, 2026-04-22](https://www.marktechpost.com/2026/04/22/alibaba-qwen-team-releases-qwen3-6-27b-a-dense-open-weight-model-outperforming-397b-moe-on-agentic-coding-benchmarks/); [Wikipedia: Qwen](https://en.wikipedia.org/wiki/Qwen))

#### Other Chinese families (mostly weak or no Arabic claim)
- DeepSeek-R1-Distill-Qwen-1.5B and 7B (January 2025) and DeepSeek-R1-0528-Qwen3-8B (May 2025) are MIT-licensed; the 8B is a Qwen3-8B-Base post-trained on R1-0528 chains of thought ([R1-0528-Qwen3-8B card](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B)). There was no new small general DeepSeek model in 2026 ([HF API listing](https://huggingface.co/api/models?author=deepseek-ai)). In a June 2026 Arabic evaluation the R1-Distill Qwen 8B was "among the lowest", and Qwen- and DeepSeek-based models drifted into Chinese or Japanese reasoning ([arXiv 2606.21460](https://arxiv.org/html/2606.21460v1)).
- MiniCPM5-2B (OpenBMB / ModelBest; September 2026): 2.52B parameters, Llama architecture, 131,072 context, Apache 2.0, English and Chinese only ([model card](https://huggingface.co/openbmb/MiniCPM5-2B)). InternLM3-8B-Instruct is Apache 2.0, English and Chinese only ([model card](https://huggingface.co/internlm/internlm3-8b-instruct)). ERNIE-4.5-0.3B (Baidu, June 2025): 0.36B, 131,072 context, Apache 2.0, English and Chinese only ([model card](https://huggingface.co/baidu/ERNIE-4.5-0.3B-PT)). GLM-4-9B-0414 is MIT with Chinese and English tags ([model card](https://huggingface.co/zai-org/GLM-4-9B-0414)).
- Tencent Hunyuan 0.5B, 1.8B, 4B and 7B (July and August 2025): Hunyuan-4B has `vocab_size` 120,818 and 262,144 positions ([config](https://huggingface.co/tencent/Hunyuan-4B-Instruct/blob/main/config.json)). Its licence grants nothing in the EU, UK or South Korea, requires a separate licence above 100M monthly users, requires a NOTICE file, and forbids using the model or its outputs "to improve any other AI model" ([licence](https://huggingface.co/tencent/Hunyuan-4B-Instruct/blob/main/LICENSE)).
- ByteDance Seed-X-Instruct-7B is a translation model covering 28 languages including Arabic, under the OpenMDW licence ([model card](https://huggingface.co/ByteDance-Seed/Seed-X-Instruct-7B)). Tencent Hy-MT2-7B (May 2026) translates among about 33 languages including Arabic and is tagged Apache 2.0 ([model card](https://huggingface.co/tencent/Hy-MT2-7B)).

#### TII Falcon (UAE)
- Falcon-H1 has 0.5B (0.52B), 1.5B, 1.5B-Deep, 3B (3.15B), 7B (7.59B) and 34B sizes. Repositories were created 2025-05-01, with GGUF builds from 2025-05-13 ([HF API listing for tiiuae](https://huggingface.co/api/models?author=tiiuae&sort=createdAt&direction=-1&limit=80)).
- Each Falcon-H1 block runs attention heads and SSM heads in parallel. Per size ([Falcon-H1 technical report, 2025-07-30](https://arxiv.org/html/2507.22448v1)):
  - Vocab: 32,778 (0.5B), 65,536 (1.5B, 1.5B-Deep, 3B), 130,048 (7B) and 261,120 (34B) in Table 1. Table 5 gives 32,768 and 131,048 for the first and fourth.
  - Context: 16K (0.5B), 128K (1.5B to 3B), 256K (7B, 34B).
- The same report says the 0.5B was trained on English only. Its introduction lists 18 languages including Arabic, but Section 3.1.1 lists 17 and omits Arabic ([Falcon-H1 technical report](https://arxiv.org/html/2507.22448v1)). The transformers docs give the 0.5B a 4K context (16K after SFT) ([transformers Falcon-H1 docs](https://huggingface.co/docs/transformers/model_doc/falcon_h1)).
- Licence: TII's terms page holds several Apache-2.0-based Falcon licences. The extracted text did not say which one covers Falcon-H1 ([TII terms](https://falconllm.tii.ae/falcon-terms-and-conditions.html)). For derivatives the TII Falcon License requires:
  - a public statement that the derivative is built using TII technology;
  - passing on an acceptable use policy that TII can update;
  - a licence copy and NOTICE content.

  It sets no royalty, no non-commercial limit and no naming rule ([TII terms](https://falconllm.tii.ae/falcon-terms-and-conditions.html)).
- Falcon-H1-Arabic (3B, 7B, 34B; 2026-01-05) is built on the Falcon-H1 architecture with about 300B tokens split roughly evenly between Arabic, English and other languages. It covers MSA and four dialect groups and does not mention classical text ([TII blog on Hugging Face](https://huggingface.co/blog/tiiuae/falcon-h1-arabic)).
- No public Falcon-H1-Arabic repository exists. A Hugging Face API search for "Falcon-H1-Arabic" returned an empty list on 2026-10-19 ([HF API search](https://huggingface.co/api/models?search=Falcon-H1-Arabic&limit=50)), and the expected card URL returned HTTP 401 ([card URL](https://huggingface.co/tiiuae/Falcon-H1-Arabic-3B-Instruct)). Aggregators claim open weights but give the non-Arabic repo ID for the 7B, so they are unreliable ([lmmarketcap](https://lmmarketcap.com/model/falcon-h1-arabic-3b-instruct)).
- Falcon Arabic 7B (May 2025, Falcon3-7B plus 32,000 Arabic tokens) is closed: the blog's author says it is served only through Falcon's chat ([TII blog](https://huggingface.co/blog/tiiuae/falcon-arabic)).
- Other small TII releases are licence "other" ([HF API listing](https://huggingface.co/api/models?author=tiiuae&sort=createdAt&direction=-1&limit=80)):
  - Falcon-H1-Tiny (January 2026): 90M, Multilingual-100M, R-0.6B and others.
  - Falcon-E (BitNet): 1B and 3B.
  - Falcon-H1R-7B.

  No Falcon-H2 was found.

#### Jais (UAE)
- The Jais family has 590M, 1.3B, 2.7B, 6.7B and 13B sizes at 2,048 context, plus 30B at 8K or 16K. All are Apache 2.0 and have chat versions ([jais-family-590m card](https://huggingface.co/inceptionai/jais-family-590m)). The 590M config has `vocab_size` 84,992, `n_positions` 2,048 and the custom class `JAISLMHeadModel` ([config](https://huggingface.co/inceptionai/jais-family-590m/blob/main/config.json)).
- ArabicMMLU scores on the card are 31.2, 28.9, 29.5 and 32.2 for the 590M, 1.3B, 2.7B and 6.7B base models, and 39.1, 42.2, 50.0 and 55.7 for the chat models ([jais-family-590m card](https://huggingface.co/inceptionai/jais-family-590m)).
- Jais 2 was announced on 2025-12-09 as open weights in 8B and 70B ([MBZUAI news](https://mbzuai.ac.ae/news/inception-cerebras-and-mbzuai-release-jais-2-the-next-generation-of-the-worlds-leading-arabic-open-weight-llm/)). Jais-2-8B-Chat ([model card](https://huggingface.co/inceptionai/Jais-2-8B-Chat)):
  - trained from scratch on Arabic and English;
  - RoPE, squared-ReLU and muP;
  - 150,272-token Arabic-centric vocabulary;
  - 8,192 context;
  - Apache 2.0, gated behind sharing contact details.

  No Jais 2 model below 8B was found. A paper exists as arXiv 2608.13580 ([abstract](https://arxiv.org/abs/2608.13580)).

#### ALLaM (Saudi Arabia)
- ALLaM-7B-Instruct-preview was developed by the National Center for AI at SDAIA and is listed under HUMAIN. It is Apache 2.0, trained from scratch on 4T English tokens then 1.2T mixed Arabic and English tokens, with 4,096 context and two revisions, v1 and v2 ([model card](https://huggingface.co/ALLaM-AI/ALLaM-7B-Instruct-preview)).
- Its config is `LlamaForCausalLM` with `vocab_size` 64,000, 32 layers and hidden size 4,096 ([config](https://huggingface.co/ALLaM-AI/ALLaM-7B-Instruct-preview/blob/main/config.json)). The humain-ai copy was created on 2025-02-13 ([HF API listing](https://huggingface.co/api/models?author=humain-ai&sort=createdAt&direction=-1&limit=40)).
- ALLaM extends the Llama-2 tokenizer with every token from an Arabic-trained tokenizer that Llama-2 lacks, initialising the new embeddings from averaged subtoken embeddings ([ALLaM paper](https://arxiv.org/html/2407.15390)).
- ALLaM 34B powers HUMAIN Chat. Its weights are not public ([Middle East AI News](https://www.middleeastainews.com/p/humain-chat-live-allam-34b-llm); [lmmarketcap, secondary](https://lmmarketcap.com/model/allam-34b)).
- Yehia-7B-preview (Navid-AI) is a GRPO fine-tune of ALLaM-7B, tagged Apache 2.0 plus a gated agreement ([model card](https://huggingface.co/Navid-AI/Yehia-7B-preview)).

#### Fanar (Qatar)
- Fanar-1-9B-Instruct (QCRI at HBKU) is continued pretraining of Gemma-2-9B on about 1T tokens (410B Arabic), with 8.7B parameters and 4,096 context. The card states Apache 2.0 and does not mention Gemma terms ([model card](https://huggingface.co/QCRI/Fanar-1-9B-Instruct)).
- Fanar Prime prunes the Gemma-2 vocabulary to 128,256. Fanar Star (7B, trained from scratch) uses a 76,800-token MorphBPE tokenizer ([Fanar paper](https://arxiv.org/pdf/2501.13944)).
- Fanar 2.0 (27B, announced 2025-12-09) has no small version ([HBKU news](https://www.hbku.edu.qa/en/news/hbku-releases-enhanced-flagship-generative-ai-platform); [Fanar-2-27B README](https://huggingface.co/QCRI/Fanar-2-27B-Instruct/blob/main/README.md)).

#### Other Arabic-centric and non-American small models
- SILMA.AI's text LLMs are SILMA-9B-Instruct-v1.0 (August 2024) and SILMA-Kashif-2B-Instruct-v1.0 (January 2025, a RAG model), both licence "gemma"; nothing newer was found ([HF API listing](https://huggingface.co/api/models?author=silma-ai&sort=createdAt&direction=-1&limit=50)).
- AceGPT (FreedomIntelligence) has v1 7B and 13B (2023), v1.5 and v2 8B, 32B and 70B (June 2024), tagged Apache 2.0. It is outdated next to 2025 models ([HF API listing](https://huggingface.co/api/models?author=FreedomIntelligence&search=AceGPT&limit=50)).
- Hala (arXiv 2509.14008, September 2025) comes in 350M, 700M, 1.2B and 9B. The 9B is built on Fanar-1-9B-Instruct under CC-BY-NC-4.0, and the small sizes appear to be LFM2-based ([paper](https://arxiv.org/abs/2509.14008); [Hala-9B card](https://huggingface.co/hammh0a/Hala-9B/blob/main/README.md)).
- Kuwain 1.5B injects Arabic into a small English model, adding 26K Arabic SentencePiece tokens for a 54K vocabulary ([Kuwain paper](https://arxiv.org/html/2504.15120)). Sadeed is a diacritization fine-tune of Kuwain. Neither set of weights was found on the developer's Hugging Face organisation ([HF API listing for Misraj](https://huggingface.co/api/models?author=Misraj&sort=createdAt&direction=-1&limit=50); [Sadeed GitHub](https://github.com/misraj-ai/Sadeed)).
- MBZUAI-Paris Nile-Chat (4B, 12B; Gemma 3 bases) and Atlas-Chat (2B, 9B, 27B; Gemma 2 bases) are dialect models (Egyptian, Moroccan) under Gemma terms ([HF API listing](https://huggingface.co/api/models?author=MBZUAI-Paris&sort=createdAt&direction=-1&limit=60)).
- Command R7B Arabic (Cohere, Canada) has about 8B parameters (7B transformer plus 1B embeddings), 128K context, and a CC-BY-NC licence plus acceptable use policy ([model card](https://huggingface.co/CohereLabs/c4ai-command-r7b-arabic-02-2025)).
- Tiny Aya (Cohere Labs, Canada; February 2026): 3.35B parameters, more than 70 languages including Arabic, 8K input and 8K output, CC-BY-NC 4.0 plus acceptable use policy, gated ([model card](https://huggingface.co/CohereLabs/tiny-aya-global); [paper](https://arxiv.org/abs/2603.11510); [TechCrunch, 2026-02-17](https://techcrunch.com/2026/02/17/cohere-launches-a-family-of-open-multilingual-models/)).
- Ministral 3 (Mistral AI, France) comes in 3B, 8B and 14B, each as Base, Instruct and Reasoning, under Apache 2.0 with 256K context. Arabic is among 11 listed languages. The 3B is a 3.4B language model plus a 0.4B vision encoder, and its Instruct version ships in FP8 while Base ships in BF16 ([Ministral-3-3B card](https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512)).
- EuroLLM-1.7B is Apache 2.0, covers 35 languages including Arabic, and has a 4,096-token sequence length ([model card](https://huggingface.co/utter-project/EuroLLM-1.7B-Instruct)). Apertus (Swiss AI; 8B, 70B; Apache 2.0) does not name Arabic ([model card](https://huggingface.co/swiss-ai/Apertus-8B-Instruct-2509)).

#### American families (marked American)
- **Gemma 3 (Google, American).** 270M, 1B and 4B, with 32K context for 270M and 1B and 128K for 4B. Over 140 languages, with Arabic not named. Gemma Terms of Use ([Gemma 3 270M card](https://huggingface.co/google/gemma-3-270m)).
  - The 270M splits into 170M embedding and 100M transformer parameters. Google pitches it for narrow fine-tuned tasks such as entity extraction and unstructured-to-structured text ([Google developers blog, 2025-08-14](https://developers.googleblog.com/en/introducing-gemma-3-270m/)).
  - Gemma Terms require derivative distributors to pass on the use restrictions as enforceable terms, give recipients the terms, mark modified files and ship a NOTICE file. Google reserves the right to restrict use that violates them ([Gemma terms](https://ai.google.dev/gemma/terms)).
- **Gemma 4 (Google, American).** Launched 2026-04-02 under Apache 2.0 in E2B, E4B, 26B MoE and 31B, with 128K context for E2B and E4B ([Google blog](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/)).
  - E2B is 2.3B effective (5.1B with per-layer embeddings) and E4B is 4.5B effective (about 8B with embeddings).
  - Vocabulary is 262K. Instruct MMMLU is 67.4 (E2B) and 76.6 (E4B).
  - The card also lists a "12B Unified" model that the blog omits ([Gemma 4 E4B card](https://huggingface.co/google/gemma-4-E4B)).
- **Llama 3.2 1B and 3B (Meta, American).** Released 2024-09-25 with 128K context. Arabic is not among the eight officially supported languages ([Llama 3.2 1B card](https://huggingface.co/meta-llama/Llama-3.2-1B)). The licence requires "Built with Llama" to be displayed, and any distributed derivative's name must begin with "Llama" ([same card](https://huggingface.co/meta-llama/Llama-3.2-1B)).
- **Phi-4-mini-instruct (Microsoft, American).** 3.8B dense, 200,064 vocabulary, 128K context, MIT licence. Arabic is listed among about 23 languages, and the card warns that training was mostly English ([model card](https://huggingface.co/microsoft/Phi-4-mini-instruct)).
- **SmolLM3-3B (Hugging Face, American with a Paris presence).** Apache 2.0, trained at 64K context, extending to 128K with YaRN. Six official European languages; Arabic appears in pretraining only in small amounts ([model card](https://huggingface.co/HuggingFaceTB/SmolLM3-3B)).
- **LFM2 and LFM2.5 (Liquid AI, American).** Arabic is listed as a supported language, with 32,768 context and a 65,536 vocabulary. LFM2.5-1.2B has 16 layers: 10 gated short-convolution blocks and 6 grouped-query attention blocks ([LFM2.5-1.2B-Instruct card](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct); [LFM2-8B-A1B card](https://huggingface.co/LiquidAI/LFM2-8B-A1B)).
  - LFM2-1.2B-Extract is Liquid's extraction fine-tune (documents to JSON, XML or YAML) and lists Arabic ([model card](https://huggingface.co/LiquidAI/LFM2-1.2B-Extract)).
  - The LFM Open License v1.0 limits commercial rights to entities under USD 10M annual revenue, and derivatives remain governed by it ([LFM licence](https://www.liquid.ai/lfm-license)).
  - Later 2026 LFM2.5 releases (230M, 8B-A1B, 24B-A2B) are known only from press coverage ([Marktechpost, 2026-06-27](https://www.marktechpost.com/2026/06/27/liquid-ai-ships-lfm2-5-230m-with-llama-cpp-mlx-vllm-sglang-and-onnx-support-for-on-device-inference/); [Marktechpost, 2026-10-14](https://www.marktechpost.com/2026/10/14/liquid-ai-lfm2-5-24b-a2b/)).
- **IBM Granite (American).** Granite 4.0 Nano (2025-10-28) comes in 350M and 1B, each as a hybrid Mamba-2 and a dense version, under Apache 2.0, with Arabic among 12 languages ([granite-4.0-h-1b card](https://huggingface.co/ibm-granite/granite-4.0-h-1b)). Granite 4.1 (2026-04-29) is dense in 3B, 8B and 30B, with 131,072 context and the same language list. The 3B scores MMMLU 57.61 and INCLUDE 52.05 ([granite-4.1-8b card](https://huggingface.co/ibm-granite/granite-4.1-8b)).

### Inferences
- The only non-American families that combine open weights, Apache 2.0 terms, sizes under 4B and measured Arabic ability are Qwen3.5 and Qwen3. Falcon-H1 is the only Arab-world family at 1.5B to 3B with mature open weights. Its Arabic evidence at those sizes is thin, and the Arabic-tuned Falcon-H1-Arabic cannot be fine-tuned because it is not downloadable.
- At 7B to 9B, the three Arab-world candidates trade off as follows:
  - Jais-2-8B scores best on Arabic, but its tokenizer is the worst on vocalized text and its tooling is thin.
  - ALLaM-7B is a plain Llama architecture, so it has the best tooling and the most diacritic-friendly tokenizer, but only 4K context.
  - Fanar-1-9B is strong on Arabic grammar, but its licence is ambiguous: a Gemma derivative labelled Apache 2.0, so Gemma's pass-through terms may still bind it.
- For releasing a derived model, Apache 2.0 bases (Qwen3, Qwen3.5, Jais, Jais 2, ALLaM, Ministral 3, Gemma 4, Granite) need only the licence text, NOTICE and change marks. The other families add obligations or block use:
  - Falcon adds an attribution statement and a mutable acceptable use policy.
  - Gemma 3 derivatives (SILMA, Nile-Chat, possibly Fanar) must pass on Google's use restrictions.
  - LFM-based models (the small Hala models) carry the USD 10M revenue threshold to every downstream user.
  - CC-BY-NC models (Tiny Aya, Command R7B Arabic, Hala-9B) are fine for research but block any commercial reuse.
  - Hunyuan is unusable in the EU and UK and forbids using its outputs to improve other models.
- Jais family small models (2024) are superseded by Jais 2. Falcon Arabic is superseded by Falcon-H1-Arabic. Qwen3 small is superseded by Qwen3.5 small. Gemma 3n and Gemma 3 4B are superseded by Gemma 4 E2B and E4B. Granite 4.0 Micro is superseded by Granite 4.1 3B.

### Gaps
- Falcon-H1-Arabic: weights, licence and tokenizer are all unconfirmed. TII's press says Falcon models are open, but no public repository was found.
- No source read names Arabic among Qwen3.5's 201 languages. The qwen.ai blog did not render.
- The Qwen3 context for the 4B is inconsistent between blog and report.
- Falcon-H1 vocabulary and language lists are inconsistent within its own report, and which TII licence version covers Falcon-H1 was not pinned down.
- The Jais family release date (2024) and the Jais 2 paper contents are not verified.
- SILMA.AI's country is not verified (often described as Saudi).
- Tokenizer details for Ministral 3, Granite, EuroLLM, Tiny Aya and SmolLM3 are not verified.
- Country attributions for Google, Meta, Microsoft, IBM, Liquid AI and Hugging Face (USA), Mistral (France), Cohere (Canada) and the Chinese developers come from general knowledge, not from pages read in this session.
- LFM2.5 releases after January 2026 are known only from press summaries.

## 2. What is the evidence on Arabic ability at small sizes, including classical Arabic?

### Takeaway
The most current like-for-like evidence is TII's QIMMA leaderboard paper (April 2026, 46 models). At 4B and below, Qwen3.5-4B-Base leads (average 50.27, ArabicMMLU 64.54), ahead of Gemma-3-4B-it and Phi-4-mini (46.93 each). At 7B to 9B, Jais-2-8B (57.89), Fanar-1-9B-Instruct (56.78), ALLaM-7B (56.51) and Qwen3.5-9B (56.28) are close together. No benchmark measures classical hadith text, and rankings flip between knowledge, grammar and classical-poetry tasks, so leaderboard rank is a weak guide for a fine-tuned segmentation task.

### Cited Findings

#### QIMMA leaderboard (TII authors; arXiv 2604.03395, v1 2026-04-03), Table 6
Decoded locally from the PDF ([QIMMA paper](https://arxiv.org/abs/2604.03395)).
- QIMMA validates existing Arabic benchmarks before evaluating, giving a suite of over 52K mostly native Arabic samples ([QIMMA abstract](https://arxiv.org/abs/2604.03395)).
- Table 6 columns: AraDiCE-Culture, ArabicMMLU, ArabCulture, PalmX, 3LM STEM, AraTrust, MizanQA, MedArabiQ, ArabLegalQA, GAT, MedAraBench, HumanEval+, MBPP+ and FannOrFlop (classical poetry explanation), plus the average.
- Selected columns for models of 9B or less:

| Model (type, size) | Avg | ArabicMMLU | AraTrust | 3LM STEM | PalmX | FannOrFlop |
|---|---|---|---|---|---|---|
| inceptionai/Jais-2-8B-Chat (instruct, 8B) | 57.89 | 73.96 | 87.55 | 79.46 | 78.98 | 51.94 |
| Navid-AI/Yehia-7B-preview (instruct, 7B) | 57.61 | 66.09 | 87.36 | 71.10 | 70.91 | 59.64 |
| QCRI/Fanar-1-9B-Instruct (instruct, 9B) | 56.78 | 67.39 | 88.51 | 83.32 | 73.18 | 0.02 |
| humain-ai/ALLaM-7B-Instruct-preview (instruct, 7B) | 56.51 | 72.54 | 84.10 | 78.03 | 76.84 | 48.48 |
| Qwen/Qwen3.5-9B (instruct, 9B) | 56.28 | 64.06 | 77.97 | 73.72 | 68.65 | 59.57 |
| Qwen/Qwen3-8B-Base (base, 8B) | 55.52 | 66.61 | 81.03 | 85.03 | 68.55 | 0.00 |
| CohereLabs/c4ai-command-r7b-12-2024 (instruct, 7B; labelled Arabic-specific in the table) | 54.19 | 60.20 | 80.84 | 69.41 | 65.14 | 49.72 |
| QCRI/Fanar-1-9B (base, 9B) | 52.42 | 63.49 | 81.61 | 81.83 | 70.09 | 14.42 |
| **Qwen/Qwen3.5-4B-Base (base, 4B)** | **50.27** | **64.54** | **85.44** | **87.25** | **71.64** | 0.00 |
| Qwen/Qwen2.5-7B-Instruct (instruct, 7B) | 49.26 | 44.96 | 74.33 | 47.06 | 49.83 | 54.65 |
| Qwen/Qwen2.5-3B-Instruct (instruct, 3B) | 47.80 | 49.37 | 68.01 | 46.23 | 47.28 | 49.90 |
| google/gemma-3-4b-it (instruct, 4B; American) | 46.93 | 48.05 | 74.90 | 40.36 | 45.78 | 50.55 |
| microsoft/Phi-4-mini-instruct (instruct, 3.8B; American) | 46.93 | 47.12 | 73.56 | 57.67 | 50.66 | 42.24 |
| ibm-granite/granite-3.3-8b-instruct (instruct, 8B; American) | 45.09 | 48.02 | 68.97 | 60.80 | 56.45 | 9.61 |
| Qwen/Qwen3.5-4B (instruct, 4B) | 44.97 | 53.59 | 70.69 | 58.36 | 55.03 | 7.67 |
| google/gemma-3-4b-pt (base, 4B; American) | 44.61 | 55.93 | 74.71 | 70.74 | 61.91 | 0.00 |
| meta-llama/Llama-3.1-8B (base, 8B; American) | 44.44 | 52.69 | 74.71 | 66.58 | 62.39 | 0.00 |
| Qwen/Qwen3.5-2B-Base (base, 2B) | 43.00 | 53.34 | 73.56 | 70.08 | 53.40 | 8.60 |
| Qwen/Qwen3-8B (instruct, 8B) | 39.38 | 35.26 | 52.68 | 24.48 | 32.16 | 57.47 |
| google/gemma-3-1b-it (instruct, 1B; American) | 37.90 | 38.76 | 59.39 | 30.09 | 34.83 | 26.16 |
| meta-llama/Llama-3.2-3B-Instruct (instruct, 3B; American) | 35.37 | 34.77 | 58.81 | 38.40 | 37.24 | 11.60 |
| Qwen/Qwen3.5-0.8B (instruct, 0.8B) | 33.03 | 38.52 | 57.85 | 35.02 | 27.34 | 23.24 |
| google/gemma-3-1b-pt (base, 1B; American) | 27.25 | 28.05 | 35.06 | 22.63 | 20.56 | 0.00 |

- No Falcon, small Jais-family, SILMA, LFM2 or Granite 4.x model appears in Table 6. The only first-generation Jais entry is jais-adapted-13b-chat, with an average of 49.51 ([QIMMA paper](https://arxiv.org/pdf/2604.03395)).
- The average is the plain mean of the 14 columns; for Qwen3.5-4B-Base the columns sum to 703.71, and 703.71 / 14 = 50.27. Base models score 0.00 on the generative FannOrFlop column. A base model that would otherwise score 50 there therefore loses about 3.6 points of average against instruct models ([QIMMA paper](https://arxiv.org/pdf/2604.03395)).

#### OALL and developer-reported scores
- OALL v2 (February 2025) replaced machine-translated and saturated tasks such as ACVA. It added native ArabicMMLU, human-translated MMLU, MadinahQA (Arabic language and grammar), AraTrust and the generative ALRAGE, run with lighteval ([OALL v2 blog](https://huggingface.co/blog/leaderboard-arabic-v2)). No OALL v3 was found as of 2026-10-19. The OALL results and requests datasets were last modified on 2025-02-09 ([HF API listing for OALL datasets](https://huggingface.co/api/datasets?author=OALL&limit=100)).
- The Hala authors ran the six multiple-choice OALL v2 tasks (ALRAGE excluded) and published a table ([Hala-9B card](https://huggingface.co/hammh0a/Hala-9B/blob/main/README.md); [Hala paper](https://arxiv.org/abs/2509.14008)):
  - Average, small models: Hala-1.2B 51.4, Qwen3-1.7B-Base 50.7, Qwen2-1.5B-Instruct 48.2, SILMA-Kashif-2B 47.7, Hala-700M 46.9, LFM2-1.2B 46.3, Qwen2.5-1.5B-Instruct 44.8, Hala-350M 41.9, LFM2-700M 41.4, LFM2-350M 34.3, Llama-3.2-1B 28.0, gemma-2-2b-it 27.1.
  - Average, 7B to 9B: Hala-9B 69.9, Fanar-1-9B-Instruct 69.2, command-r7b-arabic 65.6, Qwen3-8B-Base 64.9, Yehia-7B 63.9, ALLaM-7B 63.3, Qwen2-7B-Instruct 62.4.
  - MadinahQA (Arabic grammar): Fanar-1-9B-Instruct 73.3, Hala-9B 70.4, command-r7b-arabic 63.8, ALLaM-7B 54.2, Qwen3-8B-Base 52.2, and Qwen2-1.5B-Instruct 45.5, the best of the models up to 2B.
- Falcon-H1-Arabic's OALL scores are TII self-reported, run with a vLLM backend rather than the leaderboard's own:
  - Scores: about 62 (3B), 71.7 (7B) and about 75 (34B) ([TII blog](https://huggingface.co/blog/tiiuae/falcon-h1-arabic)).
  - The press release gives 61.87 and 71.47 ([ITWeb, 2026-01-05](https://www.itweb.co.za/article/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model/PmxVE7KEdENqQY85)).
  - TII says the 3B beats Gemma-4B, Qwen3-4B and Phi-4-mini by roughly ten points ([TII blog](https://huggingface.co/blog/tiiuae/falcon-h1-arabic)).
- Fanar-1-9B-Instruct's own card reports OALL v2 at 66.29 (0-shot) and ArabicMMLU at 67.69. On the same card, OALL v2 is 64.21 for gemma-2-9b-it, 63.66 for ALLaM-7B, 62.69 for Qwen2.5-7B and 55.97 for Llama-3.1-8B ([Fanar card](https://huggingface.co/QCRI/Fanar-1-9B-Instruct)).
- Inception's Jais-2-8B card reports AraGen-12-24 3C3H scores ([Jais-2-8B card](https://huggingface.co/inceptionai/Jais-2-8B-Chat)):
  - Jais-2-8B 58.64, Fanar-1-9B-Instruct 53.16, ALLaM-7B v1 53.16, Command R7B Arabic 49.18, Falcon-H1-7B-Instruct 47.28, jais-family-6p7b-chat 41.00 and Qwen3-8B 36.52.
  - Arabic IFEval strict is 31.93 / 35.44 for Falcon-H1-7B-Instruct against 58.17 / 67.09 for Jais-2-8B.
- Qwen3 technical report Table 28 (Arabic, Qwen's own evaluation):
  - MMMLU-Arabic, thinking mode: 38.9 (0.6B), 53.2 (1.7B), 67.7 (4B), 74.4 (8B).
  - MMMLU-Arabic, non-thinking: 35.4, 43.6, 56.7, 64.6.
  - INCLUDE-Arabic, thinking: 41.1, 44.6, 55.4, 67.9.

  ([Qwen3 technical report](https://arxiv.org/html/2505.09388v1))
- The Qwen3.5 card reports only multilingual averages, not Arabic: MMMLU 76.1 (4B) and 81.2 (9B); INCLUDE 71.0 and 75.6 ([Qwen3.5-9B card](https://huggingface.co/Qwen/Qwen3.5-9B)).
- Arabic base-model scores from the SmolLM3 card ([SmolLM3-3B card](https://huggingface.co/HuggingFaceTB/SmolLM3-3B)):

  | Benchmark | Qwen3-4B | Qwen3-1.7B | Llama 3.2 3B | SmolLM3 |
  |---|---|---|---|---|
  | Belebele-ar | 51.78 | 42.33 | 45.33 | 40.22 |
  | Global MMLU cloze (ar) | 31.85 | 29.37 | 27.67 | 28.57 |

- Ministral 3's card reports multilingual MMLU for base models: 0.652 (3B) and 0.706 (8B), against Qwen3-4B-Base 0.677 and Gemma-3-4B-Base 0.516 ([Ministral-3-3B card](https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512)).
- AraLingBench (150 expert-written MCQs on grammar, morphology, spelling, reading and syntax) ([AraLingBench paper, December 2025](https://arxiv.org/html/2511.14295)):
  - 7B to 9B: ALLaM-7B 74.0, Yehia-7B 74.0, Fanar-1-9B-Instruct 60.0, Qwen3-8B-Base 56.7, SILMA-9B 53.3.
  - Small models: Phi-4-mini 46.0, Qwen2.5-3B 40.0, Hala-1.2B 38.7.
- The Naseej evaluation (240 Arabic items, LLM-judged 0 to 5) scored Gemma 3 12B 4.548, Fanar-1-9B 4.303, Tiny Aya Global 4.234, ALLaM 7B 4.189 and Gemma 3 1B 3.319 ([arXiv 2606.21460, June 2026](https://arxiv.org/html/2606.21460v1)).

#### Classical Arabic and Islamic text
- Fann or Flop (6,984 classical-to-modern poem explanations across 12 eras) tested only two models under 10B ([Fann or Flop, EMNLP 2025](https://arxiv.org/html/2505.18152v1)):
  - ALLaM-7B scored lowest of all models: faithfulness 1.32/5, fluency 2.11/5, depth 3.12/10.
  - Fanar-Star 7B scored 2.16, 3.40 and 2.88.
- In QIMMA's FannOrFlop column, the small leaders are Yehia-7B (59.64), Qwen3.5-9B (59.57), Qwen3-8B (57.47) and Jais-2-8B (51.94). Fanar-1-9B-Instruct scores 0.02 and all base models score 0.00 ([QIMMA](https://arxiv.org/pdf/2604.03395)).
- IslamicEval 2025 (detecting and correcting made-up Quran verses and hadiths; grounded Quran and hadith QA) drew 13 final teams whose system papers rely on retrieval ([IslamicEval overview](https://aclanthology.org/2025.arabicnlp-sharedtasks.67/)).
- QIAS 2025 (Islamic inheritance and knowledge MCQs): ALLaM, Fanar, LLaMA and Mistral scored below 50%, while o3 and Gemini 2.5 scored above 90%. This comes from the overview abstract as shown on an author page ([ACL Anthology author page](https://aclanthology.org/people/shahd-gaben/); [QIAS site](https://sites.google.com/view/qias2025)).
- A 2026 review of hadith computing lists Sanadset 650K, AR-Sanad 280K, the Rezwan 1.2M-narration pipeline and Noor-Ghateh word segmentation. It reports no LLM numbers for chain and matn segmentation or narrator identification ([Haque and Islam, arXiv 2608.20364](https://arxiv.org/html/2608.20364)).
- Sadeed's diacritization benchmark SadeedDiac-25 is half Classical Arabic and half MSA ([Sadeed GitHub](https://github.com/misraj-ai/Sadeed)). It is the only small-decoder result found that is anchored in classical text (details in section 4).

#### Does general rank predict this task?
- AraLingBench correlates with ArabicMMLU at r = 0.884, but individual models diverge: Hala-9B scores 65.6 ArabicMMLU and 54.7 AraLingBench, while Yehia-7B scores 64.9 and 74.0 ([AraLingBench](https://arxiv.org/html/2511.14295)).
- Inside OALL v2, Qwen3-8B-Base is near the top on ArabicMMLU (65.0) but last of its group on MadinahQA (52.2) ([Hala-9B card](https://huggingface.co/hammh0a/Hala-9B/blob/main/README.md)).
- Arabic fine-tuning lifts small models past larger ones: Hala-350M 41.9 against LFM2-700M 41.4 ([Hala-9B card](https://huggingface.co/hammh0a/Hala-9B/blob/main/README.md)).
- An answer-matching bug fix in AlGhafa moved some models by up to 20 points ([OALL v2 blog](https://huggingface.co/blog/leaderboard-arabic-v2)).

### Inferences
- At 4B and below, Qwen3.5-4B-Base is the strongest measured non-American base model on current Arabic evidence: QIMMA 50.27 average and 64.54 ArabicMMLU, close to the 7B to 9B Arabic-centric models on ArabicMMLU, AraTrust and 3LM. Qwen3-1.7B-Base is the strongest measured model near 2B (OALL six-task average 50.7). The unmeasured exceptions are Falcon-H1 at 1.5B to 3B and Falcon-H1-Arabic-3B, whose weights are not public.
- QIMMA shows large base-versus-instruct gaps, for example Qwen3-8B-Base 66.61 against Qwen3-8B 35.26 on ArabicMMLU. These likely reflect answer-format failures in instruct and thinking models rather than missing Arabic knowledge. Fine-tuning from the -Base checkpoint avoids the chat and thinking templates.
- Segmenting a hadith into chain, matn and comments depends mostly on recognising formulaic transmission phrases and name sequences. That is closer to sequence labelling than to the MSA knowledge MCQs these leaderboards test. The benchmarks above can rule out weak models (Llama 3.2, Gemma 3 1B, Jais family small) but cannot rank the strong ones for this task. A pilot fine-tune on the project's own data would settle it.

### Gaps
- No live OALL v2 numbers were read for Qwen3 or Qwen3.5 small, Gemma 3, Falcon-H1, Jais family small or SmolLM3.
- No independent Arabic evaluation of Falcon-H1 0.5B to 3B, Falcon-H1-Arabic, Gemma 4, LFM2.5, Granite 4.x or Ministral 3 was found.
- The QIMMA numbers were decoded from glyph codes in the PDF and should be spot-checked against the rendered table. Which harness settings (shots, generative or log-likelihood) apply per column was not read.
- No benchmark tests small models on fully vocalized classical text, on hadith chain and matn spans, or on structured extraction after fine-tuning.
- Whether MadinahQA draws on classical grammar sources is unknown.

## 3. How efficient are these tokenizers on Arabic, especially vocalized classical Arabic, and is stripping diacritics common practice?

### Takeaway
Harakat are expensive. On the project's own hadith entries, 91.5% of which are fully vocalized, the Qwen3 tokenizer spends 5.10 tokens per word, against 1.69 after stripping harakat (3.0 times as many). Qwen3.5's new tokenizer spends 2.57 against 1.46 (1.8 times). A March 2026 EACL paper finds the same ratio for Qwen3 on MSA (3.25 times). It also finds full diacritization costs between 2.2 times (Llama 3) and 5.3 times (Jais 2), while stripping natural diacritics barely changes benchmark accuracy. Stripping diacritics is common in Arabic NLP, and for a span-marking task it can be done losslessly by keeping a character map back to the vocalized original.

### Cited Findings

#### Local measurement on the project's hadith entries
- Corpus: `hadiths.nass` (full entry text, chain plus matn) in the project's hadith-kg database, with 715,790 entries. Two seeded random samples were drawn: 3,000 entries (seed 20261019) and 20,000 entries (seed 7). The figures below come from the 20,000-entry sample; the 3,000-entry sample agreed to within 1% ([hadith-kg.db](file:///Users/ahmediqbal/Documents/icma/data/raw/hadith-kg/hadith-kg.db)).
- Tokenizers: the `tokenizer.json` files of [Qwen3-8B (MLX copy)](https://huggingface.co/Qwen/Qwen3-8B-MLX-4bit) and [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B), read from the local Hugging Face cache. The Qwen3.5 tokenizer is shared by 0.8B, 4B and 9B; the 0.8B and 9B files have identical BPE vocab and merges counts.
- Method: a pure-Python emulation of each file's declared pipeline (NFC normalizer, regex split, byte-level mapping, BPE merges), with every output token asserted to exist in the vocabulary. Stripping removed U+064B to U+0652 and U+0670. The tokenizers library was not installed, so counts may differ slightly from the official implementation. Script: `/private/tmp/claude-501/-Users-ahmediqbal-Documents-icma/2363b3e8-fbd5-46ec-a2d9-8ddf1f0b3abd/scratchpad/tokcount.py` (session scratchpad, temporary).
- Corpus shape:
  - Mean entry length is 587 characters and 88.7 whitespace words. Characters per entry: p50 432, p90 1,035, p99 2,804, max 21,563.
  - Marks per Arabic letter average 0.76. Of the entries, 91.5% have at least 0.5 marks per letter, 7.0% have 0.05 to 0.5, and 1.5% are effectively unvocalized.
  - Musnad Ahmad, Ibn Abi Shayba, al-Tabari's Tafsir, al-Tabarani and al-Bayhaqi are fully vocalized; Tarikh Dimashq is mostly partial.

  ([local measurement](file:///Users/ahmediqbal/Documents/icma/data/raw/hadith-kg/hadith-kg.db))
- Results, all 20,000 entries ([local measurement](file:///Users/ahmediqbal/Documents/icma/data/raw/hadith-kg/hadith-kg.db)):

| Tokenizer | Text | Tokens per entry (mean) | Tokens per word | Characters per token | Per-entry tokens p50 / p90 / p99 / max | Entries over 2,048 tokens |
|---|---|---|---|---|---|---|
| Qwen3 (151,643 BPE) | as stored (vocalized) | 452.4 | 5.10 | 1.30 | 331 / 803 / 2,137 / 17,144 | 1.09% |
| Qwen3 | harakat stripped | 150.0 | 1.69 | n/a | 111 / 263 / 711 / 5,233 | 0.15% |
| Qwen3.5 (248,044 BPE) | as stored (vocalized) | 227.6 | 2.57 | 2.58 | 166 / 402 / 1,105 / 8,824 | 0.34% |
| Qwen3.5 | harakat stripped | 129.2 | 1.46 | n/a | 96 / 226 / 612 / 4,583 | 0.10% |

- On the fully vocalized subset, inflation from harakat is 3.17 times for Qwen3 (5.37 against 1.69 tokens per word) and 1.83 times for Qwen3.5 (2.66 against 1.46). On the entries already stored unvocalized, the two tokenizers give 1.76 and 1.48 tokens per word as stored, and 1.70 and 1.47 once the few remaining marks are removed ([local measurement](file:///Users/ahmediqbal/Documents/icma/data/raw/hadith-kg/hadith-kg.db)).
- "Words" here are whitespace-separated units. This corpus writes punctuation such as `،` and `:` as free-standing units, so tokens per word run slightly lower than under a linguistic word count. The ratios between stripped and vocalized text are unaffected ([local measurement](file:///Users/ahmediqbal/Documents/icma/data/raw/hadith-kg/hadith-kg.db)).
- Worked example: ` حَدَّثَنَا` is pre-split by the Qwen3 regex into six pieces (` ح`, `َد`, `َّ`, `ث`, `َن`, `َا`) and costs 9 tokens, against 3 tokens for unvocalized ` حدثنا`. Qwen3.5 keeps the vocalized word as one piece and spends 3 tokens, or 2 unvocalized ([local measurement](file:///Users/ahmediqbal/Documents/icma/data/raw/hadith-kg/hadith-kg.db)).

#### Why some tokenizers fragment vocalized words
- Harakat are Unicode non-spacing marks, category Mn, so they fall outside the `\p{L}` letter class ([EACL26, p. 427](https://aclanthology.org/2026.findings-eacl.22.pdf)).
- Regexes without `\p{M}` end each letter run at every haraka:
  - Qwen3: `[^\r\n\p{L}\p{N}]?\p{L}+` ([Qwen3 tokenizer.json, read locally](https://huggingface.co/Qwen/Qwen3-8B-MLX-4bit)).
  - Llama 3: same letter-run pattern ([Llama 3 tokenizer.py](https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama3/tokenizer.py)).
  - LFM2-1.2B: same pattern ([LFM2-1.2B tokenizer.json](https://huggingface.co/LiquidAI/LFM2-1.2B/raw/main/tokenizer.json)).
  - cl100k: `\p{L}++` ([tiktoken openai_public.py](https://raw.githubusercontent.com/openai/tiktoken/main/tiktoken_ext/openai_public.py)).
- Regexes that include marks in the letter classes keep a vocalized word together:
  - Qwen3.5 changed its regex to `[^\r\n\p{L}\p{N}]?[\p{L}\p{M}]+` ([Qwen3.5 tokenizer.json, read locally](https://huggingface.co/Qwen/Qwen3.5-9B)).
  - o200k (GPT-4o) uses classes such as `[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*` ([tiktoken openai_public.py](https://raw.githubusercontent.com/openai/tiktoken/main/tiktoken_ext/openai_public.py)).
  - Falcon-H1 uses an o200k-style pattern that includes `\p{M}`, preceded by a punctuation splitter and followed by a digit splitter ([Falcon-H1-1.5B-Deep tokenizer.json](https://huggingface.co/tiiuae/Falcon-H1-1.5B-Deep-Instruct/raw/main/tokenizer.json)).
- SentencePiece tokenizers such as Gemma 3 (split digits, preserved whitespace, byte fallback) have no regex pre-split ([Gemma 3 technical report](https://arxiv.org/html/2503.19786)).

#### Published measurements (MSA corpus, so not directly comparable with the hadith figures)
- Inoue, Alhafni, Habash and Baldwin, "Do Diacritics Matter?", Findings of EACL 2026, Table 2, on the Wild2MaxDiacs corpus. Tokens per word, undiacritized / as found / fully diacritized ([EACL26](https://aclanthology.org/2026.findings-eacl.22.pdf)):
  - ALLaM 7B (64,000 vocab, 954 entries containing a diacritic): 1.4 / 2.7 / 4.0
  - Llama-3.1 8B (128,256): 2.6 / 4.2 / 5.8
  - GPT-4o o200k (200,000): 2.4 / 4.1 / 6.3
  - Fanar 9B (128,256): 2.4 / 4.2 / 6.7
  - Qwen3 8B: 2.4 / 4.7 / 7.8
  - Aya-Expanse 8B (256,000): 2.2 / 4.6 / 7.8
  - Jais 13B (84,992): 1.9 / 5.0 / 9.3
  - Jais 2 8B (150,222): 1.9 / 5.5 / 10.1
- EACL26 attributes the extra cost to vocabularies with few diacritic-bearing entries. Jais tokenizers fall below one character per token on fully diacritized text. Only 0.0% to 0.2% of words keep the same token count after diacritization, except ALLaM at 6.7% ([EACL26](https://aclanthology.org/2026.findings-eacl.22.pdf)).
- Other fertility figures, each on its own corpus:
  - Jais paper: Jais fertility 1.050 against GPT-2's 4.171 ([Jais paper](https://ar5iv.labs.arxiv.org/html/2308.16149)).
  - Kuwain: 2.30 tokens per word for its extended tokenizer ([Kuwain](https://arxiv.org/html/2504.15120)).
  - AraToken: SentencePiece unigram at 1.199 tokens per word on normalized, undiacritized text ([AraToken](https://arxiv.org/html/2512.18399v1)).
  - Tahakom: 1.37 falling to 1.10 as vocabulary grows from 32K to 128K, on a mix that includes the Shamela classical corpus ([arXiv 2510.13481](https://arxiv.org/html/2510.13481)).
- ALLaM reports that its merged tokenizer reaches the fertility of an Arabic-only tokenizer, and that Llama-2 often falls back to characters or bytes on Arabic ([ALLaM paper](https://arxiv.org/html/2407.15390)). The Falcon-H1 tokenizer study was English-only and found fertility did not reliably predict downstream scores ([Falcon-H1 report](https://arxiv.org/html/2507.22448)).

#### Practice and effect on accuracy
- Many Arabic NLP pipelines strip diacritics in preprocessing, for example AraBERT and CAMeLBERT. EACL26 itself strips with CAMeL Tools `dediac_ar` ([EACL26](https://aclanthology.org/2026.findings-eacl.22.pdf)).
- Fanar removes diacritics from Arabic text before training its tokenizer, "as most data is not diacritized", while keeping diacritic characters in the vocabulary and training on diacritization tasks ([Fanar paper, p. 17](https://arxiv.org/pdf/2501.13944)). Jais removes rare diacritic marks and normalises with CAMeL Tools ([Jais paper](https://ar5iv.labs.arxiv.org/html/2308.16149)).
- An opinion paper argues that both stripping and inconsistent encoding of diacritics harm models ([Gorman and Pinter, NAACL 2025](https://aclanthology.org/2025.naacl-short.25)).
- EACL26 Table 5 (zero-shot macro average over ArabicMMLU, ArabCulture and AraTrust). Removing natural diacritics left accuracy unchanged, while automatic full diacritization lowered it significantly for most models ([EACL26](https://aclanthology.org/2026.findings-eacl.22.pdf)):

  | Model | Undiacritized | Full |
  |---|---|---|
  | Llama-3.1 8B | 58.3 | 46.0 |
  | Jais 13B | 59.8 | 47.6 |
  | Fanar 9B | 65.1 | 58.6 |
  | ALLaM 7B | 63.5 | 58.9 |
  | Qwen3 8B | 60.9 | 57.7 |

### Inferences
- Stripping harakat before the model, while keeping a character-offset map back to the stored text, cuts input tokens to about a third for Qwen3 and to 57% for Qwen3.5 on this corpus. It also makes short-context models viable. The marked spans can be projected back onto the vocalized original exactly, so nothing is lost in the output.
- Derived token budgets for 400,000 entries (input side only; output depends on the label format):

  | Tokenizer and text | Input tokens |
  |---|---|
  | Qwen3, vocalized | about 181M |
  | Qwen3.5, vocalized | about 91M |
  | Qwen3, stripped | about 60M |
  | Qwen3.5, stripped | about 52M |

- If the team keeps harakat in the input, Qwen3.5's tokenizer is the most efficient measured on hadith text, at half Qwen3's cost. Its 1.83-times inflation is also below every MSA ratio in EACL26 (2.2 to 5.3 times), though that comparison crosses corpora.
- Derived from EACL26 fertility and this corpus's p99 of about 425 words per entry (2,804 characters at 6.6 characters per word):
  - Jais-2-8B (8,192 context) would need about 4,300 tokens for a p99 vocalized entry and about 800 stripped.
  - The Jais family small models (2,048 context) only fit stripped text.
  - ALLaM's 4,096 context fits a p99 vocalized entry at about 1,700 tokens.
- Harakat could still help the model in a few places, for example passive forms such as حُدِّثْتُ or telling names apart. Whether stripping costs segmentation accuracy is untested. A pilot should compare stripped and vocalized input on the same model.

### Gaps
- No measurement on hadith or other classical text exists for the ALLaM, Jais 2, Falcon-H1, Gemma 3 or 4, Phi-4-mini, LFM2, Ministral or Fanar tokenizers. Their files were not available locally, and downloading them needs approval. Extending the local script with the official tokenizers library would close this.
- Falcon-H1's tokenizer keeps marks inside words, but how many of its merges contain harakat is unknown. EACL26 shows that o200k's `\p{M}` alone did not lower its fertility.
- The Qwen3.5 count comes from an emulation, not the official tokenizers library.
- Petrov et al. (2023) Arabic tokenization premiums were not retrieved.

## 4. What published reports exist of fine-tuning small models for Arabic extraction, NER, segmentation or classical-text tasks?

### Takeaway
No published work fine-tunes a decoder of 8B or less to split a hadith into chain and matn spans, let alone the finer typed spans. The best public baselines are non-LLM. pyHadith (spaCy) reports chain and matn segmentation F1 0.983 and narrator-name F1 0.973. Arabic NER shared tasks are still won by fine-tuned encoders. The closest small-decoder precedent is Sadeed, a 1.5B decoder fine-tuned for diacritizing mostly classical text, whose main error was hallucinated words when it rewrote the input.

### Cited Findings
- **pyHadith** (spaCy 2.2.4 models with a BEGINMATN tag, an NER model and a rule) ([pyHadith on libraries.io, v0.1.4, 2020; removed from PyPI](https://libraries.io/pypi/pyHadith)):
  - Trained on 102,153 hadiths with 20% held out.
  - Chain and matn segmentation: precision 0.9709, recall 0.9961, F1 0.9833 on 20,430 hadiths.
  - Narrator-name NER: F1 0.9732.
- **Older chain and matn segmentation:**
  - Bigram features: 92.5% accuracy ([W19-5605](https://aclweb.org/anthology/W19-5605.pdf); search snippet only).
  - PPM compression: 92.76% and 90.10% ([ICON 2020](https://preview.aclanthology.org/retraction/2020.icon-main.4); search snippet only).
- **KITAB and OpenITI.** Muther and Smith compared single-pass sequence labelling with retrieve-and-tag for chain detection across OpenITI genres. They note that full-document seq2seq models are limited by memory and long documents ([WANLP 2020](https://aclanthology.org/2020.wanlp-1.12)). KITAB found annotators' definitions of a chain diverged until they compared annotations ([KITAB blog](https://kitab-project.org/Tracking-Traditions-Identifying-Isnads-in-the-OpenITI-Corpus/)).
- **Rezwan corpus.** An LLM pipeline segmented over 1.2M narrations and separated chain from text. On 1,213 narrations, six experts rated chain-text separation 9.33 out of 10. The models used and whether they were fine-tuned are not stated in the abstract ([arXiv 2510.03781](https://arxiv.org/abs/2510.03781)).
- **Sadeed** (Kuwain 1.5B decoder, supervised fine-tuning) ([Sadeed paper v2](https://arxiv.org/html/2504.21635v2)):
  - Data and setup: 1,042,698 examples (about 53M words, mostly Tashkeela classical text), max length 512, 8 A100 GPUs.
  - Results: DER 1.24 and WER 2.94 on the classical Fadel test set; DER 7.29 and WER 13.74 on SadeedDiac-25.
  - Errors: about 7.19 of the 9.92 WER points (without case endings) come from hallucinated words. The authors realign output to input with Needleman-Wunsch.
  - Leakage: the Fadel and Abbad test sets overlap with training sources.
- **WojoodNER 2024** (fine-grained Arabic NER):
  - The best flat-NER system was AraBERTv0.2 with MLP heads and a kNN store (F1 91, against an AraBERTv2 baseline of 89).
  - A team that fine-tuned BLOOMZ-7b-mt and Gemma-7b got its best run from AraBERTv2 (87), below the baseline.
  - On nested NER no team beat the AraBERTv2 baseline of 92.

  ([WojoodNER 2024 overview](https://arxiv.org/html/2407.09936v1))
- **WojoodNER 2023** flat NER: AraBERTv2 baseline 87.33, top system 91.96 ([overview](https://arxiv.org/pdf/2310.16153)).
- **Hala.** Arabic instruction tuning of LFM2-sized bases raised the OALL six-task average from 34.3 to 41.9 at 350M, from 41.4 to 46.9 at 700M, and from 46.3 to 51.4 at 1.2B ([Hala-9B card](https://huggingface.co/hammh0a/Hala-9B/blob/main/README.md)).
- **AraReasoner** applied LoRA to DeepSeek-R1 distills (1.5B, 7B, 14B) on Arabic tasks ([arXiv 2506.08768](https://arxiv.org/pdf/2506.08768)).
- **Vendor extraction fine-tunes and guidance.** Liquid AI ships LFM2-1.2B-Extract for schema-guided extraction with Arabic listed ([model card](https://huggingface.co/LiquidAI/LFM2-1.2B-Extract)). Google recommends Gemma 3 270M for high-volume extraction and structuring after fine-tuning ([Google developers blog](https://developers.googleblog.com/en/introducing-gemma-3-270m/)).
- **Leakage source in this corpus.** The hadith-kg database groups entries into 20,745 meaning groups (`hadiths.group_id`; NULL for mawquf and maqtu entries) and takhrij clusters within each group ([hadith-kg.db schema](file:///Users/ahmediqbal/Documents/icma/data/raw/hadith-kg/hadith-kg.db)).

### Inferences
- The bar for a fine-tuned decoder is about 0.98 F1 for the chain and matn split, set by an encoder-style pipeline. The decoder's case rests on two things: the finer typed spans (collector formulas, collector comments, narrator remarks, the link to the Prophet) and robustness across collections. A token-classification encoder baseline, such as CAMeLBERT or AraBERT on stripped text with a sliding window, would make a useful control.
- Sadeed's hallucination problem argues against having the model rewrite the entry with tags inserted. The model should emit span labels over input positions (word indices or boundary words) that are checked against the input, or its output should be realigned to the input.
- One hadith appears across many collections with near-identical wording. Splitting train and test by `group_id`, rather than by entry, avoids the overlap leakage seen in the Tashkeela test sets.

### Gaps
- No LoRA or full fine-tune of Qwen3, Qwen3.5, Falcon-H1, ALLaM, Jais or Fanar on Arabic NER, segmentation or classical text with published scores was found.
- No comparison of LoRA decoders against Arabic encoders on the same NER splits was found.
- Muther and Smith's scores were not retrieved because the PDF did not parse.
- IslamicEval 2025 and QIAS 2025 team-level models and scores were not retrieved.
- Whether Sadeed was trained with LoRA or full fine-tuning is not stated.
- A 2025 thesis on narrator relation extraction with more than 270,000 records appeared only in a snippet.

## 5. What are the practical fine-tuning notes: tooling support, GPU memory, and known pitfalls?

### Takeaway
Qwen3, Llama-architecture ALLaM and Gemma 3 are plain transformers that every tool supports. Qwen3.5 adds two kinds of work. Its Gated DeltaNet layers need transformers v5 and the `fla` and `causal_conv1d` kernels, and Unsloth advises against QLoRA. It also ships with a vision encoder that has to be dropped for text-only use. Even so, vLLM, LLaMA-Factory, Unsloth and MLX-LM all support it, and 4-bit MLX copies are already in the local cache. Falcon-H1 and LFM2 are supported by vLLM, llama.cpp, MLX-LM and LLaMA-Factory. Jais (both generations) has the weakest tooling. LoRA on 0.8B to 4B fits in 3 to 10 GB; full fine-tuning of a 4B model needs an 80 GB GPU.

### Cited Findings
- **Qwen3.5 in transformers.** The text-only class is `Qwen3_5ForCausalLM`, alongside `Qwen3_5ForConditionalGeneration` ([transformers Qwen3.5 docs, v5.20.1](https://huggingface.co/docs/transformers/model_doc/qwen3_5)). Unsloth says older transformers versions will not work ([Unsloth Qwen3.5 fine-tuning guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune)).
- **Qwen3.5 kernels.** The Gated DeltaNet layers use the optional `causal_conv1d` and `fla` kernels. Without them the model silently falls back to slower, more memory-hungry PyTorch code ([transformers Qwen3.5 docs](https://huggingface.co/docs/transformers/model_doc/qwen3_5)).
- **Qwen3.5 in Unsloth** ([Unsloth Qwen3.5 guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune)):
  - bf16 LoRA is supported, and Unsloth advises against QLoRA for Qwen3.5.
  - Its example targets q, k, v, o, gate, up and down projections.
  - The first run compiles custom kernels.
  - It warns that a mismatch between training and inference chat templates is the most common cause of degraded exports.
- **Qwen3.5 serving.** vLLM serves Qwen3.5 as `Qwen3_5ForConditionalGeneration`, with `--language-model-only` for text, and supports LoRA adapters for Qwen3.5, Falcon-H1, LFM2 and Granite hybrid models ([vLLM supported models](https://docs.vllm.ai/en/latest/models/supported_models.html); [Qwen3.5-9B card](https://huggingface.co/Qwen/Qwen3.5-9B)). MLX-LM has `qwen3_5.py` (text only, vision weights dropped), with its kernel path switched off during training ([MLX-LM qwen3_5.py](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/models/qwen3_5.py)).
- **Templates.** LLaMA-Factory has `qwen3`, `qwen3_nothink`, `qwen3_5`, `qwen3_5_nothink`, `falcon_h1`, `lfm2`, `gemma3`, `gemma3n`, `phi4_mini` and `llama3` templates. Jais is not listed ([LLaMA-Factory README](https://github.com/hiyouga/LLaMA-Factory)).
- **Qwen3.5 small-model behaviour.** The small models default to non-thinking mode, and the 2B is prone to thinking loops at the recommended sampling settings ([Qwen3.5-2B card](https://huggingface.co/Qwen/Qwen3.5-2B)).
- **Falcon-H1 support** ([Falcon-H1 GitHub](https://github.com/tiiuae/Falcon-H1); [transformers Falcon-H1 docs](https://huggingface.co/docs/transformers/model_doc/falcon_h1)):
  - transformers `FalconH1ForCausalLM`.
  - Unsloth and Axolotl, per TII (2025-06-30).
  - llama.cpp from 2025-07-09, with official GGUFs.
  - MLX integration from 2025-09-22.
  - TII recommends bfloat16, not float16, and the docs recommend left padding for batched generation.
- **LFM2 support.** llama.cpp has LFM2 and Liquid ships GGUFs ([llama.cpp PR 16204](https://github.com/ggml-org/llama.cpp/pull/16204); [Liquid docs](https://docs.liquid.ai/lfm/inference/llama-cpp)). MLX-LM has `lfm2.py` and `lfm2_moe.py` ([MLX-LM models](https://github.com/ml-explore/mlx-lm/tree/main/mlx_lm/models)). The LFM2.5 card links Unsloth and TRL notebooks ([LFM2.5-1.2B-Instruct card](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct)).
- **Jais support.** vLLM runs Jais 2 (`Jais2ForCausalLM`) only through its Transformers backend and does not list Jais v1. MLX-LM has no Jais file ([vLLM supported models](https://docs.vllm.ai/en/latest/models/supported_models.html); [MLX-LM models](https://github.com/ml-explore/mlx-lm/tree/main/mlx_lm/models)). The Jais family needs its custom `JAISLMHeadModel` code ([config](https://huggingface.co/inceptionai/jais-family-590m/blob/main/config.json)).
- **Gemma 3 dtype.** Activations exceed the float16 maximum on float16-only GPUs (T4, V100, RTX 20 series). bf16 GPUs are unaffected, and Unsloth has a workaround ([Unsloth Gemma 3 guide](https://docs.unsloth.ai/models/gemma-3-how-to-run-and-fine-tune)).
- **Memory, Unsloth figures:**
  - Qwen3.5 bf16 LoRA needs about 3 GB (0.8B), 5 GB (2B), 10 GB (4B) and 22 GB (9B), and full fine-tuning about four times as much ([Unsloth Qwen3.5 guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune)).
  - General minimums: QLoRA / LoRA 16-bit 3.5 / 8 GB at 3B, 5 / 19 GB at 7B, 6 / 22 GB at 8B ([Unsloth requirements](https://unsloth.ai/docs/get-started/beginner-start-here/unsloth-requirements)).
- **Memory, LLaMA-Factory per-billion-parameter rules:**
  - Full AMP: 18 GB per billion parameters.
  - Full pure bf16: 8 GB.
  - LoRA 16-bit: 2 GB.
  - QLoRA 4-bit: 0.5 GB.
  - Quoted 7B figures: 120 / 60 / 16 / 6 GB.

  ([LLaMA-Factory README](https://github.com/hiyouga/LLaMA-Factory))
- **Unverified tooling details.** Whether packed training resets recurrent state at example boundaries in Qwen3.5, Falcon-H1 or LFM2 is not documented. The Falcon-H1 Mamba mixer projections are called `in_proj` and `out_proj` in its config docstring ([transformers Falcon-H1 docs](https://huggingface.co/docs/transformers/model_doc/falcon_h1)).
- **Local environment.** This machine's Hugging Face cache already holds Qwen/Qwen3.5-9B (bf16), mlx-community Qwen3.5-0.8B, 4B and 9B 4-bit, and Qwen3-8B-MLX-4bit. No tokenizers or transformers package is installed in the system Python or in `pipeline/.venv` ([local cache](file:///Users/ahmediqbal/.cache/huggingface/hub)).

### Inferences
- **Lowest tooling risk.** Qwen3 (0.6B, 1.7B, 4B Base) is the lowest-risk path: dense, supported by every trainer and server, and usable on a Mac through MLX. Its cost is three times the tokens on vocalized input, which stripping removes.
- **Qwen3.5 checklist.** Qwen3.5 (0.8B, 2B, 4B Base) should give better Arabic per parameter and tokens per entry, at the price of:
  - pinning transformers v5 and installing `fla` and `causal_conv1d` on the training GPU;
  - using bf16 LoRA or full fine-tuning, not QLoRA;
  - loading the text-only class;
  - checking with `named_modules()` which projections in the DeltaNet layers receive adapters;
  - avoiding sequence packing until state leakage is ruled out.
- **Hardware, derived from the rules above.** LoRA on any model up to 4B fits a single 24 GB GPU. Full fine-tuning in mixed precision with AdamW needs about 15 GB (0.8B), 36 GB (2B) and 72 GB (4B) before activations, so 4B full fine-tuning needs one 80 GB GPU or optimizer offload or sharding.
- **Large-vocabulary logits.** fp32 logits cost about 1 MB per token at Qwen3.5's 248,320 vocabulary (0.6 MB for Qwen3), so a training micro-batch of 8,192 tokens holds about 8 GB of logits plus the same again for their gradients. Use a trainer with chunked or fused cross-entropy, or keep micro-batches short. Stripped input (about 130 tokens per entry) keeps sequences short anyway.
- **Embedding share.** The embedding table is a large share of the smallest models: about 254M of Qwen3.5-0.8B's parameters (248,320 by 1,024, tied) and 170M of Gemma 3 270M's. Capacity for the task sits in the remaining layers, which favours 2B or 4B over sub-1B for the finer span types.
- **Local inference.** MLX-LM has model files for Qwen3.5, Falcon-H1, LFM2, Gemma 3 and Granite hybrid but not Jais. Qwen3 also runs, since Qwen publishes official MLX conversions such as the Qwen3-8B-MLX-4bit already in the local cache. Running 400,000 stripped entries (about 52M input tokens with Qwen3.5) is a batch job whose speed was not measured.

### Gaps
- No documented batch-inference throughput for vLLM, llama.cpp or MLX on these small models; this needs a local benchmark.
- Unconfirmed tooling details:
  - minimum transformers versions for Falcon-H1, LFM2 and Granite hybrids;
  - Falcon-H1's need for `mamba-ssm` kernels, and its speed without them;
  - Unsloth support for LFM2 and Granite 4;
  - llama.cpp support for Jais 2;
  - MLX LoRA training speed on hybrid models.
- No reports of catastrophic forgetting or other problems specific to fine-tuning these models on Arabic text were found.
- Engine support for ALLaM (Llama architecture, so likely universal) and Fanar (Gemma 2 architecture) was not checked against documentation.
