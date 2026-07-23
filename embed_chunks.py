import json
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text):
    """Return a numeric vector for the input string."""
    return model.encode(text)

# --- Load all chunks from knowledge_base.jsonl ---
chunks = []
with open("knowledge_base.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

# --- Generate an embedding for each chunk ---
all_embeddings = []
for chunk in chunks:
    vector = embed(chunk["text"])
    all_embeddings.append(vector)
    chunk["embedding"] = vector.tolist()

# --- Save as embeddings.npy (required for verification) ---
embeddings_array = np.array(all_embeddings)
np.save("embeddings.npy", embeddings_array)

print(f"✅ Embedded {len(chunks)} chunks")
print(f"✅ embeddings.npy saved with shape: {embeddings_array.shape}")