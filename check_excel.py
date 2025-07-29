import pandas as pd
import os

files = [f for f in os.listdir('uploads') if f.endswith('.xlsx')]
print('Arquivos Excel:')
for f in files:
    try:
        df = pd.read_excel(f"uploads/{f}")
        print(f'{f}: {len(df)} linhas')
        if len(df) > 10:
            print(f'  Colunas: {list(df.columns)}')
            print(f'  Primeiras 3 linhas:')
            print(df.head(3))
            print()
    except Exception as e:
        print(f'{f}: Erro - {e}') 