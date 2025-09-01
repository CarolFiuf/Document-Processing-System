# app/config.py - Configuration with environment variables
from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    
    # Database Configuration
    database_url: str = "postgresql://postgres:password@localhost:5432/docprocessing"
    
    # Redis Cache Configuration
    redis_url: str = "redis://localhost:6379"
    redis_expire_seconds: int = 3600
    
    # File Storage Configuration
    upload_path: str = "./data/uploads"
    processed_path: str = "./data/processed"
    max_file_size: int = 100_000_000
    
    # OCR Configuration
    ocr_languages: List[str] = ["en", "vi"]
    ocr_gpu: bool = False
    
    # LLM Configuration
    llm_api_base: str = "http://localhost:8001/v1"
    llm_model_name: str = "microsoft/DialoGPT-medium"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.1
    
    # Vector Database Configuration
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Monitoring Configuration
    prometheus_port: int = 9090
    grafana_port: int = 3000
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "./data/logs/app.log"
    
    # Security Configuration
    secret_key: str = "your-secret-key-change-in-production"
    
    # Development Configuration
    debug: bool = False
    testing: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()