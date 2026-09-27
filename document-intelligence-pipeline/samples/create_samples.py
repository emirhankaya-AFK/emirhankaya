"""
Generate synthetic Turkish sample PDF documents for testing.
Uses reportlab to create realistic-looking invoices, contracts, and technical docs.
All companies and persons are fictional.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, grey
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT

# Colours
NAVY = HexColor("#1e3a5f")
LIGHT_GREY = HexColor("#f5f5f5")
MID_GREY = HexColor("#cccccc")
RED = HexColor("#c0392b")

styles = getSampleStyleSheet()


def _style(name: str, **kwargs) -> ParagraphStyle:
    base = styles["Normal"]
    return ParagraphStyle(name, parent=base, **kwargs)


def _doc(path: Path, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=title,
    )


# ===========================================================================
# INVOICE 1 — Standard e-Fatura
# ===========================================================================

def create_invoice_1(out_path: Path) -> None:
    doc = _doc(out_path, "Örnek E-Fatura")
    elems = []

    h1 = _style("h1", fontSize=18, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=4)
    sub = _style("sub", fontSize=9, textColor=grey, spaceAfter=2)
    normal = _style("norm", fontSize=10, spaceAfter=4)
    bold = _style("bold", fontSize=10, fontName="Helvetica-Bold", spaceAfter=4)
    right = _style("right", fontSize=10, alignment=TA_RIGHT)

    elems.append(Paragraph("ÖRNEK TİCARET A.Ş.", h1))
    elems.append(Paragraph("Atatürk Cad. No:42, Kadıköy / İstanbul", sub))
    elems.append(Paragraph("VKN: 1234567890  |  Tel: 0212 555 00 00  |  info@ornekticaret.com.tr", sub))
    elems.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=8))

    # Header table
    header_data = [
        [Paragraph("<b>E-FATURA</b>", _style("fh", fontSize=14, textColor=NAVY, fontName="Helvetica-Bold")),
         Paragraph("Fatura No: <b>FTR-2024-001234</b>", right)],
        ["", Paragraph("Tarih: 15.03.2024", right)],
        ["", Paragraph("Vade Tarihi: 15.04.2024", right)],
    ]
    ht = Table(header_data, colWidths=["50%", "50%"])
    ht.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elems.append(ht)
    elems.append(Spacer(1, 12))

    # Buyer info
    elems.append(Paragraph("ALICI BİLGİLERİ", bold))
    elems.append(Paragraph("Test Yapı Malzemeleri Ltd. Şti.", normal))
    elems.append(Paragraph("Alıcı VKN: 9876543210", normal))
    elems.append(Paragraph("Bağcılar Sanayi Sitesi No:7, Bağcılar / İstanbul", normal))
    elems.append(Spacer(1, 8))

    # Line items table
    elems.append(Paragraph("MAL/HİZMET DETAYI", bold))
    item_data = [
        ["Açıklama", "Miktar", "Birim Fiyat (TL)", "Tutar (TL)"],
        ["Yazılım Geliştirme Hizmeti - Ocak 2024", "1", "15.000,00", "15.000,00"],
        ["Proje Yönetimi Danışmanlığı", "2", "3.500,00", "7.000,00"],
        ["Sunucu Altyapı Kurulumu", "1", "5.500,00", "5.500,00"],
        ["Yıllık Bakım ve Destek Paketi", "1", "2.500,00", "2.500,00"],
    ]
    it = Table(item_data, colWidths=["45%", "15%", "20%", "20%"])
    it.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    elems.append(it)
    elems.append(Spacer(1, 8))

    # Totals
    totals = [
        ["Ara Toplam:", "30.000,00 TL"],
        ["KDV Oranı:", "%20"],
        ["KDV Tutarı:", "6.000,00 TL"],
        [Paragraph("<b>Genel Toplam:</b>", bold), Paragraph("<b>36.000,00 TL</b>", _style("bt", fontSize=11, fontName="Helvetica-Bold", alignment=TA_RIGHT))],
    ]
    tt = Table(totals, colWidths=["70%", "30%"])
    tt.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, NAVY),
    ]))
    elems.append(tt)
    elems.append(Spacer(1, 16))

    # Payment info
    elems.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=6))
    elems.append(Paragraph("ÖDEME BİLGİLERİ", bold))
    elems.append(Paragraph("Ödeme Koşulları: 30 gün net", normal))
    elems.append(Paragraph("IBAN: TR33 0006 1005 1978 6457 8413 26", normal))
    elems.append(Paragraph("Banka: Örnek Bankası A.Ş. — Kadıköy Şubesi", normal))
    elems.append(Paragraph("Para Birimi: TRY", normal))

    doc.build(elems)
    print(f"  ✅ {out_path}")


# ===========================================================================
# INVOICE 2 — USD international
# ===========================================================================

def create_invoice_2(out_path: Path) -> None:
    doc = _doc(out_path, "Uluslararası Fatura")
    elems = []
    h1 = _style("h1", fontSize=16, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=4)
    normal = _style("norm", fontSize=10, spaceAfter=4)
    bold = _style("bold", fontSize=10, fontName="Helvetica-Bold", spaceAfter=4)

    elems.append(Paragraph("GLOBAL TEKNOLOJİ ÇÖZÜMLERİ A.Ş.", h1))
    elems.append(Paragraph("VKN: 5544332211", normal))
    elems.append(Paragraph("Fatura No: INV-2024-0089", bold))
    elems.append(Paragraph("Fatura Tarihi: 01.06.2024", normal))
    elems.append(Paragraph("Vade Tarihi: 30.06.2024", normal))
    elems.append(Spacer(1, 8))
    elems.append(Paragraph("Alıcı: Sample Corp International Ltd.", bold))
    elems.append(Paragraph("Alıcı VKN: 1122334455", normal))

    item_data = [
        ["Mal/Hizmet Adı", "Adet", "Birim Fiyat", "Tutar"],
        ["API Integration Service", "1", "USD 5,000.00", "USD 5,000.00"],
        ["Cloud Migration Consulting", "3", "USD 1,200.00", "USD 3,600.00"],
    ]
    it = Table(item_data, colWidths=["50%", "10%", "20%", "20%"])
    it.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    elems.append(it)
    elems.append(Spacer(1, 8))
    elems.append(Paragraph("Ara Toplam: USD 8,600.00", normal))
    elems.append(Paragraph("KDV: %0 (İhracat Faturası)", normal))
    elems.append(Paragraph("Genel Toplam: USD 8,600.00", bold))
    elems.append(Paragraph("Para Birimi: USD", normal))
    elems.append(Paragraph("IBAN: TR61 0013 4000 0196 0063 5150 01", normal))
    elems.append(Paragraph("Ödeme Koşulları: 30 gün net", normal))
    doc.build(elems)
    print(f"  ✅ {out_path}")


# ===========================================================================
# INVOICE 3 — Incomplete (missing fields — for validation testing)
# ===========================================================================

def create_invoice_3(out_path: Path) -> None:
    doc = _doc(out_path, "Eksik Fatura")
    elems = []
    normal = _style("norm", fontSize=10, spaceAfter=4)
    bold = _style("bold", fontSize=10, fontName="Helvetica-Bold", spaceAfter=4)

    elems.append(Paragraph("Eksik Satıcı Faturası", bold))
    elems.append(Paragraph("(Bu fatura kasıtlı olarak eksik alanlar içermektedir — doğrulama testi için)", normal))
    elems.append(Spacer(1, 8))
    # Intentionally missing: fatura_no, satici_vkn, IBAN
    elems.append(Paragraph("Tarih: 20.07.2024", normal))
    elems.append(Paragraph("Alıcı: Anonim Müşteri A.Ş.", normal))
    elems.append(Paragraph("Toplam Tutar: 5.000,00 TL", normal))
    elems.append(Paragraph("KDV Oranı: %20", normal))
    elems.append(Paragraph("KDV Tutarı: 833,33 TL", normal))  # intentional conflict: 5000*0.20 != 833.33
    elems.append(Paragraph("Ara Toplam: 4.166,67 TL", normal))
    doc.build(elems)
    print(f"  ✅ {out_path}")


# ===========================================================================
# CONTRACT 1 — Service agreement
# ===========================================================================

def create_contract_1(out_path: Path) -> None:
    doc = _doc(out_path, "Hizmet Sözleşmesi")
    elems = []
    h1 = _style("h1", fontSize=16, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=6)
    h2 = _style("h2", fontSize=12, fontName="Helvetica-Bold", textColor=NAVY, spaceBefore=10, spaceAfter=4)
    normal = _style("norm", fontSize=10, spaceAfter=4, leading=14)

    elems.append(Paragraph("HİZMET SÖZLEŞMESİ", h1))
    elems.append(Paragraph("Sözleşme No: SZ-2024-0042", normal))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=8))

    elems.append(Paragraph("TARAFLAR", h2))
    elems.append(Paragraph(
        "<b>İşveren:</b> Alfa Yazılım ve Danışmanlık A.Ş., Maslak Mahallesi, Büyükdere Cad. "
        "No: 255, Sarıyer / İstanbul, VKN: 3344556677",
        normal
    ))
    elems.append(Paragraph(
        "<b>Yüklenici:</b> Beta Teknoloji Çözümleri Ltd. Şti., Çankaya / Ankara, VKN: 7788990011",
        normal
    ))
    elems.append(Spacer(1, 6))

    elems.append(Paragraph("MADDE 1 — KONU VE KAPSAM", h2))
    elems.append(Paragraph(
        "İş bu sözleşme, Yüklenici tarafından İşveren'e sağlanacak yazılım geliştirme ve "
        "teknik danışmanlık hizmetlerinin kapsamını, bedelini ve koşullarını belirlemek amacıyla "
        "01.01.2024 tarihinden itibaren akdedilmiştir.", normal
    ))

    elems.append(Paragraph("MADDE 2 — SÜRE", h2))
    elems.append(Paragraph("Sözleşme süresi 12 aylık olup 01.01.2024 tarihinde başlar ve 31.12.2024 tarihinde sona erer.", normal))
    elems.append(Paragraph("Başlangıç tarihi: 01.01.2024", normal))
    elems.append(Paragraph("Bitiş tarihi: 31.12.2024", normal))

    elems.append(Paragraph("MADDE 3 — ÖDEME KOŞULLARI", h2))
    elems.append(Paragraph(
        "Ödeme koşulları: Her ayın son iş günü fatura kesilecek olup 30 gün net vadeli ödeme "
        "yapılacaktır. Aylık hizmet bedeli 45.000,00 TL + KDV olarak belirlenmiştir.", normal
    ))

    elems.append(Paragraph("MADDE 4 — FESİH ŞARTLARI", h2))
    elems.append(Paragraph(
        "Fesih halinde taraflardan biri diğerine 30 gün önceden yazılı bildirimde bulunmak zorundadır.", normal
    ))
    elems.append(Paragraph(
        "Sözleşme feshedilebilir; ancak fesih tarihine kadar tamamlanan işlerin bedeli "
        "Yüklenici'ye ödenecektir.", normal
    ))

    elems.append(Paragraph("MADDE 5 — CEZA KLOZU", h2))
    elems.append(Paragraph(
        "Ceza klozu: Teslim gecikmesi durumunda her gecikme günü için sözleşme bedelinin "
        "binde biri (%0.1) oranında gecikme cezası uygulanır.", normal
    ))

    elems.append(Paragraph("MADDE 6 — GİZLİLİK", h2))
    elems.append(Paragraph(
        "Gizlilik yükümlülüğü kapsamında Yüklenici, sözleşme süresince ve sözleşmenin sona "
        "ermesinden itibaren 3 yıl boyunca İşveren'e ait gizli bilgileri ifşa edemez.", normal
    ))

    elems.append(Paragraph("İMZALAYANLAR", h2))
    sign_data = [
        ["İşveren Yetkilisi", "Yüklenici Yetkilisi"],
        [Paragraph("İmzalayan: Ahmet Yılmaz", normal), Paragraph("İmzalayan: Mehmet Demir", normal)],
        ["Tarih: 28.12.2023", "Tarih: 28.12.2023"],
    ]
    st = Table(sign_data, colWidths=["50%", "50%"])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GREY),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elems.append(st)
    elems.append(Paragraph("İmza Tarihi: 28.12.2023", normal))
    doc.build(elems)
    print(f"  ✅ {out_path}")


# ===========================================================================
# CONTRACT 2 — Confidentiality / NDA
# ===========================================================================

def create_contract_2(out_path: Path) -> None:
    doc = _doc(out_path, "Gizlilik Sözleşmesi NDA")
    elems = []
    h1 = _style("h1", fontSize=15, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=6)
    h2 = _style("h2", fontSize=11, fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=4)
    normal = _style("norm", fontSize=10, spaceAfter=4, leading=13)

    elems.append(Paragraph("GİZLİLİK VE TARAFLIK SÖZLEŞMESİ (NDA)", h1))
    elems.append(Paragraph("Sözleşme No: GZ-2024-007", normal))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=8))
    elems.append(Paragraph("Birinci Taraf: Gamma İnovasyon A.Ş., VKN: 2233445566", normal))
    elems.append(Paragraph("İkinci Taraf: Delta Ar-Ge Merkezi Ltd. Şti.", normal))
    elems.append(Paragraph("Sözleşme Başlangıç tarihi: 01.03.2024", normal))
    elems.append(Paragraph("Sözleşme süresi: 24 aylık", normal))

    elems.append(Paragraph("MADDE 1 — GİZLİLİK", h2))
    elems.append(Paragraph(
        "Gizlilik yükümlülüğü: Taraflar, iş bu sözleşme kapsamında öğrendikleri her türlü "
        "ticari, teknik ve finansal gizli bilgiyi, sözleşme süresince ve bitiş tarihinden "
        "itibaren 5 yıl boyunca üçüncü kişilere ifşa etmeyeceklerdir.", normal
    ))

    elems.append(Paragraph("MADDE 2 — İHLAL VE CEZA", h2))
    elems.append(Paragraph(
        "Ceza klozu: Gizlilik ihlaline sebebiyet veren taraf, diğer tarafa 500.000 TL "
        "tazminat ödemeyi kabul eder. Tazminat hakkı saklı kalmak kaydıyla fesih hakkı "
        "da kullanılabilir.", normal
    ))

    elems.append(Paragraph("MADDE 3 — FESİH", h2))
    elems.append(Paragraph(
        "Fesih şartları: Taraflardan biri sözleşmeyi 60 gün önceden yazılı ihbar ile feshedebilir.", normal
    ))
    elems.append(Paragraph(
        "Sözleşme feshedilebilir; ancak gizlilik yükümlülükleri fesih sonrasında da devam eder.", normal
    ))
    elems.append(Paragraph("İmzalayan: Zeynep Kaya | İmza Tarihi: 29.02.2024", normal))
    doc.build(elems)
    print(f"  ✅ {out_path}")


# ===========================================================================
# TECHNICAL DOC 1 — API documentation
# ===========================================================================

def create_technical_1(out_path: Path) -> None:
    doc = _doc(out_path, "API Teknik Dokümanı")
    elems = []
    h1 = _style("h1", fontSize=18, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=4)
    h2 = _style("h2", fontSize=13, fontName="Helvetica-Bold", textColor=NAVY, spaceBefore=10, spaceAfter=4)
    h3 = _style("h3", fontSize=11, fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=3)
    normal = _style("norm", fontSize=10, spaceAfter=4, leading=14)

    elems.append(Paragraph("Belge Zekası API — Teknik Doküman", h1))
    elems.append(Paragraph("Versiyon: v2.1.0", normal))
    elems.append(Paragraph("Hazırlayan: Can Şahin", normal))
    elems.append(Paragraph("Tarih: 15.08.2024", normal))
    elems.append(Paragraph("Kuruluş: Örnek Teknoloji A.Ş.", normal))
    elems.append(Paragraph("Anahtar Kelimeler: API, REST, belge işleme, PDF, Türkçe NLP", normal))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=8))

    elems.append(Paragraph("Özet", h2))
    elems.append(Paragraph(
        "Bu doküman, Belge Zekası API'sinin teknik şartnamesini açıklamaktadır. "
        "API, PDF ve DOCX belgelerini işleyerek yapılandırılmış veri çıkarımı, "
        "belge sınıflandırması ve alan doğrulaması gerçekleştirir.", normal
    ))

    elems.append(Paragraph("1 Sistem Gereksinimleri", h2))
    elems.append(Paragraph("1.1 Donanım Gereksinimleri", h3))
    elems.append(Paragraph("• Minimum 4 GB RAM", normal))
    elems.append(Paragraph("• 2 CPU çekirdek", normal))
    elems.append(Paragraph("• 20 GB disk alanı", normal))

    elems.append(Paragraph("1.2 Yazılım Gereksinimleri", h3))
    elems.append(Paragraph("• Python 3.11+", normal))
    elems.append(Paragraph("• Redis 7.0+", normal))
    elems.append(Paragraph("• Docker 24+", normal))

    elems.append(Paragraph("2 API Endpoint Listesi", h2))
    api_data = [
        ["Method", "Endpoint", "Açıklama"],
        ["POST", "/api/v1/upload", "Belge yükleme"],
        ["GET", "/api/v1/status/{job_id}", "İş durumu sorgulama"],
        ["GET", "/api/v1/result/{job_id}", "Tam sonuç"],
        ["GET", "/api/v1/result/{job_id}/fields", "Sadece alanlar"],
        ["GET", "/health", "Sağlık kontrolü"],
    ]
    at = Table(api_data, colWidths=["15%", "40%", "45%"])
    at.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    elems.append(at)

    elems.append(Paragraph("3 Mimari", h2))
    elems.append(Paragraph(
        "Sistem FastAPI tabanlı REST API, RQ + Redis iş kuyruğu ve Streamlit "
        "kontrol panelinden oluşmaktadır. Mimari detaylar için akış diyagramına bakınız.", normal
    ))

    elems.append(Paragraph("Revizyon Geçmişi", h2))
    rev_data = [
        ["Rev. No", "Tarih", "Açıklama"],
        ["v1.0.0", "01.01.2024", "İlk yayın"],
        ["v2.0.0", "01.06.2024", "RQ worker eklendi"],
        ["v2.1.0", "15.08.2024", "DOCX desteği eklendi"],
    ]
    rt = Table(rev_data, colWidths=["20%", "25%", "55%"])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    elems.append(rt)
    doc.build(elems)
    print(f"  ✅ {out_path}")


# ===========================================================================
# TECHNICAL DOC 2 — Installation guide
# ===========================================================================

def create_technical_2(out_path: Path) -> None:
    doc = _doc(out_path, "Kurulum Kılavuzu")
    elems = []
    h1 = _style("h1", fontSize=16, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=4)
    h2 = _style("h2", fontSize=12, fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=4)
    normal = _style("norm", fontSize=10, spaceAfter=4, leading=13)

    elems.append(Paragraph("Kurulum ve Yapılandırma Kılavuzu", h1))
    elems.append(Paragraph("Doküman Adı: Sistem Kurulum Kılavuzu", normal))
    elems.append(Paragraph("Versiyon: v1.3.2", normal))
    elems.append(Paragraph("Yazar: Ayşe Çelik", normal))
    elems.append(Paragraph("Tarih: 10.09.2024", normal))
    elems.append(Paragraph("Kurulus: DevOps Mühendislik Ekibi", normal))
    elems.append(Paragraph("Anahtar Kelimeler: kurulum, konfigürasyon, docker, deployment", normal))

    elems.append(Paragraph("Özet", h2))
    elems.append(Paragraph(
        "Bu kılavuz, sistemin Docker ortamında kurulumu ve yapılandırılmasını açıklamaktadır. "
        "Tüm bileşenler docker-compose ile tek komutta ayağa kaldırılır.", normal
    ))

    elems.append(Paragraph("1 Ön Koşullar", h2))
    elems.append(Paragraph("• Docker Desktop 24.x veya Docker Engine 24.x yüklü olmalı", normal))
    elems.append(Paragraph("• docker-compose v2.x yüklü olmalı", normal))

    elems.append(Paragraph("2 Kurulum Adımları", h2))
    elems.append(Paragraph("2.1 Depo Klonlama", normal))
    elems.append(Paragraph("git clone https://github.com/example/document-intelligence-pipeline", normal))
    elems.append(Paragraph("2.2 Ortam Değişkenleri", normal))
    elems.append(Paragraph("REDIS_URL=redis://redis:6379/0", normal))
    elems.append(Paragraph("2.3 Başlatma", normal))
    elems.append(Paragraph("docker-compose up --build -d", normal))

    elems.append(Paragraph("Revizyon Geçmişi", h2))
    elems.append(Paragraph("v1.0.0 | 2024-01-01 — İlk yayın", normal))
    elems.append(Paragraph("v1.3.2 | 2024-09-10 — ARM64 desteği eklendi", normal))
    doc.build(elems)
    print(f"  ✅ {out_path}")


# ===========================================================================
# Main
# ===========================================================================

if __name__ == "__main__":
    base = Path(__file__).parent

    print("Generating sample PDFs...")
    create_invoice_1(base / "invoices" / "sample_invoice_1.pdf")
    create_invoice_2(base / "invoices" / "sample_invoice_2.pdf")
    create_invoice_3(base / "invoices" / "sample_invoice_3_incomplete.pdf")
    create_contract_1(base / "contracts" / "sample_contract_1.pdf")
    create_contract_2(base / "contracts" / "sample_contract_2_nda.pdf")
    create_technical_1(base / "technical" / "sample_technical_1_api_doc.pdf")
    create_technical_2(base / "technical" / "sample_technical_2_installation.pdf")
    print("\nAll sample PDFs generated successfully.")
