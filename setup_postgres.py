#!/usr/bin/env python3
"""
Script para configurar banco de dados PostgreSQL.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

def create_database():
    """Cria o banco de dados se não existir."""
    
    # URL base para conectar ao PostgreSQL (sem especificar database)
    base_url = "postgresql://postgres:postgres@localhost:5432/postgres"
    database_name = "process_extractions"
    
    try:
        print("🔍 Conectando ao PostgreSQL...")
        engine = create_engine(base_url)
        
        with engine.connect() as conn:
            # Verificar se o banco já existe
            result = conn.execute(text(
                "SELECT 1 FROM pg_database WHERE datname = :db_name"
            ), {"db_name": database_name})
            
            if result.fetchone():
                print(f"✅ Banco de dados '{database_name}' já existe")
            else:
                print(f"🔧 Criando banco de dados '{database_name}'...")
                
                # Commit any existing transaction
                conn.commit()
                
                # Create database (must be outside transaction)
                conn.execute(text("COMMIT"))
                conn.execute(text(f"CREATE DATABASE {database_name}"))
                
                print(f"✅ Banco de dados '{database_name}' criado com sucesso")
        
        engine.dispose()
        
    except OperationalError as e:
        if "database" in str(e) and "does not exist" in str(e):
            print(f"❌ Banco PostgreSQL não está rodando ou não acessível")
            print("   Certifique-se de que o PostgreSQL está instalado e rodando")
        else:
            print(f"❌ Erro de conexão: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    
    return True


def create_tables():
    """Cria as tabelas no banco de dados."""
    try:
        from app.infrastructure.database import DatabaseManager
        from app.core.settings import settings
        
        print("🔧 Criando tabelas...")
        db_manager = DatabaseManager(settings.database_url)
        db_manager.create_tables()
        print("✅ Tabelas criadas com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False
    
    return True


def test_connection():
    """Testa a conexão com o banco."""
    try:
        from app.core.settings import settings
        
        print("🔍 Testando conexão com o banco...")
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Conexão OK - PostgreSQL: {version}")
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False
    
    return True


def main():
    """Função principal."""
    print("🐘 Configuração do PostgreSQL para Process Extraction API")
    print("=" * 60)
    
    # Verificar se o módulo psycopg2 está instalado
    try:
        import psycopg2
        print("✅ Driver psycopg2 encontrado")
    except ImportError:
        print("❌ Driver psycopg2 não encontrado")
        print("   Execute: pip install psycopg2-binary")
        return False
    
    # 1. Criar banco de dados
    if not create_database():
        return False
    
    # 2. Criar tabelas
    if not create_tables():
        return False
    
    # 3. Testar conexão
    if not test_connection():
        return False
    
    print("\n🎉 Configuração do PostgreSQL concluída com sucesso!")
    print("\n📋 Próximos passos:")
    print("   1. Configure GEMINI_API_KEY no arquivo .env")
    print("   2. Execute: uvicorn app.main:app --reload")
    print("   3. Acesse: http://localhost:8000/docs")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
