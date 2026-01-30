import json
import requests
import streamlit as st

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="OpsCopilot", layout="wide")
st.title("OpsCopilot — Agentic SQL + RAG Support Assistant")

colL, colR = st.columns([1, 2])

with colL:
    st.subheader("Tickets")
    limit = st.slider("Load tickets", 10, 200, 50, 10)
    tickets = requests.get(f"{API}/tickets", params={"limit": limit}).json()

    ticket_labels = [
        f"#{t['id']} | {t.get('status')} | {t.get('priority')} | {t.get('customer_tier')} | {t.get('subject')}"
        for t in tickets
    ]
    idx = st.selectbox("Select a ticket", range(len(tickets)), format_func=lambda i: ticket_labels[i])
    ticket_id = tickets[idx]["id"]

    model = st.text_input("Model", value="gemini-2.5-flash")
    free_text = st.text_area("Or test with free text (optional)", height=140)
    run_btn = st.button("Run Agent", type="primary")

with colR:
    st.subheader("Ticket Details")
    t = requests.get(f"{API}/tickets/{ticket_id}").json()
    st.write({
        "id": t["id"],
        "subject": t.get("subject"),
        "status": t.get("status"),
        "priority": t.get("priority"),
        "customer": t.get("customer_name"),
        "tier": t.get("customer_tier"),
        "created_at": t.get("created_at"),
    })
    st.markdown("**Body**")
    st.write(t.get("body", ""))

    if run_btn:
        with st.spinner("Running agent..."):
            payload = {"model": model}
            if free_text.strip():
                payload["free_text"] = free_text.strip()
            else:
                payload["ticket_id"] = ticket_id

            resp = requests.post(f"{API}/run_agent1", json=payload)
            out = resp.json()

        agent_run_id = out["agent_run_id"]
        result = out["result"]

        st.success(f"Agent run complete: {agent_run_id}")
        st.markdown("## Customer Reply")
        st.write(result.get("customer_reply", ""))
        st.markdown("## Recommended Actions")
        st.write(result.get("recommended_actions", []))
        st.markdown("## Citations")
        st.write(result.get("citations", []))
        st.markdown("## Risk Notes")
        st.write(result.get("risk_notes", []))

        st.markdown("## Agent Trace (Tool Calls)")
        calls = requests.get(f"{API}/runs/{agent_run_id}/tool_calls").json()

        for c in calls:
            with st.expander(f"{c['id']} — {c['tool_name']} — {c['created_at']}"):
                tool_input = json.loads(c["tool_input_json"])
                tool_output = json.loads(c["tool_output_json"])

                st.markdown("### Input")
                st.json(tool_input)
                st.markdown("### Output")
                st.json(tool_output)

                if c["tool_name"] == "llm_generate":
                    prompt = tool_input.get("prompt", {})
                    st.markdown("### 🧠 LLM Prompt Debug")
                    st.code(prompt.get("user_issue", ""))
                    st.json(prompt.get("sql_context", {}))
                    st.code(prompt.get("policy_context", ""))