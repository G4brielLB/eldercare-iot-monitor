#!/usr/bin/env python3
"""
Setup inicial do banco de dados SQLite
Cria tabelas e popula com dados de exemplo
"""

import sys
import os

# Adicionar app ao path para importações
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import create_database, initialize_sample_patients

def setup_database():
    """Setup completo do banco de dados"""
    print("🏗️  === SETUP DO BANCO DE DADOS ELDERCARE ===\n")
    
    print("1. Criando estrutura do banco...")
    create_database()
    
    print("\n2. Inserindo pacientes de exemplo...")
    initialize_sample_patients()
    
    print("\n✅ === SETUP CONCLUÍDO ===")
    print("📂 Banco criado em: app/health.db")
    print("👥 Pacientes: PAT001, PAT002, PAT003")
    print("🚀 Sistema pronto para receber dados via MQTT")
    print("\nPróximos passos:")
    print("- Execute: python app/subscriber/subscriber.py")
    print("- Execute: python app/test_smart_pulseira.py")

if __name__ == "__main__":
    setup_database()
