"""
Módulo de operações CRUD para o banco de dados.
Contém funções para inserir, consultar e manipular dados no SQLite.
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Patient, HealthMessage
from .database import get_db_session_sync

# ====== OPERAÇÕES COM PACIENTES ======

def create_patient(patient_id: str, name: str, age: int = None, sex: str = None):
    """
    Cria um novo paciente no banco de dados.
    
    Args:
        patient_id: ID único do paciente (ex: PAT001)
        name: Nome completo do paciente
        age: Idade do paciente (opcional)
        sex: Sexo do paciente (opcional)
    
    Returns:
        Patient: Objeto do paciente criado ou None se já existir
    """
    db = get_db_session_sync()
    try:
        # Verificar se paciente já existe
        existing = db.query(Patient).filter(Patient.id == patient_id).first()
        if existing:
            print(f"Paciente {patient_id} já existe")
            return existing
        
        # Criar novo paciente
        patient = Patient(
            id=patient_id,
            name=name,
            age=age,
            sex=sex
        )
        
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        print(f"Paciente criado: {patient}")
        return patient
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao criar paciente: {e}")
        return None
    finally:
        db.close()

def get_patient(patient_id: str):
    """
    Busca um paciente pelo ID.
    
    Args:
        patient_id: ID do paciente
        
    Returns:
        Patient: Objeto do paciente ou None se não encontrado
    """
    db = get_db_session_sync()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        return patient
    finally:
        db.close()

def get_all_patients():
    """
    Retorna todos os pacientes cadastrados.
    
    Returns:
        List[Patient]: Lista de todos os pacientes
    """
    db = get_db_session_sync()
    try:
        patients = db.query(Patient).all()
        return patients
    finally:
        db.close()

# ====== OPERAÇÕES COM MENSAGENS DE SAÚDE ======

def create_health_message(patient_id: str, message_type: str, data: dict, original_timestamp: str = None):
    """
    Salva uma mensagem de saúde no banco de dados.
    
    Args:
        patient_id: ID do paciente
        message_type: Tipo da mensagem ("emergency" ou "summary")
        data: Dados da mensagem (dict que será convertido para JSON)
        original_timestamp: Timestamp original da mensagem (opcional)
    
    Returns:
        HealthMessage: Objeto da mensagem criada ou None se erro
    """
    db = get_db_session_sync()
    try:
        # Verificar se paciente existe
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            print(f"Paciente {patient_id} não encontrado")
            return None
        
        # Gerar ID único para a mensagem
        timestamp_str = original_timestamp or datetime.now().isoformat()
        message_id = f"{patient_id}_{message_type}_{int(datetime.now().timestamp() * 1000)}"
        
        # Converter dados para JSON string
        data_json = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Criar mensagem
        message = HealthMessage(
            id=message_id,
            received_at=datetime.now().isoformat(),
            message_type=message_type,
            patient_id=patient_id,
            timestamp=timestamp_str,
            data=data_json
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        print(f"Mensagem salva: {message.id}")
        return message
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar mensagem: {e}")
        return None
    finally:
        db.close()

def get_all_messages(limit: int = 100):
    """
    Busca todas as mensagens de saúde.
    
    Args:
        limit: Número máximo de mensagens a retornar
    Returns:
        List[HealthMessage]: Lista de mensagens
    """
    db = get_db_session_sync()
    try:
        messages = db.query(HealthMessage).order_by(desc(HealthMessage.received_at)).limit(limit).all()
        return messages
    finally:
        db.close()

def get_patient_messages(patient_id: str, message_type: str = None, limit: int = 100):
    """
    Busca mensagens de um paciente específico.
    
    Args:
        patient_id: ID do paciente
        message_type: Tipo de mensagem para filtrar (opcional)
        limit: Número máximo de mensagens a retornar
        
    Returns:
        List[HealthMessage]: Lista de mensagens
    """
    db = get_db_session_sync()
    try:
        query = db.query(HealthMessage).filter(HealthMessage.patient_id == patient_id)
        
        if message_type:
            query = query.filter(HealthMessage.message_type == message_type)
        
        messages = query.order_by(desc(HealthMessage.received_at)).limit(limit).all()
        return messages
    finally:
        db.close()

def get_recent_emergencies(limit: int = 50):
    """
    Busca as emergências mais recentes de todos os pacientes.
    
    Args:
        limit: Número máximo de emergências a retornar
        
    Returns:
        List[HealthMessage]: Lista de mensagens de emergência
    """
    db = get_db_session_sync()
    try:
        emergencies = (db.query(HealthMessage)
                      .filter(HealthMessage.message_type == "emergency")
                      .order_by(desc(HealthMessage.received_at))
                      .limit(limit)
                      .all())
        return emergencies
    finally:
        db.close()

def get_latest_summary(patient_id: str):
    """
    Busca o último resumo de saúde de um paciente.
    
    Args:
        patient_id: ID do paciente
        
    Returns:
        HealthMessage: Última mensagem de resumo ou None
    """
    db = get_db_session_sync()
    try:
        summary = (db.query(HealthMessage)
                  .filter(HealthMessage.patient_id == patient_id)
                  .filter(HealthMessage.message_type == "summary")
                  .order_by(desc(HealthMessage.received_at))
                  .first())
        return summary
    finally:
        db.close()

def get_message_data_as_dict(message: HealthMessage):
    """
    Converte o campo data JSON de uma mensagem para dict.
    
    Args:
        message: Objeto HealthMessage
        
    Returns:
        dict: Dados da mensagem como dicionário
    """
    try:
        return json.loads(message.data)
    except (json.JSONDecodeError, AttributeError):
        return {}

# ====== FUNÇÕES DE UTILIDADE ======

def initialize_sample_patients():
    """
    Cria pacientes de exemplo para testes.
    """
    sample_patients = [
        ("PAT001", "Maria Silva", 78, "F"),
        ("PAT002", "João Santos", 82, "M"),
        ("PAT003", "Ana Costa", 75, "F"),
    ]
    
    print("Criando pacientes de exemplo...")
    for patient_id, name, age, sex in sample_patients:
        create_patient(patient_id, name, age, sex)
    
    print("Pacientes de exemplo criados com sucesso!")

if __name__ == "__main__":
    # Criar pacientes de exemplo se executado diretamente
    from .database import create_database
    create_database()
    initialize_sample_patients()
