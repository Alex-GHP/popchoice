from unittest.mock import MagicMock, patch

import pytest

import app.tmdb as tmdb_module
from app.tmdb import search_media

MOVIE_GENRES_RESP = {
    "genres": [{"id": 35, "name": "Comedy"}, {"id": 28, "name": "Action"}]
}
TV_GENRES_RESP = {
    "genres": [{"id": 35, "name": "Comedy"}, {"id": 10767, "name": "Talk"}]
}

SEARCH_RESP = {
    "results": [
        {
            "id": 8191,
            "media_type": "movie",
            "title": "White Chicks",
            "release_date": "2004-06-23",
            "overview": "Two FBI agents go undercover as white women.",
            "genre_ids": [35, 28],
        },
        {
            "id": 1001,
            "media_type": "tv",
            "name": "Friends",
            "first_air_date": "1994-09-22",
            "overview": "Six friends living in New York.",
            "genre_ids": [35],
        },
        # Person results should be filtered out.
        {
            "id": 999,
            "media_type": "person",
            "name": "Some Actor",
        },
    ]
}


def _make_http_response(data: dict) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = data
    mock.raise_for_status.return_value = None
    return mock


@pytest.fixture(autouse=True)
def reset_genre_cache():
    """Clear the in-memory genre caches before every test."""
    tmdb_module._movie_genres.clear()
    tmdb_module._tv_genres.clear()
    yield


def _patch_client(*responses):
    """Return a context-manager patch where httpx.Client().get() yields responses in order."""
    mock_client = MagicMock()
    mock_client.get.side_effect = list(responses)
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=mock_client)
    ctx.__exit__ = MagicMock(return_value=False)
    return patch("app.tmdb.httpx.Client", return_value=ctx)


class TestSearchMedia:
    def test_returns_movies_and_series(self):
        with _patch_client(
            _make_http_response(MOVIE_GENRES_RESP),
            _make_http_response(TV_GENRES_RESP),
            _make_http_response(SEARCH_RESP),
        ):
            results = search_media("white chicks")

        types = {r["type"] for r in results}
        assert types == {"movie", "series"}

    def test_filters_out_person_results(self):
        with _patch_client(
            _make_http_response(MOVIE_GENRES_RESP),
            _make_http_response(TV_GENRES_RESP),
            _make_http_response(SEARCH_RESP),
        ):
            results = search_media("white chicks")

        assert all(r["type"] in ("movie", "series") for r in results)
        assert len(results) == 2

    def test_maps_genre_ids_to_names(self):
        with _patch_client(
            _make_http_response(MOVIE_GENRES_RESP),
            _make_http_response(TV_GENRES_RESP),
            _make_http_response(SEARCH_RESP),
        ):
            results = search_media("white chicks")

        movie = next(r for r in results if r["type"] == "movie")
        assert movie["genres"] == ["Comedy", "Action"]

    def test_extracts_year_from_release_date(self):
        with _patch_client(
            _make_http_response(MOVIE_GENRES_RESP),
            _make_http_response(TV_GENRES_RESP),
            _make_http_response(SEARCH_RESP),
        ):
            results = search_media("white chicks")

        movie = next(r for r in results if r["type"] == "movie")
        assert movie["year"] == "2004"

        series = next(r for r in results if r["type"] == "series")
        assert series["year"] == "1994"

    def test_uses_first_air_date_for_tv(self):
        resp = {
            "results": [
                {
                    "id": 1,
                    "media_type": "tv",
                    "name": "Show",
                    "first_air_date": "2010-01-01",
                    "overview": "A show.",
                    "genre_ids": [],
                }
            ]
        }
        with _patch_client(
            _make_http_response(MOVIE_GENRES_RESP),
            _make_http_response(TV_GENRES_RESP),
            _make_http_response(resp),
        ):
            results = search_media("show")

        assert results[0]["year"] == "2010"

    def test_skips_genre_ids_not_in_map(self):
        resp = {
            "results": [
                {
                    "id": 1,
                    "media_type": "movie",
                    "title": "Obscure Film",
                    "release_date": "2020-01-01",
                    "overview": "desc",
                    "genre_ids": [99999],  # unknown id
                }
            ]
        }
        with _patch_client(
            _make_http_response(MOVIE_GENRES_RESP),
            _make_http_response(TV_GENRES_RESP),
            _make_http_response(resp),
        ):
            results = search_media("obscure")

        assert results[0]["genres"] == []

    def test_does_not_reload_genres_when_already_cached(self):
        # Pre-populate the caches so _load_genres should NOT be called.
        tmdb_module._movie_genres[35] = "Comedy"
        tmdb_module._tv_genres[35] = "Comedy"

        with _patch_client(_make_http_response(SEARCH_RESP)) as MockClient:
            search_media("friends")
            # Only one Client() call (for the search), not three (genre loads + search).
            assert MockClient.call_count == 1

    def test_limits_results_to_ten(self):
        many_results = {
            "results": [
                {
                    "id": i,
                    "media_type": "movie",
                    "title": f"Movie {i}",
                    "release_date": "2020-01-01",
                    "overview": "desc",
                    "genre_ids": [],
                }
                for i in range(15)
            ]
        }
        with _patch_client(
            _make_http_response(MOVIE_GENRES_RESP),
            _make_http_response(TV_GENRES_RESP),
            _make_http_response(many_results),
        ):
            results = search_media("movie")

        assert len(results) == 10

    def test_returns_empty_list_when_no_results(self):
        with _patch_client(
            _make_http_response(MOVIE_GENRES_RESP),
            _make_http_response(TV_GENRES_RESP),
            _make_http_response({"results": []}),
        ):
            results = search_media("xyzzy")

        assert results == []
