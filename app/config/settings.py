import os
from dotenv import load_dotenv

load_dotenv()

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_KEEPALIVE = 60

# Unidades de sensores
SENSOR_UNITS = {
    "heart_rate": "bpm",
    "stress_level": "%",
    "temperature": "°C",
    "oxygen_saturation": "%"
}