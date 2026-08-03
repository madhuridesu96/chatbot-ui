import streamlit as st
import requests
import uuid
import pandas as pd

API_URL = "http://127.0.0.1:8001/chat"

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

    # Call the backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "session_id": st.session_state.session_id,
                        "member_id": "M-1004",
                        "message": user_input,
                    },
                    timeout=30,
                )
                data = response.json()
                if "error" in data:
                    answer = f"⚠️ {data['error']}"
                else:
                    answer = data.get("answer", "No answer received.")
            except requests.exceptions.RequestException as e:
                answer = f"⚠️ Could not reach the backend: {e}"

        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})