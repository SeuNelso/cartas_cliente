#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def centralizar_tabela_template_5():
    """
    Centraliza a tabela no template 5
    """
    # Template 5: fim texto principal y="285.9", início texto contato y="494.1"
    # Espaço: 494.1 - 285.9 = 208.2px
    # Centralização: 285.9 + (208.2/2) = 285.9 + 104.1 = 390.0px
    
    with open("templates/carta_5_numeros.svg", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Ajustar posições da tabela
    content = re.sub(r'y="350\.9"', 'y="390.0"', content)
    content = re.sub(r'y="353\.9"', 'y="393.0"', content)
    content = re.sub(r'y="365\.9"', 'y="405.0"', content)
    content = re.sub(r'y="373\.4"', 'y="412.5"', content)
    content = re.sub(r'y="385\.9"', 'y="424.5"', content)
    content = re.sub(r'y="393\.4"', 'y="432.0"', content)
    content = re.sub(r'y="405\.9"', 'y="444.0"', content)
    content = re.sub(r'y="413\.4"', 'y="451.5"', content)
    content = re.sub(r'y="425\.9"', 'y="463.5"', content)
    content = re.sub(r'y="433\.4"', 'y="471.0"', content)
    content = re.sub(r'y="445\.9"', 'y="483.0"', content)
    content = re.sub(r'y="453\.4"', 'y="490.5"', content)
    
    with open("templates/carta_5_numeros.svg", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Template 5 centralizado")

def centralizar_tabela_template_6():
    """
    Centraliza a tabela no template 6
    """
    # Template 6: fim texto principal y="285.9", início texto contato y="509.1"
    # Espaço: 509.1 - 285.9 = 223.2px
    # Centralização: 285.9 + (223.2/2) = 285.9 + 111.6 = 397.5px
    
    with open("templates/carta_6_numeros.svg", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Ajustar posições da tabela
    content = re.sub(r'y="350\.9"', 'y="397.5"', content)
    content = re.sub(r'y="353\.9"', 'y="400.5"', content)
    content = re.sub(r'y="365\.9"', 'y="412.5"', content)
    content = re.sub(r'y="373\.4"', 'y="420.0"', content)
    content = re.sub(r'y="385\.9"', 'y="432.0"', content)
    content = re.sub(r'y="393\.4"', 'y="439.5"', content)
    content = re.sub(r'y="405\.9"', 'y="451.5"', content)
    content = re.sub(r'y="413\.4"', 'y="459.0"', content)
    content = re.sub(r'y="425\.9"', 'y="471.0"', content)
    content = re.sub(r'y="433\.4"', 'y="478.5"', content)
    content = re.sub(r'y="445\.9"', 'y="490.5"', content)
    content = re.sub(r'y="453\.4"', 'y="498.0"', content)
    content = re.sub(r'y="465\.9"', 'y="510.0"', content)
    content = re.sub(r'y="473\.4"', 'y="517.5"', content)
    
    with open("templates/carta_6_numeros.svg", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Template 6 centralizado")

if __name__ == "__main__":
    print("🔄 Centralizando tabelas nos templates 5 e 6...")
    centralizar_tabela_template_5()
    centralizar_tabela_template_6()
    print("🎯 Todas as tabelas foram centralizadas!") 