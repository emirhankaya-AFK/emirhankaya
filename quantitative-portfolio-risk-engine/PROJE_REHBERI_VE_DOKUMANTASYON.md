# 🏛️ Kantitatif Portföy Optimizasyonu & Risk Analitiği Motoru (v2.1)
## Kapsamlı Proje Rehberi, Girdi/Çıktı Analizi ve Kaynak Kod Dokümantasyonu

Bu belge; projenin mimari yapısını, ne tür girdiler kabul ettiğini, arka planda çalışan finans mühendisliği ve ekonometri modellerini, ürettiği çıktıları, gerçekleştirilen denetim düzeltmelerini ve kaynak dosyaların detaylı fihristini içermektedir.

---

## 📌 1. Proje Ne Amaçlıyor ve Ne İstiyor? (Project Objectives & Scope)

### A. Projenin Temel Amacı
Geleneksel portföy yönetimi genellikle sezgisel varsayımlara veya basit varyans modellerine dayanır. Bu proje; kantitatif portföy yönetimi, finans mühendisliği ve ekonometri prensiplerini bir araya getirerek:
1. **Çoklu Para Birimi Normalizasyonu (Multi-Currency Translation):** Portföyde hem Türk Lirası (BIST 100, BIST Bankacılık) hem de ABD Doları (S&P 500, US 10Y Tahvil, Ons Altın, Brent Petrol, Bitcoin) cinsinden fiyatlanan varlıkları dinamik USD/TRY kuru üzerinden seçilen baz para birimine (TRY veya USD) bileşik formülle dönüştürmek,
2. **Modern Portföy Teorisi & Sayısal Teşhis (Markowitz MPT):** Karesel programlama (SLSQP) ile Maksimum Sharpe ve Minimum Volatilite portföylerini hesaplamak; çözümsüz veya uygunsuz kısıt durumlarında hatayı kullanıcıdan gizlemeden doğrudan açıklayıcı teşhis mesajı dönmek,
3. **Bayesçi Black-Litterman Modeli:** Piyasa dengesi örtük getirilerini (Prior $\Pi$) analist görüşleri ($P, Q$) ve güven matrisi ($\Omega$) ile Bayesçi güncellemeye tabi tutarak aşırı uç ağırlık dağılımlarını törpülemek,
4. **Ekstrem Kuyruk Riski & Analitik Cornish-Fisher ES:** Finansal krizlerde normal dağılımın yetersizliğini aşmak üzere Cornish-Fisher kantil açılımının Hermite polinomları üzerinden **analitik kapalı formül integraliyle** Expected Shortfall (CVaR) hesaplamak,
5. **10 Günlük Çok Adımlı Bileşik Monte Carlo Yol Simülasyonu:** Analitik $\sqrt{T}$ kısayolu yerine 10 günlük ufukta $N$ adet yol boyunca $R_i^{(10)} = \prod_{t=1}^{10}(1+r_{i,t}) - 1$ bileşik getirisini simüle etmek,
6. **GARCH(1,1) Koşullu Değişen Varyans:** Finansal zaman serilerindeki oynaklık kümelenmesini (volatility clustering) saf SciPy En Çok Olabilirlik Yöntemi (MLE) ile modellemek ve 30 günlük projeksiyon üretmek,
7. **Basel III / BCBS Trafik Işığı & Kupiec POF Geriye Dönük Risk Testi (Backtest):** Son 250 işlem günündeki gerçekleşen portföy getirilerini 1-günlük %99 VaR tahminleriyle kıyaslayarak istatistiksel hata oranını (POF LR testi) ve düzenleyici sermaye yeterlilik bölgesini (Yeşil / Sarı / Kırmızı) raporlamak.

---

### B. Proje Ne Tür Girdiler İstiyor? (Inputs Required)

