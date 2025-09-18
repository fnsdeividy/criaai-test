"""
Cliente para integração com Google Gemini API.
"""
import json
import logging
import time
import random
import signal
import threading
from contextlib import contextmanager
from typing import Dict, Any, Callable, TypeVar
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import (
    ServiceUnavailable, 
    DeadlineExceeded, 
    InternalServerError,
    RetryError,
    GoogleAPIError
)

T = TypeVar('T')

from app.domain.interfaces import ILlmClient
from app.core.exceptions import LlmError

logger = logging.getLogger(__name__)


class GeminiClient(ILlmClient):
    """Cliente para Google Gemini API."""

    def __init__(
        self, 
        api_key: str, 
        max_retries: int = 3, 
        retry_delay_base: float = 1.0, 
        retry_delay_max: float = 60.0,
        upload_timeout: int = 300,
        generation_timeout: int = 600
    ):
        """
        Inicializa o cliente Gemini.
        
        Args:
            api_key: Chave da API do Google Gemini
            max_retries: Número máximo de tentativas para operações que falham
            retry_delay_base: Delay base em segundos para retry (exponential backoff)
            retry_delay_max: Delay máximo em segundos para retry
            upload_timeout: Timeout em segundos para operações de upload
            generation_timeout: Timeout em segundos para operações de geração
        """
        self.api_key = api_key
        self.max_retries = max_retries
        self.retry_delay_base = retry_delay_base
        self.retry_delay_max = retry_delay_max
        self.upload_timeout = upload_timeout
        self.generation_timeout = generation_timeout
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    @contextmanager
    def _timeout_context(self, timeout_seconds: int, operation_name: str):
        """
        Context manager para aplicar timeout em operações.
        
        Args:
            timeout_seconds: Timeout em segundos
            operation_name: Nome da operação para logs
            
        Raises:
            LlmError: Se a operação exceder o timeout
        """
        def timeout_handler(signum, frame):
            raise LlmError(f"Timeout de {timeout_seconds}s excedido para {operation_name}")
        
        # Configurar timeout usando signal (funciona apenas em Unix)
        try:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            yield
        except AttributeError:
            # signal.SIGALRM não está disponível (Windows), usar thread-based timeout
            result = [None]
            exception = [None]
            
            def target():
                try:
                    yield
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)
            
            if thread.is_alive():
                raise LlmError(f"Timeout de {timeout_seconds}s excedido para {operation_name}")
            
            if exception[0]:
                raise exception[0]
                
        finally:
            try:
                signal.alarm(0)  # Cancelar alarm
                signal.signal(signal.SIGALRM, old_handler)
            except (AttributeError, NameError):
                pass  # Não está usando signal
    
    def _with_timeout(self, operation_func: Callable[[], T], timeout_seconds: int, operation_name: str) -> T:
        """
        Executa uma operação com timeout usando threading.
        
        Args:
            operation_func: Função a ser executada
            timeout_seconds: Timeout em segundos
            operation_name: Nome da operação para logs
            
        Returns:
            Resultado da operação
            
        Raises:
            LlmError: Se a operação exceder o timeout
        """
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = operation_func()
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            logger.error(f"Timeout de {timeout_seconds}s excedido para {operation_name}")
            raise LlmError(f"Timeout de {timeout_seconds}s excedido para {operation_name}")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Verifica se um erro é recuperável e deve ser tentado novamente.
        
        Args:
            error: Exceção a ser verificada
            
        Returns:
            True se o erro for recuperável
        """
        # Erros de rede/conectividade
        if isinstance(error, (ServiceUnavailable, DeadlineExceeded, InternalServerError)):
            return True
            
        # Erros de string que indicam problemas de conectividade
        error_str = str(error).lower()
        network_errors = [
            "connection reset by peer",
            "connection refused", 
            "timeout",
            "503",
            "502",
            "504",
            "network",
            "dns",
            "ssl",
            "certificate"
        ]
        
        return any(net_error in error_str for net_error in network_errors)
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calcula o delay para retry usando exponential backoff com jitter.
        
        Args:
            attempt: Número da tentativa (0-indexed)
            
        Returns:
            Delay em segundos
        """
        # Exponential backoff: base * (2 ^ attempt)
        delay = self.retry_delay_base * (2 ** attempt)
        
        # Adicionar jitter (randomização) para evitar thundering herd
        jitter = random.uniform(0.1, 0.5) * delay
        delay += jitter
        
        # Aplicar limite máximo
        return min(delay, self.retry_delay_max)
    
    def _retry_with_backoff(self, operation_name: str, operation_func):
        """
        Executa uma operação com retry e exponential backoff.
        
        Args:
            operation_name: Nome da operação para logs
            operation_func: Função a ser executada
            
        Returns:
            Resultado da operação
            
        Raises:
            LlmError: Se todas as tentativas falharem
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return operation_func()
                
            except Exception as e:
                last_error = e
                
                # Se não for um erro recuperável, falhar imediatamente
                if not self._is_retryable_error(e):
                    logger.error(f"{operation_name} falhou com erro não recuperável: {e}")
                    raise LlmError(f"Erro não recuperável em {operation_name}: {str(e)}")
                
                # Se for a última tentativa, falhar
                if attempt == self.max_retries - 1:
                    logger.error(f"{operation_name} falhou após {self.max_retries} tentativas: {e}")
                    break
                
                # Calcular delay e aguardar
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"{operation_name} falhou na tentativa {attempt + 1}/{self.max_retries}: {e}. "
                    f"Tentando novamente em {delay:.2f}s..."
                )
                time.sleep(delay)
        
        # Se chegou até aqui, todas as tentativas falharam
        raise LlmError(f"Falha em {operation_name} após {self.max_retries} tentativas: {str(last_error)}")

    def upload_file(self, file_path: str) -> str:
        """
        Faz upload de arquivo para o Gemini com retry automático.
        
        Args:
            file_path: Caminho para o arquivo local
            
        Returns:
            ID do arquivo no Gemini
            
        Raises:
            LlmError: Se falhar no upload após todas as tentativas
        """
        def _upload_operation():
            def _do_upload():
                logger.info(f"Fazendo upload do arquivo: {file_path}")
                uploaded_file = genai.upload_file(file_path)
                logger.info(f"Upload concluído. File ID: {uploaded_file.name}")
                return uploaded_file.name
            
            return self._with_timeout(_do_upload, self.upload_timeout, "upload de arquivo")
        
        return self._retry_with_backoff("upload de arquivo", _upload_operation)

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

            # Obter arquivo do Gemini com retry
            def _get_file_operation():
                return genai.get_file(context_file_id)
            
            uploaded_file = self._retry_with_backoff("obtenção de arquivo", _get_file_operation)
            
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
            
            # Operação de geração com retry
            def _generation_operation():
                def _do_generation():
                    response = self.model.generate_content(
                        [uploaded_file, prompt],
                        generation_config=generation_config,
                        safety_settings=safety_settings
                    )
                    
                    if not response.text:
                        raise LlmError("Resposta vazia do modelo")
                    
                    # Tentar parsear JSON
                    try:
                        result = json.loads(response.text)
                        logger.info("Geração e parsing JSON bem-sucedidos")
                        return result
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON inválido na resposta: {e}")
                        logger.debug(f"Resposta recebida: {response.text[:500]}...")
                        raise LlmError(f"Resposta não é um JSON válido: {e}")
                
                return self._with_timeout(_do_generation, self.generation_timeout, "geração de conteúdo")
            
            return self._retry_with_backoff("geração de conteúdo", _generation_operation)
                        
        except LlmError:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado na extração: {e}")
            raise LlmError(f"Erro inesperado: {str(e)}")
