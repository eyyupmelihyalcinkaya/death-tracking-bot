import os
from supabase import create_client
from logger import logger
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL veya KEY eksik. Lütfen .env dosyasını kontrol edin.")

try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except Exception as e:
    logger.error(f"Supabase istemcisi oluşturulamadı: {e}")
    supabase = None

def filter_new_records(current_list):
    """Veritabanında olmayan yeni kayıtları döndürür."""
    if not supabase:
        return []
        
    try:
        if not current_list:
            return []
            
        names = [record["name"] for record in current_list]
        
        # Olabildiğince bulk sorgu yapıyoruz
        db_records_response = supabase.table("vefat_listesi").select("name, surname, date_of_burial").in_("name", names).execute()
        db_records = db_records_response.data
        
        # Set oluşturarak kolay kontrol yapıyoruz (name|surname|date)
        db_set = {f"{r['name']}|{r['surname']}|{r['date_of_burial']}" for r in db_records}
        
        new_records = []
        for record in current_list:
            key = f"{record['name']}|{record['surname']}|{record['date_of_burial']}"
            if key not in db_set:
                new_records.append(record)
                
        return new_records
    except Exception as e:
        logger.error(f"Veritabanı okuma hatası: {e}")
        return []

def insert_new_records(records):
    """Yeni kayıtları veritabanına bulk insert ile ekler."""
    if not records or not supabase:
        return False
        
    try:
        res = supabase.table("vefat_listesi").insert(records).execute()
        if res.data:
            logger.info(f"{len(records)} yeni kayıt veritabanına başarıyla eklendi.")
            return True
        return False
    except Exception as e:
        logger.error(f"Veritabanı yazma hatası (Bulk Insert): {e}")
        return False
