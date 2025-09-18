"""
Configuração de logging da aplicação.
"""
import logging
import sys
from typing import Dict, Any

from app.core.settings import settings


def setup_logging() -> None:
    """Configura o sistema de logging da aplicação."""
    
    # Configurar formato do log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configurar nível de log
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configurar logging básico
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar loggers específicos
    loggers_config = {
        "httpx": logging.WARNING,  # Reduzir verbosidade do httpx
        "urllib3": logging.WARNING,  # Reduzir verbosidade do urllib3
        "sqlalchemy.engine": logging.WARNING,  # Reduzir verbosidade do SQLAlchemy
    }
    
    for logger_name, level in loggers_config.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # Log de inicialização
    logger = logging.getLogger(__name__)
    logger.info(f"Sistema de logging configurado. Nível: {settings.log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
