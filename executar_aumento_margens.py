#!/usr/bin/env python3
import subprocess
import sys

def executar_script():
    try:
        print("🚀 Executando script de aumento de margens...")
        resultado = subprocess.run(
            [sys.executable, "aumentar_margens_templates.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("📤 Saída do script:")
        print(resultado.stdout)
        
        if resultado.stderr:
            print("⚠️  Erros:")
            print(resultado.stderr)
            
        if resultado.returncode == 0:
            print("✅ Script executado com sucesso!")
        else:
            print(f"❌ Script falhou com código: {resultado.returncode}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Script demorou muito para executar")
    except Exception as e:
        print(f"❌ Erro ao executar script: {e}")

if __name__ == "__main__":
    executar_script() 