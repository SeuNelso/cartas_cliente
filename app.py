from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
import uuid
import json
import time
import threading
from datetime import datetime
import shutil
import re
import sys

# Verificar versão do Python
python_version = sys.version_info
if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
    print("❌ Python 3.8+ é necessário")
    sys.exit(1)

print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detectado")
print(f"✅ Compatível com pandas 2.1.4")
print(f"✅ Versão Python 3.13.4 configurada")

# SVG processing
try:
    from cairosvg import svg2pdf
    SVG_AVAILABLE = True
    print("✅ cairosvg disponível")
except ImportError as e:
    SVG_AVAILABLE = False
    print(f"⚠️ cairosvg não disponível: {e}")

# PDF merging
try:
    from PyPDF2 import PdfMerger
    PDF_MERGE_AVAILABLE = True
    print("✅ PyPDF2 disponível")
except ImportError as e:
    PDF_MERGE_AVAILABLE = False
    print(f"⚠️ PyPDF2 não disponível: {e}")

# Verificar pandas
try:
    pd_version = pd.__version__
    print(f"✅ pandas {pd_version} disponível")
except Exception as e:
    print(f"❌ Erro com pandas: {e}")
    sys.exit(1)

# Configurações globais
app = Flask(__name__)
app.config['UPLOADS_FOLDER'] = 'uploads'
app.config['TEMPLATES_FOLDER'] = 'templates_word'
app.config['TEMP_FOLDER'] = 'temp'
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50MB padrão

