"""Document type classifier using weighted keyword scoring."""
from __future__ import annotations

import re
from src.models.schemas import ClassificationResult, DocumentType

# ---------------------------------------------------------------------------
# Keyword lexicons with weights (higher = stronger signal)
# ---------------------------------------------------------------------------

_LEXICONS: dict[DocumentType, dict[str, float]] = {
    DocumentType.INVOICE: {
        "fatura": 3.0,
        "fatura no": 3.5,
        "fatura numarası": 3.5,
        "invoice": 2.5,
        "kdv": 2.5,
        "kdv oranı": 3.0,
        "toplam tutar": 2.5,
        "ara toplam": 2.0,
        "iban": 2.0,
        "vade": 1.5,
        "vade tarihi": 2.0,
        "satıcı": 1.5,
        "alıcı": 1.5,
        "vergi kimlik": 2.0,
        "vkn": 2.0,
        "e-fatura": 3.0,
        "e-arşiv": 3.0,
        "mal/hizmet adı": 2.0,
        "miktar": 1.0,
        "birim fiyat": 1.5,
        "tutar": 1.0,
        "ödeme": 1.0,
        "tl": 0.5,
        "try": 0.5,
    },
    DocumentType.CONTRACT: {
        "sözleşme": 3.5,
        "contract": 2.5,
        "taraflar": 2.0,
        "işveren": 2.0,
        "yüklenici": 2.0,
        "fesih": 3.0,
        "fesih şartları": 3.5,
        "gizlilik": 2.0,
        "madde": 1.5,
        "bent": 1.5,
        "imza": 1.5,
        "imzalayan": 2.0,
        "ödeme koşulları": 2.0,
        "ceza klozu": 3.0,
        "tazminat": 2.0,
        "yükümlülük": 2.0,
        "hak ve yükümlülükler": 2.5,
        "sözleşme süresi": 3.0,
        "başlangıç tarihi": 1.5,
        "bitiş tarihi": 1.5,
        "iş bu sözleşme": 3.5,
        "akdedilmiştir": 3.5,
    },
    DocumentType.TECHNICAL: {
        "teknik": 2.0,
        "teknik doküman": 3.0,
        "teknik şartname": 3.5,
        "kullanım kılavuzu": 3.5,
        "kullanıcı kılavuzu": 3.5,
        "versiyon": 2.0,
        "version": 2.0,
        "revizyon": 2.0,
        "revision history": 2.5,
        "revizyon geçmişi": 2.5,
        "kurulum": 2.0,
        "yapılandırma": 2.0,
        "konfigürasyon": 2.0,
        "api": 1.5,
        "endpoint": 1.5,
        "şema": 1.5,
        "mimari": 2.0,
        "sistem gereksinimleri": 3.0,
        "gereksinimler": 1.5,
        "akış diyagramı": 2.5,
        "bölüm": 1.0,
        "özet": 1.0,
        "giriş": 0.5,
        "sonuç": 0.5,
    },
}

_UNCERTAIN_THRESHOLD = 0.60   # below this → mark as uncertain
_MIN_SCORE_TO_CLASSIFY = 0.5  # minimum raw score to not return UNKNOWN


class DocumentClassifier:
    """Classifies a document as invoice / contract / technical doc."""

    def classify(self, text: str) -> ClassificationResult:
        text_lower = text.lower()
        raw_scores: dict[DocumentType, float] = {}

        for doc_type, lexicon in _LEXICONS.items():
            score = 0.0
            for keyword, weight in lexicon.items():
                # Count occurrences (capped at 5 to avoid gaming)
                count = min(len(re.findall(re.escape(keyword), text_lower)), 5)
                score += count * weight
            raw_scores[doc_type] = score

        total = sum(raw_scores.values())
        if total < _MIN_SCORE_TO_CLASSIFY:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                scores={k.value: v for k, v in raw_scores.items()},
                uncertain=True,
            )

        normalized: dict[DocumentType, float] = {
            k: v / total for k, v in raw_scores.items()
        }
        best_type = max(normalized, key=lambda k: normalized[k])
        confidence = normalized[best_type]

        return ClassificationResult(
            document_type=best_type,
            confidence=round(confidence, 4),
            scores={k.value: round(v, 4) for k, v in normalized.items()},
            uncertain=confidence < _UNCERTAIN_THRESHOLD,
        )
