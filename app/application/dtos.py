"""
Data Transfer Objects (DTOs) para a aplicação.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field, field_validator


class TimelineItem(BaseModel):
    """Item da timeline do processo jurídico."""
    
    event_id: int = Field(..., ge=0, description="ID sequencial do evento")
    event_name: str = Field(..., min_length=1, description="Nome do evento jurídico")
    event_description: str = Field(..., min_length=1, description="Descrição do evento")
    event_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Data no formato YYYY-MM-DD")
    event_page_init: int = Field(..., ge=1, description="Página inicial do evento")
    event_page_end: int = Field(..., ge=1, description="Página final do evento")

    @field_validator("event_page_end")
    @classmethod
    def validate_page_range(cls, v, info):
        """Valida que página final >= página inicial."""
        if info.data and "event_page_init" in info.data and v < info.data["event_page_init"]:
            raise ValueError("event_page_end deve ser >= event_page_init")
        return v


class EvidenceItem(BaseModel):
    """Item de evidência do processo jurídico."""
    
    evidence_id: int = Field(..., ge=0, description="ID sequencial da evidência")
    evidence_name: str = Field(..., min_length=1, description="Nome da evidência")
    evidence_flaw: Optional[str] = Field(None, description="Falha ou problema na evidência")
    evidence_page_init: int = Field(..., ge=1, description="Página inicial da evidência")
    evidence_page_end: int = Field(..., ge=1, description="Página final da evidência")

    @field_validator("evidence_page_end")
    @classmethod
    def validate_page_range(cls, v, info):
        """Valida que página final >= página inicial."""
        if info.data and "evidence_page_init" in info.data and v < info.data["evidence_page_init"]:
            raise ValueError("evidence_page_end deve ser >= evidence_page_init")
        return v


class ExtractRequest(BaseModel):
    """Request para extração de dados de PDF."""
    
    pdf_url: HttpUrl = Field(..., description="URL pública do PDF")
    case_id: str = Field(..., min_length=1, description="ID único do processo")


class LlmExtraction(BaseModel):
    """Estrutura de dados extraída pelo LLM."""
    
    resume: str = Field(..., min_length=1, description="Resumo do processo")
    timeline: List[TimelineItem] = Field(..., description="Timeline de eventos")
    evidence: List[EvidenceItem] = Field(..., description="Lista de evidências")


class ExtractResponse(BaseModel):
    """Response da extração de dados."""
    
    case_id: str = Field(..., description="ID único do processo")
    resume: str = Field(..., description="Resumo do processo")
    timeline: List[TimelineItem] = Field(..., description="Timeline de eventos")
    evidence: List[EvidenceItem] = Field(..., description="Lista de evidências")
    persisted_at: datetime = Field(..., description="Data/hora de persistência")


class ProcessData(BaseModel):
    """Dados do processo para persistência."""
    
    case_id: str
    resume: str
    timeline: List[TimelineItem]
    evidence: List[EvidenceItem]
    persisted_at: datetime


class UploadRequest(BaseModel):
    """Request para upload de arquivo."""
    
    case_id: str = Field(..., description="ID único do processo")
    file_path: str = Field(..., description="Caminho do arquivo temporário")
