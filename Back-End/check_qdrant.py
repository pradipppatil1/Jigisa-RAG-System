from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(url="http://localhost:6333")
collection_name = "finbot_knowledge"

# Check total points
count = client.count(collection_name=collection_name).count
print(f"Total points in {collection_name}: {count}")

# Scroll some points to see metadata
scroll_result = client.scroll(
    collection_name=collection_name,
    limit=5,
    with_payload=True
)

print("\nSample points metadata:")
for point in scroll_result[0]:
    print(point.payload)
