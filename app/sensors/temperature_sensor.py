import random
from .base_sensor import BaseSensor

class TemperatureSensor(BaseSensor):
    def __init__(self, patient_id, status='stable'):
        super().__init__(patient_id, "temperature")
        if status == 'stable':
            # Temperatura corporal inicial estável (36.0-37.0°C)
            self.current_temperature = round(random.uniform(36.0, 37.0), 1)
        elif status == 'alert':
            # Temperatura corporal inicial em alerta (37.1-38.9°C) ou (35.0-35.9°C)
            self.current_temperature = round(random.uniform(37.1, 38.9), 1) if random.random() < 0.5 else round(random.uniform(35.0, 35.9), 1)
        elif status == 'critical':
            # Temperatura corporal inicial crítica (39.0-40.0°C)
            self.current_temperature = round(random.uniform(39.0, 40.0), 1) if random.random() < 0.5 else round(random.uniform(34.0, 34.9), 1)
        else:
            # Valor padrão se o status não for reconhecido
            self.current_temperature = 36.5
    
    def generate_data(self):
        """Gera dados de temperatura corporal (35.5-38.5°C)"""
        # Variação natural com chance de febre
        
        variation = round(random.uniform(-0.1, 0.1), 1)

        self.current_temperature += variation
        # Mantém dentro de limites realistas
        self.current_temperature = max(34.0, min(40.0, self.current_temperature))
        temperature = self.current_temperature

        return {
            "value": temperature,
            "unit": "°C",
        }