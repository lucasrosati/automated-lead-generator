#!/usr/bin/env python3
"""
Setup Automatizado - Sistema de Email Marketing Empresarial
Executa configuração completa e testes iniciais
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import subprocess

def install_dependencies():
    """Instala dependências necessárias"""
    print("📦 Instalando dependências...")
    
    dependencies = [
        'pandas',
        'python-dotenv'
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✅ {dep} instalado com sucesso")
        except subprocess.CalledProcessError:
            print(f"❌ Erro ao instalar {dep}")
            return False
    
    return True

def create_env_file():
    """Cria arquivo .env com configurações"""
    print("\n⚙️ Configurando arquivo .env...")
    
    print("\n🔧 Escolha seu provedor de email:")
    print("1. Gmail")
    print("2. Outlook/Hotmail") 
    print("3. Outro")
    
    choice = input("Digite sua escolha (1-3): ").strip()
    
    if choice == "1":
        smtp_server = "smtp.gmail.com"
        smtp_port = "587"
        provider = "Gmail"
    elif choice == "2":
        smtp_server = "smtp-mail.outlook.com"
        smtp_port = "587"
        provider = "Outlook"
    else:
        smtp_server = input("Digite o servidor SMTP: ").strip()
        smtp_port = input("Digite a porta SMTP (geralmente 587): ").strip()
        provider = "Personalizado"
    
    print(f"\n📧 Configurando {provider}...")
    email_user = input("Digite seu email: ").strip()
    
    if provider == "Gmail":
        print("\n🔑 Para Gmail, você precisa de uma SENHA DE APP:")
        print("1. Acesse https://myaccount.google.com")
        print("2. Vá em Segurança → Verificação em duas etapas")
        print("3. Ative a verificação em duas etapas")
        print("4. Vá em Senhas de app → Selecione 'Email' → 'Outro'")
        print("5. Digite 'Email Marketing Python' e copie a senha gerada")
    elif provider == "Outlook":
        print("\n🔑 Para Outlook, você pode usar:")
        print("1. Sua senha normal OU")
        print("2. Senha de aplicativo (mais seguro)")
        print("Para senha de app: account.microsoft.com → Segurança → Senhas de aplicativo")
    
    email_pass = input("Digite sua senha de app: ").strip()
    
    # Configurações avançadas
    print("\n⚡ Configurações de velocidade:")
    emails_per_day = input("Emails por dia (recomendado: 60-80): ").strip() or "70"
    delay_min = input("Delay mínimo entre emails em segundos (recomendado: 120): ").strip() or "120"
    delay_max = input("Delay máximo entre emails em segundos (recomendado: 300): ").strip() or "300"
    
    # Cria arquivo .env
    env_content = f"""# Configurações do Email Marketing
SMTP_SERVER={smtp_server}
SMTP_PORT={smtp_port}
EMAIL_USER={email_user}
EMAIL_PASS={email_pass}
EMAILS_PER_DAY={emails_per_day}
DELAY_MIN={delay_min}
DELAY_MAX={delay_max}
PROVIDER={provider}
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Arquivo .env criado com sucesso!")
    return True

