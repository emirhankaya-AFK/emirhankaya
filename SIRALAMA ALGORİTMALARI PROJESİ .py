import time  # İşlemlerin süresini ölçmek için (Kronometre).
import os  # Dosya yollarını yönetmek ve kontrol etmek için.


# ---------------------------------------------------------
# ALGORİTMA 1: BUBBLE SORT (KABARCIK SIRALAMASI)
# Mantığı: Diziyi baştan sona tarar. Yan yana duran iki sayıyı
# karşılaştırır. Eğer soldaki sayı sağdakinden büyükse yerlerini değiştirir.
# Bu işlem, tüm liste sıralanana kadar defalarca tekrarlanır.
# ---------------------------------------------------------
def bubble_sort(liste):
    # Orijinal listeyi bozmamak için kopyasını alıyoruz (.copy()).
    # Yoksa ana listedeki sayılar yer değiştirir ve diğer algoritmaya sıralı liste gider.
    arr = liste.copy()
    n = len(arr)
    adim_sayisi = 0  # İşlem yükünü (karşılaştırma + yer değiştirme) sayar.

    baslangic = time.perf_counter()  # Kronometreyi başlat.

    for i in range(n):
        # Her turda en büyük eleman sona doğru "köpürerek" gider.
        # Bu yüzden her seferinde son kısımdaki (n-i-1) elemana bakmaya gerek kalmaz.
        for j in range(0, n - i - 1):
            adim_sayisi += 1  # Karşılaştırma yapıyoruz (if satırı).

            if arr[j] > arr[j + 1]:
                # Soldaki sayı büyükse, sağdakiyle yer değiştir (Swap).
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                adim_sayisi += 1  # Yer değiştirme işlemi yapıldı.

    bitis = time.perf_counter()  # Kronometreyi durdur.
    sure = bitis - baslangic
    return arr, adim_sayisi, sure


# ---------------------------------------------------------
# ALGORİTMA 2: SELECTION SORT (SEÇMELİ SIRALAMA)
# Mantığı: Listenin en küçük elemanını bulur ve en başa koyar.
# Sonra kalan kısımdaki en küçüğü bulur ve ikinci sıraya koyar.
# ---------------------------------------------------------
def selection_sort(liste):
    arr = liste.copy()
    n = len(arr)
    adim_sayisi = 0

    baslangic = time.perf_counter()

    for i in range(n):
        min_idx = i  # En küçük sayının şu anki indeksi (varsayılan).

        # Sıralanmamış kısmı tara ve en küçüğü bul.
        for j in range(i + 1, n):
            adim_sayisi += 1  # Karşılaştırma yapıyoruz.
            if arr[j] < arr[min_idx]:
                min_idx = j  # Yeni en küçük bulundu, indeksini kaydet.

        # En küçük sayıyı olması gereken yere (i. sıraya) taşı.
        # Python'da takas işlemi tek satırda yapılabilir:
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
        adim_sayisi += 1  # Yer değiştirme yapıldı.

    bitis = time.perf_counter()
    sure = bitis - baslangic
    return arr, adim_sayisi, sure


