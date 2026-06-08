# Etsy Favori & Koleksiyon Kazıyıcı (Etsy Perfect Scraper)

**Playwright** tabanlı çalışan, Etsy kullanıcılarının favori listelerini otomatik olarak arşivleyen, yüksek çözünürlüklü ürün görsellerini indiren ve işlem anını video kaydına alarak portföy analitiği üreten kurumsal bir Python veri kazıma aracıdır.

## 🚀 Özellikler

- **🌐 Playwright Tarayıcı Otomasyonu**: JavaScript tabanlı dinamik Etsy sayfalarını sorunsuz bir şekilde yüklemek için arka planda Chromium otomasyonu kullanır.
- **🖼️ Yüksek Çözünürlüklü Görsel Yakalama**: URL filtreleme algoritmalarıyla küçük resimleri (thumbnail) atlayıp, ürünün orijinal yüksek çözünürlüklü görsel kaynağını (`il_fullxfull`) yakalar ve indirir.
- **📂 Yapılandırılmış Arşivleme Sistemi**: Çekilen her bir tasarımı temiz isimlerle klasörleyip şu içeriklerle depolar:
  - Orijinal yüksek çözünürlüklü ürün görseli (`image_1.jpg`)
  - Ürün başlığı ve detaylarının yer aldığı metin dosyası (`page_text.txt`)
  - Ürünün doğrudan bağlantı linki (`product_url.txt`)
- **📊 Otomatik Analiz Raporları**: Koleksiyona ait genel bir tema analizi (`analysis.txt`) ve tüm ürünlerin link listesini (`links.txt`) otomatik oluşturur.
- **🎥 Ekran Kayıt Entegrasyonu**: Veri kazıma sürecini canlı olarak kaydeder, `ffmpeg` ile sıkıştırarak doğrudan `process_recording.mp4` formatında rapor klasörüne ekler.

## 🛠️ Teknoloji Yığını

- **Dil**: Python 3.11
- **Tarayıcı Otomasyonu**: `Playwright` (Chromium motoru)
- **Medya İşleme**: `ffmpeg` (mp4 dönüştürme için)
- **Modüller**: `urllib`, `subprocess`, `os`

## ⚙️ Kurulum ve Çalıştırma

1. **Depoyu klonlayın**:
   ```bash
   git clone <depo-adresi>
   cd etsy-perfect-scraper
   ```

2. **Gereksinimleri yükleyin**:
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

3. **Hedef belirleyin**:
   - `scraper.py` dosyası içindeki `TARGET_URL` (koleksiyon linki) ve çıktı klasörü (`output_dir`) yollarını düzenleyin.

4. **Kazıyıcıyı çalıştırın**:
   ```bash
   python scraper.py
   ```

---

*Emirhan Kaya tarafından sevgiyle tasarlandı ve geliştirildi. 💙*
