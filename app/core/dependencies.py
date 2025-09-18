"""
Dependências da aplicação para injeção no FastAPI.
"""
import logging
from functools import lru_cache
from typing import Generator

from app.core.settings import settings
from app.infrastructure.database import DatabaseManager
from app.infrastructure.gemini_client import GeminiClient
from app.infrastructure.mock_gemini_client import MockGeminiClient
from app.infrastructure.http_downloader import HttpDownloader
from app.infrastructure.process_repository import SqlAlchemyProcessRepository
from app.application.services import LlmService, ProcessService
from app.application.use_cases import CreateProcessUseCase, GetProcessUseCase, CreateProcessFromUploadUseCase

logger = logging.getLogger(__name__)


@lru_cache()
def get_database_manager() -> DatabaseManager:
    """Retorna instância singleton do gerenciador de banco."""
    logger.info("Inicializando gerenciador de banco de dados")
    db_manager = DatabaseManager(settings.database_url)
    db_manager.create_tables()
    return db_manager


@lru_cache()
def get_gemini_client() -> GeminiClient:
    """Retorna instância singleton do cliente Gemini."""
    # Usar mock se API key não estiver configurada ou for de teste
    if settings.gemini_api_key in ["test_key", "your_gemini_api_key_here"]:
        logger.info("Usando MockGeminiClient para desenvolvimento/teste")
        return MockGeminiClient(api_key=settings.gemini_api_key)
    else:
        logger.info("Inicializando cliente Gemini real")
        return GeminiClient(settings.gemini_api_key)


@lru_cache()
def get_http_downloader() -> HttpDownloader:
    """Retorna instância singleton do downloader HTTP."""
    return HttpDownloader(timeout=settings.download_timeout)


@lru_cache()
def get_process_repository() -> SqlAlchemyProcessRepository:
    """Retorna instância singleton do repositório de processos."""
    db_manager = get_database_manager()
    return SqlAlchemyProcessRepository(db_manager)


@lru_cache()
def get_llm_service() -> LlmService:
    """Retorna instância singleton do serviço de LLM."""
    gemini_client = get_gemini_client()
    return LlmService(gemini_client)


@lru_cache()
def get_process_service() -> ProcessService:
    """Retorna instância singleton do serviço de processos."""
    return ProcessService()


@lru_cache()
def get_create_process_use_case() -> CreateProcessUseCase:
    """Retorna instância singleton do use case de criação de processo."""
    return CreateProcessUseCase(
        repository=get_process_repository(),
        llm_service=get_llm_service(),
        process_service=get_process_service(),
        downloader=get_http_downloader(),
        tmp_dir=settings.tmp_dir
    )


@lru_cache()
def get_get_process_use_case() -> GetProcessUseCase:
    """Retorna instância singleton do use case de consulta de processo."""
    return GetProcessUseCase(
        repository=get_process_repository()
    )


@lru_cache()
def get_create_process_from_upload_use_case() -> CreateProcessFromUploadUseCase:
    """Retorna instância singleton do use case de upload de processo."""
    return CreateProcessFromUploadUseCase(
        llm_service=get_llm_service(),
        process_service=get_process_service(),
        repository=get_process_repository()
    )
