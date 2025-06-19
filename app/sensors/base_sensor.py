import time
from abc import ABC, abstractmethod

class BaseSensor(ABC):
    """
    Classe base para sensores IoT
    Sensores apenas GERAM dados - não publicam diretamente
    """
    
    def __init__(self, patient_id, sensor_type):
        self.patient_id = patient_id
        self.sensor_type = sensor_type
        
    @abstractmethod
    def generate_data(self):
        """
        Método abstrato - cada sensor implementa sua lógica específica
        
        Returns:
            dict: Dados específicos do sensor (sem metadata)
        """
        pass
    
    def get_sensor_reading(self):
        """
        Retorna leitura completa do sensor com metadata
        
        Returns:
            dict: Dados completos prontos para processamento
        """
        sensor_data = self.generate_data()
        
        return {
            "sensor_type": self.sensor_type,
            "timestamp": time.time(),
            **sensor_data  # Expande os dados específicos do sensor
        }
    
    def __str__(self):
        return f"{self.sensor_type.title()}Sensor({self.patient_id})"
    
    def __repr__(self):
        return self.__str__()