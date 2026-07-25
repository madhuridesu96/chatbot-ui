# Vector Query Test — Day 9

## Setup Confirmation

- Loaded 13 chunks from `knowledge_base.jsonl` and 13 embeddings from `embeddings.npy`
- Batch-upserted all 13 records into the `coverage_kb` Chroma collection (batch size: 100)
- Verified `collection.count()` = 13, matching the chunk total exactly

## Test Question
Is physical therapy covered under the Silver plan?
## Raw Query (n_results=5, no filtering)

| # | plan_type | section | Relevant? |
|---|---|---|---|
| 1 | none | coverage | Partially — general plan overview text |
| 2 | Silver HMO | coverage | Yes — directly relevant |
| 3 | none | coverage | Partially — general out-of-pocket text |
| 4 | Bronze HMO | coverage | **No — wrong plan** |
| 5 | none | claims | Weakly relevant — claims status text |

### Review

- **Are they relevant?** Mixed. The Silver HMO chunk itself is directly relevant. Two general (non-plan-specific) chunks are loosely related. One chunk (claims status) is only weakly related to a coverage question.
- **Do they reflect Silver-plan-specific coverage?** No — the raw, unfiltered query returned a **Bronze HMO** chunk (Result 4), which is a different plan than the one asked about. This happened because Bronze HMO's summary sentence is structurally very similar in wording/format to Silver HMO's ("$X/month premium, $Y deductible, Z% coinsurance..."), causing it to land close in embedding space despite being the wrong plan.
- **Retrieval misses noted:**
  1. Bronze HMO content leaking into a Silver-specific question — a genuine miss that could mislead a real user in production.
  2. None of the retrieved chunks actually mention "physical therapy" specifically, since the synthetic benefits document never included that detail — the match is based on general coverage/pricing language similarity, not a direct answer to the literal question asked.

## Filtered Query (n_results=5, where={"plan_type": "Silver HMO"})

| # | plan_type | section |
|---|---|---|
| 1 | Silver HMO | coverage |

### Review

Only **1 result** was returned, not 5. This is correct and expected — the knowledge base currently contains exactly one chunk tagged `plan_type: "Silver HMO"`, so the filter correctly narrowed the search to only that single matching record, rather than padding results with unrelated plans.

## Conclusion

This test demonstrates the practical value of metadata filtering in a RAG system. Without filtering, semantically similar-but-wrong-plan content (Bronze HMO) can surface alongside genuinely relevant results, risking a chatbot giving a member incorrect information about a different plan. Filtering by `plan_type` at query time guarantees results are scoped to the correct plan, even though it currently returns fewer total results due to the small size of this synthetic dataset.