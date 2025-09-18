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
from app.domain.interfaces import IProcessRepository
from app.application.services import LlmService, ProcessService
from app.application.use_cases import CreateProcessUseCase, GetProcessUseCase, CreateProcessFromUploadUseCase

logger = logging.getLogger(__name__)


@lru_cache()
def get_database_manager() -> DatabaseManager:
    """Retorna instância singleton do gerenciador de banco."""
    logger.info("Inicializando gerenciador de banco de dados")
    logger.info(f"DATABASE_URL: {settings.database_url[:50]}...")
    try:
        db_manager = DatabaseManager(settings.database_url)
        logger.info("DatabaseManager criado com sucesso")
        db_manager.create_tables()
        logger.info("Tabelas criadas/verificadas com sucesso")
        # Testar conexão
        session = db_manager.get_session()
        session.close()
        logger.info("Conexão com banco testada com sucesso")
        return db_manager
    except Exception as e:
        logger.error(f"Falha ao inicializar banco de dados: {e}")
        logger.error(f"Tipo do erro: {type(e).__name__}")
        logger.error(f"DATABASE_URL: {settings.database_url}")
        logger.info("Continuando com MockDatabaseManager (sem persistência)")
        # Retorna um mock manager que não faz nada
        return MockDatabaseManager()


@lru_cache()
def get_gemini_client() -> GeminiClient:
    """Retorna instância singleton do cliente Gemini."""
    # Usar mock se API key não estiver configurada ou for de teste
    if settings.gemini_api_key in ["test_key", "your_gemini_api_key_here"]:
        logger.info("Usando MockGeminiClient para desenvolvimento/teste")
        return MockGeminiClient(api_key=settings.gemini_api_key)
    else:
        logger.info("Inicializando cliente Gemini real")
        return GeminiClient(
            api_key=settings.gemini_api_key,
            max_retries=settings.max_retries,
            retry_delay_base=settings.retry_delay_base,
            retry_delay_max=settings.retry_delay_max,
            upload_timeout=settings.gemini_upload_timeout,
            generation_timeout=settings.gemini_generation_timeout
        )


@lru_cache()
def get_http_downloader() -> HttpDownloader:
    """Retorna instância singleton do downloader HTTP."""
    return HttpDownloader(timeout=settings.download_timeout)


@lru_cache()
def get_process_repository() -> IProcessRepository:
    """Retorna instância singleton do repositório de processos."""
    db_manager = get_database_manager()
    if isinstance(db_manager, MockDatabaseManager):
        logger.info("Usando repositório mock (sem persistência)")
        return MockProcessRepository()
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


class MockDatabaseManager:
    """Mock do gerenciador de banco para quando não há banco disponível."""
    
    def create_tables(self):
        """Mock - não faz nada."""
        pass
        
    def get_session(self):
        """Mock - retorna None."""
        return None


class MockProcessRepository(IProcessRepository):
    """Mock do repositório para quando não há banco disponível."""
    
    def persist_extraction(self, case_id: str, payload: dict) -> None:
        """Mock - não persiste nada."""
        logger.info(f"Mock: Simulando persistência do processo {case_id}")
        pass
        
    def get_by_case_id(self, case_id: str) -> dict | None:
        """Mock - sempre retorna None."""
        logger.info(f"Mock: Simulando busca do processo {case_id}")
        return None
