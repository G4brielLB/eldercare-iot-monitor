import time
import threading
import random
from typing import List, Dict
from .heart_rate_sensor import HeartRateSensor
from .stress_sensor import StressSensor
from .temperature_sensor import TemperatureSensor
from .oxygen_sensor import OxygenSensor
from .fall_sensor import FallSensor
from .edge_processor import EdgeProcessor
from .pulseira_publisher import PulseiraPublisher

class SmartPulseira:
    """
    Simulação completa de uma pulseira IoT inteligente
    Integra sensores + processamento edge + comunicação MQTT
    """
    
    def __init__(self, patient_id: str, 
                 oxygen_status: str = 'stable', 
                 stress_status: str = 'stable',
                 temp_status: str = 'stable',
                 heart_rate_status: str = 'stable',
                 fall_chance: str = 'low'
                ):
        self.patient_id = patient_id
        self.running = False
        
        # === COMPONENTES PRINCIPAIS ===
        print(f"🔧 Inicializando pulseira inteligente para {patient_id}...")
        
        # 1. Sensores IoT
        self.sensors = [
            HeartRateSensor(patient_id, status=heart_rate_status),
            StressSensor(patient_id, status=stress_status),
            TemperatureSensor(patient_id, status=temp_status),
            OxygenSensor(patient_id, status=oxygen_status),
            FallSensor(patient_id, chance=fall_chance)
        ]
        
        # 2. Processador de borda (inteligência)
        self.edge_processor = EdgeProcessor(patient_id)
        
        # 3. Publisher MQTT (comunicação)
        self.publisher = PulseiraPublisher(patient_id)
        
        # === CONFIGURAÇÕES ===
        self.reading_interval = (8, 15)  # Intervalo entre leituras (segundos)
        self.heartbeat_interval = 30     # Heartbeat a cada 30 segundos
        self.last_heartbeat = 0
        
        # === ESTATÍSTICAS ===
        self.stats = {
            'readings_collected': 0,
            'emergencies_detected': 0,
            'summaries_sent': 0,
            'uptime_start': None,
            'sensor_errors': 0
        }
        
        print(f"✅ Pulseira {patient_id} inicializada com {len(self.sensors)} sensores")
    
    def start_monitoring(self, duration_seconds: int = 300):
        """
        Inicia monitoramento inteligente da pulseira
        
        Args:
            duration_seconds: Duração total do monitoramento (default: 5 minutos)
        """
        print(f"🚀 Iniciando monitoramento inteligente para {self.patient_id}")
        print(f"⏱️  Duração: {duration_seconds} segundos")
        print(f"📊 Intervalo de leitura: {self.reading_interval[0]}-{self.reading_interval[1]}s")
        
        # Conecta ao MQTT
        if not self.publisher.connect():
            print(f"❌ Falha na conexão MQTT. Abortando monitoramento.")
            return False
        
        # Inicia monitoramento
        self.running = True
        self.stats['uptime_start'] = time.time()
        
        try:
            # Thread para heartbeat periódico
            heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
            heartbeat_thread.daemon = True
            heartbeat_thread.start()
            
            # Loop principal de monitoramento
            self._main_monitoring_loop(duration_seconds)
            
        except KeyboardInterrupt:
            print(f"\n🛑 Interrompido pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro no monitoramento: {e}")
        finally:
            self.stop_monitoring()
        
        return True
    
    def _main_monitoring_loop(self, duration_seconds: int):
        """Loop principal de coleta e processamento"""
        start_time = time.time()
        cycle_count = 0
        
        while self.running and (time.time() - start_time) < duration_seconds:
            cycle_count += 1
            cycle_start = time.time()
            
            print(f"\n📋 === CICLO {cycle_count} ===")
            
            # 1. COLETA dados de todos os sensores
            all_readings = self._collect_sensor_data()
            
            if all_readings:
                # 2. PROCESSA no EdgeProcessor
                processing_result = self.edge_processor.process_sensor_readings(all_readings)
                
                # 3. AÇÃO baseada na decisão do processador
                self._handle_processing_result(processing_result)
                
                self.stats['readings_collected'] += len(all_readings)
            else:
                print("⚠️ Nenhum dado coletado neste ciclo")
            
            # 4. AGUARDA próximo ciclo (intervalo variável)
            sleep_time = random.uniform(self.reading_interval[0], self.reading_interval[1])
            print(f"😴 Aguardando {sleep_time:.1f}s para próximo ciclo...")
            time.sleep(sleep_time)
        
        print(f"\n🏁 Monitoramento finalizado após {cycle_count} ciclos")
    
    def _collect_sensor_data(self) -> List[Dict]:
        """Coleta dados de todos os sensores"""
        all_readings = []
        
        print("📡 Coletando dados dos sensores...")
        
        for sensor in self.sensors:
            try:
                reading = sensor.get_sensor_reading()
                all_readings.append(reading)
                
                # Log resumido
                value = reading.get('value', 'N/A')
                unit = reading.get('unit', '')
                print(f"   {sensor.sensor_type}: {value} {unit}")
                
            except Exception as e:
                print(f"❌ Erro no sensor {sensor.sensor_type}: {e}")
                self.stats['sensor_errors'] += 1
        
        return all_readings
    
    def _handle_processing_result(self, result: Dict):
        """Trata resultado do processamento EdgeProcessor"""
        action = result.get('action')
        
        if action == 'emergency':
            self._handle_emergency(result)
        elif action == 'summary':
            self._handle_summary(result)
        elif action == 'buffer':
            self._handle_buffer(result)
        else:
            print(f"⚠️ Ação desconhecida: {action}")
    
    def _handle_emergency(self, result: Dict):
        """Trata emergência detectada"""
        print("🚨 === EMERGÊNCIA DETECTADA ===")
        
        emergency_data = result.get('data', {})
        alerts = emergency_data.get('alerts', [])
        
        for alert in alerts:
            alert_type = alert.get('type', 'UNKNOWN')
            message = alert.get('message', 'Sem detalhes')
            print(f"   🚨 {alert_type}: {message}")
        
        # Envia emergência via MQTT
        success = self.publisher.send_emergency(emergency_data)
        if success:
            self.stats['emergencies_detected'] += 1
            print("✅ Emergência enviada com sucesso")
        else:
            print("❌ Falha no envio da emergência")
    
    def _handle_summary(self, result: Dict):
        """Trata resumo estatístico"""
        print("📊 === ENVIANDO RESUMO ===")
        
        summary_data = result.get('data', {})
        readings_count = summary_data.get('readings_count', 0)
        health_status = summary_data.get('health_status', 'unknown')
        
        print(f"   📋 Período: {readings_count} leituras")
        print(f"   🏥 Status: {health_status}")
        
        # Mostra estatísticas principais
        stats = summary_data.get('statistics', {})
        for sensor_type, sensor_stats in stats.items():
            avg = sensor_stats.get('avg', 'N/A')
            print(f"   📈 {sensor_type}: média {avg}")
        
        # Envia resumo via MQTT
        success = self.publisher.send_summary(summary_data)
        if success:
            self.stats['summaries_sent'] += 1
            print("✅ Resumo enviado com sucesso")
        else:
            print("❌ Falha no envio do resumo")
    
    def _handle_buffer(self, result: Dict):
        """Trata dados adicionados ao buffer"""
        buffer_size = result.get('buffer_size', 0)
        print(f"💾 Dados no buffer: {buffer_size} leituras")
    
    def _heartbeat_loop(self):
        """Loop de heartbeat em background"""
        while self.running:
            current_time = time.time()
            
            if current_time - self.last_heartbeat >= self.heartbeat_interval:
                self.publisher.send_heartbeat()
                self.last_heartbeat = current_time
            
            time.sleep(5)  # Verifica heartbeat a cada 5 segundos
    
    def stop_monitoring(self):
        """Para o monitoramento e desconecta"""
        print(f"🛑 Parando monitoramento da pulseira {self.patient_id}...")
        self.running = False
        
        # Desconecta do MQTT
        self.publisher.disconnect()
        
        # Mostra estatísticas finais
        self._show_final_stats()
    
    def _show_final_stats(self):
        """Mostra estatísticas finais da pulseira"""
        if self.stats['uptime_start']:
            uptime = time.time() - self.stats['uptime_start']
        else:
            uptime = 0
        
        print(f"\n📊 === ESTATÍSTICAS FINAIS - {self.patient_id} ===")
        print(f"⏱️  Tempo ativo: {uptime:.1f} segundos")
        print(f"📡 Leituras coletadas: {self.stats['readings_collected']}")
        print(f"🚨 Emergências detectadas: {self.stats['emergencies_detected']}")
        print(f"📋 Resumos enviados: {self.stats['summaries_sent']}")
        print(f"❌ Erros de sensor: {self.stats['sensor_errors']}")
        
        # Status do EdgeProcessor
        edge_status = self.edge_processor.get_status()
        print(f"💾 Buffer atual: {edge_status['buffer_size']} entradas")
        
        # Status do Publisher
        pub_status = self.publisher.get_connection_status()
        pub_stats = pub_status.get('statistics', {})
        print(f"📤 Emergências enviadas: {pub_stats.get('emergency_sent', 0)}")
        # print(f"📤 Resumos enviados: {pub_stats.get('summary_sent', 0)}")
        print(f"💓 Heartbeats enviados: {pub_stats.get('heartbeat_sent', 0)}")
    
    def get_real_time_status(self) -> Dict:
        """Retorna status em tempo real da pulseira"""
        return {
            'patient_id': self.patient_id,
            'running': self.running,
            'uptime': time.time() - (self.stats['uptime_start'] or time.time()),
            'stats': self.stats.copy(),
            'edge_processor': self.edge_processor.get_status(),
            'publisher': self.publisher.get_connection_status(),
            'sensors_count': len(self.sensors)
        }

