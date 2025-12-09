# zmq kütüphanesini içe aktarıyoruz.
import zmq
# JSON formatlı verileri işlemek için değil ama print çıktısını güzelleştirmek için kullanıyoruz.
import json
import sys


def main():
    # --- ZEROMQ KURULUMU BAŞLANGIÇ ---

    # 1. Context Oluşturma: Sunucudaki gibi, ZeroMQ motorunu başlatır.
    context = zmq.Context()

    # 2. Socket Oluşturma: İstemci "İstek Yapan" (REQ - Request) tarafındadır.
    # REQ soketi kuralı: Önce mesaj gönder (send), sonra cevap bekle (recv).
    # Cevap gelmeden yeni mesaj gönderemezsiniz.
    print("[İSTEMCİ] Sunucuya bağlanılıyor...")
    socket = context.socket(zmq.REQ)

    # 3. Bağlanma (Connect): İstemci aktif olarak sunucuyu bulur ve bağlanır.
    # localhost: Kendi bilgisayarımız. 5555: Sunucunun dinlediği kapı.
    socket.connect("tcp://localhost:5555")

    # Sonsuz döngü ile kullanıcının sürekli işlem yapabilmesini sağlıyoruz.
    while True:
        # Menü seçeneklerini ekrana yazdırıyoruz.
        print("\n--- KÜTÜPHANE SİSTEMİ ---")
        print("1. Kitap Ara")
        print("2. Kitap Ekle")
        print("3. Kitap Ödünç Al")
        print("4. Çıkış")

        secim = input("Seçiminiz (1-4): ")

        # Sunucuya gönderilecek veriyi tutacak boş bir sözlük.
        istek = {}

        # --- KULLANICI GİRDİLERİ ---

        if secim == "1":
            terim = input("Aranacak kitap adı veya yazar: ")
            # Sunucuya gidecek komut ve veri hazırlanıyor.
            istek = {"komut": "ara", "terim": terim}

        elif secim == "2":
            ad = input("Kitap Adı: ")
            yazar = input("Yazar Adı: ")
            istek = {"komut": "ekle", "ad": ad, "yazar": yazar}

        elif secim == "3":
            try:
                # Kullanıcıdan sayı istiyoruz, harf girerse hata (ValueError) yakalıyoruz.
                kitap_id = int(input("Ödünç alınacak Kitap ID'si: "))
                istek = {"komut": "odunc_al", "id": kitap_id}
            except ValueError:
                print("Lütfen geçerli bir sayı giriniz.")
                continue  # Döngünün başına dön.

        elif secim == "4":
            print("Çıkış yapılıyor...")
            break  # Döngüyü kır ve programı kapat.
        else:
            print("Geçersiz seçim.")
            continue

        # --- ZEROMQ İLETİŞİMİ ---

        # 4. Mesaj Gönderme: Hazırladığımız 'istek' sözlüğünü JSON formatında sunucuya atarız.
        # Bu işlemden sonra istemci BLOKLANIR (donar), cevap gelene kadar bir sonraki satıra geçmez.
        print(f"Sunucuya gönderiliyor: {istek}")
        socket.send_json(istek)

        # 5. Cevap Alma: Sunucunun işlemini bitirip gönderdiği yanıtı bekler ve alır.
        # recv_json(): Gelen JSON verisini Python sözlüğüne çevirir.
        yanit = socket.recv_json()

        # --- SONUÇ GÖSTERİMİ ---

        print("\n--- SUNUCU YANITI ---")
        # Sunucudan gelen "durum" bilgisine göre kullanıcıya mesaj gösteriyoruz.
        if yanit.get("durum") == "basarili":
            print(f"SONUÇ: BAŞARILI")
            # Eğer yanıt içinde bir veri listesi varsa (örn: arama sonuçları) onu güzelce yazdır.
            if "veri" in yanit:
                # json.dumps sadece ekranda güzel (indent=4) görünsün diye kullanıldı.
                print(json.dumps(yanit["veri"], indent=4, ensure_ascii=False))
            if "mesaj" in yanit:
                print(f"MESAJ: {yanit['mesaj']}")
        else:
            # Hata durumunda sunucunun gönderdiği hata mesajını göster.
            print(f"SONUÇ: HATA - {yanit.get('mesaj')}")


if __name__ == "__main__":
    main()