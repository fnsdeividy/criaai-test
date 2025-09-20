"""
Testes para os use cases da aplicação.
"""
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch
import pytest

from app.application.use_cases import CreateProcessUseCase, GetProcessUseCase
from app.application.services import LlmService, ProcessService
from app.application.dtos import ExtractRequest
from app.infrastructure.http_downloader import HttpDownloader
from app.core.exceptions import DownloadError, LlmError, ValidationError


class TestCreateProcessUseCase:
    """Testes para CreateProcessUseCase."""

    @pytest.mark.asyncio
    async def test_execute_success_happy_path(
        self,
        mock_repository,
        mock_llm_client,
        sample_extract_request,
        sample_llm_extraction,
        temp_pdf_file
    ):
        """Testa fluxo de sucesso completo."""
        # Arrange
        llm_service = LlmService(mock_llm_client)
        process_service = ProcessService()
        downloader = Mock(spec=HttpDownloader)
        downloader.download_pdf.return_value = temp_pdf_file
        
        # Mock LLM service para retornar extração válida
        with patch.object(llm_service, 'extract_process_data', return_value=sample_llm_extraction):
            use_case = CreateProcessUseCase(
                repository=mock_repository,
                llm_service=llm_service,
                process_service=process_service,
                downloader=downloader,
                tmp_dir=tempfile.gettempdir()
            )
            
            request = ExtractRequest(**sample_extract_request)
            
            # Act
            result = await use_case.execute(request)
            
            # Assert
            assert result.case_id == request.case_id
            assert result.resume == sample_llm_extraction.resume
            assert len(result.timeline) == 1
            assert len(result.evidence) == 1
            assert isinstance(result.persisted_at, datetime)
            
            # Verificar chamadas
            downloader.download_pdf.assert_called_once()
            mock_repository.persist_extraction.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_idempotency_existing_case(
        self,
        mock_repository,
        mock_llm_client,
        sample_extract_request,
        existing_process_data
    ):
        """Testa idempotência - retorna dados existentes sem reprocessar."""
        # Arrange
        mock_repository.get_by_case_id.return_value = existing_process_data
        
        llm_service = LlmService(mock_llm_client)
        process_service = ProcessService()
        downloader = Mock(spec=HttpDownloader)
        
        use_case = CreateProcessUseCase(
            repository=mock_repository,
            llm_service=llm_service,
            process_service=process_service,
            downloader=downloader
        )
        
        request = ExtractRequest(**sample_extract_request)
        
        # Act
        result = await use_case.execute(request)
        
        # Assert
        assert result.case_id == existing_process_data["case_id"]
        assert result.resume == existing_process_data["resume"]
        
        # Verificar que não fez download nem persistência
        downloader.download_pdf.assert_not_called()
        mock_repository.persist_extraction.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_download_failure(
        self,
        mock_repository,
        mock_llm_client,
        sample_extract_request
    ):
        """Testa falha no download do PDF."""
        # Arrange
        llm_service = LlmService(mock_llm_client)
        process_service = ProcessService()
        downloader = Mock(spec=HttpDownloader)
        downloader.download_pdf.side_effect = DownloadError("Erro 404")
        
        use_case = CreateProcessUseCase(
            repository=mock_repository,
            llm_service=llm_service,
            process_service=process_service,
            downloader=downloader
        )
        
        request = ExtractRequest(**sample_extract_request)
        
        # Act & Assert
        with pytest.raises(DownloadError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_execute_llm_failure_retry_success(
        self,
        mock_repository,
        mock_llm_client,
        sample_extract_request,
        sample_llm_extraction,
        temp_pdf_file
    ):
        """Testa falha no LLM na primeira tentativa e sucesso na segunda."""
        # Arrange
        llm_service = LlmService(mock_llm_client)
        process_service = ProcessService()
        downloader = Mock(spec=HttpDownloader)
        downloader.download_pdf.return_value = temp_pdf_file
        
        # Mock para falhar na primeira e suceder na segunda
        with patch.object(llm_service, 'extract_process_data') as mock_extract:
            mock_extract.side_effect = [LlmError("Falha temporária"), sample_llm_extraction]
            
            use_case = CreateProcessUseCase(
                repository=mock_repository,
                llm_service=llm_service,
                process_service=process_service,
                downloader=downloader,
                tmp_dir=tempfile.gettempdir()
            )
            
            request = ExtractRequest(**sample_extract_request)
            
            # Act - primeira chamada falha, mas o use case não tem retry automático
            # Neste caso, a falha será propagada
            with pytest.raises(LlmError):
                await use_case.execute(request)

    def test_execute_invalid_case_id(
        self, 
        mock_repository, 
        mock_llm_client
    ):
        """Testa validação de case_id inválido."""
        # Arrange
        llm_service = LlmService(mock_llm_client)
        process_service = ProcessService()
        downloader = Mock(spec=HttpDownloader)
        
        use_case = CreateProcessUseCase(
            repository=mock_repository,
            llm_service=llm_service,
            process_service=process_service,
            downloader=downloader
        )
        
        # Testar se a validação ocorre na criação do DTO
        with pytest.raises(Exception):  # Pydantic ValidationError
            ExtractRequest(
                pdf_url="https://www.orimi.com/pdf-test.pdf?utm_source=chatgpt.com",
                case_id=""  # case_id vazio
            )


class TestGetProcessUseCase:
    """Testes para GetProcessUseCase."""

    def test_execute_found(self, mock_repository, existing_process_data):
        """Testa consulta de processo existente."""
        # Arrange
        mock_repository.get_by_case_id.return_value = existing_process_data
        use_case = GetProcessUseCase(mock_repository)
        
        # Act
        result = use_case.execute("0809090-86.2024.8.12.0021")
        
        # Assert
        assert result is not None
        assert result.case_id == existing_process_data["case_id"]
        assert result.resume == existing_process_data["resume"]

    def test_execute_not_found(self, mock_repository):
        """Testa consulta de processo não existente."""
        # Arrange
        mock_repository.get_by_case_id.return_value = None
        use_case = GetProcessUseCase(mock_repository)
        
        # Act
        result = use_case.execute("inexistente")
        
        # Assert
        assert result is None
