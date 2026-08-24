import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
from logger import logger

def extract_notables(text):
    if not text:
        return "Belirtilmemiş"

    text = text.strip().strip('"\'“”')

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

def parse_detail(session, headers, detail_id):
    """Vefat detay modalının kaynağı olan alt sayfadan baba adı, iletişim ve açıklama bilgisini çeker."""
    detail_url = f"https://www.erzincan.bel.tr/vefatedenler/{detail_id}"
    res = session.get(detail_url, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, "html.parser")

    info = {"fathers_name": "", "communication_info": "", "announcement_text": ""}

    for label in soup.find_all("span", class_=re.compile("tracking-widest")):
        value_el = label.find_next_sibling("span")
        if not value_el:
            continue
        label_text = label.get_text(strip=True)
        if "BABA ADI" in label_text:
            info["fathers_name"] = value_el.get_text(strip=True)
        elif "İLETİŞİM" in label_text:
            info["communication_info"] = value_el.get_text(strip=True)

    description = soup.find("p")
    if description:
        info["announcement_text"] = description.get_text(strip=True)

    return info

def scrape_website():
    """Belediye sitesinden güncel listeyi çeker."""
    url = "https://www.erzincan.bel.tr/vefatedenler"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    session = get_session()

    try:
        res = session.get(url, headers=headers, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.content, "html.parser")

        table = soup.find("table")
        if not (table and table.find("tbody")):
            logger.warning("Tablo veya tbody bulunamadı.")
            return []

        scraped_data = []
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            name_col = cols[0]
            name_el = name_col.find("h4")
            full_name = name_el.get_text(strip=True).split() if name_el else []
            if not full_name:
                continue
            name = " ".join(full_name[:-1]) if len(full_name) > 1 else full_name[0]
            surname = full_name[-1] if len(full_name) > 1 else ""

            place_el = name_col.find("span")
            place_of_birth = place_el.get_text(strip=True) if place_el else "Belirtilmemiş"

            date_of_burial = cols[2].get_text(strip=True)
            burial_place_date_info = cols[3].get_text(strip=True)

            fathers_name = ""
            communication_info = ""
            announcement_text = ""

            detail_button = row.find("button", onclick=re.compile(r"openVefatModal"))
            detail_id_match = re.search(r"openVefatModal\((\d+)\)", detail_button.get("onclick", "")) if detail_button else None
            if detail_id_match:
                try:
                    detail = parse_detail(session, headers, detail_id_match.group(1))
                    fathers_name = detail["fathers_name"]
                    communication_info = detail["communication_info"]
                    announcement_text = detail["announcement_text"]
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Detay bilgisi alınamadı ({detail_id_match.group(1)}): {e}")

            item = {
                "name": name,
                "surname": surname,
                "fathers_name": fathers_name,
                "date_of_burial": date_of_burial,
                "burial_place_date_info": burial_place_date_info,
                "place_of_birth": place_of_birth,
                "communication_info": communication_info,
                "announcement_text": announcement_text,
                "notables_information": extract_notables(announcement_text)
            }
            scraped_data.append(item)

        logger.info(f"Siteden {len(scraped_data)} kayıt başarıyla çekildi.")
        return scraped_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Scraping ağı hatası: {e}")
        return []
    except Exception as e:
        logger.error(f"Beklenmeyen scraping hatası: {e}")
        return []
