# ElderCare IoT Monitor - Front-end

Interface web moderna para monitoramento de pacientes idosos através de dispositivos IoT.

## Funcionalidades

- **Dashboard em Tempo Real**: Visualização do status de todos os pacientes
- **Atualização Automática**: Dados atualizados a cada 10 segundos
- **Sistema de Status**: 
  - 🔴 **Crítico**: Pacientes com emergências recentes
  - 🟡 **Alerta**: Pacientes com alertas nos sensores
  - 🟢 **Estável**: Pacientes com sinais vitais normais
- **Filtros**: Filtragem por status dos pacientes
- **Detalhes do Paciente**: Modal com histórico de mensagens e métricas detalhadas
- **Interface Responsiva**: Compatível com desktop, tablet e mobile

## Como Usar

### 1. Iniciar o Backend

Primeiro, certifique-se de que o servidor FastAPI está rodando:

```bash
cd app
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### 2. Abrir o Front-end

Abra o arquivo `index.html` em um navegador web ou use um servidor HTTP local:

```bash
# Opção 1: Servidor Python simples
cd front-end
python -m http.server 3000

# Opção 2: Servidor Node.js (se tiver npx instalado)
cd front-end
npx serve .

# Opção 3: Abrir diretamente no navegador
# Apenas abra o arquivo index.html no seu navegador
```

### 3. Iniciar o Monitoramento

1. Clique no botão **"Iniciar Monitoramento"** para ativar o subscriber MQTT
2. Os dados começarão a aparecer automaticamente conforme as mensagens chegarem

## Estrutura dos Arquivos

```
front-end/
├── index.html          # Página principal
├── styles.css          # Estilos CSS
├── script.js           # Lógica JavaScript
└── README.md           # Este arquivo
```

## Endpoints Utilizados

O front-end consome os seguintes endpoints da API:

- `POST /start_subscriber` - Inicia o monitoramento MQTT
- `GET /latest_message_per_patient` - Obtém a última mensagem de cada paciente
- `GET /paciente/{patient_id}` - Detalhes de um paciente específico
- `GET /messages/{patient_id}` - Histórico de mensagens de um paciente

## Estados dos Pacientes

### Crítico 🔴
- Pacientes que enviaram mensagens de emergência recentemente
- Indicado por borda vermelha e status vermelho
- Prioridade máxima de atendimento

### Alerta 🟡  
- Pacientes com alertas detectados pelos sensores
- Indicado por borda amarela e status amarelo
- Requer atenção médica

### Estável 🟢
- Pacientes com sinais vitais normais
- Indicado por borda verde e status verde
- Monitoramento de rotina

## Métricas Monitoradas

- **Frequência Cardíaca (BPM)**: Batimentos por minuto
- **Temperatura (°C)**: Temperatura corporal
- **Saturação de Oxigênio (SpO2)**: Percentual de oxigênio no sangue
- **Nível de Stress**: Indicador de stress do paciente

## Configurações

### Intervalo de Atualização
Por padrão, os dados são atualizados a cada 10 segundos. Para alterar, modifique a constante `UPDATE_INTERVAL` no arquivo `script.js`:

```javascript
const UPDATE_INTERVAL = 10000; // 10 segundos em millisegundos
```

### URL da API
Se o backend estiver rodando em uma porta diferente, altere a constante `API_BASE_URL` no arquivo `script.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000'; // Altere conforme necessário
```

## Recursos Visuais

- **Design Moderno**: Interface limpa e profissional
- **Ícones FontAwesome**: Ícones intuitivos para melhor UX
- **Animações Suaves**: Transições e animações para melhor experiência
- **Modo Responsivo**: Adaptação automática para diferentes tamanhos de tela
- **Feedback Visual**: Notificações e indicadores de status

## Troubleshooting

### Erro de Conexão
- Verifique se o backend está rodando na porta correta
- Certifique-se de que o CORS está configurado adequadamente
- Verifique a configuração de firewall

### Dados Não Aparecem
- Clique em "Iniciar Monitoramento" para ativar o subscriber
- Verifique se há dispositivos IoT enviando dados
- Use o botão "Atualizar" para forçar uma nova requisição

### Performance
- O front-end pausa as atualizações quando a aba não está ativa
- Use o filtro para reduzir a quantidade de dados exibidos
- O modal de detalhes mostra apenas as 10 mensagens mais recentes

## Compatibilidade

- **Navegadores**: Chrome, Firefox, Safari, Edge (versões modernas)
- **Dispositivos**: Desktop, Tablet, Mobile
- **Resolução Mínima**: 320px de largura

## Segurança

Para uso em produção:

1. Configure CORS específico no backend
2. Use HTTPS para todas as comunicações
3. Implemente autenticação e autorização
4. Valide todos os dados de entrada
5. Configure CSP (Content Security Policy)
