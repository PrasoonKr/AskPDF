from fastapi import APIRouter, Depends, UploadFile, File
import os
from pathlib import Path

from typing import List

from backend.api.dependencies import get_application, get_current_user
from backend.api.schemas.document import UploadResponse, DocumentsResponse

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

@router.get("", response_model=DocumentsResponse)
async def list_documents(current_user=Depends(get_current_user)):
    user_email = (current_user.get("email") or current_user.get("sub", "default")) if current_user else "default"
    documents_dir = Path(f"backend/documents/{user_email}")
    docs = []
    if documents_dir.exists():
        for item in documents_dir.glob("*.pdf"):
            docs.append(item.name)
    return DocumentsResponse(documents=docs)

@router.post("", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    application=Depends(get_application),
    current_user=Depends(get_current_user),
):
    # Save the files to backend/documents/
    user_email = (current_user.get("email") or current_user.get("sub", "default")) if current_user else "default"
    documents_dir = Path(f"backend/documents/{user_email}")
    documents_dir.mkdir(parents=True, exist_ok=True)
    
    total_chunks = 0
    
    for file in files:
        file_path = documents_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        # Ingest it
        result = application.ingestion_service.ingest(str(file_path))
        total_chunks += result.chunks
    
    # Save the knowledge base so it persists
    application.ingestion_service.document_store.save()
    
    return UploadResponse(
        documents=len(files),
        chunks=total_chunks
    )

@router.delete("")
async def clear_documents(
    application=Depends(get_application),
    current_user=Depends(get_current_user)
):
    user_email = (current_user.get("email") or current_user.get("sub", "default")) if current_user else "default"
    documents_dir = Path(f"backend/documents/{user_email}")
    if documents_dir.exists():
        for item in documents_dir.glob("*.pdf"):
            item.unlink()
            
    application.ingestion_service.document_store.clear()
    application.ingestion_service.document_store.save()
    
    if application.ingestion_service.keyword_search:
        application.ingestion_service.keyword_search.build_index()
        
    return {"message": "Knowledge base cleared."}

@router.delete("/{filename}")
async def delete_document(
    filename: str,
    application=Depends(get_application),
    current_user=Depends(get_current_user)
):
    user_email = (current_user.get("email") or current_user.get("sub", "default")) if current_user else "default"
    documents_dir = Path(f"backend/documents/{user_email}")
    file_path = documents_dir / filename
    
    if file_path.exists():
        file_path.unlink()
        
    application.ingestion_service.document_store.remove_document(filename)
    application.ingestion_service.document_store.save()
    
    if application.ingestion_service.keyword_search:
        application.ingestion_service.keyword_search.build_index()
        
    return {"message": f"Document {filename} removed."}