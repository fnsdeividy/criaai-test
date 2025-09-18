"""
Testes para as rotas da API.
"""
from unittest.mock import patch, Mock
import pytest
from fastapi import status

from app.application.dtos import ExtractResponse
from app.core.exceptions import DownloadError, LlmError, RepositoryError


class TestExtractRoutes:
    """Testes para rotas de extração."""

    def test_post_extract_success(self, test_client, sample_extract_request):
        """Testa POST /extract com sucesso."""
        # Mock do use case
        mock_response = ExtractResponse(
            case_id=sample_extract_request["case_id"],
            resume="Resumo do processo de teste",
            timeline=[],
            evidence=[],
            persisted_at="2024-08-28T12:00:00Z"
        )
        
        with patch("app.core.dependencies.get_create_process_use_case") as mock_get_use_case:
            mock_use_case = Mock()
            mock_use_case.execute.return_value = mock_response
            mock_get_use_case.return_value = mock_use_case
            
            # Act
            response = test_client.post("/extract", json=sample_extract_request)
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["case_id"] == sample_extract_request["case_id"]
            assert data["resume"] == "Resumo do processo de teste"

    def test_post_extract_invalid_url(self, test_client):
        """Testa POST /extract com URL inválida."""
        # Arrange
        invalid_request = {
            "pdf_url": "not-a-url",
            "case_id": "0809090-86.2024.8.12.0021"
        }
        
        # Act
        response = test_client.post("/extract", json=invalid_request)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_post_extract_download_error(self, test_client, sample_extract_request):
        """Testa POST /extract com erro de download."""
        with patch("app.core.dependencies.get_create_process_use_case") as mock_get_use_case:
            mock_use_case = Mock()
            mock_use_case.execute.side_effect = DownloadError("Erro 404")
            mock_get_use_case.return_value = mock_use_case
            
            # Act
            response = test_client.post("/extract", json=sample_extract_request)
            
            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "download" in response.json()["detail"].lower()

    def test_post_extract_llm_error(self, test_client, sample_extract_request):
        """Testa POST /extract com erro de LLM."""
        with patch("app.core.dependencies.get_create_process_use_case") as mock_get_use_case:
            mock_use_case = Mock()
            mock_use_case.execute.side_effect = LlmError("Falha na IA")
            mock_get_use_case.return_value = mock_use_case
            
            # Act
            response = test_client.post("/extract", json=sample_extract_request)
            
            # Assert
            assert response.status_code == status.HTTP_502_BAD_GATEWAY
            assert "IA" in response.json()["detail"]

    def test_post_extract_repository_error(self, test_client, sample_extract_request):
        """Testa POST /extract com erro de repositório."""
        with patch("app.core.dependencies.get_create_process_use_case") as mock_get_use_case:
            mock_use_case = Mock()
            mock_use_case.execute.side_effect = RepositoryError("Erro de DB")
            mock_get_use_case.return_value = mock_use_case
            
            # Act
            response = test_client.post("/extract", json=sample_extract_request)
            
            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_extract_success(self, test_client, existing_process_data):
        """Testa GET /extract/{case_id} com sucesso."""
        case_id = existing_process_data["case_id"]
        
        mock_response = ExtractResponse(**existing_process_data)
        
        with patch("app.core.dependencies.get_get_process_use_case") as mock_get_use_case:
            mock_use_case = Mock()
            mock_use_case.execute.return_value = mock_response
            mock_get_use_case.return_value = mock_use_case
            
            # Act
            response = test_client.get(f"/extract/{case_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["case_id"] == case_id

    def test_get_extract_not_found(self, test_client):
        """Testa GET /extract/{case_id} com processo não encontrado."""
        case_id = "inexistente"
        
        with patch("app.core.dependencies.get_get_process_use_case") as mock_get_use_case:
            mock_use_case = Mock()
            mock_use_case.execute.return_value = None
            mock_get_use_case.return_value = mock_use_case
            
            # Act
            response = test_client.get(f"/extract/{case_id}")
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_extract_repository_error(self, test_client):
        """Testa GET /extract/{case_id} com erro de repositório."""
        case_id = "teste"
        
        with patch("app.core.dependencies.get_get_process_use_case") as mock_get_use_case:
            mock_use_case = Mock()
            mock_use_case.execute.side_effect = RepositoryError("Erro de DB")
            mock_get_use_case.return_value = mock_use_case
            
            # Act
            response = test_client.get(f"/extract/{case_id}")
            
            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestHealthRoutes:
    """Testes para rotas de health check."""

    def test_root_endpoint(self, test_client):
        """Testa endpoint raiz."""
        response = test_client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data

    def test_health_endpoint(self, test_client):
        """Testa endpoint de health check."""
        response = test_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "service" in data
