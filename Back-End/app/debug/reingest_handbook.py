"""
Re-ingestion script for employee_handbook.pdf using the fixed chunker.
Run: .venv\Scripts\python.exe -m app.debug.reingest_handbook

This:
1. Deletes the old 6 bad chunks from Qdrant
2. Re-parses the file using the new fallback splitter
3. Re-indexes the properly chunked documents
"""
import os
import sys

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.vector_store import vector_store
from app.ingestion.parsing import parsing_service
from app.config.settings import settings

FILE_NAME = "employee_handbook.pdf"
COLLECTION = "general"

# Step 1: Find the file
file_path = os.path.join(settings.RAW_DATA_PATH, FILE_NAME)
if not os.path.exists(file_path):
    print(f"ERROR: File not found at {file_path}")
    print(f"Please ensure the file is in the RAW_DATA_PATH: {settings.RAW_DATA_PATH}")
    sys.exit(1)

print(f"Found file: {file_path}")

# Step 2: Delete old chunks
print(f"\nStep 1: Deleting old chunks for '{FILE_NAME}'...")
vector_store.delete_by_filename(FILE_NAME)
print("Old chunks deleted.")

# Step 3: Re-parse with new chunker (fallback will trigger automatically)
print(f"\nStep 2: Re-parsing '{FILE_NAME}' with fallback chunker...")
documents = parsing_service.process_file(file_path, COLLECTION)
print(f"Parsed into {len(documents)} chunks.")

# Step 4: Re-index
print(f"\nStep 3: Indexing {len(documents)} chunks into Qdrant...")
vector_store.add_documents(documents)
print("Done! Re-indexing complete.")

# Step 5: Verify
print(f"\nStep 4: Verification - scanning for 'sick':")
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
results, _ = client.scroll("finbot_knowledge", limit=200, with_payload=True, with_vectors=False)
sick_chunks = [p for p in results if "sick" in (p.payload or {}).get("page_content", "").lower()
               and (p.payload or {}).get("metadata", {}).get("source_document") == FILE_NAME]
print(f"Found {len(sick_chunks)} chunks containing 'sick' in {FILE_NAME}")
if sick_chunks:
    snippet = sick_chunks[0].payload.get("page_content", "")[:300]
    print(f"Sample: {snippet}")
