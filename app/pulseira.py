#!/usr/bin/env python3
"""
Script para simular uma pulseira IoT individual
Permite personalizar sensores e executar monitoramento
"""

import sys
import os
from sensors.smart_pulseira import SmartPulseira

def main():
    """Interface interativa para criar e executar uma pulseira"""
    print("🔧 === SIMULADOR DE PULSEIRA IOT ===")
    print("Configure uma pulseira personalizada para monitoramento")
    
    try:
        # 1. ID do paciente
        patient_id = input("\n👤 ID do paciente (ex: PAT001): ").strip()
        if not patient_id:
            patient_id = "PAT001"
            print(f"   Usando ID padrão: {patient_id}")
        
        # 2. Duração do monitoramento
        duration_input = input("⏱️  Duração em segundos (ex: 120): ").strip()
        duration = int(duration_input) if duration_input else 120
        print(f"   Duração configurada: {duration} segundos")
        
        # 3. Configuração dos sensores
        print("\n🔧 === CONFIGURAÇÃO DOS SENSORES ===")
        print("Sensores disponíveis:")
        print("  - oxigenio (stable/alert/critical)")
        print("  - stress (stable/alert/critical)")
        print("  - temperatura (stable/alert/critical)")
        print("  - batimento (stable/alert/critical)")
        print("  - queda (low/medium/high)")
        
        # Valores padrão
        oxygen_status = "stable"
        stress_status = "stable"
        temp_status = "stable"
        heart_rate_status = "stable"
        fall_chance = "low"
        
        # Pergunta quais sensores personalizar
        sensores_input = input("\n🎛️  Quais sensores deseja personalizar? (separe por vírgula, ou deixe vazio para padrão): ").strip().lower()
        
        if sensores_input:
            sensores = [s.strip() for s in sensores_input.split(",") if s.strip()]
            
            print(f"\n📝 Configurando {len(sensores)} sensor(es) personalizado(s):")
            
            # Configuração individual de cada sensor escolhido
            if "oxigenio" in sensores or "oxygen" in sensores:
                oxygen_status = input("   🫁 Status do sensor de oxigênio (stable/alert/critical): ").strip().lower() or "stable"
                print(f"      ✅ Oxigênio: {oxygen_status}")
            
            if "stress" in sensores:
                stress_status = input("   😰 Status do sensor de stress (stable/alert/critical): ").strip().lower() or "stable"
                print(f"      ✅ Stress: {stress_status}")
            
            if "temperatura" in sensores or "temp" in sensores:
                temp_status = input("   🌡️  Status do sensor de temperatura (stable/alert/critical): ").strip().lower() or "stable"
                print(f"      ✅ Temperatura: {temp_status}")
            
            if "batimento" in sensores or "heart" in sensores or "coracao" in sensores:
                heart_rate_status = input("   💓 Status do sensor de batimento (stable/alert/critical): ").strip().lower() or "stable"
                print(f"      ✅ Batimento: {heart_rate_status}")
            
            if "queda" in sensores or "fall" in sensores:
                fall_chance = input("   🤸 Chance de queda (low/medium/high): ").strip().lower() or "low"
                print(f"      ✅ Queda: {fall_chance}")
        else:
            print("   📋 Usando configuração padrão para todos os sensores")
        
        # 4. Resumo da configuração
        print(f"\n📋 === RESUMO DA CONFIGURAÇÃO ===")
        print(f"👤 Paciente: {patient_id}")
        print(f"⏱️  Duração: {duration} segundos")
        print(f"🫁 Oxigênio: {oxygen_status}")
        print(f"😰 Stress: {stress_status}")
        print(f"🌡️  Temperatura: {temp_status}")
        print(f"💓 Batimento: {heart_rate_status}")
        print(f"🤸 Queda: {fall_chance}")
        
        # 5. Confirmação
        confirma = input("\n✅ Confirmar e iniciar monitoramento? (s/N): ").strip().lower()
        if confirma not in ['s', 'sim', 'y', 'yes']:
            print("❌ Operação cancelada pelo usuário")
            return
        
        # 6. Criação e execução da pulseira
        print(f"\n🚀 === INICIANDO PULSEIRA {patient_id} ===")
        
        # Instancia a pulseira com configurações personalizadas
        pulseira = SmartPulseira(
            patient_id=patient_id,
            oxygen_status=oxygen_status,
            stress_status=stress_status,
            temp_status=temp_status,
            heart_rate_status=heart_rate_status,
            fall_chance=fall_chance
        )
        
        # Inicia o monitoramento
        success = pulseira.start_monitoring(duration)
        
        if success:
            print(f"\n🎉 Monitoramento da pulseira {patient_id} finalizado com sucesso!")
        else:
            print(f"\n❌ Erro durante o monitoramento da pulseira {patient_id}")
    
    except KeyboardInterrupt:
        print(f"\n🛑 Interrompido pelo usuário (Ctrl+C)")
    except ValueError as e:
        print(f"\n❌ Valor inválido: {e}")
        print("   💡 Dica: Verifique se a duração é um número válido")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("   💡 Dica: Verifique se o MQTT broker está rodando")


def show_help():
    """Mostra ajuda sobre como usar o script"""
    print("🆘 === AJUDA - SIMULADOR DE PULSEIRA ===")
    print()
    print("Este script simula uma pulseira IoT individual para monitoramento de pacientes.")
    print()
    print("📋 COMO USAR:")
    print("1. Execute: python pulseira.py")
    print("2. Informe o ID do paciente (ex: PAT001)")
    print("3. Defina a duração em segundos (ex: 120)")
    print("4. Escolha quais sensores personalizar (opcional)")
    print("5. Configure os valores dos sensores escolhidos")
    print("6. Confirme e acompanhe o monitoramento")
    print()
    print("🎛️  SENSORES DISPONÍVEIS:")
    print("• oxigenio: stable (95-100%), alert (90-94%), critical (80-89%)")
    print("• stress: stable (baixo), alert (médio), critical (alto)")
    print("• temperatura: stable (normal), alert (febre leve), critical (febre alta)")
    print("• batimento: stable (normal), alert (alterado), critical (crítico)")
    print("• queda: low (1%), medium (5%), high (10%)")
    print()
    print("💡 DICAS:")
    print("• Deixe sensores em branco para usar valores padrão")
    print("• Use Ctrl+C para interromper o monitoramento")
    print("• Certifique-se que o MQTT broker está rodando")
    print("• O subscriber deve estar ativo para receber os dados")


if __name__ == "__main__":
    # Verifica se o usuário quer ajuda
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
    else:
        main()
