import json
import numpy as np
import chromadb

# --- Step 1: Load inputs from prior days ---
chunks = []
with open("knowledge_base.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

embeddings = np.load("embeddings.npy")

print(f"Loaded {len(chunks)} chunks and {embeddings.shape[0]} embeddings")

# --- Step 2: Connect to the SAME persistent Chroma collection from Day 8 ---
client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="coverage_kb")

# --- Prepare the 4 required lists ---
ids = [chunk["id"] for chunk in chunks]
documents = [chunk["text"] for chunk in chunks]
metadatas = [
    {
        "source_file": chunk["source_file"],
        "source_type": chunk["source_type"],
        "plan_type": chunk["plan_type"] if chunk["plan_type"] else "none",
        "section": chunk["section"],
        "ingested_at": chunk["ingested_at"],
    }
    for chunk in chunks
]
embeddings_list = embeddings.tolist()

# --- Batch upsert, ~100 records per call ---
batch_size = 100
for i in range(0, len(ids), batch_size):
    collection.add(
        ids=ids[i:i+batch_size],
        embeddings=embeddings_list[i:i+batch_size],
        documents=documents[i:i+batch_size],
        metadatas=metadatas[i:i+batch_size],
    )

print(f"✅ Upserted {len(ids)} records into 'coverage_kb'")

# --- Step 3: Verify count matches ---
count = collection.count()
print(f"✅ collection.count() = {count}")
assert count == len(chunks), "Mismatch between chunk count and collection count!"
print("✅ Count matches chunk total")