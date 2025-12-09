import sys  # Sistem komutları için (özellikle uygulamayı başlatırken ve kapatırken kullanılır).
import requests  # İnternet/Ağ üzerinden (Flask sunucusuyla) konuşmak için kullanılır.
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QMessageBox, QFrame)
# PyQt5: Masaüstü penceresi, butonlar ve yazı alanları oluşturmak için kullanılan kütüphanedir.
from PyQt5.QtCore import Qt  # Temel PyQt sabitleri (hizalama vb.) için.

# Grafik çizimi için gerekli kütüphaneler
import matplotlib

# Matplotlib'in PyQt penceresi içinde çalışabilmesi için 'Qt5Agg' arka ucunu kullanmasını söylüyoruz.
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
# 3D grafik çizeceğimiz için gerekli olan araç kutusu (Toolkit).
from mpl_toolkits.mplot3d import Axes3D


class FlightTrackerApp(QMainWindow):
    """
    Bu sınıf bizim ana pencere uygulamamızdır.
    QMainWindow'dan miras alır, yani standart bir pencere (kapatma tuşu, başlık çubuğu olan) özelliğine sahiptir.
    """

    def __init__(self):
        super().__init__()  # Miras alınan QMainWindow sınıfının başlangıç ayarlarını yükler.
        self.setWindowTitle("Uçuş Logu ve Rota Görüntüleyici")  # Pencere başlığı
        self.setGeometry(100, 100, 900, 700)  # Pencerenin ekrandaki yeri (x, y) ve boyutu (genişlik, yükseklik)
        self.initUI()  # Arayüz elemanlarını yerleştiren fonksiyonu çağırır.

    def initUI(self):
        """
        Pencere içindeki tüm buton, yazı ve grafikleri yerleştirdiğimiz fonksiyondur.
        """
        # Ana Widget: PyQt'de her şeyin üzerinde durduğu bir zemin olmalıdır.
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # QVBoxLayout: Elemanları yukarıdan aşağıya (Vertical) dizer.
        main_layout = QVBoxLayout(central_widget)

        # --- ÜST PANEL (Giriş Alanı) ---
        # QHBoxLayout: Elemanları soldan sağa (Horizontal) dizer.
        input_layout = QHBoxLayout()

        # Bilgi etiketi (Label)
        lbl_info = QLabel("Uçuş ID (Örn: TK1923, TK2024):")
        lbl_info.setStyleSheet("font-weight: bold; font-size: 14px;")  # Yazı tipi ayarları (CSS benzeri)

        # Kullanıcının yazı yazacağı kutu (Input)
        self.entry_flight_id = QLineEdit()
        self.entry_flight_id.setPlaceholderText("Uçuş kodunu giriniz...")

        # Sorgulama butonu
        btn_query = QPushButton("Sorgula ve Çiz")
        btn_query.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        # Butona tıklandığında 'self.query_flight' fonksiyonunu çalıştırır.
        btn_query.clicked.connect(self.query_flight)

        # Oluşturduğumuz parçaları yatay düzene ekliyoruz.
        input_layout.addWidget(lbl_info)
        input_layout.addWidget(self.entry_flight_id)
        input_layout.addWidget(btn_query)

        # Yatay düzeni, ana dikey düzene ekliyoruz.
        main_layout.addLayout(input_layout)

        # --- BİLGİ PANELİ ---
        # Sonuçların yazılı olarak gösterileceği alan
        self.info_label = QLabel("Bilgi: Henüz bir sorgulama yapılmadı.")
        self.info_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)  # Çerçeve stili (içe göçük görünüm)
        self.info_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        main_layout.addWidget(self.info_label)

        # --- GRAFİK ALANI (Matplotlib) ---
        # Matplotlib Figure: Grafiğin çizileceği boş kağıt gibi düşünebilirsiniz.
        self.figure = Figure(figsize=(5, 4), dpi=100)
        # Canvas: Bu kağıdı PyQt penceresine yapıştıran aracıdır.
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        # Başlangıçta boş bir 3D eksen oluşturuyoruz (program açılınca boş grafik gözüksün diye).
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.ax.set_title("3D Uçuş Rotası")
        self.ax.set_xlabel("Enlem (Latitude)")
        self.ax.set_ylabel("Boylam (Longitude)")
        self.ax.set_zlabel("Yükseklik (Altitude)")

    def query_flight(self):
        """
        Butona basılınca çalışan fonksiyondur. Flask sunucusuna istek atar.
        """
        # Yazı kutusundaki metni alır ve boşlukları temizler (.strip())
        flight_id = self.entry_flight_id.text().strip()

        # Eğer kutu boşsa uyarı verip fonksiyondan çıkar.
        if not flight_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir Uçuş ID giriniz!")
            return

        try:
            # Flask Sunucusuna (önceki kodunuza) istek atar.
            # 127.0.0.1:5000 adresi kendi bilgisayarınızdaki Flask sunucusudur.
            url = f"http://127.0.0.1:5000/get_flight/{flight_id}"
            response = requests.get(url)

            # status_code 200 ise işlem başarılıdır.
            if response.status_code == 200:
                json_response = response.json()  # Gelen cevabı sözlüğe çevir.
                flight_data = json_response.get("data", [])
                # Veriyi görselleştirme fonksiyonuna gönder.
                self.visualize_flight(flight_id, flight_data)

            # status_code 404 ise uçuş bulunamamıştır.
            elif response.status_code == 404:
                QMessageBox.warning(self, "Bulunamadı", f"{flight_id} ID'li uçuş bulunamadı.")
                self.reset_info()  # Ekranı temizle
            else:
                QMessageBox.critical(self, "Hata", f"Sunucu hatası: {response.status_code}")

        # Eğer Flask sunucusu kapalıysa bu hata yakalanır.
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Bağlantı Hatası",
                                 "Flask sunucusuna bağlanılamadı.\nLütfen 'server.py' dosyasının çalıştığından emin olun.")

    def visualize_flight(self, flight_id, data):
        """
        Gelen veriyi işleyip grafiğe döken fonksiyondur.
        """
        # List Comprehension: Gelen veri listesinden sadece enlem, boylam ve yükseklikleri ayırır.
        lats = [point["lat"] for point in data]
        lons = [point["lon"] for point in data]
        alts = [point["alt"] for point in data]

        num_points = len(data)
        # İlk ve son noktayı bilgi paneline yazmak için metin hazırlar.
        start_point = f"({lats[0]}, {lons[0]}, {alts[0]}m)"
        end_point = f"({lats[-1]}, {lons[-1]}, {alts[-1]}m)"

        # 1. Bilgi Panelini Güncelle (HTML formatında kalın yazı kullanabiliriz)
        info_text = (f"<b>Uçuş ID:</b> {flight_id} | "
                     f"<b>Nokta Sayısı:</b> {num_points} | "
                     f"<b>İlk Konum:</b> {start_point} | "
                     f"<b>Son Konum:</b> {end_point}")
        self.info_label.setText(info_text)

        # 2. Grafiği Temizle ve Yeniden Çiz
        self.figure.clear()  # Önceki çizimi sil
        self.ax = self.figure.add_subplot(111, projection='3d')  # Yeni bir 3D alan oluştur

        # Rotayı Çiz (Mavi çizgi)
        self.ax.plot(lats, lons, alts, label=f'Rota: {flight_id}', color='blue', linewidth=2)

        # Başlangıç (Yeşil Nokta) ve Bitiş (Kırmızı Nokta) işaretle (Scatter plot)
        self.ax.scatter(lats[0], lons[0], alts[0], color='green', s=50, label='Başlangıç')
        self.ax.scatter(lats[-1], lons[-1], alts[-1], color='red', s=50, label='Bitiş')

        # Eksen isimlerini ve başlığı ayarla
        self.ax.set_title(f"3D Rota Analizi: {flight_id}")
        self.ax.set_xlabel("Enlem")
        self.ax.set_ylabel("Boylam")
        self.ax.set_zlabel("Yükseklik (m)")
        self.ax.legend()  # Renklerin ne anlama geldiğini gösteren kutucuğu (lejant) ekle

        # Canvas'ı güncelle: Bu komut çizimin ekrana yansımasını sağlar.
        self.canvas.draw()

    def reset_info(self):
        """
        Eğer uçuş bulunamazsa grafiği ve yazıları sıfırlayan yardımcı fonksiyon.
        """
        self.info_label.setText("Bilgi: Kayıt bulunamadı.")
        self.figure.clear()
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.ax.set_title("3D Uçuş Rotası")
        self.canvas.draw()


# Python dosyası doğrudan çalıştırıldığında burası devreye girer.
if __name__ == "__main__":
    # QApplication: Her PyQt uygulamasının çalışması için gereken ana nesnedir.
    app = QApplication(sys.argv)

    # Kendi yazdığımız pencere sınıfından bir örnek oluşturuyoruz.
    window = FlightTrackerApp()
    window.show()  # Pencereyi ekranda göster.

    # sys.exit(app.exec_()): Uygulama döngüsünü başlatır. Pencere kapatılana kadar programın kapanmamasını sağlar.
    sys.exit(app.exec_())