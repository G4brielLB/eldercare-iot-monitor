# ElderCare IoT Monitor

Sistema de monitoramento de saúde para idosos utilizando pulseiras inteligentes IoT com comunicação MQTT, backend FastAPI e interface web em tempo real.

## Sobre o Projeto

O **ElderCare IoT Monitor** é um sistema completo de monitoramento de saúde em tempo real para idosos que simula um ambiente IoT distribuído. O projeto utiliza pulseiras inteligentes virtuais que coletam dados de múltiplos sensores biomédicos e os transmitem via protocolo MQTT para um backend robusto desenvolvido em FastAPI. Os dados são processados, armazenados em SQLite e visualizados através de uma interface web moderna com atualizações em tempo real.

Este projeto foi desenvolvido para a disciplina de **Sistemas Distribuídos** (UFPI, 2025.1), aplicando conceitos como:
- Arquitetura Publisher-Subscriber
- Computação na borda (Edge Computing)
- Comunicação assíncrona baseada em eventos (MQTT)
- Contêineres Docker
- Interfaces RESTful e visualização em tempo real

## Tecnologias Utilizadas

- **Backend**: FastAPI, Python 3.11+
- **Banco de Dados**: SQLite com SQLAlchemy ORM
- **Comunicação IoT**: MQTT (Eclipse Mosquitto)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Containerização**: Docker & Docker Compose
- **Validação**: Pydantic Schemas

## Principais Funcionalidades

### Sistema IoT Completo
- **Pulseiras Inteligentes Simuladas**: Coleta de dados de sensores biomédicos
- **Processamento Edge**: Análise local com detecção automática de emergências
- **Comunicação MQTT**: Protocolo de comunicação robusto com diferentes níveis de QoS e tópicos por tipo de mensagem: `heartbeat`, `summary`, `emergency`
- **Detecção de Anomalias**: Identificação automática de situações críticas

### Sensores Monitorados
- **Batimentos Cardíacos (BPM)**: 25–200 bpm, com detecção de anomalias cardíacas
- **Oxigenação (SpO₂)**: 70–100%, com alertas automáticos para hipóxia
- **Temperatura Corporal**: 34–40 °C, com detecção de febre e hipotermia
- **Nível de Stress**: 0–100%, análise contínua do estado emocional
- **Detecção de Quedas**: Indicação binária (sim/não)

### Persistência
- **Armazenamento de dados históricos no SQLite**
- **Relacionamento 1:N entre pacientes e mensagens**

### Sistema de Alertas
- **Emergências Críticas**: Quedas, parada cardíaca, hipóxia severa
- **Alertas Médicos**: Valores fora dos parâmetros normais
- **Notificações Preventivas**: Tendências preocupantes nos dados

### Interface Web Moderna
- **Dashboard em Tempo Real**: Visualização de todos os pacientes
- **Cards Dinâmicos**: Status visual com códigos de cores
- **Filtros Inteligentes**: Por status (crítico, alerta, estável)
- **Modal Detalhado**: Informações completas do paciente
- **Auto-atualização**: Dados atualizados a cada 10 segundos
- **Design Responsivo**: Funciona em desktop e mobile

## Estrutura do Projeto

```
eldercare-iot-monitor/
│
├── app/                              # Aplicação principal
│   ├── server.py                     # API FastAPI principal
│   ├── pulseira.py                   # Simulador pulseira IoT
│   ├── health.db                     # Banco SQLite
│   │
│   ├── config/                       # Configurações
│   │   ├── settings.py               # Configurações do sistema
│   │   └── mosquitto.conf            # Config broker MQTT
│   │
│   ├── database/                     # Camada de dados
│   │   ├── database.py               # Configuração SQLAlchemy
│   │   ├── models.py                 # Modelos ORM
│   │   ├── schemas.py                # Schemas Pydantic
│   │   ├── crud.py                   # Operações CRUD
│   │   └── setup_database.py         # Inicialização do banco
│   │
│   ├── sensors/                      # Sistema de sensores
│   │   ├── base_sensor.py            # Classe base dos sensores
│   │   ├── heart_rate_sensor.py      # Sensor de batimentos
│   │   ├── oxygen_sensor.py          # Sensor de oxigenação
│   │   ├── temperature_sensor.py     # Sensor de temperatura
│   │   ├── stress_sensor.py          # Sensor de stress
│   │   ├── fall_sensor.py            # Sensor de quedas
│   │   ├── edge_processor.py         # Processamento edge
│   │   ├── smart_pulseira.py         # Pulseira inteligente
│   │   └── pulseira_publisher.py     # Publisher MQTT
│   │
│   └── subscriber/                   # Sistema MQTT
│       ├── subscriber.py             # Subscriber MQTT principal
│       └── sqlite_saver.py           # Salvamento no SQLite
│
├── front-end/                        # Interface Web
│   ├── index.html                    # Página principal
│   ├── script.js                     # Lógica JavaScript
│   └── styles.css                    # Estilos CSS
│
├── Dockerfile                        # Container da aplicação
├── docker-compose.yml                # Orquestração completa
├── requirements.txt                  # Dependências Python
└── README.md                         # Documentação
```

