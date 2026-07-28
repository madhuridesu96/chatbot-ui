import json
from retrieval_engine import retrieve

test_questions = [
    "What's my copay?",
    "Is maternity care covered on the Bronze Saver HMO plan?",
    "What's the status of claim C-2003?",
    "Is dental coverage included on the Platinum Premier PPO plan?",
    "How many claims are pending for member M-1004?",
    "What is excluded under the Silver Select PPO plan?",
    "Which plans have a monthly premium under $300?",
    "Is physical therapy covered, and what's the deductible on Gold Complete PPO?",
    "What's the claims appeal process?",
    "What's the out-of-pocket max on Bronze Basic PPO?",
]

results = []
for q in test_questions:
    result = retrieve(q)
    results.append(result)
    print(f"\n{'='*60}")
    print(f"Q: {result['question']}")
    print(f"Classification: {result['classification']}")
    for c in result['context']:
        print(f"  {c[:150]}")

with open("test_harness_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\n\n✅ Ran {len(test_questions)} test questions, saved to test_harness_results.json")
