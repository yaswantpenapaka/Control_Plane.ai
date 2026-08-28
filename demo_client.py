"""
ControlPlane.ai Demo Client - OpenAI-Compatible Testing

This script demonstrates ControlPlane.ai governance in action.
It sends 3 hero scenarios through the governance pipeline and displays decisions.

Usage:
    1. Start the gateway: uvicorn gateway.app:app --host 127.0.0.1 --port 8000
    2. Run this script: python demo_client.py
"""

from openai import OpenAI
import json


def create_client():
    """Create OpenAI-compatible client for ControlPlane.ai gateway."""
    return OpenAI(
        base_url="http://127.0.0.1:8000/v1",
        api_key="controlplane-demo"
    )


def display_result(scenario_name, result):
    """Display governance decision in readable format."""
    print(f"\n{'='*80}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*80}\n")

    # User message
    choice = result["choices"][0]
    print(f"User Query:")
    print(f"  {choice.get('user_message', 'N/A')}\n")

    # AI Response
    print(f"AI Response:")
    print(f"  {choice['message']['content']}\n")

    # Governance Decision
    controlplane = result.get("controlplane", {})
    if controlplane:
        print(f"GOVERNANCE DECISION:")
        print(f"  Decision:      {controlplane.get('decision', 'UNKNOWN').upper()}")
        print(f"  Risk State:    {controlplane.get('risk_state', 'UNKNOWN').upper()}")
        print(f"  Confidence:    {controlplane.get('confidence', 0):.2f}")
        print(f"  Reason Codes:  {', '.join(controlplane.get('reason_codes', ['NONE']))}")
        print(f"  Latency:       {controlplane.get('latency_ms', 0):.1f}ms")
        print(f"  Audit ID:      {controlplane.get('audit_id', 'N/A')}\n")

    # Token Usage
    usage = result.get("usage", {})
    if usage:
        print(f"TOKEN USAGE:")
        print(f"  Input:         {usage.get('prompt_tokens', 0)}")
        print(f"  Output:        {usage.get('completion_tokens', 0)}")
        print(f"  Total:         {usage.get('total_tokens', 0)}\n")

    # Metadata
    metadata = result.get("metadata", {})
    if metadata:
        print(f"METADATA:")
        print(f"  Mode:          {metadata.get('mode', 'N/A').upper()}")
        print(f"  Workflow:      {metadata.get('workflow', 'N/A')}")
        print(f"  Est. Cost:     ${metadata.get('estimated_cost', 0):.4f}\n")


def run_demo():
    """Run 3 hero scenarios through governance pipeline."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "ControlPlane.ai - OpenAI-Compatible Demo".center(78) + "║")
    print("║" + "Governance Pipeline Testing".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")

    try:
        client = create_client()

        scenarios = [
            {
                "name": "HERO_1: Hallucination Detection",
                "message": "I bought this 45 days ago. Can I get a full refund? Everyone gets 90-day refunds, right?"
            },
            {
                "name": "HERO_2: Tool Amount Gating",
                "message": "Issue the refund for me."
            },
            {
                "name": "HERO_3: PII Detection",
                "message": "My email is john.doe@example.com and my phone is 9876543210. Can you confirm my account?"
            }
        ]

        for scenario in scenarios:
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {
                            "role": "user",
                            "content": scenario["message"]
                        }
                    ],
                    extra_body={
                        "workflow": "refund-copilot"
                    },
                    timeout=30
                )

                # Convert response to dict for display
                result = response.model_dump()
                result["choices"][0]["user_message"] = scenario["message"]

                display_result(scenario["name"], result)

            except Exception as e:
                print(f"\n❌ Error in {scenario['name']}: {str(e)}")

        print(f"\n{'='*80}")
        print("Demo Complete!")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n❌ Connection Error: {str(e)}")
        print("\nMake sure the gateway is running:")
        print("  uvicorn gateway.app:app --host 127.0.0.1 --port 8000\n")
        return False

    return True


if __name__ == "__main__":
    success = run_demo()
    exit(0 if success else 1)
