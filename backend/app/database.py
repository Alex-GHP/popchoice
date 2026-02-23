from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY
from app.embeddings import build_embedding_text, embed

_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def add_media(entry: dict) -> dict:
    text = build_embedding_text(entry)
    vector = embed(text)

    row = {**entry, "embedding": vector}

    result = _client.table("watched_media").insert(row).execute()
    return result.data[0]


def search_similar(query: str, limit: int = 5) -> list[dict]:
    query_vector = embed(query)

    result = _client.rpc(
        "search_similar_media",
        {
            "query_embedding": query_vector,
            "match_threshold": 0.2,
            "match_count": limit,
        },
    ).execute()

    return result.data