def test_csv_file():
    """Testa se o arquivo CSV está no formato correto"""
    print("\n📄 Verificando arquivo CSV...")
    
    # Busca pelos novos nomes de arquivo
    csv_files = {
        'principal': 'contatos_proposta.csv',
        'teste': 'contatos_teste_proposta.csv'
    }
    
    # Verifica arquivo principal
    csv_file = csv_files['principal']
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo principal {csv_file} não encontrado!")
        print("📁 Certifique-se de que o arquivo CSV está na mesma pasta do script")
        return False
    
    # Verifica arquivo de teste (opcional)
    csv_test = csv_files['teste']
    if os.path.exists(csv_test):
        print(f"✅ Arquivo de teste encontrado: {csv_test}")
    else:
        print(f"⚠️ Arquivo de teste não encontrado: {csv_test} (opcional)")
    
    print(f"📋 Usando arquivo principal: {csv_file}")
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        # Verifica colunas obrigatórias
        required_cols = ['RazaoSocial', 'Email1']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"❌ Colunas obrigatórias faltando: {missing_cols}")
            print(f"📋 Colunas encontradas: {list(df.columns)}")
            return False
        
        # Estatísticas do arquivo
        total_companies = len(df)
        companies_with_email = len(df[df['Email1'].notna() & (df['Email1'] != '')])
        
        print(f"✅ CSV principal carregado com sucesso!")
        print(f"📊 Total de empresas: {total_companies}")
        print(f"📧 Empresas com Email1: {companies_with_email}")
        print(f"📋 Colunas: {list(df.columns)}")
        
        # Testa arquivo de teste se existir
        if os.path.exists(csv_test):
            try:
                df_test = pd.read_csv(csv_test, encoding='utf-8')
                print(f"✅ CSV de teste também carregado: {len(df_test)} empresas")
            except Exception as e:
                print(f"⚠️ Erro no CSV de teste: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar CSV: {e}")
        return False

def test_email_connection():
    """Testa conexão com o servidor de email"""
    print("\n🔌 Testando conexão com servidor de email...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import smtplib
        from email.mime.text import MIMEText
        
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT'))
        email_user = os.getenv('EMAIL_USER')
        email_pass = os.getenv('EMAIL_PASS')
        
        # Teste de conexão
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_pass)
        
        print("✅ Conexão com servidor estabelecida com sucesso!")
        
        # Teste de envio para si mesmo
        test_send = input("\n📧 Deseja enviar um email de teste para você mesmo? (s/n): ").strip().lower()
        
        if test_send == 's':
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_user, email_pass)
                
                msg = MIMEText("Este é um teste do sistema de email marketing. Se você recebeu este email, a configuração está funcionando!", 'plain', 'utf-8')
                msg['Subject'] = "Teste - Sistema Email Marketing"
                msg['From'] = email_user
                msg['To'] = email_user
                
                server.send_message(msg)
            
            print("✅ Email de teste enviado! Verifique sua caixa de entrada.")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print("\n🔧 Possíveis soluções:")
        print("1. Verifique se a senha de app está correta")
        print("2. Confirme se a verificação em duas etapas está ativa")
        print("3. Tente regenerar a senha de app")
        return False

