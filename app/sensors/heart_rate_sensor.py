import random
from .base_sensor import BaseSensor

class HeartRateSensor(BaseSensor):
    def __init__(self, patient_id):
        super().__init__(patient_id, "heart_rate")
        self.current_heart_rate = random.randint(50, 150)
    
    def generate_data(self):
        """Gera dados de batimento cardíaco com variação gradual"""
        # Varia entre -5 e +5 bpm do valor anterior
        variation = random.randint(-5, 5)
        self.current_heart_rate += variation
        
        # Mantém dentro de limites realistas
        self.current_heart_rate = max(40, min(200, self.current_heart_rate))
            
        return {
            "value": self.current_heart_rate,
            "unit": "bpm",
        }