| Girdi Türü | Parametre / Veri | Açıklama |
|---|---|---|
| **1. Piyasa Veri Kaynağı** | `data_source` | Panel kenar çubuğundan seçilebilir: <br>• **Sentetik Kurumsal Veri:** 5 yıllık (1.260 işlem günü), Monte Carlo ve Student-t şoklarıyla üretilmiş offline deterministik CSV verisi (Tohum: 42). <br>• **Yahoo Finance (yfinance):** Yahoo Finance API üzerinden çekilen günlük kapanış fiyatları. |
| **2. Portföy Baz Para Birimi** | `base_currency` ('TRY' veya 'USD') | Portföyün hangi para birimi cinsinden değerlendirileceği. Kur riski getirisi $R_{TRY} = (1 + R_{USD})(1 + R_{FX}) - 1$ ile dönüştürülür. |
| **3. Makro Finans Parametreleri** | Risksiz Faiz Oranı ($R_f$) | Baz para birimindeki risksiz getiri oranı (TRY için varsayılan: %15.0, USD için: %4.5). |
| **4. Matris Kondisyon Ayarı** | Ledoit-Wolf Büzülme (Toggle) | Örneklem kovaryans matrisindeki örneklem gürültüsünü sabit korelasyonlu hedef matrisle filtreleme tercihi. |
| **5. Yatırımcı Görüşleri (Views)** | Sübjektif Öngörüler ($P, Q$) | Yatırımcının piyasa beklentileri: <br>• **Göreceli Görüş (Relative):** "BIST 100, S&P 500'den %6 daha iyi getiri sağlayacak." <br>• **Mutlak Görüş (Absolute):** "Altın bu yıl %18 getiri üretecek." |
| **6. Görüş Güven Düzeyleri** | Güven Skalası ($c \in [10\%, 95\%]$) | Yatırımcının kendi görüşüne dair belirlediği güven parametresi. |
| **7. Risk Zaman Ufku (Horizon)** | 1 Günlük veya 10 Günlük | 10 günlük ufukta analitik ölçekleme yerine gerçek 10 günlük örtüşen bileşik getiriler ve 10 adımlı Monte Carlo yol simülasyonu kullanılır. |
| **8. Stres Testi Seçimleri** | Kriz Senaryosu & Sermaye Tutarı | 2008 Küresel Kriz, COVID-19, Stagflasyon veya Jeopolitik Enerji Şoku senaryoları ve nominal portföy tutarı. |

---

## 🎯 2. Proje Ne Tür Çıktılar Üretiyor? (Outputs Produced)

1. **Markowitz Etkin Sınır (Efficient Frontier):**
   - Minimum varyans ile maksimum beklenen getiriyi veren kuadratik eğri.
   - 4.000 adet Dirichlet dağılımlı simüle edilmiş Monte Carlo portföy bulutu.
   - **Maksimum Sharpe Portföyü (Tangency Portfolio):** Risk başına en yüksek birim primi veren optimal varlık ağırlıkları.
   - **Minimum Volatilite Portföyü (GMV):** Portföy varyansını minimuma indiren dağılım.
   - **Çözücü Teşhis Raporu:** Kısıtların fizibilitesi ve çözücü yakınsama mesajı (`success`, `solver_message`).
2. **Bayesian Black-Litterman Çıktıları:**
   - **Piyasa İma Edilen Denge Getirileri (Prior $\Pi$):** Ters optimizasyon ile piyasanın fiyatladığı beklenen getiriler.
   - **Bayesyen Posterior Getiriler ($\mu_{BL}$):** Piyasa dengesi ile analist görüşlerinin Bayesyen harmanı.
   - **Optimal Portföy Ağırlıkları:** Görüşlerin portföy tahsisatına yansıyan net yüzde değişimleri.
3. **İleri Düzey Risk Analitiği & Kuyruk Riski:**
   - **1 Günlük ve 10 Günlük Risk Karşılaştırma Matrisi:** Parametrik Gauss, Cornish-Fisher, Tarihsel Simülasyon ve Monte Carlo metotlarının tamamı için bağımsız ve gerçek hesaplamalar. Hiçbir hücrede sahte/sabit string veya heuristik çarpan bulunmaz.
   - **Cornish-Fisher Analitik Kapalı Formül Expected Shortfall (CVaR):** Hermite polinomlarının standart Gauss ölçüsü altında analitik integrasyonu ile makine duyarlılığında ($10^{-16}$) hesaplanan kesin akademik değer.
   - **10 Günlük Monte Carlo Dağılımı:** 10 adımlı bileşik path simülasyonuyla üretilen 10.000 adet getiri yolu ve kuyruk kesimleri.
