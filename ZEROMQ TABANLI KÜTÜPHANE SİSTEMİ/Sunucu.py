# zmq kütüphanesini içe aktarıyoruz (ZeroMQ iletişimi için).
import zmq
# json kütüphanesini içe aktarıyoruz (Verileri JSON formatında okuyup yazmak için).
import json
# os kütüphanesini dosya var mı yok mu kontrolü için kullanıyoruz.
import os

# --- GÜNCELLEME BURADA YAPILDI ---
# Dosya yolunu görseldeki konuma sabitledik.
# Başına 'r' koyduk ki Windows ters slah (\) işaretlerini sorunsuz okusun.
DB_FILE = r"C:\Users\berke\Desktop\ornek.json"


def veri_yukle():
    """
    Bu fonksiyon ornek.json dosyasını okur ve Python listesine çevirir.
    Amacı: Her işlem öncesi en güncel veriyi hafızaya almaktır.
    """
    # Dosya belirtilen yolda yoksa boş liste döner.
    if not os.path.exists(DB_FILE):
        print(f"[UYARI] Dosya bulunamadı: {DB_FILE}")
        return []
    try:
        # Dosyayı okuma modunda ("r") ve Türkçe karakter desteğiyle (utf-8) açar.
        with open(DB_FILE, "r", encoding="utf-8") as f:
            # json.load: Dosyadaki JSON metnini Python listesine/sözlüğüne çevirir.
            return json.load(f)
    except Exception as e:
        print(f"Veri yükleme hatası: {e}")
        return []


def veri_kaydet(veri):
    """
    Bu fonksiyon değiştirilen verileri tekrar JSON dosyasına yazar.
    Amacı: Yapılan değişikliklerin (ödünç alma, ekleme) kalıcı olmasını sağlamaktır.
    """
    try:
        # Dosyayı yazma modunda ("w") açar.
        with open(DB_FILE, "w", encoding="utf-8") as f:
            # json.dump: Python verisini JSON formatında dosyaya yazar.
            # indent=4: Dosyanın okunabilir olması için girinti bırakır.
            # ensure_ascii=False: Türkçe karakterlerin bozulmasını engeller.
            json.dump(veri, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Veri kaydetme hatası: {e}")


def main():
    # --- ZEROMQ KURULUMU BAŞLANGIÇ ---

    # 1. Context Oluşturma: ZeroMQ'nun arka plandaki işlem motorunu başlatır.
    context = zmq.Context()

    # 2. Socket Oluşturma: Sunucu "Cevap Veren" (REP - Reply) tarafındadır.
    socket = context.socket(zmq.REP)

    # 3. Portu Bağlama (Binding): Sunucu sabit bir adreste durmalıdır.
    port = "5555"
    socket.bind(f"tcp://*:{port}")
    print(f"[SUNUCU] {port} portu üzerinden istekler dinleniyor...")
    print(f"[BİLGİ] Veritabanı dosyası: {DB_FILE}")

    # --- ZEROMQ DÖNGÜSÜ ---
    while True:
        # 4. Mesaj Bekleme
        message = socket.recv_json()

        print(f"[GELEN İSTEK]: {message}")

        komut = message.get("komut")
        yanit = {"durum": "hata", "mesaj": "Bilinmeyen komut"}

        # İşlem yapmadan önce dosyadan veriyi oku
        kitaplar = veri_yukle()

        # --- İŞLEM MANTIĞI ---

        # SENARYO 1: KİTAP ARAMA
        if komut == "ara":
            aranan = message.get("terim", "").lower()
            if not aranan:
                # Boş arama yapılırsa tüm kitapları döndürsün (opsiyonel)
                sonuclar = kitaplar
            else:
                sonuclar = [k for k in kitaplar if aranan in k["ad"].lower() or aranan in k["yazar"].lower()]

            if sonuclar:
                yanit = {"durum": "basarili", "veri": sonuclar}
            else:
                yanit = {"durum": "hata", "mesaj": "Kitap bulunamadı."}

        # SENARYO 2: KİTAP EKLEME
        elif komut == "ekle":
            yeni_kitap = {
                "id": len(kitaplar) + 1,
                "ad": message.get("ad"),
                "yazar": message.get("yazar"),
                "durum": "rafta"
            }
            kitaplar.append(yeni_kitap)
            veri_kaydet(kitaplar)
            yanit = {"durum": "basarili", "mesaj": "Kitap başarıyla eklendi.", "veri": yeni_kitap}

        # SENARYO 3: ÖDÜNÇ ALMA
        elif komut == "odunc_al":
            kitap_id = message.get("id")
            bulundu = False

            for kitap in kitaplar:
                if kitap["id"] == kitap_id:
                    bulundu = True
                    if kitap["durum"] == "rafta":
                        kitap["durum"] = "odunc_verildi"
                        veri_kaydet(kitaplar)
                        yanit = {"durum": "basarili", "mesaj": f"'{kitap['ad']}' kitabı ödünç alındı."}
                    else:
                        yanit = {"durum": "hata", "mesaj": "Bu kitap zaten ödünç verilmiş."}
                    break

            if not bulundu:
                yanit = {"durum": "hata", "mesaj": "Belirtilen ID ile kitap bulunamadı."}

        # 5. Yanıt Gönderme
        socket.send_json(yanit)


if __name__ == "__main__":
    main()