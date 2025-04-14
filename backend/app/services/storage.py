import logging
from typing import List
from fastapi import UploadFile
from google.cloud import storage

logger = logging.getLogger(__name__)

BLOB_PREFIX = "resumes"

class StorageService:
    def __init__(self, bucket_name: str):
        self.client: storage.Client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        
    async def upload_resumes(self, job_id: str, files: List[UploadFile]):
        public_urls = []
        for file in files:
            await file.seek(0)
            contents = await file.read()
            blob = self.bucket.blob(f"{BLOB_PREFIX}/{job_id}/{file.filename}")
            blob.upload_from_string(contents, content_type="application/pdf")
            logger.info(f"File {file.filename} uploaded successfully, size: {len(contents)} bytes")
            public_urls.append(blob.public_url)
        return public_urls
