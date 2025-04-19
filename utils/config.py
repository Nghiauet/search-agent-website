"""
Global configuration for the MCP Agent using Pydantic for validation.
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Search engine settings
    SEARCH_ENGINE_API_KEY: str = os.getenv("SEARCH_ENGINE_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    SEARCH_ENGINE_CSE_ID: str = os.getenv("SEARCH_ENGINE_CSE_ID", "") or os.getenv("GOOGLE_CSE_ID", "")
    
    # Server settings
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    # Model settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_GENAI_API_KEY: str = os.getenv("GOOGLE_GENAI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash-preview-04-17")
    
    # Search settings
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    CONNECTION_TIMEOUT: int = int(os.getenv("CONNECTION_TIMEOUT", "10"))
    CONTENT_TIMEOUT: int = int(os.getenv("CONTENT_TIMEOUT", "15"))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "5000"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def ensure_environment_variables(self):
        """Make sure required API keys are available in environment."""
        # Make Google API key available under both variable names
        if self.GOOGLE_GENAI_API_KEY:
            os.environ["GOOGLE_API_KEY"] = self.GOOGLE_GENAI_API_KEY
            if "GOOGLE_GENAI_API_KEY" not in os.environ:
                os.environ["GOOGLE_GENAI_API_KEY"] = self.GOOGLE_GENAI_API_KEY
        
        return True

# Create global settings instance
settings = Settings()

# Ensure environment variables are set
settings.ensure_environment_variables()
