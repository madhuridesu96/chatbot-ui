import json
import sqlite3
from datetime import datetime, timezone
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

chunks = []
chunk_counter = 0

def make_id():
    global chunk_counter
    chunk_counter += 1
    return f"chunk-{chunk_counter:04d}"

now = datetime.now(timezone.utc).isoformat()

# --- 1. Unstructured: raw_text files, chunked ---
file_sections = {
    "raw_text/benefits.txt": "coverage",
    "raw_text/claims_process.txt": "claims",
    "raw_text/enrollment.txt": "enrollment",
}

for filepath, section in file_sections.items():
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    text_chunks = splitter.split_text(text)

    for chunk_text in text_chunks:
        chunks.append({
            "id": make_id(),
            "text": chunk_text,
            "source_file": filepath,
            "source_type": "unstructured",
            "plan_type": None,
            "section": section,
            "ingested_at": now,
        })

# --- 2. Structured: plans from coverage.db, one chunk per plan (new richer schema) ---
conn = sqlite3.connect("coverage.db")
cursor = conn.cursor()
cursor.execute("""
    SELECT plan_name, tier, network_type, monthly_premium, annual_deductible,
           out_of_pocket_max, copay_primary_care, copay_specialist, coinsurance_pct,
           covers_maternity, covers_mental_health, covers_physical_therapy, covers_dental
    FROM plans
""")
rows = cursor.fetchall()
conn.close()

for (plan_name, tier, network_type, premium, deductible, oop_max,
     copay_pcp, copay_spec, coinsurance, maternity, mental_health, pt, dental) in rows:
    plan_text = (
        f"{plan_name} ({tier} tier, {network_type}): ${premium}/month premium, "
        f"${deductible} deductible, ${oop_max} out-of-pocket max, "
        f"${copay_pcp} primary care copay, ${copay_spec} specialist copay, "
        f"{coinsurance}% coinsurance. Covers maternity: {maternity}. "
        f"Covers mental health: {mental_health}. Covers physical therapy: {pt}. "
        f"Covers dental: {dental}."
    )
    chunks.append({
        "id": make_id(),
        "text": plan_text,
        "source_file": "coverage.db",
        "source_type": "structured",
        "plan_type": plan_name,
        "section": "coverage",
        "ingested_at": now,
    })

# --- 3. Write to knowledge_base.jsonl ---
with open("knowledge_base.jsonl", "w", encoding="utf-8") as f:
    for chunk in chunks:
        f.write(json.dumps(chunk) + "\n")

print(f"✅ Wrote {len(chunks)} chunks to knowledge_base.jsonl")