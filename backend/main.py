import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command
from pydantic import BaseModel

from app.agent import recommender
from app.database import add_media


INITIAL_STATE = {
    "mood": None,
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


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/recommend/reply", response_model=ReplyResponse)
def recommend_reply(body: ReplyRequest) -> ReplyResponse:
    config = {"configurable": {"thread_id": body.thread_id}}
    result = recommender.invoke(Command(resume=body.answer), config)

    if "__interrupt__" in result:
        return ReplyResponse(done=False, question=result["__interrupt__"][0].value)

    return ReplyResponse(done=True, recommendation=result["recommendation"])
