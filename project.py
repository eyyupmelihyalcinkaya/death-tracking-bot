import os
import requests
import smtplib
import json
from bs4 import BeautifulSoup
from supabase import create_client
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# .env dosyasını yükler (Lokalde çalışırken)
load_dotenv()

# Yapılandırma ve Bağlantılar
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_notables(text):
    if not text:
        return "Belirtilmemiş"
    
    first_sentence = text.split('.')[0]
    
    # Türkçe küçük harf dönüşümü yapar (İ -> i, I -> ı) [İlimiz kelimesini doğru ayıramadığı için]
    def tr_lower(metin):
        return metin.replace('İ', 'i').replace('I', 'ı').lower()

    # Kontrol için metni küçük harfe çevirir
    temp_sentence = tr_lower(first_sentence)
    keyword = "eşrafından"
    
    if keyword in temp_sentence:
        # "eşrafından" kelimesinden öncesini alır
        origin_part = temp_sentence.split(keyword)[0].strip()
        
        if "ilimiz" in origin_part:
            return "Erzincan"
        else:
            # Eğer ilimiz değilse, orijinal cümleden o kısmı bulup baş harflerini düzeltir
            # (Regex kullanarak "eşrafından" kelimesine kadar olan kısmı orijinal metinden alıyor)
            import re
            match = re.search(re.escape(keyword), first_sentence, re.IGNORECASE)
            if match:
                raw_origin = first_sentence[:match.start()].strip()
                return raw_origin.title()
            return origin_part.title()
            
    return "Belirtilmemiş"

