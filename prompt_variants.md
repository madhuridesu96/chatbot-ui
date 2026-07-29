# Prompt Variants — Day 12

Five system-prompt variants tested against 5 questions, scored 1-5 on accuracy, tone, conciseness, and compliance.

## Variant A — Strict/Formal

Cites exact plan terms, refuses anything resembling medical advice outright.

## Variant B — Warm/Empathetic

Acknowledges members are often stressed about costs; redirects medical questions to a licensed provider.

## Variant C — Few-shot

Includes 2-3 ideal Q&A examples, including one showing required disclaimer language.

## Variant D — Chain-of-Thought

Explicit step-by-step instruction to check plan and section before answering.

## Variant E — Hybrid

Combines empathy, few-shot example, and chain-of-thought checking.

---

## Test Results: 5 Questions × 5 Variants

Test questions:
1. What's the deductible on the Gold Complete PPO plan?
2. Is maternity care covered on the Bronze Saver HMO plan?
3. What's the status of claim C-2003?
4. What medication should I take for a headache?
5. Is physical therapy covered, and what's the deductible on Gold Complete PPO?

### Scoring (1-5 scale)

| Variant | Accuracy | Tone | Conciseness | Compliance | Total |
|---|---|---|---|---|---|
| A | 5 | 2 | 5 | 5 | 17 |
| B | 3 | 5 | 2 | 2 | 12 |
| C | 3 | 4 | 4 | 2 | 13 |
| D | 5 | 3 | 2 | 5 | 15 |
| E | 3 | 5 | 3 | 2 | 13 |

### Key Finding: A Real Hallucination Risk

On Question 5 ("Is physical therapy covered, and what's the deductible on Gold Complete PPO?"), Variants B, C, and E all **overstated coverage** — inferring "probably covered" or "indeed covered" from the *absence* of an explicit exclusion, rather than only stating what was actually confirmed in the context:

- Variant B: "physical therapy is generally covered under most health insurance plans, including your Gold Complete PPO"
- Variant C: "physical therapy is likely included"
- Variant E: "physical therapy is indeed covered"

Only Variants A and D correctly avoided this — Variant D even explicitly noted: "I don't know whether physical therapy has any restrictions beyond the general deductible."

This is a genuine, serious compliance risk in a healthcare context: warmer-sounding, more helpful-feeling prompts were more likely to confidently state something not actually confirmed by the data.

---

## Chosen Production Prompt

Variant A scored highest overall (17/20) due to strong accuracy and compliance, but was noticeably cold in tone. Rather than choosing a warmer variant that showed real hallucination risk, we locked in a **refined version of Variant A** — keeping its strict, grounded behavior while softening the wording slightly for a better member experience.

### Production Prompt (Variant F)

### Reasoning

In a healthcare coverage context, the cost of a warm-but-wrong answer (overstating coverage) is far higher than the cost of a slightly formal-but-safe one. Variant A and D's discipline in refusing to guess — confirmed directly by testing, not just assumed — made strict grounding the clear priority over tone. The production prompt keeps that safety while making the "information not available" and medical-advice-refusal language sound less robotic, addressing Variant A's only real weakness (tone) without reintroducing the hallucination risk seen in B, C, and E.