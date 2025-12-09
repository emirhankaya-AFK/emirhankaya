from flask import Flask, jsonify, \
    request  # Flask: Web sunucusu oluşturmak için. jsonify: Veriyi JSON formatına çevirmek için.
import json  # json: .json uzantılı dosyaları okuyup Python diline çevirmek için kullanılır.
import os  # os: İşletim sistemi işlemleri (dosya var mı yok mu kontrolü vb.) için kullanılır.

# Flask uygulamasını başlatıyoruz. '__name__' bu dosyanın ana program olduğunu belirtir.
app = Flask(__name__)

# JSON dosyasının bilgisayardaki tam yolu.
# r"..." (raw string) kullanımı, Windows dosya yollarındaki ters eğik çizgilerin (\) hata vermesini engeller.
DATA_FILE = r"C:\Users\berke\Desktop\ucus_log.json"


def load_data():
    """
    Bu fonksiyonun görevi: ucus_log.json dosyasını diskten okumak ve
    Python'un anlayabileceği bir sözlük (dictionary) yapısına çevirmektir.
    """
    # os.path.exists: Belirtilen yolda böyle bir dosya var mı diye kontrol eder.
    if not os.path.exists(DATA_FILE):
        return {}  # Dosya yoksa hata vermek yerine boş bir veri döndürür.

    # Dosyayı okuma modunda ('r') ve Türkçe karakter desteğiyle ('utf-8') açar.
    # 'with open' yapısı, işlem bitince dosyayı otomatik olarak kapatır (güvenlidir).
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)  # JSON dosyasındaki metni Python verisine dönüştürür.
        except json.JSONDecodeError:
            return {}  # Eğer dosya içeriği bozuksa programın çökmemesi için boş döner.


# @app.route: Web tarayıcısından hangi adrese gidilince hangi fonksiyonun çalışacağını belirler.
# <flight_id>: Adresteki değişken kısımdır. Örn: /get_flight/TK1923 yazıldığında 'TK1923' buraya gelir.
# methods=['GET']: Bu adresin sadece veri çekmek (GET) için kullanılacağını belirtir.
@app.route('/get_flight/<flight_id>', methods=['GET'])
def get_flight(flight_id):
    """
    İstenilen uçuş ID'sine (örn: TK123) ait log verilerini bulup kullanıcıya döner.
    """
    # Önce yukarıda yazdığımız load_data fonksiyonunu çağırıp tüm veriyi dosyadan çeker.
    data = load_data()

    # data.get(...): Sözlük içinde arama yapar.
    # flight_id.upper(): Kullanıcı 'tk123' yazsa bile onu 'TK123' yapar, çünkü genelde kodlar büyük harflidir.
    flight_data = data.get(flight_id.upper())

    if flight_data:
        # Eğer aranan uçuş kodu bulunduysa, kullanıcıya dönecek cevabı hazırlarız.
        response = {
            "status": "success",  # İşlemin başarılı olduğunu belirten mesaj
            "flight_id": flight_id,  # Aranan ID
            "data": flight_data  # Dosyadan bulunan detaylı uçuş verisi
        }
        # jsonify(response): Python sözlüğünü tarayıcının anlayacağı JSON formatına çevirir.
        # 200: HTTP protokolünde "İşlem Başarılı" (OK) anlamına gelen koddur.
        return jsonify(response), 200
    else:
        # Eğer uçuş ID dosyada bulunamazsa:
        # 404: HTTP protokolünde "Bulunamadı" (Not Found) anlamına gelen hata kodudur.
        return jsonify({"status": "error", "message": "Uçuş ID bulunamadı."}), 404


# Bu blok, dosya doğrudan çalıştırıldığında (import edilmediğinde) devreye girer.
if __name__ == '__main__':
    print(f"Flask Sunucusu Başlatılıyor... Veri dosyası: {DATA_FILE}")

    # app.run: Web sunucusunu ayağa kaldırır.
    # debug=True: Hata ayıklama modunu açar. Kodda değişiklik yaparsan sunucu otomatik yeniden başlar.
    # port=5000: Sunucunun yayın yapacağı kapı numarası (localhost:5000).
    app.run(debug=True, port=5000)