def send_email(new_items):
    """Yeni kayıtları listedeki her alıcıya birbirini görmeyecek şekilde ayrı ayrı gönderir."""
    sender = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    receiver_raw = os.getenv('EMAIL_RECEIVER', "")
    # Virgülle ayrılmış metni temiz bir listeye çeviriyoruz
    receiver_list = [email.strip() for email in receiver_raw.split(',') if email.strip()]
    
    if not all([sender, password, receiver_list]):
        print("E-posta ayarları veya alıcı listesi eksik.")
        return

    # HTML İçeriğini döngü dışında bir kez hazırlıyoruz (performans için)
    html_content_header = f"""
    <html>
    <head>
        <style>
            .container {{ font-family: 'Georgia', serif; color: #333; max-width: 600px; margin: 0 auto; padding: 0; background-color: #f9f9f9; border: 1px solid #e0e0e0; }}
            .top-banner {{ background-color: #1a252f; color: #d4af37; padding: 30px 20px; text-align: center; border-bottom: 4px solid #d4af37; }}
            .arabic-text {{ font-size: 26px; margin-bottom: 10px; font-weight: normal; }}
            .turkish-text {{ font-size: 18px; font-style: italic; opacity: 0.9; letter-spacing: 1px; }}
            .content-area {{ padding: 20px; }}
            .system-title {{ text-align: center; color: #2c3e50; font-size: 16px; margin-bottom: 20px; text-transform: uppercase; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            .card {{ background-color: #ffffff; padding: 20px; margin-bottom: 20px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #d4af37; }}
            .name {{ color: #1a252f; font-size: 20px; font-weight: bold; margin-bottom: 10px; }}
            .info-row {{ display: table; width: 100%; margin: 5px 0; }}
            .label {{ display: table-cell; width: 140px; font-weight: bold; color: #7f8c8d; font-size: 13px; }}
            .value {{ display: table-cell; color: #2c3e50; font-size: 14px; line-height: 1.5; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #95a5a6; background-color: #f1f1f1; }}
            .button {{ display: inline-block; padding: 12px 25px; background-color: #1a252f; color: #d4af37 !important; text-decoration: none; border-radius: 3px; margin-top: 15px; font-weight: bold; border: 1px solid #d4af37; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="top-banner">
                <div class="arabic-text">إِنَّا لِلَّٰهِ وَإِنَّا إِلَيْهِ رَاجِعُونَ</div>
                <div class="turkish-text">İnnâ lillâhi ve innâ ileyhi raciûn</div>
            </div>
            <div class="content-area">
                <div class="system-title">Erzincan Belediyesi Vefat Bilgilendirme</div>
    """

    cards_html = ""
    for item in new_items:
        cards_html += f"""
                <div class="card">
                    <div class="name">🕊️ {item['name']} {item['surname']}</div>
                    <div class="info-row"><div class="label">Baba Adı:</div><div class="value">{item['fathers_name']}</div></div>
                    <div class="info-row"><div class="label">Anons Metni:</div><div class="value">{item['announcement_text']}</div></div>
                    <div class="info-row"><div class="label">Eşraf:</div><div class="value">{item['notables_information']}</div></div>
                    <div class="info-row"><div class="label">Doğum Bilgisi:</div><div class="value">{item['place_of_birth']}</div></div>
                    <div class="info-row"><div class="label">Defin Tarihi:</div><div class="value">{item['date_of_burial']}</div></div>
                    <div class="info-row"><div class="label">Vakit/Yer:</div><div class="value">{item['burial_place_date_info']}</div></div>
                    <div class="info-row"><div class="label">İletişim:</div><div class="value">{item['communication_info']}</div></div>
                </div>
        """

    html_content_footer = """
                <div style="text-align: center; margin-top: 30px; padding-bottom: 20px; border-bottom: 1px dashed #ddd;">
                    <a href="https://www.erzincan.bel.tr/vefatedenler" class="button" style="background-color: #1a252f; color: #d4af37;">Belediye Listesini Görüntüle</a>
                </div>
            </div> <div class="footer" style="padding: 30px 20px; background-color: #f8f9fa;">
                <p style="margin-bottom: 10px;">Bu e-posta otomatik takip sistemi tarafından üretilmiştir.</p>
                <p style="font-weight: bold; margin-bottom: 5px;">© 2026 Vefat Takip Sistemi</p>
                
                <div style="margin-top: 15px; font-size: 11px; line-height: 1.6; color: #7f8c8d;">
                    Bu proje <strong>Eyyüp Melih Yalçınkaya</strong> tarafından geliştirilmiştir.<br>
                    MIT Lisansı ile korunmaktadır. Kaynak kodlarına GitHub üzerinden erişebilirsiniz.
                </div>
                
                <a href="https://github.com/eyyupmelihyalcinkaya/death-tracking-bot" 
                   style="display: inline-block; margin-top: 10px; color: #34495e; text-decoration: underline; font-size: 12px;">
                   GitHub Kaynak Kodları
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    
    full_html = html_content_header + cards_html + html_content_footer

    try:
        # SMTP sunucusuna bir kez bağlanıyoruz
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            
            # Her bir alıcı için döngü başlatıyoruz
            for recipient in receiver_list:
                # Her seferinde yeni bir mesaj objesi oluşturuyoruz
                msg = MIMEMultipart("alternative")
                msg['From'] = f"Vefat Takip Sistemi <{sender}>"
                msg['To'] = recipient  # Sadece o anki alıcıyı yazıyoruz
                msg['Subject'] = f"Yeni Vefat İlanı: {len(new_items)} Kayıt Mevcut"
                
                msg.attach(MIMEText(full_html, 'html', 'utf-8'))
                
                # Gönderimi yapıyoruz
                server.sendmail(sender, recipient, msg.as_string())
                print(f"E-posta gönderildi: {recipient}")
                
        print(f"Toplam {len(receiver_list)} kişiye ayrı ayrı gönderim tamamlandı.")
        
    except Exception as e:
        print(f"Gönderim hatası: {e}")

def scrape_website():
    """Belediye sitesinden güncel listeyi çeker."""
    url = "https://www.erzincan.bel.tr/vefatedenler"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    session = requests.Session()
    
    try:
        # Token Al
        first_res = session.get(url, headers=headers)
        soup = BeautifulSoup(first_res.content, "html.parser")
        token_element = soup.find("input", {"name": "_token"})
        if not token_element: return []
        token = token_element["value"]

        # Veriyi Çek
        payload = {"_token": token, "submit": "Listele"}
        res = session.post(url, data=payload, headers=headers)
        soup = BeautifulSoup(res.content, "html.parser")
        
        scraped_data = []
        table = soup.find("table")
        if table:
            rows = table.find("tbody").find_all("tr")
            for row in rows:
                cols = row.find_all("th")
                if len(cols) >= 6:
                    full_name = cols[0].text.strip().split()
                    name = " ".join(full_name[:-1]) if len(full_name) > 1 else full_name[0]
                    surname = full_name[-1] if len(full_name) > 1 else ""
                    announcement = row.get('title', '')
                    
                    item = {
                        "name": name,
                        "surname": surname,
                        "fathers_name": cols[1].text.strip(),
                        "date_of_burial": cols[2].text.strip(),
                        "burial_place_date_info": cols[3].text.strip(),
                        "place_of_birth": cols[4].text.strip(),
                        "communication_info": cols[5].text.strip(),
                        "announcement_text": announcement,
                        "notables_information": extract_notables(announcement)
                    }
                    scraped_data.append(item)
        return scraped_data
    except Exception as e:
        print(f"Scraping hatası: {e}")
        return []

def main():
    print("İşlem başlatıldı...")
    current_list = scrape_website()
    new_records = []

    for record in current_list:
        # DB Kontrolü yapar (Mükerrer kaydı önlemek için)
        check = supabase.table("vefat_listesi").select("id")\
            .eq("name", record["name"])\
            .eq("surname", record["surname"])\
            .eq("date_of_burial", record["date_of_burial"])\
            .execute()

        if not check.data:
            # Yeni kayıt varsa insert eder
            res = supabase.table("vefat_listesi").insert(record).execute()
            if res.data:
                new_records.append(record)

    if new_records:
        print(f"{len(new_records)} yeni kayıt bulundu. Bildirim gönderiliyor.")
        send_email(new_records)
    else:
        print("Yeni kayıt yok, veritabanı güncel.")

if __name__ == "__main__":
    main()