from typing import List
import uuid
from datetime import datetime
from pydantic import BaseModel


class Job(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    job_text: str
    status: int

class JobList(BaseModel):
    job_list: List[Job]

class Resume(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    created_at: datetime
    resume_text: str
    status: int
    fit_probability: float

class ResumeList(BaseModel):
    resume_list: List[Resume]
