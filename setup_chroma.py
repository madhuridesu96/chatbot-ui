import chromadb

# Create a PERSISTENT client - data survives even after the script ends
client = chromadb.PersistentClient(path="./chroma_data")

# Create the collection (a "collection" is like a table, specifically for vectors)
collection = client.create_collection(name="coverage_kb")

print("✅ Collection created:", collection.name)

# --- Confirm it exists ---
all_collections = client.list_collections()
print("✅ All collections:", [c.name for c in all_collections])

fetched = client.get_collection(name="coverage_kb")
print("✅ Confirmed retrievable by name:", fetched.name)