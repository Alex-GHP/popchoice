from unittest.mock import MagicMock, patch

from app.agent import RecommenderState, recommend, route_after_search


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_state(**overrides) -> RecommenderState:
    """
    Returns a RecommenderState with sensible defaults.
    Pass keyword args to override specific fields.
    This pattern avoids repeating the full dict in every test.
    """
    base: RecommenderState = {
        "mood": [],
        "media_type": None,
        "genres": [],
        "nostalgic_title": None,
        "search_results": [],
        "recommendation": None,
        "asked_nostalgic": False,
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
# recommend node — tests the LLM prompt construction
# ---------------------------------------------------------------------------


def test_recommend_returns_llm_content():
    mock_response = MagicMock()
    mock_response.content = "Watch Hereditary."

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = recommend(make_state())

    assert result["recommendation"] == "Watch Hereditary."


def test_recommend_includes_mood_in_prompt():
    mock_response = MagicMock()
    mock_response.content = "Some recommendation."

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        recommend(make_state(mood=["relaxed", "cozy"]))

    human_content = mock_llm.invoke.call_args[0][0][1].content
    assert "relaxed" in human_content
    assert "cozy" in human_content


def test_recommend_includes_search_results_in_prompt():
    mock_response = MagicMock()
    mock_response.content = "Some recommendation."

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
    mock_response.content = "Some recommendation."

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        recommend(make_state(search_results=[]))

    human_content = mock_llm.invoke.call_args[0][0][1].content
    assert "No strong matches" in human_content


def test_recommend_includes_nostalgic_title_in_prompt():
    mock_response = MagicMock()
    mock_response.content = "Some recommendation."

    with patch("app.agent._llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        recommend(make_state(nostalgic_title="The Matrix"))

    human_content = mock_llm.invoke.call_args[0][0][1].content
    assert "The Matrix" in human_content
