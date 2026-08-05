import streamlit as st
import requests
import uuid
import json
import pandas as pd
import re
import sqlite3

from response_cards import ClaimStatusCard, CoverageSummaryCard
from tool_calling_chatbot import get_claim_status, check_coverage


def build_card_data(user_input):
    """Detect claim/coverage questions and return card info dict if applicable, else None."""
    claim_match = re.search(r"\bC-?\d{3,}\b", user_input, re.IGNORECASE)
    if claim_match and "claim" in user_input.lower():
        claim_id = claim_match.group(0).upper()
        if not claim_id.startswith("C-"):
            claim_id = "C-" + claim_id[1:]
        try:
            result = get_claim_status(claim_id)
            card = ClaimStatusCard(
                claim_id=result.claim_id,
                status=result.status,
                amount=result.claim_amount,
                date=None,
            )
            return {"type": "claim", "data": card.model_dump()}
        except Exception:
            return None

    plan_match = re.search(r"\bPLN-?\d{3,}\b", user_input, re.IGNORECASE)
    if plan_match and ("covered" in user_input.lower() or "coverage" in user_input.lower()):
        plan_id = plan_match.group(0).upper()
        procedure_match = re.search(r"is (.+?) covered", user_input, re.IGNORECASE)
        procedure = procedure_match.group(1) if procedure_match else "General"
        try:
            result = check_coverage(plan_id, procedure)
            conn = sqlite3.connect("coverage.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT plan_name, annual_deductible, copay_primary_care FROM plans WHERE plan_id = ?",
                (plan_id,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                card = CoverageSummaryCard(
                    plan_name=row[0],
                    deductible=row[1],
                    copay=row[2],
                    covered=result.covered,
                )
                return {"type": "coverage", "data": card.model_dump()}
        except Exception:
            return None
    return None


def render_card(card_info):
    """Render a card from a stored card_info dict."""
    if not card_info:
        return
    if card_info["type"] == "claim":
        c = card_info["data"]
        with st.container(border=True):
            st.subheader(f"📋 Claim {c['claim_id']}")
            col1, col2 = st.columns(2)
            with col1:
                status_color = "🔴" if c["status"] == "Denied" else "🟢" if c["status"] == "Approved" else "🟡"
                st.metric("Status", f"{status_color} {c['status']}")
            with col2:
                st.metric("Amount", f"${c['amount']:,.2f}")
    elif card_info["type"] == "coverage":
        c = card_info["data"]
        with st.container(border=True):
            st.subheader(f"🏥 {c['plan_name']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Deductible", f"${c['deductible']:,.0f}")
            with col2:
                st.metric("Copay", f"${c['copay']:,.0f}")
            with col3:
                st.metric("Covered", "✅" if c["covered"] else "❌")


API_URL = "http://127.0.0.1:8001/chat/stream"

st.set_page_config(page_title="Coverage Assistant", page_icon="💬")

# ---------- Session state setup ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Plan Selector")
    try:
        plans_df = pd.read_csv("data/plans.csv")
        plan_options = plans_df["plan_name"].tolist()
        selected_plan = st.selectbox("Choose a plan", plan_options)
        st.caption(f"Plan ID: {plans_df[plans_df['plan_name'] == selected_plan]['plan_id'].values[0]}")
    except Exception as e:
        st.warning(f"Could not load plans: {e}")
        selected_plan = None

    st.divider()

    if st.button("🔄 New conversation"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.caption(f"Session ID: `{st.session_state.session_id[:8]}...`")

# ---------- Main chat area ----------
st.title("💬 Coverage Assistant")
st.caption("Ask about deductibles, coverage, claims, and more.")

# Render existing conversation history (including any saved cards/citations)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("card"):
            render_card(msg["card"])
        if msg.get("citations"):
            with st.expander(f"📄 Policy sources ({len(msg['citations'])})"):
                for i, cid in enumerate(msg["citations"], 1):
                    st.caption(f"[{i}] {cid}")

# Chat input box
user_input = st.chat_input("Ask a question about your coverage...")

if user_input:
    card_info = build_card_data(user_input)

    # Show user's message immediately
    st.session_state.messages.append({"role": "user", "content": user_input, "card": None, "citations": None})
    with st.chat_message("user"):
        st.write(user_input)

    # ---------- Streaming assistant response ----------
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        citation_chunk_ids = []

        try:
            with st.spinner("Thinking..."):
                response = requests.post(
                    API_URL,
                    json={
                        "session_id": st.session_state.session_id,
                        "member_id": "M-1004",
                        "message": user_input,
                    },
                    stream=True,
                    timeout=30,
                )

                for line in response.iter_lines():
                    if line:
                        decoded = line.decode("utf-8")
                        if decoded.startswith("data: "):
                            payload = json.loads(decoded[6:])

                            if "token" in payload:
                                full_response += payload["token"]
                                placeholder.write(full_response + "▌")

                            elif "error" in payload:
                                full_response = f"⚠️ {payload['error']}"
                                placeholder.write(full_response)
                                break

                            elif payload.get("done"):
                                citation_chunk_ids = payload.get("chunk_ids", [])
                                break

            placeholder.write(full_response)

            if card_info:
                render_card(card_info)

            if citation_chunk_ids:
                with st.expander(f"📄 Policy sources ({len(citation_chunk_ids)})"):
                    for i, cid in enumerate(citation_chunk_ids, 1):
                        st.caption(f"[{i}] {cid}")

        except requests.exceptions.Timeout:
            full_response = "⚠️ The response took too long. Please try again."
            placeholder.write(full_response)
        except requests.exceptions.RequestException as e:
            full_response = f"⚠️ Could not reach the backend: {e}"
            placeholder.write(full_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "card": card_info,
        "citations": citation_chunk_ids,
    })