from pydantic import BaseModel
from pydantic.typing import Optional, Field, List

from datetime import datetime

# Pydantic models
class Location(BaseModel):
    """Represents a physical location."""
    address: Optional[str] = None
    postal_code: Optional[str] = Field(None, alias='postalCode')
    city: Optional[str] = None # Added based on common resume structures
    country_code: Optional[str] = Field(None, alias='countryCode')

class WorkExperience(BaseModel):
    """Represents a single job position."""
    company_name: str = Field(..., alias='companyName')
    position: str
    start_date: datetime = Field(None, alias='startDate') 

    end_date: Optional[datetime] = Field(None, alias='endDate')
    summary: Optional[List[str]] = None # What the applicant has worked on

class VolunteerWork(BaseModel):
    """Represents a single volunteer position."""
    organization_name: str = Field(..., alias='organizationName')
    position: str
    start_date: datetime = Field(None, alias='startDate') 
    end_date: Optional[datetime] = Field(None, alias='endDate')
    summary: Optional[str] = None

class Education(BaseModel):
    """Represents a single educational institution entry."""

    institution_name: str = Field(..., alias='institutionName')

    area_of_study: str = Field(..., alias='areaOfStudy')
    degree_type: str = Field(..., alias='degreeType') # e.g., Bachelor, Master
    start_date: datetime = Field(..., alias='startDate')
    end_date: Optional[datetime] = Field(None, alias='endDate') # None if currently studying
    score_gpa: Optional[str] = Field(None, alias='scoreGpa') # Using str to accommodate various formats (4.0, Pass, etc.)
    courses_taken: Optional[List[str]] = Field(None, alias='coursesTaken')


class Award(BaseModel):
    """Represents a single award received."""
    title: str
    date_received: Optional[datetime] = Field(..., alias='dateReceived')
    awarder: str # Organization/person who gave the award
    summary: Optional[str] = None


class Certificate(BaseModel):
    """Represents a single certification."""
    certificate_name: str = Field(..., alias='certificateName')
    date_issued: datetime = Field(..., alias='dateIssued')

    issuer: str # Organization that issued the certificate

    certificate_url: Optional[str] = Field(None, alias='certificateUrl')

class Publication(BaseModel):
    """Represents a single publication."""

    publication_name: str = Field(..., alias='publicationName')

    publisher_name: Optional[str] = Field(None, alias='publisherName')
    release_date: Optional[datetime] = Field(None, alias='releaseDate')
    publication_url: Optional[str] = Field(None, alias='publicationUrl')
    summary: Optional[str] = None

class Language(BaseModel):
    """Represents proficiency in a language."""
    language: str
    fluency: Optional[str] = None # e.g., "Native speaker", "Fluent", "Conversational"


class Project(BaseModel):
    """Represents a personal or professional project."""
    project_name: str = Field(..., alias='projectName')
    start_date: Optional[datetime] = Field(None, alias='startDate') 
    end_date: Optional[datetime] = Field(None, alias='endDate')
    highlights: Optional[List[str]] = None # Added for common bullet points
    project_url: Optional[str] = Field(None, alias='projectUrl')
    keywords: Optional[List[str]] = None # Added for technologies used, etc.

# --- Main Resume Model ---

class BasicInformation(BaseModel):
    """Basic contact and personal information."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[Location] = None
    twitter: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    

class Resume(BaseModel):
    """Pydantic model representing a resume."""

    basics: BasicInformation
    workexp: Optional[List[WorkExperience]] = None
    volunteer: Optional[List[VolunteerWork]] = None
    education: Optional[List[Education]] = None

    awards: Optional[List[Award]] = None

    certificates: Optional[List[Certificate]] = None
    publications: Optional[List[Publication]] = None

    skills: Optional[List[str]] = None # Simple list of skill names for this example
    languages: Optional[List[Language]] = None
    references: Optional[List[str]] = None # Added common section (often "Available upon request")
    projects: Optional[List[Project]] = None


    class Config:
        str_strip_whitespace = True
        validate_by_name = True # Allows using snake_case or camelCase
