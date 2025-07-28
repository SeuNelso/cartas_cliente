from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import tempfile
import zipfile
from datetime import datetime
from docx import Document
import re
from docx2pdf import convert
import shutil
import uuid
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from functools import lru_cache
import sys

# Windows-specific imports (only if available)
try:
    import pythoncom
    import win32com.client
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("⚠️ Windows dependencies not available - Word conversion will use fallback methods")

# Linux-compatible Word processing
try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️ python-docx not available - using basic text conversion")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMPLATES_FOLDER'] = 'templates_word'
app.config['TEMP_FOLDER'] = 'temp'
# Configurações da aplicação
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['TIMEOUT_SECONDS'] = 0  # Sem timeout
app.config['MAX_WORKERS'] = 8  # Mais workers para Render
app.config['CHUNK_SIZE'] = 5   # Chunks maiores para Render

# Criar pastas necessárias
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMPLATES_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# Dicionário para armazenar progresso
progress_tracker = {}

# Cache para templates processados
template_cache = {}

# Dicionário para armazenar tempos de início dos jobs
job_start_times = {}

# Set para controlar jobs ativos
current_jobs = set()

# Função para limpar jobs antigos
def cleanup_old_jobs():
    """Remove jobs antigos (mais de 1 hora) para evitar vazamentos de memória"""
    current_time = time.time()
    jobs_to_remove = []
    
    for job_id, job_data in progress_tracker.items():
        if current_time - job_data.get('start_time', 0) > 3600:  # 1 hora
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        if job_id in progress_tracker:
            del progress_tracker[job_id]
        if job_id in job_start_times:
            del job_start_times[job_id]
        current_jobs.discard(job_id)
        print(f"Job antigo removido: {job_id}")

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
ALLOWED_TEMPLATE_EXTENSIONS = {'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_template_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_TEMPLATE_EXTENSIONS

# Não há template padrão - deve usar apenas template importado
DEFAULT_TEMPLATE = None

@app.route('/api/health')
def health_check():
    """Endpoint de verificação de saúde da aplicação"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_jobs': len(current_jobs),
        'workers': app.config['MAX_WORKERS'],
        'version': '1.0.0'
    })

@app.route('/api/status')
def system_status():
    """Endpoint para verificar status do sistema e se está pronto para próximo lote"""
    try:
        # Verificar se há jobs ativos
        active_jobs = len([job for job in progress_tracker.values() if job['status'] == 'processing'])
        
        # Verificar espaço em disco
        temp_folder = app.config['TEMP_FOLDER']
        disk_usage = 0
        if os.path.exists(temp_folder):
            for filename in os.listdir(temp_folder):
                file_path = os.path.join(temp_folder, filename)
                if os.path.isfile(file_path):
                    disk_usage += os.path.getsize(file_path)
        
        # Verificar se sistema está pronto
        is_ready = active_jobs == 0
        
        return jsonify({
            'status': 'ready' if is_ready else 'busy',
            'active_jobs': active_jobs,
            'total_jobs': len(progress_tracker),
            'disk_usage_mb': round(disk_usage / (1024 * 1024), 2),
            'workers': app.config['MAX_WORKERS'],
            'chunk_size': app.config['CHUNK_SIZE'],
            'ready_for_next_batch': is_ready,
            'message': 'Sistema pronto para próximo lote!' if is_ready else f'{active_jobs} job(s) em processamento'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/')
def index():
    # Listar templates disponíveis
    templates = []
    if os.path.exists(app.config['TEMPLATES_FOLDER']):
        for file in os.listdir(app.config['TEMPLATES_FOLDER']):
            if file.endswith('.docx'):
                templates.append(file)
    
    return render_template('index.html', templates=templates)

@app.route('/api/upload-template', methods=['POST'])
def upload_template():
    if 'template' not in request.files:
        return jsonify({'error': 'Nenhum arquivo de template selecionado'}), 400
    
    file = request.files['template']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if file and allowed_template_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['TEMPLATES_FOLDER'], filename)
        file.save(filepath)
        
        # Limpar cache quando novo template é adicionado
        template_cache.clear()
        
        return jsonify({
            'success': True,
            'message': f'Template "{filename}" carregado com sucesso!',
            'filename': filename
        })
    
    return jsonify({'error': 'Tipo de arquivo não permitido. Use apenas arquivos .docx'}), 400

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Ler o arquivo Excel
            df = pd.read_excel(filepath)
            
            # Converter para lista de dicionários para JSON
            data = df.to_dict('records')
            columns = df.columns.tolist()
            
            return jsonify({
                'success': True,
                'data': data,
                'columns': columns,
                'filename': filename
            })
        except Exception as e:
            return jsonify({'error': f'Erro ao ler arquivo: {str(e)}'}), 400
    
    return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        excel_data = data.get('data', [])
        template_name = data.get('template', '')
        use_word_template = data.get('useWordTemplate', False)
        
        print(f"🔍 DEBUG: Recebido request de geração")
        print(f"   Template Name: '{template_name}'")
        print(f"   Use Word Template: {use_word_template}")
        print(f"   Excel Data: {len(excel_data)} registros")
        print(f"   Request Data: {data}")
        
        if not excel_data:
            print("   ❌ Nenhum dado fornecido")
            return jsonify({'error': 'Nenhum dado fornecido'}), 400
        
        # Se apenas uma linha, gerar PDF único
        if len(excel_data) == 1:
            print(f"   📄 Gerando PDF único")
            
            # Verificar se há template Word disponível
            if use_word_template and template_name:
                template_path = os.path.join(app.config['TEMPLATES_FOLDER'], template_name)
                if os.path.exists(template_path):
                    print(f"   🎨 Usando template Word: {template_name}")
                    pdf_buffer = generate_word_pdf_ultra_optimized(excel_data[0], template_name)
                else:
                    print(f"   ⚠️ Template Word não encontrado, usando template padrão")
                    pdf_buffer = generate_digi_template_pdf(excel_data[0])
            else:
                print(f"   📄 Usando template padrão DIGI")
                pdf_buffer = generate_digi_template_pdf(excel_data[0])
            
            if pdf_buffer is None:
                return jsonify({'error': 'Erro ao gerar PDF'}), 500
            
            # Nome do arquivo baseado no número
            numero = excel_data[0].get('NUMERO', '001')
            filename = f'Carta_{numero}.pdf'
            
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        
        # Se múltiplas linhas, iniciar processo assíncrono otimizado
        print(f"   📦 Gerando múltiplos PDFs")
        print(f"   🎯 Template configurado: {template_name if template_name else 'DEFAULT'}")
        print(f"   🎨 Usar Word: {use_word_template}")
        
        job_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Determinar template a usar
        template_to_use = template_name if template_name else "Template padrão DIGI"
        
        progress_tracker[job_id] = {
            'total': len(excel_data),
            'current': 0,
            'status': 'processing',
            'message': f'Iniciando geração otimizada de PDFs usando template "{template_to_use}"...',
            'start_time': start_time,
            'estimated_time_remaining': None,
            'elapsed_time': 0
        }
        
        job_start_times[job_id] = start_time
        current_jobs.add(job_id)
        
        # Iniciar geração em background com processamento paralelo
        thread = threading.Thread(
            target=generate_multiple_pdfs_parallel,
            args=(excel_data, template_name, use_word_template, job_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'total': len(excel_data),
            'message': 'Geração otimizada iniciada. Use o job_id para acompanhar o progresso.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar PDF: {str(e)}'}), 500

@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    """Endpoint para verificar progresso"""
    try:
        # Limpar jobs antigos periodicamente
        cleanup_old_jobs()
        
        if job_id in progress_tracker:
            # Atualizar tempo decorrido em tempo real
            current_time = time.time()
            job_info = progress_tracker[job_id]
            
            if job_info['status'] == 'processing':
                # Calcular tempo decorrido atual
                elapsed_time = current_time - job_info['start_time']
                job_info['elapsed_time'] = elapsed_time
                
                # Recalcular tempo restante se há progresso
                if job_info['current'] > 0:
                    avg_time_per_pdf = elapsed_time / job_info['current']
                    remaining_pdfs = job_info['total'] - job_info['current']
                    estimated_remaining = avg_time_per_pdf * remaining_pdfs
                    job_info['estimated_time_remaining'] = estimated_remaining
            
            return jsonify(job_info)
        else:
            return jsonify({'error': 'Job não encontrado'}), 404
    except Exception as e:
        print(f"Erro ao verificar progresso do job {job_id}: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/download/<job_id>')
def download_result(job_id):
    """Endpoint para baixar resultado final"""
    if job_id not in progress_tracker:
        return jsonify({'error': 'Job não encontrado'}), 404
    
    job_info = progress_tracker[job_id]
    if job_info['status'] != 'completed':
        return jsonify({'error': 'Job ainda não foi concluído'}), 400
    
    try:
        zip_path = job_info.get('zip_path')
        if not zip_path or not os.path.exists(zip_path):
            return jsonify({'error': 'Arquivo ZIP não encontrado'}), 404
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f'cartas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        return jsonify({'error': f'Erro ao baixar arquivo: {str(e)}'}), 500

def generate_multiple_pdfs_parallel(data_list, template_name, use_word_template, job_id):
    """Gera múltiplos PDFs usando processamento paralelo otimizado"""
    try:
        print(f"🚀 SUPER ULTRA: Gerando {len(data_list)} PDFs")
        print(f"   Template selecionado: {template_name if template_name else 'DEFAULT'}")
        print(f"   Usar template Word: {use_word_template}")
        print(f"   Job ID: {job_id}")
        
        temp_zip_path = os.path.join(app.config['TEMP_FOLDER'], f'result_{job_id}.zip')
        
        # Usar configurações SUPER ULTRA
        num_workers = app.config['MAX_WORKERS']  # 16 workers
        chunk_size = app.config['CHUNK_SIZE']    # 5 registros por chunk
        print(f"   Workers: {num_workers} (SUPER ULTRA)")
        print(f"   Chunk size: {chunk_size} (SUPER ULTRA)")
        
        # Preparar template se necessário
        if use_word_template and template_name:
            print(f"   📋 Preparando cache do template: {template_name}")
            prepare_template_cache(template_name)
        
        # Processar cada PDF individualmente para progresso mais preciso
        pdf_files = []
        completed_count = 0
        
        # Dividir dados em chunks SUPER ULTRA
        chunks = [data_list[i:i + chunk_size] for i in range(0, len(data_list), chunk_size)]
        print(f"   Chunks: {len(chunks)} (tamanho: {chunk_size})")
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submeter tarefas por chunk
            future_to_chunk = {}
            for i, chunk in enumerate(chunks):
                print(f"   📦 Submetendo chunk {i} com {len(chunk)} registros")
                future = executor.submit(
                    process_chunk_optimized,
                    chunk, template_name, use_word_template, job_id, i
                )
                future_to_chunk[future] = chunk
            
            # Coletar resultados e atualizar progresso em tempo real
            for future in as_completed(future_to_chunk):
                try:
                    chunk_files = future.result()
                    pdf_files.extend(chunk_files)
                    completed_count += len(chunk_files)
                    
                    # Atualizar progresso imediatamente
                    current_time = time.time()
                    elapsed_time = current_time - progress_tracker[job_id]['start_time']
                    
                    if completed_count > 0:
                        # Calcular tempo médio por PDF
                        avg_time_per_pdf = elapsed_time / completed_count
                        remaining_pdfs = len(data_list) - completed_count
                        estimated_remaining = avg_time_per_pdf * remaining_pdfs
                    else:
                        estimated_remaining = None
                    
                    # Calcular taxa de velocidade
                    if completed_count > 0 and elapsed_time > 0:
                        rate = completed_count / elapsed_time
                    else:
                        rate = 0
                    
                    # Atualizar progresso
                    progress_tracker[job_id]['current'] = completed_count
                    progress_tracker[job_id]['elapsed_time'] = elapsed_time
                    progress_tracker[job_id]['estimated_time_remaining'] = estimated_remaining
                    progress_tracker[job_id]['rate'] = rate
                    progress_tracker[job_id]['message'] = f'SUPER: {completed_count}/{len(data_list)} PDFs ({rate:.2f}/s)'
                    
                    print(f"   ⚡ SUPER Progresso: {completed_count}/{len(data_list)} ({rate:.2f}/s)")
                    
                except Exception as e:
                    print(f"   ❌ Erro no processamento de chunk: {e}")
                    # Continuar processando outros chunks mesmo se um falhar
                    continue
        
        # Criar ZIP final
        print(f"   📦 Criando ZIP final...")
        zip_created = create_final_zip(pdf_files, temp_zip_path)
        
        if not zip_created:
            print(f"   ❌ Falha ao criar ZIP - nenhum arquivo adicionado")
            progress_tracker[job_id]['status'] = 'error'
            progress_tracker[job_id]['message'] = 'Erro: Nenhum PDF foi gerado com sucesso'
            return
        
        # Limpar arquivos temporários
        cleanup_temp_files(pdf_files)
        
        # Calcular tempo total
        total_time = time.time() - progress_tracker[job_id]['start_time']
        
        # Atualizar progresso final
        progress_tracker[job_id]['status'] = 'completed'
        progress_tracker[job_id]['message'] = f'SUPER Concluído! {len(data_list)} PDFs em {total_time:.1f}s'
        progress_tracker[job_id]['zip_path'] = temp_zip_path
        progress_tracker[job_id]['total_time'] = total_time
        progress_tracker[job_id]['estimated_time_remaining'] = 0
        
        print(f"   🎉 SUPER ULTRA: {len(data_list)} PDFs em {total_time:.1f}s")
        print(f"   🚀 Taxa SUPER: {len(data_list)/total_time:.2f} PDFs/segundo")
        print(f"   📁 ZIP salvo em: {temp_zip_path}")
        
        # Preparar sistema para próximo lote
        prepare_system_for_next_batch(job_id)
        
    except Exception as e:
        print(f"   ❌ Erro na geração: {e}")
        progress_tracker[job_id]['status'] = 'error'
        progress_tracker[job_id]['message'] = f'Erro: {str(e)}'

def process_chunk_optimized(chunk, template_name, use_word_template, job_id, chunk_id):
    """Processa um chunk de dados com otimizações de velocidade"""
    pdf_files = []
    
    print(f"🔄 Processando chunk {chunk_id} com {len(chunk)} registros")
    print(f"   Template: {template_name if template_name else 'DEFAULT'}")
    print(f"   Usar Word: {use_word_template}")
    
    for i, row_data in enumerate(chunk):
        try:
            nome = row_data.get('NOME', f'registro_{i+1}')
            print(f"   📄 Gerando PDF {i+1}/{len(chunk)} para: {nome}")
            
            # Verificar se há template Word disponível
            if use_word_template and template_name:
                template_path = os.path.join(app.config['TEMPLATES_FOLDER'], template_name)
                if os.path.exists(template_path):
                    print(f"      🎨 Usando template Word: {template_name}")
                    pdf_buffer = generate_word_pdf_ultra_optimized(row_data, template_name)
                else:
                    print(f"      ⚠️ Template Word não encontrado, usando template padrão")
                    pdf_buffer = generate_digi_template_pdf(row_data)
            else:
                print(f"      📄 Usando template padrão DIGI")
                pdf_buffer = generate_digi_template_pdf(row_data)
            
            # Verificar se o buffer foi gerado corretamente
            if pdf_buffer is None:
                print(f"      ❌ PDF buffer é None para {nome}")
                continue
                
            # Verificar se o buffer tem conteúdo
            pdf_content = pdf_buffer.getvalue()
            if not pdf_content:
                print(f"      ❌ PDF buffer vazio para {nome}")
                continue
            
            # Salvar PDF temporário com nome único
            temp_pdf_path = os.path.join(
                app.config['TEMP_FOLDER'], 
                f'temp_{job_id}_chunk_{chunk_id}_item_{i}_{int(time.time() * 1000)}.pdf'
            )
            
            with open(temp_pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            # Verificar se o arquivo foi criado
            if not os.path.exists(temp_pdf_path):
                print(f"      ❌ Arquivo PDF não foi criado: {temp_pdf_path}")
                continue
            
            file_size = os.path.getsize(temp_pdf_path)
            if file_size == 0:
                print(f"      ❌ Arquivo PDF vazio: {temp_pdf_path}")
                continue
            
            # Nome do arquivo baseado no número
            numero = row_data.get('NUMERO', f'{i+1:03d}')
            filename = f'Carta_{numero}.pdf'
            
            pdf_files.append((temp_pdf_path, filename))
            print(f"      ✅ PDF gerado: {filename} ({file_size} bytes)")
            
        except Exception as e:
            print(f"      ❌ Erro ao gerar PDF para {row_data.get('NOME', 'registro')}: {e}")
            # Continuar processando outros registros mesmo se um falhar
            continue
    
    print(f"   ✅ Chunk {chunk_id} concluído: {len(pdf_files)} PDFs gerados")
    return pdf_files

def generate_digi_template_pdf(row_data):
    """Gera PDF usando template DIGI padrão embutido"""
    try:
        print(f"      🎨 Gerando PDF com template DIGI padrão")
        
        # Extrair dados
        numero = row_data.get('NUMERO', '[NUMERO]')
        iccid = row_data.get('ICCID', '[ICCID]')
        nome = row_data.get('NOME', '[NOME]')
        
        # Gerar PDF com formatação exata da DIGI
        pdf_buffer = io.BytesIO()
        doc_pdf = SimpleDocTemplate(pdf_buffer, pagesize=A4, 
                                   topMargin=0.7*inch, bottomMargin=0.7*inch,
                                   leftMargin=0.7*inch, rightMargin=0.7*inch)
        story = []
        
        # Estilos otimizados para DIGI
        styles = getSampleStyleSheet()
        
        # Estilo para logo DIGI (azul, centralizado, grande)
        digi_logo_style = ParagraphStyle(
            'DigiLogo',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Centralizado
            textColor=colors.HexColor('#0915FF'),
            fontName='Helvetica-Bold'
        )
        
        # Estilo para saudação
        greeting_style = ParagraphStyle(
            'Greeting',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            leading=16,
            alignment=0,  # Esquerda
            textColor=colors.black
        )
        
        # Estilo para título de boas-vindas
        welcome_style = ParagraphStyle(
            'Welcome',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            leading=18,
            alignment=0,  # Esquerda
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para texto normal
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leading=14,
            alignment=0,  # Esquerda
            textColor=colors.black
        )
        
        # Estilo para dados importantes (número, ICCID)
        data_style = ParagraphStyle(
            'Data',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leading=14,
            alignment=0,  # Esquerda
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para contato
        contact_style = ParagraphStyle(
            'Contact',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            leading=14,
            alignment=0,  # Esquerda
            textColor=colors.black
        )
        
        # Estilo para fechamento
        closing_style = ParagraphStyle(
            'Closing',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=15,
            leading=14,
            alignment=0,  # Esquerda
            textColor=colors.black
        )
        
        # Estilo para rodapé legal
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            leading=12,
            alignment=0,  # Esquerda
            textColor=colors.grey
        )
        
        # Conteúdo do template DIGI
        story.append(Paragraph("DIGI", digi_logo_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("Olá,", greeting_style))
        story.append(Spacer(1, 8))
        
        story.append(Paragraph("Bem-vindo/a à DIGI!", welcome_style))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("Estamos muito entusiasmados por ter-te connosco.", normal_style))
        story.append(Spacer(1, 8))
        
        story.append(Paragraph("Agora, já podes desfrutar das vantagens de ser DIGI, como ter sempre o nosso melhor preço ou receber uma fatura sem surpresas.", normal_style))
        story.append(Spacer(1, 8))
        
        story.append(Paragraph("Aqui, encontras o teu número de telemóvel e o código ICCID associado ao teu novo cartão SIM, para que possas identificá-lo facilmente caso tenhas contratado mais do que um número.", normal_style))
        story.append(Spacer(1, 8))
        
        # Tabela com dados
        table_data = [
            ['Número', 'Código ICCID cartão'],
            [numero, iccid]
        ]
        
        pdf_table = Table(table_data)
        table_style = TableStyle([
            # Cabeçalho - negrito e sublinhado
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Linha separadora do cabeçalho
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            # Corpo da tabela
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            # Sem bordas internas
            ('BACKGROUND', (0, 0), (-1, -1), colors.white)
        ])
        
        pdf_table.setStyle(table_style)
        story.append(pdf_table)
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("Em caso de dúvida, não hesites em contactar-nos através do 923 30 90 30 (gratuito na rede DIGI e com custo de uma chamada normal para outros operadores). Estamos aqui para te ajudar.", contact_style))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph("Até breve,", closing_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("A Equipa DIGI.", closing_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("DIGI PORTUGAL, LDA. Matriculada na CRC sobo nº 516222201 - Capital Social 150.000.000,00€ Avenida José Malhoa nº11,3º Andar - 1070-157 Lisboa", footer_style))
        story.append(Spacer(1, 6))
        
        # Construir PDF
        doc_pdf.build(story)
        pdf_buffer.seek(0)
        
        print(f"      ✅ PDF gerado com sucesso: {len(pdf_buffer.getvalue())} bytes")
        return pdf_buffer
        
    except Exception as e:
        print(f"      ❌ Erro ao gerar template DIGI: {e}")
        return None

def create_final_zip(pdf_files, zip_path):
    """Cria o ZIP final com todos os PDFs"""
    print(f"📦 Criando ZIP final: {len(pdf_files)} arquivos")
    
    if not pdf_files:
        print(f"   ❌ Nenhum arquivo PDF para adicionar ao ZIP")
        return False
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        added_files = 0
        for pdf_path, filename in pdf_files:
            print(f"   📄 Verificando: {pdf_path}")
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"      ✅ Adicionando: {filename} ({file_size} bytes)")
                zip_file.write(pdf_path, filename)
                added_files += 1
            else:
                print(f"      ❌ Arquivo não encontrado: {pdf_path}")
        
        print(f"   ✅ ZIP criado com {added_files} arquivos")
        print(f"   📁 Caminho do ZIP: {zip_path}")
        
        # Verificar tamanho do ZIP
        if os.path.exists(zip_path):
            zip_size = os.path.getsize(zip_path)
            print(f"   📊 Tamanho do ZIP: {zip_size} bytes")
            return added_files > 0
        else:
            print(f"   ❌ ZIP não foi criado")
            return False

def cleanup_temp_files(pdf_files):
    """Remove arquivos temporários"""
    for pdf_path, _ in pdf_files:
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except:
            pass

def prepare_system_for_next_batch(job_id):
    """Prepara o sistema para gerar mais lotes após completar um job"""
    try:
        print(f"🔄 Preparando sistema para próximo lote...")
        
        # Limpar cache de templates para garantir templates atualizados
        template_cache.clear()
        print(f"   ✅ Cache de templates limpo")
        
        # Limpar jobs antigos (manter apenas o atual por um tempo)
        old_jobs = [jid for jid in progress_tracker.keys() if jid != job_id]
        for old_job in old_jobs:
            if old_job in progress_tracker:
                # Manter job atual por 5 minutos para download
                job_age = time.time() - progress_tracker[old_job].get('start_time', 0)
                if job_age > 300:  # 5 minutos
                    del progress_tracker[old_job]
                    if old_job in current_jobs:
                        current_jobs.remove(old_job)
        
        print(f"   ✅ Jobs antigos limpos")
        
        # Limpar arquivos temporários antigos
        temp_files = []
        for filename in os.listdir(app.config['TEMP_FOLDER']):
            if filename.startswith('temp_') and not filename.startswith(f'temp_{job_id}'):
                file_path = os.path.join(app.config['TEMP_FOLDER'], filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        temp_files.append(filename)
                except:
                    pass
        
        print(f"   ✅ {len(temp_files)} arquivos temporários antigos removidos")
        
        # Resetar configurações para próximo lote
        app.config['MAX_WORKERS'] = 8  # Manter configuração otimizada
        app.config['CHUNK_SIZE'] = 5   # Manter chunks otimizados
        
        print(f"   ✅ Sistema pronto para próximo lote!")
        print(f"   🚀 Workers: {app.config['MAX_WORKERS']}")
        print(f"   📦 Chunk Size: {app.config['CHUNK_SIZE']}")
        
    except Exception as e:
        print(f"   ⚠️ Aviso ao preparar sistema: {e}")
        # Não falhar o job por causa da limpeza

@lru_cache(maxsize=10)
def prepare_template_cache(template_name):
    """Prepara cache do template para reutilização"""
    if template_name not in template_cache:
        template_path = os.path.join(app.config['TEMPLATES_FOLDER'], template_name)
        template_cache[template_name] = {
            'path': template_path,
            'last_modified': os.path.getmtime(template_path)
        }



def generate_simple_pdf(row_data, template_text):
    """Gera PDF simples com ReportLab (fallback) - usa versão otimizada"""
    return generate_simple_pdf_optimized(row_data, template_text)

def generate_word_pdf_ultra_optimized(row_data, template_name):
    """Gera PDF a partir de template Word SEM HTML, apenas Word. Se falhar, retorna erro claro."""
    try:
        print(f"      🎨 Iniciando geração Word PDF para template: {template_name}")
        print(f"      📊 Dados recebidos: {list(row_data.keys())}")
        
        # Verificar cache
        if template_name not in template_cache:
            prepare_template_cache(template_name)
        
        template_info = template_cache[template_name]
        template_path = template_info['path']
        
        print(f"      📁 Template path: {template_path}")
        print(f"      ✅ Template existe: {os.path.exists(template_path)}")
        
        # Criar documento temporário com nome único
        timestamp = int(time.time() * 1000000)  # Microsegundos para garantir unicidade
        temp_docx = os.path.join(app.config['TEMP_FOLDER'], f'temp_{timestamp}.docx')
        temp_pdf = os.path.join(app.config['TEMP_FOLDER'], f'temp_{timestamp}.pdf')
        
        print(f"      📄 Temp DOCX: {temp_docx}")
        print(f"      📄 Temp PDF: {temp_pdf}")
        
        # Copiar template
        shutil.copy2(template_path, temp_docx)
        print(f"      ✅ Template copiado para: {temp_docx}")
        
        # Carregar documento e substituir placeholders de forma simples
        doc = Document(temp_docx)
        
        # Substituir placeholders de forma simples e robusta
        def replace_placeholders_simple():
            placeholder_mapping = {
                '[NUMERO]': 'NUMERO',
                '[ICCID]': 'ICCID',
                '[NOME]': 'NOME',
                '[EMAIL]': 'EMAIL',
                '[TELEFONE]': 'TELEFONE'
            }
            for paragraph in doc.paragraphs:
                full_text = paragraph.text
                new_text = full_text
                for placeholder, data_key in placeholder_mapping.items():
                    if placeholder in new_text and data_key in row_data:
                        new_text = new_text.replace(placeholder, str(row_data[data_key]) if row_data[data_key] is not None else '')
                        print(f"      🔄 Substituído: {placeholder} → {row_data[data_key]}")
                for key, value in row_data.items():
                    placeholder = f'[{key.upper()}]'
                    if placeholder in new_text:
                        new_text = new_text.replace(placeholder, str(value) if value is not None else '')
                if new_text != full_text:
                    paragraph.text = new_text
                    print(f"      ✅ Parágrafo atualizado")
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            full_text = paragraph.text
                            new_text = full_text
                            for placeholder, data_key in placeholder_mapping.items():
                                if placeholder in new_text and data_key in row_data:
                                    new_text = new_text.replace(placeholder, str(row_data[data_key]) if row_data[data_key] is not None else '')
                            for key, value in row_data.items():
                                placeholder = f'[{key.upper()}]'
                                if placeholder in new_text:
                                    new_text = new_text.replace(placeholder, str(value) if value is not None else '')
                            if new_text != full_text:
                                paragraph.text = new_text
        replace_placeholders_simple()
        doc.save(temp_docx)
        print(f"      ✅ Documento salvo com placeholders substituídos")
        print(f"      🔄 Convertendo para PDF usando método robusto...")
        pdf_content = convert_word_to_pdf_fallback(temp_docx, temp_pdf)
        try:
            os.remove(temp_docx)
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
        except:
            pass
        if pdf_content is not None:
            pdf_buffer = io.BytesIO(pdf_content)
            pdf_buffer.seek(0)
            print(f"      ✅ PDF gerado com sucesso: {len(pdf_content)} bytes")
            return pdf_buffer
        else:
            print(f"      ❌ Falha na conversão Word para PDF. Verifique o template.")
            raise Exception("Falha na conversão Word para PDF. Verifique o template.")
    except Exception as e:
        print(f"      ❌ Erro na geração Word PDF: {e}")
        raise Exception(f"Erro na geração Word PDF: {e}")

def generate_word_pdf_alternative_method(row_data, template_path, temp_docx, temp_pdf):
    """Método alternativo para substituir placeholders quando o método principal falha"""
    try:
        print(f"🔄 Usando método alternativo para {row_data.get('NOME', 'registro')}")
        
        # Ler o template como texto
        doc = Document(template_path)
        template_text = ""
        
        # Extrair texto completo do template preservando estrutura
        for paragraph in doc.paragraphs:
            template_text += paragraph.text + "\n"
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        template_text += paragraph.text + "\n"
        
        # Substituir placeholders no texto
        for key, value in row_data.items():
            placeholder = f'[{key.upper()}]'
            if placeholder in template_text:
                template_text = template_text.replace(placeholder, str(value) if value is not None else '')
                print(f"   ✅ Substituído {placeholder} → {value}")
        
        # Verificar se ainda há placeholders
        placeholders_restantes = []
        for key in row_data.keys():
            if f'[{key.upper()}]' in template_text:
                placeholders_restantes.append(f'[{key.upper()}]')
        
        if placeholders_restantes:
            print(f"   ⚠️ Placeholders restantes: {placeholders_restantes}")
        else:
            print(f"   ✅ Todos os placeholders substituídos!")
        
        # Gerar PDF usando ReportLab com o texto processado
        return generate_simple_pdf_optimized(row_data, template_text)
        
    except Exception as e:
        print(f"❌ Erro no método alternativo: {e}")
        return generate_simple_pdf_optimized(row_data, DEFAULT_TEMPLATE)

def convert_word_to_pdf_preserve_formatting(docx_path, pdf_path):
    """Converte Word para PDF preservando formatação exata"""
    try:
        print(f"🔄 Iniciando conversão Word→PDF: {os.path.basename(docx_path)}")
        
        # Método 1: Tentar com docx2pdf (preserva formatação)
        try:
            print(f"   📄 Tentando docx2pdf...")
            convert(docx_path, pdf_path)
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    pdf_content = f.read()
                if len(pdf_content) > 0:
                    print(f"   ✅ Conversão docx2pdf bem-sucedida: {len(pdf_content)} bytes")
                    return pdf_content
                else:
                    print(f"   ❌ PDF criado mas está vazio")
            else:
                print(f"   ❌ PDF não foi criado")
        except Exception as e:
            print(f"   ❌ docx2pdf falhou: {e}")
            
        # Método 2: Tentar com COM direto (preserva formatação)
        try:
            print(f"   🖥️ Tentando COM direto...")
            return convert_word_to_pdf_com_preserve_formatting(docx_path, pdf_path)
        except Exception as e:
            print(f"   ❌ COM direto falhou: {e}")
            
        # Método 3: Tentar COM robusto (preserva formatação)
        try:
            print(f"   🛡️ Tentando COM robusto...")
            return convert_word_to_pdf_com_robust(docx_path, pdf_path)
        except Exception as e:
            print(f"   ❌ COM robusto falhou: {e}")
            
        # Se todos os métodos falharam, não usar fallback ReportLab
        print(f"   ❌ Todos os métodos de conversão falharam")
        raise Exception("Não foi possível converter Word para PDF preservando formatação")
        
    except Exception as e:
        print(f"❌ Erro na conversão Word→PDF: {e}")
        raise e

def convert_word_to_pdf_robust(docx_path, pdf_path):
    """Converte Word para PDF com tratamento robusto de COM (método antigo)"""
    return convert_word_to_pdf_preserve_formatting(docx_path, pdf_path)

def convert_word_to_pdf_com_preserve_formatting(docx_path, pdf_path):
    """Converte Word para PDF usando COM direto preservando formatação exata"""
    
    # Fallback se Windows não estiver disponível
    if not WINDOWS_AVAILABLE:
        print(f"   ⚠️ Windows não disponível, usando fallback")
        return convert_word_to_pdf_fallback(docx_path, pdf_path)
    
    word = None
    doc = None
    try:
        # Inicializar COM para esta thread
        pythoncom.CoInitialize()
        
        # Criar instância do Word com DispatchEx para nova instância
        word = win32com.client.DispatchEx("Word.Application")
        
        # Configurar Word para preservar formatação
        word.Visible = False
        word.DisplayAlerts = False
        
        # Verificar se arquivo existe
        if not os.path.exists(docx_path):
            raise Exception(f"Arquivo não encontrado: {docx_path}")
        
        # Abrir documento com caminho absoluto
        abs_docx_path = os.path.abspath(docx_path)
        abs_pdf_path = os.path.abspath(pdf_path)
        
        print(f"   📄 Abrindo documento: {os.path.basename(docx_path)}")
        doc = word.Documents.Open(abs_docx_path)
        
        # Configurar opções de PDF para preservar formatação
        print(f"   🔄 Convertendo para PDF...")
        
        # Múltiplas tentativas com diferentes parâmetros (versão robusta)
        methods = [
            lambda: doc.SaveAs(abs_pdf_path, FileFormat=17, OptimizeFor=0),
            lambda: doc.SaveAs(abs_pdf_path, FileFormat=17),
            lambda: doc.SaveAs(abs_pdf_path, FileFormat=6),
            lambda: doc.SaveAs(abs_pdf_path)
        ]
        
        success = False
        for i, method in enumerate(methods):
            try:
                method()
                success = True
                print(f"   ✅ Conversão bem-sucedida com método {i+1}")
                break
            except Exception as e:
                if i == len(methods) - 1:  # Última tentativa
                    raise e
                print(f"   ⚠️ Método {i+1} falhou, tentando próximo...")
                continue
        
        # Fechar documento
        doc.Close(False)  # False = não salvar alterações
        
        # Verificar se PDF foi criado
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            if file_size > 1000:  # PDF deve ter pelo menos 1KB
                print(f"   ✅ PDF criado com sucesso: {file_size} bytes")
                with open(pdf_path, 'rb') as f:
                    pdf_content = f.read()
                return pdf_content
            else:
                raise Exception(f"PDF criado mas muito pequeno: {file_size} bytes")
        else:
            raise Exception("PDF não foi criado")
            
    except Exception as e:
        print(f"   ❌ Erro na conversão COM: {e}")
        raise e
        
    finally:
        # Limpar recursos de forma robusta
        if doc is not None:
            try:
                doc.Close(False)
            except:
                pass
        if word is not None:
            try:
                word.Quit()
            except:
                pass
        try:
            pythoncom.CoUninitialize()
        except:
            pass

def convert_word_to_pdf_fallback(docx_path, pdf_path):
    """Fallback robusto para conversão Word para PDF usando apenas ReportLab"""
    try:
        print(f"   📄 Usando conversão ReportLab robusta")
        
        # Ler o documento Word
        doc = Document(docx_path)
        
        # Gerar PDF com formatação exata da DIGI
        pdf_buffer = io.BytesIO()
        doc_pdf = SimpleDocTemplate(pdf_buffer, pagesize=A4, 
                                   topMargin=0.7*inch, bottomMargin=0.7*inch,
                                   leftMargin=0.7*inch, rightMargin=0.7*inch)
        story = []
        
        # Estilos otimizados para DIGI
        styles = getSampleStyleSheet()
        
        # Estilo para logo DIGI (azul, centralizado, grande)
        digi_logo_style = ParagraphStyle(
            'DigiLogo',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Centralizado
            textColor=colors.HexColor('#0915FF'),
            fontName='Helvetica-Bold'
        )
        
        # Estilo para saudação
        greeting_style = ParagraphStyle(
            'Greeting',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            leading=16,
            alignment=0,  # Esquerda
            textColor=colors.black
        )
        
        # Estilo para título de boas-vindas
        welcome_style = ParagraphStyle(
            'Welcome',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            leading=18,
            alignment=0,  # Esquerda
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para texto normal
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leading=14,
            alignment=0,  # Esquerda
            textColor=colors.black
        )
        
        # Estilo para dados importantes (número, ICCID)
        data_style = ParagraphStyle(
            'Data',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leading=14,
            alignment=0,  # Esquerda
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para contato
        contact_style = ParagraphStyle(
            'Contact',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            leading=14,
            alignment=0,  # Esquerda
            textColor=colors.black
        )
        
        # Estilo para fechamento
        closing_style = ParagraphStyle(
            'Closing',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=15,
            leading=14,
            alignment=0,  # Esquerda
            textColor=colors.black
        )
        
        # Estilo para rodapé legal
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            leading=12,
            alignment=0,  # Esquerda
            textColor=colors.grey
        )
        
        # Processar parágrafos de forma inteligente
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
                
            # Detectar tipo de conteúdo baseado no texto
            text_lower = text.lower()
            
            if 'digi' in text_lower and len(text.strip()) <= 10:
                # Logo DIGI
                story.append(Paragraph(text, digi_logo_style))
                story.append(Spacer(1, 20))
                
            elif 'olá' in text_lower or 'ola' in text_lower:
                # Saudação
                story.append(Paragraph(text, greeting_style))
                story.append(Spacer(1, 8))
                
            elif 'bem-vindo' in text_lower or 'bem-vinda' in text_lower:
                # Título de boas-vindas
                story.append(Paragraph(text, welcome_style))
                story.append(Spacer(1, 12))
                
            elif any(keyword in text_lower for keyword in ['entusiasmados', 'vantagens', 'preço', 'fatura']):
                # Texto explicativo
                story.append(Paragraph(text, normal_style))
                story.append(Spacer(1, 8))
                
            elif any(keyword in text_lower for keyword in ['número', 'iccid', 'cartão', 'sim']):
                # Texto sobre dados
                story.append(Paragraph(text, normal_style))
                story.append(Spacer(1, 8))
                
            elif any(keyword in text_lower for keyword in ['923', 'contactar', 'dúvida', 'gratuito']):
                # Informações de contato
                story.append(Paragraph(text, contact_style))
                story.append(Spacer(1, 10))
                
            elif any(keyword in text_lower for keyword in ['até breve', 'equipa digi', 'equipe digi']):
                # Fechamento
                story.append(Paragraph(text, closing_style))
                story.append(Spacer(1, 15))
                
            elif any(keyword in text_lower for keyword in ['matriculada', 'capital social', 'avenida', 'lisboa']):
                # Rodapé legal
                story.append(Paragraph(text, footer_style))
                story.append(Spacer(1, 6))
                
            else:
                # Texto normal
                story.append(Paragraph(text, normal_style))
                story.append(Spacer(1, 6))
        
        # Processar tabelas de forma otimizada
        for table in doc.tables:
            if table.rows:
                table_data = []
                
                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        # Extrair texto da célula
                        cell_text = ""
                        for paragraph in cell.paragraphs:
                            cell_text += paragraph.text + " "
                        row_data.append(cell_text.strip())
                    
                    if any(cell.strip() for cell in row_data):  # Só adicionar se não estiver vazio
                        table_data.append(row_data)
                
                if table_data:
                    # Criar tabela no PDF
                    pdf_table = Table(table_data)
                    
                    # Estilo da tabela DIGI (cabeçalho sublinhado, sem bordas internas)
                    table_style = TableStyle([
                        # Cabeçalho - negrito e sublinhado
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 0), (-1, 0), 8),
                        # Linha separadora do cabeçalho
                        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                        # Corpo da tabela
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 11),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                        ('TOPPADDING', (0, 1), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                        # Sem bordas internas
                        ('BACKGROUND', (0, 0), (-1, -1), colors.white)
                    ])
                    
                    pdf_table.setStyle(table_style)
                    story.append(pdf_table)
                    story.append(Spacer(1, 15))
        
        # Construir PDF
        doc_pdf.build(story)
        pdf_buffer.seek(0)
        
        # Salvar PDF
        with open(pdf_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        # Ler o PDF gerado e retornar o conteúdo
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        print(f"   ✅ PDF gerado com sucesso: {pdf_path} ({len(pdf_content)} bytes)")
        return pdf_content
        
    except Exception as e:
        print(f"   ❌ Erro no fallback ReportLab: {str(e)}")
        return None

def convert_word_to_pdf_com_robust(docx_path, pdf_path):
    """Converte Word para PDF usando COM direto com tratamento robusto (método antigo)"""
    return convert_word_to_pdf_com_preserve_formatting(docx_path, pdf_path)

def generate_simple_pdf_optimized(row_data, template_text):
    """Gera PDF simples com ReportLab otimizado e formatação melhorada"""
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, 
                           topMargin=1*inch, bottomMargin=1*inch,
                           leftMargin=1*inch, rightMargin=1*inch)
    story = []
    
    # Estilos otimizados
    styles = getSampleStyleSheet()
    
    # Estilo para título
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=1,  # Centralizado
        textColor=colors.HexColor('#0915FF')
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        leading=16,
        alignment=0  # Justificado
    )
    
    # Estilo para assinatura
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        leading=16,
        alignment=2  # Direita
    )
    
    # Substituir placeholders no template de forma otimizada
    content = template_text
    for key, value in row_data.items():
        placeholder = f'[{key.upper()}]'
        content = content.replace(placeholder, str(value) if value is not None else '')
    
    # Dividir o conteúdo em linhas e criar parágrafos com formatação inteligente
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line:  # Se a linha não estiver vazia
            # Detectar tipo de linha para aplicar estilo apropriado
            if line.upper() in ['CARTA PERSONALIZADA', 'CARTA', 'DOCUMENTO']:
                story.append(Paragraph(line, title_style))
            elif line.startswith('Com os melhores cumprimentos') or line.startswith('Atenciosamente'):
                story.append(Paragraph(line, signature_style))
            elif line == row_data.get('NOME', ''):  # Assinatura
                story.append(Paragraph(line, signature_style))
            else:
                story.append(Paragraph(line, normal_style))
        else:
            story.append(Spacer(1, 8))
    
    # Construir PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

if __name__ == '__main__':
    # Configuração para produção (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Iniciando servidor na porta {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"👥 Max workers: {app.config['MAX_WORKERS']}")
    print(f"📦 Chunk size: {app.config['CHUNK_SIZE']}")
    
    app.run(
        host='0.0.0.0',  # Importante para Render/Heroku
        port=port,
        debug=debug,
        threaded=True
    ) 