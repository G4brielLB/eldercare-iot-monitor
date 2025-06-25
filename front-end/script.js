// Configuração da API
const API_BASE_URL = 'http://localhost:8000';
const UPDATE_INTERVAL = 10000; // 10 segundos

// Estado da aplicação
let currentFilter = 'all';
let updateInterval = null;
let isConnected = false;
let patients = [];

// Elementos DOM
const elements = {
    connectionStatus: document.getElementById('connectionStatus'),
    lastUpdate: document.getElementById('lastUpdate'),
    startSubscriber: document.getElementById('startSubscriber'),
    refreshData: document.getElementById('refreshData'),
    criticalCount: document.getElementById('criticalCount'),
    alertCount: document.getElementById('alertCount'),
    stableCount: document.getElementById('stableCount'),
    totalCount: document.getElementById('totalCount'),
    patientsGrid: document.getElementById('patientsGrid'),
    patientModal: document.getElementById('patientModal'),
    modalClose: document.getElementById('modalClose'),
    modalBody: document.getElementById('modalBody'),
    modalPatientName: document.getElementById('modalPatientName'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    filterButtons: document.querySelectorAll('.filter-btn')
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    startAutoUpdate();
    loadPatients();
});

// Event Listeners
function initializeEventListeners() {
    elements.startSubscriber.addEventListener('click', startSubscriber);
    elements.refreshData.addEventListener('click', () => loadPatients(true));
    elements.modalClose.addEventListener('click', closeModal);
    elements.patientModal.addEventListener('click', (e) => {
        if (e.target === elements.patientModal) closeModal();
    });
    
    elements.filterButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            setFilter(e.target.dataset.filter);
        });
    });
    
    // Fechar modal com ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

// Funções da API
async function makeRequest(endpoint, options = {}) {
    try {
        showLoading();
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        updateConnectionStatus(true);
        return await response.json();
    } catch (error) {
        console.error(`Erro na requisição ${endpoint}:`, error);
        updateConnectionStatus(false);
        showError(`Erro ao conectar com o servidor: ${error.message}`);
        throw error;
    } finally {
        hideLoading();
    }
}

async function startSubscriber() {
    try {
        elements.startSubscriber.disabled = true;
        elements.startSubscriber.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Iniciando...';
        
        const result = await makeRequest('/start_subscriber', { method: 'POST' });
        
        showSuccess(result.status);
        
        // Aguardar um pouco e recarregar dados
        setTimeout(() => {
            loadPatients();
        }, 2000);
    } catch (error) {
        console.error('Erro ao iniciar subscriber:', error);
    } finally {
        elements.startSubscriber.disabled = false;
        elements.startSubscriber.innerHTML = '<i class="fas fa-play"></i> Iniciar Monitoramento';
    }
}

async function loadPatients(showFeedback = false) {
    try {
        if (showFeedback) {
            elements.refreshData.disabled = true;
            elements.refreshData.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
        }
        
        const data = await makeRequest('/latest_message_per_patient');
        patients = await processPatientData(data);
        
        updateStats();
        renderPatients();
        updateLastUpdateTime();
        
        if (showFeedback) {
            showSuccess('Dados atualizados com sucesso!');
        }
    } catch (error) {
        console.error('Erro ao carregar pacientes:', error);
        if (patients.length === 0) {
            showEmptyState();
        }
    } finally {
        if (showFeedback) {
            elements.refreshData.disabled = false;
            elements.refreshData.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar';
        }
    }
}

async function loadPatientDetails(patientId) {
    try {
        const [patient, messages] = await Promise.all([
            makeRequest(`/paciente/${patientId}`),
            makeRequest(`/messages/${patientId}`)
        ]);
        
        return { patient, messages };
    } catch (error) {
        console.error('Erro ao carregar detalhes do paciente:', error);
        throw error;
    }
}

// Adicione uma função auxiliar para buscar dados do paciente
async function fetchPatientInfo(patientId) {
    try {
        return await makeRequest(`/paciente/${patientId}`);
    } catch {
        return { nome: `Paciente ${patientId}`, sexo: 'M' }; // fallback
    }
}

// Modifique processPatientData para buscar nome/sexo
async function processPatientData(data) {
    const patients = [];
    for (const item of data) {
        const info = await fetchPatientInfo(item.patient_id);
        const prefix = info.sex === 'F' ? 'Sra.' : 'Sr.';
        patients.push({
            id: item.patient_id,
            name: `${prefix} ${info.name}`, // Para o card
            rawName: info.name,             // Nome puro para detalhes/modal
            sex: info.sex,
            lastMessage: item,
            timestamp: item.timestamp,
            status: determinePatientStatus(item),
            metrics: extractMetrics(item.data),
            info: info // salva info completa para o modal
        });
    }
    return patients;
}

