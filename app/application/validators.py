"""
Validadores de segurança para a aplicação.
"""
import logging
import magic
import hashlib
import uuid
from pathlib import Path
from typing import BinaryIO, Tuple
from fastapi import UploadFile

from app.core.settings import settings
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Constantes de segurança
MAX_FILE_SIZE_BYTES = settings.max_file_size_mb * 1024 * 1024
ALLOWED_MIME_TYPES = {"application/pdf"}
PDF_MAGIC_BYTES = b"%PDF-"
CHUNK_SIZE = 8192  # 8KB chunks para streaming


class FileValidator:
    """Validador seguro de arquivos."""
    
    @staticmethod
    def generate_secure_case_id() -> str:
        """
        Gera um case_id seguro e único.
        
        Returns:
            ID único e imprevisível
        """
        return f"upload_{uuid.uuid4().hex[:16]}"
    
    @staticmethod
    def validate_file_size_streaming(file: UploadFile) -> None:
        """
        Valida tamanho do arquivo usando streaming para evitar DoS.
        
        Args:
            file: Arquivo enviado
            
        Raises:
            ValidationError: Se arquivo for muito grande
        """
        total_size = 0
        
        # Reset file pointer
        file.file.seek(0)
        
        while True:
            chunk = file.file.read(CHUNK_SIZE)
            if not chunk:
                break
                
            total_size += len(chunk)
            
            if total_size > MAX_FILE_SIZE_BYTES:
                raise ValidationError(
                    f"Arquivo muito grande. Máximo permitido: {settings.max_file_size_mb}MB"
                )
        
        # Reset file pointer para uso posterior
        file.file.seek(0)
        logger.info(f"Arquivo validado: {total_size} bytes")
    
    @staticmethod
    def validate_pdf_content(file_content: bytes) -> None:
        """
        Valida se o conteúdo é realmente um PDF.
        
        Args:
            file_content: Conteúdo do arquivo
            
        Raises:
            ValidationError: Se não for um PDF válido
        """
        # Verificar magic bytes
        if not file_content.startswith(PDF_MAGIC_BYTES):
            raise ValidationError("Arquivo não é um PDF válido (magic bytes)")
        
        # Verificar com python-magic se disponível
        try:
            mime_type = magic.from_buffer(file_content[:1024], mime=True)
            if mime_type not in ALLOWED_MIME_TYPES:
                raise ValidationError(f"Tipo MIME não permitido: {mime_type}")
        except ImportError:
            logger.warning("python-magic não disponível, usando apenas magic bytes")
        
        logger.info("Conteúdo PDF validado com sucesso")
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Sanitiza e valida nome do arquivo.
        
        Args:
            filename: Nome original do arquivo
            
        Returns:
            Nome sanitizado
            
        Raises:
            ValidationError: Se filename for inválido
        """
        if not filename:
            raise ValidationError("Nome do arquivo é obrigatório")
        
        # Remover caracteres perigosos
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        sanitized = "".join(c for c in filename if c in safe_chars)
        
        if not sanitized:
            raise ValidationError("Nome do arquivo contém apenas caracteres inválidos")
        
        # Garantir extensão .pdf
        if not sanitized.lower().endswith(".pdf"):
            sanitized += ".pdf"
        
        return sanitized
    
    @staticmethod
    def create_secure_temp_path(filename: str) -> Path:
        """
        Cria caminho seguro para arquivo temporário.
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            Caminho seguro para o arquivo
        """
        # Sanitizar filename
        safe_filename = FileValidator.validate_filename(filename)
        
        # Criar nome único para evitar colisões
        unique_name = f"{uuid.uuid4().hex}_{safe_filename}"
        
        # Garantir que está dentro do diretório temporário configurado
        temp_dir = Path(settings.tmp_dir).resolve()
        temp_path = temp_dir / unique_name
        
        # Verificar se não há path traversal
        if not str(temp_path).startswith(str(temp_dir)):
            raise ValidationError("Path traversal detectado")
        
        return temp_path


class ContentValidator:
    """Validador de conteúdo de requisições."""
    
    @staticmethod
    def validate_case_id(case_id: str) -> str:
        """
        Valida e sanitiza case_id.
        
        Args:
            case_id: ID do caso
            
        Returns:
            Case ID validado
            
        Raises:
            ValidationError: Se case_id for inválido
        """
        if not case_id or not case_id.strip():
            raise ValidationError("case_id não pode estar vazio")
        
        # Remover espaços e caracteres perigosos
        sanitized = case_id.strip()
        
        # Validar comprimento
        if len(sanitized) > 100:
            raise ValidationError("case_id muito longo (máximo 100 caracteres)")
        
        # Validar caracteres permitidos
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        if not all(c in allowed_chars for c in sanitized):
            raise ValidationError("case_id contém caracteres não permitidos")
        
        return sanitized
