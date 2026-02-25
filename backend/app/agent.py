from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from app.database import search_similar
from app.tmdb import get_watch_providers, search_media


@tool
def check_streaming_in_romania(title: str) -> str:
    """Check if a movie or series is currently available for streaming in Romania.
    Returns the platforms it's available on, or states it's not available."""
    results = search_media(title)
    if not results:
        return f"Could not find '{title}' on TMDB."

    top = results[0]
    tmdb_id = top["tmdb_id"]
    media_type = top["type"]

    providers = get_watch_providers(tmdb_id, media_type)
    flatrate = providers.get("RO", {}).get("flatrate", [])

    if not flatrate:
        return f"'{top['title']}' is NOT currently available for streaming in Romania."

    platforms = [p["provider_name"] for p in flatrate]
    return f"'{top['title']}' is available on: {', '.join(platforms)} in Romania."


class RecommenderState(TypedDict):
    mood: list[str]
    media_type: str | None
    genres: list[str]
    nostalgic_title: str | None
    search_results: list[dict]
    recommendation: str | None
    asked_nostalgic: bool
    availability_info: str | None


_llm = ChatAnthropic(model="claude-haiku-4-5-20251001")  # type: ignore[call-arg]
_llm_with_tools = _llm.bind_tools([check_streaming_in_romania])


def ask_mood(state: RecommenderState) -> dict:
    answer = interrupt(
        "What mood are you two in tonight? "
        "(You can give multiple moods separated by commas, e.g. 'relaxed, adventurous')"
    )
    moods = [m.strip() for m in answer.replace(" and ", ",").split(",") if m.strip()]
    return {"mood": moods}


def ask_type(state: RecommenderState) -> dict:
    media_type = interrupt("Are you in the mood for a movie, a series, or both?")
    return {"media_type": media_type}


def ask_genres(state: RecommenderState) -> dict:
    answer = interrupt(
        "Any genre preferences? (e.g. thriller, comedy, drama — or say 'no preference')"
    )
    if "no preference" in answer.lower():
        genres = []
    else:
        genres = [
            g.strip() for g in answer.replace(" and ", ",").split(",") if g.strip()
        ]
    return {"genres": genres}


def search_db(state: RecommenderState) -> dict:
    parts = []
    if state.get("mood"):
        parts.append(f"mood: {', '.join(state['mood'])}")
    if state.get("media_type"):
        parts.append(f"type: {state['media_type']}")
    if state.get("genres"):
        parts.append(f"genres: {', '.join(state['genres'])}")
    if state.get("nostalgic_title"):
        parts.append(f"similar feel to: {state['nostalgic_title']}")

    query = ". ".join(parts)
    results = search_similar(query, limit=5)
    return {"search_results": results}


def ask_nostalgic(state: RecommenderState) -> dict:
    title = interrupt(
        "I'm not finding strong matches yet. "
        "Is there a movie or series you've watched before that really stuck with you?"
    )
    return {"nostalgic_title": title, "asked_nostalgic": True}


def _build_watch_context(state: RecommenderState) -> str:
    results = state.get("search_results", [])
    if not results:
        return "No strong matches found in their watch history."
    lines = []
    for r in results:
        line = (
            f"- {r['title']} ({r['type']}, rated {r.get('user_rating', '?')}/10): "
            f'Mora said "{r.get("user_review", "")}". '
            f'GF said "{r.get("gf_review", "")}".'
        )
        lines.append(line)
    return "\n".join(lines)


