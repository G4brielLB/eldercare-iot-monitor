# ElderCare Subscriber

Sistema de monitoramento que recebe dados das pulseiras IoT via MQTT e processa informações de saúde dos idosos.

## 📋 Funcionalidades

- **Recebe mensagens MQTT** dos 3 tipos: `emergency`, `summary`, `heartbeat`
- **Salva dados em JSON** (temporário, preparando para SQLite)
- **Calcula estados dos pacientes**: SAUDÁVEL, ALERTA, CRÍTICO
- **Monitora conectividade** das pulseiras em tempo real

## 🎯 Estados dos Pacientes

### CRÍTICO 🚨
- Emergência detectada nas **últimas 1 hora**
- Requer atenção imediata

### ALERTA ⚠️
- Emergência nas **últimas 24 horas** OU
- Último resumo = `"preocupante"`

### SAUDÁVEL ✅
- Último resumo = `"estavel"` ou `"atencao"` E
- Sem emergências recentes

## 📁 Estrutura de Dados

### Arquivos Gerados

```
data/
├── messages.json       # Todas as mensagens recebidas
├── patients_status.json # Estado atual dos pacientes  
└── heartbeats.json     # Último heartbeat de cada pulseira
```

### Estrutura das Mensagens

```json
{
  "received_at": "2025-06-18T10:30:00",
  "topic": "eldercare/emergency/PAT001",
  "message_type": "emergency",
  "patient_id": "PAT001",
  "qos": 2,
  "payload": {
    "alerts": [
      {
        "type": "FALL_DETECTED",
        "severity": "CRITICAL",
        "message": "Queda detectada!"
      }
    ]
  }
}
```

## 🚀 Como Usar

### 1. Preparação

Certifique-se de que o Mosquitto está rodando:
```bash
docker-compose up -d mosquitto
```

### 2. Executar Subscriber

```bash
# Modo direto
python subscriber/subscriber.py

# Ou com testes
python test_subscriber.py
```

### 3. Menu de Testes

O arquivo `test_subscriber.py` oferece:
- **1** - Teste básico (1 pulseira, 30s)
- **2** - Múltiplas pulseiras (2 pulseiras, 60s)  
- **3** - Verificar arquivos de dados
- **4** - Status dos pacientes
- **5** - Subscriber contínuo

## 📡 Tópicos MQTT Monitorados

| Tópico | QoS | Descrição |
|--------|-----|-----------|
| `eldercare/emergency/+` | 2 | Emergências críticas |
| `eldercare/summary/+` | 1 | Resumos periódicos |
| `eldercare/heartbeat/+` | 0 | Status das pulseiras |

## 🔧 Configuração

O subscriber usa as configurações em `config/settings.py`:
- `MQTT_BROKER` - IP do broker (padrão: localhost)
- `MQTT_PORT` - Porta MQTT (padrão: 1883)

## 📊 Exemplo de Uso Completo

### Terminal 1: Subscriber
```bash
cd app
python subscriber/subscriber.py
```

### Terminal 2: Pulseiras de Teste
```bash
cd app  
python test_smart_pulseira.py
# Escolha: 2 - Teste individual padrão (2 minutos)
```

### Terminal 3: Monitorar MQTT
```bash
docker exec -it eldercare-mosquitto mosquitto_sub -t "eldercare/#" -v
```

## 📈 Estatísticas

O subscriber exibe estatísticas em tempo real:
- Mensagens recebidas por tipo
- Pacientes ativos
- Erros de processamento
- Tempo de atividade

## 🔄 Fluxo de Processamento

```
📱 Pulseira → 📡 MQTT → 🖥️ Subscriber → 💾 JSON → 📊 Estado
```

1. **Pulseira** envia dados via MQTT
2. **Subscriber** recebe e processa
3. **Dados** salvos em arquivos JSON
4. **Estado** do paciente calculado automaticamente

## 🛠️ Próximos Passos

- [ ] Migrar JSON → SQLite + SQLAlchemy
- [ ] Criar API FastAPI para consultas
- [ ] Interface web para visualização
- [ ] Alertas em tempo real
- [ ] Dashboard de monitoramento

## ⚠️ Resolução de Problemas

### Erro de Conexão MQTT
```bash
# Verifique se Mosquitto está rodando
docker ps | grep mosquitto

# Reinicie se necessário
docker-compose restart mosquitto
```

### Erro de Importação
```bash
# Execute sempre do diretório app/
cd app
python subscriber/subscriber.py
```

### Arquivos não Criados
- Verifique permissões da pasta `data/`
- Certifique-se de que há mensagens sendo enviadas

---

**Status**: ✅ Implementado e testado  
**Próximo**: Implementação da camada de banco de dados SQLite
