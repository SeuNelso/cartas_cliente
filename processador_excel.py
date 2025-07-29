import pandas as pd
import re
from typing import List, Dict, Tuple
import os

class ProcessadorExcel:
    def __init__(self):
        self.max_numeros_por_carta = 6
        
    def processar_excel(self, caminho_arquivo: str) -> List[Dict]:
        """
        Processa arquivo Excel e retorna lista de cartas a serem geradas
        """
        try:
            # Ler arquivo Excel
            df = pd.read_excel(caminho_arquivo)
            
            # Verificar se tem as colunas necessárias
            colunas_necessarias = ['Cliente', 'Número', 'ICCID']
            for coluna in colunas_necessarias:
                if coluna not in df.columns:
                    raise ValueError(f"Coluna '{coluna}' não encontrada no Excel")
            
            # Agrupar por cliente
            cartas_geradas = []
            
            for cliente in df['Cliente'].unique():
                dados_cliente = df[df['Cliente'] == cliente]
                
                # Dividir em grupos de 6 números
                numeros_cliente = []
                for _, linha in dados_cliente.iterrows():
                    numeros_cliente.append({
                        'numero': str(linha['Número']),
                        'iccid': str(linha['ICCID'])
                    })
                
                # Dividir em cartas de 6 números
                grupos = self._dividir_em_grupos(numeros_cliente, self.max_numeros_por_carta)
                
                for i, grupo in enumerate(grupos):
                    carta = {
                        'cliente': cliente,
                        'numeros': grupo,
                        'numero_carta': i + 1,
                        'total_cartas': len(grupos)
                    }
                    cartas_geradas.append(carta)
            
            return cartas_geradas
            
        except Exception as e:
            raise Exception(f"Erro ao processar Excel: {str(e)}")
    
    def _dividir_em_grupos(self, lista: List, tamanho_grupo: int) -> List[List]:
        """
        Divide uma lista em grupos de tamanho especificado
        """
        grupos = []
        for i in range(0, len(lista), tamanho_grupo):
            grupos.append(lista[i:i + tamanho_grupo])
        return grupos
    
    def gerar_svg_carta(self, dados_carta: Dict, template_path: str) -> str:
        """
        Gera SVG da carta substituindo placeholders
        """
        try:
            # Ler template SVG
            with open(template_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Preencher dados
            svg_modificado = svg_content
            
            # Preencher números e ICCIDs
            for i, numero_data in enumerate(dados_carta['numeros'], 1):
                svg_modificado = svg_modificado.replace(
                    f'{{{{NUMERO_{i}}}}}', numero_data['numero']
                )
                svg_modificado = svg_modificado.replace(
                    f'{{{{ICCID_{i}}}}}', numero_data['iccid']
                )
            
            # Remover linhas vazias (placeholders não preenchidos)
            svg_modificado = self._remover_linhas_vazias(svg_modificado)
            
            return svg_modificado
            
        except Exception as e:
            raise Exception(f"Erro ao gerar SVG: {str(e)}")
    
    def _remover_linhas_vazias(self, svg_content: str) -> str:
        """
        Remove linhas que contêm placeholders vazios
        """
        # Padrão para encontrar elementos text com placeholders
        padrao_numero = r'<text[^>]*>\s*<tspan[^>]*>\s*\{\{NUMERO_\d+\}\}\s*</tspan>\s*</text>'
        padrao_iccid = r'<text[^>]*>\s*<tspan[^>]*>\s*\{\{ICCID_\d+\}\}\s*</tspan>\s*</text>'
        
        # Remover elementos com placeholders não preenchidos
        svg_content = re.sub(padrao_numero, '', svg_content)
        svg_content = re.sub(padrao_iccid, '', svg_content)
        
        return svg_content
    
    def salvar_cartas(self, cartas_geradas: List[Dict], pasta_destino: str = "cartas_geradas"):
        """
        Salva todas as cartas geradas como arquivos SVG
        """
        try:
            # Criar pasta se não existir
            os.makedirs(pasta_destino, exist_ok=True)
            
            template_path = "templates_word/carta-digi-6linhas.svg"
            
            for carta in cartas_geradas:
                # Gerar SVG
                svg_content = self.gerar_svg_carta(carta, template_path)
                
                # Nome do arquivo
                nome_arquivo = f"{carta['cliente']}_carta_{carta['numero_carta']}.svg"
                nome_arquivo = self._sanitizar_nome_arquivo(nome_arquivo)
                
                # Salvar arquivo
                caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)
                with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                print(f"Carta salva: {caminho_arquivo}")
            
            return len(cartas_geradas)
            
        except Exception as e:
            raise Exception(f"Erro ao salvar cartas: {str(e)}")
    
    def _sanitizar_nome_arquivo(self, nome: str) -> str:
        """
        Remove caracteres inválidos do nome do arquivo
        """
        # Caracteres inválidos para nomes de arquivo
        caracteres_invalidos = '<>:"/\\|?*'
        for char in caracteres_invalidos:
            nome = nome.replace(char, '_')
        return nome

# Função de exemplo para uso
def processar_arquivo_excel(caminho_excel: str, pasta_destino: str = "cartas_geradas"):
    """
    Função principal para processar arquivo Excel e gerar cartas
    """
    processador = ProcessadorExcel()
    
    try:
        # Processar Excel
        print("Processando arquivo Excel...")
        cartas = processador.processar_excel(caminho_excel)
        
        print(f"Encontrados {len(cartas)} cartas para gerar")
        
        # Salvar cartas
        print("Gerando cartas...")
        total_geradas = processador.salvar_cartas(cartas, pasta_destino)
        
        print(f"✅ Processamento concluído! {total_geradas} cartas geradas.")
        
        return cartas
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None

if __name__ == "__main__":
    # Exemplo de uso
    processar_arquivo_excel("dados_clientes.xlsx") 