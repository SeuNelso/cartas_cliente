#!/usr/bin/env python3
import os
import re

def aplicar_margens_template(arquivo):
    """Aplica margens aumentadas em um template SVG"""
    
    print(f"🔧 Processando: {arquivo}")
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # 1. Expandir viewBox
    conteudo = re.sub(
        r'viewBox="0 0 420\.9449 595\.2755737"',
        'viewBox="0 0 500 700"',
        conteudo
    )
    
    # 2. Expandir rect
    conteudo = re.sub(
        r'<rect width="420\.9449" height="595\.2755737"',
        '<rect width="500" height="700"',
        conteudo
    )
    
    # 3. Mover textos principais para direita
    conteudo = re.sub(
        r'<text x="22\.6"',
        '<text x="42.6"',
        conteudo
    )
    
    # 4. Expandir largura das tabelas
    conteudo = re.sub(
        r'x2="351\.1"',
        'x2="450.1"',
        conteudo
    )
    
    # 5. Mover coluna ICCID para direita
    conteudo = re.sub(
        r'<text x="194\.7"',
        '<text x="250.7"',
        conteudo
    )
    
    # 6. Mover código do cliente
    conteudo = re.sub(
        r'<text x="360\.5" y="542\.5"',
        '<text x="460.5" y="620.5"',
        conteudo
    )
    
    # 7. Ajustar posições Y das tabelas (mover para baixo)
    # Cabeçalhos da tabela
    conteudo = re.sub(
        r'<text x="49\.9" y="([0-9]+\.?[0-9]*)" style="font-size: 9px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; font-weight: 700; fill: #010101;">\s*Número',
        lambda m: f'<text x="49.9" y="{float(m.group(1)) + 20}" style="font-size: 9px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; font-weight: 700; fill: #010101;">\n    Número',
        conteudo
    )
    
    # Linhas da tabela
    conteudo = re.sub(
        r'<line x1="50\.5" y1="([0-9]+\.?[0-9]*)" x2="[^"]*" y2="[^"]*"',
        lambda m: f'<line x1="50.5" y1="{float(m.group(1)) + 20}" x2="450.1" y2="{float(m.group(1)) + 20}"',
        conteudo
    )
    
    # Dados da tabela
    conteudo = re.sub(
        r'<text x="49\.9" y="([0-9]+\.?[0-9]*)" style="font-size: 8\.5px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #010101;">\s*\[NUMERO\]',
        lambda m: f'<text x="49.9" y="{float(m.group(1)) + 20}" style="font-size: 8.5px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #010101;">\n    [NUMERO]',
        conteudo
    )
    
    conteudo = re.sub(
        r'<text x="250\.7" y="([0-9]+\.?[0-9]*)" style="font-size: 8\.5px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #010101;">\s*\[ICCID\]',
        lambda m: f'<text x="250.7" y="{float(m.group(1)) + 20}" style="font-size: 8.5px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #010101;">\n    [ICCID]',
        conteudo
    )
    
    # 8. Mover texto de contato para baixo
    conteudo = re.sub(
        r'<text x="42\.6" y="([0-9]+\.?[0-9]*)" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #231f20;">\s*Em caso de dúvida',
        lambda m: f'<text x="42.6" y="{float(m.group(1)) + 20}" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #231f20;">\n    Em caso de dúvida',
        conteudo
    )
    
    # Ajustar outras linhas do texto de contato
    conteudo = re.sub(
        r'<text x="42\.6" y="([0-9]+\.?[0-9]*)" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #231f20;">\s*na rede DIGI',
        lambda m: f'<text x="42.6" y="{float(m.group(1)) + 20}" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #231f20;">\n    na rede DIGI',
        conteudo
    )
    
    conteudo = re.sub(
        r'<text x="42\.6" y="([0-9]+\.?[0-9]*)" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #231f20;">\s*Estamos aqui para te ajudar',
        lambda m: f'<text x="42.6" y="{float(m.group(1)) + 20}" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #231f20;">\n    Estamos aqui para te ajudar',
        conteudo
    )
    
    conteudo = re.sub(
        r'<text x="42\.6" y="([0-9]+\.?[0-9]*)" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #231f20;">\s*Até breve',
        lambda m: f'<text x="42.6" y="{float(m.group(1)) + 20}" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; fill: #231f20;">\n    Até breve',
        conteudo
    )
    
    conteudo = re.sub(
        r'<text x="42\.6" y="([0-9]+\.?[0-9]*)" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; font-weight: 700; fill: #231f20;">\s*A Equipa DIGI',
        lambda m: f'<text x="42.6" y="{float(m.group(1)) + 20}" style="font-size: 10px; font-family: DejaVu Sans, Liberation Sans, Arial, sans-serif; font-weight: 700; fill: #231f20;">\n    A Equipa DIGI',
        conteudo
    )
    
    # Salvar arquivo modificado
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"✅ Margens aplicadas em: {arquivo}")

def main():
    """Processa todos os templates restantes"""
    
    templates = [
        "templates/carta_3_numeros.svg",
        "templates/carta_4_numeros.svg", 
        "templates/carta_5_numeros.svg",
        "templates/carta_6_numeros.svg"
    ]
    
    print("🚀 Aplicando margens aumentadas nos templates restantes...")
    
    for template in templates:
        if os.path.exists(template):
            aplicar_margens_template(template)
        else:
            print(f"❌ Template não encontrado: {template}")
    
    print("\n🎯 Processamento concluído!")
    print("📝 Todos os templates foram atualizados com margens aumentadas")

if __name__ == "__main__":
    main() 