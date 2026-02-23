from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")


def build_embedding_text(entry: dict) -> str:
    genres = ", ".join(entry.get("genres", []))
    parts = [
        f"Title: {entry['title']}",
        f"Type: {entry['type']}",
        f"Genres: {genres}",
    ]

    if entry.get("description"):
        parts.append(f"Description: {entry['description']}")

    if entry.get("user_review"):
        rating = entry.get("user_rating", "?")
        parts.append(f"Mora's review (rating {rating}/10): {entry['user_review']}")

    if entry.get("gf_review"):
        rating = entry.get("gf_rating", "?")
        parts.append(f"GF's review (rating {rating}/10): {entry['gf_review']}")

    return ". ".join(parts)


def embed(text: str) -> list[float]:
    vector = _model.encode(text)
    return vector.tolist()
