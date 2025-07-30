#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def aplicar_margens_template_4_6(svg_content, template_name):
    """
    Aplica as mesmas alterações de margem dos templates 1-3 para templates 4-6
    """
    
    print(f"🔧 Aplicando margens do template: {template_name}")
    
    # 1. Expandir o viewBox (mesmo que template 1)
    # De: viewBox="0 0 420.9449 595.2755737"
    # Para: viewBox="0 0 500 700"
    svg_content = re.sub(
        r'viewBox="0 0 420\.9449 595\.2755737"',
        'viewBox="0 0 500 700"',
        svg_content
    )
    
    # 2. Ajustar largura e altura do rect
    svg_content = re.sub(
        r'<rect width="420\.9449" height="595\.2755737"',
        '<rect width="500" height="700"',
        svg_content
    )
    
    # 3. Mover texto principal para direita (x="22.6" -> x="42.6")
    svg_content = re.sub(
        r'x="22\.6"',
        'x="42.6"',
        svg_content
    )
    
    # 4. Expandir largura das tabelas (x2="351.1" -> x2="451.1")
    svg_content = re.sub(
        r'x2="351\.1"',
        'x2="451.1"',
        svg_content
    )
    
    # 5. Ajustar posição da coluna ICCID (x="194.7" -> x="250.7")
    svg_content = re.sub(
        r'x="194\.7"',
        'x="250.7"',
        svg_content
    )
    
    # 6. Mover código do cliente para posição mais alta (y="542.5" -> y="620.5")
    svg_content = re.sub(
        r'y="542\.5"',
        'y="620.5"',
        svg_content
    )
    
    # 7. Ajustar posições específicas para templates com múltiplos números
    # Mover tabelas para baixo para dar mais espaço
    svg_content = re.sub(
        r'y="305\.5"',
        'y="350.9"',
        svg_content
    )
    
    svg_content = re.sub(
        r'y="308\.5"',
        'y="353.9"',
        svg_content
    )
    
    # Ajustar posições das linhas da tabela
    svg_content = re.sub(
        r'y="320\.5"',
        'y="365.9"',
        svg_content
    )
    
    svg_content = re.sub(
        r'y="324\.0"',
        'y="373.4"',
        svg_content
    )
    
    svg_content = re.sub(
        r'y="340\.0"',
        'y="385.9"',
        svg_content
    )
    
    svg_content = re.sub(
        r'y="343\.5"',
        'y="393.4"',
        svg_content
    )
    
    svg_content = re.sub(
        r'y="359\.5"',
        'y="405.9"',
        svg_content
    )
    
    svg_content = re.sub(
        r'y="363\.0"',
        'y="413.4"',
        svg_content
    )
    
    svg_content = re.sub(
        r'y="379\.0"',
        'y="425.9"',
        svg_content
    )
    
    svg_content = re.sub(
        r'y="382\.5"',
        'y="433.4"',
        svg_content
    )
    
    # 8. Ajustar posições do texto de contato
    svg_content = re.sub(
        r'y="440\.6"',
        'y="479.1"',
        svg_content
    )
    
    svg_content = re.sub(
        r'y="452\.6"',
        'y="491.1"',
        svg_content
    )
    
    print(f"✅ Margens aplicadas para {template_name}")
    return svg_content

def processar_templates_4_6():
    """
    Processa os templates 4, 5 e 6
    """
    
    templates = ["carta_4_numeros.svg", "carta_5_numeros.svg", "carta_6_numeros.svg"]
    
    print("🔄 Aplicando margens nos templates 4, 5 e 6...")
    
    for template_name in templates:
        template_path = f"templates/{template_name}"
        
        if not os.path.exists(template_path):
            print(f"❌ Template {template_name} não encontrado")
            continue
        
        try:
            # Ler template original
            with open(template_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Aplicar margens
            svg_modificado = aplicar_margens_template_4_6(svg_content, template_name)
            
            # Salvar template modificado
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(svg_modificado)
            
            print(f"✅ {template_name} processado com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao processar {template_name}: {e}")
    
    print("\n🎯 Templates 4, 5 e 6 foram atualizados!")
    print("📝 Agora todos os templates têm as mesmas margens")

if __name__ == "__main__":
    print("🔄 Script para Aplicar Margens nos Templates 4, 5 e 6")
    print("=" * 60)
    
    processar_templates_4_6() 