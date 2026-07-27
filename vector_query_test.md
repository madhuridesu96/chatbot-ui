# Vector Query Test — Day 9

## Setup Confirmation

- Loaded 55 chunks from `knowledge_base.jsonl` and 55 embeddings from `embeddings.npy`
- Batch-upserted all 55 records into the `coverage_kb` Chroma collection (batch size: 100)
- Verified `collection.count()` = 55, matching the chunk total exactly

## Test Question

Is physical therapy covered under the Silver plan?

## Raw Query (n_results=5, no filtering)

| # | plan_type | section | Relevant? |
|---|---|---|---|
| 1 | Silver Plus EPO | coverage | Yes — directly relevant |
| 2 | none | coverage | Partially — general Plan 3 overview text (Silver Select PPO section) |
| 3 | Silver Senior EPO | coverage | Yes — directly relevant |
| 4 | Silver Select PPO | coverage | Yes — directly relevant |
| 5 | Silver Balance PPO | coverage | Yes — directly relevant |

### Review

- **Are they relevant?** Yes, mostly. 4 of 5 results are directly relevant Silver-tier plan summaries; the 5th is general overview text about a Silver plan.
- **Do they reflect Silver-plan-specific coverage (not another plan)?** Yes, completely. No Bronze or Gold plan content appeared anywhere in the results — a genuine improvement over the original test, which had a Bronze HMO chunk incorrectly appear for a Silver-specific question.
- **Retrieval misses noted:** None of the 5 results explicitly confirm or deny "physical therapy" coverage using that exact phrase. The actual answer exists in the structured data (`covers_physical_therapy: Yes` for Silver Select PPO, Silver Value HMO, and Silver Plus EPO), but wasn't the top-ranked semantic result. This suggests raw semantic search favors general plan-pricing similarity over the specific coverage-flag detail being asked about.

## Filtered Query (n_results=5, where={"plan_type": "Silver Value HMO"})

| # | plan_type | section |
|---|---|---|
| 1 | Silver Value HMO | coverage |

### Review

Only **1 result** was returned, not 5. This is correct and expected — the knowledge base contains exactly one chunk tagged `plan_type: "Silver Value HMO"`, so the filter correctly narrowed the search to only that single matching record.

## Conclusion

With richer, more varied data (18 plans, including 5 distinct Silver-tier plans instead of just 1), unfiltered semantic search performed noticeably better at staying within the correct plan tier — no Bronze or Gold content leaked into the results, unlike the original 3-plan dataset test. This suggests retrieval quality scales positively with data diversity. However, the physical-therapy-specific retrieval miss shows that semantic search alone is still not sufficient for coverage-flag-style yes/no questions — combining it with a structured SQL lookup against the plans table's coverage flags (`covers_maternity`, `covers_mental_health`, `covers_physical_therapy`, `covers_dental`) would produce more reliable answers. This is exactly the "both" classification scenario Day 10's retrieval engine is designed to handle.