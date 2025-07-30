#!/usr/bin/env python3

import os
import re

def test_placeholder_replacement():
    """Testa a substituição de placeholders"""
    
    # Simular dados de teste
    cliente_nome = "João Silva"
    grupo = [
        {'numero': '968200392', 'iccid': '8935102241115530665'},
        {'numero': '966640970', 'iccid': '8935102241115530657'},
        {'numero': '962355566', 'iccid': '8935102241115530632'}
    ]
    
    # Ler template
    template_path = "templates/carta_3_numeros.svg"
    with open(template_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    print(f"Template: {template_path}")
    print(f"Cliente: {cliente_nome}")
    print(f"Números: {len(grupo)}")
    
    # Contar placeholders originais
    num_placeholders = svg_content.count('[NUMERO]')
    iccid_placeholders = svg_content.count('[ICCID]')
    cliente_placeholders = svg_content.count('[CLIENTE]')
    
    print(f"Placeholders originais:")
    print(f"  [NUMERO]: {num_placeholders}")
    print(f"  [ICCID]: {iccid_placeholders}")
    print(f"  [CLIENTE]: {cliente_placeholders}")
    
    # Substituir cliente
    svg_modificado = svg_content
    svg_modificado = svg_modificado.replace('[CLIENTE]', cliente_nome)
    
    # Substituir números sequencialmente
    for i, item in enumerate(grupo):
        numero = item['numero']
        iccid = item['iccid']
        
        print(f"Substituindo número {i+1}: {numero}, ICCID: {iccid}")
        
        # Substituir apenas o primeiro placeholder encontrado
        svg_modificado = svg_modificado.replace('[NUMERO]', numero, 1)
        svg_modificado = svg_modificado.replace('[ICCID]', iccid, 1)
    
    # Limpar placeholders não utilizados
    svg_modificado = svg_modificado.replace('[NUMERO]', '')
    svg_modificado = svg_modificado.replace('[ICCID]', '')
    
    # Verificar placeholders restantes
    remaining_num = svg_modificado.count('[NUMERO]')
    remaining_iccid = svg_modificado.count('[ICCID]')
    remaining_cliente = svg_modificado.count('[CLIENTE]')
    
    print(f"\nPlaceholders restantes:")
    print(f"  [NUMERO]: {remaining_num}")
    print(f"  [ICCID]: {remaining_iccid}")
    print(f"  [CLIENTE]: {remaining_cliente}")
    
    # Salvar resultado
    output_path = "test_output.svg"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_modificado)
    
    print(f"\nResultado salvo em: {output_path}")
    
    # Mostrar algumas linhas do resultado
    lines = svg_modificado.split('\n')
    for i, line in enumerate(lines):
        if '[NUMERO]' in line or '[ICCID]' in line or '968200392' in line or '966640970' in line:
            print(f"Linha {i+1}: {line.strip()}")

if __name__ == '__main__':
    test_placeholder_replacement() 