from scraper import scrape_website
from database import filter_new_records, insert_new_records
from mailer import send_email
from logger import logger

def main():
    logger.info("İşlem başlatıldı...")
    
    current_list = scrape_website()
    
    if not current_list:
        logger.info("Siteden güncel liste alınamadı veya liste boş.")
        return

    new_records = filter_new_records(current_list)

    if new_records:
        logger.info(f"{len(new_records)} yeni kayıt bulundu. Veritabanına ekleniyor...")
        if insert_new_records(new_records):
            logger.info("Veritabanı güncellendi. Bildirim gönderiliyor...")
            send_email(new_records)
        else:
            logger.error("Kayıtlar veritabanına eklenirken sorun oluştu. E-posta gönderilmedi.")
    else:
        logger.info("Yeni kayıt yok, veritabanı güncel.")

if __name__ == "__main__":
    main()