4. **GARCH(1,1) Dinamik Koşullu Volatilite:**
   - Son 120 günlük geçmiş koşullu volatilite serisi ($\sigma_t$).
   - 30 günlük ileriye dönük volatilite projeksiyonu, Log-Likelihood skoru ve uzun vadeli koşulsuz varyansa yakınsama hızı.
5. **Basel III / BCBS Trafik Işığı & Kupiec POF Geriye Dönük Risk Testi (Backtest):**
   - Son 250 işlem gününde 1 günlük %99 VaR modelinin gerçekleşen portföy kayıplarıyla test edilmesi.
   - Kupiec Olabilirlik Oranı (POF) test istatistiği ($LR_{POF}$) ve $p$-değeri.
   - Basel Komitesi standartlarında Trafik Işığı Bölgesi (Yeşil: $\le 4$ ihlal, Sarı: 5-9 ihlal, Kırmızı: $\ge 10$ ihlal) ve sermaye çarpanı ($3.00\times - 4.00\times$).
   - Günlük getiri ve VaR eşiği ihlal noktalarının interaktif zaman serisi grafiği.
6. **Makro Stres Testi Raporu:**
   - Seçilen kriz senaryosunda portföyün toplam sermaye kaybı (Drawdown %).
   - Net nominal kâr/zarar etkisi ve varlık bazında risk katkıları.
   - Portföy Dayanıklılık Notu (A+, A, B, C, D).

---

## 📂 3. Kaynak Kod Dosyaları ve Mimari Fihristi (Source Code Directory)

```text
quantitative-portfolio-risk-engine/
│
├── data/                                    # Veri Katmanı
│   ├── generate_market_data.py              # 5 yıllık çoklu varlık piyasa veri simülatörü
│   └── institutional_market_data.csv        # 1.260 işlem günü x 8 varlık fiyat zaman serisi
│
├── src/                                     # Analitik ve Matematiksel Motor Katmanı
│   ├── __init__.py                          # Paket başlangıç dosyası
│   ├── data_adapter.py                      # Modüler veri bağdaştırıcı katmanı (SyntheticCSVAdapter & YahooFinanceAdapter)
│   ├── data_loader.py                       # Veri yükleme, TRY/USD kur dönüşümü, getiri hesaplama ve adaptör desteği
│   ├── portfolio_optimizer.py               # Markowitz MPT, Ledoit-Wolf büzülme, Etkin Sınır ve teşhis raporu
│   ├── black_litterman.py                   # Bayesian Black-Litterman ters optimizasyon ve görüş motoru
│   └── risk_engine.py                       # Analitik CF-CVaR, çok adımlı MC, GARCH(1,1), Kupiec POF Backtest & Stres Testi
│
├── dashboard/                               # Kullanıcı Arayüzü Katmanı
│   ├── __init__.py
│   ├── theme.py                             # Institutional Risk Terminal merkezi tasarım sistemi
│   └── app.py                               # Institutional Risk Terminal Streamlit kokpiti (5 ana bölüm, 2 adımlı güvenli kapatma)
│
├── tests/                                   # Otomasyon ve Bağımsız Doğrulama Katmanı
│   ├── __init__.py
│   ├── run_math_audit.py                    # 8 adımlı bağımsız çalışan matematik ve istatistik denetim betiği
│   ├── test_currency_and_diagnostics.py     # Kur dönüşümü, CF-CVaR analitik referans, MC path ve Backtest testleri (8 test)
│   ├── test_data_loader.py                  # Veri bütünlüğü ve zaman serisi testleri (4 test)
│   ├── test_portfolio_optimizer.py          # Optimizasyon matematik ve sınır testleri (6 test)
│   ├── test_black_litterman.py              # Bayesyen güncelleme ve duyarlılık testleri (5 test)
│   └── test_risk_engine.py                  # VaR/CVaR tutarlılığı ve GARCH durağanlık testleri (5 test)
│
├── requirements.txt                         # Proje bağımlılıkları (numpy, pandas, scipy, sklearn, streamlit, plotly, pytest, yfinance)
├── README.md                                # Çift dilli (TR/EN) teknik tanıtım dokümanı
└── PROJE_REHBERI_VE_DOKUMANTASYON.md        # Bu kapsamlı detaylı kullanım ve metodoloji rehberi
```

