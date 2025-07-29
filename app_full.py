from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import os
import uuid
import threading
import re
from werkzeug.utils import secure_filename
from cairosvg import svg2pdf
from PyPDF2 import PdfMerger
import tempfile

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_WORKERS'] = int(os.environ.get('MAX_WORKERS', 3))
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB

# Pastas
UPLOAD_FOLDER = 'uploads'
TEMPLATE_FOLDER = 'templates_word'
TEMP_FOLDER = 'temp'

for folder in [UPLOAD_FOLDER, TEMPLATE_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Jobs em andamento
jobs = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return "OK"

@app.route('/ping')
def ping():
    return "pong"

@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Apenas arquivos Excel são permitidos'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Ler dados do Excel
        df = pd.read_excel(filepath)
        columns = df.columns.tolist()
        
        return jsonify({
            'message': 'Arquivo Excel carregado com sucesso',
            'filename': filename,
            'columns': columns,
            'rows': len(df)
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

@app.route('/api/upload-template', methods=['POST'])
def upload_template():
    try:
        if 'template' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['template']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.endswith('.svg'):
            return jsonify({'error': 'Apenas arquivos SVG são permitidos'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(TEMPLATE_FOLDER, filename)
        file.save(filepath)
        
        return jsonify({
            'message': 'Template SVG carregado com sucesso',
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao processar template: {str(e)}'}), 500

@app.route('/api/generate-pdfs', methods=['POST'])
def generate_pdfs():
    try:
        data = request.get_json()
        excel_file = data.get('excel_file')
        template_file = data.get('template_file')
        selected_columns = data.get('selected_columns', [])
        
        if not excel_file or not template_file:
            return jsonify({'error': 'Arquivo Excel e template são obrigatórios'}), 400
        
        # Gerar ID único para o job
        job_id = str(uuid.uuid4())
        
        # Iniciar job em background
        thread = threading.Thread(
            target=process_pdf_generation,
            args=(job_id, excel_file, template_file, selected_columns)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Geração de PDFs iniciada',
            'job_id': job_id
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao iniciar geração: {str(e)}'}), 500

def process_pdf_generation(job_id, excel_file, template_file, selected_columns):
    try:
        jobs[job_id] = {'status': 'processing', 'progress': 0, 'message': 'Iniciando processamento...'}
        
        # Ler dados do Excel
        excel_path = os.path.join(UPLOAD_FOLDER, excel_file)
        df = pd.read_excel(excel_path)
        
        # Ler template SVG
        template_path = os.path.join(TEMPLATE_FOLDER, template_file)
        with open(template_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = f'Processando {len(df)} registros...'
        
        # Lista para armazenar PDFs gerados
        pdf_files = []
        
        for index, row in df.iterrows():
            try:
                # Substituir placeholders no SVG
                current_svg = svg_content
                for column in selected_columns:
                    placeholder = f'{{{{{column}}}}}'
                    value = str(row[column]) if pd.notna(row[column]) else ''
                    current_svg = current_svg.replace(placeholder, value)
                
                # Gerar PDF temporário
                temp_svg = os.path.join(TEMP_FOLDER, f'temp_{index}.svg')
                temp_pdf = os.path.join(TEMP_FOLDER, f'temp_{index}.pdf')
                
                with open(temp_svg, 'w', encoding='utf-8') as f:
                    f.write(current_svg)
                
                # Converter SVG para PDF
                svg2pdf(url=temp_svg, write_to=temp_pdf)
                pdf_files.append(temp_pdf)
                
                # Atualizar progresso
                progress = 10 + int((index + 1) / len(df) * 80)
                jobs[job_id]['progress'] = progress
                jobs[job_id]['message'] = f'Processado {index + 1} de {len(df)} registros'
                
            except Exception as e:
                print(f"Erro ao processar linha {index}: {e}")
                continue
        
        # Mesclar PDFs
        jobs[job_id]['message'] = 'Mesclando PDFs...'
        merger = PdfMerger()
        
        for pdf_file in pdf_files:
            merger.append(pdf_file)
        
        # Salvar PDF final
        output_path = os.path.join(TEMP_FOLDER, f'output_{job_id}.pdf')
        merger.write(output_path)
        merger.close()
        
        # Limpar arquivos temporários
        for pdf_file in pdf_files:
            try:
                os.remove(pdf_file)
            except:
                pass
        
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['message'] = 'PDFs gerados com sucesso!'
        jobs[job_id]['download_url'] = f'/api/download/{job_id}'
        
    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = f'Erro: {str(e)}'

@app.route('/api/job-status/<job_id>')
def job_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job não encontrado'}), 404
    
    return jsonify(jobs[job_id])

@app.route('/api/download/<job_id>')
def download_pdf(job_id):
    if job_id not in jobs or jobs[job_id]['status'] != 'completed':
        return jsonify({'error': 'PDF não disponível'}), 404
    
    pdf_path = os.path.join(TEMP_FOLDER, f'output_{job_id}.pdf')
    if not os.path.exists(pdf_path):
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
    return send_file(pdf_path, as_attachment=True, download_name='cartas_geradas.pdf')

@app.route('/api/templates')
def get_templates():
    try:
        templates = []
        for filename in os.listdir(TEMPLATE_FOLDER):
            if filename.endswith('.svg'):
                templates.append(filename)
        return jsonify({'templates': templates})
    except Exception as e:
        return jsonify({'error': f'Erro ao listar templates: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 