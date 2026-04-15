from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.ingestion.schemas import UploadResponse, DeleteResponse, IngestionStatusResponse
from app.ingestion.parsing import parsing_service
from app.core.vector_store import vector_store
from app.config.settings import settings
import shutil
import os

router = APIRouter(prefix="/ingesta", tags=["ingesta"])

# Simple in-memory status tracker
ingestion_status = {}

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(...),
    access_roles: str = Form(None)
):
    if collection not in ["general", "finance", "engineering", "marketing", "hr"]:
        raise HTTPException(status_code=400, detail="Invalid collection name.")

    explicit_roles_list = []
    if access_roles:
        explicit_roles_list = [r.strip() for r in access_roles.split(",") if r.strip()]

    os.makedirs(settings.RAW_DATA_PATH, exist_ok=True)
    file_path = os.path.join(settings.RAW_DATA_PATH, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        ingestion_status[file.filename] = {
            "status": "Processing",
            "collection": collection,
            "processed_chunks": 0
        }
        
        documents = parsing_service.process_file(file_path, collection, explicit_roles=explicit_roles_list)
        vector_store.add_documents(documents)
        
        ingestion_status[file.filename].update({
            "status": "Indexed",
            "processed_chunks": len(documents)
        })
        
        return UploadResponse(
            filename=file.filename,
            collection=collection,
            message="Document successfully uploaded and indexed."
        )
    except Exception as e:
        ingestion_status[file.filename]["status"] = f"Failed: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.delete("/document/{filename}", response_model=DeleteResponse)
async def delete_document(filename: str):
    try:
        vector_store.delete_by_filename(filename)
        if filename in ingestion_status:
            del ingestion_status[filename]
            
        return DeleteResponse(
            filename=filename,
            message="Document successfully deleted from vector store."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@router.get("/status", response_model=list[IngestionStatusResponse])
async def get_ingestion_status():
    return [
        IngestionStatusResponse(filename=k, **v)
        for k, v in ingestion_status.items()
    ]

