# Elektrik Tüketim Planlayıcı

Evde veya küçük bir işletmede hangi cihazın ayda ne kadar elektrik tükettiğini görmek için tarayıcıda çalışan ücretsiz bir hesaplayıcı.

## Ne işe yarar?

- Cihaz gücü, adet, günlük kullanım ve aylık gün bilgisiyle kWh hesaplar.
- Bekleme tüketimini aktif tüketimden ayrı gösterir.
- İki kademeli tarifeyi ve ek vergi/oranları kullanıcının girdiği değerlerle hesaplar.
- Mevcut kullanım ile planlanan kullanım süresini karşılaştırır.
- Verileri yalnızca tarayıcıda saklar; bir sunucuya göndermez.
- JSON yedeği ve Excel uyumlu CSV raporu üretir.
- İlk açılıştan sonra service worker sayesinde çevrimdışı kullanılabilir.

Uygulamada güncel tarife fiyatı sabitlenmemiştir. Tarife; dönem, abone grubu ve mevzuata göre değişebildiği için kullanıcı kendi faturasındaki değerleri girer.

## Hesaplama

```text
aktif kWh = watt × adet × saat/gün × gün/ay ÷ 1000
bekleme kWh = bekleme watt × adet × (24 - aktif saat) × gün/ay ÷ 1000
```

Toplam tüketim önce alt kademeye, sınırı aşan bölüm üst kademeye uygulanır. Cihaz maliyetleri toplam faturanın ortalama birim maliyetiyle oransal dağıtılır; bu nedenle cihaz satırları yaklaşık pay gösterir.

## Yerelde çalıştırma

```bash
npm install
npm test
python -m http.server 8080
```

Ardından `http://127.0.0.1:8080` adresini açın. Service worker, `file://` üzerinden çalışmaz.

## Sınırlar

Bu araç fatura düzenlemez ve resmi tarife kaynağı değildir. Cihaz etiketi nominal gücü gösterir; termostat, inverter, yük profili ve gerçek çalışma döngüsü sonucu değiştirebilir. En doğru karşılaştırma için priz tipi enerji ölçer veya akıllı sayaç verisi kullanılmalıdır.

## Lisans

MIT
