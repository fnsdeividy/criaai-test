"""
Testes para os DTOs da aplicação.
"""
import pytest
from pydantic import ValidationError

from app.application.dtos import TimelineItem, EvidenceItem, ExtractRequest, LlmExtraction


class TestTimelineItem:
    """Testes para TimelineItem."""

    def test_valid_timeline_item(self):
        """Testa criação de item válido."""
        item = TimelineItem(
            event_id=0,
            event_name="Petição Inicial",
            event_description="Petição inicial protocolada",
            event_date="2024-01-15",
            event_page_init=1,
            event_page_end=3
        )
        
        assert item.event_id == 0
        assert item.event_name == "Petição Inicial"
        assert item.event_date == "2024-01-15"

    def test_invalid_date_format(self):
        """Testa validação de formato de data inválido."""
        with pytest.raises(ValidationError):
            TimelineItem(
                event_id=0,
                event_name="Evento",
                event_description="Descrição",
                event_date="15/01/2024",  # formato inválido
                event_page_init=1,
                event_page_end=3
            )

    def test_invalid_page_range(self):
        """Testa validação de range de páginas inválido."""
        with pytest.raises(ValidationError):
            TimelineItem(
                event_id=0,
                event_name="Evento",
                event_description="Descrição",
                event_date="2024-01-15",
                event_page_init=5,
                event_page_end=3  # página final menor que inicial
            )

    def test_negative_event_id(self):
        """Testa validação de event_id negativo."""
        with pytest.raises(ValidationError):
            TimelineItem(
                event_id=-1,  # negativo
                event_name="Evento",
                event_description="Descrição",
                event_date="2024-01-15",
                event_page_init=1,
                event_page_end=3
            )


class TestEvidenceItem:
    """Testes para EvidenceItem."""

    def test_valid_evidence_item(self):
        """Testa criação de evidência válida."""
        item = EvidenceItem(
            evidence_id=0,
            evidence_name="Documento",
            evidence_flaw=None,
            evidence_page_init=10,
            evidence_page_end=12
        )
        
        assert item.evidence_id == 0
        assert item.evidence_name == "Documento"
        assert item.evidence_flaw is None

    def test_evidence_with_flaw(self):
        """Testa evidência com falha."""
        item = EvidenceItem(
            evidence_id=0,
            evidence_name="Documento",
            evidence_flaw="parcialmente ilegível",
            evidence_page_init=10,
            evidence_page_end=12
        )
        
        assert item.evidence_flaw == "parcialmente ilegível"

    def test_invalid_page_range(self):
        """Testa validação de range de páginas inválido."""
        with pytest.raises(ValidationError):
            EvidenceItem(
                evidence_id=0,
                evidence_name="Documento",
                evidence_flaw=None,
                evidence_page_init=15,
                evidence_page_end=10  # página final menor que inicial
            )


class TestExtractRequest:
    """Testes para ExtractRequest."""

    def test_valid_request(self):
        """Testa requisição válida."""
        request = ExtractRequest(
            pdf_url="https://exemplo.com/documento.pdf",
            case_id="0809090-86.2024.8.12.0021"
        )
        
        assert str(request.pdf_url) == "https://exemplo.com/documento.pdf"
        assert request.case_id == "0809090-86.2024.8.12.0021"

    def test_invalid_url(self):
        """Testa URL inválida."""
        with pytest.raises(ValidationError):
            ExtractRequest(
                pdf_url="not-a-url",
                case_id="0809090-86.2024.8.12.0021"
            )

    def test_empty_case_id(self):
        """Testa case_id vazio."""
        with pytest.raises(ValidationError):
            ExtractRequest(
                pdf_url="https://exemplo.com/documento.pdf",
                case_id=""
            )


class TestLlmExtraction:
    """Testes para LlmExtraction."""

    def test_valid_extraction(self):
        """Testa extração válida."""
        timeline_item = TimelineItem(
            event_id=0,
            event_name="Petição Inicial",
            event_description="Petição inicial protocolada",
            event_date="2024-01-15",
            event_page_init=1,
            event_page_end=3
        )
        
        evidence_item = EvidenceItem(
            evidence_id=0,
            evidence_name="Documento",
            evidence_flaw=None,
            evidence_page_init=10,
            evidence_page_end=12
        )
        
        extraction = LlmExtraction(
            resume="Resumo do processo",
            timeline=[timeline_item],
            evidence=[evidence_item]
        )
        
        assert extraction.resume == "Resumo do processo"
        assert len(extraction.timeline) == 1
        assert len(extraction.evidence) == 1

    def test_empty_resume(self):
        """Testa resumo vazio."""
        with pytest.raises(ValidationError):
            LlmExtraction(
                resume="",  # vazio
                timeline=[],
                evidence=[]
            )
