from qdrant_client import QdrantClient
from qdrant_client.http import models
import json

client = QdrantClient(url="http://localhost:6333")
collection_name = "finbot_knowledge"

# Scroll some points to see metadata
scroll_result = client.scroll(
    collection_name=collection_name,
    limit=5,
    with_payload=True
)

print("\nSample points metadata:")
for point in scroll_result[0]:
    # Print keys only to avoid long output
    print(f"ID: {point.id}")
    print(f"Keys: {list(point.payload.keys())}")
    if 'metadata' in point.payload:
        print(f"Metadata Keys: {list(point.payload['metadata'].keys())}")
        print(f"Metadata Content: {point.payload['metadata']}")
    else:
        print(f"Payload Content: {point.payload}")
    print("-" * 20)
