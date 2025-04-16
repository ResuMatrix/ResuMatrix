from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, Depends, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
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
        return JSONResponse(content={"job": jsonable_encoder(job)})
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


@router.get("/{job_id}/resumes", status_code=200)
async def get_all_resumes_with_job_id(
        job_id: str,
        db_service:DatabaseService = Depends(get_db_service)):
    try:
        resumes = await db_service.get_resumes_with_job_id(job_id)
        jd = await db_service.get_job(job_id)
        if resumes is None or jd is None:
            LOG.error(f"No resumes found with job_id: {job_id}")
            raise HTTPException(status_code=404, detail=f"No resumes found with job_id: {job_id}")
        else:
            return JSONResponse(content={"job_text": jd.job_text, "resumes" : jsonable_encoder(resumes)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{job_id}/resumes/{resume_id}", status_code=200)
async def get_resume_with_id(
        resume_id: str,
        db_service:DatabaseService = Depends(get_db_service)):
    try:
        resume = await db_service.get_resume(resume_id)
        if resume is None:
            LOG.error(f"No resume found with resume_id: {resume_id}")
            raise HTTPException(status_code=404, detail=f"No resume found with resume_id: {resume_id}")
        else:
            return JSONResponse(content={"resume" : jsonable_encoder(resume)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{job_id}", status_code=200)
async def get_job_with_id(
        job_id: str,
        db_service:DatabaseService = Depends(get_db_service)):
    try:
        jd = await db_service.get_job(job_id)
        if jd is None:
            LOG.error(f"No job found with job_id: {job_id}")
            raise HTTPException(status_code=404, detail=f"No job found with job_id: {job_id}")
        else:
            return JSONResponse(content={"job": jsonable_encoder(jd)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/", status_code=200)
async def get_all_jobs_by_user_id(
        user_id: str | None = None,
        db_service: DatabaseService = Depends(get_db_service)):
    try:
        if user_id is not None:
            jobs = await db_service.get_jobs_by_user_id(user_id)
        else:
            jobs  = await db_service.get_all_jobs()
        
        if jobs is None:
            error_msg = f"No jobs found with user_id: {user_id}" if user_id else "No jobs found"
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            return JSONResponse(content={"jobs": jsonable_encoder(jobs)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

