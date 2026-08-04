import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from openai import OpenAI
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
llm_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

GROUNDING_PROMPT = """Answer using ONLY the context below.
If the answer isn't in the context, say you don't know and suggest the member contact support.
This is not medical advice.

Context: {context}

Question: {question}
"""

def stream_chat_response(session_id, member_id, message):
    start_time = time.time()
    save_turn(session_id, member_id, "user", message)

    try:
        retrieved = retrieve(message)
        context_text = "\n".join(retrieved["context"])
        prompt = GROUNDING_PROMPT.format(context=context_text, question=message)

        stream = llm_client.chat.completions.create(
            model="llama3.1",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        full_answer = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_answer += delta
                yield f"data: {json.dumps({'token': delta})}\n\n"

        save_turn(session_id, member_id, "assistant", full_answer)
        elapsed = round(time.time() - start_time, 3)
        print(f"[TIMING] session={session_id} elapsed={elapsed}s classification={retrieved['classification']}")
        yield f"data: {json.dumps({'done': True})}\n\n"

    except Exception as e:
        elapsed = round(time.time() - start_time, 3)
        print(f"[ERROR] session={session_id} elapsed={elapsed}s error={e}")
        yield f"data: {json.dumps({'error': 'Something went wrong while generating a response. Please try again or contact support.'})}\n\n"

@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    return StreamingResponse(
        stream_chat_response(request.session_id, request.member_id, request.message),
        media_type="text/event-stream",
    )

@app.get("/history/{session_id}")
def history(session_id: str):
    return {"session_id": session_id, "turns": get_history(session_id)}

@app.get("/health")
def health_check():
    return {"status": "ok"}
