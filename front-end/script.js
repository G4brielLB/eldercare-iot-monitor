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
        patients = processPatientData(data);
        
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

// Processamento de dados
function processPatientData(data) {
    return data.map(item => {
        const patient = {
            id: item.patient_id,
            name: `Paciente ${item.patient_id}`,
            lastMessage: item,
            timestamp: item.timestamp,
            status: determinePatientStatus(item),
            metrics: extractMetrics(item.data)
        };
        
        return patient;
    });
}

function determinePatientStatus(message) {
    if (message.message_type === 'emergency') {
        return 'critical';
    }
    
    const data = message.data || {};
    const alerts = data.alerts || [];
    
    if (alerts.length > 0) {
        return 'alert';
    }
    
    return 'stable';
}

function extractMetrics(data) {
    if (!data) return {};
    
    return {
        heartRate: data.heart_rate || data.bpm || '--',
        temperature: data.temperature || data.temp || '--',
        oxygen: data.oxygen_saturation || data.spo2 || '--',
        stress: data.stress_level || '--'
    };
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
        <div class="patient-card ${patient.status}" onclick="openPatientModal('${patient.id}')">
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
                    <div class="metric-value">${patient.metrics.temperature}</div>
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
            
            <div class="patient-footer">
                <div class="last-message">Última atualização: ${timeAgo}</div>
                <a href="#" class="view-details" onclick="event.stopPropagation()">Ver detalhes</a>
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
async function openPatientModal(patientId) {
    try {
        showLoading();
        
        const { patient, messages } = await loadPatientDetails(patientId);
        const patientData = patients.find(p => p.id === patientId);
        
        elements.modalPatientName.textContent = `Paciente ${patientId}`;
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
    const recentMessages = messages.slice(-10).reverse();
    
    return `
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
                            <strong>${patient.metrics.temperature}°C</strong>
                        </div>
                        <div class="metric-row">
                            <span>Saturação de Oxigênio:</span>
                            <strong>${patient.metrics.oxygen}%</strong>
                        </div>
                        <div class="metric-row">
                            <span>Nível de Stress:</span>
                            <strong>${patient.metrics.stress}</strong>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h4>Mensagens Recentes</h4>
                <div class="messages-list">
                    ${recentMessages.map(msg => `
                        <div class="message-item ${msg.message_type}">
                            <div class="message-header">
                                <span class="message-type">${msg.message_type}</span>
                                <span class="message-time">${formatDateTime(msg.timestamp)}</span>
                            </div>
                            <div class="message-data">
                                ${formatMessageData(msg.data)}
                            </div>
                        </div>
                    `).join('')}
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
        </style>
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
    elements.lastUpdate.textContent = now.toLocaleTimeString('pt-BR');
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
