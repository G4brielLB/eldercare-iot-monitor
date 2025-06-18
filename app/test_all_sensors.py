"""Teste de todos os sensores para um paciente"""
import time
from sensors.heart_rate_sensor import HeartRateSensor
from sensors.stress_sensor import StressSensor
from sensors.temperature_sensor import TemperatureSensor
from sensors.oxygen_sensor import OxygenSensor
from sensors.fall_sensor import FallSensor

def test_patient_sensors(patient_id, duration=30):
    print(f"🧪 Testando todos os sensores para {patient_id}")
    
    sensors = [
        HeartRateSensor(patient_id),
        StressSensor(patient_id),
        TemperatureSensor(patient_id),
        OxygenSensor(patient_id),
        FallSensor(patient_id)
    ]
    
    # Conecta todos
    for sensor in sensors:
        if not sensor.connect():
            print(f"❌ Falha ao conectar {sensor.sensor_type}")
            return
    
    print(f"✅ Todos os sensores conectados! Enviando dados por {duration}s...")
    
    # Envia dados
    start_time = time.time()
    count = 0
    
    while time.time() - start_time < duration:
        for sensor in sensors:
            sensor.publish_data()
        
        count += 1
        print(f"📊 Ciclo {count} enviado")
        time.sleep(2)
    
    # Desconecta
    for sensor in sensors:
        sensor.client.disconnect()
    
    print(f"🏁 Teste completo finalizado! {count} ciclos enviados")

if __name__ == "__main__":
    test_patient_sensors("PAT001", 20)