from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from app.database import search_similar


class RecommenderState(TypedDict):
    mood: list[str]
    media_type: str | None
    genres: list[str]
    nostalgic_title: str | None
    search_results: list[dict]
    recommendation: str | None
    asked_nostalgic: bool


_llm = ChatAnthropic(model="claude-haiku-4-5-20251001")  # type: ignore[call-arg]
_search_tool = TavilySearch(max_results=3)
_llm_with_tools = _llm.bind_tools([_search_tool])


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


def recommend(state: RecommenderState) -> dict:
    results = state.get("search_results", [])

    if results:
        context_lines = []
        for r in results:
            line = (
                f"- {r['title']} ({r['type']}, rated {r.get('user_rating', '?')}/10): "
                f'Mora said "{r.get("user_review", "")}". '
                f'GF said "{r.get("gf_review", "")}".'
            )
            context_lines.append(line)
        context = "\n".join(context_lines)
    else:
        context = "No strong matches found in their watch history."

    system = SystemMessage(
        content=(
            "You are a movie and TV series recommender for a couple. "
            "Based on their current mood, preferences, and what they've genuinely enjoyed before, "
            "recommend exactly ONE specific title they haven't seen yet. "
            "Use the web_search tool (at most 2 searches total) to verify the title is available "
            "to watch in Romania (Netflix Romania, HBO Max Romania, Disney+ Romania, Amazon Prime Romania, or similar). "
            "If it is NOT available, search for one alternative. "
            "Do not narrate your search process — go straight to the formatted recommendation. "
            "Your entire response must follow this exact structure and nothing else: "
            "A h2 markdown header for the title (e.g. ## Prison Break). "
            "A new paragraph with 2-3 sentences explaining why it matches their mood, "
            "referencing specific things from their past reviews. "
            "A line with the available platform: ### Available platform: `Netflix`. "
            "No intro, no outro, no bullet points, no reasoning — only the formatted output above."
        )
    )

    human = HumanMessage(
        content=(
            f"Current mood: {', '.join(state.get('mood', [])) or 'not specified'}\n"
            f"Wants: {state.get('media_type')}\n"
            f"Genres: {', '.join(state.get('genres', [])) or 'no preference'}\n"
            f"Nostalgic reference: {state.get('nostalgic_title') or 'none'}\n\n"
            f"Their watch history matches:\n{context}\n\n"
            "Give your recommendation. Remember to search for availability in Romania first."
        )
    )

    messages = [system, human]

    while True:
        response = _llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            tool_result = _search_tool.invoke(tool_call["args"])
            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                )
            )

    final_content = response.content

    if isinstance(final_content, list):
        final_content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in final_content
        )

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
    graph.add_node("recommend", recommend)

    graph.set_entry_point("ask_mood")
    graph.add_edge("ask_mood", "ask_type")
    graph.add_edge("ask_type", "ask_genres")
    graph.add_edge("ask_genres", "search_db")
    graph.add_edge("ask_nostalgic", "search_db")
    graph.add_edge("recommend", END)

    graph.add_conditional_edges(
        "search_db",
        route_after_search,
        {
            "recommend": "recommend",
            "ask_nostalgic": "ask_nostalgic",
        },
    )

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


recommender = build_graph()
