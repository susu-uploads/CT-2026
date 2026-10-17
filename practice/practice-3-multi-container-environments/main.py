"""Заметки в Redis для практики многоконтейнерного развертывания."""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from redis.asyncio import Redis
from redis.exceptions import RedisError


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis.from_url(
        os.environ.get("REDIS_URL", "redis://redis:6379/0"),
        decode_responses=True, socket_connect_timeout=2, socket_timeout=2,
    )
    yield
    await app.state.redis.aclose()


app = FastAPI(title="Заметки", lifespan=lifespan)
KEY = "practice3:notes"
ADD_NOTE = """
if redis.call('LLEN', KEYS[1]) >= 100 then return 0 end
redis.call('RPUSH', KEYS[1], ARGV[1])
return 1
"""


class Note(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=500)

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


@app.exception_handler(RedisError)
async def redis_error(request: Request, error: RedisError):
    return JSONResponse(status_code=503, content={"detail": "Хранилище временно недоступно."})


@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(Path(__file__).with_name("index.html"))


@app.get("/health")
async def health(request: Request):
    await request.app.state.redis.ping()
    return {"status": "ok"}


@app.get("/api/notes")
async def notes(request: Request):
    return {"notes": await request.app.state.redis.lrange(KEY, 0, -1)}


@app.post("/api/notes", status_code=201)
async def add_note(note: Note, request: Request):
    if not await request.app.state.redis.eval(ADD_NOTE, 1, KEY, note.text):
        raise HTTPException(status_code=409, detail="Достигнут лимит: 100 заметок.")
    return {"text": note.text}
