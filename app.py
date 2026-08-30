import streamlit as st
import requests
import json
from datetime import datetime
from config.settings import get_settings
from policy.engine import PolicyEngine
from demo.fixtures import DEMO_SCENARIOS

st.set_page_config(
    page_title="ControlPlane.ai",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "last_decision" not in st.session_state:
    st.session_state.last_decision = None

# Custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5em;
        font-weight: bold;
        color: #1F3A70;
        margin-bottom: 0.2em;
    }
    .tagline {
        font-size: 1.2em;
        color: #00A88F;
        font-style: italic;
        margin-bottom: 1em;
    }
    .decision-box {
        padding: 1.5em;
        border-radius: 0.5em;
        margin: 1em 0;
    }
    .decision-allow { background-color: #E8F5E9; border-left: 5px solid #4CAF50; }
    .decision-edit { background-color: #FFF3E0; border-left: 5px solid #FF9800; }
    .decision-regenerate { background-color: #FCE4EC; border-left: 5px solid #E91E63; }
    .decision-escalate { background-color: #FFEBEE; border-left: 5px solid #F44336; }
    .decision-block { background-color: #F3E5F5; border-left: 5px solid #9C27B0; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'>ControlPlane.ai</div>", unsafe_allow_html=True)
st.markdown("<div class='tagline'>🤖 Models generate. ControlPlane governs.</div>", unsafe_allow_html=True)

settings = get_settings()
policy_engine = PolicyEngine()

mode_badge_color = (
    "🟢 LIVE"
    if settings.is_live_mode
    else ("🟡 DEMO" if settings.is_demo_mode else "🔵 REPLAY")
)
st.markdown(f"**Mode:** `{mode_badge_color}`")

# HELPER FUNCTION: Display governance decision
def display_governance_decision(result):
    """Display governance decision prominently"""
    cp = result.get("controlplane", {})
    decision = cp.get("decision", "UNKNOWN").upper()

    # Store in session state
    st.session_state.last_decision = {
        "decision": decision,
        "risk_state": cp.get("risk_state", "N/A"),
        "confidence": cp.get("confidence", 0),
        "reason_codes": cp.get("reason_codes", []),
        "latency_ms": cp.get("latency_ms", 0),
        "audit_id": cp.get("audit_id", "N/A"),
    }

    # Color code
    decision_colors = {
        "ALLOW": "🟢",
        "EDIT": "🟡",
        "REGENERATE": "🟠",
        "ESCALATE": "🔴",
        "BLOCK": "⛔"
    }
    decision_emoji = decision_colors.get(decision, "❓")

    # Decision banner with emoji
    decision_color_map = {
        "ALLOW": "#4CAF50",
        "EDIT": "#FF9800",
        "REGENERATE": "#E91E63",
        "ESCALATE": "#F44336",
        "BLOCK": "#9C27B0"
    }
    decision_color = decision_color_map.get(decision, "#666")

    st.markdown(f"<h2 style='color: {decision_color};'>{decision_emoji} {decision}</h2>", unsafe_allow_html=True)

    # Key metrics in nice layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Risk State", cp.get("risk_state", "N/A").upper(), help="ENTAILED | CONTRADICTED | UNVERIFIED")
    with col2:
        conf = cp.get('confidence', 0)
        st.metric("📊 Confidence", f"{conf:.2f}", f"{int(conf*100)}%")
    with col3:
        st.metric("⏱️ Latency", f"{cp.get('latency_ms', 0):.0f}ms")
    with col4:
        audit_id = str(cp.get("audit_id", "N/A"))[:8]
        st.metric("📝 Audit ID", audit_id, help="Decision record hash")

    # Reason codes
    if cp.get("reason_codes"):
        st.markdown("**Reason Codes:**")
        reason_text = " | ".join(cp.get("reason_codes", []))
        st.code(reason_text, language="text")

    st.divider()

    # Response
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("AI Response")
        st.write(result["choices"][0]["message"]["content"])
    with col2:
        st.subheader("Governance Details")
        st.markdown(f"**Intervention:** {cp.get('intervention', 'None')}")
        st.markdown(f"**Tool Executed:** {cp.get('tool_executed', 'N/A')}")
        st.markdown(f"**Workflow:** {result.get('metadata', {}).get('workflow', 'N/A')}")
        st.markdown(f"**Mode:** {result.get('metadata', {}).get('mode', 'N/A').upper()}")

# HELPER FUNCTION: Send request to gateway
def send_to_gateway(messages, workflow, cohort=""):
    """Send request to gateway and get governance decision"""
    try:
        response = requests.post(
            "http://127.0.0.1:8000/v1/chat/completions",
            json={
                "messages": messages,
                "model": settings.groq_model,
                "workflow": workflow,
                "cohort": cohort,
            },
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        st.info("Make sure the FastAPI gateway is running on http://127.0.0.1:8000")
        return None

# TABS: Only keep essential ones
tab1, tab2, tab3, tab4 = st.tabs([
    "Live Control",
    "Decision Inspector",
    "Policy Center",
    "Demo Scenarios",
])

# TAB 1: Live Control
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
                result = send_to_gateway(
                    messages=[{"role": "user", "content": user_message}],
                    workflow=workflow,
                    cohort=cohort
                )
                if result:
                    st.success("Request processed!")
                    display_governance_decision(result)

# TAB 2: Decision Inspector
with tab2:
    st.header("Decision Inspector")

    st.markdown("### How Decisions Are Made")

    st.markdown("""
    **Pipeline Flow:**

    1. **Lane A (Deterministic Checks)**
       - PII Detection: Email, Phone, Account Numbers
       - Tool Validation: Amount limits, Authorization checks
       - Safety Keywords: Blocks unsafe operations

    2. **Risk Router**
       - Decides if Lane B (ML-based) checks needed
       - Routes based on policy risk tier

    3. **Lane B (Evidence-Based Checks)**
       - Retrieval: Fetch relevant policy documents
       - Claim Extraction: Identify factual claims
       - NLI Verification: Check claims against policy (entailment scoring)

    4. **Decision Engine**
       - Combines Lane A + Lane B results
       - Applies policy rules
       - Outputs: ALLOW | EDIT | REGENERATE | ESCALATE | BLOCK

    5. **Audit Trail**
       - Records decision with reason codes
       - Creates tamper-evident hash chain
       - Stores in SQLite database
    """)

    st.markdown("### Last Decision Details")
    if st.session_state.last_decision:
        dec = st.session_state.last_decision
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Decision:** {dec['decision']}")
            st.write(f"**Risk State:** {dec['risk_state']}")
            st.write(f"**Confidence:** {dec['confidence']:.2f}")
        with col2:
            st.write(f"**Reason Codes:** {', '.join(dec['reason_codes'])}")
            st.write(f"**Latency:** {dec['latency_ms']:.0f}ms")
    else:
        st.info("Send a message in Live Control to see decision details")

# TAB 3: Policy Center
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

# TAB 4: Demo Scenarios - FIXED
with tab4:
    st.header("Demo Scenarios")
    st.markdown("### 🎯 Click any scenario to run it and see governance decisions in action")

    # Hero Scenarios
    st.markdown("### ⭐ Hero Scenarios (Proven Working)")

    demo_scenarios = [
        ("HERO_1", "Hallucination Detection", "🚨 Detects false 90-day policy claim when actual policy is 30 days"),
        ("HERO_2", "Tool Amount Gating", "🔒 Blocks refund exceeding ₹5000 policy limit"),
        ("HERO_3", "PII Detection", "🔐 Redacts email and phone from response"),
    ]

    cols = st.columns(3)
    for idx, (scenario_id, title, description) in enumerate(demo_scenarios):
        with cols[idx]:
            # Create nice button with description
            st.markdown(f"**{title}**")
            st.caption(description)

            if st.button(f"▶ Run {scenario_id}", use_container_width=True, key=f"btn_{scenario_id}"):
                with st.spinner(f"⏳ Running {scenario_id}..."):
                    if scenario_id in DEMO_SCENARIOS:
                        scenario = DEMO_SCENARIOS[scenario_id]
                        # Send scenario messages to gateway
                        result = send_to_gateway(
                            messages=scenario.get("user_messages", []),
                            workflow=scenario.get("workflow", "refund-copilot"),
                        )
                        if result:
                            st.success(f"✓ {scenario_id} Complete")

                            # Show scenario info
                            with st.expander(f"📋 Scenario Details: {scenario.get('name', scenario_id)}", expanded=True):
                                st.markdown(f"**Description:** {scenario.get('description', 'N/A')}")
                                st.markdown(f"**Expected Decision:** `{scenario.get('expected_decision', 'N/A')}`")
                                st.markdown(f"**Expected Risk State:** `{scenario.get('expected_risk_state', 'N/A')}`")

                            # Show actual governance decision
                            st.markdown("### 🎯 Governance Decision")
                            display_governance_decision(result)
                    else:
                        st.error(f"Scenario {scenario_id} not found")

    # Other demo scenarios
    st.markdown("---")
    st.markdown("### 📚 Other Demo Scenarios (D01-D12)")
    st.caption("Additional scenarios covering edge cases and complex interactions")

    other_scenarios = [
        ("D01", "Grounded policy answer"),
        ("D02", "Partial hallucination with correct dates"),
        ("D03", "Outside refund window"),
        ("D04", "PII leakage"),
        ("D05", "Tool within policy limits"),
        ("D06", "Tool above policy limits"),
    ]

    cols = st.columns(3)
    for idx, (scenario_id, desc) in enumerate(other_scenarios):
        with cols[idx % 3]:
            if st.button(f"▶ {scenario_id}", use_container_width=True, key=f"demo_{scenario_id}"):
                with st.spinner(f"Running {scenario_id}..."):
                    if scenario_id in DEMO_SCENARIOS:
                        scenario = DEMO_SCENARIOS[scenario_id]
                        result = send_to_gateway(
                            messages=scenario.get("user_messages", []),
                            workflow=scenario.get("workflow", "refund-copilot"),
                        )
                        if result:
                            st.success(f"✓ {scenario_id} Complete")
                            display_governance_decision(result)
                    else:
                        st.info(f"Scenario {scenario_id} - {desc}")

# SIDEBAR
st.sidebar.markdown("---")
st.sidebar.markdown("**ControlPlane.ai Prototype**")
st.sidebar.markdown(f"Mode: `{settings.controlplane_mode.upper()}`")
st.sidebar.markdown(f"Gateway: `http://127.0.0.1:8000`")
st.sidebar.markdown(f"Database: `{settings.database_path}`")

if st.sidebar.button("Reset Demo Data"):
    st.success("Demo data reset")
