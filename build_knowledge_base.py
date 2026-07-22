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

# --- 2. Structured: plans from coverage.db, one chunk per plan ---
conn = sqlite3.connect("coverage.db")
cursor = conn.cursor()
cursor.execute("SELECT plan_name, monthly_premium, annual_deductible, copay_pct, coverage_type, network_tier FROM plans")
rows = cursor.fetchall()
conn.close()

for plan_name, premium, deductible, copay_pct, coverage_type, network_tier in rows:
    plan_text = (
        f"{plan_name}: ${premium}/month premium, ${deductible} deductible, "
        f"{copay_pct}% coinsurance, network: {network_tier} ({coverage_type})"
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