function determinePatientStatus(message) {
    if (message.message_type === 'emergency') {
        return 'critical';
    }
    
    const data = message.data || {};
    const alerts = data.alerts || [];
    const health_status = data.health_status || 'stable';
    
    return health_status;
}

function extractMetrics(data) {
    if (!data) return {};

    // Para mensagens tipo summary, os dados podem estar em "statistics"
    let stats = data.statistics || {};
    // Para emergency, pode estar como lista ou objeto
    if (Array.isArray(stats)) {
        // Pega o último valor de cada tipo
        const metrics = {};
        stats.forEach(item => {
            if (item.sensor_type === 'heart_rate') metrics.heartRate = item.value;
            if (item.sensor_type === 'temperature') metrics.temperature = item.value;
            if (item.sensor_type === 'oxygen_saturation') metrics.oxygen = item.value;
            if (item.sensor_type === 'stress_level') metrics.stress = item.value;
            if (item.sensor_type === 'fall_detection') metrics.fall = item.fall_detected;
        });
        return {
            heartRate: metrics.heartRate ?? '--',
            temperature: metrics.temperature ?? '--',
            oxygen: metrics.oxygen ?? '--',
            stress: metrics.stress ?? '--',
            fall: metrics.fall !== undefined ? (metrics.fall ? 'Sim' : 'Não') : '--'
        };
    } else {
        // summary: statistics é objeto, emergency: pode estar direto em data
        return {
            heartRate: stats.heart_rate?.last_value ?? data.heart_rate ?? '--',
            temperature: stats.temperature?.last_value ?? data.temperature ?? '--',
            oxygen: stats.oxygen_saturation?.last_value ?? data.oxygen_saturation ?? '--',
            stress: stats.stress_level?.last_value ?? data.stress_level ?? '--',
            fall: stats.fall_detection?.fall_detected !== undefined
                ? (stats.fall_detection.fall_detected ? 'Sim' : 'Não')
                : (data.fall_detected !== undefined ? (data.fall_detected ? 'Sim' : 'Não') : '--')
        };
    }
}

// Renderização
function updateStats() {
    const stats = patients.reduce((acc, patient) => {
        acc.total++;
        acc[patient.status]++;
        return acc;
    }, { total: 0, critical: 0, alert: 0, stable: 0 });
    
    elements.criticalCount.textContent = stats.critical;
    elements.alertCount.textContent = stats.alert;
    elements.stableCount.textContent = stats.stable;
    elements.totalCount.textContent = stats.total;
}

function renderPatients() {
    const filteredPatients = filterPatients();
    
    if (filteredPatients.length === 0) {
        showEmptyState();
        return;
    }
    
    elements.patientsGrid.innerHTML = filteredPatients
        .map(patient => createPatientCard(patient))
        .join('');
}

function filterPatients() {
    if (currentFilter === 'all') return patients;
    return patients.filter(patient => patient.status === currentFilter);
}

function createPatientCard(patient) {
    const statusText = {
        critical: 'Crítico',
        alert: 'Alerta',
        stable: 'Estável'
    };

    const timeAgo = formatTimeAgo(patient.timestamp);

    return `
        <div class="patient-card ${patient.status}" onclick="openPatientModal('${patient.id}', '${patient.rawName}')">
            <div class="patient-header">
                <div class="patient-info">
                    <h3>${patient.name}</h3>
                    <div class="patient-id">ID: ${patient.id}</div>
                </div>
                <div class="patient-status ${patient.status}">
                    ${statusText[patient.status]}
                </div>
            </div>
            
            <div class="patient-metrics">
                <div class="metric">
                    <div class="metric-value">${patient.metrics.heartRate}</div>
                    <div class="metric-label">BPM</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${patient.metrics.temperature !== '--' ? parseFloat(patient.metrics.temperature).toFixed(1) : patient.metrics.temperature}</div>
                    <div class="metric-label">°C</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${patient.metrics.oxygen}</div>
                    <div class="metric-label">SpO2</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${patient.metrics.stress}</div>
                    <div class="metric-label">Stress</div>
                </div>
            </div>
            <div class="queda${patient.metrics.fall === 'Sim' ? ' sim' : ''}">Queda: ${patient.metrics.fall}</div>
            <div class="patient-footer">
                <div class="last-message">Última atualização: ${timeAgo}</div>
                <a href="#" class="view-details" onclick="event.stopPropagation(); openPatientModal('${patient.id}', '${patient.rawName}')">Ver detalhes</a>
            </div>
        </div>
    `;
}

