"""
Lead Scoring Agent - Configuration Management
Centralized configuration using pydantic-settings
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Environment
    env: str = "development"
    debug: bool = True
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Lead Scoring Agent"
    api_version: str = "1.0.0"
    api_description: str = "Autonomous AI agent for lead conversion prediction"
    
    # Database Configuration
    database_path: str = "./data/lead_scoring.db"
    
    # Model Configuration
    model_version: str = "1.0"
    retraining_threshold: int = 50
    accuracy_improvement_threshold: float = 0.02
    target_auc: float = 0.75
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def database_dir(self) -> Path:
        """Get database directory path"""
        return Path(self.database_path).parent
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.database_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
