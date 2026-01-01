# Vefat Takip Sistemi

Erzincan Belediyesi resmi web sitesinde yayınlanan vefat ilanlarını otomatik olarak takip eden ve yeni kayıtları bildirim olarak ileten bir Python uygulamasıdır.

## Özellikler

- Erzincan Belediyesi vefat listesinden anlık veri çekme
- Yeni kayıtları Supabase veritabanında saklama
- Mükerrer kayıtları engelleme sistemi
- Yeni vefat ilanlarını e-posta ile bilgilendirme
- Eşraf bilgilerini otomatik ayıklama ve düzenleme

## Gereksinimler

Uygulamayı çalıştırmak için aşağıdaki Python kütüphanelerine ihtiyaç vardır:

```
requests
beautifulsoup4
python-dotenv
supabase
```

## Kurulum

1. Depoyu yerel sisteminize klonlayın:
```bash
git clone <repository-url>
cd "vefat listesi"
```

2. Gerekli bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

3. Proje kök dizininde `.env` dosyası oluşturun ve gerekli bilgileri ekleyin:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECEIVER=receiver@email.com
```

## Kullanım

Uygulamayı çalıştırmak için:

```bash
python project.py
```

Program çalıştırıldığında:
1. Erzincan Belediyesi vefat ilanları sayfasından güncel listeyi çeker
2. Veritabanında kayıtlı olmayan yeni kayıtları tespit eder
3. Yeni kayıtları Supabase veritabanına ekler
4. Yeni kayıtlar varsa belirtilen e-posta adresine bildirim gönderir

## Veritabanı Yapısı

Supabase üzerinde `vefat_listesi` tablosu aşağıdaki alanları içermelidir:

- `name`: İsim
- `surname`: Soyisim
- `fathers_name`: Baba adı
- `date_of_burial`: Defin tarihi
- `burial_place_date_info`: Cenaze yeri ve saat bilgisi
- `place_of_birth`: Doğum yeri
- `communication_info`: İletişim bilgileri
- `announcement_text`: Vefat ilan metni
- `notables_information`: Eşraf bilgisi

## E-posta Yapılandırması

Gmail kullanıyorsanız, uygulama şifresi oluşturmanız gerekir:

1. Google hesabınızın güvenlik ayarlarına gidin
2. İki faktörlü doğrulamayı aktif edin
3. Uygulama şifresi oluşturun
4. Bu şifreyi `.env` dosyasındaki `EMAIL_PASSWORD` alanına girin

## Otomatik Çalıştırma

Projeyi belirli aralıklarla otomatik çalıştırmak için:

### Windows (Görev Zamanlayıcı)
Windows Görev Zamanlayıcı kullanarak belirli aralıklarla scripti çalıştırabilirsiniz.

### Linux/Mac (Cron Job)
```bash
# Her saat başı çalıştırmak için
0 * * * * /usr/bin/python3 /path/to/project.py
```

### Heroku/Cloud Platform
Heroku Scheduler veya benzeri servisler ile periyodik olarak çalıştırılabilir.

## Notlar

- Program, veritabanında zaten kayıtlı olan vefat ilanlarını tekrar eklemez
- E-posta bildirimleri yalnızca yeni kayıt tespit edildiğinde gönderilir
- Eşraf bilgisi, ilan metninden otomatik olarak çıkarılmaktadır

## Lisans

Bu proje açık kaynak kodlu bir projedir.

## Sorumluluk Reddi

Bu uygulama kişisel bilgilendirme amaçlı geliştirilmiştir. Erzincan Belediyesi ile resmi bir ilişkisi yoktur. Uygulamanın kullanımından doğacak sorumluluk kullanıcıya aittir.
