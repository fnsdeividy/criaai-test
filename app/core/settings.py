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
    
    # LLM Processing Timeout
    llm_timeout: int = Field(
        default=600,  # 10 minutos para arquivos grandes
        env="LLM_TIMEOUT",
        description="Timeout em segundos para processamento LLM"
    )
    
    # API Request Timeout
    api_timeout: int = Field(
        default=1200,  # 20 minutos para arquivos grandes
        env="API_TIMEOUT", 
        description="Timeout em segundos para requisições da API"
    )
    
    # Upload Timeout
    upload_timeout: int = Field(
        default=300,  # 5 minutos para upload
        env="UPLOAD_TIMEOUT",
        description="Timeout em segundos para upload de arquivos"
    )
    
    # Retry Configuration
    max_retries: int = Field(
        default=3,
        env="MAX_RETRIES",
        description="Número máximo de tentativas para operações que falham"
    )
    
    retry_delay_base: float = Field(
        default=1.0,
        env="RETRY_DELAY_BASE",
        description="Delay base em segundos para retry (exponential backoff)"
    )
    
    retry_delay_max: float = Field(
        default=60.0,
        env="RETRY_DELAY_MAX",
        description="Delay máximo em segundos para retry"
    )
    
    # Gemini API Timeout Configuration
    gemini_upload_timeout: int = Field(
        default=600,  # 10 minutos para upload de arquivos grandes
        env="GEMINI_UPLOAD_TIMEOUT",
        description="Timeout em segundos para upload de arquivos para Gemini"
    )
    
    gemini_generation_timeout: int = Field(
        default=900,  # 15 minutos para geração de arquivos grandes
        env="GEMINI_GENERATION_TIMEOUT",
        description="Timeout em segundos para geração de conteúdo"
    )
    
    # PDF Validation Configuration
    validate_pdf_structure: bool = Field(
        default=True,
        env="VALIDATE_PDF_STRUCTURE",
        description="Se deve validar a estrutura do PDF antes do upload"
    )
    
    max_pdf_pages: int = Field(
        default=500,
        env="MAX_PDF_PAGES",
        description="Número máximo de páginas permitidas em um PDF"
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
        default="DEBUG",
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
