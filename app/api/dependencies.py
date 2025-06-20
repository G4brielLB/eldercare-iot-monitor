"""
Dependências compartilhadas da API FastAPI

Este módulo centraliza as dependências que serão reutilizadas
em diferentes routers da API, seguindo o padrão de injeção
de dependência do FastAPI.

Principais dependências:
- get_database(): Sessão do banco de dados SQLite
- Futuras: autenticação, logging, etc.
"""

from sqlalchemy.orm import Session
from typing import Generator
from database import get_db_session_sync


def get_database() -> Generator[Session, None, None]:
    """
    Dependência para obter uma sessão do banco de dados SQLite
    
    Esta função é usada como dependência nos endpoints FastAPI
    para fornecer uma sessão ativa do banco de dados.
    
    Uso nos routers:
        @router.get("/endpoint")
        def my_endpoint(db: Session = Depends(get_database)):
            # Usar db para consultas
    
    Returns:
        Session: Sessão ativa do SQLAlchemy para o SQLite
    """
    db = get_db_session_sync()
    try:
        yield db
    finally:
        db.close()


# Dependências futuras podem ser adicionadas aqui:
#
# def get_current_user():
#     """Dependência para autenticação (futuro)"""
#     pass
#
# def get_logger():
#     """Dependência para logging centralizado (futuro)"""
#     pass
#
# def rate_limit():
#     """Dependência para rate limiting (futuro)"""
#     pass
