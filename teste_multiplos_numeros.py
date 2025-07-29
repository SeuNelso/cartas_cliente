#!/usr/bin/env python3
"""
Script de teste para a funcionalidade de múltiplos números por cliente
"""

import pandas as pd
import os
from processador_excel import ProcessadorExcel

def criar_excel_teste():
    """Cria um arquivo Excel de teste"""
    dados = {
        'Cliente': [
            'João Silva', 'João Silva', 'João Silva',
            'Maria Costa', 'Maria Costa', 'Maria Costa', 'Maria Costa', 
            'Maria Costa', 'Maria Costa', 'Maria Costa',
            'Pedro Santos', 'Ana Oliveira', 'Ana Oliveira'
        ],
        'Número': [
            '928307037', '928351767', '928351768',
            '928351769', '928351770', '928351771', '928351772',
            '928351773', '928351774', '928351775',
            '928351776', '928351777', '928351778'
        ],
        'ICCID': [
            '8935102241115578094', '8935102241115578102', '8935102241115578103',
            '8935102241115578104', '8935102241115578105', '8935102241115578106',
            '8935102241115578107', '8935102241115578108', '8935102241115578109',
            '8935102241115578110', '8935102241115578111', '8935102241115578112',
            '8935102241115578113'
        ]
    }
    
    df = pd.DataFrame(dados)
    df.to_excel('dados_teste.xlsx', index=False)
    print("✅ Arquivo Excel de teste criado: dados_teste.xlsx")
    return 'dados_teste.xlsx'

def testar_processamento():
    """Testa o processamento do Excel"""
    try:
        # Criar arquivo de teste
        arquivo_excel = criar_excel_teste()
        
        # Processar Excel
        processador = ProcessadorExcel()
        cartas = processador.processar_excel(arquivo_excel)
        
        print(f"\n📊 Resultados do processamento:")
        print(f"Total de cartas: {len(cartas)}")
        
        for carta in cartas:
            print(f"\n📄 Carta {carta['numero_carta']} de {carta['total_cartas']} para {carta['cliente']}")
            print(f"   Números: {len(carta['numeros'])}")
            for i, numero in enumerate(carta['numeros'], 1):
                print(f"   {i}. {numero['numero']} - {numero['iccid']}")
        
        # Testar geração de SVG
        print(f"\n🎨 Testando geração de SVG...")
        template_path = "templates_word/carta-digi-6linhas.svg"
        
        if os.path.exists(template_path):
            for carta in cartas[:2]:  # Testar apenas 2 cartas
                svg_content = processador.gerar_svg_carta(carta, template_path)
                
                # Salvar SVG de teste
                nome_arquivo = f"teste_{carta['cliente']}_carta_{carta['numero_carta']}.svg"
                with open(nome_arquivo, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                print(f"✅ SVG gerado: {nome_arquivo}")
        
        else:
            print(f"⚠️  Template não encontrado: {template_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return False

def limpar_arquivos_teste():
    """Remove arquivos de teste"""
    arquivos_para_remover = [
        'dados_teste.xlsx',
        'teste_João Silva_carta_1.svg',
        'teste_João Silva_carta_2.svg'
    ]
    
    for arquivo in arquivos_para_remover:
        if os.path.exists(arquivo):
            os.remove(arquivo)
            print(f"🗑️  Removido: {arquivo}")

if __name__ == "__main__":
    print("🧪 Iniciando testes da funcionalidade de múltiplos números...")
    
    try:
        sucesso = testar_processamento()
        
        if sucesso:
            print("\n✅ Todos os testes passaram!")
        else:
            print("\n❌ Alguns testes falharam!")
            
    except Exception as e:
        print(f"\n💥 Erro durante os testes: {str(e)}")
    
    finally:
        # Perguntar se quer limpar arquivos de teste
        resposta = input("\n🧹 Deseja remover os arquivos de teste? (s/n): ")
        if resposta.lower() in ['s', 'sim', 'y', 'yes']:
            limpar_arquivos_teste()
            print("✅ Arquivos de teste removidos!")
        else:
            print("📁 Arquivos de teste mantidos para inspeção.") 