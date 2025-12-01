import json  # JSON dosyalarını okumak ve yazmak için kullanılan kütüphane.
import time  # İşlemlerin süresini (kronometre gibi) ölçmek için.
import os  # Bilgisayardaki dosya yollarını ve klasörleri kontrol etmek için.


def kumelerle_islemler():
    """
    Bu fonksiyon projenin ana beynidir.
    1. Kullanıcıdan dosya adını alır (veya varsayılanı kullanır).
    2. JSON verisini okuyup matematiksel küme işlemlerini yapar.
    3. Sonuçları ve süreleri yeni bir dosyaya kaydeder.
    """

    print("--- Kümelerle Temel İşlemler Projesi ---")

    # ---------------------------------------------------------
    # ADIM 1: Dosya Yolunu Belirleme
    # ---------------------------------------------------------
    # Senin bilgisayarındaki özel dosya yolu.
    # Başındaki 'r' harfi, Windows dosya yollarındaki ters eğik çizgilerin (\) sorun çıkarmamasını sağlar.
    varsayilan_yol = r"C:\Users\berke\Desktop\veri.json"

    print(f"Varsayılan dosya yolu: {varsayilan_yol}")
    # Kullanıcıya seçenek sunuyoruz: Ya yeni yol yazar ya da ENTER'a basıp geçerek varsayılanı kullanır.
    kullanici_girdisi = input("Farklı bir dosya girmek isterseniz yazın, yoksa varsayılan için ENTER'a basın: ")

    # .strip() boşlukları temizler. Eğer içi boşsa (sadece Enter'a basıldıysa) varsayılanı al.
    if kullanici_girdisi.strip() == "":
        dosya_adi = varsayilan_yol
    else:
        dosya_adi = kullanici_girdisi

    # Dosya sistemde var mı diye kontrol ediyoruz. Yoksa program hata verip kapanır.
    if not os.path.exists(dosya_adi):
        print(f"\nHATA: '{dosya_adi}' konumunda dosya bulunamadı!")
        return

    try:
        # ---------------------------------------------------------
        # ADIM 2: Dosyayı Okuma (Veri Alma)
        # ---------------------------------------------------------
        # 'with open' dosyayı güvenli açar ve iş bitince otomatik kapatır.
        # 'r': read (okuma) modu. 'utf-8': Türkçe karakter sorunu olmasın diye.
        with open(dosya_adi, 'r', encoding='utf-8') as f:
            veri = json.load(f)  # Dosyadaki yazıları Python'un anlayacağı listeye çevirir.

        # JSON içinden "liste_a" ve "liste_b" isimli listeleri çekiyoruz.
        # .get() kullanıyoruz ki eğer liste yoksa hata vermesin, boş liste versin.
        liste_1 = veri.get("liste_a", [])
        liste_2 = veri.get("liste_b", [])

        print(f"\nDosya başarıyla okundu.")
        print(f"Liste 1 Eleman Sayısı: {len(liste_1)}")
        print(f"Liste 2 Eleman Sayısı: {len(liste_2)}")

    except json.JSONDecodeError:
        print("Hata: Dosya içeriği bozuk veya düzgün bir JSON formatında değil.")
        return
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")
        return

    # ---------------------------------------------------------
    # ADIM 3: Kümeye Dönüştürme ve Matematiksel İşlemler
    # ---------------------------------------------------------
    # set() fonksiyonu listeyi kümeye çevirir. Tekrar eden sayıları siler.
    kume_1 = set(liste_1)
    kume_2 = set(liste_2)

    # Sonuçları saklayacağımız boş bir sözlük (dictionary).
    sonuclar = {}

    # --- İŞLEM A: BİRLEŞİM (UNION / A U B) ---
    baslangic = time.perf_counter()  # Saati başlat.
    birlesim = kume_1.union(kume_2)  # İki kümeyi birleştir.
    bitis = time.perf_counter()  # Saati durdur.

    # Sonuçları sözlüğe ekliyoruz.
    # JSON kümeleri tanımaz, bu yüzden 'list(birlesim)' diyerek tekrar listeye çeviriyoruz.
    sonuclar["birlesim"] = {
        "sonuc": list(birlesim),
        "eleman_sayisi": len(birlesim),
        "sure_saniye": f"{bitis - baslangic:.10f}"  # Süreyi virgülden sonra 10 hane hassas göster.
    }

    # --- İŞLEM B: KESİŞİM (INTERSECTION / A ∩ B) ---
    baslangic = time.perf_counter()
    kesisim = kume_1.intersection(kume_2)  # Sadece ortak olanları al.
    bitis = time.perf_counter()

    sonuclar["kesisim"] = {
        "sonuc": list(kesisim),
        "eleman_sayisi": len(kesisim),
        "sure_saniye": f"{bitis - baslangic:.10f}"
    }

    # --- İŞLEM C: FARK (A - B) ---
    baslangic = time.perf_counter()
    fark_a_b = kume_1.difference(kume_2)  # A'da olup B'de olmayanlar.
    bitis = time.perf_counter()

    sonuclar["fark_liste_a_eksi_liste_b"] = {
        "sonuc": list(fark_a_b),
        "eleman_sayisi": len(fark_a_b),
        "sure_saniye": f"{bitis - baslangic:.10f}"
    }

    # --- İŞLEM D: FARK (B - A) ---
    baslangic = time.perf_counter()
    fark_b_a = kume_2.difference(kume_1)  # B'de olup A'da olmayanlar.
    bitis = time.perf_counter()

    sonuclar["fark_liste_b_eksi_liste_a"] = {
        "sonuc": list(fark_b_a),
        "eleman_sayisi": len(fark_b_a),
        "sure_saniye": f"{bitis - baslangic:.10f}"
    }

    # ---------------------------------------------------------
    # ADIM 4: Sonuçları Dosyaya Yazma
    # ---------------------------------------------------------
    # Sonuç dosyasını, kaynak dosyanın (Masaüstü) olduğu yere kaydedelim.
    klasor_yolu = os.path.dirname(dosya_adi)
    cikti_dosyasi = os.path.join(klasor_yolu, "sonuclar.json")

    try:
        # Dosyayı yazma modunda ('w') açıyoruz.
        with open(cikti_dosyasi, 'w', encoding='utf-8') as f:
            # json.dump veriyi dosyaya yazar.
            # indent=4: Okuması kolay olsun diye girintili yazar.
            # ensure_ascii=False: Türkçe karakterler bozulmasın diye.
            json.dump(sonuclar, f, indent=4, ensure_ascii=False)

        print(f"\nİşlemler başarıyla tamamlandı!")
        print(f"Sonuç dosyası oluşturuldu: {cikti_dosyasi}")

    except Exception as e:
        print(f"Dosya kaydedilirken hata oluştu: {e}")


# Bu blok, kodun doğrudan çalıştırıldığında (import edilmediğinde) devreye girmesini sağlar.
if __name__ == "__main__":
    kumelerle_islemler()