#!/usr/bin/env python3
"""
TESTE ANTI-SPAM OTIMIZADO - 8 Empresas
Configurado especificamente para evitar spam
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

class TesteAntiSpam:
    def __init__(self):
        # Limpar cache .env
        for key in list(os.environ.keys()):
            if key.startswith(('EMAIL_', 'SMTP_')):
                del os.environ[key]
        
        # Recarregar .env
        load_dotenv('.env', override=True)
        
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.email = os.getenv('EMAIL_USER')
        self.password = os.getenv('EMAIL_PASS')
        
        print(f"📧 Usando email: {self.email}")
        print(f"🔑 Senha carregada: {self.password[:4]}****{self.password[-4:]}")
    
    def create_antispam_email(self, recipient: str, nome_empresa: str) -> MIMEMultipart:
        """Cria email otimizado anti-spam"""
        
        # Template MUITO casual e menos comercial
        subject = f"Conversa sobre tecnologia - {nome_empresa}"
        
        body = f"""Olá, equipe da {nome_empresa}!

Espero que vocês estejam bem.

Tenho trabalhado com algumas empresas na implementação de soluções tecnológicas e notei alguns resultados interessantes que podem ser relevantes para a {nome_empresa}.

Algumas áreas onde temos ajudado:
• Otimização de processos através de automação
• Análise de dados para melhor tomada de decisão  
• Integração de sistemas e APIs
• Implementação de dashboards inteligentes

Recentemente, empresas similares conseguiram:
• Reduzir significativamente o tempo em tarefas repetitivas
• Melhorar a precisão de análises e relatórios
• Otimizar custos operacionais

Acredito que pode haver oportunidades interessantes para a {nome_empresa} também.

Que tal trocarmos uma ideia sobre isso? Posso compartilhar alguns exemplos específicos do setor de vocês.

Disponível para uma conversa rápida quando for conveniente.

Cumprimentos,

Lucas Rosati
Especialista em IA e Automação
WhatsApp: [Seu número]
Email: {self.email}

P.S.: Se preferirem, posso enviar alguns casos de estudo relevantes ao segmento da {nome_empresa}.

---
Para não receber mais contatos como este, basta responder "remover"."""

        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Adicionar cabeçalhos anti-spam
        msg['Reply-To'] = self.email
        msg['Message-ID'] = f"<{datetime.now().strftime('%Y%m%d%H%M%S')}.{recipient.split('@')[0]}@automated-lead-generator>"
        
        # Corpo do email
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        return msg
    
    def send_single_antispam_email(self, recipient: str, nome_empresa: str) -> bool:
        """Envia um email com máxima otimização anti-spam"""
        try:
            msg = self.create_antispam_email(recipient, nome_empresa)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            print(f"✅ Email enviado para: {nome_empresa} ({recipient})")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar para {nome_empresa} ({recipient}): {e}")
            return False
    
    def run_antispam_test(self):
        """Executa teste com configurações anti-spam máximas"""
        
        # Carregar dados
        df = pd.read_csv('contatos_teste_proposta.csv', encoding='utf-8')
        
        print("🛡️ TESTE ANTI-SPAM OTIMIZADO")
        print("="*50)
        print(f"📊 Total de empresas: {len(df)}")
        print("⏱️ Delay: 5 minutos entre cada email")
        print("🎯 Objetivo: 100% na caixa de entrada")
        print("📧 Template: Casual e menos comercial")
        print("🔍 Cabeçalhos: Otimizados anti-spam")
        print()
        
        # Preview dos emails
        print("🔍 PREVIEW DOS EMAILS:")
        print("-" * 30)
        for i, row in df.iterrows():
            nome = row['NomeFantasia'] or row['RazaoSocial']
            email = row['Email1']
            print(f"{i+1}. {nome} → {email}")
        print()
        
        # Confirmação
        confirm = input("🚀 Iniciar teste anti-spam? (s/n): ").strip().lower()
        if confirm != 's':
            print("❌ Teste cancelado")
            return
        
        print("\n📧 INICIANDO ENVIOS COM DELAY DE 5 MINUTOS...")
        print("="*50)
        
        results = {
            'enviados': 0,
            'falharam': 0,
            'detalhes': []
        }
        
        # Tempo estimado
        total_time = (len(df) - 1) * 5  # 5 min entre emails
        print(f"⏰ Tempo estimado total: {total_time} minutos ({total_time/60:.1f} horas)")
        print()
        
        for i, row in df.iterrows():
            nome = row['NomeFantasia'] or row['RazaoSocial']
            email = row['Email1']
            
            print(f"📤 [{datetime.now().strftime('%H:%M:%S')}] Enviando {i+1}/{len(df)}: {nome}")
            
            success = self.send_single_antispam_email(email, nome)
            
            if success:
                results['enviados'] += 1
                results['detalhes'].append({
                    'empresa': nome,
                    'email': email,
                    'status': 'enviado',
                    'horario': datetime.now().isoformat()
                })
            else:
                results['falharam'] += 1
                results['detalhes'].append({
                    'empresa': nome,
                    'email': email,
                    'status': 'falhou',
                    'horario': datetime.now().isoformat()
                })
            
            # Delay de 5 minutos entre emails (exceto último)
            if i < len(df) - 1:
                print(f"⏳ Aguardando 5 minutos antes do próximo email...")
                print(f"🕐 Próximo envio: {datetime.now().strftime('%H:%M:%S')} + 5min")
                print("-" * 40)
                time.sleep(300)  # 5 minutos = 300 segundos
        
        # Relatório final
        print("\n" + "="*50)
        print("📊 RELATÓRIO FINAL - TESTE ANTI-SPAM")
        print("="*50)
        print(f"✅ Enviados com sucesso: {results['enviados']}")
        print(f"❌ Falharam: {results['falharam']}")
        print(f"🎯 Taxa de sucesso: {(results['enviados']/len(df))*100:.1f}%")
        
        # Salvar resultados
        with open('teste_antispam_resultados.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Resultados salvos em: teste_antispam_resultados.json")
        
        # Instruções pós-teste
        print("\n🔍 INSTRUÇÕES PÓS-TESTE:")
        print("1. Aguarde 10-15 minutos")
        print("2. Verifique TODAS as caixas de entrada:")
        print("   📧 Caixa principal")
        print("   📧 Pasta de spam")
        print("   📧 Pasta de promoções (Gmail)")
        print("3. Relate quantos chegaram na caixa principal")
        
        return results

def main():
    print("🛡️ SISTEMA DE TESTE ANTI-SPAM")
    print("Otimizado para máxima entrega na caixa de entrada")
    print("="*60)
    
    # Testar configurações primeiro
    teste = TesteAntiSpam()
    
    if not teste.email or not teste.password:
        print("❌ Configurações de email não encontradas!")
        print("Execute: python3 -c \"from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('EMAIL_USER'))\"")
        return
    
    # Teste rápido de autenticação
    print("\n🔌 Testando autenticação...")
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(teste.email, teste.password)
        print("✅ Autenticação OK!")
    except Exception as e:
        print(f"❌ Erro de autenticação: {e}")
        return
    
    # Executar teste
    teste.run_antispam_test()

if __name__ == "__main__":
    main()