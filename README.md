# K-Emlak — İstanbul Konut Değerleme ve İlan Analiz Sistemi

Ev özelliklerine (konum, metrekare, oda sayısı, bina yaşı, ısınma tipi vb.) dayalı
olarak konutların **tahmini piyasa değerini** üreten; ilanları bu tahminle
karşılaştırarak **piyasa altı / piyasa değerinde / piyasa üstü** biçiminde
önizleyen makine öğrenmesi tabanlı bir web uygulaması.

- **Backend:** FastAPI · SQLAlchemy · Alembic · PostgreSQL
- **Model:** CatBoost (log-fiyat regresyonu) — `k_emlak/istanbul_model.cbm` repoda hazır gelir
- **Frontend:** React + Vite (+ recharts)
- **Veri toplama:** Camoufox/Playwright ile Hepsiemlak scraper (opsiyonel)

---

## Gereksinimler

- **Python 3.14** (repodaki `venv` yerine kendi sanal ortamınızı kurun)
- **Node.js 18+** ve npm
- **PostgreSQL** — en kolayı: **Docker** (repodaki `docker-compose.yml` hazır)

---

## Hızlı Başlangıç

Aşağıdaki komutlar **Windows PowerShell** içindir. Sırasıyla: veritabanı → backend → frontend.

### 1) Veritabanı (Docker ile — en kolay yol)

**Docker'ı hiç kullanmadıysanız:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)
kurup çalıştırın (Windows). Sonra proje kökünde:

```powershell
# DB'yi başlat ve bağlantı kabul edene kadar bekle
docker compose up -d --wait

# Durumu gör (STATUS "healthy" olmalı)
docker compose ps
```

Bu, `localhost:5432` üzerinde `kemlak_db` adında bir PostgreSQL başlatır
(kullanıcı: `kemlak`, şifre: `kemlak_sifre`). Bu değerler `.env.example`'daki
`DATABASE_URL` ile birebir uyumludur; başka bir şey ayarlamanız gerekmez.

Sık kullanılan komutlar:

```powershell
docker compose stop     # DB'yi durdur (veri korunur)
docker compose start    # tekrar başlat
docker compose down     # kaldır (veri "pgdata" biriminde saklı kalır)
docker compose down -v  # kaldır ve TÜM veriyi sil
```

> **Docker yerine Neon/kendi PostgreSQL'iniz:** Docker kullanmak istemezseniz kendi
> PostgreSQL'inizi ya da Neon gibi bir bulut DB'yi kullanabilirsiniz — tek yapmanız
> gereken `.env` içindeki `DATABASE_URL`'i o bağlantıyla değiştirmek. **Gerçek
> bağlantı diziniz (özellikle şifre içeren Neon string'i) yalnızca yerel `.env`'de
> kalmalı; asla repoya / README'ye yazılmamalıdır.** (`.env` zaten git'e dahil değildir.)

### 2) Backend (FastAPI)

```powershell
# Proje kökünde
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Ortam değişkenlerini hazırla: ornegi kopyala ve icini doldur
copy .env.example .env

# Veritabanı tablolarını oluştur (Alembic migration'ları)
alembic upgrade head

# (Opsiyonel) Hazır CSV'deki ilanları veritabanına yükle -> uygulamada veri görünsün
python -m scripts.ingest_listings

# API'yi başlat  ->  http://127.0.0.1:8000  (Swagger: /docs)
uvicorn app.main:app --reload
```

> `pip install` sonrası model ve CSV repoda hazır geldiği için tahmin **ekstra bir
> eğitim gerektirmeden** çalışır.

### 3) Frontend (React + Vite)

Yeni bir terminalde:

```powershell
cd frontend
npm install
npm run dev
```

Vite geliştirme sunucusu genelde `http://localhost:5173` adresinde açılır ve
`/api` isteklerini otomatik olarak backend'e (`http://localhost:8000`) yönlendirir.
Yani backend'in **8000 portunda çalışıyor olması** yeterlidir.

---

## Ortam Değişkenleri (`.env`)

`.env` dosyası git'e **dahil edilmez**; `.env.example`'ı kopyalayıp doldurun.

| Değişken | Açıklama |
|---|---|
| `DATABASE_URL` | PostgreSQL bağlantısı. Docker için: `postgresql+psycopg2://kemlak:kemlak_sifre@localhost:5432/kemlak_db` |
| `SCRAPER_PYTHON_PATH` | Scraper'ı çalıştıracak Python (venv içindeki `python.exe`) — yalnızca veri toplama için |
| `SCRAPER_SCRIPT_PATH` | Scraper betiğinin tam yolu (`k_emlak/hepsiemlak_istanbul_camoufox.py`) |
| `SCRAPER_WORKING_DIR` | Scraper'ın çalışma dizini (`k_emlak`) |

---

## Veri Toplama (Scraper — Opsiyonel)

Uygulamayı ilk kez ayağa kaldırmak için scraper **gerekli değildir** (hazır CSV
mevcuttur). Güncel veri çekmek isterseniz:

- `pip install -r requirements.txt` scraper bağımlılıklarını da (playwright/camoufox)
  kurar. Camoufox tarayıcı binary'sini indirmek için: `camoufox fetch`
- Veri toplama, **Yönetim** ekranındaki "Verileri şimdi çek" düğmesinden başlatılır;
  işlem sırasında bulunan yeni ilan sayısı canlı gösterilir, istediğiniz an
  durdurabilirsiniz. Durdurulunca çekilenler veritabanına aktarılır ve model
  otomatik yeniden eğitilir.

---

## Proje Yapısı (özet)

```
app/                FastAPI uygulaması (routers, crud, services, models, schemas)
alembic/            Veritabanı migration'ları
scripts/            ingest_listings.py (CSV -> DB), mape_olc.py (model hatası ölçümü)
k_emlak/            CatBoost modeli, eğitim modülü, scraper, veri CSV'si
frontend/           React + Vite arayüzü
docker-compose.yml  Yerel PostgreSQL
requirements.txt    Python bağımlılıkları
```

---

## Faydalı Komutlar

```powershell
# Model hatasını (MAPE) ölç
python -m scripts.mape_olc

# Modeli güncel veriyle yeniden eğit
python -c "from k_emlak.catboost.tahmin_egit import egit; egit(kaydet=True)"

# Frontend'i production için derle
cd frontend; npm run build
```
