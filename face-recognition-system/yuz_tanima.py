import cv2
import os

# Klasör yollarını belirle
fotograflar_klasoru = os.path.join(os.getcwd(), "fotograflar")
yuz_tanima_klasoru = os.path.join(os.getcwd(), "yuz_tanima")

# Eğer klasörler yoksa oluştur
for klasor in [fotograflar_klasoru, yuz_tanima_klasoru]:
    if not os.path.exists(klasor):
        os.makedirs(klasor)

# OpenCV yüz tanıma modelini yükle
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Fotoğraflardaki yüzleri yükle
known_faces = {}
print("📂 Fotoğraflar klasöründeki yüzler taranıyor...")

for resim in os.listdir(fotograflar_klasoru):
    resim_yolu = os.path.join(fotograflar_klasoru, resim)
    img = cv2.imread(resim_yolu)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) > 0:
        known_faces[resim] = faces[0]  # İlk yüzü al

print(f"✅ {len(known_faces)} yüz yüklendi! Şimdi test ediyoruz...\n")

# Test edilecek yüzleri tara
for test_resim in os.listdir(yuz_tanima_klasoru):
    test_resim_yolu = os.path.join(yuz_tanima_klasoru, test_resim)
    test_img = cv2.imread(test_resim_yolu)
    test_gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
    test_faces = face_cascade.detectMultiScale(test_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(test_faces) == 0:
        print(f"❌ {test_resim}: Yüz bulunamadı.")
        continue

    print(f"📸 {test_resim} için yüz bulundu! Şimdi karşılaştırıyoruz...")

    for name, face in known_faces.items():
        (x, y, w, h) = face
        (tx, ty, tw, th) = test_faces[0]  # İlk test yüzünü al

        # Yüz boyutlarının benzer olup olmadığını kontrol et
        if abs(w - tw) < 30 and abs(h - th) < 30:
            print(f"✅ {test_resim} → {name} ile eşleşiyor!")

print("\n🔥 Yüz tanıma tamamlandı!")
