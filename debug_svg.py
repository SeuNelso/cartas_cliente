import re
import os

# Verificar se o arquivo existe
svg_path = 'templates_word/carta-digi.svg'
if not os.path.exists(svg_path):
    print(f"❌ Arquivo não encontrado: {svg_path}")
    exit()

# Ler o template SVG
with open(svg_path, 'r', encoding='utf-8') as f:
    svg_content = f.read()

print("=== DEBUG SVG TEMPLATE ===")
print(f"Tamanho do SVG: {len(svg_content)} caracteres")

# Procurar por NUMERO
print("\n=== PROCURANDO POR NUMERO ===")
numero_matches = re.findall(r'>([^<]*NUMERO[^<]*)</tspan>', svg_content)
print(f"Matches para NUMERO: {numero_matches}")

# Procurar por [
print("\n=== PROCURANDO POR [ ===")
bracket_matches = re.findall(r'>([^<]*\[[^<]*)</tspan>', svg_content)
print(f"Matches para [: {bracket_matches}")

# Procurar por ]
print("\n=== PROCURANDO POR ] ===")
close_bracket_matches = re.findall(r'>([^<]*\][^<]*)</tspan>', svg_content)
print(f"Matches para ]: {close_bracket_matches}")

# Procurar por ICCID
print("\n=== PROCURANDO POR ICCID ===")
iccid_matches = re.findall(r'>([^<]*ICCID[^<]*)</tspan>', svg_content)
print(f"Matches para ICCID: {iccid_matches}")

# Simular substituição
print("\n=== SIMULANDO SUBSTITUIÇÃO ===")
test_data = {'NUMERO': 963000000, 'ICCID': '365412358796539904'}

# Substituir NUMERO
old_content = svg_content
svg_content = svg_content.replace('>NUMERO</tspan>', f'>{test_data["NUMERO"]}</tspan>')
print(f"NUMERO substituído: {'SIM' if old_content != svg_content else 'NÃO'}")

# Remover ]
svg_content = svg_content.replace('>] </tspan>', '></tspan>')
print("] removido")

# Substituir ICCID
old_content = svg_content
svg_content = svg_content.replace('>[ICCID]</tspan>', f'>{test_data["ICCID"]}</tspan>')
print(f"ICCID substituído: {'SIM' if old_content != svg_content else 'NÃO'}")

# Verificar resultado
print("\n=== RESULTADO FINAL ===")
numero_final = re.findall(r'>([^<]*963000000[^<]*)</tspan>', svg_content)
print(f"NUMERO final: {numero_final}")

iccid_final = re.findall(r'>([^<]*365412358796539904[^<]*)</tspan>', svg_content)
print(f"ICCID final: {iccid_final}") 