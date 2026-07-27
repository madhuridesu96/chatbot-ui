# Structured Queries — Coverage Chatbot Data (Updated Dataset)

Five SQL queries written and tested against the updated coverage.db (18 plans, 250 claims, 120 members), mapped to realistic member questions.

## 1. What's the deductible on the Gold PPO plan?

SELECT plan_name, annual_deductible FROM plans WHERE plan_name = 'Gold Complete PPO';

Output:
[('Gold Complete PPO', 1500)]

## 2. How many claims are pending for member M1001?

SELECT COUNT(*) FROM claims
WHERE member_id = 'M-1001' AND status = 'Pending';

Output:
[(0,)]

Note: Member M-1001 (Wyatt Garcia) is a real, enrolled member with no claims currently on file. This is a valid, honest result — the query correctly returns zero rather than erroring, confirming it handles members with no claim history correctly.

## 3. Which plans have a monthly premium under $400?

SELECT plan_name, monthly_premium FROM plans WHERE monthly_premium < 400;

Output:
[('Bronze Basic PPO', 289.0), ('Bronze Saver HMO', 245.0), ('Silver Select PPO', 379.0), ('Silver Value HMO', 349.0), ('Silver Plus EPO', 399.0), ('Bronze Basic HMO Jr', 199.0), ('Silver Balance PPO', 365.0), ('Bronze Flex EPO', 275.0)]

## 4. JOIN — Claims joined with plan details

SELECT claims.claim_id, claims.member_id, claims.procedure_description,
       claims.claim_amount, plans.plan_name
FROM claims
JOIN plans ON claims.plan_id = plans.plan_id
LIMIT 5;

Output:
[('C-2001', 'M-1057', 'Mental Health Counseling Session', 121.98, 'Silver Plus EPO'),
 ('C-2002', 'M-1052', 'Blood Panel Lab Work', 63.7, 'Platinum Premier PPO'),
 ('C-2003', 'M-1032', 'Physical Therapy Session', 117.9, 'Bronze Flex EPO'),
 ('C-2004', 'M-1049', 'Blood Panel Lab Work', 105.43, 'Gold Advantage HMO'),
 ('C-2005', 'M-1008', 'Dermatology Consultation', 226.81, 'Silver Select PPO')]

## 5. Top-N — Most claimed procedures by total amount

SELECT procedure_description, SUM(claim_amount) as total_amount
FROM claims
GROUP BY procedure_description
ORDER BY total_amount DESC
LIMIT 3;

Output:
[('Outpatient Surgery - Minor', 39032.08), ('Emergency Room Visit', 25105.85), ('MRI Scan - Knee', 24077.87)]

## Note on Schema Update

This dataset was upgraded from an original 3-plan/5-claim synthetic set to a richer 18-plan/250-claim/120-member dataset, adding a members table to properly link claims to real enrolled individuals. Query 1 references "Gold Complete PPO," an actual Gold-tier plan in the new dataset, in place of the original generic "Gold PPO" example. Query 2's member ID format was updated to match the new dataset's dash-included format (M-1001 instead of M1001).
## Day 6 Sanity Check (Updated Dataset — 55 chunks)

- Total chunk count: 55 (confirmed via `wc -l knowledge_base.jsonl`)
- Random 5-chunk sample (chunk-0002, chunk-0022, chunk-0053, chunk-0011, chunk-0042): all 5 read as complete, coherent passages with no mid-sentence truncation
- Targeted exclusion-clause check (all 4 plans, not just a sample):
  - Plan 1 exclusions (chunk-0009): Fully intact
  - Plan 2 exclusions (chunk-0015): Cut off mid-list, continues into next chunk
  - Plan 3 exclusions (chunk-0022): Fully intact
  - Plan 4 exclusions (chunk-0028): Cut off mid-list, continues into next chunk

**Finding:** 2 of 4 exclusion lists were split across chunk boundaries at the fixed 500-character limit, since comma-separated lists lack the strong paragraph/sentence breaks the recursive splitter prioritizes. A future improvement would be to detect "Excluded Services:" as an explicit section marker and avoid splitting within it regardless of character count.
## Day 7 Sanity Check — Updated Dataset (55 chunks)

- Claims section: fully clustered, tightly grouped and clearly separated from other sections ✅
- Enrollment section: distinct, isolated point (only 1 chunk in this category) ✅
- Coverage section: does NOT cluster tightly — widely spread across the plot ⚠️

**Finding:** The "coverage" section mixes two structurally different content types — unstructured narrative PDF text (31 chunks) and structured, formulaic plan-summary sentences (18 chunks). Despite sharing the same section label, their embeddings land in different regions of the semantic space, since sentence structure/style influences embeddings alongside topic. This suggests source_type (structured vs. unstructured) may be a stronger clustering predictor than section alone when a section contains mixed content types.

embeddings_2d.png saved and reflects this finding visually.