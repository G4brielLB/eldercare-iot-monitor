# eldercare-iot-monitor

Sistema de Monitoramento IoT para Idosos utilizando FastAPI, MQTT e SQLite.

## Descrição

Este projeto simula um sistema de monitoramento de saúde para idosos, utilizando pulseiras inteligentes que enviam dados via MQTT para um backend FastAPI. Os dados são armazenados em um banco SQLite e podem ser consultados via API.

## Principais Funcionalidades

- **Simulação de Pulseira IoT:** Envio de dados de sensores (batimentos, oxigênio, temperatura, etc) via MQTT.
- **Subscriber MQTT:** Recebe mensagens das pulseiras e armazena no banco de dados.
- **API FastAPI:** Consulta de pacientes, mensagens, status e controle do sistema.
- **Banco de Dados SQLite:** Armazenamento local dos dados de saúde.
- **Docker:** Ambiente facilmente replicável e isolado.

## Estrutura do Projeto

```
eldercare-iot-monitor/
│
├── app/
│   ├── server.py                # API FastAPI
│   ├── pulseira.py              # Simulador de pulseira IoT
│   ├── subscriber/
│   │   └── subscriber.py        # Subscriber MQTT
│   ├── database/
│   │   ├── crud.py              # Operações no banco
│   │   ├── models.py            # Modelos ORM
│   │   └── schemas.py           # Schemas Pydantic
│   └── health.db                # Banco de dados SQLite
│
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Como Executar

### 1. Clonar o repositório

```sh
git clone <url-do-repo>
cd eldercare-iot-monitor
```

### 2. Subir com Docker Compose

```sh
docker-compose up --build
```

- O Mosquitto (broker MQTT) ficará disponível na porta 1883.
- A API FastAPI ficará disponível em `http://localhost:8000`.

### 3. Endpoints Principais

- `POST /start_subscriber` — Inicia o subscriber MQTT.
- `POST /start_pulseira` — Inicia simulação de pulseira (parâmetros: id, duração, sensores).
- `GET /paciente/{patient_id}` — Consulta dados de um paciente.
- `GET /messages/{patient_id}` — Lista todas as mensagens de um paciente.
- `GET /latest_message_per_patient` — Última mensagem de cada paciente.
- `GET /status` — Lista todas as mensagens do sistema.

### 4. Simular Pulseira via API

Exemplo de chamada via `curl`:

```sh
curl -X POST "http://localhost:8000/start_pulseira" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "PAT001", "duration": 120, "oxygen_status": "stable"}'
```

### 5. Consultar Mensagens

```sh
curl http://localhost:8000/messages/PAT001
```

## Observações

- O sistema utiliza SQLite, que não é recomendado para produção com muitos acessos concorrentes.
- Para produção, recomenda-se usar PostgreSQL ou MySQL.
- O código é modular e pode ser expandido para novos sensores e integrações.

## Licença

MIT

---
Desenvolvido para fins acadêmicos.
