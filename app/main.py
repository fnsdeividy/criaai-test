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

# Configurar CORS - Versão robusta para produção
import os

# Middleware de debug personalizado para CORS
@app.middleware("http")
async def cors_debug_middleware(request: Request, call_next):
    """Debug middleware para CORS."""
    origin = request.headers.get("origin")
    method = request.method
    
    print(f"🔍 Request: {method} {request.url}")
    print(f"🔍 Origin: {origin}")
    print(f"🔍 Headers: {dict(request.headers)}")
    
    if method == "OPTIONS":
        # Handle preflight manually
        response = JSONResponse({"message": "CORS preflight OK"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "3600"
        print(f"🔍 Preflight response headers: {dict(response.headers)}")
        return response
    
    response = await call_next(request)
    
    # Add CORS headers to all responses
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    print(f"🔍 Response headers: {dict(response.headers)}")
    return response

# Middleware de segurança
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Em produção, especificar hosts

# Rate limiting
app.middleware("http")(rate_limit_middleware)

# Rota de teste para CORS
@app.get("/cors-test")
async def cors_test():
    """Rota de teste para verificar se CORS está funcionando."""
    return {
        "message": "CORS está funcionando!",
        "allowed_origins": ["*"],
        "timestamp": "2024-09-18",
        "debug": "versao_simplificada_v2"
    }

# Rota para debug de headers
@app.get("/debug-headers")
async def debug_headers(request: Request):
    """Debug dos headers da requisição."""
    return {
        "headers": dict(request.headers),
        "origin": request.headers.get("origin"),
        "host": request.headers.get("host"),
        "method": request.method
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


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
