import os
import subprocess

print("🔄 Fazendo rollback para commit a45d2be...")

# Mudar para o diretório
os.chdir("C:\\CARTA_AUTOMATICA")

# Comando 1: Reset hard
print("1. Executando git reset --hard a45d2be...")
try:
    resultado = subprocess.run(["git", "reset", "--hard", "a45d2be"], 
                             capture_output=True, text=True, timeout=30)
    print(f"Código de retorno: {resultado.returncode}")
    print(f"Saída: {resultado.stdout}")
    if resultado.stderr:
        print(f"Erro: {resultado.stderr}")
except Exception as e:
    print(f"Erro ao executar reset: {e}")

# Comando 2: Push force
print("\n2. Executando git push --force origin main...")
try:
    resultado = subprocess.run(["git", "push", "--force", "origin", "main"], 
                             capture_output=True, text=True, timeout=60)
    print(f"Código de retorno: {resultado.returncode}")
    print(f"Saída: {resultado.stdout}")
    if resultado.stderr:
        print(f"Erro: {resultado.stderr}")
except Exception as e:
    print(f"Erro ao executar push: {e}")

print("\n✅ Rollback concluído!") 