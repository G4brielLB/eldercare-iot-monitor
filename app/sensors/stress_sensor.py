import random
from .base_sensor import BaseSensor

class StressSensor(BaseSensor):
    def __init__(self, patient_id, status='stable'):
        super().__init__(patient_id, "stress_level")
        if status == 'stable':
            # Nível de estresse inicial estável (5-30)
            self.current_stress = random.randint(0, 60)
        elif status == 'alert':
            # Nível de estresse inicial em alerta (31-60)
            self.current_stress = random.randint(61, 80)
        elif status == 'critical':
            # Nível de estresse inicial crítico (61-100)
            self.current_stress = random.randint(81, 100)
        else:
            # Valor padrão se o status não for reconhecido
            self.current_stress = 40

    
    def generate_data(self):
        """Gera dados de nível de estresse (0-100)"""
        
        variation = random.randint(-3, 3)
        self.current_stress += variation
        # Mantém dentro de limites realistas
        self.current_stress = max(0, min(100, self.current_stress))
        stress = self.current_stress
            
        return {
            "value": stress,
            "unit": "%",
        }
