#!/usr/bin/env python3
"""
ElderCare Subscriber - Sistema de Monitoramento de Idosos
Recebe mensagens MQTT das pulseiras e salva em SQLite

Funcionalidades:
- Recebe emergency/summary/heartbeat via MQTT
- Salva dados em SQLite usando módulo database
- Calcula estado atual dos pacientes (SAUDÁVEL/ALERTA/CRÍTICO)
- Monitora conectividade das pulseiras

Estrutura de Estados:
- CRÍTICO: emergência nas últimas 1h
- ALERTA: último resumo = "preocupante" OU emergência nas últimas 24h
- SAUDÁVEL: último resumo = "estavel"/"atencao" E sem emergências recentes
"""

import json
import time
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, MQTT_PORT

# Importar módulo de persistência SQLite
from database import create_health_message, get_patient


class ElderCareSubscriber:
    """
    Subscriber MQTT que:
    1. SALVA apenas emergency e summary em SQLite
    2. PROCESSA heartbeat apenas para status online/offline (NÃO SALVA)
    3. Calcula estado atual dos pacientes
    """
    
    def __init__(self):
        # Status online dos pacientes (apenas em memória)
        self.online_patients = {}  # {patient_id: last_heartbeat_time}
        
        # Estados possíveis
        self.HEALTHY = "ESTÁVEL"
        self.ALERT = "ALERTA" 
        self.CRITICAL = "CRÍTICO"
        self.OFFLINE = "OFFLINE"
        
        # Controle de execução
        self.running = False
        
        # Timeout de heartbeat
        self.heartbeat_timeout = 90    # 90s sem heartbeat = offline
        self.offline_check_interval = 30  # Verifica a cada 30 segundos
        
        # Estatísticas
        self.stats = {
            'messages_received': 0,
            'emergencies_received': 0,
            'summaries_received': 0,
            'heartbeats_processed': 0,  # Só para estatística, não salva
            'start_time': datetime.now()
        }
        
        # Cliente MQTT
        try:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=f"eldercare_subscriber_{int(time.time())}"
            )
        except (AttributeError, TypeError):
            self.client = mqtt.Client(client_id=f"eldercare_subscriber_{int(time.time())}")
        
        print("🔧 ElderCare Subscriber inicializado")
        print(f" SALVA em SQLite: emergency + summary")
        print(f"💓 PROCESSA (não salva): heartbeat")
    
    def _init_files(self):
        """Inicializa arquivos JSON se não existirem"""
        if not os.path.exists(self.messages_file):
            with open(self.messages_file, 'w') as f:
                json.dump([], f, indent=2)
        
        if not os.path.exists(self.patients_file):
            with open(self.patients_file, 'w') as f:
                json.dump({}, f, indent=2)
    
    def start_listening(self):
        """Inicia o subscriber MQTT"""
        print("\n🚀 Iniciando ElderCare Subscriber...")
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Inicia flag de execução
        self.running = True
        
        try:
            print(f"🔗 Conectando ao broker {MQTT_BROKER}:{MQTT_PORT}...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            
            # Inicia thread de monitoramento de timeout em background
            self._start_patient_monitor()
            
            print("👂 Aguardando mensagens MQTT...")
            print("Press Ctrl+C para parar\n")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print(f"\n🛑 Interrompido pelo usuário (Ctrl+C)")
            self._graceful_shutdown()
        except Exception as e:
            print(f"❌ Erro no subscriber: {e}")
            self._graceful_shutdown()
    
    def _graceful_shutdown(self):
        """Desligamento gracioso do subscriber"""
        try:
            print("🔄 Finalizando subscriber...")
            
            # Para thread de monitoramento
            self.running = False
            
            self._show_final_stats()
            
            # Tenta desconectar de forma segura
            if hasattr(self, 'client') and self.client.is_connected():
                print("🔌 Desconectando do broker MQTT...")
                self.client.disconnect()
                self.client.loop_stop()  # Para o loop de forma segura
            
            print("✅ Subscriber finalizado com sucesso")
            
        except Exception as e:
            print(f"⚠️  Erro durante finalização: {e}")
            print("✅ Subscriber finalizado (com avisos)")
    
    def _start_patient_monitor(self):
        """Inicia thread de monitoramento de timeout de pacientes"""
        import threading
        monitor_thread = threading.Thread(target=self._patient_timeout_monitor, daemon=True)
        monitor_thread.start()
        print(f"👁️  Monitor de timeout iniciado (verifica a cada {self.offline_check_interval}s)")
    
    def _patient_timeout_monitor(self):
        """
        Monitor que roda em thread separada
        Verifica se algum paciente ficou offline (sem heartbeat)
        """
        patients_offline = set()  # Track de pacientes já marcados como offline
        
        while self.running:
            try:
                current_time = time.time()
                
                # Verifica cada paciente que já enviou heartbeat
                for patient_id, last_heartbeat in self.online_patients.items():
                    time_since_last = current_time - last_heartbeat
                    
                    if time_since_last > self.heartbeat_timeout:
                        # Paciente ficou offline
                        if patient_id not in patients_offline:
                            print(f"⚠️  PACIENTE OFFLINE: {patient_id} (sem heartbeat há {int(time_since_last)}s)")
                            patients_offline.add(patient_id)
                    else:
                        # Paciente voltou online
                        if patient_id in patients_offline:
                            print(f"✅ PACIENTE ONLINE: {patient_id} (heartbeat recebido)")
                            patients_offline.remove(patient_id)
                
                # Aguarda próxima verificação
                time.sleep(self.offline_check_interval)
                
            except Exception as e:
                print(f"⚠️  Erro no monitor de timeout: {e}")
                time.sleep(self.offline_check_interval)
    
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Callback quando conecta ao broker"""
        if hasattr(reason_code, 'is_failure'):
            if not reason_code.is_failure:
                print("✅ Subscriber conectado ao broker MQTT")
                self._subscribe_to_topics(client)
            else:
                print(f"❌ Falha na conexão: {reason_code}")
        else:
            if reason_code == 0:
                print("✅ Subscriber conectado ao broker MQTT")
                self._subscribe_to_topics(client)
            else:
                print(f"❌ Falha na conexão, código: {reason_code}")
    
    def _subscribe_to_topics(self, client):
        """Subscreve aos tópicos eldercare"""
        client.subscribe("eldercare/+/+", qos=2)
        print("📡 Subscrito aos tópicos: eldercare/+/+")
        print("   🚨 emergency/* - SALVA")
        print("   📊 summary/* - SALVA") 
        print("   💓 heartbeat/* - APENAS status online")
    
    def _on_disconnect(self, client, userdata, reason_code, properties=None, *args):
        """Callback quando desconecta do broker"""
        print(f"🔌 Desconectado do broker MQTT (código: {reason_code})")
    
    def _on_message(self, client, userdata, msg):
        """Callback quando recebe mensagem"""
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) != 3:
                print(f"⚠️  Tópico inválido: {msg.topic}")
                return
                
            message_type = topic_parts[1]
            patient_id = topic_parts[2]
            payload = json.loads(msg.payload.decode())
            
            # HEARTBEAT: Apenas atualiza status online (NÃO REGISTRA)
            if message_type == 'heartbeat':
                self._process_heartbeat_only(patient_id, payload)
                return
            
            # EMERGENCY e SUMMARY: Salva e processa
            if message_type in ['emergency', 'summary']:
                self.stats['messages_received'] += 1
                self._save_medical_message(message_type, patient_id, payload, msg.qos)
                
                if message_type == 'emergency':
                    self.stats['emergencies_received'] += 1
                else:
                    self.stats['summaries_received'] += 1
            else:
                print(f"⚠️  Tipo desconhecido: {message_type}")
                
        except json.JSONDecodeError:
            print(f"❌ Erro decodificando JSON: {msg.topic}")
        except Exception as e:
            print(f"❌ Erro processando mensagem: {e}")
    
    def _process_heartbeat_only(self, patient_id: str, payload: Dict):
        """
        Processa heartbeat APENAS para status online
        NÃO SALVA em arquivo nenhum
        Só marca online se o heartbeat for recente (<= 60s)
        """
        # Extrai timestamp do heartbeat
        created_at = payload.get('created_at')
        if created_at is None:
            print(f"⚠️  Heartbeat de {patient_id} sem 'created_at'. Ignorado.")
            return
        try:
            heartbeat_time = float(created_at)
        except Exception:
            print(f"⚠️  Timestamp inválido no heartbeat de {patient_id}: {created_at}")
            return
        now = time.time()
        age = now - heartbeat_time
        # Só aceita heartbeats dos últimos 60s
        if age > 60:
            print(f"⏳ Heartbeat antigo ignorado para {patient_id} (age={int(age)}s, ts={heartbeat_time})")
            return
        # Atualiza apenas em memória
        self.online_patients[patient_id] = now
        # Estatística (mas não salva)
        self.stats['heartbeats_processed'] += 1
        uptime = payload.get('uptime_seconds', 0)
        print(f"💓 {patient_id} online (uptime: {uptime}s, heartbeat age: {int(age)}s)")
    
    def _save_medical_message(self, message_type: str, patient_id: str, data: Dict, qos: int):
        """Salva APENAS mensagens médicas (emergency + summary) em SQLite"""
        # Verificar se paciente existe no banco
        patient = get_patient(patient_id)
        if not patient:
            print(f"⚠️  Paciente {patient_id} não encontrado no banco. Mensagem ignorada.")
            return
        
        # Extrair timestamp original da mensagem
        created_at = data.get('created_at', time.time())
        if isinstance(created_at, (int, float)):
            original_timestamp = datetime.fromtimestamp(created_at).isoformat()
        else:
            original_timestamp = created_at
        
        # Salvar no SQLite usando módulo database
        message = create_health_message(
            patient_id=patient_id,
            message_type=message_type,
            data=data,
            original_timestamp=original_timestamp
        )
        
        if message:
            # Log de sucesso
            if message_type == 'emergency':
                alerts = data.get('alerts', [])
                print(f"🚨 EMERGÊNCIA salva: {patient_id} - {len(alerts)} alertas")
            else:
                readings_count = data.get('readings_count', 0)
                health_status = data.get('health_status', 'unknown')
                print(f"📊 RESUMO salvo: {patient_id} - {readings_count} leituras, status: {health_status}")
        else:
            print(f"❌ Erro ao salvar mensagem {message_type} para {patient_id}")
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas do subscriber"""
        uptime = datetime.now() - self.stats['start_time']
        online_count = len([p for p, t in self.online_patients.items() 
                          if time.time() - t < self.heartbeat_timeout])
        
        return {
            **self.stats,
            'uptime_seconds': int(uptime.total_seconds()),
            'patients_online': online_count,
            'total_patients': len(self.online_patients)
        }
    
    def _show_final_stats(self):
        """Mostra estatísticas finais"""
        stats = self.get_statistics()
        print(f"\n📊 === ESTATÍSTICAS FINAIS SUBSCRIBER ===")
        print(f"⏱️  Tempo ativo: {stats['uptime_seconds']} segundos")
        print(f"📨 Mensagens salvas no SQLite: {stats['messages_received']}")
        print(f"🚨 Emergências salvas: {stats['emergencies_received']}")
        print(f"📊 Resumos salvos: {stats['summaries_received']}")
        print(f"💓 Heartbeats processados (não salvos): {stats['heartbeats_processed']}")
        print(f"👥 Pacientes monitorados: {stats['total_patients']}")
        print(f"🟢 Pacientes online: {stats['patients_online']}")

if __name__ == "__main__":
    subscriber = ElderCareSubscriber()
    subscriber.start_listening()