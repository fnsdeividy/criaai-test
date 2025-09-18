"""
Configuração e modelos do banco de dados.
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class ProcessExtraction(Base):
    """Modelo para armazenar extrações de processos."""
    
    __tablename__ = "process_extractions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(100), unique=True, nullable=False, index=True)
    resume = Column(Text, nullable=False)
    timeline = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=False)
    persisted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para dicionário."""
        return {
            "case_id": self.case_id,
            "resume": self.resume,
            "timeline": self.timeline,
            "evidence": self.evidence,
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
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Cria as tabelas no banco de dados."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self) -> Session:
        """Retorna uma nova sessão do banco."""
        return self.SessionLocal()
