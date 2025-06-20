import random
from .base_sensor import BaseSensor

class HeartRateSensor(BaseSensor):
    def __init__(self, patient_id, status='stable'):
        super().__init__(patient_id, "heart_rate")
        if status == 'stable':
            # Batimento cardíaco inicial estável (60-100 bpm)
            self.current_heart_rate = random.randint(65, 100)
        elif status == 'alert':
            # Batimento cardíaco inicial em alerta (101-120 bpm ou 40-64)
            self.current_heart_rate = random.randint(101, 120) if random.random() < 0.5 else random.randint(40, 64)
        elif status == 'critical':
            # Batimento cardíaco inicial crítico (acima de 120 bpm ou abaixo de 40)
            self.current_heart_rate = random.randint(121, 200) if random.random() < 0.5 else random.randint(25, 39)
        else:
            # Valor padrão se o status não for reconhecido
            self.current_heart_rate = 75
    
    def generate_data(self):
        """Gera dados de batimento cardíaco com variação gradual"""
        # Varia entre -5 e +5 bpm do valor anterior
        variation = random.randint(-5, 5)
        self.current_heart_rate += variation
        
        # Mantém dentro de limites realistas
        self.current_heart_rate = max(25, min(200, self.current_heart_rate))
            
        return {
            "value": self.current_heart_rate,
            "unit": "bpm",
        }