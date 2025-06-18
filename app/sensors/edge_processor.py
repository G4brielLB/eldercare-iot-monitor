import time
from typing import List, Dict, Optional
from config.settings import ALERT_THRESHOLDS

class EdgeProcessor:
    """
    Processador de borda - Inteligência da pulseira IoT
    Recebe dados de múltiplos sensores e decide o que enviar
    """
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.normal_data_buffer = []
        self.last_summary_sent = time.time()
        self.summary_interval = 60  # 5 minutos entre resumos
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
        
        # Verifica alertas críticos primeiro
        emergency_result = self._check_emergency_conditions(sensor_readings)
        if emergency_result:
            return emergency_result
        
        # Adiciona ao buffer de dados normais
        self._add_to_buffer(sensor_readings)
        
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
                'severity': 'CRITICAL',
                'message': 'Queda detectada!'
            })
        
        # 2. Oxigenação crítica
        oxygen_data = sensor_data.get('oxygen_saturation')
        if oxygen_data and oxygen_data.get('value', 100) < 90:
            critical_alerts.append({
                'type': 'LOW_OXYGEN',
                'severity': 'CRITICAL',
                'value': oxygen_data.get('value'),
                'message': f"Oxigenação crítica: {oxygen_data.get('value')}%"
            })
        
        # 3. Temperatura extrema
        temp_data = sensor_data.get('temperature')
        if temp_data:
            temp_value = temp_data.get('value', 36.5)
            if temp_value < 35.0 or temp_value > 39.5:
                critical_alerts.append({
                    'type': 'EXTREME_TEMPERATURE',
                    'severity': 'HIGH',
                    'value': temp_value,
                    'message': f"Temperatura extrema: {temp_value}°C"
                })
        
        # 4. Combinação de alertas (correlação)
        heart_data = sensor_data.get('heart_rate')
        stress_data = sensor_data.get('stress_level')
        
        if heart_data and stress_data:
            heart_rate = heart_data.get('value', 70)
            stress_level = stress_data.get('value', 20)
            
            # Condição: batimento alto + stress muito alto = possível crise
            if heart_rate > 110 and stress_level > 85:
                critical_alerts.append({
                    'type': 'CARDIAC_STRESS',
                    'severity': 'HIGH',
                    'message': f"Batimento elevado ({heart_rate} bpm) + stress alto ({stress_level}%)"
                })
        
        # Se há alertas críticos, cria emergência
        if critical_alerts:
            self.last_emergency_time = current_time
            
            return {
                'action': 'emergency',
                'priority': 'CRITICAL',
                'channel': f'eldercare/emergency/{self.patient_id}',
                'data': {
                    'patient_id': self.patient_id,
                    'alert_type': 'EMERGENCY',
                    'timestamp': current_time,
                    'alerts': critical_alerts,
                    'all_sensor_data': readings,
                    'requires_immediate_attention': True,
                    'context': self._get_recent_context()
                }
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
        
        summary_data = {
            'patient_id': self.patient_id,
            'summary_type': 'normal_monitoring',
            'period_start': self.last_summary_sent,
            'period_end': current_time,
            'readings_count': len(self.normal_data_buffer),
            'statistics': stats,
            'health_status': self._assess_overall_health(stats)
        }
        
        # Limpa buffer e atualiza timestamp
        self.normal_data_buffer.clear()
        self.last_summary_sent = current_time
        
        return {
            'action': 'summary',
            'priority': 'NORMAL',
            'channel': f'eldercare/summary/{self.patient_id}',
            'data': summary_data
        }
    
    def _calculate_statistics(self) -> Dict:
        """Calcula estatísticas dos dados no buffer"""
        stats = {}
        
        # Agrupa dados por tipo de sensor
        sensor_groups = {}
        for entry in self.normal_data_buffer:
            for reading in entry['readings']:
                sensor_type = reading.get('sensor_type')
                if sensor_type not in sensor_groups:
                    sensor_groups[sensor_type] = []
                
                # Adiciona valor se existir
                value = reading.get('value')
                if value is not None:
                    sensor_groups[sensor_type].append(value)
        
        # Calcula estatísticas para cada sensor
        for sensor_type, values in sensor_groups.items():
            if values:
                stats[sensor_type] = {
                    'avg': round(sum(values) / len(values), 2),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values),
                    'last_value': values[-1]
                }
        
        return stats
    
    def _assess_overall_health(self, stats: Dict) -> str:
        """Avalia estado geral de saúde baseado nas estatísticas"""
        concerns = []
        
        # Analisa cada sensor
        if 'heart_rate' in stats:
            avg_hr = stats['heart_rate']['avg']
            if avg_hr > 90:
                concerns.append('batimento_elevado')
            elif avg_hr < 65:
                concerns.append('batimento_baixo')
        
        if 'stress_level' in stats:
            avg_stress = stats['stress_level']['avg']
            if avg_stress > 60:
                concerns.append('stress_alto')
        
        if 'temperature' in stats:
            avg_temp = stats['temperature']['avg']
            if avg_temp > 37.3:
                concerns.append('temperatura_elevada')
        
        if 'oxygen_saturation' in stats:
            avg_oxygen = stats['oxygen_saturation']['avg']
            if avg_oxygen < 96:
                concerns.append('oxigenacao_baixa')
        
        # Determina status geral
        if not concerns:
            return 'estavel'
        elif len(concerns) == 1:
            return 'atencao'
        else:
            return 'preocupante'
    
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