import random
from .base_sensor import BaseSensor

class HeartRateSensor(BaseSensor):
    def __init__(self, patient_id):
        super().__init__(patient_id, "heart_rate")
    
    def generate_data(self):
        """Gera dados aleatórios de batimento cardíaco"""
        # Simula variação normal com picos ocasionais
        if random.random() < 0.1:  # 10% chance de pico
            heart_rate = random.randint(100, 120)
        else:
            heart_rate = random.randint(65, 85)
            
        return {
            "value": heart_rate,
            "unit": "bpm",
            "status": "high" if heart_rate > 100 else "normal"
        }