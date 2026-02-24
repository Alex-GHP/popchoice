import json
import os
import uuid

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langgraph.types import Command
from pydantic import BaseModel

from app.agent import recommender
from app.config import API_SECRET
from app.database import add_media
from app.tmdb import search_media as tmdb_search


INITIAL_STATE = {
    "mood": [],
    "media_type": None,
    "genres": [],
    "nostalgic_title": None,
    "search_results": [],
    "recommendation": None,
    "asked_nostalgic": False,
}


class MediaIn(BaseModel):
    title: str
    type: str
    genres: list[str]
    description: str
    user_rating: int
    gf_rating: int
    user_review: str = ""
    gf_review: str = ""


class StartResponse(BaseModel):
    thread_id: str
    question: str


class ReplyRequest(BaseModel):
    thread_id: str
    answer: str


class ReplyResponse(BaseModel):
    done: bool
    question: str | None = None
    recommendation: str | None = None


class SearchResult(BaseModel):
    tmdb_id: int
    title: str
    type: str
    year: str
    description: str
    genres: list[str]


_bearer = HTTPBearer()


def _verify_token(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> None:
    if credentials.credentials != API_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


app = FastAPI(dependencies=[Depends(_verify_token)])

_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/search")
def search(q: str) -> list[SearchResult]:
    return tmdb_search(q)


@app.post("/media")
def save_media(body: MediaIn) -> dict:
    saved = add_media(body.model_dump())
    return saved


@app.post("/recommend/start", response_model=StartResponse)
def recommend_start() -> StartResponse:
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    result = recommender.invoke(INITIAL_STATE, config)
    question = result["__interrupt__"][0].value
    return StartResponse(thread_id=thread_id, question=question)


@app.post("/recommend/reply")
def recommend_reply(body: ReplyRequest) -> StreamingResponse:
    config = {"configurable": {"thread_id": body.thread_id}}

    def event_stream():
        got_chunk = False
        for chunk, metadata in recommender.stream(
            Command(resume=body.answer),
            config,
            stream_mode="messages",
        ):
            node = metadata.get("langgraph_node")
            content = chunk.content

            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                text = ""

            if node == "recommend" and text:
                got_chunk = True
                yield f"data: {json.dumps({'type': 'chunk', 'content': text})}\n\n"

        if not got_chunk:
            state = recommender.get_state(config)
            if state.tasks and state.tasks[0].interrupts:
                question = state.tasks[0].interrupts[0].value
                yield f"data: {json.dumps({'type': 'question', 'question': question})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
