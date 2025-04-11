from typing import List
from fastapi import APIRouter, HTTPException, Response, UploadFile, Depends, Body
from fastapi.responses import JSONResponse
import pymupdf
from app.services.database import DatabaseService
from app.services.storage import StorageService
from app.api.deps import get_db_service, get_storage_service
import logging
import io

LOG = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/", status_code=201)
async def create_job(data: dict = Body(...),
                     db_service: DatabaseService = Depends(get_db_service)
                     ):
    try:
        job = await db_service.create_job(data["job_text"], data["user_id"])
        LOG.info(f"Job created with id: {job.id}")
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create a job item: {str(e)}")


@router.post("/{job_id}/resumes", status_code=201)
async def upload_resume_files(
        job_id:str, 
        files: List[UploadFile], 
        db_service: DatabaseService = Depends(get_db_service),
        storage_service: StorageService = Depends(get_storage_service)):
    LOG.info(f"files: {[file.filename for file in files]}")
    LOG.info(f"sizes: {[file.size for file in files]}")
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    try:
        resume_text_list = []
        for file in files:
            contents = await file.read()
            pdf_stream = io.BytesIO(contents)
            text = ""
            with pymupdf.open(stream=pdf_stream, filetype="pdf") as pdf_doc:
                for page_num in range(len(pdf_doc)):
                    text += pdf_doc[page_num].get_text("text")
            resume_text_list.append(text)

        _ = await db_service.create_resumes(job_id, resume_text_list)
        
        public_urls = await storage_service.upload_resumes(job_id, files) 
        return JSONResponse(content={"public_urls": public_urls}, status_code=201)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")



