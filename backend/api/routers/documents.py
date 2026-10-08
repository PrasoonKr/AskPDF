from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import os
from pathlib import Path
from typing import List

from backend.api.dependencies import get_application, get_current_user
from backend.api.schemas.document import UploadResponse, DocumentsResponse
from backend.database.session import SessionLocal
from backend.database import repository
from backend.services.s3_service import S3Service

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

@router.get("", response_model=DocumentsResponse)
async def list_documents(current_user=Depends(get_current_user)):
    user_email = (current_user.get("email") or current_user.get("sub", "default")) if current_user else "default"
    
    with SessionLocal() as db:
        user = repository.get_or_create_user(db, user_email)
        docs = repository.get_user_documents(db, user.id)
        doc_filenames = [doc.filename for doc in docs]
        
    return DocumentsResponse(documents=doc_filenames)

@router.post("", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    application=Depends(get_application),
    current_user=Depends(get_current_user),
):
    user_email = (current_user.get("email") or current_user.get("sub", "default")) if current_user else "default"
    documents_dir = Path(f"backend/documents/{user_email}")
    documents_dir.mkdir(parents=True, exist_ok=True)
    
    total_chunks = 0
    s3_service = S3Service()
    
    with SessionLocal() as db:
        user = repository.get_or_create_user(db, user_email)
        
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF document.")
            
            # Idempotency check: if document already exists, delete old records, chunks, and FAISS
            existing_doc = repository.get_user_documents(db, user.id)
            if any(d.filename == file.filename for d in existing_doc):
                # Clean up Postgres
                repository.delete_document_record(db, user.id, file.filename)
                repository.delete_document_chunks(db, user.id, file.filename)
                # Clean up FAISS
                application.ingestion_service.document_store.remove_document(file.filename)
            
            # 1. Save temporarily
            file_path = documents_dir / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                if not content:
                    raise HTTPException(status_code=400, detail=f"File {file.filename} is empty.")
                f.write(content)
                
            # 2. Ingest into FAISS & DB chunks
            result = application.ingestion_service.ingest(str(file_path))
            total_chunks += result.chunks
            
            # 3. Upload to S3
            s3_key = f"documents/{user.id}/{file.filename}"
            s3_service.upload_file(str(file_path), s3_key)
            
            # 4. Save metadata to Postgres
            repository.create_document_record(db, user.id, file.filename, chunk_count=result.chunks)
            
            # 5. Clean up local PDF
            file_path.unlink()
        
    # Save the knowledge base so FAISS index persists
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
    s3_service = S3Service()
    
    with SessionLocal() as db:
        user = repository.get_or_create_user(db, user_email)
        docs = repository.get_user_documents(db, user.id)
        for doc in docs:
            # Delete from S3
            s3_key = f"documents/{user.id}/{doc.filename}"
            s3_service.delete_file(s3_key)
            
            # Delete Postgres document records and chunks
            repository.delete_document_record(db, user.id, doc.filename)
            repository.delete_document_chunks(db, user.id, doc.filename)
            
    # Clear FAISS index
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
    s3_service = S3Service()
    
    with SessionLocal() as db:
        user = repository.get_or_create_user(db, user_email)
        
        # Delete from S3
        s3_key = f"documents/{user.id}/{filename}"
        s3_service.delete_file(s3_key)
        
        # Delete Postgres document records
        repository.delete_document_record(db, user.id, filename)
        
    # Remove from FAISS (and implicitly chunks table via DocumentStore)
    application.ingestion_service.document_store.remove_document(filename)
    application.ingestion_service.document_store.save()
    
    if application.ingestion_service.keyword_search:
        application.ingestion_service.keyword_search.build_index()
        
    return {"message": f"Document {filename} removed."}