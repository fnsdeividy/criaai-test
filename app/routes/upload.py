"""
Rota para upload de arquivos PDF.
"""
import logging
import os
import tempfile
import time
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import ValidationError as PydanticValidationError

from app.application.dtos import UploadRequest, ExtractResponse
from app.application.use_cases import CreateProcessFromUploadUseCase
from app.core.exceptions import LlmError, RepositoryError, ValidationError
from app.core.dependencies import get_create_process_from_upload_use_case

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])


@router.get("/test")
async def test_upload_route():
    """Teste básico para verificar se a rota está funcionando."""
    try:
        from app.core.dependencies import get_create_process_from_upload_use_case
        use_case = get_create_process_from_upload_use_case()
        return {"status": "ok", "use_case": str(type(use_case))}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("", response_model=ExtractResponse, status_code=status.HTTP_200_OK)
async def extract_from_upload(
    file: UploadFile = File(...),
    case_id: str = None,
    use_case: CreateProcessFromUploadUseCase = Depends(get_create_process_from_upload_use_case)
) -> ExtractResponse:
    """
    Extrai dados estruturados de um arquivo PDF enviado via upload.
    
    Args:
        file: Arquivo PDF enviado
        case_id: ID único do processo (opcional, será gerado se não fornecido)
        use_case: Use case para processamento
        
    Returns:
        Dados extraídos e persistidos
        
    Raises:
        HTTPException: Em caso de erro no processamento
    """
    try:
        logger.info(f"Recebido upload de arquivo: {file.filename}")
        logger.info(f"Content-Type: {file.content_type}")
        
        # Validar tipo de arquivo
        if not file.content_type == "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Apenas arquivos PDF são aceitos"
            )
        
        # Validar tamanho do arquivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Arquivo muito grande. Máximo permitido: 10MB"
            )
        
        # Gerar case_id se não fornecido
        if not case_id:
            case_id = f"upload_{int(time.time())}"
        
        # Salvar arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(contents)
            temp_file_path = tmp_file.name
        
        try:
            logger.info(f"Arquivo salvo temporariamente: {temp_file_path}")
            
            # Criar request para upload
            upload_request = UploadRequest(
                case_id=case_id,
                file_path=temp_file_path
            )
            logger.info(f"UploadRequest criado: {upload_request}")
            
            # Executar processamento
            logger.info("Iniciando processamento com use case...")
            result = use_case.execute(upload_request)
            
            logger.info(f"Upload processado com sucesso: {file.filename}")
            return result
            
        finally:
            # Limpar arquivo temporário
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário: {e}")
                
    except HTTPException:
        raise
    except PydanticValidationError as e:
        logger.error(f"Erro de validação no upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Dados de entrada inválidos: {str(e)}"
        )
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
        logger.error(f"Erro inesperado no upload: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )
