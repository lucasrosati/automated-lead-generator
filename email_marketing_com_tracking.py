#!/usr/bin/env python3
"""
Sistema de Email Marketing com Tracking Completo
Versão integrada com monitoramento de entregas, aberturas e cliques
"""

import pandas as pd
import smtplib
import time
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random
from sistema_monitoramento_analytics import EmailAnalytics

class EmailMarketingComTracking:
    def __init__(self):
        # Configurações básicas
        for key in list(os.environ.keys()):
            if key.startswith(('EMAIL_', 'SMTP_')):
                del os.environ[key]
        
        load_dotenv('.env', override=True)
        
        self.email = os.getenv('EMAIL_USER')
        self.password = os.getenv('EMAIL_PASS')
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        
        # Sistema de analytics
        self.analytics = EmailAnalytics()
        
        # Logs tradicionais + analytics
        self.sent_log = "emails_enviados_empresas.json"
        self.failed_log = "emails_falharam.json"
        
    def classificar_provedor(self, email):
        """Classifica provedor para analytics"""
        domain = email.split('@')[1].lower()
        
        if domain == 'gmail.com':
            return 'gmail'
        elif domain in ['hotmail.com', 'outlook.com', 'live.com', 'msn.com']:
            return 'outlook'
        elif domain in ['uol.com.br', 'yahoo.com.br']:
            return 'outros'
        elif domain.endswith('.gov.br'):
            return 'governo'
        elif domain.endswith('.edu.br'):
            return 'educacional'
        else:
            return 'corporativo'
    
    def send_tracked_email(self, recipient, empresa_nome, razao_social, subject_template, body_template):
        """Envia email com tracking completo"""
        
        provedor_tipo = self.classificar_provedor(recipient)
        
        try:
            # Criar email com tracking
            msg, tracking_id = self.analytics.create_tracked_email(
                recipient, empresa_nome, razao_social, 
                subject_template, body_template, provedor_tipo
            )
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            print(f"Email enviado com tracking: {empresa_nome} (ID: {tracking_id})")
            
            # Salvar no sistema tradicional também
            self.save_sent_email_traditional(razao_social, recipient, tracking_id)
            
            return True, tracking_id
            
        except Exception as e:
            print(f"Erro ao enviar para {empresa_nome}: {e}")
            self.save_failed_email(razao_social, recipient, str(e))
            return False, None
    
    def save_sent_email_traditional(self, razao_social, email, tracking_id):
        """Mantém compatibilidade com sistema tradicional"""
        sent_emails = self.load_sent_emails()
        sent_emails[razao_social] = {
            'email': email,
            'sent_at': datetime.now().isoformat(),
            'tracking_id': tracking_id,
            'status': 'sent_with_tracking'
        }
        with open(self.sent_log, 'w', encoding='utf-8') as f:
            json.dump(sent_emails, f, ensure_ascii=False, indent=2)
    
    def load_sent_emails(self):
        """Carrega emails enviados"""
        if os.path.exists(self.sent_log):
            with open(self.sent_log, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_failed_email(self, razao_social, email, error):
        """Salva email que falhou"""
        failed_emails = {}
        if os.path.exists(self.failed_log):
            with open(self.failed_log, 'r', encoding='utf-8') as f:
                failed_emails = json.load(f)
        
        failed_emails[razao_social] = {
            'email': email,
            'error': str(error),
            'failed_at': datetime.now().isoformat()
        }
        
        with open(self.failed_log, 'w', encoding='utf-8') as f:
            json.dump(failed_emails, f, ensure_ascii=False, indent=2)
    
    def executar_campanha_com_tracking(self, csv_file, subject_template, body_template, 
                                     emails_per_day=50, delay_range=(300, 600)):
        """Executa campanha completa com tracking"""
        
        # Carregar dados
        df = pd.read_csv(csv_file, encoding='utf-8')
        sent_emails = self.load_sent_emails()
        
        print("CAMPANHA COM TRACKING COMPLETO")
        print("="*50)
        print(f"Total de empresas: {len(df)}")
        print(f"Tracking habilitado: Abertura + Cliques + Respostas")
        print(f"Dashboard em tempo real: dashboard_analytics.html")
        
        # Filtrar não enviados
        remaining_companies = []