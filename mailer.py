import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
from logger import logger

load_dotenv()

def send_email(new_items):
    """Yeni kayıtları listedeki her alıcıya gönderir."""
    sender = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    receiver_raw = os.getenv('EMAIL_RECEIVER', "")
    sender_email = os.getenv('SENDER_EMAIL', "melih@heom.com.tr")
    
    receiver_list = [email.strip() for email in receiver_raw.split(',') if email.strip()]
    
    if not all([sender, password, receiver_list]):
        logger.error("E-posta ayarları veya alıcı listesi eksik.")
        return

    # Jinja2 template render
    try:
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('email_template.html')
        full_html = template.render(items=new_items)
    except Exception as e:
        logger.error(f"Şablon oluşturma hatası: {e}")
        return

    try:
        with smtplib.SMTP('smtp-relay.brevo.com', 587) as server:
            logger.info(f"Brevo sunucusuna {sender} ile bağlanılıyor...")
            server.starttls()
            server.login(sender, password)
            
            for recipient in receiver_list:
                msg = MIMEMultipart("alternative")
                msg['From'] = f"Vefat Takip Sistemi <{sender_email}>"
                msg['To'] = recipient
                msg['Subject'] = f"Vefat Bildirim Mesajı - {len(new_items)} adet yeni vefat bildirimi."
                
                msg.attach(MIMEText(full_html, 'html', 'utf-8'))
                
                server.sendmail(sender, recipient, msg.as_string())
                logger.info(f"E-posta başarıyla gönderildi: {recipient}")
                
        logger.info(f"Toplam {len(receiver_list)} kişiye gönderim tamamlandı.")
        
    except Exception as e:
        logger.error(f"Gönderim hatası: {e}")
