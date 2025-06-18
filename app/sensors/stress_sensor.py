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
            level = "low"
        elif rand < 0.8:  # 30% - moderado
            stress = random.randint(31, 60)
            level = "moderate"
        elif rand < 0.95:  # 15% - alto
            stress = random.randint(61, 80)
            level = "high"
        else:  # 5% - crítico
            stress = random.randint(81, 100)
            level = "critical"
            
        alert = "alert" if stress > 70 else "normal"
            
        return {
            "value": stress,
            "unit": "percentage",
            "level": level,
            "alert_level": alert,
            "description": self._get_description(level)
        }
    
    def _get_description(self, level):
        descriptions = {
            "low": "Relaxado e calmo",
            "moderate": "Ligeiramente estressado",
            "high": "Estresse elevado",
            "critical": "Estresse muito alto"
        }
        return descriptions.get(level, "Normal")