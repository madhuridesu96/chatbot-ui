# RAG Q&A Results — Day 11

Same 10 test questions from Day 10, now run through the full pipeline: retrieve → generate → answer.

---

## 1. What's my copay?

**Classification:** structured

**Final Answer:** "I don't know. The error message 'No matching structured data found' suggests that there may be a technical issue or data retrieval problem, which isn't related to your personal health insurance or copays. It might be best for you to contact the system's support in this case."

**Day 10 baseline:** Poor (raw output: `[SQL] No matching structured data found.`)

**Day 11 comparison:** Improved to a well-formed, honest sentence — correctly avoided guessing a number, though it slightly over-explains the internal SQL error rather than just saying it needs a specific plan name.

---

## 2. Is maternity care covered on the Bronze Saver HMO plan?

**Classification:** unstructured

**Final Answer:** "I don't know and suggest the member contact support to verify, as there is no information about maternity care coverage in the context provided for the Bronze Saver HMO plan."

**Day 10 baseline:** Partial (retrieved relevant chunks but didn't state yes/no clearly)

**Day 11 comparison:** Honest, well-formed — correctly refused to guess since the exact chunk with the exclusion wasn't in the top-5 context this run.

---

## 3. What's the status of claim C-2003?

**Classification:** structured

**Final Answer:** "The status of claim C-2003 is: Denied"

**Day 10 baseline:** Good (raw SQL output was already precise)

**Day 11 comparison:** Clean, natural sentence — same correct fact, better phrased.

---

## 4. Is dental coverage included on the Platinum Premier PPO plan?

**Classification:** unstructured

**Final Answer:** "I don't know. The provided context only lists the premium, deductible, out-of-pocket maximum, primary care copay, and specialist copay for the Platinum Premier PPO plan, but it does not mention dental coverage. It's best to contact support for more information."

**Day 10 baseline:** Partial (retrieved correct plan chunk, but dental flag was truncated)

**Day 11 comparison:** Improved — honestly explains what information IS and ISN'T available, rather than guessing.

---

## 5. How many claims are pending for member M-1004?

**Classification:** structured

**Final Answer:** "According to the context: There are 0 pending claims."

**Day 10 baseline:** Good

**Day 11 comparison:** Same correct fact, clean natural phrasing.

---

## 6. What is excluded under the Silver Select PPO plan?

**Classification:** unstructured

**Final Answer:** "I don't know and suggest the member contact support for specific information on exclusions."

**Day 10 baseline:** Partial (retrieved plan chunk, missed the actual exclusions list)

**Day 11 comparison:** Improved — honestly declines rather than fabricating an exclusions list.

---

## 7. Which plans have a monthly premium under $300?

**Classification:** structured

**Final Answer:** "I don't know. This message relates to an issue with structured data in SQL, it does not provide information about insurance plans or their premiums. It would be best for you to contact support."

**Day 10 baseline:** Poor (SQL found nothing — known limitation, no numeric filter support)

**Day 11 comparison:** Still Poor — same root cause carried through. The model correctly avoided guessing, but the underlying `sql_lookup` gap (no numeric filter handling) still needs fixing at the retrieval layer, not the generation layer.

---

## 8. Is physical therapy covered, and what's the deductible on Gold Complete PPO? (Mixed question)

**Classification:** both

**Final Answer:** "According to the context, physical therapy coverage is not mentioned, so I don't know about that. However, for your specific plan, Gold Complete PPO, the deductible is $1500."

**Day 10 baseline:** Good (SQL gave exact deductible, vector search gave relevant plan chunks)

**Day 11 comparison:** Excellent — the model correctly separated the two parts of the question, answering the SQL-backed part precisely while honestly declining the unconfirmed part.

---

## 9. What's the claims appeal process?

**Classification:** unstructured

**Final Answer:** "If a claim is denied, members have 180 days from the date of the denial notice to file a written appeal. Appeals should include..."

**Day 10 baseline:** Good (all 5 retrieved chunks were directly relevant claims-process steps)

**Day 11 comparison:** Excellent — clean, accurate paraphrase directly from the real policy text.

---

## 10. What's the out-of-pocket max on Bronze Basic PPO?

**Classification:** structured

**Final Answer:** "I don't know. The member may want to contact support for this information."

**Day 10 baseline:** Partial (plan found, but out_of_pocket_max missing from SQL SELECT statement)

**Day 11 comparison:** Improved — honestly declined rather than guessing, correctly reflecting the real data gap identified on Day 10.

---

## Summary: Day 10 vs. Day 11 Comparison

| # | Day 10 Score | Day 11 Score | Improved? |
|---|---|---|---|
| 1 | Poor | Good | ✅ |
| 2 | Partial | Good | ✅ |
| 3 | Good | Good | = |
| 4 | Partial | Good | ✅ |
| 5 | Good | Good | = |
| 6 | Partial | Good | ✅ |
| 7 | Poor | Poor | = (retrieval-layer limitation, not fixed by generation) |
| 8 | Good | Good | = |
| 9 | Good | Good | = |
| 10 | Partial | Good | ✅ |

**Key finding:** 5 of 10 questions improved from Day 10's raw retrieval baseline to Day 11's generated answers — largely because the LLM converts messy or incomplete raw context into clean, honest, well-formed sentences, correctly declining to answer rather than guessing when information is genuinely missing.

**Key remaining limitation:** Question 7 (numeric premium filter) still fails, because the underlying issue is in the *retrieval* layer (`sql_lookup` has no logic for open-ended numeric comparisons), not something the generation/grounding step can fix on its own. This confirms the grounding prompt is working correctly — it can only work with what retrieval actually finds.

**Grounding assessment:** Across all 10 answers, the model never fabricated a fact not present in the retrieved context. Every "I don't know" response correctly reflected a genuine gap in the retrieved data, rather than the model guessing — validating that the grounding prompt is functioning as intended for a health-coverage use case where overstating coverage would be genuinely harmful.