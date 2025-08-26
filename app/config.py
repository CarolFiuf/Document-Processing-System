# app/config.py - Add new settings
from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Existing settings...
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    
    # Database - Updated to PostgreSQL
    database_url: str = "postgresql://postgres:password@localhost:5432/docprocessing"
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379"
    redis_expire_seconds: int = 3600  # 1 hour
    
    # File Storage
    upload_path: str = "./data/uploads"
    processed_path: str = "./data/processed"
    max_file_size: int = 100_000_000  # 100MB
    
    # OCR Settings
    ocr_languages: List[str] = ["en", "vi"]
    ocr_gpu: bool = False
    
    # LLM Settings (NEW!)
    llm_api_base: str = "http://localhost:8001/v1"  # vLLM OpenAI API
    llm_model_name: str = "microsoft/DialoGPT-medium"  # Will upgrade to better model
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.1
    
    # Vector Database (NEW!)
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Monitoring (NEW!)
    prometheus_port: int = 9090
    grafana_port: int = 3000
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./data/logs/app.log"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()