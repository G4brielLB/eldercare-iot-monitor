#!/usr/bin/env python3
"""
Testes e simulações para SmartPulseira
Sistema de monitoramento de idosos com pulseira IoT simulada

Este arquivo contém funções de teste para validar o funcionamento 
completo da pulseira inteligente, incluindo:
- Teste individual de pulseira
- Simulação de múltiplas pulseiras simultâneas
- Testes de integração de todos os componentes

Uso:
    python test_smart_pulseira.py
"""

import time
import threading
from typing import List
from sensors.smart_pulseira import SmartPulseira


def test_single_patient(patient_id: str = "PAT001", duration: int = 120):
    """
    Testa uma pulseira individual
    
    Args:
        patient_id: ID do paciente para teste
        duration: Duração do teste em segundos
    """
    print(f"🧪 === TESTE PULSEIRA INDIVIDUAL - {patient_id} ===")
    print(f"⏱️  Duração: {duration} segundos")
    print("📝 Testando: sensores + edge processing + MQTT publishing")
    
    pulseira = SmartPulseira(patient_id)
    success = pulseira.start_monitoring(duration)
    
    if success:
        print(f"✅ Teste finalizado com sucesso para {patient_id}")
    else:
        print(f"❌ Teste falhou para {patient_id}")
    
    return success


def simulate_multiple_patients(patient_ids: List[str], duration: int = 180):
    """
    Simula múltiplas pulseiras simultaneamente
    
    Args:
        patient_ids: Lista de IDs dos pacientes
        duration: Duração da simulação em segundos
    """
    print(f"🧪 === SIMULAÇÃO MÚLTIPLAS PULSEIRAS ===")
    print(f"👥 Pacientes: {', '.join(patient_ids)}")
    print(f"⏱️  Duração: {duration} segundos")
    print("📝 Testando: concorrência + múltiplos clientes MQTT")
    
    threads = []
    pulseiras = []
    results = []
    
    # Função wrapper para capturar resultado
    def run_pulseira_test(pulseira, duration, results, index):
        try:
            success = pulseira.start_monitoring(duration)
            results.append((index, pulseira.patient_id, success))
        except Exception as e:
            print(f"❌ Erro na pulseira {pulseira.patient_id}: {e}")
            results.append((index, pulseira.patient_id, False))
    
    # Inicia cada pulseira em thread separada
    for i, patient_id in enumerate(patient_ids):
        print(f"🔧 Inicializando pulseira {patient_id}...")
        pulseira = SmartPulseira(patient_id)
        pulseiras.append(pulseira)
        
        thread = threading.Thread(
            target=run_pulseira_test,
            args=(pulseira, duration, results, i)
        )
        thread.start()
        threads.append(thread)
        
        # Pequeno delay entre inicializações para evitar conflitos
        time.sleep(2)
    
    print(f"🚀 Todas as {len(patient_ids)} pulseiras iniciadas!")
    
    # Aguarda todas finalizarem
    for thread in threads:
        thread.join()
    
    # Mostra resultados finais
    print(f"\n📊 === RESULTADOS DA SIMULAÇÃO ===")
    successful = 0
    for index, patient_id, success in results:
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"   {patient_id}: {status}")
        if success:
            successful += 1
    
    print(f"\n🏁 Simulação finalizada: {successful}/{len(patient_ids)} pulseiras executaram com sucesso")
    return successful == len(patient_ids)


def test_stress_scenario(num_patients: int = 5, duration: int = 300):
    """
    Teste de estresse com muitas pulseiras simultâneas
    
    Args:
        num_patients: Número de pulseiras para testar
        duration: Duração do teste em segundos
    """
    print(f"🔥 === TESTE DE ESTRESSE ===")
    print(f"👥 Número de pulseiras: {num_patients}")
    print(f"⏱️  Duração: {duration} segundos")
    
    # Gera IDs de pacientes
    patient_ids = [f"STRESS{i:03d}" for i in range(1, num_patients + 1)]
    
    start_time = time.time()
    success = simulate_multiple_patients(patient_ids, duration)
    end_time = time.time()
    
    total_time = end_time - start_time
    print(f"\n📈 Tempo total de execução: {total_time:.1f} segundos")
    print(f"⚡ Performance: {num_patients * duration / total_time:.1f} pulseira-segundos/segundo")
    
    return success


def test_quick_validation():
    """Teste rápido para validação básica"""
    print(f"⚡ === TESTE RÁPIDO DE VALIDAÇÃO ===")
    print("📝 Teste de 30 segundos para validar funcionamento básico")
    
    return test_single_patient("QUICK001", 30)


def interactive_test_menu():
    """Menu interativo para escolher tipo de teste"""
    print("\n" + "="*50)
    print("🧪 SISTEMA DE TESTES - PULSEIRA INTELIGENTE")
    print("="*50)
    print("Escolha o tipo de teste:")
    print("1 - Teste rápido (30 segundos)")
    print("2 - Teste individual padrão (2 minutos)")
    print("3 - Múltiplas pulseiras (PAT001, PAT002, 3 minutos)")
    print("4 - Teste de estresse (5 pulseiras, 5 minutos)")
    print("5 - Teste personalizado")
    print("0 - Sair")
    
    while True:
        try:
            choice = input("\nDigite sua escolha (0-5): ").strip()
            
            if choice == "0":
                print("👋 Saindo...")
                break
            elif choice == "1":
                test_quick_validation()
            elif choice == "2":
                test_single_patient("PAT001", 120)
            elif choice == "3":
                simulate_multiple_patients(["PAT001", "PAT002"], 180)
            elif choice == "4":
                test_stress_scenario(5, 300)
            elif choice == "5":
                custom_test()
            else:
                print("❌ Opção inválida! Tente novamente.")
                continue
            
            # Pergunta se quer continuar
            continue_choice = input("\nDeseja executar outro teste? (s/N): ").strip().lower()
            if continue_choice not in ['s', 'sim', 'y', 'yes']:
                print("👋 Finalizando testes...")
                break
                
        except KeyboardInterrupt:
            print("\n\n🛑 Interrompido pelo usuário. Saindo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")


def custom_test():
    """Permite configurar teste personalizado"""
    print("\n🔧 === TESTE PERSONALIZADO ===")
    
    try:
        # Tipo de teste
        test_type = input("Tipo (1=individual, 2=múltiplas): ").strip()
        
        if test_type == "1":
            patient_id = input("ID do paciente (ex: PAT001): ").strip() or "PAT001"
            duration = int(input("Duração em segundos (ex: 120): ").strip() or "120")
            test_single_patient(patient_id, duration)
            
        elif test_type == "2":
            patients_input = input("IDs dos pacientes separados por vírgula (ex: PAT001,PAT002): ").strip()
            if patients_input:
                patient_ids = [p.strip() for p in patients_input.split(",")]
            else:
                patient_ids = ["PAT001", "PAT002"]
            
            duration = int(input("Duração em segundos (ex: 180): ").strip() or "180")
            simulate_multiple_patients(patient_ids, duration)
        else:
            print("❌ Tipo inválido!")
            
    except ValueError as e:
        print(f"❌ Valor inválido: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")


def main():
    """Função principal para execução direta do script"""
    try:
        interactive_test_menu()
    except KeyboardInterrupt:
        print("\n\n🛑 Programa interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


if __name__ == "__main__":
    main()
