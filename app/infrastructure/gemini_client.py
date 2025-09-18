"""
Cliente para integração com Google Gemini API.
"""
import json
import logging
from typing import Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.domain.interfaces import ILlmClient
from app.core.exceptions import LlmError

logger = logging.getLogger(__name__)


class GeminiClient(ILlmClient):
    """Cliente para Google Gemini API."""

    def __init__(self, api_key: str):
        """
        Inicializa o cliente Gemini.
        
        Args:
            api_key: Chave da API do Google Gemini
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def upload_file(self, file_path: str) -> str:
        """
        Faz upload de arquivo para o Gemini.
        
        Args:
            file_path: Caminho para o arquivo local
            
        Returns:
            ID do arquivo no Gemini
            
        Raises:
            LlmError: Se falhar no upload
        """
        try:
            logger.info(f"Fazendo upload do arquivo: {file_path}")
            uploaded_file = genai.upload_file(file_path)
            logger.info(f"Upload concluído. File ID: {uploaded_file.name}")
            return uploaded_file.name
        except Exception as e:
            logger.error(f"Erro no upload do arquivo: {e}")
            raise LlmError(f"Falha no upload do arquivo: {str(e)}")

    def extract_structured(
        self, 
        context_file_id: str, 
        instruction: str, 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extrai dados estruturados usando o arquivo como contexto.
        
        Args:
            context_file_id: ID do arquivo no Gemini
            instruction: Instruções para o modelo
            schema: Schema JSON esperado
            
        Returns:
            Dados estruturados extraídos
            
        Raises:
            LlmError: Se falhar na geração ou se resposta for inválida
        """
        try:
            # Configurar geração com JSON estruturado
            generation_config = genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=8192
            )

            # Configurar filtros de segurança
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            # Obter arquivo do Gemini
            uploaded_file = genai.get_file(context_file_id)
            
            # Criar prompt com schema
            prompt = f"""
{instruction}

Responda EXATAMENTE no formato JSON especificado abaixo:

Schema esperado:
{json.dumps(schema, indent=2, ensure_ascii=False)}

IMPORTANTE:
- Todas as datas devem estar no formato YYYY-MM-DD
- Todos os campos obrigatórios devem ser preenchidos
- IDs devem ser sequenciais começando em 0
- Páginas devem ser números inteiros >= 1
- Se event_page_end < event_page_init, corrija para event_page_end = event_page_init
- Use vocabulário jurídico apropriado para event_name
"""

            logger.info("Iniciando geração com Gemini")
            
            # Fazer até 2 tentativas
            for attempt in range(2):
                try:
                    response = self.model.generate_content(
                        [uploaded_file, prompt],
                        generation_config=generation_config,
                        safety_settings=safety_settings
                    )
                    
                    if not response.text:
                        raise LlmError("Resposta vazia do modelo")
                    
                    # Tentar parsear JSON
                    result = json.loads(response.text)
                    logger.info(f"Geração bem-sucedida na tentativa {attempt + 1}")
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Tentativa {attempt + 1}: JSON inválido - {e}")
                    if attempt == 1:  # Última tentativa
                        raise LlmError(f"Resposta não é um JSON válido após 2 tentativas: {e}")
                    
                except Exception as e:
                    logger.warning(f"Tentativa {attempt + 1}: Erro na geração - {e}")
                    if attempt == 1:  # Última tentativa
                        raise LlmError(f"Falha na geração após 2 tentativas: {e}")
                        
        except LlmError:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado na extração: {e}")
            raise LlmError(f"Erro inesperado: {str(e)}")
