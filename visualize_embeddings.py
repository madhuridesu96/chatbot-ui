import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# --- Load embeddings and chunk metadata ---
embeddings = np.load("embeddings.npy")

chunks = []
with open("knowledge_base.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

sections = [chunk["section"] for chunk in chunks]

# --- Reduce to 2D with PCA ---
pca = PCA(n_components=2)
reduced = pca.fit_transform(embeddings)

# --- Color-code by section ---
unique_sections = sorted(set(sections))
colors = plt.cm.tab10.colors  # a set of distinct colors
section_to_color = {sec: colors[i % len(colors)] for i, sec in enumerate(unique_sections)}

plt.figure(figsize=(8, 6))
for sec in unique_sections:
    idx = [i for i, s in enumerate(sections) if s == sec]
    plt.scatter(reduced[idx, 0], reduced[idx, 1], label=sec, color=section_to_color[sec], s=80)

plt.legend(title="Section")
plt.title("2D PCA Visualization of Knowledge Base Embeddings")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.savefig("embeddings_2d.png")
print("✅ embeddings_2d.png saved")