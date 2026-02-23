from unittest.mock import patch

import pytest

from app.database import add_media, search_similar


# ---------------------------------------------------------------------------
# Fixtures
# pytest fixtures are reusable setup blocks. Any test that declares a fixture
# as a parameter receives it automatically — no need to call it manually.
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client():
    """Replaces the real Supabase client with a mock for the duration of a test."""
    with patch("app.database._client") as m:
        yield m


@pytest.fixture
def mock_embed():
    """Replaces embed() with a fixed 384-float vector so tests don't load the model."""
    with patch("app.database.embed", return_value=[0.1] * 384) as m:
        yield m


@pytest.fixture
def mock_build_text():
    """Replaces build_embedding_text() with a fixed string."""
    with patch(
        "app.database.build_embedding_text", return_value="mocked rich text"
    ) as m:
        yield m


# ---------------------------------------------------------------------------
# add_media
# ---------------------------------------------------------------------------


def test_add_media_calls_build_text_with_entry(
    mock_client, mock_embed, mock_build_text
):
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "1", "title": "Severance"}
    ]
    entry = {"title": "Severance", "type": "series", "genres": ["thriller"]}

    add_media(entry)

    mock_build_text.assert_called_once_with(entry)


def test_add_media_embeds_the_built_text(mock_client, mock_embed, mock_build_text):
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "1", "title": "Severance"}
    ]

    add_media({"title": "Severance", "type": "series", "genres": []})

    mock_embed.assert_called_once_with("mocked rich text")


def test_add_media_inserts_row_with_embedding(mock_client, mock_embed, mock_build_text):
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "1", "title": "Severance"}
    ]
    entry = {"title": "Severance", "type": "series", "genres": ["thriller"]}

    add_media(entry)

    # Inspect exactly what was passed to .insert()
    inserted = mock_client.table.return_value.insert.call_args[0][0]
    assert inserted["title"] == "Severance"
    assert inserted["embedding"] == [0.1] * 384


def test_add_media_returns_the_saved_row(mock_client, mock_embed, mock_build_text):
    saved_row = {"id": "abc-123", "title": "Severance", "type": "series"}
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        saved_row
    ]

    result = add_media({"title": "Severance", "type": "series", "genres": []})

    assert result == saved_row


# ---------------------------------------------------------------------------
# search_similar
# ---------------------------------------------------------------------------


def test_search_similar_embeds_the_query(mock_client, mock_embed):
    mock_client.rpc.return_value.execute.return_value.data = []

    search_similar("dark tense thriller")

    mock_embed.assert_called_once_with("dark tense thriller")


def test_search_similar_calls_rpc_with_correct_function_name(mock_client, mock_embed):
    mock_client.rpc.return_value.execute.return_value.data = []

    search_similar("test query")

    rpc_name = mock_client.rpc.call_args[0][0]
    assert rpc_name == "search_similar_media"


def test_search_similar_passes_vector_threshold_and_limit(mock_client, mock_embed):
    mock_client.rpc.return_value.execute.return_value.data = []

    search_similar("test query", limit=3)

    params = mock_client.rpc.call_args[0][1]
    assert params["query_embedding"] == [0.1] * 384
    assert params["match_threshold"] == 0.2
    assert params["match_count"] == 3


def test_search_similar_returns_rpc_data(mock_client, mock_embed):
    expected = [{"title": "Parasite", "similarity": 0.85}]
    mock_client.rpc.return_value.execute.return_value.data = expected

    results = search_similar("dark social thriller")

    assert results == expected


def test_search_similar_default_limit_is_5(mock_client, mock_embed):
    mock_client.rpc.return_value.execute.return_value.data = []

    search_similar("anything")

    params = mock_client.rpc.call_args[0][1]
    assert params["match_count"] == 5
