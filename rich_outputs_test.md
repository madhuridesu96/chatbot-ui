# Rich Outputs Test — Day 19

Testing 3 required scenarios: policy citations, a claim-status card, and a coverage-summary card, all rendered live in the Streamlit UI.

## Test 1: Question that should show policy citations

Question: What is the claims appeal process?

Response: If a claim is denied, members have 180 days from the date of the denial notice to file a written appeal. Appeals should include...

Citations rendered:
Policy sources (5)
[1] chunk-0036
[2] chunk-0035
[3] chunk-0032
[4] chunk-0033
[5] chunk-0034

Confirmed correct? Yes. The answer streamed in correctly, and an expandable "Policy sources (5)" section appeared directly below it, listing 5 real chunk IDs from the actual knowledge base, matching the claims-process content. Citations persisted correctly across subsequent messages in the same conversation.

## Test 2: Question that should show a claim-status card

Question: What's the status of claim C-2003?

Response: The status of the claim C-2003 is "Denied".

Card rendered:
Claim C-2003
Status: Denied (red indicator)
Amount: $117.90

Confirmed correct? Yes. A bordered container with columns rendered directly below the text answer, showing real claim data sourced from the Day 13 get_claim_status() tool function, validated through the ClaimStatusCard Pydantic model. A second test with claim C-2001 also rendered correctly, showing "Pending" (yellow indicator) with its own amount ($121.98).

## Test 3: Question that should show a coverage-summary card

Question: Is physical therapy covered under plan PLN-005?

Response: Don't know and suggest the member contact support. The provided context doesn't mention "physical therapy" explicitly.

Card rendered:
Silver Plus EPO
Deductible: $3,800
Copay: $25
Covered: Yes (checkmark)

Confirmed correct? Yes. Despite the text answer honestly declining to confirm coverage from vector-search context, the structured card, sourced independently from the Day 13 check_coverage() tool function plus a direct database lookup, correctly rendered the plan's real deductible, copay, and coverage flag, validated through the CoverageSummaryCard Pydantic model.

Notable finding: This revealed a useful discrepancy: the text answer (grounded in vector search) said "don't know," while the card (grounded in the direct database coverage flag) correctly showed "Covered: Yes." The card result is actually the more precise answer here, since it queries the exact coverage flag directly rather than relying on the LLM to infer an answer from retrieved narrative text.

## Persistence Verification

Across all 3 tests conducted in sequence within the same conversation, all citations and cards from earlier questions remained visible and correctly rendered even after asking later questions, confirming that storing card and citation data inside st.session_state.messages (rather than only rendering for the current turn) works correctly across Streamlit's constant script reruns.

## Markdown Rendering Verification

Separately confirmed (via a dedicated test file) that st.chat_message correctly renders numbered lists with bold text, tables, and syntax-highlighted code blocks, all displaying as properly formatted visual elements rather than raw markdown syntax.

## Summary

| Test | Feature | Result |
|---|---|---|
| 1 | Policy citations | Rendered correctly, persisted across turns |
| 2 | Claim-status card | Rendered correctly for 2 different claims, persisted across turns |
| 3 | Coverage-summary card | Rendered correctly, revealed a useful discrepancy vs. the text answer |