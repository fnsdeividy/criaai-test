"""
Use cases da aplicação para orquestrar fluxos de negócio.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from app.domain.interfaces import IProcessRepository
from app.infrastructure.http_downloader import HttpDownloader
from app.application.services import LlmService, ProcessService
from app.application.dtos import ExtractRequest, ExtractResponse, UploadRequest, ProcessData
from app.core.exceptions import DownloadError, LlmError, RepositoryError, ValidationError

logger = logging.getLogger(__name__)


class CreateProcessUseCase:
    """Use case para criar/processar extração de processo jurídico."""

    def __init__(
        self,
        repository: IProcessRepository,
        llm_service: LlmService,
        process_service: ProcessService,
        downloader: HttpDownloader,
        tmp_dir: str = "/tmp"
    ):
        """
        Inicializa o use case.
        
        Args:
            repository: Repositório de processos
            llm_service: Serviço de LLM
            process_service: Serviço de processos
            downloader: Cliente de download
            tmp_dir: Diretório temporário para arquivos
        """
        self.repository = repository
        self.llm_service = llm_service
        self.process_service = process_service
        self.downloader = downloader
        self.tmp_dir = tmp_dir

    async def execute(self, request: ExtractRequest) -> ExtractResponse:
        """
        Executa o fluxo completo de extração de processo.
        
        Args:
            request: Dados da requisição
            
        Returns:
            Resposta com dados extraídos e persistidos
            
        Raises:
            ValidationError: Se dados de entrada forem inválidos
            DownloadError: Se falhar no download do PDF
            LlmError: Se falhar na extração com LLM
            RepositoryError: Se falhar na persistência
        """
        case_id = request.case_id.strip()
        pdf_url = str(request.pdf_url)
        
        logger.info(f"Iniciando processamento do caso {case_id}")
        
        # Validar case_id
        if not self.process_service.validate_case_id(case_id):
            raise ValidationError(f"ID de caso inválido: {case_id}")
        
        # Verificar se já existe (idempotência)
        logger.info(f"Verificando se caso {case_id} já existe")
        existing_data = self.repository.get_by_case_id(case_id)
        if existing_data:
            logger.info(f"Caso {case_id} já existe, retornando dados salvos")
            return ExtractResponse(
                case_id=existing_data["case_id"],
                resume=existing_data["resume"],
                timeline=[item for item in existing_data["timeline"]],
                evidence=[item for item in existing_data["evidence"]],
                persisted_at=existing_data["persisted_at"]
            )
        
        # Caminho do arquivo temporário
        pdf_file_path = os.path.join(self.tmp_dir, f"{case_id}.pdf")
        
        try:
            # 1. Download do PDF
            logger.info(f"Fazendo download do PDF: {pdf_url}")
            await self.downloader.download_pdf(pdf_url, pdf_file_path)
            
            # 2. Extração com LLM
            logger.info("Extraindo dados com LLM")
            extraction = self.llm_service.extract_process_data(pdf_file_path)
            
            # 3. Normalizar dados
            normalized_data = self.process_service.normalize_extraction_data(extraction)
            
            # 4. Persistir dados
            persisted_at = datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            payload = {
                **normalized_data,
                "persisted_at": persisted_at
            }
            
            logger.info(f"Persistindo dados do caso {case_id}")
            self.repository.persist_extraction(case_id, payload)
            
            # 5. Retornar resposta
            logger.info(f"Processamento do caso {case_id} concluído com sucesso")
            return ExtractResponse(
                case_id=case_id,
                resume=extraction.resume,
                timeline=extraction.timeline,
                evidence=extraction.evidence,
                persisted_at=persisted_at
            )
            
        finally:
            # Limpar arquivo temporário
            try:
                if os.path.exists(pdf_file_path):
                    os.remove(pdf_file_path)
                    logger.info(f"Arquivo temporário removido: {pdf_file_path}")
            except Exception as e:
                logger.warning(f"Falha ao remover arquivo temporário {pdf_file_path}: {e}")


class GetProcessUseCase:
    """Use case para recuperar processo existente."""

    def __init__(self, repository: IProcessRepository):
        """
        Inicializa o use case.
        
        Args:
            repository: Repositório de processos
        """
        self.repository = repository

    def execute(self, case_id: str) -> Optional[ExtractResponse]:
        """
        Recupera dados de um processo existente.
        
        Args:
            case_id: ID do processo
            
        Returns:
            Dados do processo se encontrado, None caso contrário
            
        Raises:
            RepositoryError: Se falhar na consulta
        """
        logger.info(f"Buscando dados do caso {case_id}")
        
        data = self.repository.get_by_case_id(case_id.strip())
        if not data:
            logger.info(f"Caso {case_id} não encontrado")
            return None
        
        logger.info(f"Caso {case_id} encontrado")
        return ExtractResponse(
            case_id=data["case_id"],
            resume=data["resume"],
            timeline=[item for item in data["timeline"]],
            evidence=[item for item in data["evidence"]],
            persisted_at=data["persisted_at"]
        )


class CreateProcessFromUploadUseCase:
    """Use case para processar arquivo enviado via upload."""

    def __init__(self, llm_service: LlmService, process_service: ProcessService, repository: IProcessRepository):
        """
        Inicializa o use case.
        
        Args:
            llm_service: Serviço de LLM
            process_service: Serviço de processo
            repository: Repositório de processos
        """
        self.llm_service = llm_service
        self.process_service = process_service
        self.repository = repository

    def execute(self, request: UploadRequest) -> ExtractResponse:
        """
        Executa o processamento de arquivo enviado via upload.
        
        Args:
            request: Dados do upload (case_id e caminho do arquivo)
            
        Returns:
            Resposta com dados extraídos e persistidos
            
        Raises:
            ValidationError: Se dados de entrada forem inválidos
            LlmError: Se falhar na extração com LLM
            RepositoryError: Se falhar na persistência
        """
        logger.info(f"Iniciando processamento de upload para caso {request.case_id}")
        
        # Verificar se já existe processo com este case_id
        existing_data = self.repository.get_by_case_id(request.case_id)
        if existing_data:
            logger.info(f"Processo {request.case_id} já existe, retornando dados existentes")
            return ExtractResponse(
                case_id=existing_data["case_id"],
                resume=existing_data["resume"],
                timeline=[item for item in existing_data["timeline"]],
                evidence=[item for item in existing_data["evidence"]],
                persisted_at=existing_data["persisted_at"]
            )
        
        try:
            # Processar arquivo com LLM
            logger.info(f"Processando arquivo {request.file_path} com LLM")
            extraction = self.llm_service.extract_process_data(request.file_path)
            
            # Persistir dados
            logger.info(f"Persistindo dados do caso {request.case_id}")
            process_data = ProcessData(
                case_id=request.case_id,
                resume=extraction.resume,
                timeline=extraction.timeline,
                evidence=extraction.evidence,
                persisted_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            
            # Salvar dados no repositório
            payload = {
                "resume": process_data.resume,
                "timeline": [item.model_dump() for item in process_data.timeline],
                "evidence": [item.model_dump() for item in process_data.evidence],
                "persisted_at": process_data.persisted_at
            }
            logger.info(f"💾 Tentando persistir dados para caso {process_data.case_id}")
            logger.info(f"🗄️ Tipo do repositório: {type(self.repository).__name__}")
            logger.info(f"📋 Payload: resume={len(payload['resume'])} chars, timeline={len(payload['timeline'])} items, evidence={len(payload['evidence'])} items")
            
            self.repository.persist_extraction(process_data.case_id, payload)
            logger.info(f"✅ Dados persistidos com sucesso para caso {process_data.case_id}")
            
            # Retornar resposta
            saved_data = ExtractResponse(
                case_id=process_data.case_id,
                resume=process_data.resume,
                timeline=process_data.timeline,
                evidence=process_data.evidence,
                persisted_at=process_data.persisted_at
            )
            
            logger.info(f"Upload processado com sucesso para caso {request.case_id}")
            return saved_data
            
        except Exception as e:
            logger.error(f"Erro no processamento do upload {request.case_id}: {e}")
            raise