def check_availability(state: RecommenderState) -> dict:
    """Use the LLM with tools to find a title that is available for streaming."""
    context = _build_watch_context(state)

    system = SystemMessage(
        content=(
            "You are helping a couple find something to watch tonight. "
            "Use the check_streaming_in_romania tool to verify titles are available. "
            "If a title is NOT available, pick a different one and check again. "
            "Keep trying until you find one that IS available (up to 4 checks)."
        )
    )

    human = HumanMessage(
        content=(
            f"Current mood: {', '.join(state.get('mood', [])) or 'not specified'}\n"
            f"Wants: {state.get('media_type')}\n"
            f"Genres: {', '.join(state.get('genres', [])) or 'no preference'}\n"
            f"Nostalgic reference: {state.get('nostalgic_title') or 'none'}\n\n"
            f"Their watch history matches:\n{context}\n\n"
            "Find a title that matches their preferences and verify "
            "it is available for streaming in Romania."
        )
    )

    messages: list = [system, human]

    while True:
        response = _llm_with_tools.invoke(messages)

        if not response.tool_calls:
            break

        messages.append(response)
        for tool_call in response.tool_calls:
            tool_result = check_streaming_in_romania.invoke(tool_call["args"])
            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                )
            )

    tool_results = [m.content for m in messages if isinstance(m, ToolMessage)]
    return {"availability_info": "\n".join(tool_results) if tool_results else ""}


def recommend(state: RecommenderState) -> dict:
    """Generate the formatted recommendation (no tool calls — safe to stream)."""
    context = _build_watch_context(state)
    availability = state.get("availability_info") or "No availability data."

    system = SystemMessage(
        content=(
            "You are a movie and TV series recommender for a couple. "
            "Based on their mood, preferences, watch history, and the verified "
            "streaming availability below, recommend exactly ONE title.\n\n"
            "Your response must follow this EXACT format — start IMMEDIATELY with '## ':\n\n"
            "## {Title}\n\n"
            "{2-3 sentences explaining why it matches their mood, referencing their past reviews.}\n\n"
            "### Available on: `{Platform}`\n\n"
            "Here is an example of a perfect response:\n\n"
            "## Prison Break\n\n"
            "This high-tension thriller is perfect for your adventurous mood tonight. "
            "Mora loved the suspense in Breaking Bad and your girlfriend enjoyed the fast pacing of Money Heist, "
            "so the constant cliffhangers and clever plotting in Prison Break should hit the same sweet spot for both of you.\n\n"
            "### Available on: `Netflix`"
        )
    )

    human = HumanMessage(
        content=(
            f"Current mood: {', '.join(state.get('mood', [])) or 'not specified'}\n"
            f"Wants: {state.get('media_type')}\n"
            f"Genres: {', '.join(state.get('genres', [])) or 'no preference'}\n"
            f"Nostalgic reference: {state.get('nostalgic_title') or 'none'}\n\n"
            f"Their watch history matches:\n{context}\n\n"
            f"Verified streaming availability:\n{availability}\n\n"
            "Write the recommendation. Start IMMEDIATELY with '## '."
        )
    )

    response = _llm.invoke([system, human])
    final_content = response.content

    if isinstance(final_content, list):
        final_content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in final_content
        )

    marker = final_content.find("## ")
    if marker > 0:
        final_content = final_content[marker:]

    return {"recommendation": final_content}


def route_after_search(state: RecommenderState) -> str:
    enough_results = len(state.get("search_results", [])) >= 2
    already_asked = state.get("asked_nostalgic", False)

    if enough_results or already_asked:
        return "recommend"
    return "ask_nostalgic"


def build_graph():
    graph = StateGraph(RecommenderState)  # type: ignore[arg-type]

    graph.add_node("ask_mood", ask_mood)
    graph.add_node("ask_type", ask_type)
    graph.add_node("ask_genres", ask_genres)
    graph.add_node("search_db", search_db)
    graph.add_node("ask_nostalgic", ask_nostalgic)
    graph.add_node("check_availability", check_availability)
    graph.add_node("recommend", recommend)

    graph.set_entry_point("ask_mood")
    graph.add_edge("ask_mood", "ask_type")
    graph.add_edge("ask_type", "ask_genres")
    graph.add_edge("ask_genres", "search_db")
    graph.add_edge("ask_nostalgic", "search_db")
    graph.add_edge("check_availability", "recommend")
    graph.add_edge("recommend", END)

    graph.add_conditional_edges(
        "search_db",
        route_after_search,
        {
            "recommend": "check_availability",
            "ask_nostalgic": "ask_nostalgic",
        },
    )

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


recommender = build_graph()
