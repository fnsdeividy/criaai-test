"""
Exceções customizadas da aplicação.
"""


class AppError(Exception):
    """Exceção base da aplicação."""
    pass


class DownloadError(AppError):
    """Erro no download de arquivos."""
    pass


class LlmError(AppError):
    """Erro na integração com LLM."""
    pass


class RepositoryError(AppError):
    """Erro no repositório/banco de dados."""
    pass


class ValidationError(AppError):
    """Erro de validação de dados."""
    pass
