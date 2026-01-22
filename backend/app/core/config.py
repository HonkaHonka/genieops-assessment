from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # This must match the key name in your .env file
    DATABASE_URL: str 
    
    # LLM Settings (Optional so it doesn't crash)
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3"
    
    class Config:
        env_file = ".env"
        extra = "ignore" # This ignores extra variables in .env

# THIS LINE IS CRITICAL - it creates the 'settings' object other files are trying to import
settings = Settings()