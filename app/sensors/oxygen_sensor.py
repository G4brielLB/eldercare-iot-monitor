import random
from .base_sensor import BaseSensor

class OxygenSensor(BaseSensor):
    def __init__(self, patient_id):
        super().__init__(patient_id, "oxygen_saturation")
    
    def generate_data(self):
        """Gera dados de saturação de oxigênio (85-100%)"""
        # Normal: 95-100%
        # Baixo: 90-94% (atenção)
        # Crítico: <90%
        
        rand = random.random()
        
        if rand < 0.7:  # 70% - normal
            oxygen = random.randint(95, 100)
        elif rand < 0.9:  # 20% - baixo
            oxygen = random.randint(90, 94)
        else:  # 10% - crítico
            oxygen = random.randint(85, 89)
            
        return {
            "value": oxygen,
            "unit": "%",
        }