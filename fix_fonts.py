#!/usr/bin/env python3

import os
import glob
import re

def fix_templates():
    """Corrige todas as fontes nos templates SVG"""
    
    # Encontrar todos os templates SVG
    templates = glob.glob("templates/carta_*.svg")
    
    print(f"🔍 Encontrados {len(templates)} templates para corrigir")
    
    for template_path in templates:
        print(f"📝 Corrigindo: {template_path}")
        
        # Ler template
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Substituir TODAS as variações de fontes
        replacements = [
            # ArialMT -> DejaVu Sans
            ('font-family: ArialMT, Arial', 'font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif'),
            ('font-family: Arial-BoldMT, Arial', 'font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif'),
            ('font-family: ArialMT, Arial;', 'font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif;'),
            ('font-family: Arial-BoldMT, Arial;', 'font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif;'),
            
            # Substituir fontes específicas
            ('ArialMT, Arial', 'DejaVu Sans, Liberation Sans, Arial, sans-serif'),
            ('Arial-BoldMT, Arial', 'DejaVu Sans, Liberation Sans, Arial, sans-serif'),
            
            # Substituir fontes com aspas
            ('font-family:ArialMT, Arial', 'font-family:DejaVu Sans, Liberation Sans, Arial, sans-serif'),
            ('font-family:Arial-BoldMT, Arial', 'font-family:DejaVu Sans, Liberation Sans, Arial, sans-serif'),
            
            # Substituir fontes com aspas e ponto e vírgula
            ('font-family:ArialMT, Arial;', 'font-family:DejaVu Sans, Liberation Sans, Arial, sans-serif;'),
            ('font-family:Arial-BoldMT, Arial;', 'font-family:DejaVu Sans, Liberation Sans, Arial, sans-serif;'),
        ]
        
        # Aplicar todas as substituições
        for old, new in replacements:
            content = content.replace(old, new)
        
        # Salvar template corrigido
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Corrigido: {template_path}")
    
    print(f"\n🎉 Todos os {len(templates)} templates foram corrigidos!")

if __name__ == '__main__':
    fix_templates() 