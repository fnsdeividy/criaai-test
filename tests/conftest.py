"""
Configurações e fixtures compartilhadas para testes.
"""
import os
import tempfile
from typing import Dict, Any
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.domain.interfaces import ILlmClient, IProcessRepository
from app.application.dtos import LlmExtraction, TimelineItem, EvidenceItem


@pytest.fixture
def test_client():
    """Cliente de teste para FastAPI."""
    # Limpar cache das dependências para testes
    from app.core.dependencies import (
        get_database_manager, get_gemini_client, get_http_downloader,
        get_process_repository, get_llm_service, get_process_service,
        get_create_process_use_case, get_get_process_use_case,
        get_create_process_from_upload_use_case
    )

    get_database_manager.cache_clear()
    get_gemini_client.cache_clear()
    get_http_downloader.cache_clear()
    get_process_repository.cache_clear()
    get_llm_service.cache_clear()
    get_process_service.cache_clear()
    get_create_process_use_case.cache_clear()
    get_get_process_use_case.cache_clear()
    get_create_process_from_upload_use_case.cache_clear()

    return TestClient(app)


@pytest.fixture
def mock_create_use_case():
    """Mock do use case de criação."""
    from unittest.mock import AsyncMock
    return AsyncMock()


@pytest.fixture
def mock_get_use_case():
    """Mock do use case de consulta."""
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def mock_llm_client():
    """Mock do cliente LLM."""
    mock = Mock(spec=ILlmClient)
    mock.upload_file.return_value = "test_file_id"
    mock.extract_structured.return_value = {
        "resume": "Resumo do processo de teste",
        "timeline": [
            {
                "event_id": 0,
                "event_name": "Petição Inicial",
                "event_description": "Petição inicial protocolada",
                "event_date": "2024-01-15",
                "event_page_init": 1,
                "event_page_end": 3
            }
        ],
        "evidence": [
            {
                "evidence_id": 0,
                "evidence_name": "Documento de Identidade",
                "evidence_flaw": None,
                "evidence_page_init": 10,
                "evidence_page_end": 11
            }
        ]
    }
    return mock


@pytest.fixture
def mock_repository():
    """Mock do repositório."""
    mock = Mock(spec=IProcessRepository)
    mock.get_by_case_id.return_value = None  # Por padrão, não existe
    return mock


@pytest.fixture
def sample_extract_request():
    """Requisição de extração de exemplo."""
    return {
        "pdf_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "case_id": "0809090-86.2024.8.12.0021"
    }


@pytest.fixture
def sample_llm_extraction():
    """Extração LLM de exemplo."""
    return LlmExtraction(
        resume="Resumo do processo de teste",
        timeline=[
            TimelineItem(
                event_id=0,
                event_name="Petição Inicial",
                event_description="Petição inicial protocolada",
                event_date="2024-01-15",
                event_page_init=1,
                event_page_end=3
            )
        ],
        evidence=[
            EvidenceItem(
                evidence_id=0,
                evidence_name="Documento de Identidade",
                evidence_flaw=None,
                evidence_page_init=10,
                evidence_page_end=11
            )
        ]
    )


@pytest.fixture
def temp_pdf_file():
    """Arquivo PDF temporário para testes."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        # Escrever header básico de PDF
        f.write(b"%PDF-1.4\n")
        f.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        f.write(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
        f.write(b"3 0 obj\n<< /Type /Page /Parent 2 0 R >>\nendobj\n")
        f.write(b"xref\n0 4\n0000000000 65535 f \n")
        f.write(b"0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n")
        f.write(b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n174\n%%EOF\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def existing_process_data():
    """Dados de processo existente."""
    return {
        "case_id": "0809090-86.2024.8.12.0021",
        "resume": "Resumo do processo existente",
        "timeline": [
            {
                "event_id": 0,
                "event_name": "Petição Inicial",
                "event_description": "Petição inicial protocolada",
                "event_date": "2024-01-15",
                "event_page_init": 1,
                "event_page_end": 3
            }
        ],
        "evidence": [
            {
                "evidence_id": 0,
                "evidence_name": "Documento de Identidade",
                "evidence_flaw": None,
                "evidence_page_init": 10,
                "evidence_page_end": 11
            }
        ],
        "persisted_at": "2024-08-28T12:00:00Z"
    }
