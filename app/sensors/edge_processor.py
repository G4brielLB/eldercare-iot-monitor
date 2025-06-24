import time
from typing import List, Dict, Optional
from config.settings import SENSOR_UNITS

class EdgeProcessor:
    """
    Processador de borda - Inteligência da pulseira IoT
    Recebe dados de múltiplos sensores e decide o que enviar
    """
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.normal_data_buffer = []
        self.last_summary_sent = time.time()
        self.summary_interval = 60  # 1 minutos entre resumos
        self.emergency_cooldown = 30  # 1 minuto entre emergências
        self.last_emergency_time = 0
        
    def process_sensor_readings(self, sensor_readings: List[Dict]) -> Dict:
        """
        Processa múltiplas leituras de sensores e decide ação
        
        Args:
            sensor_readings: Lista de dados de todos os sensores
            
        Returns:
            Dict com decisão: 'emergency', 'summary', 'buffer' ou 'ignore'
        """

        # Adiciona ao buffer de dados normais
        self._add_to_buffer(sensor_readings)
        
        # Verifica alertas críticos primeiro
        emergency_result = self._check_emergency_conditions(sensor_readings)
        if emergency_result:
            return emergency_result
        
        
        # Verifica se deve enviar resumo
        if self._should_send_summary():
            return self._create_summary_result()
        
        # Apenas adiciona ao buffer, não envia nada
        return {
            'action': 'buffer',
            'message': f'Dados adicionados ao buffer ({len(self.normal_data_buffer)} readings)',
            'buffer_size': len(self.normal_data_buffer)
        }
    
    def _check_emergency_conditions(self, readings: List[Dict]) -> Optional[Dict]:
        """
        Verifica condições de emergência analisando múltiplos sensores
        
        Returns:
            Dict com dados de emergência ou None se não há emergência
        """
        current_time = time.time()
        
        # Cooldown entre emergências (evita spam)
        if current_time - self.last_emergency_time < self.emergency_cooldown:
            return None
        
        # Organiza readings por tipo de sensor
        sensor_data = {}
        for reading in readings:
            sensor_type = reading.get('sensor_type')
            sensor_data[sensor_type] = reading
        
        # Verifica condições críticas individuais
        critical_alerts = []
        
        # 1. Queda detectada = EMERGÊNCIA IMEDIATA
        fall_data = sensor_data.get('fall_detection')
        if fall_data and fall_data.get('fall_detected'):
            critical_alerts.append({
                'type': 'FALL_DETECTED',
                'message': 'Queda detectada!'
            })
        
        # 2. Oxigenação crítica
        oxygen_data = sensor_data.get('oxygen_saturation')
        if oxygen_data and oxygen_data.get('value', 100) < 90:
            critical_alerts.append({
                'type': 'LOW_OXYGEN',
                'value': oxygen_data.get('value'),
                'message': f"Oxigenação crítica: {oxygen_data.get('value')}%"
            })
        
        # 3. Temperatura extrema
        temp_data = sensor_data.get('temperature')
        if temp_data:
            temp_value = temp_data.get('value', 36.5)
            if temp_value < 35.0 or temp_value > 39.0:
                critical_alerts.append({
                    'type': 'EXTREME_TEMPERATURE',
                    'value': temp_value,
                    'message': f"Temperatura extrema: {temp_value}°C"
                })
        
        # 4. Batimento cardíaco crítico
        heart_data = sensor_data.get('heart_rate')
        if heart_data:
            heart_rate = heart_data.get('value', 70)
            if heart_rate < 40 or heart_rate > 120:
                critical_alerts.append({
                'type': 'CRITICAL_HEART_RATE',
                'value': heart_rate,
                'message': f"Batimento cardíaco crítico: {heart_rate} bpm"
            })
        
        # 5. Nível de stress crítico
        stress_data = sensor_data.get('stress_level')
        if stress_data:
            stress_level = stress_data.get('value', 20)
            if stress_level > 80:
                critical_alerts.append({
                'type': 'HIGH_STRESS',
                'value': stress_level,
                'message': f"Nível de stress crítico: {stress_level}%"
            })
        
        # Se há alertas críticos, cria emergência
        if critical_alerts:
            self.last_emergency_time = current_time
            
            critical_message = self._create_unified_message(
                message_type='emergency',
                patient_id=self.patient_id,
                severity='critical',
                health_status='critical',
                statistics=readings,
                alerts=critical_alerts,
                context_data=self._get_recent_context()
            )

            return {
                'action': 'emergency',
                'priority': 'critical',
                'channel': f'eldercare/emergency/{self.patient_id}',
                'data': critical_message
            }
        
        return None
    
    def _add_to_buffer(self, readings: List[Dict]):
        """Adiciona leituras ao buffer de dados normais"""
        timestamp = time.time()
        
        buffer_entry = {
            'timestamp': timestamp,
            'readings': readings,
            'readings_count': len(readings)
        }
        
        self.normal_data_buffer.append(buffer_entry)
        
        # Limita o buffer (evita crescimento infinito)
        if len(self.normal_data_buffer) > 100:
            self.normal_data_buffer.pop(0)  # Remove o mais antigo
    
    def _should_send_summary(self) -> bool:
        """Verifica se deve enviar resumo dos dados normais"""
        current_time = time.time()
        time_elapsed = current_time - self.last_summary_sent
        
        # Envia resumo se: tempo passou E tem dados no buffer
        return (time_elapsed >= self.summary_interval and 
                len(self.normal_data_buffer) > 0)
    
    def _create_summary_result(self) -> Dict:
        """Cria resultado com resumo estatístico"""
        if not self.normal_data_buffer:
            return {'action': 'ignore', 'message': 'Buffer vazio'}
        
        current_time = time.time()
        
        # Calcula estatísticas por sensor
        stats = self._calculate_statistics()
        
        health_status, health_alerts = self._assess_overall_health(stats)
        
        summary_data = self._create_unified_message(
            message_type='summary',
            patient_id=self.patient_id,
            severity='normal',
            health_status=health_status,
            alerts=health_alerts,
            statistics=stats,
            readings_count=len(self.normal_data_buffer),
            period_start=self.normal_data_buffer[0]['timestamp'],
            period_end=current_time
        )
        
        # Limpa buffer e atualiza timestamp
        self.normal_data_buffer.clear()
        self.last_summary_sent = current_time
        
        return {
            'action': 'summary',
            'priority': 'normal',
            'channel': f'eldercare/summary/{self.patient_id}',
            'data': summary_data
        }
    
    def _create_unified_message(self, message_type: str, **kwargs) -> Dict:
        """Centraliza criação de estrutura unificada"""
        
        # CAMPOS COMUNS (definidos uma vez só)
        base_message = {
            'message_type': message_type,
            'timestamp': time.time(),
            'patient_id': self.patient_id,
            #'severity': kwargs.get('severity', 'normal'),
            'health_status': kwargs.get('health_status', 'stable'),
            'alerts': kwargs.get('alerts', []),
            'statistics': kwargs.get('statistics', {})
        }
        
        # CAMPOS ESPECÍFICOS POR TIPO
        # if message_type == 'emergency':
        #     base_message.update({
        #         'context_data': kwargs.get('context_data', {})
        #     })
        # elif message_type == 'summary':
        #     base_message.update({
        #         'readings_count': kwargs.get('readings_count', 0),
        #         'period_start': kwargs.get('period_start'),
        #         'period_end': kwargs.get('period_end')
        #     })
        
        return base_message
    
    def _calculate_statistics(self) -> Dict:
        """Calcula estatísticas dos dados no buffer"""
        stats = {}
        sensor_groups = {}

        for entry in self.normal_data_buffer:
            for reading in entry['readings']:
                sensor_type = reading.get('sensor_type')
                if sensor_type not in sensor_groups:
                    sensor_groups[sensor_type] = []
                # Sensor de queda: salva o bool
                if sensor_type == 'fall_detection':
                    sensor_groups[sensor_type].append(reading.get('fall_detected', False))
                else:
                    value = reading.get('value')
                    if value is not None:
                        sensor_groups[sensor_type].append(value)

        for sensor_type, values in sensor_groups.items():
            unit = SENSOR_UNITS.get(sensor_type, 'unknown')
            if sensor_type == 'fall_detection':
                # Se qualquer valor for True, houve queda
                stats[sensor_type] = {
                    'fall_detected': any(values),
                }
            elif values:
                stats[sensor_type] = {
                    'avg': round(sum(values) / len(values), 2),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values),
                    'last_value': values[-1],
                    'unit': unit
                }

        return stats
    
    def _assess_overall_health(self, stats: Dict) -> tuple[str, List[Dict]]:
        """
        Avalia estado geral de saúde baseado nas estatísticas
        
        Returns:
            tuple: (status_geral, lista_de_alertas)
        """
        concerns = []
        criticals = []
        alerts = []
        
        # Analisa cada sensor
        if 'heart_rate' in stats:
            avg_hr = stats['heart_rate']['avg']
            if avg_hr > 100:
                if avg_hr > 120:
                    criticals.append('batimento_critico_alto')
                    alerts.append({
                    'type': 'batimento_critico_alto',
                    'sensor': 'heart_rate',
                    'value': avg_hr,
                    'severity': 'critical',
                    'message': f'Batimento cardíaco muito alto: {avg_hr} bpm'
                    })
                else:
                    concerns.append('batimento_elevado')
                    alerts.append({
                    'type': 'batimento_elevado',
                    'sensor': 'heart_rate',
                    'value': avg_hr,
                    'severity': 'concern',
                    'message': f'Batimento cardíaco elevado: {avg_hr} bpm'
                    })
            elif avg_hr < 65:
                if avg_hr < 40:
                    criticals.append('batimento_critico_baixo')
                    alerts.append({
                    'type': 'batimento_critico_baixo',
                    'sensor': 'heart_rate',
                    'value': avg_hr,
                    'severity': 'critical',
                    'message': f'Batimento cardíaco muito baixo: {avg_hr} bpm'
                    })
                else: 
                    concerns.append('batimento_baixo')
                    alerts.append({
                    'type': 'batimento_baixo',
                    'sensor': 'heart_rate',
                    'value': avg_hr,
                    'severity': 'concern',
                    'message': f'Batimento cardíaco baixo: {avg_hr} bpm'
                    })
        
        if 'stress_level' in stats:
            avg_stress = stats['stress_level']['avg']
            if avg_stress > 80:
                criticals.append('stress_critico')
                alerts.append({
                    'type': 'stress_critico',
                    'sensor': 'stress_level',
                    'value': avg_stress,
                    'severity': 'critical',
                    'message': f'Nível de stress crítico: {avg_stress}%'
                })
            elif avg_stress > 60:
                concerns.append('stress_alto')
                alerts.append({
                    'type': 'stress_alto',
                    'sensor': 'stress_level',
                    'value': avg_stress,
                    'severity': 'concern',
                    'message': f'Nível de stress elevado: {avg_stress}%'
                })
        
        if 'temperature' in stats:
            avg_temp = stats['temperature']['avg']
            if avg_temp > 37.0:
                if avg_temp >= 39.0:
                    criticals.append('temperatura_critica_alta')
                    alerts.append({
                    'type': 'temperatura_critica_alta',
                    'sensor': 'temperature',
                    'value': avg_temp,
                    'severity': 'critical',
                    'message': f'Temperatura corporal muito alta: {avg_temp}°C'
                    })
                else:
                    concerns.append('temperatura_elevada')
                    alerts.append({
                    'type': 'temperatura_elevada',
                    'sensor': 'temperature',
                    'value': avg_temp,
                    'severity': 'concern',
                    'message': f'Temperatura corporal elevada: {avg_temp}°C'
                    })
            elif avg_temp < 36.0:
                if avg_temp < 35.0:
                    criticals.append('temperatura_critica_baixa')
                    alerts.append({
                    'type': 'temperatura_critica_baixa',
                    'sensor': 'temperature',
                    'value': avg_temp,
                    'severity': 'critical',
                    'message': f'Temperatura corporal muito baixa: {avg_temp}°C'
                    })
                else:
                    concerns.append('temperatura_baixa')
                    alerts.append({
                    'type': 'temperatura_baixa',
                    'sensor': 'temperature',
                    'value': avg_temp,
                    'severity': 'concern',
                    'message': f'Temperatura corporal baixa: {avg_temp}°C'
                    })
        
        if 'oxygen_saturation' in stats:
            avg_oxygen = stats['oxygen_saturation']['avg']
            if avg_oxygen < 96:
                if avg_oxygen < 90:
                    criticals.append('oxigenacao_critica_baixa')
                    alerts.append({
                    'type': 'oxigenacao_critica_baixa',
                    'sensor': 'oxygen_saturation',
                    'value': avg_oxygen,
                    'severity': 'critical',
                    'message': f'Oxigenação sanguínea muito baixa: {avg_oxygen}%'
                    })
                else:
                    concerns.append('oxigenacao_baixa')
                    alerts.append({
                    'type': 'oxigenacao_baixa',
                    'sensor': 'oxygen_saturation',
                    'value': avg_oxygen,
                    'severity': 'concern',
                    'message': f'Oxigenação sanguínea baixa: {avg_oxygen}%'
                    })

        if 'fall_detection' in stats and stats['fall_detection'].get('fall_detected', False):
            criticals.append('queda_detectada')
            alerts.append({
            'type': 'queda_detectada',
            'sensor': 'fall_detection',
            'severity': 'critical',
            'message': 'Queda detectada!'
            })

        
        # Determina status geral
        if criticals:
            status = 'critical'
        elif concerns:
            status = 'alert'
        else:
            status = 'stable'
        
        return status, alerts

    
    def _get_recent_context(self) -> Dict:
        """Retorna contexto dos dados recentes para emergências"""
        if not self.normal_data_buffer:
            return {'message': 'Sem dados recentes disponíveis'}
        
        # Pega últimos 3 entries do buffer
        recent_entries = self.normal_data_buffer[-3:] if len(self.normal_data_buffer) >= 3 else self.normal_data_buffer
        
        return {
            'recent_readings_count': len(recent_entries),
            'buffer_size': len(self.normal_data_buffer),
            'trend': 'Dados estavam normais antes da emergência'
        }
    
    
    def get_status(self) -> Dict:
        """Retorna status atual do processador"""
        return {
            'patient_id': self.patient_id,
            'buffer_size': len(self.normal_data_buffer),
            'last_summary': self.last_summary_sent,
            'next_summary_in': max(0, self.summary_interval - (time.time() - self.last_summary_sent)),
            'last_emergency': self.last_emergency_time
        }

# Função para testes
if __name__ == "__main__":
    # Teste do EdgeProcessor
    processor = EdgeProcessor("PAT001")
    
    # Simula dados normais
    normal_readings = [
        {'sensor_type': 'heart_rate', 'value': 75, 'status': 'normal'},
        {'sensor_type': 'stress_level', 'value': 25, 'level': 'low'},
        {'sensor_type': 'temperature', 'value': 36.5, 'status': 'normal'}
    ]
    
    print("🧪 Teste 1: Dados normais")
    result = processor.process_sensor_readings(normal_readings)
    print(f"Resultado: {result}")
    
    # Simula emergência
    emergency_readings = [
        {'sensor_type': 'fall_detection', 'fall_detected': True, 'status': 'ALERT'},
        {'sensor_type': 'heart_rate', 'value': 115, 'status': 'high'},
        {'sensor_type': 'stress_level', 'value': 90, 'level': 'critical'}
    ]
    
    print("\n🚨 Teste 2: Emergência (queda)")
    result = processor.process_sensor_readings(emergency_readings)
    print(f"Resultado: {result}")
    
    print(f"\n📊 Status do processador:")
    print(processor.get_status())