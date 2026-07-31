# Fine-Tune Prep Notes — Day 14

## Reviewing Day 10-13 Test Logs: 3 Recurring Issues

### Issue 1: Inconsistent tone and verbosity across responses
**Source:** Day 12's prompt variant testing (prompt_variants.md) showed the same underlying facts phrased very differently depending on prompt wording — sometimes clinical and cold ("This information is not available in the provided plan documentation"), sometimes overly padded ("I'd be happy to help you understand your coverage options...").

**Can fine-tuning fix this?** YES. Fine-tuning on many examples of the exact desired tone (warm but concise, consistent structure) trains the model to default to that style reliably, without needing to re-engineer the prompt every time.

### Issue 2: Inconsistent or missing disclaimer language
**Source:** Day 11-13 testing showed the "This is not medical advice" disclaimer appeared inconsistently — sometimes included, sometimes only appearing when a question was directly medical, sometimes phrased differently each time.

**Can fine-tuning fix this?** YES. Training on examples that consistently include the exact required disclaimer phrasing, in the same style every time, makes this a learned habit of the model rather than something dependent on prompt engineering alone.

### Issue 3: Fabricated details beyond validated tool/retrieval data
**Source:** Day 13's tool-calling tests showed the model inventing specific page numbers, copay percentages, and plan nicknames that did not exist anywhere in the actual Pydantic-validated tool results (documented in tool_call_log.md).

**Can fine-tuning fix this?** PARTIALLY, but this is fundamentally a retrieval/grounding problem, not a style problem. Fine-tuning can reinforce a habit of saying "I don't know" when data is incomplete, but the root cause — the model's general tendency to generate plausible-sounding specifics — is better addressed through explicit grounding instructions in the prompt (as done in Day 13) and by ensuring retrieval provides complete, correct data in the first place. Fine-tuning cannot fix a missing database column (e.g., Day 10's missing out_of_pocket_max field) or missing SQL logic (Day 10's numeric filter gap) — those are retrieval bugs that must be fixed in sql_lookup itself.

## Summary: What Fine-Tuning Can and Cannot Fix

| Problem | Fine-tuning fixes it? | Why |
|---|---|---|
| Inconsistent tone/verbosity | Yes | Style is learnable from consistent examples |
| Missing/inconsistent disclaimers | Yes | Format/habit is learnable from consistent examples |
| Fabricating details beyond data | Partially | Root cause is retrieval completeness + grounding, not style |
| Missing SQL logic (numeric filters) | No | This is a code/retrieval bug, not a style issue |
| Missing database columns | No | This is a data completeness issue |
| Outdated plan facts | No | Fine-tuning bakes in facts at training time; RAG stays current automatically |

## Conclusion

Fine-tuning is the right tool for enforcing consistent tone, terminology, and disclaimer usage — issues directly observed and documented in Days 11-13. It is NOT the right tool for fixing retrieval gaps or teaching new factual plan knowledge, which should remain the responsibility of the RAG and tool-calling systems built in Days 9-13.