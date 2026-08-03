import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from retrieval_engine import retrieve
from rag_chatbot import generate_answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions.db")

def init_session_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            member_id TEXT,
            role TEXT,
            content TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()

init_session_db()

def save_turn(session_id, member_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO turns (session_id, member_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        (session_id, member_id, role, content, time.time())
    )
    conn.commit()
    conn.close()

def get_history(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, timestamp FROM turns WHERE session_id = ? ORDER BY id",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

class ChatRequest(BaseModel):
    session_id: str
    member_id: str
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    start_time = time.time()
    save_turn(request.session_id, request.member_id, "user", request.message)

    try:
        retrieved = retrieve(request.message)
        answer = generate_answer(request.message, retrieved["context"])
    except Exception as e:
        elapsed = round(time.time() - start_time, 3)
        print(f"[ERROR] session={request.session_id} elapsed={elapsed}s error={e}")
        return {
            "session_id": request.session_id,
            "error": "Something went wrong while generating a response. Please try again or contact support.",
            "status": 500,
        }

    save_turn(request.session_id, request.member_id, "assistant", answer)
    elapsed = round(time.time() - start_time, 3)
    print(f"[TIMING] session={request.session_id} elapsed={elapsed}s classification={retrieved['classification']}")

    return {
        "session_id": request.session_id,
        "classification": retrieved["classification"],
        "answer": answer,
        "elapsed_seconds": elapsed,
    }

@app.get("/history/{session_id}")
def history(session_id: str):
    return {"session_id": session_id, "turns": get_history(session_id)}

@app.get("/health")
def health_check():
    return {"status": "ok"}
