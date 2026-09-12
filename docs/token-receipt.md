# Token and model receipt

The successful live Blender construction run used GPT-6 Astra, medium reasoning, across **9 model requests in one user turn**. It reused the initial procedural script produced during the earlier attempts. The successful session ran 2026-09-11 05:48:49.788–05:52:01.055 UTC, about 3 minutes 11 seconds; this excludes all prior setup.

| Scope | Requests | Uncached input | Cached input | Output | Reasoning, included in output |
|---|---:|---:|---:|---:|---:|
| First headless attempt | 9 | 60,203 | 489,856 | 5,297 | 816 |
| Second headless attempt | 8 | 71,579 | 444,032 | 1,926 | 248 |
| MCP permission failure | 4 | 58,943 | 188,800 | 643 | 22 |
| Successful live MCP construction | 9 | 63,929 | 438,656 | 4,214 | 423 |
| All four Astra attempts | 30 | 254,654 | 1,561,344 | 12,080 | 1,509 |

The successful run totals **68,143 uncached-input plus output tokens**, or **506,799 including cached input**. All four attempts total **266,734 uncached-input plus output**, or **1,828,078 including cached input**. Cache writes are reported as zero by these Codex records. This is token accounting, not measured dollars, credits or account quota.

Not all work was Astra. A Claude Sonnet 5 session supervised photo sourcing, tool setup, execution and inspection. A deliberately broad 2026-09-11 00:09–05:53 UTC window contains 93 unique assistant message IDs: 185 ordinary input tokens, 790,076 cache-write input tokens, 27,351,980 cache-read input tokens, and 78,800 output tokens. That timebox includes research and troubleshooting and is **not a clean Flatiron-only attribution**. It excludes later ornament trials and showcase delivery. Do not add it to the Astra construction number and label the result a precise project cost.

Separate open-source research used local Qwen3-Coder 30B. The current showcase/publication effort is outside the original construction figures.

Method: sum each distinct Codex `token_usage_record.payload.response_id` once; compare with final cumulative `token_count` totals. Attribute the model and reasoning effort from each run's context. For Claude, deduplicate assistant records by message ID, retaining maximum reported values for each usage field to avoid counting streaming records repeatedly. Reasoning is already included in output. Local private logs are not redistributed.
