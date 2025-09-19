.PHONY: install run test lint clean help setup-db docker-up docker-down frontend-install frontend-dev frontend-build dev

# Variáveis
VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip3
UVICORN = $(VENV)/bin/uvicorn
PYTEST = $(VENV)/bin/pytest

# Ajuda
help:
	@echo "Comandos disponíveis:"
	@echo "Backend:"
	@echo "  install        - Instalar dependências backend"
	@echo "  run            - Executar API backend"
	@echo "  test           - Executar testes"
	@echo "  test-cov       - Executar testes com cobertura"
	@echo "  lint           - Executar linting"
	@echo "  setup-db       - Configurar banco PostgreSQL"
	@echo "Frontend:"
	@echo "  frontend-install - Instalar dependências frontend"
	@echo "  frontend-dev     - Executar frontend (dev)"
	@echo "  frontend-build   - Build frontend (produção)"
	@echo "Desenvolvimento:"
	@echo "  dev            - Executar backend + frontend"
	@echo "  setup          - Configuração inicial completa"
	@echo "PostgreSQL:"
	@echo "  install-pg     - Instalar PostgreSQL (macOS)"
	@echo "  docker-up      - Iniciar PostgreSQL com Docker"
	@echo "  docker-down    - Parar PostgreSQL Docker"
	@echo "  docker-admin   - Iniciar PostgreSQL + PgAdmin"
	@echo "Outros:"
	@echo "  clean          - Limpar arquivos temporários"

# Instalação
install:
	@echo "Criando/verificando virtual environment..."
	@if [ ! -d "$(VENV)" ]; then \
		python3 -m venv $(VENV); \
		echo "Virtual environment criado em $(VENV)"; \
	fi
	@echo "Instalando dependências..."
	$(PIP) install -r requirements.txt

# Executar aplicação
run:
	@echo "Iniciando Process Extraction API..."
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

# Executar aplicação em produção
run-prod:
	@echo "Iniciando Process Extraction API (produção)..."
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Testes
test:
	@echo "Executando testes..."
	$(PYTEST) -v

# Testes com cobertura
test-cov:
	@echo "Executando testes com cobertura..."
	$(PYTEST) --cov=app --cov-report=html --cov-report=term-missing -v

# Linting (opcional)
lint:
	@echo "Executando linting..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check app/ tests/; \
	elif command -v flake8 >/dev/null 2>&1; then \
		flake8 app/ tests/; \
	else \
		echo "Nenhum linter encontrado (ruff ou flake8)"; \
	fi

# Formatação (opcional)
format:
	@echo "Formatando código..."
	@if command -v black >/dev/null 2>&1; then \
		black app/ tests/; \
	else \
		echo "Black não encontrado, pulando formatação"; \
	fi

# Limpeza
clean:
	@echo "Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ htmlcov/ .coverage 2>/dev/null || true
	rm -f process_extractions.db* 2>/dev/null || true
	rm -f /tmp/*.pdf 2>/dev/null || true

# Instalação PostgreSQL (macOS)
install-pg:
	@echo "Instalando PostgreSQL no macOS..."
	@if command -v brew >/dev/null 2>&1; then \
		brew install postgresql; \
		brew services start postgresql; \
		echo "PostgreSQL instalado e iniciado"; \
	else \
		echo "Homebrew não encontrado. Instale manualmente o PostgreSQL"; \
	fi

# Configuração do banco PostgreSQL
setup-db:
	@echo "Configurando banco PostgreSQL..."
	$(PYTHON) setup_postgres.py

# Docker PostgreSQL
docker-up:
	@echo "Iniciando PostgreSQL com Docker..."
	docker-compose up -d postgres
	@echo "Aguardando PostgreSQL iniciar..."
	@sleep 5
	@echo "PostgreSQL disponível em localhost:5432"

docker-down:
	@echo "Parando PostgreSQL Docker..."
	docker-compose down

docker-admin:
	@echo "Iniciando PostgreSQL + PgAdmin..."
	docker-compose --profile admin up -d
	@echo "PostgreSQL: localhost:5432"
	@echo "PgAdmin: http://localhost:5050 (admin@criaai.com / admin123)"

# Frontend Commands
frontend-install:
	@echo "Instalando dependências do frontend..."
	cd frontend && npm install

frontend-dev:
	@echo "Iniciando frontend em modo desenvolvimento..."
	cd frontend && npm run dev

frontend-build:
	@echo "Fazendo build do frontend..."
	cd frontend && npm run build

# Desenvolvimento (Backend + Frontend)
dev:
	@echo "Iniciando desenvolvimento completo..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:8080"
	@echo "Docs API: http://localhost:8000/docs"
	@echo ""
	@echo "Pressione Ctrl+C para parar ambos os serviços"
	@trap 'kill %1; kill %2' INT; \
	make run & make frontend-dev & \
	wait

# Configuração inicial
setup:
	@echo "Configuração inicial do projeto..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Arquivo .env criado. Configure GEMINI_API_KEY e DATABASE_URL."; \
	else \
		echo "Arquivo .env já existe."; \
	fi
	make install
	make frontend-install
	@echo ""
	@echo "Configuração concluída!"
	@echo "IMPORTANTE: O projeto agora usa virtual environment!"
	@echo "Para executar comandos, use 'make <comando>' ou ative o venv manualmente:"
	@echo "  source venv/bin/activate"
	@echo ""
	@echo "Opções para PostgreSQL:"
	@echo "  A) Docker: make docker-up && make setup-db"
	@echo "  B) Local:  make install-pg && make setup-db"
	@echo "Depois:"
	@echo "  1. Edite .env e configure GEMINI_API_KEY"
	@echo "  2. Execute: make dev"
	@echo "  3. Backend: http://localhost:8000/docs"
	@echo "  4. Frontend: http://localhost:8080"

# Verificar configuração
check:
	@echo "Verificando configuração..."
	@if [ -f .env ]; then \
		echo "✓ Arquivo .env encontrado"; \
	else \
		echo "✗ Arquivo .env não encontrado (execute: make setup)"; \
	fi
	@if grep -q "your_gemini_api_key_here" .env 2>/dev/null; then \
		echo "✗ GEMINI_API_KEY não configurado"; \
	else \
		echo "✓ GEMINI_API_KEY configurado"; \
	fi
	@if [ -d "$(VENV)" ]; then \
		echo "✓ Virtual environment encontrado"; \
		$(PYTHON) -c "import app.main" 2>/dev/null && echo "✓ Aplicação pode ser importada" || echo "✗ Erro na importação da aplicação"; \
	else \
		echo "✗ Virtual environment não encontrado (execute: make install)"; \
	fi

# Executar exemplo de teste
demo:
	@echo "Executando demonstração..."
	@echo "Iniciando servidor em background..."
	@$(UVICORN) app.main:app --host 0.0.0.0 --port 8000 &
	@sleep 3
	@echo "Testando health check..."
	@curl -s http://localhost:8000/health | $(PYTHON) -m json.tool || echo "Erro no health check"
	@echo "Parando servidor..."
	@pkill -f "$(UVICORN) app.main:app" 2>/dev/null || true
