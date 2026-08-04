import streamlit as st
import requests
import uuid
import json
import pandas as pd

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

# Render existing conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input box
user_input = st.chat_input("Ask a question about your coverage...")

if user_input:
    # Show user's message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # ---------- Streaming assistant response ----------
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        first_token_received = False

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
                                first_token_received = True

                            elif "error" in payload:
                                full_response = f"⚠️ {payload['error']}"
                                placeholder.write(full_response)
                                break

                            elif payload.get("done"):
                                break

            placeholder.write(full_response)

        except requests.exceptions.Timeout:
            full_response = "⚠️ The response took too long. Please try again."
            placeholder.write(full_response)
        except requests.exceptions.RequestException as e:
            full_response = f"⚠️ Could not reach the backend: {e}"
            placeholder.write(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response}) 