#!/usr/bin/env python3
"""
Teste simples para verificar se as dependências funcionam
"""

import sys
print(f"Python version: {sys.version}")

try:
    import flask
    print(f"✅ Flask {flask.__version__} OK")
except ImportError as e:
    print(f"❌ Flask error: {e}")

try:
    import pandas
    print(f"✅ Pandas {pandas.__version__} OK")
except ImportError as e:
    print(f"❌ Pandas error: {e}")

try:
    import openpyxl
    print(f"✅ OpenPyXL OK")
except ImportError as e:
    print(f"❌ OpenPyXL error: {e}")

try:
    from cairosvg import svg2pdf
    print(f"✅ CairoSVG OK")
except ImportError as e:
    print(f"❌ CairoSVG error: {e}")

try:
    from PyPDF2 import PdfMerger
    print(f"✅ PyPDF2 OK")
except ImportError as e:
    print(f"❌ PyPDF2 error: {e}")

try:
    from werkzeug.utils import secure_filename
    print(f"✅ Werkzeug OK")
except ImportError as e:
    print(f"❌ Werkzeug error: {e}")

print("✅ Todos os testes concluídos!") 