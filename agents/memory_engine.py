from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid
import datetime

# Connect to memory database
client = QdrantClient(host="localhost", port=6333)
encoder = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION = "cerebro_memories"

def init_memory():
    """Create memory collection if it doesn't exist"""
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print("[CEREBRO MEMORY] Memory bank initialized ✅")
    else:
        print("[CEREBRO MEMORY] Memory bank loaded ✅")

def remember(content: str, category: str = "general"):
    """Store a memory"""
    vector = encoder.encode(content).tolist()
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload={
            "content": content,
            "category": category,
            "timestamp": datetime.datetime.now().isoformat()
        }
    )
    client.upsert(collection_name=COLLECTION, points=[point])
    print(f"[CEREBRO MEMORY] Remembered: {content[:60]}...")

def recall(query: str, limit: int = 3):
    """Search memory for relevant past experiences"""
    vector = encoder.encode(query).tolist()
    results = client.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=limit
    ).points
    memories = [r.payload["content"] for r in results]
    return memories

def recall_formatted(query: str, limit: int = 3):
    """Return memories as readable text"""
    memories = recall(query, limit)
    if not memories:
        return "No relevant memories found."
    formatted = "\n".join([f"- {m}" for m in memories])
    return f"Relevant memories:\n{formatted}"

if __name__ == "__main__":
    init_memory()

    # Test: store some memories
    remember("David prefers Python over Node.js for backends", "preference")
    remember("David is building CEREBRO Sentinel v0.1", "project")
    remember("David uses FastAPI for REST APIs", "preference")
    remember("David's machine has 16GB RAM and NVIDIA T500 GPU", "system")

    print("\n[CEREBRO MEMORY] Testing recall...\n")

    # Test: retrieve memories
    query = "What does David prefer for backend development?"
    print(f"Query: {query}")
    print(recall_formatted(query))