---

## 🧮 4. Matematiksel Formüller ve Akademik Temeller

### A. Para Birimi Getiri Dönüşümü (Currency Translation)
Yerel para birimindeki bir varlığın getirisi $R_{i, USD}$ ve kur getirisi $R_{USDTRY}$ olduğunda:
$$R_{i, TRY} = (1 + R_{i, USD})(1 + R_{USDTRY}) - 1$$
Ters yönde USD bazına geçerken:
$$R_{i, USD} = \frac{1 + R_{i, TRY}}{1 + R_{USDTRY}} - 1$$

### B. Ledoit-Wolf Kovaryans Büzülme (Shrinkage)
Örneklem kovaryansı $\mathbf{S}$ ile yapılandırılmış sabit korelasyon hedef matrisi $\mathbf{F}$ optimal katsayı $\delta^* \in [0, 1]$ ile harmanlanır:
$$\boldsymbol{\Sigma}_{shrunk} = \delta^* \mathbf{F} + (1 - \delta^*) \mathbf{S}$$

### C. Bayesçi Black-Litterman Modeli
İçsel piyasa denge getirisi (Prior):
$$\boldsymbol{\Pi} = \lambda \boldsymbol{\Sigma} \mathbf{w}_{mkt}, \quad \lambda = \frac{E[R_{mkt}] - R_f}{\sigma_{mkt}^2}$$
Analist görüş matrisi $\mathbf{P}$, getiri vektörü $\mathbf{Q}$ ve belirsizlik kovaryansı $\boldsymbol{\Omega}$ ile sonsal getiri:
$$E[\mathbf{R}] = \left[(\tau \boldsymbol{\Sigma})^{-1} + \mathbf{P}^T \boldsymbol{\Omega}^{-1} \mathbf{P}\right]^{-1} \left[(\tau \boldsymbol{\Sigma})^{-1} \boldsymbol{\Pi} + \mathbf{P}^T \boldsymbol{\Omega}^{-1} \mathbf{Q}\right]$$

### D. Cornish-Fisher Analitik Kapalı Formül Expected Shortfall (CVaR)
Taylor serisi açılımı ile çarpıklık ($S$) ve basıklık ($K$) düzeltmeli kantil $z_{CF}(\alpha)$:
$$z_{CF}(\alpha) = z_\alpha + \frac{S}{6}(z_\alpha^2 - 1) + \frac{K}{24}(z_\alpha^3 - 3z_\alpha) - \frac{S^2}{36}(2z_\alpha^2 - 5z_\alpha)$$
> [!NOTE]
> Çok günlük ufuklarda ($T > 1$, örn. 10 gün), günlük çarpıklık ve basıklık değerlerinin doğrudan kopyalanması istatistiki bozulmaya yol açacağından, model momentleri ($S, K, \mu, \sigma$) doğrudan 10 günlük örtüşen bileşik getiri serisinden ($R_{10} = \prod_{t=1}^{10}(1+r_t)-1$) hesaplar.

Hermite polinomlarının standart Gauss ölçüsü altında $\int_\alpha^1 z_{CF}(u)du = \int_{z_\alpha}^\infty z_{CF}(\Phi(z))\phi(z)dz$ integrasyonu ile:
$$CVaR_{CF}(\alpha) = -\mu + \sigma \frac{\phi(z_\alpha)}{1 - \alpha} \left[ 1 + \frac{S}{6} z_\alpha + \frac{K}{24}(z_\alpha^2 - 1) - \frac{S^2}{36}(2z_\alpha^2 - 1) \right]$$
Bu formül sayısal kesme hatalarını sıfırlayarak analitik kesinlik sağlar.

