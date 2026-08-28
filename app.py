import streamlit as st
import requests
import json
from datetime import datetime
from config.settings import get_settings
from policy.engine import PolicyEngine

st.set_page_config(page_title="ControlPlane.ai", layout="wide")

st.markdown("# ControlPlane.ai")
st.markdown("### Models generate. ControlPlane governs.")

settings = get_settings()
policy_engine = PolicyEngine()

mode_badge_color = (
    "🟢 LIVE"
    if settings.is_live_mode
    else ("🟡 DEMO" if settings.is_demo_mode else "🔵 REPLAY")
)
st.markdown(f"**Mode:** `{mode_badge_color}`")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    [
        "Live Control",
        "Decision Inspector",
        "Policy Center",
        "Risk & Budget",
        "Bias Monitor",
        "Audit Explorer",
        "Evaluation",
        "Demo Scenarios",
    ]
)

with tab1:
    st.header("Live Control Panel")

    col1, col2 = st.columns(2)

    with col1:
        workflow = st.selectbox(
            "Workflow",
            options=policy_engine.list_workflows(),
            index=0,
        )

    with col2:
        cohort = st.text_input("Cohort (optional)", "")

    user_message = st.text_area("User Prompt", placeholder="Enter your message...", height=100)

    if st.button("Send Message", type="primary"):
        if user_message and workflow:
            with st.spinner("Processing..."):
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/v1/chat/completions",
                        json={
                            "messages": [{"role": "user", "content": user_message}],
                            "model": settings.groq_model,
                            "workflow": workflow,
                            "cohort": cohort,
                        },
                        timeout=30,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("Request processed!")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader("Model Response")
                            st.write(result["choices"][0]["message"]["content"])

                        with col2:
                            st.subheader("Metadata")
                            st.json(result.get("metadata", {}))

                        st.subheader("Token Usage")
                        st.json(result.get("usage", {}))
                    else:
                        st.error(f"Error: {response.text}")

                except Exception as e:
                    st.error(f"Connection error: {e}")
                    st.info("Make sure the FastAPI gateway is running on http://127.0.0.1:8000")

with tab2:
    st.header("Decision Inspector")
    st.info(
        "This page will show the detailed decision pipeline: "
        "Request → Lane A → Risk Router → Lane B → Decision"
    )

with tab3:
    st.header("Policy Center")

    for workflow_name in policy_engine.list_workflows():
        policy = policy_engine.get_policy(workflow_name)
        if policy:
            with st.expander(f"📋 {workflow_name.upper()}"):
                st.markdown(f"**Risk Tier:** `{policy.risk_tier}`")
                st.markdown(f"**Evidence Required:** `{policy.evidence.required}`")
                st.markdown(f"**Max Refund:** ₹{policy.tools.get('issue_refund', {}).get('max_amount', 'N/A')}")
                st.markdown(f"**Error Budget:** {policy.error_budget.target * 100}% in {policy.error_budget.window}")

with tab4:
    st.header("Risk & Budget Analysis")
    st.info("Budget burn rate, intervention distribution, and Lane A/B routing metrics will appear here.")

with tab5:
    st.header("Bias Monitor")
    st.info("Population-level cohort analytics and disparity measurements will appear here.")

with tab6:
    st.header("Audit Explorer")
    st.info("Recent audit records, decision details, and chain verification status will appear here.")

with tab7:
    st.header("Evaluation Results")
    st.info(
        "Benchmark metrics including precision, recall, PII redaction, "
        "tool-gate accuracy, and latency measurements will appear here."
    )

with tab8:
    st.header("Demo Scenarios")

    demo_scenarios = [
        ("D01", "Grounded policy answer", "✓ ALLOW"),
        ("D02", "Plausible hallucinated policy claim", "→ REGENERATE"),
        ("D03", "No evidence available", "→ ESCALATE"),
        ("D04", "PII leakage", "→ EDIT"),
        ("D05", "Tool amount within policy", "✓ ALLOW"),
        ("D06", "Tool amount above policy", "→ ESCALATE"),
        ("D07", "Tool backed by unsupported claim", "→ BLOCK"),
        ("D08", "Low-risk workflow", "Policy-dependent"),
        ("D09", "Budget pressure", "Tighter routing"),
        ("D10", "Multi-turn propagation", "Action remains gated"),
        ("D11", "Bias batch", "Dashboard warning"),
        ("D12", "Audit tampering", "Chain verification fails"),
    ]

    cols = st.columns(2)
    for idx, (demo_id, description, expected) in enumerate(demo_scenarios):
        with cols[idx % 2]:
            if st.button(f"{demo_id}: {description}"):
                st.info(f"Running {demo_id}... Expected: {expected}")

st.sidebar.markdown("---")
st.sidebar.markdown("**ControlPlane.ai Prototype**")
st.sidebar.markdown(f"Mode: `{settings.controlplane_mode.upper()}`")
st.sidebar.markdown(f"Gateway: `http://127.0.0.1:8000`")
st.sidebar.markdown(f"Database: `{settings.database_path}`")

if st.sidebar.button("Reset Demo Data"):
    st.success("Demo data reset")
