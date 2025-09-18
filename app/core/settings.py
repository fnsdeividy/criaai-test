"""
Configurações da aplicação.
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação usando Pydantic Settings."""
    
    # LLM Configuration
    gemini_api_key: str = Field(default="test_key", env="GEMINI_API_KEY", description="Chave da API do Google Gemini")
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/process_extractions",
        env="DATABASE_URL",
        description="URL de conexão com o banco de dados PostgreSQL"
    )
    
    # Application Configuration
    tmp_dir: str = Field(
        default="/tmp",
        env="TMP_DIR",
        description="Diretório temporário para arquivos"
    )
    
    download_timeout: int = Field(
        default=30,
        env="DOWNLOAD_TIMEOUT",
        description="Timeout em segundos para download de arquivos"
    )
    
    # File Upload Configuration
    max_file_size_mb: int = Field(
        default=14,
        env="MAX_FILE_SIZE_MB",
        description="Tamanho máximo de arquivo em MB"
    )
    
    # Security Configuration
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS",
        description="Origens permitidas para CORS"
    )
    
    rate_limit_requests: int = Field(
        default=100,
        env="RATE_LIMIT_REQUESTS",
        description="Número máximo de requests por minuto"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # API Configuration
    api_title: str = Field(
        default="Process Extraction API",
        env="API_TITLE",
        description="Título da API"
    )
    
    api_description: str = Field(
        default="API para extração de dados estruturados de processos jurídicos usando IA",
        env="API_DESCRIPTION",
        description="Descrição da API"
    )
    
    api_version: str = Field(
        default="1.0.0",
        env="API_VERSION",
        description="Versão da API"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global das configurações
settings = Settings()