### E. 10 Günlük Çok Adımlı Monte Carlo Simülasyonu
$T = 10$ işlem günü için $N = 10.000$ adet Student-t ağır kuyruk yolu:
$$r_{i, t} = \mu_{daily} + \sigma_{daily} \cdot \tilde{z}_{i, t}, \quad \tilde{z}_{i, t} \sim t_{df=7}$$
$$R_i^{(10)} = \prod_{t=1}^{10} (1 + r_{i, t}) - 1$$

### F. Basel III / BCBS Kupiec POF Likelihood Ratio Backtesting
Gözlem sayısı $N$, gerçekleşen ihlal $x$, beklenen ihlal oranı $p = 1 - \alpha$ ve gerçekleşen oran $\hat{p} = x/N$:
$$LR_{POF} = 2 \left[ x \ln\left(\frac{\hat{p}}{p}\right) + (N - x) \ln\left(\frac{1 - \hat{p}}{1 - p}\right) \right] \sim \chi^2(1)$$
Basel Komitesi Trafik Işığı (250 gün, 1 günlük %99 VaR - BCBS CRE53 Standart Çizelgesi):
- **Yeşil Bölge (0–4 ihlal):** Model geçerli, yasal çarpan $3.00\times$.
- **Sarı Bölge (5–9 ihlal):** Denetim uyarısı, BCBS CRE53 kademeli sermaye çarpanı cezası:
  - 5 ihlal: $3.40\times$
  - 6 ihlal: $3.50\times$
  - 7 ihlal: $3.65\times$
  - 8 ihlal: $3.75\times$
  - 9 ihlal: $3.85\times$
- **Kırmızı Bölge (10+ ihlal):** Model reddedilir, yasal çarpan $4.00\times$.

---

## 🔒 5. Güvenlik Mekanizması: Kapatma Koruması

İnternetten erişen herhangi bir ziyaretçinin sunucuyu tek tıkla kapatmasını önlemek amacıyla iki katmanlı koruma uygulanmıştır:
1. **Varsayılan Koruma (`ENABLE_SHUTDOWN="false"`):** Çevre değişkeni atanmadığında veya `false` olduğunda sunucu kapatma arayüzü tamamen gizlenir, yerine `🔒 Güvenli Sunucu` statüsü gösterilir.
2. **İki Aşamalı Onay Mekanizması:** `ENABLE_SHUTDOWN="true"` olarak ayarlandığında bile doğrudan kapatılmaz; kullanıcı "⏻ Kapat" düğmesine bastığında ekranda onay kartı açılır (`[🛑 Evet, Sunucuyu Kapat]` ve `[❌ Vazgeç / İptal]`).

---

## 🧪 6. Doğrulama ve Test Sonuçları

1. **Pytest Birim ve Entegrasyon Test Paketi:**
   ```bash
   python -m pytest tests/ -v
   # Sonuç: 30 passed, 0 warnings in 2.36s (100% Başarı)
   ```
2. **Bağımsız 8 Adımlı Matematik Denetimi:**
   ```bash
   python tests/run_math_audit.py

   # Sonuç:
   # 1. Covariance Positive Definite: PASS (min eigval: 0.002889)
   # 2. Ledoit-Wolf Shrinkage Delta: PASS (0.0050)
   # 3. Markowitz Weights & Sharpe: PASS (Max Sharpe: 1.82, Min Vol: 1.26)
   # 4. Black-Litterman Bayesian Posterior: PASS
   # 5. VaR & CVaR Ordering: PASS (Parametric VaR: 2.03%, CVaR: 2.60%)
   # 6. GARCH(1,1) Stationarity: PASS (alpha+beta = 0.7789 < 1.0)
   # 7. Cornish-Fisher Analytical Closed-Form: PASS (Divergence vs Quad: 2.78e-17 < 1e-8)
   # 8. Basel III & Kupiec POF Backtest: PASS (3 breaches in 250d, GREEN)
   # === ALL 8 MATHEMATICAL CHECKS PASSED PERFECTLY! ===
   ```
3. **Streamlit Smoke Testi:**
   `http://localhost:1001` adresinde HTTP 200 OK ile sorunsuz yanıt vermektedir.
