import os
import requests
import smtplib
import json
from bs4 import BeautifulSoup
from supabase import create_client
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# .env dosyasını yükle (Lokalde çalışırken)
load_dotenv()

# Yapılandırma ve Bağlantılar
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_notables(text):
    if not text:
        return "Belirtilmemiş"
    
    # İlk cümleyi al
    first_sentence = text.split('.')[0]
    
    # Türkçe küçük harf dönüşümü (İ -> i, I -> ı)
    def tr_lower(metin):
        return metin.replace('İ', 'i').replace('I', 'ı').lower()

    # Kontrol için metni küçük harfe çeviriyoruz
    temp_sentence = tr_lower(first_sentence)
    keyword = "eşrafından"
    
    if keyword in temp_sentence:
        # "eşrafından" kelimesinden öncesini al
        origin_part = temp_sentence.split(keyword)[0].strip()
        
        # "ilimiz" kontrolü (artık tamamen küçük harf ve Türkçe uyumlu)
        if "ilimiz" in origin_part:
            return "Erzincan"
        else:
            # Eğer ilimiz değilse, orijinal cümleden o kısmı bulup baş harflerini düzeltelim
            # (Regex kullanarak "eşrafından" kelimesine kadar olan kısmı orijinal metinden alıyoruz)
            import re
            match = re.search(re.escape(keyword), first_sentence, re.IGNORECASE)
            if match:
                raw_origin = first_sentence[:match.start()].strip()
                return raw_origin.title()
            return origin_part.title()
            
    return "Belirtilmemiş"

def send_email(new_items):
    """Yeni kayıtları e-posta ile gönderir."""
    sender = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    receiver = os.getenv('EMAIL_RECEIVER')
    
    if not all([sender, password, receiver]):
        print("E-posta ayarları eksik, gönderim atlanıyor.")
        return

    msg = MIMEMultipart()
    msg['From'] = f"Vefat Takip Sistemi <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = f"Yeni Vefat İlanı Var ({len(new_items)} Kişi)"

    body = "Erzincan Belediyesi vefat listesine yeni eklenen kayıtlar:\n\n"
    for item in new_items:
        body += f"📍 {item['name']} {item['surname']} (Baba: {item['fathers_name']})\n"
        body += f"   Eşraf: {item['notables_information']}\n"
        body += f"   Defin Tarihi: {item['date_of_burial']}\n"
        body += f"   Yer/Zaman: {item['burial_place_date_info']}\n"
        body += f"   İletişim: {item['communication_info']}\n"
        body += "-"*30 + "\n"
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver.split(','), msg.as_string())
        print("E-posta başarıyla gönderildi.")
    except Exception as e:
        print(f"E-posta gönderim hatası: {e}")

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
        # DB Kontrolü (Mükerrer kaydı önlemek için)
        check = supabase.table("vefat_listesi").select("id")\
            .eq("name", record["name"])\
            .eq("surname", record["surname"])\
            .eq("date_of_burial", record["date_of_burial"])\
            .execute()

        if not check.data:
            # Yeni kayıt varsa insert et
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