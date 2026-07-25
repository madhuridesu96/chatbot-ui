# Vector Database Notes — Chroma vs. Pinecone

## Comparison Table

| Criteria | Chroma (local) | Pinecone (cloud) |
|---|---|---|
| **Deployment** | Runs locally on your own machine, embedded in your Python process | Fully managed cloud service, accessed via API |
| **Free-tier limits** | No limits — fully free, since it's just software running on your own hardware | Free tier: 1 serverless index, ~100K vectors (at 1536 dimensions), no credit card required |
| **Latency** | Very low — no network round-trip, queries happen in-process on local disk/memory | Higher — every query travels over the internet to Pinecone's servers and back |
| **Ease of setup** | `pip install chromadb`, a few lines of Python — no account, no signup | Requires account signup, dashboard configuration, and an API key before any code runs |
| **Data persistence** | Stored in a local SQLite-backed folder (`chroma_data/`) — survives restarts, but lives only on this machine | Stored in Pinecone's cloud infrastructure — accessible from anywhere, backed by their SLA |
| **Scalability** | Limited by local machine's RAM/disk — fine for prototyping, not built for massive scale | Built for production scale — auto-scaling serverless architecture |

## Access Control in a Real Enterprise Deployment

This is where the two options diverge the most. In a real healthcare deployment, member data needs per-member or per-plan access control — one member should never be able to retrieve another member's claims data through the chatbot.

- **Chroma (local):** Has no built-in access control system. Since it's just a Python library embedded in your own application, *your application code* would be entirely responsible for enforcing who can see what — for example, manually filtering results by `member_id` metadata after every query, or running completely separate collections per member/plan. This puts the full security burden on the application layer, which is risky if not implemented carefully and consistently everywhere.

- **Pinecone (cloud):** Offers **namespaces** — a built-in way to logically partition data within a single index (e.g., one namespace per member or per plan), so queries can be scoped to only search within an authorized namespace. Enterprise Pinecone plans also support more advanced access control features (like private endpoints and stricter network-level security) that a local, embedded Chroma instance simply cannot offer, since it isn't a networked service with its own security perimeter.

**Bottom line:** For a real enterprise healthcare deployment with strict per-member data isolation requirements, Pinecone's namespace and network-level controls provide a stronger, more built-in foundation than Chroma — though a well-designed Chroma-based application could still enforce access control manually at the application layer, with more engineering effort and more risk of mistakes.

## Decision: Which will we use going forward?

**We'll use Chroma for the remainder of this program.**

Chroma is the simplest choice for this stage of development — it requires zero signup, zero API keys, zero cost, and zero network dependency, letting us iterate quickly and locally while learning the fundamentals of vector search. Since this program's data is entirely synthetic and not real member data, Chroma's lack of built-in access control isn't a practical concern right now. If this project were ever moved toward a genuine production healthcare deployment handling real member data, migrating to a cloud-hosted option like Pinecone — specifically for its namespace-based access control and enterprise-grade security features — would be a reasonable and likely necessary next step.

## Note: Dimension Mismatch Observed

When creating the Pinecone index via their dashboard, I used their integrated embedding model option (`llama-text-embed-v2`), which automatically set the index dimension to 1024. This does not match the 384-dimension output of the local `all-MiniLM-L6-v2` model used for the Chroma collection and embeddings.npy. Since today's task only required an empty Pinecone index for comparison purposes, this wasn't corrected — but it would need to be resolved (either by recreating the index with a matching custom dimension, or generating separate Pinecone-specific embeddings) before any real vectors could be inserted into Pinecone in a later step.