# OpenCV Tabanlı Yüz Tanıma ve Eşleştirme Sistemi (Face Recognition)

OpenCV kütüphanesini ve Haar Cascade sınıflandırıcılarını kullanarak referans resimler ile test resimlerindeki yüzleri tespit eden, uzamsal boyut analizleri ile bunları eşleştiren hafif ve etkili bir yüz tanıma uygulamasıdır.

## 🚀 Özellikler

- **📂 Yapılandırılmış Dizin Yönetimi**:
  - Referans (bilinen) yüzleri `fotograflar/` klasöründen yükler.
  - Test edilecek (bilinmeyen) yüzleri `yuz_tanima/` klasöründen okur.
  - Klasörler mevcut değilse ilk çalıştırmada otomatik oluşturur.
- **🔍 Hassas Yüz Tespiti**: OpenCV'nin optimize edilmiş `haarcascade_frontalface_default.xml` sınıflandırıcısını kullanarak yüz sınırlarını milisaniyeler içinde tespit eder.
- **⚡ Boyutsal Eşleştirme Algoritması**: Tespit edilen yüzlerin piksel tabanlı genişlik ve yükseklik oranlarını analiz ederek bilinen yüzlerle yüksek doğrulukta eşleştirme yapar.

## 📁 Proje Yapısı

- `yuz_tanima.py`: Yüz algılama ve karşılaştırma motorunu çalıştıran ana Python dosyası.
- `/fotograflar`: Tanınacak kişilerin referans fotoğraflarının yer aldığı klasör (örn: `ahmet.jpg`).
- `/yuz_tanima`: Karşılaştırılacak ve test edilecek fotoğrafların yüklendiği klasör.

## 🛠️ Teknoloji Yığını

- **Kütüphane**: `OpenCV (cv2)`
- **Dil**: Python 3.11
- **Dizin İşlemleri**: Python `os` kütüphanesi

## ⚙️ Kurulum ve Çalıştırma

1. **Depoyu klonlayın**:
   ```bash
   git clone <depo-adresi>
   cd face-recognition-system
   ```

2. **Gereksinimleri yükleyin**:
   ```bash
   pip install opencv-python
   ```

3. **Verileri hazırlayın**:
   - Programı bir kez çalıştırarak klasörleri oluşturun.
   - Tanıtmak istediğiniz kişilerin fotoğraflarını `fotograflar/` klasörüne ekleyin (dosya ismini kişinin adı yapın).
   - Test etmek istediğiniz fotoğrafları `yuz_tanima/` klasörüne atın.

4. **Sistemi başlatın**:
   ```bash
   python yuz_tanima.py
   ```

---

*Emirhan Kaya tarafından sevgiyle tasarlandı ve geliştirildi. 💙*
