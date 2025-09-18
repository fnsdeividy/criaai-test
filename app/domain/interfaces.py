"""
Interfaces do domínio para abstrair dependências externas.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class ILlmClient(ABC):
    """Interface para cliente de LLM (Large Language Model)."""

    @abstractmethod
    def upload_file(self, file_path: str) -> str:
        """
        Faz upload de um arquivo para o serviço de LLM.
        
        Args:
            file_path: Caminho para o arquivo local
            
        Returns:
            ID ou referência do arquivo no serviço
        """
        pass

    @abstractmethod
    def extract_structured(
        self, 
        context_file_id: str, 
        instruction: str, 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extrai informações estruturadas de um arquivo usando LLM.
        
        Args:
            context_file_id: ID do arquivo no serviço de LLM
            instruction: Instruções para o modelo
            schema: Schema JSON esperado na resposta
            
        Returns:
            Dados estruturados extraídos do arquivo
        """
        pass


class IProcessRepository(ABC):
    """Interface para repositório de processos jurídicos."""

    @abstractmethod
    def persist_extraction(self, case_id: str, payload: Dict[str, Any]) -> None:
        """
        Persiste os dados extraídos de um processo.
        
        Args:
            case_id: Identificador único do processo
            payload: Dados extraídos para persistir
        """
        pass

    @abstractmethod
    def get_by_case_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera dados de um processo pelo ID.
        
        Args:
            case_id: Identificador único do processo
            
        Returns:
            Dados do processo se encontrado, None caso contrário
        """
        pass
