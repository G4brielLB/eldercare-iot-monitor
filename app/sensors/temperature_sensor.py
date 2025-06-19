import random
from .base_sensor import BaseSensor

class TemperatureSensor(BaseSensor):
    def __init__(self, patient_id):
        super().__init__(patient_id, "temperature")
    
    def generate_data(self):
        """Gera dados de temperatura corporal (35.5-38.5°C)"""
        # Temperatura normal: 36.1-37.2°C
        # Variação natural com chance de febre
        
        rand = random.random()
        
        if rand < 0.8:  # 80% - temperatura normal
            temperature = round(random.uniform(36.1, 37.2), 1)
        elif rand < 0.95:  # 15% - ligeiramente elevada
            temperature = round(random.uniform(37.3, 37.8), 1)
        else:  # 5% - febre
            temperature = round(random.uniform(37.9, 39.2), 1)

        return {
            "value": temperature,
            "unit": "°C",
        }