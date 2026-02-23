import numpy as np

from app.embeddings import build_embedding_text, embed


# ---------------------------------------------------------------------------
# build_embedding_text — pure function, no mocking needed
# ---------------------------------------------------------------------------


def test_full_entry_contains_all_fields():
    entry = {
        "title": "Test Movie",
        "type": "movie",
        "genres": ["thriller", "drama"],
        "description": "A gripping story.",
        "user_rating": 8,
        "user_review": "Loved the tension.",
        "gf_rating": 7,
        "gf_review": "Pretty good.",
    }
    text = build_embedding_text(entry)
    assert "Test Movie" in text
    assert "movie" in text
    assert "thriller, drama" in text
    assert "A gripping story" in text
    assert "rating 8/10" in text
    assert "Loved the tension" in text
    assert "rating 7/10" in text
    assert "Pretty good" in text


def test_minimal_entry_does_not_crash():
    entry = {"title": "Minimal", "type": "series", "genres": []}
    text = build_embedding_text(entry)
    assert "Minimal" in text
    assert "series" in text


def test_missing_optional_fields_are_omitted():
    entry = {"title": "Untitled", "type": "movie", "genres": ["comedy"]}
    text = build_embedding_text(entry)
    assert "review" not in text.lower()
    assert "rating" not in text.lower()


def test_missing_description_is_omitted():
    entry = {"title": "No Desc", "type": "movie", "genres": ["action"]}
    text = build_embedding_text(entry)
    assert "Description" not in text


def test_only_user_review_included_when_gf_review_missing():
    entry = {
        "title": "Solo Review",
        "type": "movie",
        "genres": [],
        "user_rating": 9,
        "user_review": "Amazing film.",
    }
    text = build_embedding_text(entry)
    assert "Amazing film" in text
    assert "GF" not in text


# ---------------------------------------------------------------------------
# embed — calls the real local model (no network, ~1s on first run)
# ---------------------------------------------------------------------------


def test_embed_returns_list_of_floats():
    vector = embed("test sentence")
    assert isinstance(vector, list)
    assert all(isinstance(v, float) for v in vector)


def test_embed_returns_384_dimensions():
    vector = embed("another test")
    assert len(vector) == 384


def test_different_texts_produce_different_vectors():
    v1 = embed("happy romantic comedy")
    v2 = embed("dark horror thriller")
    assert v1 != v2


def test_similar_texts_are_closer_than_unrelated():
    # Core property of a good embedding model: semantically related sentences
    # should have higher cosine similarity than unrelated ones.
    v_horror_a = np.array(embed("I love scary horror movies"))
    v_horror_b = np.array(embed("terrifying films and thrillers"))
    v_cooking = np.array(embed("delicious pasta recipe with tomatoes"))

    def cosine(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    sim_related = cosine(v_horror_a, v_horror_b)
    sim_unrelated = cosine(v_horror_a, v_cooking)
    assert sim_related > sim_unrelated
