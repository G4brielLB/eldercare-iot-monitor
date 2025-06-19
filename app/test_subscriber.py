#!/usr/bin/env python3
"""
Teste do ElderCare Subscriber
Testa a recepção e processamento de mensagens MQTT
"""

import time
import threading
import json
import os
from subscriber.subscriber import ElderCareSubscriber
from test_smart_pulseira import test_single_patient

def test_subscriber_basic():
    """Teste básico do subscriber"""
    print("🧪 === TESTE BÁSICO DO SUBSCRIBER ===")
    
    subscriber = ElderCareSubscriber()
    
    # Inicia subscriber em thread separada
    subscriber_thread = threading.Thread(target=subscriber.start_listening)
    subscriber_thread.daemon = True
    subscriber_thread.start()
    
    print("⏱️ Aguardando 5 segundos para subscriber conectar...")
    time.sleep(5)
    
    # Agora inicia uma pulseira para gerar dados
    print("🔧 Iniciando pulseira de teste...")
    test_single_patient("TEST001", 30)  # 30 segundos de teste
    
    print("✅ Teste básico concluído!")

def test_subscriber_with_multiple_patients():
    """Teste com múltiplas pulseiras"""
    print("🧪 === TESTE SUBSCRIBER MÚLTIPLAS PULSEIRAS ===")
    
    from test_smart_pulseira import simulate_multiple_patients
    
    subscriber = ElderCareSubscriber()
    
    # Inicia subscriber
    subscriber_thread = threading.Thread(target=subscriber.start_listening)
    subscriber_thread.daemon = True
    subscriber_thread.start()
    
    print("⏱️ Aguardando subscriber conectar...")
    time.sleep(3)
    
    # Múltiplas pulseiras
    simulate_multiple_patients(["MULTI001", "MULTI002"], 60)
    
    print("✅ Teste múltiplas pulseiras concluído!")

def check_data_files():
    """Verifica arquivos de dados criados"""
    print("📁 === VERIFICANDO ARQUIVOS DE DADOS ===")
    
    data_dir = "data"
    files_to_check = [
        "messages.json",
        "patients_status.json", 
        "heartbeats.json"
    ]
    
    for filename in files_to_check:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {filename}: {size} bytes")
            
            # Mostra amostra do conteúdo
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        print(f"   📊 {len(data)} entradas")
                    elif isinstance(data, dict):
                        print(f"   📊 {len(data)} pacientes/entradas")
            except Exception as e:
                print(f"   ⚠️ Erro lendo arquivo: {e}")
        else:
            print(f"❌ {filename}: não encontrado")

def show_patient_status():
    """Mostra status atual dos pacientes"""
    print("👥 === STATUS DOS PACIENTES ===")
    
    patients_file = "data/patients_status.json"
    if os.path.exists(patients_file):
        with open(patients_file, 'r', encoding='utf-8') as f:
            patients = json.load(f)
        
        for patient_id, status in patients.items():
            state = status.get('current_state', 'UNKNOWN')
            last_update = status.get('last_updated', 'N/A')
            print(f"   {patient_id}: {state} (atualizado: {last_update})")
    else:
        print("   Nenhum dado de paciente encontrado")

def interactive_subscriber_test():
    """Teste interativo do subscriber"""
    print("\n" + "="*50)
    print("🧪 TESTES DO ELDERCARE SUBSCRIBER")
    print("="*50)
    print("Escolha o tipo de teste:")
    print("1 - Teste básico (1 pulseira, 30s)")
    print("2 - Múltiplas pulseiras (2 pulseiras, 60s)")
    print("3 - Verificar arquivos de dados")
    print("4 - Status dos pacientes")
    print("5 - Subscriber contínuo (manual)")
    print("0 - Sair")
    
    while True:
        try:
            choice = input("\nDigite sua escolha (0-5): ").strip()
            
            if choice == "0":
                print("👋 Saindo...")
                break
            elif choice == "1":
                test_subscriber_basic()
            elif choice == "2":
                test_subscriber_with_multiple_patients()
            elif choice == "3":
                check_data_files()
            elif choice == "4":
                show_patient_status()
            elif choice == "5":
                print("🔄 Iniciando subscriber contínuo...")
                print("   Pressione Ctrl+C para parar")
                subscriber = ElderCareSubscriber()
                subscriber.start_listening()
            else:
                print("❌ Opção inválida!")
                continue
            
            if choice in ["1", "2"]:
                print("\n📁 Verificando dados gerados...")
                check_data_files()
                show_patient_status()
            
            if choice != "5":
                continue_choice = input("\nDeseja executar outro teste? (s/N): ").strip().lower()
                if continue_choice not in ['s', 'sim', 'y', 'yes']:
                    print("👋 Finalizando testes...")
                    break
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Teste interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    interactive_subscriber_test()
