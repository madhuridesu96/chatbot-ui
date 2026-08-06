import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import sqlite3
import re
import tiktoken
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
# ---------- Day 20 conversations table ----------

def init_conversations_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()

init_conversations_db()

# ---------- End Step 1 ----------
def save_conversation_turn(session_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, role, content, time.time())
    )
    conn.commit()
    conn.close()

def get_conversation_history(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY id",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    return len(encoding.encode(text))

def count_history_tokens(history):
    return sum(count_tokens(msg["content"]) for msg in history)

def replace_conversation_history(session_id, new_history):
    """Delete all turns for a session and replace with a new (summarized) history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    for msg in new_history:
        cursor.execute(
            "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, msg["role"], msg["content"], time.time())
        )
    conn.commit()
    conn.close()

def summarize_oldest_half(session_id, history):
    """Summarize the oldest half of history with one LLM call, replace those turns."""
    midpoint = len(history) // 2
    oldest_half = history[:midpoint]
    recent_half = history[midpoint:]

    oldest_text = "\n".join([f"{m['role']}: {m['content']}" for m in oldest_half])
    summary_prompt = f"Summarize this conversation history concisely, preserving any specific facts mentioned (like plan names, plan IDs, claim numbers, dollar amounts):\n\n{oldest_text}"

    response = llm_client.chat.completions.create(
        model="llama3.1",
        messages=[{"role": "user", "content": summary_prompt}],
    )
    summary_text = response.choices[0].message.content

    new_history = [{"role": "system", "content": f"[Summary of earlier conversation]: {summary_text}"}] + recent_half
    replace_conversation_history(session_id, new_history)
    return new_history

def extract_plan_id(text):
    """Detect a plan ID (like PLN-003) mentioned in text."""
    match = re.search(r"\bPLN-?\d{3,}\b", text, re.IGNORECASE)
    if match:
        found = match.group(0).upper()
        if not found.startswith("PLN-"):
            found = "PLN-" + found[3:]
        return found
    return None

def get_remembered_plan_id(session_id):
    """Look through the full conversation history for the most recently mentioned plan_id."""
    history = get_conversation_history(session_id)
    for msg in reversed(history):
        plan_id = extract_plan_id(msg["content"])
        if plan_id:
            return plan_id
    return None

def build_context_messages(session_id, current_message):
    """Load history, apply last-N-turns limit, and detect any remembered plan_id."""
    history = get_conversation_history(session_id)
    total_tokens = count_history_tokens(history)
    print(f"[TOKENS] session={session_id} history_tokens_before={total_tokens}")

    if total_tokens > 2000:
        print(f"[SUMMARIZE] session={session_id} exceeded 2000 tokens, summarizing oldest half...")
        history = summarize_oldest_half(session_id, history)
        new_total = count_history_tokens(history)
        print(f"[TOKENS] session={session_id} history_tokens_after_summary={new_total}")


    remembered_plan_id = get_remembered_plan_id(session_id) or extract_plan_id(current_message)

    last_n = history[-10:]

    return last_n, remembered_plan_id

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

GROUNDING_PROMPT = """Answer using ONLY the context below AND the conversation history and plan information provided above, if relevant.
If the answer isn't in the context or the conversation history, say you don't know and suggest the member contact support.
This is not medical advice.


Context: {context}

Question: {question}
"""

def stream_chat_response(session_id, member_id, message):
    start_time = time.time()
    save_turn(session_id, member_id, "user", message)
    save_conversation_turn(session_id, "user", message)
    
    try:

        recent_history, remembered_plan_id = build_context_messages(session_id, message)

        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent_history])
        plan_note = f"\n[The member has previously mentioned plan_id: {remembered_plan_id}]" if remembered_plan_id else " "
        retrieved = retrieve(message)
        context_text = "\n".join(retrieved["context"])
        prompt = GROUNDING_PROMPT.format(context=context_text, question=message)
        full_prompt = f"Conversation history so far:\n{history_text}{plan_note}\n\n{prompt}"

        stream = llm_client.chat.completions.create(
            model="llama3.1",
            messages=[{"role": "user", "content": full_prompt}],
            stream=True,
        )

        full_answer = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_answer += delta
                yield f"data: {json.dumps({'token': delta})}\n\n"

        save_turn(session_id, member_id, "assistant", full_answer)
        save_conversation_turn(session_id, "assistant", full_answer)

        elapsed = round(time.time() - start_time, 3)
        print(f"[TIMING] session={session_id} elapsed={elapsed}s classification={retrieved['classification']}")
        yield f"data: {json.dumps({'done': True, 'chunk_ids': retrieved.get('chunk_ids', [])})}\n\n"

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
