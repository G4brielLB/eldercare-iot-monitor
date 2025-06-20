"""
Módulo API do ElderCare IoT Monitor

Este módulo contém a API FastAPI para servir dados do sistema de monitoramento de idosos.

Estrutura:
- main.py: Aplicação FastAPI principal
- routers/: Endpoints organizados por domínio
  - dashboard.py: Endpoints do dashboard geral
  - patients.py: Endpoints específicos de pacientes
- dependencies.py: Dependências compartilhadas

A API segue os princípios SOLID:
- SRP: Cada router tem uma responsabilidade específica
- OCP: Novos endpoints podem ser adicionados sem modificar existentes
- DIP: Routers dependem de abstrações (database/crud)
"""
