"""
Diagnostic: Check if sick leave data exists in any stored chunk.
Run: .venv\\Scripts\\python.exe -m app.debug.inspect_qdrant
"""
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
collection = "finbot_knowledge"

# Scroll all points and search Python-side for "sick"
print("=== Scanning ALL chunks for 'sick leave' text ===")
offset = None
found = []
while True:
    results, next_offset = client.scroll(
        collection_name=collection,
        offset=offset,
        limit=50,
        with_payload=True,
        with_vectors=False,
    )
    for point in results:
        payload = point.payload or {}
        content = payload.get("page_content", "")
        if "sick" in content.lower():
            meta = payload.get("metadata", {})
            found.append({
                "id": point.id,
                "source": meta.get("source_document", "?"),
                "page": meta.get("page_number", "?"),
                "collection": meta.get("collection", "?"),
                "access_roles": meta.get("access_roles", []),
                "content_snippet": content[:400],
                "total_length": len(content),
            })
    if next_offset is None:
        break
    offset = next_offset

print(f"\nFound {len(found)} chunks containing 'sick':\n")
for i, f in enumerate(found):
    print(f"--- Chunk {i+1} ---")
    print(f"Source:       {f['source']} (Page {f['page']})")
    print(f"Collection:   {f['collection']}")
    print(f"access_roles: {f['access_roles']}")
    print(f"Total length: {f['total_length']} chars")
    print(f"Snippet:      {f['content_snippet']}")
    print()
