"""
Serviços da aplicação para orquestrar regras de negócio.
"""
import logging
from typing import Dict, Any

from app.domain.interfaces import ILlmClient
from app.application.dtos import LlmExtraction
from app.core.exceptions import LlmError, ValidationError

logger = logging.getLogger(__name__)


class LlmService:
    """Serviço para coordenar operações com LLM."""

    def __init__(self, llm_client: ILlmClient):
        """
        Inicializa o serviço.
        
        Args:
            llm_client: Cliente do LLM
        """
        self.llm_client = llm_client

    def extract_process_data(self, file_path: str) -> LlmExtraction:
        """
        Extrai dados estruturados de um processo jurídico.
        
        Args:
            file_path: Caminho para o arquivo PDF
            
        Returns:
            Dados extraídos e validados
            
        Raises:
            LlmError: Se falhar na extração
            ValidationError: Se dados extraídos forem inválidos
        """
        try:
            # Upload do arquivo
            logger.info("Fazendo upload do arquivo para o LLM")
            file_id = self.llm_client.upload_file(file_path)
            
            # Definir schema esperado
            schema = {
                "type": "object",
                "properties": {
                    "resume": {"type": "string"},
                    "timeline": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "integer"},
                                "event_name": {"type": "string"},
                                "event_description": {"type": "string"},
                                "event_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                                "event_page_init": {"type": "integer", "minimum": 1},
                                "event_page_end": {"type": "integer", "minimum": 1}
                            },
                            "required": ["event_id", "event_name", "event_description", "event_date", "event_page_init", "event_page_end"]
                        }
                    },
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "evidence_id": {"type": "integer"},
                                "evidence_name": {"type": "string"},
                                "evidence_flaw": {"type": ["string", "null"]},
                                "evidence_page_init": {"type": "integer", "minimum": 1},
                                "evidence_page_end": {"type": "integer", "minimum": 1}
                            },
                            "required": ["evidence_id", "evidence_name", "evidence_page_init", "evidence_page_end"]
                        }
                    }
                },
                "required": ["resume", "timeline", "evidence"]
            }
            
            # Instrução para o modelo
            instruction = """
Você é um perito jurídico. Leia o PDF anexado como arquivo (não resuma apenas o texto extraído). 
Identifique fatos processuais, datas e páginas. Construa exatamente o JSON no response_schema.

Diretrizes:
- Converta todas as datas para YYYY-MM-DD
- Se houver múltiplas menções do mesmo evento, considere a mais relevante/mais recente
- Use páginas do próprio PDF para *_page_*
- Para event_name, use vocabulário jurídico apropriado como:
  * "Decisão Interlocutória"
  * "Citação/Intimação" 
  * "Audiência/Sessão"
  * "Manifestação das Partes"
  * "Sentença"
  * "Recurso"
  * "Despacho"
- Para evidence_flaw, indique problemas como "parcialmente ilegível", "sem inconsistências", etc.
- Se event_page_end < event_page_init, corrija para event_page_end = event_page_init
- IDs devem ser sequenciais começando em 0
- Evite suposições, baseie-se apenas no conteúdo do PDF

Exemplo de eventos (apenas para referência, não fixe estes valores):
- "Petição Inicial" em 2024-01-15
- "Citação/Intimação" em 2024-02-20
"""
            
            # Extrair dados estruturados
            logger.info("Extraindo dados estruturados do processo")
            raw_data = self.llm_client.extract_structured(file_id, instruction, schema)
            
            # Validar com Pydantic
            logger.info("Validando dados extraídos")
            extraction = LlmExtraction(**raw_data)
            
            logger.info("Extração concluída com sucesso")
            return extraction
            
        except Exception as e:
            if isinstance(e, (LlmError, ValidationError)):
                raise
            logger.error(f"Erro inesperado na extração: {e}")
            raise LlmError(f"Erro inesperado na extração: {str(e)}")


class ProcessService:
    """Serviço para regras de negócio de processos jurídicos."""

    def validate_case_id(self, case_id: str) -> bool:
        """
        Valida formato do ID do processo.
        
        Args:
            case_id: ID do processo para validar
            
        Returns:
            True se válido, False caso contrário
        """
        # Validação básica - pode ser expandida conforme necessário
        return bool(case_id and len(case_id.strip()) > 0)

    def normalize_extraction_data(self, extraction: LlmExtraction) -> Dict[str, Any]:
        """
        Normaliza dados extraídos para persistência.
        
        Args:
            extraction: Dados extraídos validados
            
        Returns:
            Dados normalizados para persistência
        """
        return {
            "resume": extraction.resume,
            "timeline": [item.model_dump() for item in extraction.timeline],
            "evidence": [item.model_dump() for item in extraction.evidence]
        }
