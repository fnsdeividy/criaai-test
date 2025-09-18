"""
Rota para upload de arquivos PDF com segurança aprimorada.
"""
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import ValidationError as PydanticValidationError

from app.application.dtos import UploadRequest, ExtractResponse
from app.application.use_cases import CreateProcessFromUploadUseCase
from app.application.validators import FileValidator, ContentValidator
from app.core.exceptions import LlmError, RepositoryError, ValidationError
from app.core.dependencies import get_create_process_from_upload_use_case
from app.core.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])


async def _validate_upload_request(file: UploadFile, case_id: Optional[str]) -> None:
    """
    Valida requisição de upload de forma segura.
    
    Args:
        file: Arquivo enviado
        case_id: ID do caso (opcional)
        
    Raises:
        ValidationError: Se validação falhar
    """
    # Validar presença do arquivo
    if not file or not file.filename:
        raise ValidationError("Arquivo é obrigatório")
    
    # Validar Content-Type (primeira linha de defesa)
    if file.content_type != "application/pdf":
        raise ValidationError("Apenas arquivos PDF são aceitos")
    
    # Validar tamanho usando streaming (evita DoS)
    FileValidator.validate_file_size_streaming(file)
    
    logger.info(f"Validação inicial concluída: {file.filename}")


def _process_case_id(case_id: Optional[str]) -> str:
    """
    Processa e valida case_id.
    
    Args:
        case_id: ID do caso (opcional)
        
    Returns:
        Case ID validado ou gerado
    """
    if case_id:
        return ContentValidator.validate_case_id(case_id)
    else:
        # Gerar ID seguro
        return FileValidator.generate_secure_case_id()


async def _save_file_securely(file: UploadFile) -> Path:
    """
    Salva arquivo de forma segura com validação de conteúdo.
    
    Args:
        file: Arquivo a ser salvo
        
    Returns:
        Caminho do arquivo salvo
        
    Raises:
        ValidationError: Se arquivo for inválido
    """
    # Criar caminho seguro
    temp_path = FileValidator.create_secure_temp_path(file.filename)
    
    # Criar diretório se necessário
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ler e validar conteúdo
    file_content = await file.read()
    
    # Validar se é realmente um PDF
    FileValidator.validate_pdf_content(file_content)
    
    # Salvar arquivo
    with open(temp_path, "wb") as f:
        f.write(file_content)
    
    logger.info(f"Arquivo salvo com segurança: {temp_path}")
    return temp_path


async def _process_upload(
    temp_file_path: Path, 
    case_id: str, 
    use_case: CreateProcessFromUploadUseCase
) -> ExtractResponse:
    """
    Processa upload usando use case.
    
    Args:
        temp_file_path: Caminho do arquivo temporário
        case_id: ID do caso
        use_case: Use case para processamento
        
    Returns:
        Resultado do processamento
    """
    upload_request = UploadRequest(
        case_id=case_id,
        file_path=str(temp_file_path)
    )
    
    logger.info(f"Iniciando processamento para caso: {case_id}")
    return use_case.execute(upload_request)


def _cleanup_temp_file(temp_file_path: Path) -> None:
    """
    Remove arquivo temporário de forma segura.
    
    Args:
        temp_file_path: Caminho do arquivo a ser removido
    """
    try:
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()
            logger.info(f"Arquivo temporário removido: {temp_file_path}")
    except Exception as e:
        logger.warning(f"Erro ao remover arquivo temporário {temp_file_path}: {e}")


@router.get("/test")
async def test_upload_route():
    """Teste básico para verificar se a rota está funcionando."""
    try:
        use_case = get_create_process_from_upload_use_case()
        return {
            "status": "ok", 
            "use_case": str(type(use_case)),
            "max_file_size_mb": settings.max_file_size_mb
        }
    except Exception as e:
        logger.error(f"Erro no teste da rota: {e}")
        return {"status": "error", "message": str(e)}


@router.post("", response_model=ExtractResponse, status_code=status.HTTP_200_OK)
async def extract_from_upload(
    file: UploadFile = File(..., description="Arquivo PDF para processamento"),
    case_id: Optional[str] = None,
    use_case: CreateProcessFromUploadUseCase = Depends(get_create_process_from_upload_use_case)
) -> ExtractResponse:
    """
    Extrai dados estruturados de um arquivo PDF enviado via upload.
    
    Implementa validações de segurança rigorosas:
    - Validação de tipo MIME e conteúdo
    - Validação de tamanho usando streaming
    - Path traversal protection
    - Sanitização de inputs
    - Cleanup garantido de arquivos temporários
    
    Args:
        file: Arquivo PDF enviado (máx. 14MB)
        case_id: ID único do processo (opcional, será gerado se não fornecido)
        use_case: Use case para processamento
        
    Returns:
        Dados extraídos e persistidos
        
    Raises:
        HTTPException: Em caso de erro no processamento
    """
    temp_file_path: Optional[Path] = None
    
    try:
        logger.info(f"=== INÍCIO UPLOAD SEGURO ===")
        logger.info(f"Arquivo: {file.filename}, Content-Type: {file.content_type}")
        
        # 1. Validações de entrada
        await _validate_upload_request(file, case_id)
        
        # 2. Processar case_id
        validated_case_id = _process_case_id(case_id)
        logger.info(f"Case ID: {validated_case_id}")
        
        # 3. Salvar arquivo de forma segura
        temp_file_path = await _save_file_securely(file)
        
        # 4. Executar processamento
        result = await _process_upload(temp_file_path, validated_case_id, use_case)
        
        logger.info(f"=== UPLOAD CONCLUÍDO COM SUCESSO ===")
        return result
        
    except HTTPException:
        # Re-raise HTTPExceptions sem modificar
        raise
    except ValidationError as e:
        logger.error(f"Erro de validação: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except LlmError as e:
        logger.error(f"Erro no LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha na extração com IA: {str(e)}"
        )
    except RepositoryError as e:
        logger.error(f"Erro no repositório: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na persistência dos dados"
        )
    except Exception as e:
        logger.error(f"Erro inesperado no upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
    finally:
        # Cleanup garantido
        if temp_file_path:
            _cleanup_temp_file(temp_file_path)
        logger.info(f"=== FIM PROCESSAMENTO UPLOAD ===")