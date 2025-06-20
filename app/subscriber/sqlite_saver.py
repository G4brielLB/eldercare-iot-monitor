import os
import sqlite3
import json

# Caminho do banco dentro da pasta app
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "health.db")

def create_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Cria tabela de pacientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            sex TEXT CHECK(sex IN ('M', 'F'))
        )
    """)
    # Cria tabela de mensagens de saúde
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_messages (
            id TEXT PRIMARY KEY,
            received_at TEXT,
            message_type TEXT,
            patient_id TEXT,
            timestamp TEXT,
            data TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    conn.commit()
    conn.close()

def insert_patient(patient_id, name, age, sex, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO patients (id, name, age, sex)
        VALUES (?, ?, ?, ?)
    """, (patient_id, name, age, sex))
    conn.commit()
    conn.close()

def insert_message(id, received_at, message_type, patient_id, timestamp, data, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO health_messages (id, received_at, message_type, patient_id, timestamp, data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        id,
        received_at,
        message_type,
        patient_id,
        timestamp,
        json.dumps(data, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

# Exemplo de uso
if __name__ == "__main__":
    create_db()
    # Exemplo de paciente
    insert_patient("PAT001", "Maria Silva", 78, "F")
    # Exemplo de mensagem
    msg = {
        "health_status": "critical",
        "alerts": [{"type": "fall_detected", "severity": "critical"}],
        "statistics": [{"sensor_type": "heart_rate", "avg": 120}]
    }
    insert_message(
        id="PAT001_emergency_1750373951011",
        received_at="2025-06-19T19:59:11.011328",
        message_type="emergency",
        patient_id="PAT001",
        timestamp="2025-06-19T19:59:10.997497",
        data=msg
    )
    print("Paciente e mensagem salvos no banco de dados SQLite.")