function showEmptyState() {
    const filterText = {
        all: 'pacientes',
        critical: 'pacientes críticos',
        alert: 'pacientes com alertas',
        stable: 'pacientes estáveis'
    };
    
    elements.patientsGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
            <i class="fas fa-users"></i>
            <h3>Nenhum ${filterText[currentFilter]} encontrado</h3>
            <p>Verifique se o monitoramento está ativo ou tente atualizar os dados.</p>
        </div>
    `;
}

// Modal
async function openPatientModal(patientId, patientName) {
    try {
        showLoading();
        
        const { patient, messages } = await loadPatientDetails(patientId);
        const patientData = patients.find(p => p.id === patientId);

        elements.modalPatientName.textContent = `Paciente ${patientName}`;
        elements.modalBody.innerHTML = createPatientDetailsContent(patientData, messages);
        
        elements.patientModal.classList.add('show');
        document.body.style.overflow = 'hidden';
    } catch (error) {
        showError('Erro ao carregar detalhes do paciente');
    }
}

function closeModal() {
    elements.patientModal.classList.remove('show');
    document.body.style.overflow = '';
}

function createPatientDetailsContent(patient, messages) {
    const info = patient.info || {};
    const sortedMessages = [...messages].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    // Busca alerts do último resumo/emergência (se houver)
    const latestMsg = sortedMessages[0] || {};
    const alerts = Array.isArray(latestMsg.data?.alerts) ? latestMsg.data.alerts : [];
    return `
        <div class="patient-basic-info">
            <strong>Nome:</strong> ${patient.rawName}<br>
            <strong>Sexo:</strong> ${info.sex === 'F' ? 'Feminino' : 'Masculino'}<br>
            <strong>Idade:</strong> ${info.age || '--'}<br>
            <strong>ID:</strong> ${patient.id}
        </div>
        <hr>
        <div class="patient-details">
            <div class="detail-section">
                <h4>Status Atual</h4>
                <div class="status-overview">
                    <div class="patient-status ${patient.status}">
                        ${patient.status === 'critical' ? 'Crítico' : 
                          patient.status === 'alert' ? 'Alerta' : 'Estável'}
                    </div>
                    <div class="status-metrics">
                        <div class="metric-row">
                            <span>Frequência Cardíaca:</span>
                            <strong>${patient.metrics.heartRate} BPM</strong>
                        </div>
                        <div class="metric-row">
                            <span>Temperatura:</span>
                            <strong>${patient.metrics.temperature !== '--' ? parseFloat(patient.metrics.temperature).toFixed(1) : patient.metrics.temperature}°C</strong>
                        </div>
                        <div class="metric-row">
                            <span>Saturação de Oxigênio:</span>
                            <strong>${patient.metrics.oxygen}%</strong>
                        </div>
                        <div class="metric-row">
                            <span>Nível de Stress:</span>
                            <strong>${patient.metrics.stress}</strong>
                        </div>
                        <div class="metric-row">
                            <span>Queda:</span>
                            <strong>${patient.metrics.fall}</strong>
                        </div>
                    </div>
                    ${alerts.length > 0 ? `
                    <div class="alerts-list" style="margin-top:1rem;">
                        <h5 style="color:#111;margin-bottom:0.5rem;">Alertas recentes:</h5>
                        <ul style="padding-left:1.2rem;">
                            ${alerts.map(alert => {
                                let color = '#111';
                                if (alert.severity === 'concern') color = 'var(--warning-color)';
                                else color = 'var(--danger-color)';
                                return `<li style="color:${color}">${alert.message || alert.type}</li>`;
                            }).join('')}
                        </ul>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h4>Mensagens Recentes</h4>
                <div class="messages-list">
                    ${sortedMessages.slice(0, 10).map(msg => createMessageCard(msg)).join('')}
                </div>
            </div>
        </div>
        
        <style>
            .patient-details { margin-top: 1rem; }
            .detail-section { margin-bottom: 2rem; }
            .detail-section h4 { 
                margin-bottom: 1rem; 
                color: var(--text-primary);
                font-weight: 600;
            }
            .status-overview {
                background: var(--background-color);
                padding: 1rem;
                border-radius: 0.5rem;
            }
            .status-metrics { margin-top: 1rem; }
            .metric-row {
                display: flex;
                justify-content: space-between;
                padding: 0.5rem 0;
                border-bottom: 1px solid var(--border-color);
            }
            .metric-row:last-child { border-bottom: none; }
            .messages-list {
                max-height: 300px;
                overflow-y: auto;
            }
            .message-item {
                background: var(--background-color);
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 0.5rem;
                border-left: 4px solid var(--border-color);
            }
            .message-item.emergency {
                border-left-color: var(--danger-color);
                background: rgba(239, 68, 68, 0.05);
            }
            .message-item.summary {
                border-left-color: var(--primary-color);
            }
            .message-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.5rem;
            }
            .message-type {
                font-weight: 600;
                text-transform: capitalize;
            }
            .message-time {
                color: var(--text-secondary);
                font-size: 0.875rem;
            }
            .message-data {
                font-family: monospace;
                font-size: 0.875rem;
                color: var(--text-secondary);
                background: var(--surface-color);
                padding: 0.5rem;
                border-radius: 0.25rem;
                white-space: pre-wrap;
                word-break: break-word;
            }
            .alerts-list ul { font-weight: 500; }
            
            /* Novos estilos para message cards */
            .messages-list {
                display: flex;
                flex-direction: column;
                gap: 1rem;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .message-card {
                background: var(--surface-color);
                border-radius: 0.75rem;
                padding: 1rem;
                border: 1px solid var(--border-color);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .message-card:hover {
                transform: translateY(-1px);
                box-shadow: var(--shadow-lg);
            }
            
            .message-card.emergency {
                border-left: 4px solid var(--danger-color);
                background: rgba(239, 68, 68, 0.02);
            }
            
            .message-card.critical {
                border-left: 4px solid var(--danger-color);
            }
            
            .message-card.alert {
                border-left: 4px solid var(--warning-color);
            }
            
            .message-card.stable {
                border-left: 4px solid var(--success-color);
            }
            
            .message-card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.75rem;
            }
            
            .message-type-badge {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.025em;
            }
            
            .message-time {
                display: flex;
                align-items: center;
                gap: 0.25rem;
                color: var(--text-secondary);
                font-size: 0.75rem;
            }
            
            .message-metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                gap: 0.75rem;
                margin-bottom: 0.75rem;
            }
            
            .metric-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem;
                background: var(--background-color);
                border-radius: 0.5rem;
                font-size: 0.875rem;
                font-weight: 500;
            }
            
            .metric-item i {
                font-size: 1rem;
            }
            
            .message-alerts {
                border-top: 1px solid var(--border-color);
                padding-top: 0.75rem;
            }
            
            .alerts-header {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--danger-color);
                font-size: 0.875rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
            }
            
            .alerts-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
            }
            
            .alert-tag {
                padding: 0.25rem 0.5rem;
                border-radius: 0.375rem;
                font-size: 0.75rem;
                font-weight: 500;
                border: 1px solid;
            }
            
            .alert-tag.critical {
                background: rgba(239, 68, 68, 0.1);
                color: var(--danger-color);
                border-color: var(--danger-color);
            }
            
            .alert-tag.concern {
                background: rgba(245, 158, 11, 0.1);
                color: var(--warning-color);
                border-color: var(--warning-color);
            }
            
            .alert-tag.more {
                background: var(--background-color);
                color: var(--text-secondary);
                border-color: var(--border-color);
            }
        </style>
    `;
}

function createMessageCard(msg) {
    const messageTypeText = {
        'emergency': 'Emergência',
        'summary': 'Resumo'
    };
    
    const data = msg.data || {};
    const stats = data.statistics || {};
    const alerts = Array.isArray(data.alerts) ? data.alerts : [];
    
    // Extrai métricas principais
    const metrics = {
        heartRate: stats.heart_rate?.last_value ?? stats.heart_rate?.avg ?? '--',
        temperature: stats.temperature?.last_value ?? stats.temperature?.avg ?? '--',
        oxygen: stats.oxygen_saturation?.last_value ?? stats.oxygen_saturation?.avg ?? '--',
        stress: stats.stress_level?.last_value ?? stats.stress_level?.avg ?? '--',
        fall: stats.fall_detection?.fall_detected ? 'Sim' : 'Não'
    };
    
    // Determina cor do card baseado no tipo e status
    let cardClass = 'message-card';
    let statusColor = '#64748b';
    
    if (msg.message_type === 'emergency') {
        cardClass += ' emergency';
        statusColor = 'var(--danger-color)';
    } else if (data.health_status === 'critical') {
        cardClass += ' critical';
        statusColor = 'var(--danger-color)';
    } else if (data.health_status === 'alert') {
        cardClass += ' alert';
        statusColor = 'var(--warning-color)';
    } else {
        cardClass += ' stable';
        statusColor = 'var(--success-color)';
    }
    
    return `
        <div class="${cardClass}">
            <div class="message-card-header">
                <div class="message-type-badge" style="background: ${statusColor};">
                    <i class="fas ${msg.message_type === 'emergency' ? 'fa-exclamation-triangle' : 'fa-chart-line'}"></i>
                    ${messageTypeText[msg.message_type] || msg.message_type}
                </div>
                <div class="message-time">
                    <i class="fas fa-clock"></i>
                    ${formatDateTime(msg.timestamp)}
                </div>
            </div>
            
            <div class="message-metrics">
                <div class="metric-item">
                    <i class="fas fa-heartbeat" style="color: #ef4444;"></i>
                    <span>${metrics.heartRate} bpm</span>
                </div>
                <div class="metric-item">
                    <i class="fas fa-thermometer-half" style="color: #f59e0b;"></i>
                    <span>${metrics.temperature !== '--' ? parseFloat(metrics.temperature).toFixed(1) : metrics.temperature}°C</span>
                </div>
                <div class="metric-item">
                    <i class="fas fa-lungs" style="color: #3b82f6;"></i>
                    <span>${metrics.oxygen}%</span>
                </div>
                <div class="metric-item">
                    <i class="fas fa-brain" style="color: #8b5cf6;"></i>
                    <span>${metrics.stress}%</span>
                </div>
                <div class="metric-item">
                    <i class="fas fa-person-falling" style="color: ${metrics.fall === 'Sim' ? '#ef4444' : '#10b981'};"></i>
                    <span>${metrics.fall}</span>
                </div>
            </div>
            
            ${alerts.length > 0 ? `
                <div class="message-alerts">
                    <div class="alerts-header">
                        <i class="fas fa-exclamation-circle"></i>
                        Alertas (${alerts.length})
                    </div>
                    <div class="alerts-tags">
                        ${alerts.slice(0, 3).map(alert => `
                            <span class="alert-tag ${alert.severity}">
                                ${alert.message || alert.type}
                            </span>
                        `).join('')}
                        ${alerts.length > 3 ? `<span class="alert-tag more">+${alerts.length - 3}</span>` : ''}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

// Filtros
function setFilter(filter) {
    currentFilter = filter;
    
    elements.filterButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        }
    });
    
    renderPatients();
}

