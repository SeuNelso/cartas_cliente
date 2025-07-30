#!/usr/bin/env python3

import os
import subprocess

def test_fonts():
    """Testa se as fontes estão instaladas corretamente"""
    
    print("🔍 Verificando fontes instaladas...")
    
    try:
        # Verificar se fc-list está disponível
        result = subprocess.run(['fc-list'], capture_output=True, text=True)
        if result.returncode == 0:
            fonts = result.stdout
            print("✅ fc-list funcionando")
            
            # Verificar fontes específicas
            arial_found = 'Arial' in fonts
            dejavu_found = 'DejaVu' in fonts
            liberation_found = 'Liberation' in fonts
            
            print(f"📋 Fontes encontradas:")
            print(f"  Arial: {'✅' if arial_found else '❌'}")
            print(f"  DejaVu: {'✅' if dejavu_found else '❌'}")
            print(f"  Liberation: {'✅' if liberation_found else '❌'}")
            
            if arial_found:
                print("🎉 Arial encontrada! PDFs devem renderizar corretamente.")
            else:
                print("⚠️  Arial não encontrada. Usando fallback fonts.")
                
        else:
            print("❌ fc-list não funcionando")
            
    except FileNotFoundError:
        print("❌ fontconfig não instalado")
    except Exception as e:
        print(f"❌ Erro ao verificar fontes: {e}")

def test_svg_conversion():
    """Testa a conversão SVG para PDF"""
    
    print("\n🔄 Testando conversão SVG para PDF...")
    
    try:
        from cairosvg import svg2pdf
        
        # Criar SVG de teste simples
        test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">
  <rect width="400" height="200" fill="white"/>
  <text x="50" y="50" font-family="Arial, DejaVu Sans, sans-serif" font-size="16" fill="black">
    Teste de fonte Arial
  </text>
  <text x="50" y="80" font-family="Arial, DejaVu Sans, sans-serif" font-size="16" font-weight="bold" fill="black">
    Teste de fonte Arial Bold
  </text>
  <text x="50" y="110" font-family="DejaVu Sans, sans-serif" font-size="16" fill="black">
    Teste de fonte DejaVu Sans
  </text>
</svg>'''
        
        # Salvar SVG de teste
        with open('test_font.svg', 'w', encoding='utf-8') as f:
            f.write(test_svg)
        
        # Converter para PDF
        svg2pdf(url='test_font.svg', write_to='test_font.pdf')
        
        print("✅ Conversão SVG para PDF bem-sucedida!")
        print("📄 PDF gerado: test_font.pdf")
        
        # Limpar arquivos de teste
        os.remove('test_font.svg')
        os.remove('test_font.pdf')
        
    except Exception as e:
        print(f"❌ Erro na conversão: {e}")

if __name__ == '__main__':
    test_fonts()
    test_svg_conversion() 