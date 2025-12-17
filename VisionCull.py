import os
import shutil
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# --- AYARLAR ---
# Ekran görüntüsündeki dosya yolu:
kaynak_klasor = r"C:\Users\berke\Desktop\emirhan_111225"

# Hedef klasör isimleri (Bu klasörler yukarıdaki emirhan_111225 klasörünün içine açılacak)
hedef_klasorler = {
    '1': "veri_setine_dahil_edilecek_olanlar",
    '2': "veri_setine_dahil_edilmeyecek_olanlar",
    '3': "kararsiz_kaldiklariniz"
}

# Desteklenen formatlar
uzantilar = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')


class ResimAyiklayici:
    def __init__(self, root):
        self.root = root
        self.root.title("Veri Seti Ayıklama Aracı - Emirhan Dataset")
        self.root.geometry("900x750")

        # Hedef klasörleri oluştur
        self.klasorleri_hazirla()

        # Resim listesini al ve SIRALA (Mola verince karışmasın diye sorted kullandık)
        # Sadece dosya olanları alıyoruz, klasörleri listeye katmıyoruz.
        try:
            self.resim_listesi = sorted([
                f for f in os.listdir(kaynak_klasor)
                if os.path.isfile(os.path.join(kaynak_klasor, f)) and f.lower().endswith(uzantilar)
            ])
        except FileNotFoundError:
            messagebox.showerror("Hata",
                                 f"Klasör bulunamadı:\n{kaynak_klasor}\nLütfen yolun doğru olduğundan emin olun.")
            root.destroy()
            return

        self.toplam_resim = len(self.resim_listesi)
        self.suanki_index = 0

        if self.toplam_resim == 0:
            messagebox.showinfo("Bilgi", "Bu klasörde ayıklanacak resim bulunamadı veya hepsi zaten taşınmış.")
            root.destroy()
            return

        # Bilgi Etiketleri
        self.lbl_bilgi = tk.Label(root, text="", font=("Arial", 12))
        self.lbl_bilgi.pack(pady=5)

        # Resim Alanı
        self.panel = tk.Label(root)
        self.panel.pack(expand=True)

        # Talimatlar
        self.lbl_talimat = tk.Label(root, text="KLAVYE KISAYOLLARI:\n1: Dahil Et  |  2: Dahil Etme  |  3: Kararsız",
                                    font=("Arial", 14, "bold"), fg="#333")
        self.lbl_talimat.pack(pady=20)

        # Klavye tuşlarını bağla
        root.bind('1', lambda event: self.resmi_tasi('1'))
        root.bind('2', lambda event: self.resmi_tasi('2'))
        root.bind('3', lambda event: self.resmi_tasi('3'))

        self.resmi_goster()

    def klasorleri_hazirla(self):
        for k in hedef_klasorler.values():
            yol = os.path.join(kaynak_klasor, k)
            if not os.path.exists(yol):
                os.makedirs(yol)

    def resmi_goster(self):
        # Liste sınırını kontrol et
        if self.suanki_index >= self.toplam_resim:
            messagebox.showinfo("Bitti", "Harika! Tüm resimler sınıflandırıldı.")
            self.root.destroy()
            return

        resim_adi = self.resim_listesi[self.suanki_index]
        dosya_yolu = os.path.join(kaynak_klasor, resim_adi)

        # Dosya yerinde yoksa (belki manuel silinmiştir), sonrakine geç
        if not os.path.exists(dosya_yolu):
            self.suanki_index += 1
            self.resmi_goster()
            return

        # Bilgi güncelle
        kalan = self.toplam_resim - self.suanki_index
        self.lbl_bilgi.config(text=f"Dosya: {resim_adi}\nKalan: {kalan} / {self.toplam_resim}")

        try:
            img = Image.open(dosya_yolu)

            # Resmi pencereye sığdır (maksimum 800x550)
            img.thumbnail((800, 550))

            self.img_tk = ImageTk.PhotoImage(img)
            self.panel.config(image=self.img_tk)
        except Exception as e:
            print(f"Resim açma hatası ({resim_adi}): {e}")
            # Açılmayan bozuk resimse 'kararsiz' klasörüne atıp geçelim ki program durmasın
            self.resmi_tasi('3')

    def resmi_tasi(self, secim):
        if self.suanki_index >= self.toplam_resim:
            return

        resim_adi = self.resim_listesi[self.suanki_index]
        kaynak_yol = os.path.join(kaynak_klasor, resim_adi)
        hedef_klasor_adi = hedef_klasorler[secim]
        hedef_yol = os.path.join(kaynak_klasor, hedef_klasor_adi, resim_adi)

        try:
            shutil.move(kaynak_yol, hedef_yol)
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya taşınırken hata oluştu:\n{e}")
            return

        # Bir sonraki resme geç
        self.suanki_index += 1
        self.resmi_goster()


if __name__ == "__main__":
    root = tk.Tk()
    app = ResimAyiklayici(root)
    root.mainloop()