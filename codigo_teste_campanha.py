#!/usr/bin/env python3
"""
CÓDIGO DE TESTE - Email Marketing Empresarial
Para testar com a planilha: contatos_teste_proposta  contatos_teste_proposta.csv.csv
"""

import pandas as pd
import smtplib
import time
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

class EmailMarketingTeste:
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.test_log = "teste_emails_enviados.json"
        
    def load_test_csv(self, file_path: str) -> pd.DataFrame:
        """Carrega planilha de teste"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            print(f"✅ CSV de teste carregado: {len(df)} empresas")
            print(f"📋 Colunas: {list(df.columns)}")
            return df
        except Exception as e:
            print(f"❌ Erro ao carregar CSV: {e}")
            raise
    
    def get_best_email_test(self, row: pd.Series) -> tuple:
        """Retorna melhor email para teste"""
        emails_to_check = [
            (row.get('Email1'), 1),
            (row.get('Email2'), 2), 
            (row.get('Email3'), 3)
        ]
        
        for email, priority in emails_to_check:
            if pd.notna(email) and email and '@' in str(email):
                return str(email).strip(), priority
        
        return None, 0
    
    def get_nome_empresa_test(self, row: pd.Series) -> str:
        """Extrai nome da empresa para teste"""
        nome_fantasia = row.get('NomeFantasia')
        razao_social = row.get('RazaoSocial')
        
        if pd.notna(nome_fantasia) and str(nome_fantasia).strip():
            return str(nome_fantasia).strip()
        else:
            return str(razao_social).strip()
    
    def preview_all_personalizations(self, csv_file: str, subject_template: str, body_template: str):
        """Mostra preview de TODAS as empresas do teste"""
        df = self.load_test_csv(csv_file)
        
        print("\n" + "="*80)
        print("🔍 PREVIEW COMPLETO - TODAS AS EMPRESAS DE TESTE")
        print("="*80)
        
        for index, row in df.iterrows():
            nome_empresa = self.get_nome_empresa_test(row)
            razao_social = row['RazaoSocial']
            email, priority = self.get_best_email_test(row)
            
            print(f"\n📧 EMPRESA {index + 1}:")
            print(f"   Razão Social: {razao_social}")
            print(f"   Nome Fantasia: {row.get('NomeFantasia', 'N/A')}")
            print(f"   Nome Usado: {nome_empresa}")
            print(f"   Email{priority}: {email if email else '❌ SEM EMAIL VÁLIDO'}")
            
            if email:
                # Personaliza assunto e corpo
                subject_personalizado = subject_template.format(
                    empresa=nome_empresa,
                    razao_social=razao_social
                )
                
                body_preview = body_template.format(
                    empresa=nome_empresa,
                    razao_social=razao_social,
                    nome_empresa=nome_empresa
                )[:300] + "..."
                
                print(f"   📮 Assunto: {subject_personalizado}")
                print(f"   📝 Corpo (preview): {body_preview}")
            
            print("-" * 60)
    
    def send_test_email(self, recipient: str, nome_empresa: str, razao_social: str, 
                       subject_template: str, body_template: str) -> bool:
        """Envia um email de teste"""
        try:
            # Personaliza conteúdo
            subject = subject_template.format(
                empresa=nome_empresa,
                razao_social=razao_social
            )
            
            body = body_template.format(
                empresa=nome_empresa,
                razao_social=razao_social,
                nome_empresa=nome_empresa
            )
            
            # Adiciona marcação de teste no assunto e corpo
            subject = f"[TESTE] {subject}"
            body = f"🧪 ESTE É UM EMAIL DE TESTE 🧪\n\n{body}\n\n---\n⚠️ Este email foi enviado como teste do sistema de marketing automatizado."
            
            # Cria mensagem
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Envia
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            print(f"✅ Teste enviado para: {nome_empresa} ({recipient})")
            return True
            
        except Exception as e:
            print(f"❌ Erro no teste para {nome_empresa} ({recipient}): {e}")
            return False
    
    def run_test_campaign(self, csv_file: str, subject_template: str, body_template: str, 
                         send_emails: bool = False, delay_seconds: int = 10):
        """
        Executa campanha de teste
        
        Args:
            csv_file: Arquivo CSV de teste
            subject_template: Template do assunto
            body_template: Template do corpo
            send_emails: Se True, realmente envia emails. Se False, apenas simula
            delay_seconds: Delay entre emails de teste
        """
        df = self.load_test_csv(csv_file)
        
        print(f"\n🚀 {'ENVIANDO' if send_emails else 'SIMULANDO'} CAMPANHA DE TESTE")
        print(f"📊 Total de empresas: {len(df)}")
        print(f"⏱️ Delay entre envios: {delay_seconds}s")
        print("="*60)
        
        results = {
            'total_empresas': len(df),
            'enviados_sucesso': 0,
            'falharam': 0,
            'sem_email': 0,
            'detalhes': []
        }
        
        for index, row in df.iterrows():
            nome_empresa = self.get_nome_empresa_test(row)
            razao_social = row['RazaoSocial']
            email, priority = self.get_best_email_test(row)
            
            print(f"\n📤 Processando {index + 1}/{len(df)}: {nome_empresa}")
            
            if not email:
                print(f"⚠️ {nome_empresa}: SEM EMAIL VÁLIDO")
                results['sem_email'] += 1
                results['detalhes'].append({
                    'empresa': nome_empresa,
                    'status': 'sem_email',
                    'email': None
                })
                continue
            
            if send_emails:
                print(f"📧 Enviando para: {email}")
                success = self.send_test_email(
                    email, nome_empresa, razao_social, 
                    subject_template, body_template
                )
                
                if success:
                    results['enviados_sucesso'] += 1
                    results['detalhes'].append({
                        'empresa': nome_empresa,
                        'status': 'enviado',
                        'email': email,
                        'prioridade': priority
                    })
                else:
                    results['falharam'] += 1
                    results['detalhes'].append({
                        'empresa': nome_empresa,
                        'status': 'falhou',
                        'email': email
                    })
                
                if index < len(df) - 1:  # Se não é o último
                    print(f"⏳ Aguardando {delay_seconds}s...")
                    time.sleep(delay_seconds)
            else:
                print(f"✅ SIMULAR: Enviaria para {email} (Email{priority})")
                results['enviados_sucesso'] += 1
                results['detalhes'].append({
                    'empresa': nome_empresa,
                    'status': 'simulado',
                    'email': email,
                    'prioridade': priority
                })
        
        # Salva resultados
        with open(self.test_log, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Relatório final
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL DO TESTE")
        print("="*60)
        print(f"📈 Total de empresas: {results['total_empresas']}")
        print(f"✅ Enviados com sucesso: {results['enviados_sucesso']}")
        print(f"❌ Falharam: {results['falharam']}")
        print(f"⚠️ Sem email: {results['sem_email']}")
        
        if results['enviados_sucesso'] > 0:
            print(f"🎯 Taxa de sucesso: {(results['enviados_sucesso']/results['total_empresas'])*100:.1f}%")
        
        print(f"\n📄 Relatório detalhado salvo em: {self.test_log}")
        
        return results

def main():
    """Função principal para executar os testes"""
    print("🧪 SISTEMA DE TESTE - EMAIL MARKETING")
    print("="*50)
    
    # Carrega configurações com limpeza de cache
    import os
    
    # Limpar variáveis antigas do ambiente
    for key in list(os.environ.keys()):
        if key.startswith(('EMAIL_', 'SMTP_')):
            del os.environ[key]
    
    # Recarregar .env
    load_dotenv('.env', override=True)
    
    # Configurações de teste
    EMAIL_CONFIG = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'email': os.getenv('EMAIL_USER'),
        'password': os.getenv('EMAIL_PASS')
    }
    
    # Debug: mostrar configurações carregadas
    print(f"\n🔧 Configurações carregadas:")
    print(f"Email: {EMAIL_CONFIG['email']}")
    print(f"Senha: {EMAIL_CONFIG['password'][:4] if EMAIL_CONFIG['password'] else 'None'}****{EMAIL_CONFIG['password'][-4:] if EMAIL_CONFIG['password'] else 'None'}")
    
    # Verifica se configurações existem
    if not EMAIL_CONFIG['email'] or not EMAIL_CONFIG['password']:
        print("❌ Configurações de email não encontradas!")
        print("📝 Problema no carregamento do .env")
        return
    
    # Teste rápido de autenticação
    print("\n🔌 Testando autenticação...")
    try:
        import smtplib
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        print("✅ Autenticação OK!")
    except Exception as e:
        print(f"❌ Erro de autenticação: {e}")
        print("🔧 Execute: rm .env && python3 setup_automatico.py")
        return
    
    # Template de teste
    SUBJECT_TEST = "Proposta IA para {empresa} - Teste do Sistema"
    
    BODY_TEST = """Olá, equipe da {empresa}!

