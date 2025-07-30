#!/usr/bin/env python3
import subprocess
import sys

def executar_comando(comando):
    """Executa um comando e retorna o resultado"""
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        return resultado.returncode, resultado.stdout, resultado.stderr
    except Exception as e:
        return 1, "", str(e)

def main():
    print("🔄 Fazendo reset para o commit dff0636...")
    
    # 1. Verificar status atual
    print("📊 Status atual:")
    codigo, saida, erro = executar_comando("git status")
    print(saida)
    if erro:
        print(f"⚠️  Avisos: {erro}")
    
    # 2. Fazer reset hard
    print("\n🔄 Executando git reset --hard dff0636...")
    codigo, saida, erro = executar_comando("git reset --hard dff0636")
    
    if codigo == 0:
        print("✅ Reset realizado com sucesso!")
        print(saida)
    else:
        print("❌ Erro no reset:")
        print(erro)
        return
    
    # 3. Verificar status após reset
    print("\n📊 Status após reset:")
    codigo, saida, erro = executar_comando("git status")
    print(saida)
    
    print("\n🎯 Reset para commit dff0636 concluído!")

if __name__ == "__main__":
    main() 