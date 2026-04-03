import re
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory # Tambahan untuk Stemming

class FAQMatcher:
    def __init__(self, faq_items: List[Dict], threshold: float = 0.30):
        self.faq_items = faq_items
        self.threshold = threshold
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            use_idf=True,
            smooth_idf=True,
            norm="l2",
            min_df=1,
        )
        
        # Inisialisasi Sastrawi Stemmer
        factory = StemmerFactory()
        self.stemmer = factory.create_stemmer()
        
        # Kamus Sinonim & Typo (Bisa ditambah sesuai kebutuhan)
        self.synonyms = {
            "gimana": "bagaimana",
            "bikin": "buat",
            "plmt": "pltmh",
            "pltm": "pltmh",
            "mikrohidro": "mikro hidro",
            "aturan": "syarat",
            "tempat": "lokasi",
            "buka": "jam",
        }

        self.documents = [self._build_doc(item) for item in self.faq_items]
        self.X = self.vectorizer.fit_transform(self.documents)

    def _clean_text(self, text: str) -> str:
        # 1. Lowercase dan bersihkan spasi
        text = text.lower().strip()
        
        # 2. Hapus tanda baca
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        
        # 3. Ganti kata menggunakan kamus sinonim/typo
        words = text.split()
        replaced_words = [self.synonyms.get(w, w) for w in words]
        text = " ".join(replaced_words)
        
        # 4. Terapkan stemming (menghapus imbuhan, misal: 'wisatawan' -> 'wisata')
        text = self.stemmer.stem(text)
        
        return text

    def _build_doc(self, item: Dict) -> str:
        question = item.get("question", "")
        keywords = " ".join(item.get("keywords", []))
        category = item.get("category", "")
        return self._clean_text(f"{question} {keywords} {category}")

    def _keyword_fallback(self, query: str) -> Dict:
        q = self._clean_text(query)
        best_item = None
        best_hits = 0
        for item in self.faq_items:
            # Perlu diperhatikan: keyword dari FAQ juga sebaiknya bersih dari imbuhan
            hits = sum(1 for kw in item.get("keywords", []) if self._clean_text(kw) in q)
            if hits > best_hits:
                best_hits = hits
                best_item = item
                
        if best_item and best_hits > 0:
            return {
                "id": best_item["id"],
                "answer": best_item["answer"],
                "score": float(best_hits),
                "points": best_item.get("points", 5),
                "match_type": "keyword",
            }
            
        return {
            "id": None,
            "answer": "Maaf, saya tidak dapat menemukan jawaban yang sesuai. Silakan coba kata kunci lain seperti jam buka, fasilitas, PLTMH, turbin, generator, atau kuis.",
            "score": 0.0,
            "points": 0,
            "match_type": "fallback",
        }

    def search(self, query: str) -> Dict:
        q = self._clean_text(query)
        if not q:
            return {
                "id": None,
                "answer": "Silakan ketik pertanyaan terlebih dahulu.",
                "score": 0.0,
                "points": 0,
                "match_type": "empty",
            }

        q_vec = self.vectorizer.transform([q])
        sims = cosine_similarity(q_vec, self.X)[0]
        best_idx = int(sims.argmax())
        best_score = float(sims[best_idx])

        if best_score >= self.threshold:
            item = self.faq_items[best_idx]
            return {
                "id": item["id"],
                "answer": item["answer"],
                "score": round(best_score, 4),
                "points": item.get("points", 5),
                "match_type": "similarity",
            }

        return self._keyword_fallback(query) 