"""
Repositório para persistência de processos jurídicos.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.domain.interfaces import IProcessRepository
from app.infrastructure.database import ProcessExtraction, DatabaseManager
from app.core.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class SqlAlchemyProcessRepository(IProcessRepository):
    """Repositório SQLAlchemy para processos jurídicos."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa o repositório.
        
        Args:
            db_manager: Gerenciador do banco de dados
        """
        self.db_manager = db_manager

    def persist_extraction(self, case_id: str, payload: Dict[str, Any]) -> None:
        """
        Persiste os dados extraídos de um processo.
        
        Args:
            case_id: Identificador único do processo
            payload: Dados extraídos para persistir
            
        Raises:
            RepositoryError: Se falhar na persistência
        """
        logger.info(f"🔍 SqlAlchemyProcessRepository.persist_extraction chamado para caso {case_id}")
        
        # Garantir que as tabelas existem (importante no Vercel)
        try:
            logger.info(f"🔧 Verificando/criando tabelas no banco...")
            self.db_manager.create_tables()
            logger.info(f"✅ Tabelas verificadas/criadas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise RepositoryError(f"Falha ao criar tabelas: {str(e)}")
        
        session: Session = self.db_manager.get_session()
        
        if session is None:
            logger.error(f"❌ Sessão do banco é None - usando MockDatabaseManager?")
            raise RepositoryError("Sessão do banco de dados não disponível")
            
        logger.info(f"✅ Sessão do banco obtida com sucesso")
        
        try:
            # Verificar se já existe
            logger.info(f"🔍 Verificando se processo {case_id} já existe...")
            existing = session.query(ProcessExtraction).filter_by(case_id=case_id).first()
            if existing:
                logger.info(f"⚠️ Processo {case_id} já existe, pulando persistência")
                return
            
            # Criar novo registro
            logger.info(f"🆕 Criando novo registro para processo {case_id}")
            extraction = ProcessExtraction(
                case_id=case_id,
                resume=payload["resume"],
                timeline=json.dumps(payload["timeline"], ensure_ascii=False),  # Converter para JSON string
                evidence=json.dumps(payload["evidence"], ensure_ascii=False),  # Converter para JSON string
                persisted_at=payload.get("persisted_at", datetime.utcnow())
            )
            
            logger.info(f"💾 Adicionando registro à sessão...")
            session.add(extraction)
            logger.info(f"🔄 Fazendo commit da transação...")
            session.commit()
            logger.info(f"✅ Processo {case_id} persistido com sucesso no banco!")
            
        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Processo {case_id} já existe (constraint violation)")
            # Não é erro, apenas já existe
        except Exception as e:
            session.rollback()
            logger.error(f"Erro ao persistir processo {case_id}: {e}")
            raise RepositoryError(f"Falha na persistência: {str(e)}")
        finally:
            session.close()

    def get_by_case_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera dados de um processo pelo ID.
        
        Args:
            case_id: Identificador único do processo
            
        Returns:
            Dados do processo se encontrado, None caso contrário
            
        Raises:
            RepositoryError: Se falhar na consulta
        """
        session: Session = self.db_manager.get_session()
        try:
            extraction = session.query(ProcessExtraction).filter_by(case_id=case_id).first()
            
            if extraction:
                logger.info(f"Processo {case_id} encontrado no banco")
                return extraction.to_dict()
            else:
                logger.info(f"Processo {case_id} não encontrado no banco")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao consultar processo {case_id}: {e}")
            raise RepositoryError(f"Falha na consulta: {str(e)}")
        finally:
            session.close()
