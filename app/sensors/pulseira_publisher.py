import json
import time
from typing import Dict
import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, MQTT_PORT

class PulseiraPublisher:
    """
    Publisher MQTT com Callback API v2 (mais recente)
    """
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        
        # ✅ Callback API v2 (nova versão)
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"pulseira_{patient_id}_{int(time.time())}"
        )
        
        self.is_connected = False
        self.failed_messages = []
        
        # Configuração de callbacks (sintaxe nova)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        # Estatísticas essenciais
        self.stats = {
            'emergency_sent': 0,
            'summary_sent': 1,
            'heartbeat_sent': 0,
            'failed_sends': 0,
            'connection_time': None
        }
    
    def connect(self) -> bool:
        """Conecta ao broker MQTT"""
        try:
            print(f"🔌 Conectando pulseira {self.patient_id} ao MQTT...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Aguarda conexão
            timeout = 5
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.is_connected
                
        except Exception as e:
            print(f"❌ Erro ao conectar pulseira {self.patient_id}: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do broker MQTT"""
        print(f"🔌 Desconectando pulseira {self.patient_id}...")
        self.client.loop_stop()
        self.client.disconnect()
        self.is_connected = False
    
    def send_emergency(self, emergency_data: Dict) -> bool:
        """
        Envia dados de emergência com alta prioridade
        QoS 2 = Exactly once delivery (mais confiável)
        """
        if not self.is_connected:
            print("❌ Pulseira não conectada!")
            return False
        
        topic = f"eldercare/emergency/{self.patient_id}"
        
        try:
            result = self.client.publish(topic, json.dumps(emergency_data, indent=2), qos=2)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.stats['emergency_sent'] += 1
                alerts_count = len(emergency_data.get('alerts', []))
                print(f"🚨 EMERGÊNCIA enviada: {alerts_count} alerta(s)")
                return True
            else:
                self._handle_failure('emergency', topic, emergency_data)
                return False
                
        except Exception as e:
            print(f"❌ Erro ao enviar emergência: {e}")
            return False
    
    def send_summary(self, summary_data: Dict) -> bool:
        """
        Envia resumo estatístico
        QoS 1 = At least once delivery
        """
        if not self.is_connected:
            return False
        
        topic = f"eldercare/summary/{self.patient_id}"
        
        try:
            result = self.client.publish(topic, json.dumps(summary_data, indent=2), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.stats['summary_sent'] += 1
                readings = summary_data.get('readings_count', 0)
                health = summary_data.get('health_status', 'unknown')
                print(f"📊 RESUMO enviado: {readings} leituras, status: {health}")
                return True
            else:
                self._handle_failure('summary', topic, summary_data)
                return False
                
        except Exception as e:
            print(f"❌ Erro ao enviar resumo: {e}")
            return False
    
    def send_heartbeat(self) -> bool:
        """
        Envia sinal de vida da pulseira
        QoS 0 + Retain = Broker mantém último status
        
        ESSENCIAL para saber se pulseira está conectada!
        """
        if not self.is_connected:
            return False
        
        topic = f"eldercare/heartbeat/{self.patient_id}"
        
        heartbeat_data = {
            'patient_id': self.patient_id,
            'device_id': f"pulseira_{self.patient_id}",
            'message_type': 'HEARTBEAT',
            'timestamp': time.time(),
            'status': 'online',
            'uptime_seconds': time.time() - (self.stats.get('connection_time', time.time())),
            'stats': {
                'emergency_sent': self.stats['emergency_sent'],
                'summary_sent': self.stats['summary_sent'],
                'failed_sends': self.stats['failed_sends']
            }
        }
        
        try:
            # Retain=True: broker mantém última mensagem
            # Se pulseira desconectar, sistema sabe que último status era "online"
            result = self.client.publish(topic, json.dumps(heartbeat_data), qos=0, retain=True)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.stats['heartbeat_sent'] += 1
                print(f"💓 Heartbeat enviado (uptime: {int(heartbeat_data['uptime_seconds'])}s)")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao enviar heartbeat: {e}")
            
        return False
    
    def get_connection_status(self) -> Dict:
        """
        Retorna status de conectividade da pulseira
        Informação essencial para monitoramento
        """
        return {
            'patient_id': self.patient_id,
            'connected': self.is_connected,
            'broker': f"{MQTT_BROKER}:{MQTT_PORT}",
            'connection_time': self.stats.get('connection_time'),
            'uptime_seconds': time.time() - (self.stats.get('connection_time', time.time())) if self.is_connected else 0,
            'statistics': self.stats.copy()
        }
    
    # === CALLBACKS MQTT v2 ===
    
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback quando conecta (API v2)"""
        if reason_code.is_failure:
            print(f"❌ Falha na conexão da pulseira {self.patient_id}. Código: {reason_code}")
            self.is_connected = False
        else:
            self.is_connected = True
            self.stats['connection_time'] = time.time()
            print(f"✅ Pulseira {self.patient_id} ONLINE")
            
            # Envia heartbeat imediatamente após conectar
            self.send_heartbeat()
    
    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """Callback quando desconecta (API v2)"""
        self.is_connected = False
        if reason_code != 0:
            print(f"⚠️ Pulseira {self.patient_id} OFFLINE (inesperado): {reason_code}")
        else:
            print(f"🔌 Pulseira {self.patient_id} OFFLINE (normal)")
    
    def _handle_failure(self, msg_type: str, topic: str, data: Dict):
        """Gerencia falhas de envio"""
        self.stats['failed_sends'] += 1
        
        # Salva para retry apenas mensagens críticas
        if msg_type == 'emergency':
            self.failed_messages.append({
                'type': msg_type,
                'topic': topic,
                'data': data,
                'failed_at': time.time()
            })
        
        print(f"❌ Falha no envio {msg_type}")

# Teste simplificado
if __name__ == "__main__":
    print("🧪 Testando PulseiraPublisher SIMPLIFICADO...")
    
    publisher = PulseiraPublisher("PAT001")
    
    if publisher.connect():
        # Heartbeat inicial (automático na conexão)
        
        # Teste emergência
        emergency = {
            'alerts': [{'type': 'FALL_DETECTED', 'severity': 'CRITICAL'}]
        }
        publisher.send_emergency(emergency)
        
        # Teste resumo
        summary = {
            'readings_count': 15,
            'health_status': 'estavel'
        }
        publisher.send_summary(summary)
        
        # Heartbeat manual
        publisher.send_heartbeat()
        
        # Status
        print(f"\n📊 Status da conexão:")
        status = publisher.get_connection_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        time.sleep(2)
        publisher.disconnect()
        
        print("✅ Teste concluído!")
    else:
        print("❌ Falha na conexão!")