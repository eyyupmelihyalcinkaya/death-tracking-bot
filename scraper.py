import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
from logger import logger

def extract_notables(text):
    if not text:
        return "Belirtilmemiş"
    
    first_sentence = text.split('.')[0]
    
    def tr_lower(metin):
        return metin.replace('İ', 'i').replace('I', 'ı').lower()

    temp_sentence = tr_lower(first_sentence)
    keyword = "eşrafından"
    
    if keyword in temp_sentence:
        origin_part = temp_sentence.split(keyword)[0].strip()
        
        if "ilimiz" in origin_part:
            return "Erzincan"
        else:
            match = re.search(re.escape(keyword), first_sentence, re.IGNORECASE)
            if match:
                raw_origin = first_sentence[:match.start()].strip()
                return raw_origin.title()
            return origin_part.title()
            
    return "Belirtilmemiş"

def get_session():
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def scrape_website():
    """Belediye sitesinden güncel listeyi çeker."""
    url = "https://www.erzincan.bel.tr/vefatedenler"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    session = get_session()
    
    try:
        # Token Al
        first_res = session.get(url, headers=headers, timeout=10)
        first_res.raise_for_status()
        
        soup = BeautifulSoup(first_res.content, "html.parser")
        token_element = soup.find("input", {"name": "_token"})
        if not token_element:
            logger.error("Token bulunamadı.")
            return []
            
        token = token_element["value"]

        # Veriyi Çek
        payload = {"_token": token, "submit": "Listele"}
        res = session.post(url, data=payload, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.content, "html.parser")
        
        scraped_data = []
        table = soup.find("table")
        if table and table.find("tbody"):
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
            logger.info(f"Siteden {len(scraped_data)} kayıt başarıyla çekildi.")
            return scraped_data
        else:
            logger.warning("Tablo veya tbody bulunamadı.")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Scraping ağı hatası: {e}")
        return []
    except Exception as e:
        logger.error(f"Beklenmeyen scraping hatası: {e}")
        return []
