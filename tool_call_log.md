# Tool Call Log — Day 13

6 test questions run through the tool-calling pipeline: 5 questions each triggering a tool (covering all 4 available tools, with `check_coverage` tested twice on different procedures), plus 1 control question that should trigger no tool.

---

## Test 1: What's the deductible on plan PLN-003?

- **Tool called:** `get_plan_details`
- **Arguments:** `{"plan_id": "PLN-003"}`
- **Tool result:** `{"plan_id": "PLN-003", "plan_name": "Silver Select PPO", "monthly_premium": 379.0, "annual_deductible": 4000, "network_type": "PPO"}`
- **Final answer:** "The deductible on plan PLN-003 is $4,000 per year."
- **Correct tool selection?** Yes

---

## Test 2: Is physical therapy covered under plan PLN-005?

- **Tool called:** `check_coverage`
- **Arguments:** `{"plan_id": "PLN-005", "procedure": "Physical Therapy"}`
- **Tool result:** `{"plan_id": "PLN-005", "procedure": "Physical Therapy", "covered": true, "notes": "Based on plan coverage flags for PLN-005."}`
- **Final answer:** "Yes."
- **Correct tool selection?** Yes

---

## Test 3: What's the status of claim C-2003?

- **Tool called:** `get_claim_status`
- **Arguments:** `{"claim_id": "C-2003"}`
- **Tool result:** `{"claim_id": "C-2003", "member_id": "M-1032", "status": "Denied", "procedure_description": "Physical Therapy Session", "claim_amount": 117.9}`
- **Final answer:** "The claim C-2003 is denied."
- **Correct tool selection?** Yes

---

## Test 4: How much would I pay out of pocket for physical therapy under plan PLN-005?

- **Tool called:** `estimate_out_of_pocket_cost`
- **Arguments:** `{"plan_id": "PLN-005", "procedure": "Physical Therapy"}`
- **Tool result:** `{"plan_id": "PLN-005", "procedure": "Physical Therapy", "estimated_member_cost": 950.0, "basis": "Estimated as 25% coinsurance applied to deductible (mock estimate)"}`
- **Final answer:** "Based on the provided plan details for PLN-005, you would pay out of pocket approximately $950.00 for physical therapy. This is an estimated amount based on a 25% coinsurance applied to the deductible."
- **Correct tool selection?** Yes

---

## Test 5: Is dental coverage included under plan PLN-009?

- **Tool called:** `check_coverage`
- **Arguments:** `{"plan_id": "PLN-009", "procedure": "Dental Coverage"}`
- **Tool result:** `{"plan_id": "PLN-009", "procedure": "Dental Coverage", "covered": true, "notes": "Based on plan coverage flags for PLN-009."}`
- **Final answer:** "Yes."
- **Correct tool selection?** Yes

---

## Test 6 (Control — should trigger NO tool): What medication should I take for a headache?

- **Tool called:** None
- **Arguments:** None
- **Tool result:** None
- **Final answer:** "I'm not able to provide medical advice — a licensed healthcare provider is the right person to help with that."
- **Correct behavior?** Yes — correctly avoided calling any tool, directly refused as a medical advice question.

---

## Debugging Story: A Real Fabrication Issue Found and Fixed

### Initial run — the problem

On the first run of this exact test set, tool selection was correct for 5 of 6 questions, but several **final answers contained fabricated details that did not exist anywhere in the actual tool results**:

- Test 2 originally returned: *"...pages 12 through 15 of the plan's brochure. According to section 1.2.3, physical therapy services are subject to a copayment of $25 for each visit. The total number of covered visits per year is capped at 20..."* — none of this exists in the `CoverageResult` model, which only contains a boolean `covered` field and a generic note.
- Test 5 originally returned invented percentages and dollar caps ("80% of dental procedure costs... $1,500 per year... $3,000 annually") with the same issue — the actual tool result only contains a simple yes/no.
- Test 6 originally incorrectly called `check_coverage` with a nonsensical procedure ("Ibuprofen prescription") instead of correctly recognizing this as a no-tool medical advice question.

### Root cause

The system prompt did not explicitly forbid adding details beyond what the tool's validated result actually contained, and did not explicitly instruct the model to avoid calling tools for medication/medical questions.

### Fix

Two additions were made to `SYSTEM_PROMPT`:
1. An explicit instruction: "When a tool returns data, use ONLY the exact fields and values in that tool's result. NEVER add specific numbers, percentages, page references, copay amounts, visit limits, or any other detail that is not explicitly present in the tool's returned data."
2. An explicit instruction naming all 4 tools directly and stating they must never be called for medication, symptom, diagnosis, or treatment questions.

### Result after fix

All 6 tests (documented above) now produce answers containing ONLY information that is directly traceable to the actual Pydantic-validated tool result fields, with no fabricated specifics. Test 6 correctly triggers no tool call at all.

### Key takeaway

Pydantic validation confirms the STRUCTURE and TYPE of tool results is correct, but does not prevent the language model from inventing additional plausible-sounding details when generating its final natural-language answer. Grounding instructions in the system prompt must explicitly and specifically forbid adding unsupported specifics — a general "use only the context" instruction (as used in Day 11/12) was not sufficient on its own once tool calling was introduced; an explicit anti-fabrication clause was required.