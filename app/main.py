"""
Ponto de entrada da aplicação FastAPI.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.settings import settings
from app.core.logging_config import setup_logging
from app.routes.extract import router as extract_router
from app.routes.upload import router as upload_router

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    logger.info("Iniciando aplicação Process Extraction API")
    logger.info(f"Configurações carregadas: {settings.api_title} v{settings.api_version}")
    
    yield
    
    # Shutdown
    logger.info("Encerrando aplicação Process Extraction API")


# Rate limiting simples em memória
request_counts = {}

async def rate_limit_middleware(request: Request, call_next):
    """Middleware simples de rate limiting."""
    # Pular rate limiting para requisições OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response
    
    client_ip = request.client.host
    current_time = time.time()
    
    # Limpar contadores antigos (mais de 1 minuto)
    request_counts[client_ip] = [
        timestamp for timestamp in request_counts.get(client_ip, [])
        if current_time - timestamp < 60
    ]
    
    # Verificar limite (mais permissivo em desenvolvimento)
    max_requests = settings.rate_limit_requests if not settings.log_level == "DEBUG" else 1000
    if len(request_counts.get(client_ip, [])) >= max_requests:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."}
        )
    
    # Adicionar timestamp atual
    if client_ip not in request_counts:
        request_counts[client_ip] = []
    request_counts[client_ip].append(current_time)
    
    response = await call_next(request)
    return response


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.log_level == "DEBUG" else None,  # Docs apenas em debug
    redoc_url="/redoc" if settings.log_level == "DEBUG" else None,
    timeout=settings.api_timeout  # Timeout configurável
)

# CORS completamente liberado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)

# Middleware de segurança
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Em produção, especificar hosts

# Rate limiting removido temporariamente para debug
# app.middleware("http")(rate_limit_middleware)

# Rota de teste para CORS
@app.get("/cors-test")
async def cors_test():
    """Rota de teste para verificar se CORS está funcionando."""
    return {
        "message": "CORS TOTALMENTE LIBERADO!",
        "allowed_origins": ["*"],
        "timestamp": "2024-09-18",
        "version": "cors_liberado_v3"
    }

# Rota simples para testar deployment
@app.get("/test-deploy")
async def test_deploy():
    """Rota simples para testar se deployment funciona."""
    import time
    return {
        "message": "Deploy funcionando!",
        "timestamp": int(time.time()),
        "version": "deploy_test_v1"
    }

# Registrar routers
app.include_router(extract_router)
app.include_router(upload_router)


@app.get("/", tags=["health"])
async def root():
    """Endpoint de health check."""
    return {
        "message": "Process Extraction API está funcionando",
        "version": settings.api_version,
        "status": "healthy"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint de verificação de saúde da aplicação."""
    return {
        "status": "healthy",
        "version": settings.api_version,
        "service": "process-extraction-api"
    }


@app.get("/db-status", tags=["debug"])
async def db_status():
    """Verifica o status do banco de dados."""
    from app.core.dependencies import get_database_manager, get_process_repository
    
    db_manager = get_database_manager()
    repository = get_process_repository()
    
    return {
        "database_url": settings.database_url[:50] + "..." if len(settings.database_url) > 50 else settings.database_url,
        "database_manager_type": str(type(db_manager).__name__),
        "repository_type": str(type(repository).__name__),
        "is_mock": "Mock" in str(type(repository).__name__),
        "session_available": db_manager.get_session() is not None
    }


@app.post("/test-persist", tags=["debug"])
async def test_persist():
    """Testa persistência diretamente no banco."""
    from app.core.dependencies import get_process_repository
    import uuid
    from datetime import datetime
    
    repository = get_process_repository()
    
    test_case_id = f"test_{uuid.uuid4().hex[:8]}"
    test_payload = {
        "resume": "Teste de persistência no banco de dados",
        "timeline": [
            {
                "event_id": 0,
                "event_name": "Teste",
                "event_description": "Evento de teste",
                "event_date": "2024-09-18",
                "event_page_init": 1,
                "event_page_end": 1
            }
        ],
        "evidence": [
            {
                "evidence_id": 0,
                "evidence_name": "Evidência de teste",
                "evidence_flaw": "Sem inconsistências",
                "evidence_page_init": 1,
                "evidence_page_end": 1
            }
        ],
        "persisted_at": datetime.utcnow()
    }
    
    try:
        repository.persist_extraction(test_case_id, test_payload)
        
        # Tentar recuperar
        saved_data = repository.get_by_case_id(test_case_id)
        
        return {
            "success": True,
            "test_case_id": test_case_id,
            "repository_type": str(type(repository).__name__),
            "persisted": True,
            "retrieved": saved_data is not None,
            "data": saved_data
        }
    except Exception as e:
        return {
            "success": False,
            "test_case_id": test_case_id,
            "repository_type": str(type(repository).__name__),
            "error": str(e),
            "error_type": str(type(e).__name__)
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
