from unittest.mock import MagicMock, patch

from app.agent import (
    RecommenderState,
    check_availability,
    check_streaming_in_romania,
    recommend,
    route_after_search,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_state(**overrides) -> RecommenderState:
    """
    Returns a RecommenderState with sensible defaults.
    Pass keyword args to override specific fields.
    """
    base: RecommenderState = {
        "mood": [],
        "media_type": None,
        "genres": [],
        "nostalgic_title": None,
        "search_results": [],
        "recommendation": None,
        "asked_nostalgic": False,
        "availability_info": None,
    }
    return {**base, **overrides}  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# route_after_search — pure routing logic, no mocking needed
# ---------------------------------------------------------------------------


def test_routes_to_recommend_when_two_or_more_results():
    state = make_state(search_results=[{}, {}])
    assert route_after_search(state) == "recommend"


def test_routes_to_recommend_when_more_than_two_results():
    state = make_state(search_results=[{}, {}, {}])
    assert route_after_search(state) == "recommend"


def test_routes_to_ask_nostalgic_when_one_result_and_not_asked():
    state = make_state(search_results=[{}], asked_nostalgic=False)
    assert route_after_search(state) == "ask_nostalgic"


def test_routes_to_ask_nostalgic_when_zero_results_and_not_asked():
    state = make_state(search_results=[], asked_nostalgic=False)
    assert route_after_search(state) == "ask_nostalgic"


def test_routes_to_recommend_when_already_asked_nostalgic_with_zero_results():
    state = make_state(search_results=[], asked_nostalgic=True)
    assert route_after_search(state) == "recommend"


def test_routes_to_recommend_when_already_asked_nostalgic_with_one_result():
    state = make_state(search_results=[{}], asked_nostalgic=True)
    assert route_after_search(state) == "recommend"


# ---------------------------------------------------------------------------
# check_availability — uses _llm_with_tools to find an available title
# ---------------------------------------------------------------------------


def test_check_availability_returns_tool_results():
    mock_response_with_tool = MagicMock()
    mock_response_with_tool.tool_calls = [
        {
            "name": "check_streaming_in_romania",
            "args": {"title": "Inception"},
            "id": "1",
        }
    ]

    mock_response_done = MagicMock()
    mock_response_done.tool_calls = []

    with (
        patch("app.agent._llm_with_tools") as mock_tools,
        patch("app.agent.check_streaming_in_romania") as mock_tool_fn,
    ):
        mock_tools.invoke.side_effect = [mock_response_with_tool, mock_response_done]
        mock_tool_fn.invoke.return_value = (
            "'Inception' is available on: Netflix in Romania."
        )
        result = check_availability(make_state())

    assert "Inception" in result["availability_info"]
    assert "Netflix" in result["availability_info"]


def test_check_availability_returns_empty_when_no_tool_calls():
    mock_response = MagicMock()
    mock_response.tool_calls = []

    with patch("app.agent._llm_with_tools") as mock_tools:
        mock_tools.invoke.return_value = mock_response
        result = check_availability(make_state())

    assert result["availability_info"] == ""


def test_check_availability_includes_mood_in_prompt():
    mock_response = MagicMock()
    mock_response.tool_calls = []

    with patch("app.agent._llm_with_tools") as mock_tools:
        mock_tools.invoke.return_value = mock_response
        check_availability(make_state(mood=["relaxed", "cozy"]))

    human_content = mock_tools.invoke.call_args[0][0][1].content
    assert "relaxed" in human_content
    assert "cozy" in human_content


# ---------------------------------------------------------------------------
# recommend — generates formatted recommendation (no tools, safe to stream)
# ---------------------------------------------------------------------------


def test_recommend_returns_llm_content():
    mock_response = MagicMock()
    mock_response.content = (
        "## Hereditary\n\nGreat horror.\n\n### Available on: `Netflix`"
    )

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = recommend(make_state(availability_info="available on Netflix"))

    assert result["recommendation"].startswith("## Hereditary")


def test_recommend_strips_preamble_before_heading():
    mock_response = MagicMock()
    mock_response.content = (
        "Here's my pick: ## Breaking Bad\n\nGreat show.\n\n### Available on: `Netflix`"
    )

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = recommend(make_state())

    assert result["recommendation"].startswith("## Breaking Bad")


def test_recommend_includes_availability_in_prompt():
    mock_response = MagicMock()
    mock_response.content = "## Movie\n\nDesc.\n\n### Available on: `Netflix`"

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        recommend(
            make_state(
                availability_info="'Inception' is available on: Netflix in Romania."
            )
        )

    human_content = mock_llm.invoke.call_args[0][0][1].content
    assert "Inception" in human_content
    assert "Netflix" in human_content


def test_recommend_includes_search_results_in_prompt():
    mock_response = MagicMock()
    mock_response.content = "## Movie\n\nDesc.\n\n### Available on: `Netflix`"

    results = [
        {
            "title": "Fleabag",
            "type": "series",
            "user_rating": 8,
            "user_review": "Loved it.",
            "gf_review": "Favourite show.",
        }
    ]

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        recommend(make_state(search_results=results))

    human_content = mock_llm.invoke.call_args[0][0][1].content
    assert "Fleabag" in human_content
    assert "Loved it" in human_content
    assert "Favourite show" in human_content


def test_recommend_uses_no_matches_message_when_results_empty():
    mock_response = MagicMock()
    mock_response.content = "## Movie\n\nDesc.\n\n### Available on: `Netflix`"

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        recommend(make_state(search_results=[]))

    human_content = mock_llm.invoke.call_args[0][0][1].content
    assert "No strong matches" in human_content


def test_recommend_includes_nostalgic_title_in_prompt():
    mock_response = MagicMock()
    mock_response.content = "## Movie\n\nDesc.\n\n### Available on: `Netflix`"

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        recommend(make_state(nostalgic_title="The Matrix"))

    human_content = mock_llm.invoke.call_args[0][0][1].content
    assert "The Matrix" in human_content


# ---------------------------------------------------------------------------
# check_streaming_in_romania — tests the TMDB availability tool
# ---------------------------------------------------------------------------


def test_check_streaming_returns_platforms_when_available():
    with (
        patch("app.agent.search_media") as mock_search,
        patch("app.agent.get_watch_providers") as mock_providers,
    ):
        mock_search.return_value = [
            {"tmdb_id": 1, "type": "movie", "title": "Inception"}
        ]
        mock_providers.return_value = {
            "RO": {"flatrate": [{"provider_name": "Netflix"}]}
        }
        result = check_streaming_in_romania.invoke({"title": "Inception"})

    assert "Inception" in result
    assert "Netflix" in result


def test_check_streaming_reports_not_available():
    with (
        patch("app.agent.search_media") as mock_search,
        patch("app.agent.get_watch_providers") as mock_providers,
    ):
        mock_search.return_value = [
            {"tmdb_id": 1, "type": "movie", "title": "Inception"}
        ]
        mock_providers.return_value = {"RO": {}}
        result = check_streaming_in_romania.invoke({"title": "Inception"})

    assert "NOT" in result


def test_check_streaming_handles_title_not_on_tmdb():
    with patch("app.agent.search_media") as mock_search:
        mock_search.return_value = []
        result = check_streaming_in_romania.invoke({"title": "XYZUnknown"})

    assert "Could not find" in result
