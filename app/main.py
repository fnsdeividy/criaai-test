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

# Middleware de segurança
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Em produção, especificar hosts

# Rate limiting
app.middleware("http")(rate_limit_middleware)

# Configurar CORS - Versão robusta para produção
import os

# Configurar origens permitidas para CORS
# Lista padrão de origens confiáveis
default_origins = [
    "https://criaai-test.vercel.app",
    # URLs dinâmicas do Vercel (frontend)
    "https://criaai-test-git-main-fnsdeividys-projects.vercel.app",
    "https://criaai-test-fnsdeividys-projects.vercel.app",
    # URLs dinâmicas do Vercel (backend) - caso sejam usadas como frontend
    "https://criaai-test-afe7-xscdfc12f-fnsdeividys-projects.vercel.app",
    # Desenvolvimento local
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080"
]

# Adicionar suporte para URLs dinâmicas do Vercel baseadas no host atual
current_host = os.getenv("VERCEL_URL")
if current_host:
    # Adicionar a URL atual e variações comuns
    vercel_urls = [
        f"https://{current_host}",
        "https://criaai-test.vercel.app",  # URL principal
    ]
    default_origins.extend(vercel_urls)
    print(f"🔧 URLs Vercel detectadas: {vercel_urls}")

# Tentar obter origens do ambiente
env_origins = os.getenv("ALLOWED_ORIGINS", "")
if env_origins:
    try:
        import json
        cors_origins = json.loads(env_origins)
        print(f"🔧 CORS Origins do ENV: {cors_origins}")
    except:
        # Se falhar o parse, usar lista padrão
        cors_origins = default_origins
        print(f"🔧 CORS Origins fallback (parse error): {cors_origins}")
else:
    # Usar lista padrão em vez de wildcard
    cors_origins = default_origins
    print(f"🔧 CORS Origins padrão: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,  # Sempre permitir credentials com origens específicas
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type", 
        "Authorization", 
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    max_age=3600,
)

# Rota de teste para CORS
@app.get("/cors-test")
async def cors_test():
    """Rota de teste para verificar se CORS está funcionando."""
    return {
        "message": "CORS está funcionando!",
        "allowed_origins": cors_origins,
        "timestamp": "2024-09-18"
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
