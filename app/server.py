from fastapi import FastAPI, BackgroundTasks
from subscriber.subscriber import ElderCareSubscriber
from test_smart_pulseira import test_single_patient, simulate_multiple_patients
from database.crud import get_patient, get_all_messages, get_patient_messages
from fastapi.responses import JSONResponse
from typing import List
from database.schemas import HealthMessageSchema
import json

app = FastAPI()
subscriber_instance = None

@app.post("/start_subscriber")
def start_subscriber(background_tasks: BackgroundTasks):
    global subscriber_instance
    if subscriber_instance is None:
        subscriber_instance = ElderCareSubscriber()
        background_tasks.add_task(subscriber_instance.start_listening)
        return {"status": "Subscriber iniciado"}
    return {"status": "Subscriber já está rodando"}

@app.post("/run_publisher_test")
def run_publisher_test(patient_id: str = "PAT001", duration: int = 120):
    result = test_single_patient(patient_id, duration)
    return {"result": result}

@app.get("/status")
def get_status():
    messages = get_all_messages()
    return {"messages": messages}

@app.get("/paciente/{patient_id}")
def read_patient(patient_id: str):
    patient = get_patient(patient_id)
    if patient:
        return patient
    return {"error": "Paciente não encontrado"}

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
            "data": data,
            "original_timestamp": getattr(m, "original_timestamp", "")
        })
    return result
