from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import vertexai

from typing import Optional 
class VertexAIManager:
    """Manages interactions with Google's Vertex AI services."""
    
    def __init__(self, project_id: Optional[str] = None, 
                 location: str = "us-central1"):

        """
        Initialize the Vertex AI manager. 
        Ensure gcloud auth is setup with all the necessary env 
        variables such as GOOGLE_CLOUD_PROJECT, credentials json
        """
        self.aiplatform = aiplatform.init()
        logger.info(f"Initialized Vertex AI with project: {self.project_id}")
    

    def get_embedding_model(self, model_name: str = "text-embedding-005") -> TextEmbeddingModel:
        """
        Get a reference to a text embedding model.
        
        Args:
            model_name: The name of the embedding model to use
        
        Returns:
            A reference to the embedding model
        """
        return TextEmbeddingModel.from_pretrained(model_name)

