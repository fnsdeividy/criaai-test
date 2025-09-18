"""
Cliente mock para desenvolvimento/teste sem API key real.
"""
import json
import logging
from typing import Dict, Any
from app.domain.interfaces import ILlmClient
from app.core.exceptions import LlmError

logger = logging.getLogger(__name__)


class MockGeminiClient(ILlmClient):
    """Cliente mock para Google Gemini API."""

    def __init__(self, api_key: str):
        """
        Inicializa o cliente mock.
        
        Args:
            api_key: Chave da API (ignorada no mock)
        """
        self.api_key = api_key
        logger.info("Usando MockGeminiClient para desenvolvimento/teste")

    def upload_file(self, file_path: str) -> str:
        """
        Simula upload de arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            ID fictício do arquivo
        """
        logger.info(f"Mock: Upload simulado de {file_path}")
        return f"mock_file_id_{hash(file_path)}"

    def extract_from_pdf(self, file_uri: str) -> Dict[str, Any]:
        """
        Simula extração de dados de PDF.
        
        Args:
            file_uri: URI do arquivo
            
        Returns:
            Dados extraídos simulados
        """
        logger.info(f"Mock: Extração simulada de {file_uri}")
        
        # Dados mock para demonstração
        mock_response = {
            "resume": "Este é um processo jurídico de teste gerado pelo sistema mock. O processo trata de uma ação civil entre partes fictícias, demonstrando a funcionalidade de extração de dados estruturados.",
            "timeline": [
                {
                    "event_id": 1,
                    "event_name": "Distribuição do Processo",
                    "event_description": "Processo distribuído para análise inicial",
                    "event_date": "2024-01-15",
                    "event_page_init": 1,
                    "event_page_end": 2
                },
                {
                    "event_id": 2,
                    "event_name": "Citação da Parte Requerida",
                    "event_description": "Citação realizada com sucesso",
                    "event_date": "2024-02-01",
                    "event_page_init": 3,
                    "event_page_end": 4
                },
                {
                    "event_id": 3,
                    "event_name": "Apresentação de Defesa",
                    "event_description": "Defesa apresentada dentro do prazo legal",
                    "event_date": "2024-02-15",
                    "event_page_init": 5,
                    "event_page_end": 8
                }
            ],
            "evidence": [
                {
                    "evidence_id": 1,
                    "evidence_name": "Contrato Social",
                    "evidence_description": "Documento que comprova a constituição da empresa",
                    "evidence_page_init": 9,
                    "evidence_page_end": 12
                },
                {
                    "evidence_id": 2,
                    "evidence_name": "Comprovante de Pagamento",
                    "evidence_description": "Recibo que demonstra o pagamento realizado",
                    "evidence_page_init": 13,
                    "evidence_page_end": 13
                }
            ]
        }
        
        return mock_response

    def extract_structured(
        self, 
        context_file_id: str, 
        instruction: str, 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simula extração estruturada de dados.
        
        Args:
            context_file_id: ID do arquivo de contexto
            instruction: Instrução para o LLM
            schema: Schema JSON esperado
            
        Returns:
            Dados extraídos simulados
        """
        logger.info(f"Mock: Extração estruturada simulada para arquivo {context_file_id}")
        
        # Retornar dados mock baseados no schema esperado
        mock_structured_response = {
            "resume": "Este é um processo jurídico de teste gerado pelo sistema mock. O processo trata de uma ação civil entre partes fictícias, demonstrando a funcionalidade de extração de dados estruturados.",
            "timeline": [
                {
                    "event_id": 1,
                    "event_name": "Distribuição do Processo",
                    "event_description": "Processo distribuído para análise inicial",
                    "event_date": "2024-01-15",
                    "event_page_init": 1,
                    "event_page_end": 2
                },
                {
                    "event_id": 2,
                    "event_name": "Citação da Parte Requerida",
                    "event_description": "Citação realizada com sucesso",
                    "event_date": "2024-02-01",
                    "event_page_init": 3,
                    "event_page_end": 4
                }
            ],
            "evidence": [
                {
                    "evidence_id": 1,
                    "evidence_name": "Contrato Social",
                    "evidence_description": "Documento que comprova a constituição da empresa",
                    "evidence_page_init": 9,
                    "evidence_page_end": 12
                },
                {
                    "evidence_id": 2,
                    "evidence_name": "Comprovante de Pagamento",
                    "evidence_description": "Recibo que demonstra o pagamento realizado",
                    "evidence_page_init": 13,
                    "evidence_page_end": 13
                }
            ]
        }
        
        return mock_structured_response
