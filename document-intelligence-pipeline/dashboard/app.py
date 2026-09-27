"""
Streamlit dashboard for the Document Intelligence Pipeline.
3 tabs: Upload & Process | Results & Evidence | Evaluation Report
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402
from dashboard.theme import get_css  # noqa: E402

# Page config
st.set_page_config(
    page_title="Document Intelligence Platform",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(get_css(), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Lazy imports (only needed at runtime)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_pipeline():
    from src.pipeline.coordinator import DocumentPipeline
    return DocumentPipeline()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown("""
<div class="terminal-header">
  <div>
    <span class="terminal-title">📄 Document Intelligence Platform</span>
    <span class="terminal-badge">v1.0</span>
  </div>
  <div class="terminal-meta">
    <span class="meta-chip">🇹🇷 Turkish NLP</span>
    <span class="meta-chip">PDF · DOCX</span>
    <span class="meta-chip">Fatura · Sözleşme · Teknik Doküman</span>
    <span class="meta-chip">Regex Extraction Engine</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_upload, tab_results, tab_eval = st.tabs([
    "📤 Upload & Process",
    "📊 Results & Evidence",
    "🎯 Evaluation Report",
])

# ===========================================================================
# TAB 1 — Upload & Process
# ===========================================================================

with tab_upload:
    st.markdown("### Belge Yükle")

    col_up, col_info = st.columns([2, 1])

    with col_up:
        uploaded = st.file_uploader(
            "PDF veya DOCX yükleyin",
            type=["pdf", "docx"],
            help="Türkçe fatura, sözleşme veya teknik doküman",
        )

    with col_info:
        st.markdown("""
<div class="info-card">
  <h4>Desteklenen Belge Türleri</h4>
  <div class="field-row"><span class="field-key">Fatura</span><span class="field-val">14 alan</span></div>
  <div class="field-row"><span class="field-key">Sözleşme</span><span class="field-val">12 alan</span></div>
  <div class="field-row"><span class="field-key">Teknik Dok.</span><span class="field-val">10 alan</span></div>
</div>
""", unsafe_allow_html=True)

    if uploaded:
        st.markdown("---")
        with st.spinner("🔄 Pipeline çalışıyor: extract → classify → parse → validate..."):
            pipeline = get_pipeline()
            data = uploaded.read()
            result = pipeline.run_bytes(data, uploaded.name)
            st.session_state["result"] = result

        # KPI row
        doc_type = result.classification.document_type.value
        confidence = result.classification.confidence
        n_fields = sum(1 for v in result.fields.values() if v not in ("", [], {}, None))
        n_evidence = len(result.evidence)
        is_valid = result.validation.is_valid
        n_issues = len(result.validation.issues)

        type_labels = {"invoice": "Fatura 🧾", "contract": "Sözleşme 📝", "technical": "Teknik 🔧", "unknown": "Bilinmiyor ❓"}
        type_colors = {"invoice": "accent", "contract": "success", "technical": "warning", "unknown": "danger"}
        col_color = type_colors.get(doc_type, "accent")

        st.markdown(f"""
<div class="metric-row">
  <div class="metric-card {col_color}">
    <div class="metric-label">Belge Türü</div>
    <div class="metric-value">{type_labels.get(doc_type, doc_type)}</div>
    <div class="metric-sub">Güven: {confidence:.0%}</div>
  </div>
  <div class="metric-card accent">
    <div class="metric-label">Çıkarılan Alan</div>
    <div class="metric-value">{n_fields}</div>
    <div class="metric-sub">Dolu alan sayısı</div>
  </div>
  <div class="metric-card accent">
    <div class="metric-label">Atıf Kaydı</div>
    <div class="metric-value">{n_evidence}</div>
    <div class="metric-sub">Kaynak sayfa + snippet</div>
  </div>
  <div class="metric-card {'success' if is_valid else 'danger'}">
    <div class="metric-label">Doğrulama</div>
    <div class="metric-value">{'✅ Geçti' if is_valid else '⚠️ Sorun Var'}</div>
    <div class="metric-sub">{n_issues} sorun tespit edildi</div>
  </div>
  <div class="metric-card accent">
    <div class="metric-label">Sayfa Sayısı</div>
    <div class="metric-value">{result.extraction.total_pages}</div>
    <div class="metric-sub">{uploaded.name[:25]}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.success(f"✅ **{uploaded.name}** başarıyla işlendi. 'Results & Evidence' sekmesine geçin.")

        # Raw JSON expander
        with st.expander("📋 Ham JSON Çıktısı", expanded=False):
            st.code(result.model_dump_json(indent=2), language="json")

# ===========================================================================
# TAB 2 — Results & Evidence
# ===========================================================================

with tab_results:
    result = st.session_state.get("result")

    if result is None:
        st.info("ℹ️ Önce 'Upload & Process' sekmesinden bir belge yükleyin.")
    else:
        doc_type = result.classification.document_type.value
        fields = result.fields
        evidence = result.evidence
        validation = result.validation

        col_left, col_right = st.columns([1, 1])

        with col_left:
            # --- Extracted Fields ---
            st.markdown("#### 📋 Çıkarılan Alanlar")
            field_html = ['<div class="info-card"><h4>Yapılandırılmış Çıktı</h4>']
            for key, val in fields.items():
                if val in ("", [], {}, None):
                    field_html.append(
                        f'<div class="field-row">'
                        f'<span class="field-key">{key}</span>'
                        f'<span class="field-missing">— bulunamadı</span></div>'
                    )
                elif isinstance(val, list):
                    display = f"[{len(val)} öğe]"
                    if val and isinstance(val[0], dict):
                        display = f"[{len(val)} satır]"
                    field_html.append(
                        f'<div class="field-row">'
                        f'<span class="field-key">{key}</span>'
                        f'<span class="field-val">{display}</span></div>'
                    )
                else:
                    val_str = str(val)[:80]
                    field_html.append(
                        f'<div class="field-row">'
                        f'<span class="field-key">{key}</span>'
                        f'<span class="field-val">{val_str}</span></div>'
                    )
            field_html.append("</div>")
            st.markdown("".join(field_html), unsafe_allow_html=True)

            # Line items table (invoice)
            if doc_type == "invoice" and fields.get("kalemler"):
                st.markdown("#### 📦 Kalem Listesi")
                import pandas as pd
                items = fields["kalemler"]
                if items and isinstance(items[0], dict):
                    df = pd.DataFrame(items)
                    st.dataframe(df, use_container_width=True, hide_index=True)

        with col_right:
            # --- Validation ---
            st.markdown("#### ✅ Doğrulama Sonuçları")
            if not validation.issues:
                st.markdown('<div class="issue-ok">✅ Tüm zorunlu alanlar mevcut, format geçerli.</div>', unsafe_allow_html=True)
            else:
                for issue in validation.issues:
                    icon = "❌" if issue.severity == "error" else "⚠️"
                    cls = "issue-error" if issue.severity == "error" else "issue-warning"
                    st.markdown(
                        f'<div class="{cls}">{icon} [{issue.issue_type.upper()}] <b>{issue.field}</b>: {issue.message}</div>',
                        unsafe_allow_html=True,
                    )

            # --- Evidence / Citations ---
            st.markdown("#### 🔍 Kaynak Atıflar")
            if not evidence:
                st.info("Atıf kaydı bulunamadı.")
            else:
                for ev in evidence[:15]:
                    confidence_bar = "█" * int(ev.confidence * 10)
                    st.markdown(f"""
<div class="evidence-item">
  <div class="evidence-field">📌 {ev.field}</div>
  <div style="color:var(--text-primary);font-weight:600;margin:3px 0;">{str(ev.value)[:80]}</div>
  <div class="evidence-snippet">{ev.snippet[:150]}</div>
  <div class="evidence-meta">Sayfa {ev.page} &nbsp;|&nbsp; Güven: {ev.confidence:.0%} {confidence_bar}</div>
</div>
""", unsafe_allow_html=True)

        # --- Raw text expander ---
        with st.expander("📄 Ham Belge Metni", expanded=False):
            for page in result.extraction.pages:
                st.markdown(f"**--- Sayfa {page.page_number} ---**")
                st.text(page.text[:3000])

# ===========================================================================
# TAB 3 — Evaluation Report
# ===========================================================================

with tab_eval:
    st.markdown("### 🎯 Extraction Accuracy Raporu")
    st.markdown("""
Bu rapor, 7 kontrollü örnek belge üzerinde pipeline'ın çıkarım doğruluğunu ölçer.
Ground truth `tests/evaluation/ground_truth.json` dosyasında manuel olarak etiketlenmiştir.
""")

    if st.button("▶ Evaluation'ı Çalıştır", type="primary"):
        with st.spinner("Tüm sample belgeler işleniyor..."):
            import subprocess
            r = subprocess.run(
                [sys.executable, "tests/evaluation/run_evaluation.py"],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            output = r.stdout + r.stderr

        st.markdown("#### Sonuçlar")
        st.code(output, language="text")

        if r.returncode == 0:
            st.success("✅ Evaluation tamamlandı — F1 ≥ 0.70 eşiği aşıldı.")
        else:
            st.error("⚠️ Evaluation tamamlandı ancak F1 eşiğinin altında.")

    with st.expander("📋 Ground Truth İçeriği", expanded=False):
        gt_path = ROOT / "tests" / "evaluation" / "ground_truth.json"
        if gt_path.exists():
            st.json(json.loads(gt_path.read_text()))

    # Pipeline architecture diagram
    st.markdown("---")
    st.markdown("#### 🔧 Pipeline Mimarisi")
    st.markdown("""
```
PDF/DOCX
   │
   ▼
PDFExtractor / DocxExtractor
   │  (metin, tablo, bbox)
   ▼
DocumentClassifier
   │  (invoice | contract | technical)
   ▼
InvoiceParser / ContractParser / TechnicalDocParser
   │  (yapılandırılmış JSON alanları)
   ▼
CitationBuilder
   │  (her alana sayfa + snippet + bbox)
   ▼
FieldValidator
   │  (eksik / çelişkili / format hatası)
   ▼
PipelineResult → FastAPI → Streamlit
```
""")
