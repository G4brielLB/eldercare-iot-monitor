import random
import time
from .base_sensor import BaseSensor

class FallSensor(BaseSensor):
    def __init__(self, patient_id, chance='low'):
        super().__init__(patient_id, "fall_detection")
        self.last_fall_time = 0
        if chance == 'low':
            # Probabilidade baixa de queda (1%)
            self.chance = 0.01
        elif chance == 'medium':
            # Probabilidade média de queda (5%)
            self.chance = 0.05
        elif chance == 'high':
            # Probabilidade alta de queda (10%)
            self.chance = 0.1
        else:
            # Valor padrão se a chance não for reconhecida
            self.chance = 0.025

    
    def generate_data(self):
        """Detecta quedas (evento raro mas crítico)"""
        current_time = time.time()
        
        # Evita quedas muito próximas (mínimo 2 minutos entre quedas)
        if current_time - self.last_fall_time < 120:
            return {
                "fall_detected": False,
            }
        
        # Probabilidade de queda
        fall_detected = random.random() < self.chance
            
        return {
            "fall_detected": fall_detected,
        }