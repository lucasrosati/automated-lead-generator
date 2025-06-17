#!/usr/bin/env python3
"""
Sistema de Monitoramento e Analytics
Tracking completo de entrega, abertura, cliques e respostas
"""

import pandas as pd
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from dotenv import load_dotenv
import sqlite3
import hashlib

class EmailAnalytics:
    def __init__(self):
        load_dotenv('.env', override=True)
        self.email = os.getenv('EMAIL_USER')
        self.password = os.getenv('EMAIL_PASS')
        self.tracking_domain = "track.automated-lead-generator.com"  # Pode usar ngrok ou servidor próprio
        self.db_file = "email_analytics.db"
        self.setup_database()
        
    def setup_database(self):
        """Cria banco de dados para tracking"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Tabela principal de emails
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id TEXT UNIQUE,
                empresa_nome TEXT,
                razao_social TEXT,
                email_destino TEXT,
                provedor_tipo TEXT,
                assunto TEXT,
                enviado_em TIMESTAMP,
                status_entrega TEXT,
                aberto BOOLEAN DEFAULT 0,
                primeiro_abertura TIMESTAMP,
                total_aberturas INTEGER DEFAULT 0,
                clicou_link BOOLEAN DEFAULT 0,
                primeiro_clique TIMESTAMP,
                total_cliques INTEGER DEFAULT 0,
                respondeu BOOLEAN DEFAULT 0,
                data_resposta TIMESTAMP,
                bounce BOOLEAN DEFAULT 0,
                spam_reclamacao BOOLEAN DEFAULT 0,
                dispositivo_abertura TEXT,
                localizacao_abertura TEXT,
                user_agent TEXT
            )
        ''')
        
        # Tabela de eventos de tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracking_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id TEXT,
                evento_tipo TEXT,
                timestamp TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                dados_extras TEXT,
                FOREIGN KEY (tracking_id) REFERENCES email_campaigns (tracking_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def gerar_tracking_id(self, email_destino, empresa_nome):
        """Gera ID único para tracking"""
        raw_string = f"{email_destino}{empresa_nome}{datetime.now().isoformat()}"
        return hashlib.md5(raw_string.encode()).hexdigest()[:16]
    
    def create_tracked_email(self, recipient, empresa_nome, razao_social, subject_template, body_template, provedor_tipo):
        """Cria email com tracking completo"""
        
        tracking_id = self.gerar_tracking_id(recipient, empresa_nome)
        
        # Personalizar conteúdo
        subject = subject_template.format(empresa=empresa_nome, razao_social=razao_social)
        body = body_template.format(empresa=empresa_nome, razao_social=razao_social)
        
        # URLs de tracking
        pixel_url = f"https://{self.tracking_domain}/pixel/{tracking_id}.png"
        click_base_url = f"https://{self.tracking_domain}/click/{tracking_id}"
        unsubscribe_url = f"https://{self.tracking_domain}/unsubscribe/{tracking_id}"
        
        # Adicionar tracking pixel (invisível)
        tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt="">'
        
        # Converter links para tracking
        if "linkedin.com" in body:
            body = body.replace(
                "[Seu LinkedIn]", 
                f'<a href="{click_base_url}?url=https://linkedin.com/in/seu-perfil">LinkedIn</a>'
            )
        
        # Adicionar unsubscribe
        body += f'\n\n---\nPara descadastrar: {unsubscribe_url}'
        
        # HTML version com tracking
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        {body.replace(chr(10), '<br>')}
        {tracking_pixel}
        </body>
        </html>
        """
        
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['From'] = f"Lucas Rosati <{self.email}>"
        msg['To'] = recipient
        msg['Subject'] = subject
        msg['Reply-To'] = self.email
        msg['List-Unsubscribe'] = f"<{unsubscribe_url}>"
        
        # Adicionar versões texto e HTML
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Salvar no banco
        self.registrar_email_enviado(tracking_id, empresa_nome, razao_social, recipient, provedor_tipo, subject)
        
        return msg, tracking_id
    
    def registrar_email_enviado(self, tracking_id, empresa_nome, razao_social, email_destino, provedor_tipo, assunto):
        """Registra email enviado no banco"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO email_campaigns 
            (tracking_id, empresa_nome, razao_social, email_destino, provedor_tipo, assunto, enviado_em, status_entrega)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tracking_id, empresa_nome, razao_social, email_destino, provedor_tipo, assunto, datetime.now(), 'enviado'))
        
        conn.commit()
        conn.close()
    
    def registrar_evento(self, tracking_id, evento_tipo, ip_address=None, user_agent=None, dados_extras=None):
        """Registra evento de tracking"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tracking_events 
            (tracking_id, evento_tipo, timestamp, ip_address, user_agent, dados_extras)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tracking_id, evento_tipo, datetime.now(), ip_address, user_agent, json.dumps(dados_extras)))
        
        # Atualizar tabela principal
        if evento_tipo == 'abertura':
            cursor.execute('''
                UPDATE email_campaigns 
                SET aberto = 1, 
                    primeiro_abertura = COALESCE(primeiro_abertura, ?),
                    total_aberturas = total_aberturas + 1
                WHERE tracking_id = ?
            ''', (datetime.now(), tracking_id))
            
        elif evento_tipo == 'clique':
            cursor.execute('''
                UPDATE email_campaigns 
                SET clicou_link = 1,
                    primeiro_clique = COALESCE(primeiro_clique, ?),
                    total_cliques = total_cliques + 1
                WHERE tracking_id = ?
            ''', (datetime.now(), tracking_id))
        
        conn.commit()
        conn.close()
    
    def gerar_relatorio_completo(self):
        """Gera relatório completo da campanha"""
        conn = sqlite3.connect(self.db_file)
        
        # Estatísticas gerais
        query_geral = '''
            SELECT 
                COUNT(*) as total_enviados,
                COUNT(CASE WHEN aberto = 1 THEN 1 END) as total_abertos,
                COUNT(CASE WHEN clicou_link = 1 THEN 1 END) as total_cliques,
                COUNT(CASE WHEN respondeu = 1 THEN 1 END) as total_respostas,
                COUNT(CASE WHEN bounce = 1 THEN 1 END) as total_bounces,
                AVG(total_aberturas) as media_aberturas_por_email
            FROM email_campaigns
        '''
        
        stats_geral = pd.read_sql_query(query_geral, conn)
        
        # Por provedor
        query_provedor = '''
            SELECT 
                provedor_tipo,
                COUNT(*) as enviados,
                COUNT(CASE WHEN aberto = 1 THEN 1 END) as abertos,
                ROUND(COUNT(CASE WHEN aberto = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as taxa_abertura,
                COUNT(CASE WHEN clicou_link = 1 THEN 1 END) as cliques,
                ROUND(COUNT(CASE WHEN clicou_link = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as taxa_clique
            FROM email_campaigns
            GROUP BY provedor_tipo
            ORDER BY enviados DESC
        '''
        
        stats_provedor = pd.read_sql_query(query_provedor, conn)
        
        # Timeline de aberturas
        query_timeline = '''
            SELECT 
                DATE(primeiro_abertura) as data,
                COUNT(*) as aberturas_dia
            FROM email_campaigns 
            WHERE primeiro_abertura IS NOT NULL
            GROUP BY DATE(primeiro_abertura)
            ORDER BY data
        '''
        
        timeline = pd.read_sql_query(query_timeline, conn)
        
        # Empresas mais engajadas
        query_engajamento = '''
            SELECT 
                empresa_nome,
                email_destino,
                total_aberturas,
                total_cliques,
                CASE WHEN respondeu = 1 THEN 'Sim' ELSE 'Não' END as respondeu,
                primeiro_abertura
            FROM email_campaigns
            WHERE aberto = 1
            ORDER BY total_aberturas DESC, total_cliques DESC
            LIMIT 20
        '''
        
        top_engajamento = pd.read_sql_query(query_engajamento, conn)
        
        conn.close()
        
        return {
            'geral': stats_geral,
            'por_provedor': stats_provedor,
            'timeline': timeline,
            'top_engajamento': top_engajamento
        }
    
    def gerar_dashboard_html(self):
        """Gera dashboard HTML interativo"""
        relatorio = self.gerar_relatorio_completo()
        
        # Calcular métricas principais
        total = relatorio['geral']['total_enviados'].iloc[0]
        abertos = relatorio['geral']['total_abertos'].iloc[0]
        cliques = relatorio['geral']['total_cliques'].iloc[0]
        respostas = relatorio['geral']['total_respostas'].iloc[0]
        
        taxa_abertura = (abertos / total * 100) if total > 0 else 0
        taxa_clique = (cliques / total * 100) if total > 0 else 0
        taxa_resposta = (respostas / total * 100) if total > 0 else 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Email Marketing Analytics</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric {{ display: inline-block; text-align: center; margin: 10px 20px; }}
                .metric-value {{ font-size: 2.5em; font-weight: bold; color: #2196F3; }}
                .metric-label {{ font-size: 0.9em; color: #666; }}
                .table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                .table th, .table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                .table th {{ background-color: #f8f9fa; }}
                .status-enviado {{ color: #28a745; }}
                .status-aberto {{ color: #007bff; }}
                .status-clicado {{ color: #ffc107; }}
                .status-respondido {{ color: #dc3545; }}
                h1, h2 {{ color: #333; }}
                .update-time {{ color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Email Marketing Analytics Dashboard</h1>
                <p class="update-time">Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                
                <div class="card">
                    <h2>Métricas Principais</h2>
                    <div class="metric">
                        <div class="metric-value">{total}</div>
                        <div class="metric-label">Emails Enviados</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{abertos}</div>
                        <div class="metric-label">Abertos ({taxa_abertura:.1f}%)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{cliques}</div>
                        <div class="metric-label">Cliques ({taxa_clique:.1f}%)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{respostas}</div>
                        <div class="metric-label">Respostas ({taxa_resposta:.1f}%)</div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Performance por Provedor</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Provedor</th>
                                <th>Enviados</th>
                                <th>Abertos</th>
                                <th>Taxa Abertura</th>
                                <th>Cliques</th>
                                <th>Taxa Clique</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for _, row in relatorio['por_provedor'].iterrows():
            html_content += f"""
                            <tr>
                                <td>{row['provedor_tipo']}</td>
                                <td>{row['enviados']}</td>
                                <td>{row['abertos']}</td>
                                <td>{row['taxa_abertura']}%</td>
                                <td>{row['cliques']}</td>
                                <td>{row['taxa_clique']}%</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
                
                <div class="card">
                    <h2>Top 10 Empresas Mais Engajadas</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Empresa</th>
                                <th>Email</th>
                                <th>Aberturas</th>
                                <th>Cliques</th>
                                <th>Respondeu</th>
                                <th>Primeira Abertura</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for _, row in relatorio['top_engajamento'].head(10).iterrows():
            html_content += f"""
                            <tr>
                                <td>{row['empresa_nome']}</td>
                                <td>{row['email_destino']}</td>
                                <td>{row['total_aberturas']}</td>
                                <td>{row['total_cliques']}</td>
                                <td>{row['respondeu']}</td>
                                <td>{row['primeiro_abertura'] or 'N/A'}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Salvar dashboard
        with open('dashboard_analytics.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("Dashboard salvo como: dashboard_analytics.html")
        return html_content
    
    def exportar_dados_detalhados(self):
        """Exporta todos os dados para Excel"""
        conn = sqlite3.connect(self.db_file)
        
        # Dados principais
        df_emails = pd.read_sql_query('SELECT * FROM email_campaigns', conn)
        df_eventos = pd.read_sql_query('SELECT * FROM tracking_events', conn)
        
        conn.close()
        
        # Salvar em Excel com múltiplas abas
        with pd.ExcelWriter('analytics_detalhado.xlsx', engine='openpyxl') as writer:
            df_emails.to_excel(writer, sheet_name='Emails', index=False)
            df_eventos.to_excel(writer, sheet_name='Eventos', index=False)
            
            # Aba de resumo
            relatorio = self.gerar_relatorio_completo()
            relatorio['geral'].to_excel(writer, sheet_name='Resumo_Geral', index=False)
            relatorio['por_provedor'].to_excel(writer, sheet_name='Por_Provedor', index=False)
        
        print("Dados detalhados exportados para: analytics_detalhado.xlsx")
    
    def monitorar_respostas_gmail(self):
        """Monitora respostas no Gmail usando IMAP"""
        import imaplib
        import email
        
        try:
            # Conectar ao Gmail
            imap = imaplib.IMAP4_SSL('imap.gmail.com')
            imap.login(self.email, self.password)
            imap.select('INBOX')
            
            # Buscar emails recentes
            date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            _, messages = imap.search(None, f'(SINCE "{date}")')
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            for msg_id in messages[0].split():
                _, msg_data = imap.fetch(msg_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                sender = email_message['From']
                subject = email_message['Subject']
                
                # Verificar se é resposta para algum email da campanha
                cursor.execute('''
                    UPDATE email_campaigns 
                    SET respondeu = 1, data_resposta = ?
                    WHERE email_destino LIKE ? AND respondeu = 0
                ''', (datetime.now(), f'%{sender}%'))
            
            conn.commit()
            conn.close()
            imap.close()
            imap.logout()
            
            print("Verificação de respostas concluída")
            
        except Exception as e:
            print(f"Erro ao verificar respostas: {e}")

def create_tracking_server():
    """Cria servidor simples para tracking (usando Flask)"""
    server_code = '''
from flask import Flask, request, send_file, redirect
import sqlite3
from datetime import datetime
import io
import base64

app = Flask(__name__)

# Pixel transparente 1x1
PIXEL_DATA = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")

@app.route("/pixel/<tracking_id>.png")
def track_open(tracking_id):
    # Registrar abertura
    conn = sqlite3.connect("email_analytics.db")
    cursor = conn.cursor()
    
    ip_address = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")
    
    cursor.execute("""
        INSERT INTO tracking_events 
        (tracking_id, evento_tipo, timestamp, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?)
    """, (tracking_id, "abertura", datetime.now(), ip_address, user_agent))
    
    cursor.execute("""
        UPDATE email_campaigns 
        SET aberto = 1, 
            primeiro_abertura = COALESCE(primeiro_abertura, ?),
            total_aberturas = total_aberturas + 1
        WHERE tracking_id = ?
    """, (datetime.now(), tracking_id))
    
    conn.commit()
    conn.close()
    
    return send_file(io.BytesIO(PIXEL_DATA), mimetype="image/png")

@app.route("/click/<tracking_id>")
def track_click(tracking_id):
    url = request.args.get("url", "https://linkedin.com")
    
    # Registrar clique
    conn = sqlite3.connect("email_analytics.db")
    cursor = conn.cursor()
    
    ip_address = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")
    
    cursor.execute("""
        INSERT INTO tracking_events 
        (tracking_id, evento_tipo, timestamp, ip_address, user_agent, dados_extras)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tracking_id, "clique", datetime.now(), ip_address, user_agent, url))
    
    cursor.execute("""
        UPDATE email_campaigns 
        SET clicou_link = 1,
            primeiro_clique = COALESCE(primeiro_clique, ?),
            total_cliques = total_cliques + 1
        WHERE tracking_id = ?
    """, (datetime.now(), tracking_id))
    
    conn.commit()
    conn.close()
    
    return redirect(url)

@app.route("/unsubscribe/<tracking_id>")
def unsubscribe(tracking_id):
    return f"<h2>Descadastrado com sucesso!</h2><p>ID: {tracking_id}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
'''
    
    with open('tracking_server.py', 'w') as f:
        f.write(server_code)
    
    print("Servidor de tracking criado: tracking_server.py")
    print("Para executar: python tracking_server.py")
    print("Para expor publicamente: use ngrok ou deploy em servidor")

if __name__ == "__main__":
    analytics = EmailAnalytics()
    
    print("SISTEMA DE MONITORAMENTO E ANALYTICS")
    print("="*50)
    
    # Demonstração das funcionalidades
    print("\nFuncionalidades disponíveis:")
    print("1. Tracking de abertura (pixel invisível)")
    print("2. Tracking de cliques em links")
    print("3. Monitoramento de respostas")
    print("4. Dashboard HTML interativo")
    print("5. Exportação para Excel")
    print("6. Relatórios em tempo real")
    
    # Gerar dashboard de exemplo
    analytics.gerar_dashboard_html()
    
    # Criar servidor de tracking
    create_tracking_server()
    
    print("\nArquivos criados:")
    print("- dashboard_analytics.html (dashboard interativo)")
    print("- tracking_server.py (servidor de tracking)")
    print("- email_analytics.db (banco de dados)")