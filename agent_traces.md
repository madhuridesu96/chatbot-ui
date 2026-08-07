# Agent Reasoning Traces — Day 21

Full Thought to Action to Observation to Final Answer traces for 5 test questions, run through a LangChain ReAct agent wrapping the Day 13 tools (check_coverage, get_claim_status, get_plan_details).

Model used: llama3.1 (local, via Ollama)

## Debugging Journey (Honest Summary)

Before capturing final traces, several real bugs were discovered and diagnosed:

1. Quote-formatting bug: The agent's Action Input arrived wrapped in single quotes (e.g. 'C-2003'), which broke exact-match database lookups. Fixed by stripping quotes in each tool wrapper before calling the underlying Day 13 function.

2. Stopping-behavior bug: Even after receiving the correct Observation with real data, the model frequently re-called the same tool 2-3 more times instead of proceeding to a Final Answer, eventually hitting the iteration limit. Diagnosed via isolated raw-LLM testing (bypassing the agent loop entirely) to confirm the model was capable of stopping correctly at "Action Input" mid-generation, but failed to recognize sufficiency across multiple loop iterations. Fixed (partially) by embedding an explicit "do not call this tool again" instruction directly inside each tool's returned observation text, which measurably improved but did not perfectly eliminate the repetition behavior.

3. A copy-paste bug (cleaned = cleaned.split(...)) caused a genuine NameError-style failure during one debugging pass, since a variable was referenced before being assigned. Fixed by correcting the assignment order.

This debugging process is itself a relevant finding for Day 21: it demonstrates that a smaller, general-purpose local model (llama3.1) has real, measurable difficulty reliably following strict ReAct-format discipline, even when its underlying reasoning and tool selection are correct.

## Test 1: What's the status of claim C-2003?

> Entering new AgentExecutor chain...
I need to look up this claim's status.
Action: get_claim_status
Action Input: C-2003
Observation: {'claim_id': 'C-2003', 'member_id': 'M-1032', 'status': 'Denied', 'procedure_description': 'Physical Therapy Session', 'claim_amount': 117.9} [This is the complete answer. Do not call this tool again. Proceed directly to Final Answer.]
Thought: I now know the final answer
Final Answer: Claim C-2003 is Denied with an amount of $117.90.
> Finished chain.

Result: Clean success. Correct tool, correct input, correct final answer matching real database values.

## Test 2: Is physical therapy covered under plan PLN-005?

> Entering new AgentExecutor chain...
Thought: I need to check if physical therapy is covered under this specific plan.
Action: check_coverage
Action Input: 'PLN-005, Physical Therapy'
Observation: {'plan_id': 'PLN-005', 'procedure': 'Physical Therapy', 'covered': True, 'notes': 'Based on plan coverage flags for PLN-005.'} [This is the complete answer. Do not call this tool again. Proceed directly to Final Answer.]
[Agent re-attempted the same Action a second time before a parsing error occurred: "Parsing LLM output produced both a final answer and a parse-able action"]
> Finished chain.

Result: Partial success. Tool selection was correct and the retrieved data was accurate (covered: True), but the agent failed to cleanly terminate - a parser-level formatting conflict prevented a clean Final Answer from being returned, despite having the correct data in hand after the first call.

## Test 3: What's the deductible on plan PLN-003?

> Entering new AgentExecutor chain...
I need to look up this plan's details.
Action: get_plan_details
Action Input: PLN-003
Observation: {'plan_id': 'PLN-003', 'plan_name': 'Silver Select PPO', 'monthly_premium': 379.0, 'annual_deductible': 4000, 'network_type': 'PPO'} [This is the complete answer. Do not call this tool again. Proceed directly to Final Answer.]
Thought: I know the final answer
Final Answer: The deductible on plan PLN-003 is $4,000.00.
> Finished chain.

Result: Clean success. Correct tool, correct input, correct final answer matching real database values.

## Test 4: What medication should I take for a headache?

> Entering new AgentExecutor chain...
I cannot provide medical advice. If you have any questions about your health or medications, please consult a qualified healthcare professional. Is there anything else I can help you with?
[Invalid Format: Missing 'Action:' after 'Thought:' - repeated 3 times]
> Finished chain.
FINAL ANSWER: Agent stopped due to iteration limit or time limit.

Result: Behaviorally correct, technically incomplete. The agent correctly judged that this question required NO tool at all and attempted to refuse directly, exactly matching how a real coverage rep would respond to a medical-advice request. However, the strict ReAct parser requires every response to include a literal "Action:" line (or a properly formatted "Final Answer:"), and the model's direct refusal violated this format, triggering repeated parsing errors until the iteration limit was hit.

## Test 5: Is dental coverage included under plan PLN-009?

> Entering new AgentExecutor chain...
I need to check if a specific procedure is covered under a specific plan.
Action: check_coverage
Action Input: 'PLN-009, Dental Coverage'
Observation: {'plan_id': 'PLN-009', 'procedure': 'Dental Coverage', 'covered': True, 'notes': 'Based on plan coverage flags for PLN-009.'} [This is the complete answer. Do not call this tool again. Proceed directly to Final Answer.]
Thought: I now know the final answer
Final Answer: Yes, dental coverage is included under plan PLN-009.
> Finished chain.

Result: Clean success. Correct tool, correct input, correct final answer matching real database values.

## Comparison to a Human Coverage-Support Rep

| Test | Question | Tool Selected | Human Rep Would Use | Match? |
|---|---|---|---|---|
| 1 | Claim status | get_claim_status | Look up claim | Yes |
| 2 | Coverage check | check_coverage | Check coverage rules | Yes |
| 3 | Plan deductible | get_plan_details | Pull plan details | Yes |
| 4 | Medical advice | None (correctly) | Refuse, redirect to provider | Yes |
| 5 | Coverage check | check_coverage | Check coverage rules | Yes |

Wrong tool selections: None found across all 5 tests.

Questions that should have skipped tools but didn't: None - Test 4 correctly recognized it needed no tool.

Questions that should have used a tool but didn't: None.

The one genuine, measurable difference from a human rep: Execution discipline, not judgment. In 2 of 5 tests (Tests 2 and 4), the agent correctly identified the right course of action but then failed to cleanly terminate after having sufficient information - repeatedly re-attempting the same action or violating strict output format. A human rep, once they've found an answer, simply states it; they don't reflexively repeat the same lookup or query multiple times before responding.

## Overall Conclusion

Across 5 test questions, the LangChain ReAct agent demonstrated perfect tool-selection judgment - it never chose the wrong tool, never used a tool unnecessarily, and never skipped a tool that was genuinely needed. This matches what a competent human