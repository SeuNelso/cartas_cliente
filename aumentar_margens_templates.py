#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import glob

def aumentar_margens_template(svg_content, nome_template):
    """
    Aumenta as margens de um template SVG para evitar overflow
    """
    
    print(f"🔧 Aumentando margens do template: {nome_template}")
    
    # 1. Expandir o viewBox para dar mais margem
    # Largura: 420.9449 -> 500 (mais margem lateral)
    # Altura: 595.2755737 -> 700 (mais margem vertical)
    svg_content = re.sub(
        r'viewBox="0 0 420\.9449 595\.2755737"',
        'viewBox="0 0 500 700"',
        svg_content
    )
    
    # 2. Ajustar posições dos elementos de texto principais
    # Mover textos ligeiramente para a direita para dar mais margem
    svg_content = re.sub(
        r'<text x="22\.6"',
        '<text x="42.6"',
        svg_content
    )
    
    # 3. Ajustar posições de transform translate
    # Para templates que usam transform="translate(x y)"
    svg_content = re.sub(
        r'transform="translate\(22\.5977704',
        'transform="translate(42.5977704',
        svg_content
    )
    
    # 4. Expandir largura das tabelas
    # Aumentar largura das linhas da tabela
    svg_content = re.sub(
        r'<line x1="50\.5" y1="[^"]*" x2="351\.1" y2="[^"]*"',
        lambda match: match.group(0).replace('x2="351.1"', 'x2="450.1"'),
        svg_content
    )
    
    # 5. Ajustar posições das colunas da tabela
    # Mover coluna ICCID para a direita
    svg_content = re.sub(
        r'<text x="194\.7"',
        '<text x="250.7"',
        svg_content
    )
    
    # 6. Ajustar posições de transform para tabelas
    svg_content = re.sub(
        r'transform="translate\(194\.6543958',
        'transform="translate(250.6543958',
        svg_content
    )
    
    # 7. Mover código do cliente para posição mais alta
    # Evitar que saia da tela
    svg_content = re.sub(
        r'transform="translate\(360\.505821 542\.4750366\)"',
        'transform="translate(460.505821 620.4750366)"',
        svg_content
    )
    
    # 8. Ajustar posições específicas para templates com múltiplos números
    # Mover tabelas para baixo para dar espaço ao texto expandido
    if "carta_2_numeros" in nome_template or "carta_3_numeros" in nome_template or "carta_4_numeros" in nome_template or "carta_5_numeros" in nome_template or "carta_6_numeros" in nome_template:
        # Ajustar posições das tabelas para templates com múltiplos números
        svg_content = re.sub(
            r'<text x="49\.9" y="324\.5"',
            '<text x="49.9" y="344.5"',
            svg_content
        )
        
        # Ajustar linhas da tabela
        svg_content = re.sub(
            r'<line x1="50\.5" y1="327\.5"',
            '<line x1="50.5" y1="347.5"',
            svg_content
        )
    
    print(f"✅ Margens aumentadas para: {nome_template}")
    return svg_content

def processar_todos_templates():
    """
    Processa todos os templates SVG na pasta templates/
    """
    
    print("🚀 Iniciando processamento de todos os templates...")
    
    # Encontrar todos os arquivos SVG na pasta templates
    templates = glob.glob("templates/carta_*.svg")
    
    if not templates:
        print("❌ Nenhum template encontrado na pasta templates/")
        return
    
    print(f"📁 Encontrados {len(templates)} templates:")
    for template in templates:
        print(f"  - {os.path.basename(template)}")
    
    # Processar cada template
    for template_path in templates:
        nome_template = os.path.basename(template_path)
        
        try:
            # Ler template original
            with open(template_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Aplicar aumento de margens
            svg_modificado = aumentar_margens_template(svg_content, nome_template)
            
            # Salvar template modificado
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(svg_modificado)
            
            print(f"✅ Template processado: {nome_template}")
            
        except Exception as e:
            print(f"❌ Erro ao processar {nome_template}: {e}")
    
    print("\n🎯 Processamento concluído!")
    print("📝 Todos os templates foram atualizados com margens aumentadas")

def testar_template_modificado():
    """
    Testa um template modificado para verificar se as margens estão corretas
    """
    
    print("🧪 Testando template modificado...")
    
    # Testar com carta_1_numero.svg
    template_path = "templates/carta_1_numero.svg"
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Verificar se o viewBox foi expandido
        if 'viewBox="0 0 500 700"' in svg_content:
            print("✅ ViewBox expandido corretamente")
        else:
            print("❌ ViewBox não foi expandido")
        
        # Verificar se as posições foram ajustadas
        if 'x="42.6"' in svg_content:
            print("✅ Posições de texto ajustadas")
        else:
            print("❌ Posições de texto não foram ajustadas")
        
        print("📄 Template pronto para teste de geração de PDF")

if __name__ == "__main__":
    print("🔄 Iniciando aumento de margens para todos os templates...")
    
    # Processar todos os templates
    processar_todos_templates()
    
    # Testar template modificado
    testar_template_modificado()
    
    print("\n🎉 Processo concluído!")
    print("📋 Agora todos os templates têm margens aumentadas para evitar overflow") 