Este é um email de teste do nosso sistema de marketing automatizado.

🤖 Testando personalização:
• Nome da empresa: {empresa}
• Razão social: {razao_social}

Se você recebeu este email, significa que:
✅ A personalização está funcionando
✅ O sistema está enviando corretamente
✅ Sua configuração de email está OK

Este é apenas um teste - ignore este email.

Atenciosamente,
Sistema de Teste de Email Marketing

---
⚠️ Este é um email de teste automatizado."""
    
    # Arquivo CSV de teste
    CSV_TESTE = 'contatos_teste_proposta.csv'
    
    # Inicializa sistema de teste
    teste_system = EmailMarketingTeste(**EMAIL_CONFIG)
    
    print("\n1️⃣ PREVIEW DAS PERSONALIZAÇÕES:")
    teste_system.preview_all_personalizations(CSV_TESTE, SUBJECT_TEST, BODY_TEST)
    
    print("\n2️⃣ ESCOLHA O TIPO DE TESTE:")
    print("1. Apenas simular (não envia emails)")
    print("2. Enviar emails de teste (realmente envia)")
    
    choice = input("\nDigite sua escolha (1 ou 2): ").strip()
    
    if choice == "1":
        print("\n🎭 EXECUTANDO SIMULAÇÃO...")
        teste_system.run_test_campaign(
            CSV_TESTE, SUBJECT_TEST, BODY_TEST, 
            send_emails=False
        )
    elif choice == "2":
        confirm = input("\n⚠️ Tem certeza que quer enviar emails reais? (s/n): ").strip().lower()
        if confirm == 's':
            print("\n📧 ENVIANDO EMAILS DE TESTE...")
            teste_system.run_test_campaign(
                CSV_TESTE, SUBJECT_TEST, BODY_TEST,
                send_emails=True,
                delay_seconds=15  # 15 segundos entre emails
            )
        else:
            print("❌ Teste cancelado.")
    else:
        print("❌ Opção inválida.")

if __name__ == "__main__":
    main()