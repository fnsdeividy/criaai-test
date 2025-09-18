#!/usr/bin/env python3
"""
Script de demonstração da Process Extraction API.
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"


def test_health():
    """Testa o endpoint de health check."""
    print("🔍 Testando health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ Health check OK")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ Health check falhou: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")


def test_extract_api():
    """Testa a API de extração (sem PDF real)."""
    print("\n🔍 Testando API de extração...")
    
    # Dados de teste
    test_data = {
        "pdf_url": "https://httpbin.org/status/404",  # URL que retorna 404 para testar erro
        "case_id": "demo-001-2024"
    }
    
    try:
        response = requests.post(f"{API_BASE}/extract", json=test_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Erro de download capturado corretamente")
            print(f"   Detalhe: {response.json().get('detail', 'N/A')}")
        else:
            print(f"Response: {response.json()}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")


def main():
    """Função principal de demonstração."""
    print("🚀 Demonstração da Process Extraction API")
    print("=" * 50)
    
    # Testar health check
    test_health()
    
    # Testar API de extração
    test_extract_api()
    
    print("\n📚 Para usar a API:")
    print(f"   - Swagger UI: {API_BASE}/docs")
    print(f"   - ReDoc: {API_BASE}/redoc")
    print(f"   - Health: {API_BASE}/health")
    
    print("\n🔧 Para configurar:")
    print("   1. Configure GEMINI_API_KEY no arquivo .env")
    print("   2. Execute: uvicorn app.main:app --reload")
    print("   3. Teste com um PDF real")


if __name__ == "__main__":
    main()
