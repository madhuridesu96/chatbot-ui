# Retrieval Test Results — Day 10

10 test questions run through the `retrieve()` function, logging classification, retrieved context, and a manual quality score (good / partial / poor).

---

## 1. What's my copay?

**Classification:** structured

**Retrieved context:** `[SQL] No matching structured data found.`

**Score:** Poor

**Notes:** No plan name mentioned in the question, so the template-based `sql_lookup` had nothing to match against. Reveals a real limitation — generic questions without an identified plan can't currently be answered.

---

## 2. Is maternity care covered on the Bronze Saver HMO plan?

**Classification:** unstructured

**Retrieved context:** Bronze Saver HMO's own plan chunk retrieved (relevant), plus two "coverage examples" scenarios (Peg's pregnancy, Joe's diabetes), Bronze Basic HMO Jr, and Silver Value HMO.

**Score:** Partial

**Notes:** Correctly surfaced the right plan, but didn't directly state a yes/no on maternity coverage; mixed in loosely related content from other plans.

---

## 3. What's the status of claim C-2003?

**Classification:** structured

**Retrieved context:** `[SQL] Claim C-2003 (member M-1032, plan PLN-016): Physical Therapy Session, $117.9, status: Denied`

**Score:** Good

**Notes:** Exact, precise, correct answer.

---

## 4. Is dental coverage included on the Platinum Premier PPO plan?

**Classification:** unstructured

**Retrieved context:** Platinum Premier PPO's own chunk retrieved, plus Platinum Complete PPO, Gold Complete PPO, Silver Select PPO, and a coverage-examples scenario.

**Score:** Partial

**Notes:** Correct plan surfaced, but the `covers_dental` value was truncated in the preview and not clearly visible in the answer.

---

## 5. How many claims are pending for member M-1004?

**Classification:** structured

**Retrieved context:** `[SQL] Member M-1004 has 0 pending claim(s).`

**Score:** Good

**Notes:** Exact, correct answer — correctly handles a member with zero pending claims.

---

## 6. What is excluded under the Silver Select PPO plan?

**Classification:** unstructured

**Retrieved context:** Silver Select PPO's own chunk, the plan comparison table, Silver Balance PPO, Gold Complete PPO, and Gold Family PPO.

**Score:** Partial

**Notes:** Correct plan surfaced, but the actual "Excluded Services" list for this plan wasn't among the top 5 results — a genuine retrieval miss.

---

## 7. Which plans have a monthly premium under $300?

**Classification:** structured

**Retrieved context:** `[SQL] No matching structured data found.`

**Score:** Poor

**Notes:** `sql_lookup` currently only handles plan-name, member-ID, and claim-ID lookups — it has no logic for open-ended numeric filter questions like "under $300," even though this exact query works fine when run directly via `queries.py`.

---

## 8. Is physical therapy covered, and what's the deductible on Gold Complete PPO? (Mixed question)

**Classification:** both

**Retrieved context:** `[SQL]` Gold Complete PPO's exact deductible ($1,500). `[VECTOR]` Gold Complete PPO's own chunk, plus Gold Senior PPO, Gold Family PPO, Platinum Complete PPO, and Bronze Basic PPO.

**Score:** Good

**Notes:** Strong demonstration of the "both" pathway — SQL gave the precise deductible number, vector search surfaced the correct plan's full coverage details alongside related plans for comparison.

---

## 9. What's the claims appeal process?

**Classification:** unstructured

**Retrieved context:** All 5 results are claims-process steps, in a sensible order (Step 6, Step 5, overview, Step 2, Step 4).

**Score:** Good

**Notes:** Highly relevant, precise results — the best-performing unstructured query in this test set.

---

## 10. What's the out-of-pocket max on Bronze Basic PPO?

**Classification:** structured

**Retrieved context:** `[SQL] Bronze Basic PPO: $289.0/month premium, $6500 deductible, $45 primary care copay, $90 specialist copay, 40% coinsurance, network: PPO`

**Score:** Partial

**Notes:** Correct plan identified, but `out_of_pocket_max` is not included in the SQL template's SELECT statement, so the specific value asked about is missing from the answer despite the plan being correctly found.

---

## Summary

| Score | Count | Questions |
|---|---|---|
| Good | 3 | Q3, Q8, Q9 |
| Partial | 4 | Q2, Q4, Q6, Q10 |
| Poor | 2 | Q1, Q7 |

**Key findings for Day 11 baseline:**
1. `sql_lookup` cannot handle open-ended numeric filter questions (e.g., "premium under $300") — it only matches by explicit plan name, member ID, or claim ID.
2. The SQL plan-lookup template doesn't include `out_of_pocket_max` in its output, even though it's a commonly asked-about field.
3. Vector search reliably finds the *correct plan's* chunk, but doesn't always surface the *most specific* relevant sentence within that plan's larger text block (e.g., exclusions, specific coverage flags) — a chunking/retrieval precision issue rather than a wrong-plan issue.
4. The "both" classification pathway (Q8) performed well, combining precise SQL facts with broader vector context effectively.