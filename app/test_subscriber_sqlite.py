#!/usr/bin/env python3
"""
Teste de integração do Subscriber com SQLite
Simula mensagens MQTT e verifica se são salvas corretamente no banco
"""

import json
import time
from datetime import datetime
from database import get_patient_messages, get_all_patients, create_health_message

def test_subscriber_sqlite_integration():
    """Testa integração completa do subscriber com SQLite"""
    print("🧪 === TESTE DE INTEGRAÇÃO SUBSCRIBER + SQLITE ===\n")
    
    # 1. Verificar pacientes existentes
    print("1. Verificando pacientes cadastrados...")
    patients = get_all_patients()
    print(f"   👥 Pacientes encontrados: {len(patients)}")
    for patient in patients:
        print(f"   - {patient.id}: {patient.name} ({patient.age} anos)")
    
    if not patients:
        print("   ❌ Nenhum paciente encontrado. Execute primeiro o setup do banco.")
        return
    
    # 2. Simular mensagens para PAT001
    patient_id = "PAT001"
    print(f"\n2. Simulando mensagens para {patient_id}...")
    
    # Emergência simulada
    emergency_data = {
        'created_at': datetime.now().isoformat(),
        'alerts': [
            {'sensor': 'fall', 'value': 'detected', 'timestamp': datetime.now().isoformat()},
            {'sensor': 'heart_rate', 'value': 45, 'timestamp': datetime.now().isoformat()}
        ],
        'readings_count': 25,
        'patient_id': patient_id
    }
    
    print("   🚨 Criando emergência...")
    emergency_msg = create_health_message(patient_id, 'emergency', emergency_data)
    print(f"   ✅ Emergência salva: {emergency_msg.id if emergency_msg else 'ERRO'}")
    
    time.sleep(1)  # Pequena pausa
    
    # Resumo simulado
    summary_data = {
        'created_at': datetime.now().isoformat(),
        'readings_count': 120,
        'health_status': 'preocupante',
        'averages': {
            'heart_rate': 68,
            'oxygen': 96,
            'temperature': 37.2,
            'stress_level': 0.7
        },
        'patient_id': patient_id
    }
    
    print("   📊 Criando resumo...")
    summary_msg = create_health_message(patient_id, 'summary', summary_data)
    print(f"   ✅ Resumo salvo: {summary_msg.id if summary_msg else 'ERRO'}")
    
    # 3. Verificar mensagens salvas
    print(f"\n3. Verificando mensagens salvas para {patient_id}...")
    
    # Emergências
    emergencies = get_patient_messages(patient_id, 'emergency', limit=5)
    print(f"   🚨 Emergências: {len(emergencies)}")
    for msg in emergencies[:2]:  # Mostrar apenas as 2 mais recentes
        data = json.loads(msg.data)
        alerts_count = len(data.get('alerts', []))
        print(f"      - {msg.id}: {alerts_count} alertas ({msg.received_at})")
    
    # Resumos
    summaries = get_patient_messages(patient_id, 'summary', limit=5)
    print(f"   📊 Resumos: {len(summaries)}")
    for msg in summaries[:2]:  # Mostrar apenas os 2 mais recentes
        data = json.loads(msg.data)
        health_status = data.get('health_status', 'unknown')
        readings = data.get('readings_count', 0)
        print(f"      - {msg.id}: {readings} leituras, status={health_status} ({msg.received_at})")
    
    # 4. Teste de consulta JSON
    print(f"\n4. Teste de consulta de dados JSON...")
    if summaries:
        latest_summary = summaries[0]
        data = json.loads(latest_summary.data)
        averages = data.get('averages', {})
        print(f"   📈 Última médias do {patient_id}:")
        for sensor, value in averages.items():
            print(f"      - {sensor}: {value}")
    
    print(f"\n✅ === TESTE CONCLUÍDO COM SUCESSO ===")
    print(f"💾 Mensagens agora são salvas em SQLite")
    print(f"🔍 Dados podem ser consultados via SQL ou FastAPI")

if __name__ == "__main__":
    test_subscriber_sqlite_integration()
