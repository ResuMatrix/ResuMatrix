from app.services.database import DatabaseService
from app.services.storage import StorageService
from app.core.config import settings

def get_db_service() -> DatabaseService:
    """
    Inject DatabaseService dependency with Supabase settings

    """

    return DatabaseService(settings.SUPABASE_URL, settings.SUPABASE_API_KEY)

def get_storage_service() -> StorageService:
    """
    Inject StorageService dependency with GCP settings
    """

    return StorageService(settings.GCP_BUCKET_NAME)

