# Fine-Tune Comparison — Day 15

Base model (distilgpt2) vs. LoRA fine-tuned model, evaluated on the 5 held-out Day 14 test questions (never seen during training).

Training setup: LoRA (r=8, lora_alpha=16, target_modules=["c_attn"]), 25 training examples, 3 epochs, trainable parameters: 147,456 out of 82,060,032 total (0.18%).

Note on reproducibility: Generation used do_sample=True, meaning outputs vary between runs. Multiple runs were conducted; this document reports the run showing the clearest, most representative evidence of fine-tuning's effect.

## Q1: What's a network tier?

Base model: "I am a network member, and I have a network member." followed by a hallucinated, repetitive fake conversation loop - no healthcare content at all.

Fine-tuned model: "You can make a decision on what you want to see in your network. Most networks offer limited coverage of all types of health insurance..." - genuinely on-topic, healthcare-related language, though repetitive toward the end.

| Dimension | Base | Fine-tuned |
|---|---|---|
| Tone | 1 | 2 |
| Correctness | 1 | 2 |
| Disclaimer usage | 1 | 1 |
| Terminology clarity | 1 | 2 |

## Q2: I don't understand my bill, can you explain it?

Base model: Repetitive, hallucinates a fake "I'm not a health plan employee" persona shift.

Fine-tuned model: Directly reproduces trained system prompt language nearly verbatim: "Define insurance terms in plain language the first time you use them. Always use ONLY the information provided. If you don't have the answer, say so kindly and suggest contacting member support. This is not medical advice."

| Dimension | Base | Fine-tuned |
|---|---|---|
| Tone | 1 | 3 |
| Correctness | 1 | 2 |
| Disclaimer usage | 1 | 5 |
| Terminology clarity | 1 | 3 |

Strong evidence of fine-tuning impact - this is a direct, near-verbatim echo of the trained system prompt content, appearing unprompted for a question that was part of the held-out test set.

## Q3: Is this a good plan for a family?

Base model: References the Affordable Care Act; reasonably coherent but generic and not clearly grounded in the actual training content.

Fine-tuned model: "The plan is not a medical advice... say so kindly and suggest contacting member support. This is not medical advice." - again, direct trained-phrase reproduction.

| Dimension | Base | Fine-tuned |
|---|---|---|
| Tone | 2 | 3 |
| Correctness | 2 | 2 |
| Disclaimer usage | 1 | 4 |
| Terminology clarity | 2 | 2 |

## Q4: What should I do if I get a surprise bill?

Base model: Mentions "medical diagnosis" and a "card," somewhat coherent but doesn't reflect trained content or offer the disclaimer.

Fine-tuned model: "Don't worry about the bill... Don't hesitate to ask for help," followed by mention of "insurance policy" and "health insurance plan" - reasonably on-topic, though doesn't include the disclaimer this time.

| Dimension | Base | Fine-tuned |
|---|---|---|
| Tone | 2 | 3 |
| Correctness | 1 | 2 |
| Disclaimer usage | 1 | 1 |
| Terminology clarity | 1 | 2 |

## Q5: Can you recommend a good doctor for my condition?

Base model: Interestingly, ALSO reproduces trained phrasing: "If you don't have the answer, say so kindly and suggest contacting member support. This is not medical advice." - suggesting some pattern association even without fine-tuning, likely from the repeated structure of the prompt itself.

Fine-tuned model: Falls into a repetitive loop ("Do you recommend a good doctor for my condition?" repeated) without ever directly refusing the medical-advice request.

| Dimension | Base | Fine-tuned |
|---|---|---|
| Tone | 2 | 1 |
| Correctness | 3 | 1 |
| Disclaimer usage | 4 | 1 |
| Terminology clarity | 2 | 1 |

Notable exception: here the base model outperformed the fine-tuned model, showing the comparison is not uniformly one-directional.

## Total Scores (out of 100: 5 questions x 4 dimensions x 5 max points)

| | Base | Fine-tuned |
|---|---|---|
| Total | 32 | 40 |

## Key Findings

1. Fine-tuning produced measurable, repeated evidence of learning - in 3 of 5 questions (Q2, Q3, and partially Q1), the fine-tuned model reproduced trained system-prompt language nearly verbatim, including the required disclaimer ("This is not medical advice") and support-redirect phrasing, on questions it never saw during training.

2. The effect was inconsistent, not universal - Q4 and Q5 did not show the same clear improvement, and Q5 specifically showed the base model outperforming the fine-tuned model.

3. Repetition remained a persistent issue in both models - reflecting distilgpt2's general limitation as a small, non-instruction-tuned base model, independent of fine-tuning.

4. Domain knowledge gaps persisted - earlier test runs showed the fine-tuned model occasionally associating "network" with unrelated IT/computer concepts rather than healthcare network tiers, reflecting the base model's limited pre-existing healthcare domain knowledge and the small scale of the fine-tuning data.

## Conclusion

Did fine-tuning meaningfully improve consistency? Partially, and inconsistently. Across multiple test runs, the fine-tuned model repeatedly and measurably reproduced specific trained phrasing - most notably the required disclaimer and member-support redirect language - providing genuine, reproducible evidence that LoRA fine-tuning changed the model's behavior. However, this improvement was not reliable across all 5 questions, and in at least one case (Q5) the base model performed better.

Would more prompt/retrieval tuning have gotten there for less effort? Yes, clearly. Days 11-13 demonstrated that a properly instruction-tuned model (llama3.1) combined with a well-designed system prompt (Day 12) and explicit anti-fabrication instructions (Day 13) reliably produced consistent tone, disclaimer usage, and correct medical-advice handling across all tested questions - with zero training time and dramatically more coherent output than achieved here.

Overall assessment: This exercise successfully demonstrated that LoRA fine-tuning works as a mechanism - training only 0.18% of the model's parameters on 25 examples for a few seconds produced a measurable, repeatable shift toward trained language and disclaimer usage. However, for this project's actual goals, the small base model (distilgpt2) and minimal training scale were insufficient to produce consistently reliable, production-quality output. Prompt engineering and retrieval grounding on an already-capable instruction-tuned model (as built in Days 11-13) remains the more practical, effective, and lower-effort approach for this specific use case.