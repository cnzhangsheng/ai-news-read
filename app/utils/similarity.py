# app/utils/similarity.py
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_title_hash(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()


def compute_similarity(title1: str, title2: str) -> float:
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([title1, title2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(similarity[0][0])
    except ValueError:
        return 0.0


def is_similar(title1: str, title2: str, threshold: float = 0.85) -> bool:
    return compute_similarity(title1, title2) > threshold


def check_duplicate_by_title(title: str, existing_titles: list[str], threshold: float = 0.85) -> bool:
    for existing in existing_titles:
        if is_similar(title, existing, threshold):
            return True
    return False