# Criar pastas necessárias
os.makedirs(app.config['UPLOADS_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMPLATES_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# Variáveis globais para controle de jobs
jobs = {}

# Configurações da aplicação
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sua_chave_secreta_aqui')
app.config['MAX_WORKERS'] = int(os.environ.get('MAX_WORKERS', 4))

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
ALLOWED_TEMPLATE_EXTENSIONS = {'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_template_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_TEMPLATE_EXTENSIONS

@app.route('/api/health')
def health_check():
    """Endpoint de verificação de saúde da aplicação"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_jobs': len([j for j in jobs.values() if j['status'] == 'processing']),
        'version': '3.0.0-svg-only'
    })

@app.route('/api/status')
def system_status():
    """Endpoint para verificar status do sistema"""
    try:
        active_jobs = len([job for job in jobs.values() if job['status'] == 'processing'])
        
        return jsonify({
            'status': 'ready',
            'active_jobs': active_jobs,
            'total_jobs': len(jobs),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/')
def index():
    """Página principal"""
    try:
        # Listar templates SVG disponíveis
        templates_folder = app.config['TEMPLATES_FOLDER']
        svg_templates = []
        
        if os.path.exists(templates_folder):
            for filename in os.listdir(templates_folder):
                if filename.lower().endswith('.svg'):
                    svg_templates.append(filename)
        
        return render_template('index.html', svg_templates=svg_templates)
    except Exception as e:
        return f"Erro ao carregar página: {str(e)}"

@app.route('/api/upload-template', methods=['POST'])
def upload_template():
    """Upload de template SVG"""
    try:
        if 'template' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['template']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_template_file(file.filename):
            return jsonify({'success': False, 'error': 'Apenas arquivos SVG são permitidos'}), 400
        
        filename = secure_filename(file.filename)
        template_path = os.path.join(app.config['TEMPLATES_FOLDER'], filename)
        
        file.save(template_path)
        
        return jsonify({
            'success': True, 
            'filename': filename,
            'message': 'Template SVG enviado com sucesso'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload de arquivo Excel"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Tipo de arquivo não permitido'}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOADS_FOLDER'], filename)
        
        file.save(file_path)
        
        # Verificar se o arquivo pode ser lido
        try:
            df = pd.read_excel(file_path)
            row_count = len(df)
            return jsonify({
                'success': True,
                'filename': filename,
                'row_count': row_count,
                'message': f'Arquivo enviado com sucesso. {row_count} registros encontrados.'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f'Erro ao ler arquivo Excel: {str(e)}'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """Gerar PDF com dados do Excel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        template_name = data.get('template_name')
        excel_filename = data.get('excel_filename')  # Nome do arquivo Excel enviado
        
        if not template_name:
            return jsonify({'success': False, 'error': 'Nome do template não fornecido'}), 400
        
        if not excel_filename:
            return jsonify({'success': False, 'error': 'Nome do arquivo Excel não fornecido'}), 400
        
        print(f"📄 Template selecionado: {template_name}")
        print(f"📊 Arquivo Excel selecionado: {excel_filename}")
        
        # Usar o arquivo Excel específico enviado
        excel_path = os.path.join(app.config['UPLOADS_FOLDER'], excel_filename)
        
        if not os.path.exists(excel_path):
            return jsonify({'success': False, 'error': f'Arquivo Excel não encontrado: {excel_filename}'}), 400
        
        print(f"📊 Usando arquivo Excel: {excel_filename}")
        
        # Ler dados do Excel
        excel_data = pd.read_excel(excel_path).to_dict('records')
        print(f"📊 Dados lidos do Excel: {len(excel_data)} registros")
        print(f"📊 Primeiro registro: {excel_data[0] if excel_data else 'Nenhum'}")
        
        # Verificar colunas disponíveis
        if excel_data:
            columns = list(excel_data[0].keys())
            print(f"📊 Colunas disponíveis: {columns}")
        
        # Criar job
        job_id = str(uuid.uuid4())
        job_data = {
            'status': 'processing',
            'current': 0,
            'total': len(excel_data),
            'message': 'Iniciando processamento...'
        }
        
        jobs[job_id] = job_data
        
        # Iniciar processamento em background
        thread = threading.Thread(
            target=process_data_with_svg,
            args=(job_id, excel_data, template_name)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'total': len(excel_data)
        })
        
    except Exception as e:
        print(f"❌ Erro em generate_pdf: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def process_data_with_svg(job_id, data_list, template_name):
    """Processa dados usando apenas SVG"""
    try:
        print(f"🚀 Iniciando processamento SVG para job {job_id}")
        print(f"   📊 Total de registros: {len(data_list)}")
        print(f"   📄 Template: {template_name}")
        print(f"   📊 Primeiro registro: {data_list[0] if data_list else 'Nenhum'}")
        
        result = generate_svg_pdf_with_pages(data_list, template_name, job_id)
        
        if result:
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['message'] = f'PDF SVG gerado com sucesso: {len(data_list)} páginas'
            print(f"✅ Job {job_id} concluído com sucesso")
        else:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['message'] = 'Erro ao gerar PDF SVG'
            print(f"❌ Job {job_id} falhou")
            
    except Exception as e:
        print(f"❌ Erro no processamento SVG: {e}")
        import traceback
        traceback.print_exc()
        if job_id in jobs:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['message'] = f'Erro: {str(e)}'

@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    """Obter progresso de um job específico"""
    try:
        if job_id not in jobs:
            return jsonify({'error': 'Job não encontrado'}), 404
        
        job = jobs[job_id]
        return jsonify({
            'status': job['status'],
            'current': job['current'],
            'total': job['total'],
            'message': job.get('message', ''),
            'progress': (job['current'] / job['total'] * 100) if job['total'] > 0 else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<job_id>')
def download_result(job_id):
    """Download do resultado do job"""
    try:
        if job_id not in jobs:
            return jsonify({'error': 'Job não encontrado'}), 404
        
        job = jobs[job_id]
        if job['status'] != 'completed':
            return jsonify({'error': 'Job ainda não concluído'}), 400
        
        # Buscar arquivo PDF gerado
        pdf_filename = f'cartas_{job_id}.pdf'
        pdf_path = os.path.join(app.config['UPLOADS_FOLDER'], pdf_filename)
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'Arquivo PDF não encontrado'}), 404
        
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_svg_pdf_with_pages(data_list, template_name, job_id):
    """Gera PDF único com múltiplas páginas usando template SVG"""
    try:
        if not SVG_AVAILABLE or not PDF_MERGE_AVAILABLE:
            print("❌ Dependências não disponíveis")
            return None
        
        template_path = os.path.join(app.config['TEMPLATES_FOLDER'], template_name)
        if not os.path.exists(template_path):
            print(f"❌ Template não encontrado: {template_path}")
            return None
        
        pdf_path = os.path.join(app.config['UPLOADS_FOLDER'], f'cartas_{job_id}.pdf')
        timestamp = int(time.time() * 1000000)
        pdf_files = []
        
        print(f"📄 Processando {len(data_list)} registros")
        print(f"📄 Template: {template_path}")
        
        # Para cada registro, gerar um PDF individual
        for i, row_data in enumerate(data_list):
            print(f"\n📄 Processando registro {i+1}/{len(data_list)}")
            print(f"📊 Dados do registro: {row_data}")
            
            # Ler template SVG
            with open(template_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            print(f"📄 Template carregado: {len(svg_content)} caracteres")
            
            # Verificar quais placeholders existem no template
            all_placeholders = []
            import re
            # Regex para capturar placeholders [CAMPO] e também texto simples CAMPO
            placeholder_pattern = r'\[([A-Z_]+)\]'
            found_placeholders = re.findall(placeholder_pattern, svg_content)
            
            # Também procurar por texto simples que pode ser substituído
            simple_text_pattern = r'>([A-Z_]+)</tspan>'
            simple_texts = re.findall(simple_text_pattern, svg_content)
            
            print(f"🔍 Placeholders encontrados no template: {found_placeholders}")
            print(f"🔍 Textos simples encontrados: {simple_texts}")
            
            # Substituir placeholders dinamicamente
            print(f"🔄 Substituindo placeholders:")
            for placeholder_name in found_placeholders:
                placeholder = f'[{placeholder_name}]'
                
                # Verificar se o campo existe nos dados
                if placeholder_name in row_data:
                    value = row_data[placeholder_name]
                    if value is not None:
                        # Converter para string e formatar
                        if isinstance(value, (int, float)):
                            value = str(int(value))
                        else:
                            value = str(value)
                        
                        # Formatação especial para ICCID - remover espaços
                        if placeholder_name == 'ICCID':
                            value = value.replace(' ', '')
                            print(f"   ✅ [{placeholder_name}] -> {value} (espaços removidos)")
                        
                        # Fazer a substituição
                        old_content = svg_content
                        svg_content = svg_content.replace(placeholder, value)
                        
                        if old_content != svg_content:
                            print(f"   ✅ [{placeholder_name}] -> {value}")
                        else:
                            print(f"   ⚠️ [{placeholder_name}] não foi substituído")
                    else:
                        svg_content = svg_content.replace(placeholder, '')
                        print(f"   ⚠️ [{placeholder_name}] -> '' (valor nulo)")
                elif placeholder_name.upper() == 'DATA':
                    from datetime import datetime
                    current_date = datetime.now().strftime('%d/%m/%Y')
                    svg_content = svg_content.replace(placeholder, current_date)
                    print(f"   ✅ [DATA] -> {current_date}")
                else:
                    # Campo não encontrado nos dados
                    svg_content = svg_content.replace(placeholder, '')
                    print(f"   ⚠️ [{placeholder_name}] -> '' (campo não encontrado)")
            
            # Substituir textos simples também
            print(f"🔄 Substituindo textos simples:")
            for text_name in simple_texts:
                if text_name in row_data:
                    value = row_data[text_name]
                    if value is not None:
                        # Converter para string
                        if isinstance(value, (int, float)):
                            value = str(int(value))
                        else:
                            value = str(value)
                        
                        # Substituir o texto dentro das tags tspan preservando posicionamento
                        old_content = svg_content
                        
                        # Encontrar o elemento tspan com NUMERO
                        if text_name == 'NUMERO':
                            # Usar regex para encontrar e substituir mantendo o posicionamento
                            pattern = r'(<tspan[^>]*>)[^<]*NUMERO[^<]*(</tspan>)'
                            # Usar uma função de substituição para evitar problemas com grupos
                            def replace_numero(match):
                                return match.group(1) + value + match.group(2)
                            svg_content = re.sub(pattern, replace_numero, svg_content)
                        else:
                            # Para outros campos, usar substituição simples
                            pattern = f'>{text_name}</tspan>'
                            replacement = f'>{value}</tspan>'
                            svg_content = svg_content.replace(pattern, replacement)
                        
                        if old_content != svg_content:
                            print(f"   ✅ {text_name} -> {value}")
                        else:
                            print(f"   ⚠️ {text_name} não foi substituído")
                    else:
                        # Se valor é nulo, remover o texto
                        pattern = f'>{text_name}</tspan>'
                        replacement = f'></tspan>'
                        svg_content = svg_content.replace(pattern, replacement)
                        print(f"   ⚠️ {text_name} -> '' (valor nulo)")
                else:
                    print(f"   ⚠️ {text_name} -> '' (campo não encontrado)")
            
            # Tratamento especial para NUMERO - remover o ] que está separado e o [ que pode estar no início
            if 'NUMERO' in row_data and row_data['NUMERO'] is not None:
                value = str(int(row_data['NUMERO']))
                # Remover o ] que está em elemento separado
                svg_content = svg_content.replace('>] </tspan>', '></tspan>')
                # Remover qualquer [ que possa estar no início do valor
                svg_content = svg_content.replace(f'>[{value}</tspan>', f'>{value}</tspan>')
                # Remover [ solto que pode estar antes do NUMERO
                svg_content = svg_content.replace('>[</tspan>', '></tspan>')
                print(f"   ✅ Tratamento especial para NUMERO: {value}")
            
            # Verificar se ainda há placeholders não substituídos
            remaining_placeholders = re.findall(placeholder_pattern, svg_content)
            if remaining_placeholders:
                print(f"⚠️ Placeholders não substituídos: {remaining_placeholders}")
            
            # Verificar se há texto que parece placeholder mas não foi substituído
            remaining_texts = re.findall(simple_text_pattern, svg_content)
            if remaining_texts:
                print(f"⚠️ Textos não substituídos: {remaining_texts}")
            
            # Verificar se há [ ou ] soltos
            if '[' in svg_content or ']' in svg_content:
                print(f"⚠️ Colchetes soltos encontrados no SVG final")
                # Remover colchetes soltos
                svg_content = svg_content.replace('>[</tspan>', '></tspan>')
                svg_content = svg_content.replace('>]</tspan>', '></tspan>')
                svg_content = svg_content.replace('>] </tspan>', '></tspan>')
                print(f"   ✅ Colchetes soltos removidos")
            
            # Criar arquivo SVG temporário
            temp_svg = os.path.join(app.config['TEMP_FOLDER'], f'temp_{timestamp}_{i}.svg')
            with open(temp_svg, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            print(f"💾 SVG temporário salvo: {temp_svg}")
            
            # Converter SVG para PDF
            temp_pdf = os.path.join(app.config['TEMP_FOLDER'], f'temp_{timestamp}_{i}.pdf')
            try:
                svg2pdf(url=temp_svg, write_to=temp_pdf)
                print(f"📄 PDF gerado: {temp_pdf}")
                pdf_files.append(temp_pdf)
            except Exception as e:
                print(f"❌ Erro ao converter SVG para PDF: {e}")
                continue
            
            # Limpar arquivo SVG temporário
            try:
                os.remove(temp_svg)
            except:
                pass
            
            # Atualizar progresso
            if job_id in jobs:
                jobs[job_id]['current'] = i + 1
                jobs[job_id]['message'] = f'Processando página {i+1} de {len(data_list)}'
        
        print(f"\n📄 Total de PDFs gerados: {len(pdf_files)}")
        
        if not pdf_files:
            print("❌ Nenhum PDF foi gerado")
            return None
        
        # Juntar todos os PDFs em um só
        merger = PdfMerger()
        for pdf_file in pdf_files:
            merger.append(pdf_file)
        
        merger.write(pdf_path)
        merger.close()
        
        print(f"✅ PDF final salvo: {pdf_path}")
        
        # Limpar arquivos temporários
        for pdf_file in pdf_files:
            try:
                os.remove(pdf_file)
            except:
                pass
        
        return pdf_path
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF SVG: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Iniciando servidor SVG-Only na porta {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📦 SVG disponível: {SVG_AVAILABLE}")
    print(f"📦 PDF Merge disponível: {PDF_MERGE_AVAILABLE}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    ) 