import secrets

from pydantic_settings import BaseSettings 


class Settings(BaseSettings):
    # model_config =SettingsConfigDict(
    #         # root of backend
    #         env_file="../.env",
    #         env_ignore_empty=True,
    #         extra="ignore"
    #         )
    API_V1_STR: str = "/api"
    SECRET_KEY:str = secrets.token_urlsafe(32)
    PROJECT_NAME: str = "ResuMatrix"
    
    HF_TOKEN: str
    GCP_BUCKET_NAME: str
    SUPABASE_URL: str
    SUPABASE_API_KEY: str
    
    # Gemini
    GOOGLE_API_KEY: str
    OPENAI_API_KEY: str
    class Config:
        env_file = ".env"


settings = Settings() 
