from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

    factory = StemmerFactory()
    stemmer = factory.create_stemmer()

    def preprocess(text):
        return stemmer.stem(text.lower())
except:
    def preprocess(text):
        return text.lower()


class FAQMatcher:
    def __init__(self, faq_items, threshold=0.30):
        self.faq_items = faq_items
        self.threshold = threshold

        # Gabungkan question + keywords agar TF-IDF lebih akurat
        self.documents = []

        for faq in faq_items:
            keywords = " ".join(faq.get("keywords", []))

            document = (
                faq.get("question", "")
                + " "
                + keywords
            )

            self.documents.append(preprocess(document))

        self.vectorizer = TfidfVectorizer()
        self.faq_matrix = self.vectorizer.fit_transform(self.documents)

    def search(self, query):
        query_clean = preprocess(query)

        # ==================================================
        # PRIORITAS 1 : KEYWORD MATCHING
        # ==================================================

        keyword_scores = []

        for faq in self.faq_items:
            score = 0

            keywords = faq.get("keywords", [])

            for keyword in keywords:
                keyword_clean = preprocess(keyword)

                # exact phrase
                if keyword_clean in query_clean:
                    score += 3

                # per kata
                for word in keyword_clean.split():
                    if word in query_clean.split():
                        score += 1

            keyword_scores.append(score)

        max_keyword_score = max(keyword_scores)

        if max_keyword_score > 0:
            best_idx = keyword_scores.index(max_keyword_score)
            faq = self.faq_items[best_idx]

            return {
                "id": faq["id"],
                "answer": faq["answer"],
                "points": faq.get("points", 5),
                "score": float(max_keyword_score),
                "match_type": "keyword"
            }

        # ==================================================
        # PRIORITAS 2 : TF-IDF
        # ==================================================

        query_vector = self.vectorizer.transform([query_clean])

        similarities = cosine_similarity(
            query_vector,
            self.faq_matrix
        ).flatten()

        best_idx = similarities.argmax()
        best_score = similarities[best_idx]

        if best_score >= self.threshold:
            faq = self.faq_items[best_idx]

            return {
                "id": faq["id"],
                "answer": faq["answer"],
                "points": faq.get("points", 5),
                "score": float(best_score),
                "match_type": "tfidf"
            }

        # ==================================================
        # TIDAK ADA YANG COCOK
        # ==================================================

        return {
            "id": None,
            "answer": (
                "Maaf, saya belum menemukan jawaban yang sesuai. "
                "Silakan coba gunakan kata lain atau lihat contoh pertanyaan yang tersedia."
            ),
            "points": 0,
            "score": 0.0,
            "match_type": "fallback"
        }