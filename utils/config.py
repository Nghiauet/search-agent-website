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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure required API keys are available in environment
        if self.GOOGLE_GENAI_API_KEY:
            os.environ["GOOGLE_API_KEY"] = self.GOOGLE_GENAI_API_KEY
            if "GOOGLE_GENAI_API_KEY" not in os.environ:
                os.environ["GOOGLE_GENAI_API_KEY"] = self.GOOGLE_GENAI_API_KEY

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create global settings instance
settings = Settings()
