-- Script de inicialização do banco PostgreSQL
-- Este arquivo é executado automaticamente quando o container PostgreSQL é criado

-- Criar extensões úteis
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Comentário sobre a tabela principal (será criada pelo SQLAlchemy)
COMMENT ON DATABASE process_extractions IS 'Banco de dados para Process Extraction API - Extração de dados de processos jurídicos usando IA';
