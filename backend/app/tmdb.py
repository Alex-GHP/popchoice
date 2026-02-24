import httpx

from app.config import TMDB_API_KEY

_BASE = "https://api.themoviedb.org/3"

_movie_genres: dict[int, str] = {}
_tv_genres: dict[int, str] = {}


def _load_genres() -> None:
    with httpx.Client() as client:
        movie_resp = client.get(
            f"{_BASE}/genre/movie/list", params={"api_key": TMDB_API_KEY}
        )
        tv_resp = client.get(f"{_BASE}/genre/tv/list", params={"api_key": TMDB_API_KEY})
    movie_resp.raise_for_status()
    tv_resp.raise_for_status()
    for g in movie_resp.json()["genres"]:
        _movie_genres[g["id"]] = g["name"]
    for g in tv_resp.json()["genres"]:
        _tv_genres[g["id"]] = g["name"]


def search_media(query: str) -> list[dict]:
    if not _movie_genres:
        _load_genres()

    with httpx.Client() as client:
        resp = client.get(
            f"{_BASE}/search/multi",
            params={"api_key": TMDB_API_KEY, "query": query, "include_adult": False},
        )
    resp.raise_for_status()

    results = []
    for item in resp.json().get("results", []):
        media_type = item.get("media_type")
        if media_type not in ("movie", "tv"):
            continue
        is_movie = media_type == "movie"
        genre_map = _movie_genres if is_movie else _tv_genres
        genres = [
            genre_map[gid] for gid in item.get("genre_ids", []) if gid in genre_map
        ]
        results.append(
            {
                "tmdb_id": item["id"],
                "title": item.get("title") if is_movie else item.get("name"),
                "type": "movie" if is_movie else "series",
                "year": (item.get("release_date") or item.get("first_air_date") or "")[
                    :4
                ],
                "description": item.get("overview", ""),
                "genres": genres,
            }
        )

    return results[:10]
