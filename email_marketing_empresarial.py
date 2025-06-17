#!/usr/bin/env python3
"""
Sistema de Email Marketing Empresarial
Desenvolvido para campanhas B2B com personalização automática
Autor: Lucas Rosati
"""

import pandas as pd
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

class EmailMarketingEmpresarial:
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.sent_log = "emails_enviados_empresas.json"
        self.failed_log = "emails_falharam.json"
        self.setup_logging()
        
    def setup_logging(self):
        """Configura sistema de logs detalhado"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('email_marketing_empresarial.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_empresas_csv(self, file_path: str) -> pd.DataFrame:
        """Carrega dados das empresas do CSV"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Verifica se tem as colunas necessárias
            required_cols = ['RazaoSocial', 'Email1']
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Coluna '{col}' não encontrada no CSV")
            
            # Remove linhas sem razão social
            df = df.dropna(subset=['RazaoSocial'])
            df = df[df['RazaoSocial'].str.strip() != '']
            
            self.logger.info(f"Carregadas {len(df)} empresas do arquivo {file_path}")
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar CSV: {e}")
            raise
    
    def get_best_email(self, row: pd.Series) -> Tuple[Optional[str], int]:
        """
        Retorna o melhor email disponível e sua prioridade
        Retorna: (email, prioridade) onde prioridade: 1=Email1, 2=Email2, 3=Email3
        """
        emails_to_check = [
            (row.get('Email1'), 1),
            (row.get('Email2'), 2), 
            (row.get('Email3'), 3)
        ]
        
        for email, priority in emails_to_check:
            if pd.notna(email) and email and '@' in str(email) and '.' in str(email):
                # Validação básica de email
                email_clean = str(email).strip().lower()
                if len(email_clean) > 5 and email_clean.count('@') == 1:
                    return email_clean, priority
        
        return None, 0
    
    def get_nome_empresa(self, row: pd.Series) -> str:
        """Extrai o nome da empresa, priorizando NomeFantasia sobre RazaoSocial"""
        nome_fantasia = row.get('NomeFantasia')
        razao_social = row.get('RazaoSocial')
        
        # Se tem nome fantasia e não está vazio
        if pd.notna(nome_fantasia) and str(nome_fantasia).strip():
            nome = str(nome_fantasia).strip()
        else:
            nome = str(razao_social).strip()
        
        # Limpa o nome (remove LTDA, S.A., etc se necessário)
        nome_clean = self.clean_company_name(nome)
        return nome_clean
    
    def clean_company_name(self, nome: str) -> str:
        """Limpa nome da empresa removendo sufixos desnecessários"""
        # Lista de sufixos para remover
        sufixes_remove = [
            ' LTDA', ' LTDA.', ' S.A.', ' S/A', ' SA', ' S.A', 
            ' EIRELI', ' ME', ' EPP', ' MICROEMPRESA', ' - ME',
            ' - EPP', ' - EIRELI', ' LIMITADA'
        ]
        
        nome_upper = nome.upper()
        for suffix in sufixes_remove:
            if nome_upper.endswith(suffix):
                nome = nome[:len(nome)-len(suffix)]
                break
        
        return nome.strip()
    
    def load_sent_emails(self) -> Dict:
        """Carrega histórico de emails enviados"""
        if os.path.exists(self.sent_log):
            with open(self.sent_log, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_sent_email(self, razao_social: str, email: str, priority: int):
        """Salva email como enviado"""
        sent_emails = self.load_sent_emails()
        sent_emails[razao_social] = {
            'email': email,
            'priority': priority,
            'sent_at': datetime.now().isoformat(),
            'status': 'sent'
        }
        with open(self.sent_log, 'w', encoding='utf-8') as f:
            json.dump(sent_emails, f, ensure_ascii=False, indent=2)
    
    def save_failed_email(self, razao_social: str, email: str, error: str):
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
    
    def create_personalized_email(self, recipient: str, nome_empresa: str, 
                                razao_social: str, subject_template: str, 
                                body_template: str, is_html: bool = False, 
                                attachment_path: str = None) -> MIMEMultipart:
        """Cria email personalizado para a empresa"""
        
        # Personaliza assunto
        subject = subject_template.format(
            empresa=nome_empresa,
            razao_social=razao_social
        )
        
        # Personaliza corpo
        body = body_template.format(
            empresa=nome_empresa,
            razao_social=razao_social,
            nome_empresa=nome_empresa  # alias para compatibilidade
        )
        
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Adiciona corpo
        if is_html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Adiciona anexo se especificado
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                
                # Nome do arquivo
                filename = os.path.basename(attachment_path)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
                
            self.logger.info(f"📎 Anexo adicionado: {filename}")
        
        return msg
    
    def send_single_email(self, recipient: str, nome_empresa: str, razao_social: str,
                         subject_template: str, body_template: str, 
                         is_html: bool = False, attachment_path: str = None) -> bool:
        """Envia um email individual personalizado"""
        try:
            msg = self.create_personalized_email(
                recipient, nome_empresa, razao_social, 
                subject_template, body_template, is_html, attachment_path
            )
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            self.logger.info(f"✅ Email enviado para {nome_empresa} ({recipient})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar para {nome_empresa} ({recipient}): {e}")
            self.save_failed_email(razao_social, recipient, str(e))
            return False
    
    def is_business_hours(self, start_time: str = "09:00", end_time: str = "17:00") -> bool:
        """Verifica se está no horário comercial"""
        current_time = datetime.now().time()
        start = datetime.strptime(start_time, "%H:%M").time()
        end = datetime.strptime(end_time, "%H:%M").time()
        return start <= current_time <= end
    
    def wait_until_business_hours(self, start_time: str = "09:00"):
        """Aguarda até o próximo horário comercial"""
        now = datetime.now()
        start = datetime.strptime(start_time, "%H:%M").time()
        
        if now.time() > start:
            # Próximo dia
            next_start = datetime.combine(
                now.date() + timedelta(days=1),
                start
            )
        else:
            # Hoje mesmo
            next_start = datetime.combine(now.date(), start)
        
        wait_seconds = (next_start - now).total_seconds()
        hours = wait_seconds / 3600
        
        self.logger.info(f"⏰ Aguardando horário comercial. Próximo envio: {next_start.strftime('%d/%m/%Y %H:%M')} ({hours:.1f}h)")
        time.sleep(wait_seconds)
    
    def send_bulk_emails_empresas(self, csv_file: str, subject_template: str, 
                                body_template: str, emails_per_day: int = 80,
                                delay_range: tuple = (60, 180), is_html: bool = False,
                                start_time: str = "09:00", end_time: str = "17:00",
                                enable_warmup: bool = True, attachment_path: str = None):
        """
        Envia emails para todas as empresas do CSV
        
        Args:
            csv_file: Arquivo CSV com dados das empresas
            subject_template: Template do assunto (use {empresa} e {razao_social})
            body_template: Template do corpo (use {empresa} e {razao_social})
            emails_per_day: Limite de emails por dia
            delay_range: Intervalo de delay entre emails (min, max) em segundos
            is_html: Se o corpo é HTML
            start_time: Horário de início dos envios (HH:MM)
            end_time: Horário de fim dos envios (HH:MM)
            enable_warmup: Se deve usar aquecimento gradual
            attachment_path: Caminho para arquivo anexo (PDF, DOC, etc.)
        """
        
        df = self.load_empresas_csv(csv_file)
        sent_emails = self.load_sent_emails()
        
        # Cronograma de aquecimento
        warmup_schedule = [5, 10, 15, 25, 35, 50, 70] if enable_warmup else []
        
        # Filtra empresas não contatadas
        remaining_companies = []
        for index, row in df.iterrows():
            razao_social = row['RazaoSocial']
            if razao_social not in sent_emails:
                email, priority = self.get_best_email(row)
                if email:
                    remaining_companies.append((index, row, email, priority))
        
        if not remaining_companies:
            self.logger.info("🎉 Todos os emails já foram enviados!")
            return
        
        self.logger.info(f"📧 Iniciando campanha para {len(remaining_companies)} empresas")
        if enable_warmup:
            self.logger.info("🔥 Modo aquecimento ativado - velocidade gradual")
        
        sent_today = 0
        last_reset = datetime.now().date()
        campaign_day = 1  # Contador de dias da campanha
        
        for index, row, email, priority in remaining_companies:
            razao_social = row['RazaoSocial']
            nome_empresa = self.get_nome_empresa(row)
            
            # Verifica horário comercial
            if not self.is_business_hours(start_time, end_time):
                self.wait_until_business_hours(start_time)
            
            # Reset contador diário
            current_date = datetime.now().date()
            if current_date > last_reset:
                sent_today = 0
                last_reset = current_date
                campaign_day += 1
                self.logger.info(f"📅 Novo dia: {current_date} (Dia {campaign_day} da campanha)")
            
            # Determina limite do dia (aquecimento ou normal)
            if enable_warmup and campaign_day <= len(warmup_schedule):
                daily_limit = warmup_schedule[campaign_day - 1]
                self.logger.info(f"🔥 Aquecimento dia {campaign_day}: {daily_limit} emails")
            else:
                daily_limit = emails_per_day
            
            # Verifica limite diário
            if sent_today >= daily_limit:
                tomorrow = datetime.combine(
                    datetime.now().date() + timedelta(days=1),
                    datetime.strptime(start_time, "%H:%M").time()
                )
                wait_seconds = (tomorrow - datetime.now()).total_seconds()
                
                if enable_warmup and campaign_day <= len(warmup_schedule):
                    self.logger.info(f"🔥 Limite de aquecimento atingido ({daily_limit} emails). Próximo dia: {daily_limit} → {warmup_schedule[min(campaign_day, len(warmup_schedule)-1)]}")
                else:
                    self.logger.info(f"🚫 Limite diário atingido ({daily_limit} emails)")
                
                self.logger.info(f"⏰ Aguardando até amanhã ({wait_seconds/3600:.1f}h)")
                time.sleep(wait_seconds)
                sent_today = 0
            
            # Delay maior durante aquecimento
            if enable_warmup and campaign_day <= 3:  # Primeiros 3 dias
                warmup_delay = (delay_range[0] * 2, delay_range[1] * 2)  # Delay 2x maior
                current_delay_range = warmup_delay
                self.logger.info(f"🔥 Modo aquecimento: delay extra ({current_delay_range[0]}-{current_delay_range[1]}s)")
            else:
                current_delay_range = delay_range
            
            # Envia o email
            self.logger.info(f"📤 Enviando para: {nome_empresa} | Email{priority}: {email}")
            
            success = self.send_single_email(
                email, nome_empresa, razao_social, 
                subject_template, body_template, is_html, attachment_path
            )
            
            if success:
                self.save_sent_email(razao_social, email, priority)
                sent_today += 1
                
                # Delay aleatório (maior durante aquecimento)
                delay = random.randint(current_delay_range[0], current_delay_range[1])
                self.logger.info(f"⏳ Aguardando {delay}s antes do próximo...")
                time.sleep(delay)
            else:
                # Delay menor em caso de erro
                time.sleep(30)
    
    def get_campaign_report(self, csv_file: str) -> Dict:
        """Gera relatório detalhado da campanha"""
        df = self.load_empresas_csv(csv_file)
        sent_emails = self.load_sent_emails()
        
        # Estatísticas gerais
        total_companies = len(df)
        companies_contacted = len(sent_emails)
        remaining = total_companies - companies_contacted
        
        # Análise de emails disponíveis
        email_stats = {'email1': 0, 'email2': 0, 'email3': 0, 'sem_email': 0}
        priority_sent = {'priority_1': 0, 'priority_2': 0, 'priority_3': 0}
        
        for _, row in df.iterrows():
            email, priority = self.get_best_email(row)
            if email:
                email_stats[f'email{priority}'] += 1
            else:
                email_stats['sem_email'] += 1
        
        # Prioridades dos emails enviados
        for data in sent_emails.values():
            priority = data.get('priority', 1)
            priority_sent[f'priority_{priority}'] += 1
        
        return {
            'campanha': {
                'total_empresas': total_companies,
                'emails_enviados': companies_contacted,
                'empresas_restantes': remaining,
                'percentual_concluido': round((companies_contacted / total_companies) * 100, 1) if total_companies > 0 else 0
            },
            'distribuicao_emails': email_stats,
            'prioridade_enviados': priority_sent,
            'empresas_sem_email': email_stats['sem_email']
        }
    
    def preview_personalization(self, csv_file: str, subject_template: str, 
                              body_template: str, num_samples: int = 3):
        """Mostra preview de como ficará a personalização"""
        df = self.load_empresas_csv(csv_file)
        
        print("🔍 PREVIEW DA PERSONALIZAÇÃO:")
        print("=" * 60)
        
        for i in range(min(num_samples, len(df))):
            row = df.iloc[i]
            nome_empresa = self.get_nome_empresa(row)
            razao_social = row['RazaoSocial']
            email, priority = self.get_best_email(row)
            
            if email:
                subject = subject_template.format(
                    empresa=nome_empresa,
                    razao_social=razao_social
                )
                
                body_preview = body_template.format(
                    empresa=nome_empresa,
                    razao_social=razao_social,
                    nome_empresa=nome_empresa
                )[:200] + "..."
                
                print(f"\n📧 EMPRESA {i+1}:")
                print(f"   Nome: {nome_empresa}")
                print(f"   Email{priority}: {email}")
                print(f"   Assunto: {subject}")
                print(f"   Corpo: {body_preview}")
                print("-" * 40)
    
    def pause_campaign(self):
        """Cria flag para pausar campanha"""
        with open('PAUSE_CAMPAIGN.flag', 'w') as f:
            f.write('PAUSED')
        self.logger.info("⏸️ Campanha pausada")
    
    def resume_campaign(self):
        """Remove flag de pausa"""
        if os.path.exists('PAUSE_CAMPAIGN.flag'):
            os.remove('PAUSE_CAMPAIGN.flag')
        self.logger.info("▶️ Campanha retomada")
    
    def is_campaign_paused(self) -> bool:
        """Verifica se campanha está pausada"""
        return os.path.exists('PAUSE_CAMPAIGN.flag')

# Configurações pré-definidas para diferentes provedores
SMTP_CONFIGS = {
    'gmail': {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'instructions': 'Use senha de app do Gmail, não a senha normal'
    },
    'outlook': {
        'smtp_server': 'smtp-mail.outlook.com', 
        'smtp_port': 587,
        'instructions': 'Use sua senha normal do Outlook'
    },
    'yahoo': {
        'smtp_server': 'smtp.mail.yahoo.com',
        'smtp_port': 587,
        'instructions': 'Ative "Acesso a apps menos seguros"'
    }
}

# Templates prontos para usar
TEMPLATES_PRONTOS = {
    'proposta_ai': {
        'subject': 'Proposta IA e Automação para {empresa} - 15min de conversa?',
        'body': '''Olá, equipe da {empresa}!

Espero que este email os encontre bem.

Sou especialista em Inteligência Artificial e Automações, e após pesquisar sobre a {empresa}, acredito que posso agregar valor significativo aos processos de vocês.

🤖 O que oferecemos:
• Automação de processos repetitivos (redução de até 60% do tempo manual)
• Sistemas de IA para análise de dados e tomada de decisão
• Chatbots inteligentes para atendimento ao cliente
• Integração de APIs e sistemas
• Dashboards automatizados e relatórios inteligentes

💡 Resultados já entregues para empresas similares:
• 40% de redução em custos operacionais
• 70% de melhoria na precisão de análises
• ROI médio de 250% em 8 meses

🎯 Proposta:
Que tal agendarmos 15 minutos para:
✓ Identificar oportunidades específicas na {empresa}
✓ Apresentar cases de sucesso do seu setor
✓ Demonstração prática (sem compromisso)

Quando seria um bom horário para vocês esta semana?

Atenciosamente,

[Seu Nome]
[Seu WhatsApp]
[Seu Email]
[Seu LinkedIn]

P.S.: Tenho cases específicos de empresas do seu segmento que podem interessar à {empresa}.

---
Para não receber mais emails, responda com "REMOVER".'''
    },
    
    'consultoria_tech': {
        'subject': 'Consultoria em Tecnologia para {empresa} - Café de 20min?',
        'body': '''Prezados da {empresa},

Como consultor em tecnologia, tenho acompanhado empresas do seu setor e acredito que posso contribuir com os desafios tecnológicos da {empresa}.

🚀 Áreas de especialização:
• Transformação digital e modernização de sistemas
• Arquitetura de software e cloud computing
• Implementação de metodologias ágeis
• Segurança da informação e compliance
• Otimização de performance e custos de TI

📊 Resultados recentes:
• 50% de redução em custos de infraestrutura
• 80% de melhoria na velocidade de deploy
• 99.9% de uptime em sistemas críticos

☕ Proposta:
Um café de 20 minutos para discutir:
✓ Principais desafios tecnológicos da {empresa}
✓ Oportunidades de otimização
✓ Roadmap estratégico personalizado

Qual seria um bom momento esta semana?

Cumprimentos,

[Seu Nome]
[Seu Telefone]
[Seu Email]

---
Para descadastrar, responda "REMOVER".'''
    }
}

# Exemplo de uso
if __name__ == "__main__":
    print("📧 Sistema de Email Marketing Empresarial")
    print("Use este módulo importando a classe EmailMarketingEmpresarial")
    print("Exemplo: from email_marketing_empresarial import EmailMarketingEmpresarial")