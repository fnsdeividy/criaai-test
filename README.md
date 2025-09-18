# Process Extraction API

API para extração de dados estruturados de processos jurídicos usando Google Gemini AI.

## Funcionalidades

- **Extração automatizada**: Recebe URL de PDF e extrai dados estruturados
- **IA Avançada**: Utiliza Google Gemini 1.5 para análise de documentos jurídicos
- **Dados estruturados**: Retorna resumo, timeline e evidências em formato JSON
- **Persistência**: Armazena dados extraídos em banco SQLite local
- **Idempotência**: Evita reprocessamento de casos já analisados
- **API REST**: Interface FastAPI com documentação automática

## Arquitetura

O projeto segue arquitetura em camadas com Clean Architecture:

```
app/
├── application/     # DTOs, services, use-cases
├── domain/         # Interfaces (ports) & contratos
├── infrastructure/ # Adapters (DB, LLM, HTTP)
├── routes/         # FastAPI routers
├── core/           # Config, exceptions, utils
└── main.py         # Entrypoint FastAPI
```

## Requisitos

- Python 3.11+
- PostgreSQL 12+ (rodando localmente ou remoto)
- Chave da API do Google Gemini
- Acesso à internet para download de PDFs

## Instalação

1. **Clone o repositório**:
   ```bash
   git clone <repository-url>
   cd criaai
   ```

2. **Configure PostgreSQL**:
   
   **Opção A: Docker (Recomendado para desenvolvimento)**:
   ```bash
   make docker-up
   # PostgreSQL estará disponível em localhost:5432
   ```
   
   **Opção B: Instalação local (macOS com Homebrew)**:
   ```bash
   make install-pg
   # ou manualmente: brew install postgresql && brew services start postgresql
   ```

3. **Instale as dependências**:
   ```bash
   make install
   # ou: pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**:
   ```bash
   cp env.example .env
   ```
   
   Edite o arquivo `.env` e configure:
   ```env
   GEMINI_API_KEY=sua_chave_aqui
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/process_extractions
   ```

5. **Configure o banco de dados**:
   ```bash
   make setup-db
   # ou: python setup_postgres.py
   ```

6. **Execute a aplicação**:
   ```bash
   make run
   # ou: uvicorn app.main:app --reload
   ```

A API estará disponível em: http://localhost:8000

## Documentação da API

Acesse a documentação interativa:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### POST /extract

Extrai dados estruturados de um processo jurídico.

**Request Body**:
```json
{
  "pdf_url": "https://exemplo.com/processo.pdf",
  "case_id": "0809090-86.2024.8.12.0021"
}
```

**Response (200)**:
```json
{
  "case_id": "0809090-86.2024.8.12.0021",
  "resume": "Resumo do processo...",
  "timeline": [
    {
      "event_id": 0,
      "event_name": "Petição Inicial",
      "event_description": "Petição inicial protocolada",
      "event_date": "2024-01-15",
      "event_page_init": 1,
      "event_page_end": 3
    }
  ],
  "evidence": [
    {
      "evidence_id": 0,
      "evidence_name": "Documento de Identidade",
      "evidence_flaw": null,
      "evidence_page_init": 10,
      "evidence_page_end": 11
    }
  ],
  "persisted_at": "2024-08-28T12:00:00Z"
}
```

### GET /extract/{case_id}

Recupera dados de um processo já processado.

**Response (200)**: Mesmo formato do POST
**Response (404)**: Processo não encontrado

### GET /health

Verifica saúde da aplicação.

## Códigos de Erro

- **422**: Dados de entrada inválidos (URL malformada, case_id vazio)
- **400**: Falha no download do PDF (404, timeout, etc.)
- **502**: Falha na extração com IA (erro no Gemini)
- **500**: Erro interno (persistência, validação)

## Testes

Execute os testes unitários:

```bash
pytest -v
```

Para executar com cobertura:

```bash
pytest --cov=app --cov-report=html
```

## Makefile

O projeto inclui um Makefile com comandos úteis:

```bash
make install    # Instalar dependências
make run        # Executar aplicação
make test       # Executar testes
make lint       # Executar linting (se configurado)
make clean      # Limpar arquivos temporários
```

## Estrutura dos Dados

### Timeline Events

Os eventos da timeline utilizam vocabulário jurídico apropriado:
- "Petição Inicial"
- "Citação/Intimação"
- "Audiência/Sessão"
- "Manifestação das Partes"
- "Decisão Interlocutória"
- "Sentença"
- "Recurso"
- "Despacho"

### Evidence Items

As evidências incluem:
- **evidence_name**: Nome do documento/prova
- **evidence_flaw**: Problemas identificados ("parcialmente ilegível", "sem inconsistências", etc.)
- **Páginas**: Localização no PDF original

## Configuração Avançada

### Variáveis de Ambiente

- `GEMINI_API_KEY`: Chave da API do Google Gemini (obrigatório)
- `DATABASE_URL`: URL do banco PostgreSQL (padrão: localhost)
- `TMP_DIR`: Diretório temporário (padrão: /tmp)
- `DOWNLOAD_TIMEOUT`: Timeout para downloads em segundos (padrão: 30)
- `LOG_LEVEL`: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Banco de Dados PostgreSQL

O projeto usa PostgreSQL como banco principal. Configurações padrão:

```env
# Desenvolvimento local
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/process_extractions

# Produção (exemplo)
DATABASE_URL=postgresql://user:password@host:5432/database_name
```

**Comandos úteis do PostgreSQL:**
```bash
# Conectar ao banco
psql -h localhost -U postgres -d process_extractions

# Ver tabelas
\dt

# Ver dados da tabela
SELECT * FROM process_extractions;
```

## Limitações

- **Formato de arquivo**: Apenas PDFs
- **Tamanho**: Limitado pelas restrições da API do Gemini
- **Idioma**: Otimizado para documentos em português
- **Rede**: Requer acesso à internet para download e API

## Troubleshooting

### Erro "Invalid API Key"
- Verifique se `GEMINI_API_KEY` está configurado corretamente
- Confirme que a chave tem acesso à API Gemini

### Erro de Download
- Verifique se a URL do PDF é acessível publicamente
- Confirme conectividade com a internet
- Aumente `DOWNLOAD_TIMEOUT` se necessário

### Erro de Extração
- Verifique se o PDF contém texto extraível
- PDFs escaneados podem ter problemas
- Arquivos muito grandes podem exceder limites da API

## Desenvolvimento

### Adicionando Novos Campos

1. Atualize os DTOs em `app/application/dtos.py`
2. Modifique o schema no `LlmService`
3. Atualize o modelo de banco em `app/infrastructure/database.py`
4. Execute migração se necessário

### Testando Localmente

```bash
# Executar com reload automático
uvicorn app.main:app --reload --log-level debug

# Testar endpoint
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{"pdf_url": "https://exemplo.com/doc.pdf", "case_id": "teste-001"}'
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para detalhes.
# Force deployment Thu Sep 18 15:28:47 -03 2025
