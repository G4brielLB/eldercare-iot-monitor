"""Teste do novo BaseSensor sem MQTT"""
from sensors.heart_rate_sensor import HeartRateSensor
from sensors.stress_sensor import StressSensor
import time

def test_sensor_without_mqtt():
    print("🧪 Testando sensores SEM MQTT...")
    
    # Cria sensores
    heart_sensor = HeartRateSensor("PAT001")
    stress_sensor = StressSensor("PAT001")
    
    print(f"📋 Sensores criados: {heart_sensor}, {stress_sensor}")
    
    # Testa geração de dados
    for i in range(5):
        heart_reading = heart_sensor.get_sensor_reading()
        stress_reading = stress_sensor.get_sensor_reading()
        
        print(f"\n📊 Leitura {i+1}:")
        print(f"   Coração: {heart_reading}")
        print(f"   Estresse: {stress_reading}")
        
        time.sleep(1)
    
    print("\n✅ Teste concluído - sensores funcionando sem MQTT!")

if __name__ == "__main__":
    test_sensor_without_mqtt()