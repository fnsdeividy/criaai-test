"""
Rotas para extração de processos jurídicos.
"""
import logging
import os
import tempfile
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import ValidationError as PydanticValidationError

from app.application.dtos import ExtractRequest, ExtractResponse
from app.application.use_cases import CreateProcessUseCase, GetProcessUseCase
from app.core.exceptions import DownloadError, LlmError, RepositoryError, ValidationError
from app.core.dependencies import get_create_process_use_case, get_get_process_use_case

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/extract", tags=["extract"])


@router.post("", response_model=ExtractResponse, status_code=status.HTTP_200_OK)
async def extract_process(
    request: ExtractRequest,
    use_case: CreateProcessUseCase = Depends(get_create_process_use_case)
) -> ExtractResponse:
    """
    Extrai dados estruturados de um processo jurídico a partir de PDF.
    
    Args:
        request: Dados da requisição (URL do PDF e ID do caso)
        use_case: Use case para processamento
        
    Returns:
        Dados extraídos e persistidos
        
    Raises:
        HTTPException: Em caso de erro no processamento
    """
    try:
        logger.info(f"Recebida requisição de extração para caso: {request.case_id}")
        
        result = use_case.execute(request)
        
        logger.info(f"Extração concluída com sucesso para caso: {request.case_id}")
        return result
        
    except PydanticValidationError as e:
        logger.error(f"Erro de validação na requisição: {e}")
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
    except DownloadError as e:
        logger.error(f"Erro no download: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Falha no download do PDF: {str(e)}"
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
        logger.error(f"Erro inesperado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get("/{case_id}", response_model=ExtractResponse, status_code=status.HTTP_200_OK)
async def get_process(
    case_id: str,
    use_case: GetProcessUseCase = Depends(get_get_process_use_case)
) -> ExtractResponse:
    """
    Recupera dados de um processo existente.
    
    Args:
        case_id: ID único do processo
        use_case: Use case para consulta
        
    Returns:
        Dados do processo
        
    Raises:
        HTTPException: Se processo não for encontrado ou erro interno
    """
    try:
        logger.info(f"Recebida consulta para caso: {case_id}")
        
        result = use_case.execute(case_id)
        
        if not result:
            logger.info(f"Caso não encontrado: {case_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processo não encontrado: {case_id}"
            )
        
        logger.info(f"Consulta concluída para caso: {case_id}")
        return result
        
    except HTTPException:
        raise
    except RepositoryError as e:
        logger.error(f"Erro no repositório: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na consulta dos dados"
        )
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
