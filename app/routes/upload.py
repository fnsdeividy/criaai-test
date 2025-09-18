"""
Rota para upload de arquivos PDF com segurança aprimorada.
"""
import asyncio
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
from app.core.task_manager import task_manager, TaskStatus

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
        # ContentValidator.validate_case_id já levanta ValidationError se inválido
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
    
    # Validar estrutura do PDF se habilitado
    if settings.validate_pdf_structure:
        try:
            pdf_info = FileValidator.validate_pdf_structure(str(temp_path))
            logger.info(f"PDF estruturalmente válido: {pdf_info['pages']} páginas")
        except ValidationError as e:
            # Remover arquivo inválido
            try:
                temp_path.unlink()
            except:
                pass
            raise e
    
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


@router.get("/status/{task_id}")
async def get_upload_status(task_id: str):
    """Obtém o status de uma tarefa de upload."""
    task_info = task_manager.get_task(task_id)
    
    if not task_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada"
        )
    
    return task_info.to_dict()


@router.post("/quick", status_code=status.HTTP_202_ACCEPTED)
async def upload_quick_start(
    file: UploadFile = File(..., description="Arquivo PDF para processamento"),
    case_id: Optional[str] = None
):
    """
    Inicia upload de forma ultra-rápida.
    Salva o arquivo imediatamente e processa depois.
    """
    temp_file_path = None
    
    try:
        # Validação mínima para resposta rápida
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Arquivo é obrigatório"
            )
        
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Apenas arquivos PDF são aceitos"
            )
        
        # Criar tarefa imediatamente
        task_id = task_manager.create_task("pdf_upload")
        
        # Salvar arquivo IMEDIATAMENTE (não em background)
        validated_case_id = _process_case_id(case_id) if case_id else FileValidator.generate_secure_case_id()
        temp_path = FileValidator.create_secure_temp_path(file.filename)
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar rapidamente
        file_content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(file_content)
        
        temp_file_path = temp_path
        logger.info(f"Arquivo salvo imediatamente: {temp_path} ({len(file_content)} bytes)")
        
        # AGORA processar em background
        asyncio.create_task(_process_saved_file(task_id, temp_file_path, validated_case_id))
        
        # Resposta imediata
        return {
            "task_id": task_id,
            "status": "accepted",
            "message": f"Upload de {len(file_content)} bytes recebido. Processamento em background.",
            "status_url": f"/upload/status/{task_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no upload rápido: {e}")
        # Cleanup se deu erro
        if temp_file_path:
            _cleanup_temp_file(temp_file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post("/async", status_code=status.HTTP_202_ACCEPTED)
async def upload_async(
    file: UploadFile = File(..., description="Arquivo PDF para processamento"),
    case_id: Optional[str] = None,
    use_case: CreateProcessFromUploadUseCase = Depends(get_create_process_from_upload_use_case)
):
    """
    Inicia upload assíncrono de PDF.
    
    Retorna um task_id que pode ser usado para acompanhar o progresso.
    """
    try:
        # Validação rápida inicial
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Arquivo é obrigatório"
            )
        
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Apenas arquivos PDF são aceitos"
            )
        
        # Criar tarefa assíncrona
        task_id = task_manager.create_task("pdf_upload")
        
        # Para arquivos grandes, não ler todo o conteúdo de uma vez
        # Apenas fazer validação básica rápida
        
        # Executar processamento em background (arquivo será lido lá)
        asyncio.create_task(_process_upload_async(task_id, file, case_id, use_case))
        
        return {
            "task_id": task_id,
            "status": "accepted",
            "message": "Upload iniciado. Use /upload/status/{task_id} para acompanhar o progresso.",
            "status_url": f"/upload/status/{task_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao iniciar upload assíncrono: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


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


async def _process_upload_async(
    task_id: str,
    file: UploadFile,
    case_id: Optional[str],
    use_case: CreateProcessFromUploadUseCase
):
    """
    Processa upload de forma assíncrona com atualizações de progresso.
    """
    temp_file_path: Optional[Path] = None
    
    try:
        # Atualizar progresso: validação
        task_manager.update_task(task_id, progress=10, message="Validando arquivo...")
        
        # 1. Validações básicas
        if not file or not file.filename:
            raise ValidationError("Arquivo é obrigatório")
        
        if file.content_type != "application/pdf":
            raise ValidationError("Apenas arquivos PDF são aceitos")
        
        # 2. Processar case_id
        task_manager.update_task(task_id, progress=10, message="Processando case_id...")
        validated_case_id = _process_case_id(case_id)
        
        # 3. Validar tamanho com streaming (sem carregar tudo na memória)
        task_manager.update_task(task_id, progress=20, message="Validando tamanho do arquivo...")
        FileValidator.validate_file_size_streaming(file)
        
        # 4. Salvar arquivo usando streaming
        task_manager.update_task(task_id, progress=30, message="Salvando arquivo...")
        temp_path = FileValidator.create_secure_temp_path(file.filename)
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar arquivo em chunks para não sobrecarregar memória
        total_size = 0
        pdf_validated = False
        
        with open(temp_path, "wb") as f:
            # Reset file pointer
            await file.seek(0)
            
            while True:
                chunk = await file.read(8192)  # 8KB chunks
                if not chunk:
                    break
                
                # Validar magic bytes PDF no primeiro chunk
                if not pdf_validated:
                    if not chunk.startswith(b"%PDF-"):
                        raise ValidationError("Arquivo não é um PDF válido")
                    pdf_validated = True
                
                f.write(chunk)
                total_size += len(chunk)
                
                # Atualizar progresso durante o salvamento
                if total_size % (1024 * 1024) == 0:  # A cada 1MB
                    progress = min(30 + (total_size / (14 * 1024 * 1024)) * 20, 50)
                    task_manager.update_task(task_id, progress=int(progress), 
                                           message=f"Salvando arquivo... {total_size // (1024*1024)}MB")
        
        logger.info(f"Arquivo salvo: {temp_path} ({total_size} bytes)")
        temp_file_path = temp_path
        
        # 4. Executar processamento
        task_manager.update_task(task_id, progress=50, message="Processando com IA...")
        result = await _process_upload(temp_file_path, validated_case_id, use_case)
        
        # 5. Concluir
        task_manager.complete_task(task_id, result.model_dump())
        
    except Exception as e:
        logger.error(f"Erro no processamento assíncrono: {e}", exc_info=True)
        task_manager.fail_task(task_id, str(e))
    finally:
        # Cleanup garantido
        if temp_file_path:
            _cleanup_temp_file(temp_file_path)


async def _save_and_process_later(
    task_id: str,
    file: UploadFile,
    case_id: Optional[str]
):
    """
    Salva arquivo e processa depois (ultra-rápido).
    """
    temp_file_path: Optional[Path] = None
    
    try:
        # 1. Processar case_id
        task_manager.update_task(task_id, progress=5, message="Iniciando...")
        validated_case_id = _process_case_id(case_id) if case_id else FileValidator.generate_secure_case_id()
        
        # 2. Criar arquivo temporário
        task_manager.update_task(task_id, progress=10, message="Preparando arquivo...")
        temp_path = FileValidator.create_secure_temp_path(file.filename)
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 3. Salvar arquivo rapidamente
        task_manager.update_task(task_id, progress=20, message="Salvando arquivo...")
        
        # Reset file pointer
        await file.seek(0)
        
        with open(temp_path, "wb") as f:
            while True:
                chunk = await file.read(8192)  # 8KB chunks
                if not chunk:
                    break
                f.write(chunk)
        
        temp_file_path = temp_path
        logger.info(f"Arquivo salvo rapidamente: {temp_path}")
        
        # 4. Agora processar com IA
        task_manager.update_task(task_id, progress=50, message="Processando com IA...")
        
        # Obter use case
        use_case = get_create_process_from_upload_use_case()
        
        # Processar
        result = await _process_upload(temp_file_path, validated_case_id, use_case)
        
        # 5. Concluir
        task_manager.complete_task(task_id, result.model_dump())
        
    except Exception as e:
        logger.error(f"Erro no processamento rápido: {e}", exc_info=True)
        task_manager.fail_task(task_id, str(e))
    finally:
        # Cleanup garantido
        if temp_file_path:
            _cleanup_temp_file(temp_file_path)


async def _process_saved_file(
    task_id: str,
    temp_file_path: Path,
    case_id: str
):
    """
    Processa arquivo já salvo.
    """
    try:
        task_manager.update_task(task_id, progress=30, message="Validando arquivo salvo...")
        
        # Validar se arquivo existe e é PDF
        if not temp_file_path.exists():
            raise ValidationError("Arquivo temporário não encontrado")
        
        # Ler início do arquivo para validar PDF
        with open(temp_file_path, "rb") as f:
            header = f.read(1024)
            if not header.startswith(b"%PDF-"):
                raise ValidationError("Arquivo não é um PDF válido")
        
        task_manager.update_task(task_id, progress=50, message="Processando com IA...")
        
        # Obter use case e processar
        use_case = get_create_process_from_upload_use_case()
        result = await _process_upload(temp_file_path, case_id, use_case)
        
        # Concluir
        task_manager.complete_task(task_id, result.model_dump())
        
    except Exception as e:
        logger.error(f"Erro processando arquivo salvo: {e}", exc_info=True)
        task_manager.fail_task(task_id, str(e))
    finally:
        # Cleanup garantido
        if temp_file_path and temp_file_path.exists():
            _cleanup_temp_file(temp_file_path)