# ---------------------------------------------------------
# ANA PROGRAM
# ---------------------------------------------------------
def ana_program():
    print("--- Sıralama Algoritmaları Karşılaştırma Projesi ---")

    # -----------------------------------------------------
    # ADIM 1: Dosya Yolunu Belirleme (OTOMATİK)
    # -----------------------------------------------------
    # Resimdeki masaüstü yolunu varsayılan olarak ayarladık.
    # 'r' harfi dosya yolundaki ters eğik çizgilerin (\) hata vermesini engeller.
    varsayilan_yol = r"C:\Users\berke\Desktop\sayilar.txt"

    print(f"Varsayılan dosya yolu: {varsayilan_yol}")
    kullanici_girdisi = input("Farklı bir dosya girmek isterseniz yazın, yoksa varsayılan için ENTER'a basın: ")

    # Eğer kullanıcı hiçbir şey yazmazsa varsayılan yolu kullan.
    if kullanici_girdisi.strip() == "":
        dosya_adi = varsayilan_yol
    else:
        dosya_adi = kullanici_girdisi

    # Dosya kontrolü: Dosya gerçekten orada mı?
    if not os.path.exists(dosya_adi):
        print(f"\nHATA: '{dosya_adi}' konumunda dosya bulunamadı!")
        print("Lütfen dosya yolunu ve ismini kontrol edin.")
        return

    try:
        # -----------------------------------------------------
        # ADIM 2: Dosyayı Okuma ve Listeye Çevirme
        # -----------------------------------------------------
        with open(dosya_adi, "r", encoding="utf-8") as f:
            icerik = f.read()
            # Dosyadaki metni (örn: "64, 34, 25") virgüllerden ayırıp sayı listesine çevirir.
            # .strip() boşlukları temizler, int() sayıya çevirir.
            sayi_listesi = [int(x.strip()) for x in icerik.split(",")]

        print(f"\nDosya başarıyla okundu. Toplam {len(sayi_listesi)} adet sayı var.")
        print(f"Sıralanacak Liste (İlk 10): {sayi_listesi[:10]}...")  # Sadece ilk 10 sayıyı göster.

        # -----------------------------------------------------
        # ADIM 3: Algoritmaları Yarıştırma
        # -----------------------------------------------------
        print("\nAlgoritmalar çalışıyor, lütfen bekleyin...")

        # Bubble Sort'u çalıştır ve sonuçları al.
        b_sirali, b_adim, b_sure = bubble_sort(sayi_listesi)

        # Selection Sort'u çalıştır ve sonuçları al.
        s_sirali, s_adim, s_sure = selection_sort(sayi_listesi)

        # -----------------------------------------------------
        # ADIM 4: Raporu Hazırlama ve Kaydetme
        # -----------------------------------------------------
        # Karşılaştırma mantığı: Kimin süresi daha azsa o kazanır.
        hizli_olan = 'Bubble Sort' if b_sure < s_sure else 'Selection Sort'
        az_adim_atan = 'Bubble Sort' if b_adim < s_adim else 'Selection Sort'

        rapor = f"""
===================================================
SIRALAMA ALGORİTMALARI KARŞILAŞTIRMA RAPORU
===================================================
İşlenen Dosya : {dosya_adi}
Eleman Sayısı : {len(sayi_listesi)}
---------------------------------------------------

1. BUBBLE SORT (Kabarcık Sıralaması)
------------------------------------
- Toplam Adım Sayısı : {b_adim}
- İşlem Süresi       : {b_sure:.10f} saniye
- Durum              : Başarılı

2. SELECTION SORT (Seçmeli Sıralama)
------------------------------------
- Toplam Adım Sayısı : {s_adim}
- İşlem Süresi       : {s_sure:.10f} saniye
- Durum              : Başarılı

---------------------------------------------------
KARŞILAŞTIRMA SONUCU:
Daha Hızlı Olan      : {hizli_olan}
Daha Az Adım Atan    : {az_adim_atan}
===================================================

SIRALANMIŞ LİSTE (İlk 20 Eleman):
{b_sirali[:20]}...
"""
        # Sonuç dosyasını da masaüstüne (okunan dosyanın yanına) kaydedelim.
        klasor_yolu = os.path.dirname(dosya_adi)
        cikti_dosyasi = os.path.join(klasor_yolu, "siralama_raporu.txt")

        with open(cikti_dosyasi, "w", encoding="utf-8") as f:
            f.write(rapor)

        print(f"\nİşlem tamamlandı!")
        print(f"Rapor dosyası şuraya kaydedildi: {cikti_dosyasi}")
        print("Rapor içeriği ekrana yazdırılıyor:\n")
        print(rapor)

    except ValueError:
        print("Hata: Dosyanın içinde sayı olmayan karakterler (harf vb.) var.")
        print("Lütfen dosyada sadece virgülle ayrılmış sayılar olduğundan emin olun.")
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")


if __name__ == "__main__":
    ana_program()