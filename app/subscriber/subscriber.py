#!/usr/bin/env python3
"""
ElderCare Subscriber - Sistema de Monitoramento de Idosos
Recebe mensagens MQTT das pulseiras e processa dados

Funcionalidades:
- Recebe emergency/summary/heartbeat via MQTT
- Salva dados em JSON (temporário, migrar para SQLite)
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
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, MQTT_PORT


class ElderCareSubscriber:
    """
    Subscriber MQTT que:
    1. SALVA apenas emergency e summary em JSON
    2. PROCESSA heartbeat apenas para status online/offline (NÃO SALVA)
    3. Calcula estado atual dos pacientes
    """
    
    def __init__(self):
        # Arquivos de armazenamento (apenas dados médicos)
        self.data_dir = "data"
        self.messages_file = os.path.join(self.data_dir, "messages.json")
        self.patients_file = os.path.join(self.data_dir, "patients_status.json")
        
        # Status online dos pacientes (apenas em memória)
        self.online_patients = {}  # {patient_id: last_heartbeat_time}
        
        # Estados possíveis
        self.HEALTHY = "ESTÁVEL"
        self.ALERT = "ALERTA" 
        self.CRITICAL = "CRÍTICO"
        self.OFFLINE = "OFFLINE"
        
        # Apenas timeout de heartbeat
        self.heartbeat_timeout = 90    # 90s sem heartbeat = offline
        
        # Estatísticas
        self.stats = {
            'messages_received': 0,
            'emergencies_received': 0,
            'summaries_received': 0,
            'heartbeats_processed': 0,  # Só para estatística, não salva
            'start_time': datetime.now()
        }
        
        # Garante que diretório existe
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Inicializa arquivos se não existirem
        self._init_files()
        
        # Cliente MQTT
        try:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=f"eldercare_subscriber_{int(time.time())}"
            )
        except (AttributeError, TypeError):
            self.client = mqtt.Client(client_id=f"eldercare_subscriber_{int(time.time())}")
        
        print("🔧 ElderCare Subscriber inicializado")
        print(f"📁 Diretório de dados: {self.data_dir}")
        print(f"💾 SALVA: emergency + summary")
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
        
        try:
            print(f"🔗 Conectando ao broker {MQTT_BROKER}:{MQTT_PORT}...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            
            print("👂 Aguardando mensagens MQTT...")
            print("Press Ctrl+C para parar\n")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n⏹️  Parando subscriber...")
            self._show_final_stats()
            self.client.disconnect()
        except Exception as e:
            print(f"❌ Erro no subscriber: {e}")
    
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
    
    def _on_disconnect(self, client, userdata, reason_code, properties=None):
        """Callback quando desconecta do broker"""
        print(f"🔌 Desconectado do broker MQTT")
    
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
                self._update_patient_status(patient_id, message_type, payload)
                
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
        """
        current_time = time.time()
        
        # Atualiza apenas em memória
        self.online_patients[patient_id] = current_time
        
        # Estatística (mas não salva)
        self.stats['heartbeats_processed'] += 1
        
        # Log mínimo
        uptime = payload.get('uptime_seconds', 0)
        print(f"💓 {patient_id} online (uptime: {uptime}s)")
    
    def _save_medical_message(self, message_type: str, patient_id: str, payload: Dict, qos: int):
        """Salva APENAS mensagens médicas (emergency + summary)"""
        medical_message = {
            'id': f"{patient_id}_{message_type}_{int(time.time() * 1000)}",
            'received_at': datetime.now().isoformat(),
            'message_type': message_type,
            'patient_id': patient_id,
            'qos': qos,
            'payload': payload
        }
        
        # Carrega e adiciona
        try:
            with open(self.messages_file, 'r') as f:
                messages = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            messages = []
        
        messages.append(medical_message)
        
        # Salva
        with open(self.messages_file, 'w') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        
        # Log
        if message_type == 'emergency':
            alerts = payload.get('alerts', [])
            print(f"🚨 EMERGÊNCIA salva: {patient_id} - {len(alerts)} alertas")
        else:
            readings_count = payload.get('readings_count', 0)
            health_status = payload.get('health_status', 'unknown')
            print(f"📊 RESUMO salvo: {patient_id} - {readings_count} leituras, status: {health_status}")
    
    def _update_patient_status(self, patient_id: str, message_type: str, payload: Dict):
        """Atualiza estado baseado na mensagem recebida (não no tempo)"""
        try:
            with open(self.patients_file, 'r') as f:
                patients = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            patients = {}
        
        # Inicializa paciente se não existe
        if patient_id not in patients:
            patients[patient_id] = {
                'patient_id': patient_id,
                'current_status': self.HEALTHY,
                'last_emergency': None,
                'last_summary': None,
                'last_update': None
            }
        
        current_time = datetime.now().isoformat()
        
        # Atualiza baseado no tipo
        if message_type == 'emergency':
            patients[patient_id]['last_emergency'] = current_time
            patients[patient_id]['current_status'] = self.CRITICAL
            
        elif message_type == 'summary':
            patients[patient_id]['last_summary'] = current_time
            
            # Estado baseado no health_status do EdgeProcessor
            health_status = payload.get('health_status', 'unknown')
            if health_status == 'preocupante':
                patients[patient_id]['current_status'] = self.ALERT
            elif health_status in ['estavel', 'atencao']:
                patients[patient_id]['current_status'] = self.HEALTHY
        
        patients[patient_id]['last_update'] = current_time
        
        # Salva
        with open(self.patients_file, 'w') as f:
            json.dump(patients, f, indent=2, ensure_ascii=False)
    
    def get_patients_status(self) -> Dict:
        """Retorna status atual de todos os pacientes"""
        try:
            with open(self.patients_file, 'r') as f:
                patients = json.load(f)
            
            # Adiciona status online/offline baseado no heartbeat
            current_time = time.time()
            for patient_id, data in patients.items():
                last_heartbeat = self.online_patients.get(patient_id, 0)
                is_online = (current_time - last_heartbeat) < self.heartbeat_timeout
                data['online_status'] = 'ONLINE' if is_online else 'OFFLINE'
                if last_heartbeat > 0:
                    data['last_heartbeat'] = datetime.fromtimestamp(last_heartbeat).isoformat()
                else:
                    data['last_heartbeat'] = None
            
            return patients
        except Exception:
            return {}
    
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
        print(f"📨 Mensagens salvas: {stats['messages_received']}")
        print(f"🚨 Emergências salvas: {stats['emergencies_received']}")
        print(f"📊 Resumos salvos: {stats['summaries_received']}")
        print(f"💓 Heartbeats processados (não salvos): {stats['heartbeats_processed']}")
        print(f"👥 Pacientes monitorados: {stats['total_patients']}")
        print(f"🟢 Pacientes online: {stats['patients_online']}")

if __name__ == "__main__":
    subscriber = ElderCareSubscriber()
    subscriber.start_listening()