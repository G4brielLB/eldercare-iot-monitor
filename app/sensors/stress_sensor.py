import random
from .base_sensor import BaseSensor

class StressSensor(BaseSensor):
    def __init__(self, patient_id):
        super().__init__(patient_id, "stress_level")
    
    def generate_data(self):
        """Gera dados de nível de estresse (0-100)"""
        rand = random.random()
        
        if rand < 0.5:  # 50% - baixo estresse
            stress = random.randint(5, 30)
        elif rand < 0.8:  # 30% - moderado
            stress = random.randint(31, 60)
        elif rand < 0.95:  # 15% - alto
            stress = random.randint(61, 80)
        else:  # 5% - crítico
            stress = random.randint(81, 100)
            
        return {
            "value": stress,
            "unit": "%",
        }
