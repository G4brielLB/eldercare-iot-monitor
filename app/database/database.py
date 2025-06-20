"""
Módulo para gerenciamento da conexão com o banco de dados SQLite.
Responsável por criar e configurar a conexão com o banco.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Caminho para o banco de dados
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'health.db')
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necessário para SQLite com FastAPI
    echo=False  # True para debug SQL
)

# SessionLocal para criar sessões do banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_database():
    """
    Cria todas as tabelas no banco de dados.
    Deve ser chamada uma vez para inicializar o banco.
    """
    Base.metadata.create_all(bind=engine)
    print(f"Banco de dados criado em: {DATABASE_PATH}")

def get_db_session():
    """
    Retorna uma nova sessão do banco de dados.
    Para uso em operações CRUD.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session_sync():
    """
    Retorna uma sessão síncrona do banco de dados.
    Para uso direto sem context manager.
    """
    return SessionLocal()

if __name__ == "__main__":
    # Criar o banco se executado diretamente
    create_database()
