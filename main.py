from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List
import random
import uuid
import string
from datetime import datetime, timedelta          # ← add timedelta here
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager

app = FastAPI(title="Anonymous Real-Time Polling API")

# CORS (unchanged)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
polls: Dict[str, dict] = {}
connections: Dict[str, List[WebSocket]] = {}


class PollCreate(BaseModel):
    question: str
    options: List[str]


class Vote(BaseModel):
    option: str
    anon_id: str


class ClosePoll(BaseModel):
    anon_id: str


def generate_poll_id(length=6):
    chars = string.ascii_uppercase + string.digits
    while True:
        poll_id = ''.join(random.choice(chars) for _ in range(length))
        if poll_id not in polls:
            return poll_id


def cleanup_old_polls():
    now = datetime.utcnow()
    to_delete = []
    for poll_id, data in list(polls.items()):
        expires = data.get("expires_at")
        if expires and isinstance(expires, datetime) and expires < now:
            to_delete.append(poll_id)

    for poll_id in to_delete:
        if poll_id in connections:
            for ws in connections[poll_id][:]:
                try:
                    asyncio.create_task(ws.close())
                except Exception:
                    pass
            connections.pop(poll_id, None)
        polls.pop(poll_id, None)


# Modern lifespan + background cleanup
@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(cleanup_loop())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


async def cleanup_loop():
    while True:
        cleanup_old_polls()
        await asyncio.sleep(60)


app.router.lifespan_context = lifespan  # Attach it


# ──────────────────────────────────────────────────────────────

@app.get("/anonymous-id")
def get_anonymous_id():
    return {"anon_id": f"anon_{uuid.uuid4().hex[:12]}"}


@app.post("/polls")
def create_poll(poll: PollCreate, anon_id: str = Query(...)):
    poll_id = generate_poll_id()
    now = datetime.utcnow()
    polls[poll_id] = {
        "question": poll.question,
        "options": {opt: 0 for opt in poll.options},
        "voted_users": set(),
        "creator": anon_id,
        "created_at": now,
        "voting_ends_at": now + timedelta(hours=24),
        "expires_at": now + timedelta(hours=48),
        "is_open": True
    }
    connections[poll_id] = []
    return {"poll_id": poll_id}


@app.get("/polls/{poll_id}")
def get_poll(poll_id: str, anon_id: str = Query(None)):
    if poll_id not in polls:
        raise HTTPException(status_code=404, detail="Poll not found or has expired")

    poll = polls[poll_id]
    now = datetime.utcnow()
    is_open = poll["is_open"] and now < poll["voting_ends_at"]

    return {
        "question": poll["question"],
        "options": poll["options"],
        "is_open": is_open,
        "created_at": poll["created_at"].isoformat(),
        "voting_ends_at": poll["voting_ends_at"].isoformat(),
        "results_visible_until": poll["expires_at"].isoformat(),
        "is_creator": poll.get("creator") == anon_id,
    }


@app.post("/polls/{poll_id}/vote")
async def vote(poll_id: str, vote: Vote):
    if poll_id not in polls:
        raise HTTPException(status_code=404, detail="Poll not found or has expired")

    poll = polls[poll_id]
    now = datetime.utcnow()

    if now >= poll["voting_ends_at"]:
        poll["is_open"] = False
        raise HTTPException(status_code=403, detail="Voting period has ended")
    if not poll["is_open"]:
        raise HTTPException(status_code=403, detail="Poll is closed")
    if vote.option not in poll["options"]:
        raise HTTPException(status_code=400, detail="Invalid option")
    if vote.anon_id in poll["voted_users"]:
        raise HTTPException(status_code=403, detail="You have already voted")

    poll["options"][vote.option] += 1
    poll["voted_users"].add(vote.anon_id)

    payload = {
        "question": poll["question"],
        "options": poll["options"],
        "is_open": now < poll["voting_ends_at"]
    }

    # Broadcast to connected clients
    for ws in connections.get(poll_id, [])[:]:
        try:
            await ws.send_json(payload)
        except Exception:
            connections[poll_id].remove(ws)

    return {"message": "Vote recorded"}


@app.post("/polls/{poll_id}/close")
async def close_poll(poll_id: str, request: ClosePoll):
    if poll_id not in polls:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = polls[poll_id]
    if poll.get("creator") != request.anon_id:
        raise HTTPException(status_code=403, detail="Only the creator can close this poll")

    poll["is_open"] = False

    payload = {
        "question": poll["question"],
        "options": poll["options"],
        "is_open": False,
        "message": "Poll closed by creator"
    }

    for ws in connections.get(poll_id, [])[:]:
        try:
            await ws.send_json(payload)
        except Exception:
            connections[poll_id].remove(ws)

    return {"message": "Poll closed. Results visible until expiration."}


@app.websocket("/ws/polls/{poll_id}")
async def poll_updates(websocket: WebSocket, poll_id: str):
    # Check existence before accepting
    if poll_id not in polls:
        await websocket.close(code=1008, reason="Poll not found or expired")
        return

    await websocket.accept()

    connections.setdefault(poll_id, []).append(websocket)

    poll = polls[poll_id]
    now = datetime.utcnow()

    await websocket.send_json({
        "question": poll["question"],
        "options": poll["options"],
        "is_open": poll["is_open"] and now < poll["voting_ends_at"],
        "voting_ends_at": poll["voting_ends_at"].isoformat(),
    })

    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        if poll_id in connections:
            connections[poll_id].remove(websocket)
            if not connections[poll_id]:
                connections.pop(poll_id, None)