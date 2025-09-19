"""
Configuração e modelos do banco de dados.
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Import psycopg2 to ensure PostgreSQL dialect is available for SQLAlchemy
try:
    import psycopg2  # noqa: F401
except ImportError:
    pass  # psycopg2 not available, will fall back to mock

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class ProcessExtraction(Base):
    """Modelo para armazenar extrações de processos."""
    
    __tablename__ = "process_extractions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(100), unique=True, nullable=False, index=True)
    resume = Column(Text, nullable=False)
    timeline = Column(Text, nullable=False)  # JSON como texto para compatibilidade SQLite
    evidence = Column(Text, nullable=False)  # JSON como texto para compatibilidade SQLite
    persisted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para dicionário."""
        return {
            "case_id": self.case_id,
            "resume": self.resume,
            "timeline": json.loads(self.timeline) if isinstance(self.timeline, str) else self.timeline,
            "evidence": json.loads(self.evidence) if isinstance(self.evidence, str) else self.evidence,
            "persisted_at": self.persisted_at
        }


class DatabaseManager:
    """Gerenciador do banco de dados."""

    def __init__(self, database_url: str):
        """
        Inicializa o gerenciador.

        Args:
            database_url: URL de conexão com o banco
        """
        # Convert postgres:// to postgresql:// for SQLAlchemy compatibility
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Cria as tabelas no banco de dados."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self) -> Session:
        """Retorna uma nova sessão do banco."""
        return self.SessionLocal()
