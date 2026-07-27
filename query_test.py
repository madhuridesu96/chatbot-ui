import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="coverage_kb")

# --- Step 4: Raw test query (no filtering) ---
test_question = "Is physical therapy covered under the Silver plan?"
query_embedding = model.encode(test_question).tolist()

print("=== RAW QUERY (no filter) ===")
raw_results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
)
for i, (doc, meta) in enumerate(zip(raw_results["documents"][0], raw_results["metadatas"][0])):
    print(f"\n--- Result {i+1} | plan_type: {meta['plan_type']} | section: {meta['section']} ---")
    print(doc[:200])

# --- Step 6: Filtered query (only Silver plan) ---
print("\n\n=== FILTERED QUERY (plan_type = Silver Value HMO) ===")
filtered_results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"plan_type": "Silver Value HMO"},
)
for i, (doc, meta) in enumerate(zip(filtered_results["documents"][0], filtered_results["metadatas"][0])):
    print(f"\n--- Result {i+1} | plan_type: {meta['plan_type']} | section: {meta['section']} ---")
    print(doc[:200])