"""
Módulo de persistência em SQLite para o sistema de monitoramento de idosos.

Este módulo contém:
- models.py: Definições das tabelas SQLAlchemy (Patient, HealthMessage)
- database.py: Configuração da conexão e engine do SQLite
- crud.py: Operações de Create, Read, Update, Delete

Uso típico:
    from database import create_database, create_patient, create_health_message
    
    # Inicializar banco
    create_database()
    
    # Criar paciente
    create_patient("PAT001", "Maria Silva", 78, "F")
    
    # Salvar mensagem de emergência
    create_health_message("PAT001", "emergency", {"sensor": "fall", "value": "detected"})
"""

from .database import create_database, get_db_session, get_db_session_sync
from .crud import (
    create_patient, get_patient, get_all_patients,
    create_health_message, get_patient_messages, 
    get_recent_emergencies, get_latest_summary,
    get_message_data_as_dict, initialize_sample_patients
)
from .models import Patient, HealthMessage, Base

__all__ = [
    # Database
    "create_database", "get_db_session", "get_db_session_sync",
    
    # CRUD operations
    "create_patient", "get_patient", "get_all_patients",
    "create_health_message", "get_patient_messages",
    "get_recent_emergencies", "get_latest_summary",
    "get_message_data_as_dict", "initialize_sample_patients",
    
    # Models
    "Patient", "HealthMessage", "Base"
]