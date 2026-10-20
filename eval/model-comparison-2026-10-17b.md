| Model | Done | Cost (USD) | Time (s) | Warnings | Verbatim extractions | CL recall | CL precision | PCL recall | Convergence verdict right |
|---|---|---|---|---|---|---|---|---|---|
| deepseek/deepseek-v4-pro | yes | 0.078 | 1719 | 0 | 48/49 | 0.33 | 0.67 | 0.00 | no |
| deepseek/deepseek-v4-pro-0813 | yes | 0.847 | 4007 | 1 | 46/46 | 0.67 | 0.44 | 0.00 | no |
| deepseek/deepseek-v4.1-flash | yes | 0.247 | 1633 | 3 | 48/48 | 0.00 | 0.00 | 0.00 | yes |
| z-ai/glm-5.3 | no | 0.953 | 908 | 0 | 0/0 | - | - | - | - |
| moonshotai/kimi-k3 | yes | 2.346 | 1391 | 0 | 44/44 | 0.33 | 0.40 | 0.00 | no |
| qwen/qwen3.8-2.4t-a95b | no | 0.113 | 181 | 0 | 0/0 | - | - | - | - |
| qwen/qwen3.8-27b | no | 0.179 | 578 | 0 | 0/0 | - | - | - | - |
| minimax/minimax-m3 | no | 0.089 | 300 | 0 | 0/0 | - | - | - | - |
| xiaomi/mimo-v2.6-pro | yes | 0.184 | 4897 | 20 | 43/43 | 0.17 | 0.50 | 0.20 | yes |

Errors:
- z-ai/glm-5.3: OpenRouter HTTP 402: {"error":{"message":"This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.","code":402,"metadata":{"reason":"in_flight_budget_exhausted","limit_source":"openrouter_in_flight_budget","remedy_hint":"Retry after your in-flight requests settle (see the Retry-After header). Adding credits at ht
- qwen/qwen3.8-2.4t-a95b: ChainMatnSet: output does not match the schema: 1 validation error for ChainMatnSet
  Input should be an object [type=model_type, input_value=[{'chain_id': 113231, 're...ame_as_chain_id': None}], input_type=list]
    For further information visit https://errors.pydantic.dev/2.14/v/model_type
- qwen/qwen3.8-27b: MatnInventory: output does not match the schema: 1 validation error for MatnInventory
  Invalid JSON: EOF while parsing a value at line 1 column 0 [type=json_invalid, input_value='', input_type=str]
    For further information visit https://errors.pydantic.dev/2.14/v/json_invalid
- minimax/minimax-m3: IcmaAnalysis: output does not match the schema: 1 validation error for IcmaAnalysis
  Invalid JSON: EOF while parsing a string at line 1 column 2400 [type=json_invalid, input_value='{"convergence_point":{"n...mon link who framed and', input_type=str]
    For further information visit https://errors.pydantic.dev/2.14/v/json_invalid
