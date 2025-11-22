from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # MongoDB
    mongodb_url: str = ""
    mongodb_db_name: str = "screenshot_sherlock"
    
    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.electronhub.ai"
    openai_model: str = "gpt-4o-2024-11-20"
    
    # Anthropic (Optional)
    anthropic_api_key: str = ""
    
    # JWT Auth
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    
    # CORS - can be JSON array string or comma-separated string
    allowed_origins: List[str] = ["chrome-extension://*"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60
    
    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # If empty string, return default
            if not v or v.strip() == "":
                return ["chrome-extension://*"]
            # Try to parse as JSON first
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            # Otherwise, split by comma
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["chrome-extension://*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