## API Endpoints
- `/start_subscriber`: inicia o subscriber MQTT
- `/status`: mensagens recentes do sistema
- `/paciente/{id}`: dados de um paciente
- `/messages/{id}`: histórico completo
- `/latest_message_per_patient`: últimas leituras por paciente
- `/patients_status`: status online/offline

### Parâmetros da Pulseira
```json
{
  "patient_id": "PAT001",
  "duration": 120,
  "heart_rate_status": "normal|high|low|critical",
  "oxygen_status": "normal|low|critical", 
  "temperature_status": "normal|fever|hypothermia",
  "stress_status": "low|normal|high|critical",
  "fall_probability": 0.1
}
```

## Interface Web

### Dashboard Principal
- **Cards de Status**: Visualização rápida de críticos, alertas e estáveis
- **Grid de Pacientes**: Lista todos os pacientes com dados em tempo real
- **Filtros**: Permite filtrar por status (todos, críticos, alertas, estáveis)
- **Auto-refresh**: Atualização automática a cada 10 segundos

### Detalhes do Paciente
- **Informações Básicas**: Nome, sexo, idade, ID
- **Métricas Atuais**: Frequência cardíaca, temperatura, oxigenação, stress
- **Status de Queda**: Indicação visual destacada
- **Histórico**: Últimas 10 mensagens com timestamps

### Recursos Visuais
- **Códigos de Cores**: Verde (estável), amarelo (alerta), vermelho (crítico)
- **Ícones Intuitivos**: FontAwesome para melhor UX
- **Design Responsivo**: Funciona em desktop, tablet e mobile
- **Loading States**: Feedback visual durante requisições

## Arquitetura do Sistema

### Fluxo de Dados
1. **Pulseiras IoT** → Coletam dados dos sensores
2. **Edge Processor** → Processa e analisa dados localmente
3. **MQTT Publisher** → Envia dados para broker
4. **MQTT Subscriber** → Recebe e processa mensagens
5. **SQLite Database** → Armazena dados históricos
6. **FastAPI Backend** → Expõe dados via API RESTful
7. **Frontend Web** → Visualiza dados em tempo real

### Componentes Principais

#### Sensores Inteligentes
- **BaseSensor**: Classe abstrata para todos os sensores
- **HeartRateSensor**: Monitora batimentos cardíacos (60-180 BPM)
- **OxygenSensor**: Mede saturação de oxigênio (85-100%)
- **TemperatureSensor**: Controla temperatura corporal (35-42°C)  
- **StressSensor**: Avalia nível de stress (1-10)
- **FallSensor**: Detecta quedas via acelerômetro

#### Processamento Edge
- **Análise em Tempo Real**: Detecção imediata de anomalias
- **Agregação de Dados**: Combina múltiplos sensores
- **Classificação de Alertas**: Normal, alerta, crítico, emergência
- **Buffering Inteligente**: Otimiza transmissão de dados

#### Comunicação MQTT
- **Publisher**: Envia dados com QoS configurável
- **Subscriber**: Recebe e processa mensagens
- **Tópicos Estruturados**: `/health/{patient_id}/{message_type}`
- **Persistência**: Mensagens importantes são persistidas

#### Banco de Dados
- **Modelos SQLAlchemy**: Patient, HealthMessage
- **Schemas Pydantic**: Validação de dados de entrada/saída
- **CRUD Operations**: Create, Read, Update, Delete
- **Relacionamentos**: FK entre pacientes e mensagens

## Configurações

### Variáveis de Ambiente
```bash
# Database
DATABASE_URL=sqlite:///./health.db

# MQTT  
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_KEEPALIVE=60

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Frontend
FRONTEND_URL=http://localhost:8080
API_BASE_URL=http://localhost:8000
```

### Configuração MQTT (mosquitto.conf)
```
port 1883
allow_anonymous true
persistence true  
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
```

## Considerações de Segurança
- **CORS**: Configurado para permitir comunicação frontend-backend
- **Validação**: Schemas Pydantic em todos os endpoints
- **Error Handling**: Tratamento robusto de exceções
- **Logging**: Logs detalhados para debugging
- **Multiprocessing**: Isolamento do subscriber MQTT

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Projeto Acadêmico

**Desenvolvido para fins acadêmicos**

- **Curso**: Ciência da Computação - 5º Período
- **Disciplina**: Sistemas Distribuídos
- **Instituição**: Universidade Federal do Piauí (UFPI)
- **Semestre**: 2025.1
- **Professor**: José Rodrigues Torres Neto

### Equipe de Desenvolvimento

- **Antônio Enzo Ferreira Do Nascimento**
- **Gabriel Lopes Bastos**
- **José Victor Vieira de Oliveira**

---

## 📽️ Demonstração

- [📺 Vídeo no YouTube](https://youtu.be/coO7n6pJm1M)
- [🔗 Repositório no GitHub](https://github.com/G4brielLB/eldercare-iot-monitor)

---