def create_sample_template():
    """Cria arquivo com template de exemplo"""
    print("\n📝 Criando template de exemplo...")
    
    template = {
        "subject": "Proposta IA e Automação para {empresa} - 15min de conversa?",
        "body": """Olá, equipe da {empresa}!

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

[SEU NOME]
[SEU WHATSAPP]
[SEU EMAIL]
[SEU LINKEDIN]

P.S.: Tenho cases específicos de empresas do seu segmento que podem interessar à {empresa}.

---
Para não receber mais emails, responda com "REMOVER"."""
    }
    
    with open('template_email.json', 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    
    print("✅ Template criado em 'template_email.json'")
    print("📝 Você pode editá-lo antes de iniciar a campanha")

def create_launch_script():
    """Cria script de lançamento da campanha"""
    print("\n🚀 Criando script de lançamento...")
    
    launch_script = '''#!/usr/bin/env python3
"""
Script de Lançamento - Campanha Email Marketing
Execute este arquivo para iniciar sua campanha
"""

import os
import json
from dotenv import load_dotenv
from email_marketing_empresarial import EmailMarketingEmpresarial

def load_template():
    """Carrega template do email"""
    with open('template_email.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    print("🚀 INICIANDO CAMPANHA DE EMAIL MARKETING")
    print("=" * 50)
    
    # Carrega configurações
    load_dotenv()
    
    # Inicializa sistema
    email_system = EmailMarketingEmpresarial(
        smtp_server=os.getenv('SMTP_SERVER'),
        smtp_port=int(os.getenv('SMTP_PORT')),
        email=os.getenv('EMAIL_USER'),
        password=os.getenv('EMAIL_PASS')
    )
    
    # Carrega template
    template = load_template()
    
    # Mostra preview
    print("\\n🔍 PREVIEW DA PERSONALIZAÇÃO:")
    email_system.preview_personalization(
        'contatos_proposta.csv',  # Nome atualizado
        template['subject'],
        template['body'],
        num_samples=3
    )
    
    # Relatório inicial
    report = email_system.get_campaign_report('contatos_proposta.csv')  # Nome atualizado
    print("\\n📊 RELATÓRIO INICIAL:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # Confirmação
    confirm = input("\\n✅ Tudo certo? Iniciar campanha? (s/n): ").strip().lower()
    
    if confirm == 's':
        print("\\n🚀 Iniciando campanha...")
        
        # Inicia campanha
        email_system.send_bulk_emails_empresas(
            csv_file='contatos_proposta.csv',  # Nome atualizado
            subject_template=template['subject'],
            body_template=template['body'],
            emails_per_day=int(os.getenv('EMAILS_PER_DAY', 70)),
            delay_range=(int(os.getenv('DELAY_MIN', 120)), int(os.getenv('DELAY_MAX', 300))),
            start_time="09:00",
            end_time="17:00",
            is_html=False
        )
        
        print("\\n🎉 Campanha concluída!")
        
        # Relatório final
        final_report = email_system.get_campaign_report('contatos_proposta.csv')  # Nome atualizado
        print("\\n📊 RELATÓRIO FINAL:")
        print(json.dumps(final_report, indent=2, ensure_ascii=False))
    else:
        print("\\n❌ Campanha cancelada.")

if __name__ == "__main__":
    main()
'''
    
    with open('iniciar_campanha.py', 'w', encoding='utf-8') as f:
        f.write(launch_script)
    
    print("✅ Script de lançamento criado: 'iniciar_campanha.py'")

def show_next_steps():
    """Mostra próximos passos"""
    print("\n" + "="*60)
    print("🎉 SETUP CONCLUÍDO COM SUCESSO!")
    print("="*60)
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. ✏️  Edite o template em 'template_email.json' se necessário")
    print("2. 🔍 Execute 'python iniciar_campanha.py' para ver preview")
    print("3. 🚀 Confirme e inicie a campanha")
    print("4. 📊 Monitore os logs em 'email_marketing_empresarial.log'")
    
    print("\n📁 ARQUIVOS CRIADOS:")
    files_created = [
        ".env - Configurações do email",
        "template_email.json - Template da mensagem", 
        "iniciar_campanha.py - Script para iniciar",
        "email_marketing_empresarial.py - Sistema principal"
    ]
    
    for file in files_created:
        print(f"  ✅ {file}")
    
    print("\n⚠️  LEMBRETE IMPORTANTE:")
    print("• Mantenha os arquivos .env e .json seguros")
    print("• Faça backup do progresso regularmente")
    print("• Monitore a taxa de resposta e ajuste se necessário")
    
    print("\n🆘 SUPORTE:")
    print("• Logs detalhados em: email_marketing_empresarial.log")
    print("• Progresso salvo em: emails_enviados_empresas.json")
    print("• Falhas registradas em: emails_falharam.json")

def main():
    """Função principal do setup"""
    print("🔧 SETUP AUTOMÁTICO - EMAIL MARKETING EMPRESARIAL")
    print("="*55)
    print("Este script vai configurar tudo para você!")
    print("Tempo estimado: 5-10 minutos")
    print()
    
    # Etapa 1: Dependências
    if not install_dependencies():
        print("❌ Falha na instalação de dependências")
        return
    
    # Etapa 2: Arquivo .env
    if not create_env_file():
        print("❌ Falha na criação do arquivo .env")
        return
    
    # Etapa 3: Teste CSV
    if not test_csv_file():
        print("❌ Problema com arquivo CSV")
        return
    
    # Etapa 4: Teste conexão
    if not test_email_connection():
        print("❌ Problema na conexão de email")
        return
    
    # Etapa 5: Template
    create_sample_template()
    
    # Etapa 6: Script de lançamento
    create_launch_script()
    
    # Etapa 7: Próximos passos
    show_next_steps()

if __name__ == "__main__":
    main()