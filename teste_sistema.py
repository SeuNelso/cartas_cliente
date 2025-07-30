#!/usr/bin/env python3
"""
Script de teste para verificar o sistema de geração de PDFs por cliente
"""

import os
import sys
from app import process_pdf_generation_por_cliente, agrupar_por_cliente, read_excel_with_openpyxl

def testar_sistema():
    print("🧪 Testando sistema de geração de PDFs por cliente...")
    
    # Arquivo de teste
    excel_file = "teste_clientes.xlsx"
    excel_path = os.path.join("uploads", excel_file)
    
    if not os.path.exists(excel_path):
        print(f"❌ Arquivo de teste não encontrado: {excel_path}")
        return False
    
    try:
        # Ler dados do Excel
        print("📊 Lendo dados do Excel...")
        columns, data = read_excel_with_openpyxl(excel_path)
        print(f"✅ Dados lidos: {len(data)} registros")
        print(f"📋 Colunas: {columns}")
        
        # Agrupar por cliente
        print("👥 Agrupando por cliente...")
        clientes = agrupar_por_cliente(data, "Cliente")
        print(f"✅ Clientes encontrados: {len(clientes)}")
        
        for cliente, registros in clientes.items():
            print(f"  - {cliente}: {len(registros)} números")
        
        # Testar processamento
        print("🔄 Testando processamento...")
        job_id = "teste_123"
        
        # Simular processamento
        process_pdf_generation_por_cliente(
            job_id=job_id,
            excel_file=excel_file,
            coluna_cliente="Cliente",
            coluna_numero="Número",
            coluna_iccid="ICCID"
        )
        
        print("✅ Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = testar_sistema()
    sys.exit(0 if success else 1) 