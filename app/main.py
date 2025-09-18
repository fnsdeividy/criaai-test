"""
Ponto de entrada da aplicação FastAPI.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
