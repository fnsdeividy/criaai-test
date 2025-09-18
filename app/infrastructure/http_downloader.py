"""
Cliente HTTP para download de arquivos.
"""
import logging
import os
from pathlib import Path
from typing import Any
import httpx

from app.core.exceptions import DownloadError

logger = logging.getLogger(__name__)


class HttpDownloader:
    """Cliente para download de arquivos via HTTP."""

    def __init__(self, timeout: int = 30):
        """
        Inicializa o downloader.
        
        Args:
            timeout: Timeout em segundos para requisições
        """
        self.timeout = timeout

    def download_pdf(self, url: str, output_path: str) -> str:
        """
        Baixa um PDF de uma URL.
        
        Args:
            url: URL do PDF
            output_path: Caminho onde salvar o arquivo
            
        Returns:
            Caminho do arquivo baixado
            
        Raises:
            DownloadError: Se falhar no download
        """
        try:
            logger.info(f"Iniciando download de: {url}")
            
            # Criar diretório se não existir
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                
                # Verificar se é PDF
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" not in content_type:
                    # Verificar pelo conteúdo (header PDF)
                    if not response.content.startswith(b"%PDF"):
                        logger.warning(f"Conteúdo pode não ser PDF. Content-Type: {content_type}")
                
                # Salvar arquivo
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                logger.info(f"Download concluído. Arquivo salvo em: {output_path} ({file_size} bytes)")
                
                return output_path
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP no download: {e.response.status_code} - {e.response.text}")
            raise DownloadError(f"Erro HTTP {e.response.status_code}: {url}")
        except httpx.TimeoutException:
            logger.error(f"Timeout no download: {url}")
            raise DownloadError(f"Timeout ao baixar arquivo: {url}")
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão no download: {e}")
            raise DownloadError(f"Erro de conexão: {url}")
        except OSError as e:
            logger.error(f"Erro ao salvar arquivo: {e}")
            raise DownloadError(f"Erro ao salvar arquivo: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado no download: {e}")
            raise DownloadError(f"Erro inesperado: {str(e)}")
