import re
import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="coverage_kb")

# ---------- STEP 1: Classifier ----------

STRUCTURED_KEYWORDS = [
    "deductible", "premium", "copay", "coinsurance", "claim status",
    "status of claim", "out-of-pocket", "network tier", "monthly cost",
    "how much", "pending claims", "claim id",
]
UNSTRUCTURED_KEYWORDS = [
    "covered", "coverage", "cover ", "exclusion", "excluded", "procedure",
    "maternity", "physical therapy", "mental health", "appeal", "policy",
    "benefit", "process", "eligib", "dental",
]

def classify(question):
    q = question.lower()
    has_structured = (
        any(kw in q for kw in STRUCTURED_KEYWORDS)
        or bool(re.search(r"\bc-?\d{3,}\b", q))
        or bool(re.search(r"\bm-?\d{3,}\b", q))
    )
    has_unstructured = any(kw in q for kw in UNSTRUCTURED_KEYWORDS)

    if has_structured and has_unstructured:
        return "both"
    elif has_structured:
        return "structured"
    elif has_unstructured:
        return "unstructured"
    else:
        return "unstructured"

# ---------- STEP 2: sql_lookup ----------

def sql_lookup(question):
    q = question.lower()
    conn = sqlite3.connect("coverage.db")
    cursor = conn.cursor()
    results = []

    claim_match = re.search(r"\bC-?\d{3,}\b", question, re.IGNORECASE)
    if claim_match:
        claim_id = claim_match.group(0).upper().replace("C", "C-").replace("C--", "C-")
        cursor.execute(
            "SELECT claim_id, member_id, plan_id, procedure_description, claim_amount, status FROM claims WHERE claim_id = ?",
            (claim_id,)
        )
        rows = cursor.fetchall()
        for r in rows:
            results.append(f"Claim {r[0]} (member {r[1]}, plan {r[2]}): {r[3]}, ${r[4]}, status: {r[5]}")

    member_match = re.search(r"\bM-?\d{3,}\b", question, re.IGNORECASE)
    if member_match and "pending" in q:
        member_id = member_match.group(0).upper().replace("M", "M-").replace("M--", "M-")
        cursor.execute(
            "SELECT COUNT(*) FROM claims WHERE member_id = ? AND status = 'Pending'",
            (member_id,)
        )
        count = cursor.fetchone()[0]
        results.append(f"Member {member_id} has {count} pending claim(s).")

    cursor.execute("SELECT plan_name FROM plans")
    all_plan_names = [row[0] for row in cursor.fetchall()]
    for plan_name in all_plan_names:
        if plan_name.lower() in q:
            cursor.execute(
                """SELECT plan_name, monthly_premium, annual_deductible, copay_primary_care,
                   copay_specialist, coinsurance_pct, network_type FROM plans WHERE plan_name = ?""",
                (plan_name,)
            )
            row = cursor.fetchone()
            if row:
                results.append(
                    f"{row[0]}: ${row[1]}/month premium, ${row[2]} deductible, "
                    f"${row[3]} primary care copay, ${row[4]} specialist copay, "
                    f"{row[5]}% coinsurance, network: {row[6]}"
                )

    conn.close()
    return results if results else ["No matching structured data found."]

# ---------- STEP 3: vector_lookup ----------

def vector_lookup(question, n_results=5):
    query_embedding = model.encode(question).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    return list(zip(results["documents"][0], results["metadatas"][0]))

# ---------- STEP 4: retrieve (the router) ----------

def retrieve(question):
    classification = classify(question)
    context = []

    if classification in ("structured", "both"):
        sql_results = sql_lookup(question)
        context.extend([f"[SQL] {r}" for r in sql_results])

    if classification in ("unstructured", "both"):
        vector_results = vector_lookup(question)
        for doc, meta in vector_results:
            entry = f"[VECTOR - {meta.get('plan_type', 'none')}/{meta.get('section', '?')}] {doc[:150]}"
            if entry not in context:
                context.append(entry)

    return {
        "question": question,
        "classification": classification,
        "context": context,
    }

if __name__ == "__main__":
    test = retrieve("What's the deductible on the Gold Complete PPO plan?")
    print(test)