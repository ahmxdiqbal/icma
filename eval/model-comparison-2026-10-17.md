| Model | Done | Cost (USD) | Time (s) | Warnings | Verbatim extractions | CL recall | CL precision | PCL recall | Convergence verdict right |
|---|---|---|---|---|---|---|---|---|---|
| deepseek/deepseek-v4-pro | yes | 0.055 | 1127 | 3 | 46/46 | 0.00 | 0.00 | 0.00 | no |
| deepseek/deepseek-v4-pro-0813 | yes | 0.228 | 770 | 66 | 1/1 | 0.00 | 0.00 | 0.00 | yes |
| deepseek/deepseek-v4.1-flash | no | 0.007 | 65 | 0 | 0/0 | - | - | - | - |
| z-ai/glm-5.3 | no | 0.456 | 320 | 0 | 0/0 | - | - | - | - |
| moonshotai/kimi-k3 | yes | 2.071 | 893 | 1 | 50/50 | 0.33 | 0.33 | 0.40 | no |
| qwen/qwen3.8-2.4t-a95b | no | 0.000 | 0 | 0 | 0/0 | - | - | - | - |
| qwen/qwen3.8-27b | yes | 0.229 | 487 | 71 | 0/0 | 0.00 | 0.00 | 0.00 | yes |
| minimax/minimax-m3 | yes | 0.053 | 84 | 65 | 1/1 | 0.50 | 0.30 | 0.00 | no |
| xiaomi/mimo-v2.6-pro | no | 0.054 | 673 | 0 | 0/0 | - | - | - | - |

Errors:
- deepseek/deepseek-v4.1-flash: MatnInventory: output hit max_tokens before finishing
- z-ai/glm-5.3: IcmaAnalysis: output hit max_tokens before finishing
- qwen/qwen3.8-2.4t-a95b: ChainMatnSet: output does not match the schema: 1 validation error for ChainMatnSet
  Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='```json\n[\n  {\n    "ch...نَفْيُ سَنَة', input_type=str]
    For further information visit https://errors.pydantic.dev/2.14/v/json_invalid
- xiaomi/mimo-v2.6-pro: MatnInventory: output hit max_tokens before finishing
