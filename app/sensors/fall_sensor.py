import random
import time
from .base_sensor import BaseSensor

class FallSensor(BaseSensor):
    def __init__(self, patient_id):
        super().__init__(patient_id, "fall_detection")
        self.last_fall_time = 0
    
    def generate_data(self):
        """Detecta quedas (evento raro mas crítico)"""
        current_time = time.time()
        
        # Evita quedas muito próximas (mínimo 5 minutos entre quedas)
        if current_time - self.last_fall_time < 300:
            return {
                "fall_detected": False,
                "status": "monitoring",
                "activity_level": random.choice(["resting", "walking", "sitting"])
            }
        
        # Probabilidade muito baixa de queda (0.5%)
        fall_detected = random.random() < 0.005
        
        if fall_detected:
            self.last_fall_time = current_time
            activity = "fallen"
            status = "ALERT"
        else:
            activity = random.choice([
                "resting", "walking", "sitting", 
                "standing", "light_activity"
            ])
            status = "monitoring"
            
        return {
            "fall_detected": fall_detected,
            "status": status,
            "activity_level": activity
        }