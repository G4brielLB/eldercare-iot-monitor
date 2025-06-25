from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from subscriber.subscriber import ElderCareSubscriber
from database.crud import get_patient, get_all_messages, get_patient_messages, get_all_patients
from fastapi.responses import JSONResponse
from typing import List
from database.schemas import HealthMessageSchema
import json
import multiprocessing
from fastapi import Response
from fastapi.encoders import jsonable_encoder
import threading

app = FastAPI(title="ElderCare IoT Monitor API", version="1.0.0")

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

subscriber_instance = None
subscriber_thread = None

def run_subscriber():
    global subscriber_instance
    subscriber_instance = ElderCareSubscriber()
    subscriber_instance.start_listening()

@app.post("/start_subscriber")
def start_subscriber():
    global subscriber_thread
    if subscriber_thread is None or not subscriber_thread.is_alive():
        subscriber_thread = threading.Thread(target=run_subscriber, daemon=True)
        subscriber_thread.start()
        return {"status": "Subscriber iniciado em background (thread)"}
    else:
        return {"status": "Subscriber já está rodando"}

@app.get("/paciente/{patient_id}")
def read_patient(patient_id: str):
    patient = get_patient(patient_id)
    if patient:
        return patient
    return {"error": "Paciente não encontrado"}

@app.get("/status", response_model=List[HealthMessageSchema])
def get_status():
    messages = get_all_messages()
    result = []
    for m in messages:
        data = m.data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}
        result.append({
            "id": m.id,
            "patient_id": m.patient_id,
            "message_type": m.message_type,
            "timestamp": m.timestamp,
            "data": data
        })
    return result

# pega todas as mensagens do paciente
@app.get("/messages/{patient_id}", response_model=List[HealthMessageSchema])
def read_patient_messages(patient_id: str):
    messages = get_patient_messages(patient_id)
    result = []
    for m in messages:
        # Se m.data for string, converte para dict
        data = m.data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}
        result.append({
            "id": m.id,
            "patient_id": m.patient_id,
            "message_type": m.message_type,
            "timestamp": m.timestamp,
            "data": data
        })
    return result

@app.get("/latest_message_per_patient", response_model=List[HealthMessageSchema])
def latest_message_per_patient():
    patients = get_all_patients()
    result = []
    for patient in patients:
        messages = get_patient_messages(patient.id)
        if messages:
            # Ordena por timestamp ou received_at, pega a mais recente
            latest = max(messages, key=lambda m: getattr(m, "timestamp", None) or 0)
            data = latest.data
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    data = {}
            result.append({
                "id": latest.id,
                "patient_id": latest.patient_id,
                "message_type": latest.message_type,
                "timestamp": getattr(latest, "timestamp", ""),
                "data": data,
            })
    return result

@app.get("/patients_status")
def get_patients_status():
    """
    Retorna o status online/offline de todos os pacientes
    """
    global subscriber_instance
    
    if subscriber_instance is None:
        return {"error": "Subscriber não está rodando. Inicie o subscriber primeiro."}
    
    import time
    current_time = time.time()
    timeout = getattr(subscriber_instance, 'heartbeat_timeout', 30)  # 30s default
    
    patients_status = {}
    
    # Verifica status de todos os pacientes que já enviaram heartbeat
    for patient_id, last_heartbeat in subscriber_instance.online_patients.items():
        time_since_last = current_time - last_heartbeat
        is_online = time_since_last <= timeout
        
        patients_status[patient_id] = {
            "patient_id": patient_id,
            "is_online": is_online,
            "last_heartbeat": last_heartbeat,
            "time_since_last": int(time_since_last),
            "status": "ONLINE" if is_online else "OFFLINE"
        }
    
    # Adiciona pacientes que existem no banco mas nunca enviaram heartbeat
    all_patients = get_all_patients()
    for patient in all_patients:
        if patient.id not in patients_status:
            patients_status[patient.id] = {
                "patient_id": patient.id,
                "is_online": False,
                "last_heartbeat": None,
                "time_since_last": None,
                "status": "NEVER_CONNECTED"
            }
    
    return {
        "patients": list(patients_status.values()),
        "total_patients": len(patients_status),
        "online_count": len([p for p in patients_status.values() if p["is_online"]]),
        "offline_count": len([p for p in patients_status.values() if not p["is_online"]])
    }

