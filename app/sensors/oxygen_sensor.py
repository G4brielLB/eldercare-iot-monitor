import random
from .base_sensor import BaseSensor

class OxygenSensor(BaseSensor):
    def __init__(self, patient_id, status='stable'):
        super().__init__(patient_id, "oxygen_saturation")
        if status == 'stable':
            # Saturação de oxigênio inicial estável (95-100%)
            self.current_oxygen = random.randint(95, 100)
        elif status == 'alert':
            # Saturação de oxigênio inicial em alerta (90-94%)
            self.current_oxygen = random.randint(90, 94)
        elif status == 'critical':
            # Saturação de oxigênio inicial crítica (85-89%)
            self.current_oxygen = random.randint(80, 89)
        else:
            # Valor padrão se o status não for reconhecido
            self.current_oxygen = 98
    
    def generate_data(self):
        """Gera dados de saturação de oxigênio (85-100%)"""
        # Normal: 95-100%
        # Baixo: 90-94% (atenção)
        # Crítico: <90%
        
        variation = random.randint(-1, 1)
        self.current_oxygen += variation
        # Mantém dentro de limites realistas
        self.current_oxygen = max(70, min(100, self.current_oxygen))
        
        oxygen = self.current_oxygen

        return {
            "value": oxygen,
            "unit": "%",
        }