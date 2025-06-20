import os
from dotenv import load_dotenv

load_dotenv()

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_KEEPALIVE = 60

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "eldercare"

# Topics MQTT
MQTT_TOPICS = {
    "heart_rate": "eldercare/+/heart_rate",
    "stress_level": "eldercare/+/stress_level",  # 0-100
    "temperature": "eldercare/+/temperature",
    "fall_detection": "eldercare/+/fall_detection",
    "oxygen_saturation": "eldercare/+/oxygen_saturation"
}

# IDs dos pacientes para simulação
PATIENT_IDS = ["PAT001", "PAT002", "PAT003", "PAT004"]

# Alertas - valores críticos
ALERT_THRESHOLDS = {
    "heart_rate": {"min": 60, "max": 100},
    "stress_level": {"min": 0, "max": 70},  # Acima de 70 = estresse alto
    "temperature": {"min": 36.1, "max": 37.5},
    "oxygen_saturation": {"min": 95, "max": 100}
}

# Níveis de estresse (para interpretação)
STRESS_LEVELS = {
    "low": {"min": 0, "max": 30, "description": "Relaxado"},
    "moderate": {"min": 31, "max": 60, "description": "Moderado"},
    "high": {"min": 61, "max": 85, "description": "Estressado"},
    "critical": {"min": 86, "max": 100, "description": "Muito estressado"}
}

# Unidades de sensores
SENSOR_UNITS = {
    "heart_rate": "bpm",
    "stress_level": "%",
    "temperature": "°C",
    "oxygen_saturation": "%"
}