// Utilitários
function formatTimeAgo(timestamp) {
    if (!timestamp) return 'Nunca';
    
    const now = new Date();
    const messageTime = new Date(timestamp);
    const diffMs = now - messageTime;
    const diffMinutes = Math.floor(diffMs / 60000);
    
    if (diffMinutes < 1) return 'Agora';
    if (diffMinutes < 60) return `${diffMinutes}m atrás`;
    
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h atrás`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d atrás`;
}

function formatDateTime(timestamp) {
    if (!timestamp) return 'Data inválida';
    
    const date = new Date(timestamp);
    return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function formatMessageData(data) {
    if (!data) return 'Sem dados';
    return JSON.stringify(data, null, 2);
}

function updateLastUpdateTime() {
    const now = new Date();
    elements.lastUpdate.textContent = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function updateConnectionStatus(connected) {
    isConnected = connected;
    
    if (connected) {
        elements.connectionStatus.classList.remove('disconnected');
        elements.connectionStatus.classList.add('connected');
        elements.connectionStatus.querySelector('span').textContent = 'Conectado';
    } else {
        elements.connectionStatus.classList.remove('connected');
        elements.connectionStatus.classList.add('disconnected');
        elements.connectionStatus.querySelector('span').textContent = 'Desconectado';
    }
}

// Auto-update
function startAutoUpdate() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
    
    updateInterval = setInterval(() => {
        loadPatients();
    }, UPDATE_INTERVAL);
}

function stopAutoUpdate() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// UI Feedback
function showLoading() {
    elements.loadingOverlay.classList.add('show');
}

function hideLoading() {
    elements.loadingOverlay.classList.remove('show');
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'error');
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 
                          type === 'error' ? 'fa-exclamation-circle' : 
                          'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Adicionar estilos se não existirem
    if (!document.querySelector('#notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 0.5rem;
                color: white;
                font-weight: 500;
                z-index: 1001;
                animation: slideIn 0.3s ease-out;
                max-width: 400px;
            }
            .notification.success { background: var(--success-color); }
            .notification.error { background: var(--danger-color); }
            .notification.info { background: var(--primary-color); }
            .notification-content {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(styles);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Gerenciamento de visibilidade da página
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopAutoUpdate();
    } else {
        startAutoUpdate();
        loadPatients();
    }
});

// Cleanup ao sair
window.addEventListener('beforeunload', () => {
    stopAutoUpdate();
});
