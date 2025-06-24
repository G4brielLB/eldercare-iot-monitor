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

app = FastAPI(title="ElderCare IoT Monitor API", version="1.0.0")

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

subscriber_process = None

def run_subscriber():
    subscriber = ElderCareSubscriber()
    subscriber.start_listening()

@app.post("/start_subscriber")
def start_subscriber():
    global subscriber_process
    if subscriber_process is None or not subscriber_process.is_alive():
        subscriber_process = multiprocessing.Process(target=run_subscriber)
        subscriber_process.start()
        return {"status": "Subscriber iniciado em novo processo"}
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

