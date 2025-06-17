#!/usr/bin/env python3
"""
Script de Lançamento - Campanha Email Marketing com Anexos
Execute este arquivo para iniciar sua campanha
"""

import os
import json
import glob
from dotenv import load_dotenv
from email_marketing_empresarial import EmailMarketingEmpresarial

def load_template():
    """Carrega template do email"""
    with open('template_email.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def find_attachments():
    """Busca por possíveis anexos na pasta"""
    # Extensões suportadas
    extensions = ['*.pdf', '*.doc', '*.docx', '*.ppt', '*.pptx', '*.jpg', '*.png', '*.zip']
    
    attachments = []
    for ext in extensions:
        attachments.extend(glob.glob(ext))
    
    return attachments

def select_attachment():
    """Permite selecionar um anexo"""
    attachments = find_attachments()
    
    if not attachments:
        print("📎 Nenhum arquivo de anexo encontrado na pasta")
        print("💡 Coloque arquivos PDF, DOC, PPT, etc. na pasta do projeto")
        return None
    
    print("\n📎 ANEXOS DISPONÍVEIS:")
    print("0. Sem anexo")
    
    for i, file in enumerate(attachments, 1):
        size_mb = os.path.getsize(file) / (1024 * 1024)
        print(f"{i}. {file} ({size_mb:.1f}MB)")
    
    try:
        choice = int(input("\nEscolha o anexo (número): "))
        if choice == 0:
            return None
        elif 1 <= choice <= len(attachments):
            selected = attachments[choice - 1]
            size_mb = os.path.getsize(selected) / (1024 * 1024)
            
            # Verificar tamanho (Gmail = 25MB max)
            if size_mb > 25:
                print(f"⚠️ Arquivo muito grande ({size_mb:.1f}MB). Gmail limita a 25MB.")
                return None
            
            print(f"✅ Anexo selecionado: {selected}")
            return selected
        else:
            print("❌ Opção inválida")
            return None
    except ValueError:
        print("❌ Entrada inválida")
        return None

def main():
    print("🚀 INICIANDO CAMPANHA DE EMAIL MARKETING")
    print("=" * 50)
    
    # Limpar cache .env
    for key in list(os.environ.keys()):
        if key.startswith(('EMAIL_', 'SMTP_')):
            del os.environ[key]
    
    # Carrega configurações
    load_dotenv('.env', override=True)
    
    # Inicializa sistema
    email_system = EmailMarketingEmpresarial(
        smtp_server=os.getenv('SMTP_SERVER'),
        smtp_port=int(os.getenv('SMTP_PORT')),
        email=os.getenv('EMAIL_USER'),
        password=os.getenv('EMAIL_PASS')
    )
    
    # Carrega template
    template = load_template()
    
    # Seleção de anexo
    attachment = select_attachment()
    
    # Mostra preview
    print("\n🔍 PREVIEW DA PERSONALIZAÇÃO:")
    email_system.preview_personalization(
        'contatos_proposta.csv',
        template['subject'],
        template['body'],
        num_samples=3
    )
    
    # Mostra anexo selecionado
    if attachment:
        print(f"\n📎 ANEXO CONFIGURADO: {attachment}")
    else:
        print("\n📧 SEM ANEXO - Apenas texto")
    
    # Relatório inicial
    report = email_system.get_campaign_report('contatos_proposta.csv')
    print("\n📊 RELATÓRIO INICIAL:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # Configurações da campanha
    print("\n⚙️ CONFIGURAÇÕES DA CAMPANHA:")
    print(f"📧 Emails por dia: {os.getenv('EMAILS_PER_DAY', 70)}")
    print(f"⏱️ Delay: {os.getenv('DELAY_MIN', 150)}-{os.getenv('DELAY_MAX', 300)}s")
    print(f"🔥 Aquecimento: Ativado (5→10→15→25→35→50→70)")
    print(f"🕐 Horário: 09:00-17:00")
    
    # Confirmação
    print("\n" + "="*50)
    confirm = input("✅ Tudo certo? Iniciar campanha? (s/n): ").strip().lower()
    
    if confirm == 's':
        print("\n🚀 Iniciando campanha com aquecimento automático...")
        
        # Inicia campanha
        email_system.send_bulk_emails_empresas(
            csv_file='contatos_proposta.csv',
            subject_template=template['subject'],
            body_template=template['body'],
            emails_per_day=int(os.getenv('EMAILS_PER_DAY', 70)),
            delay_range=(int(os.getenv('DELAY_MIN', 150)), int(os.getenv('DELAY_MAX', 300))),
            start_time="09:00",
            end_time="17:00",
            is_html=False,
            enable_warmup=True,
            attachment_path=attachment
        )
        
        print("\n🎉 Campanha concluída!")
        
        # Relatório final
        final_report = email_system.get_campaign_report('contatos_proposta.csv')
        print("\n📊 RELATÓRIO FINAL:")
        print(json.dumps(final_report, indent=2, ensure_ascii=False))
    else:
        print("\n❌ Campanha cancelada.")

if __name__ == "__main__":
    main()