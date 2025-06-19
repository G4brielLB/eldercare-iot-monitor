# Testes da SmartPulseira

Este diretório contém os testes para o sistema de monitoramento de idosos com pulseira IoT.

## Arquivos

- `sensors/smart_pulseira.py` - Classe principal da pulseira (apenas a classe, sem código de teste)
- `test_smart_pulseira.py` - Arquivo de testes e simulações

## Como Executar os Testes

### 1. Preparação do Ambiente

Certifique-se de que o Docker Compose com Mosquitto está rodando:

```bash
cd /Users/gabriellopesbastos/Documents/Programming/eldercare-iot-monitor
docker-compose up -d mosquitto
```

### 2. Ativar o Ambiente Virtual

```bash
cd /Users/gabriellopesbastos/Documents/Programming/eldercare-iot-monitor
source iotvenv/bin/activate
```

### 3. Executar Testes

#### Modo Interativo (Recomendado)

```bash
cd app
python test_smart_pulseira.py
```

Este comando abrirá um menu interativo com as seguintes opções:
- **1** - Teste rápido (30 segundos)
- **2** - Teste individual padrão (2 minutos)
- **3** - Múltiplas pulseiras (PAT001, PAT002, 3 minutos)
- **4** - Teste de estresse (5 pulseiras, 5 minutos)
- **5** - Teste personalizado
- **0** - Sair

#### Importar e Usar Programaticamente

```python
from test_smart_pulseira import test_single_patient, simulate_multiple_patients

# Teste individual
test_single_patient("PAT001", 120)

# Múltiplas pulseiras
simulate_multiple_patients(["PAT001", "PAT002", "PAT003"], 180)
```

## Tipos de Teste

### 1. Teste Individual
- Testa uma única pulseira
- Valida: sensores → edge processor → MQTT publisher
- Monitoramento de estatísticas em tempo real

### 2. Múltiplas Pulseiras
- Testa várias pulseiras simultaneamente
- Valida concorrência e múltiplos clientes MQTT
- Útil para testar cenários reais

### 3. Teste de Estresse
- Simula muitas pulseiras simultaneamente
- Testa limites do sistema
- Mede performance

### 4. Teste Rápido
- Validação básica em 30 segundos
- Ideal para verificações rápidas
- Usado em desenvolvimento

## Monitoramento Durante os Testes

### Logs do Mosquitto
Para ver as mensagens MQTT em tempo real:

```bash
docker logs -f eldercare-iot-monitor-mosquitto-1
```

### Mensagens Publicadas
Os testes publicam mensagens nos seguintes tópicos:
- `eldercare/{patient_id}/emergency` (QoS 2) - Emergências
- `eldercare/{patient_id}/summary` (QoS 1) - Resumos
- `eldercare/{patient_id}/heartbeat` (QoS 0, retained) - Status da pulseira

### Estatísticas
Cada teste mostra estatísticas finais incluindo:
- Tempo ativo da pulseira
- Número de leituras coletadas
- Emergências detectadas
- Resumos enviados
- Status do buffer do edge processor
- Estatísticas do publisher MQTT

## Estrutura de uma Sessão de Teste

1. **Inicialização**: Criação dos sensores, edge processor e publisher
2. **Conexão MQTT**: Estabelecimento da conexão com o broker
3. **Monitoramento**: Loop principal com coleta, processamento e envio
4. **Heartbeat**: Thread em background para manter conexão ativa
5. **Finalização**: Desconexão limpa e relatório de estatísticas

## Resolução de Problemas

### Erro de Conexão MQTT
- Verifique se o Mosquitto está rodando: `docker ps`
- Reinicie o container: `docker-compose restart mosquitto`

### Erro de Importação
- Execute sempre a partir do diretório `app/`
- Verifique se o ambiente virtual está ativo

### Performance Baixa
- Reduza o número de pulseiras simultâneas
- Aumente os intervalos de leitura
- Monitore uso de CPU e memória

## Próximos Passos

Após validar que os testes estão funcionando:
1. Implementar `subscriber.py` para receber dados do MQTT
2. Criar camada de database (SQLite + SQLAlchemy)
3. Desenvolver API FastAPI
4. Integrar frontend para visualização
