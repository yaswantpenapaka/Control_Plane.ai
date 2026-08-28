import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SimulatedToolRegistry:
    @staticmethod
    def execute(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "issue_refund":
            return SimulatedToolRegistry.issue_refund(arguments)
        elif tool_name == "lookup_customer":
            return SimulatedToolRegistry.lookup_customer(arguments)
        elif tool_name == "cancel_subscription":
            return SimulatedToolRegistry.cancel_subscription(arguments)
        elif tool_name == "change_address":
            return SimulatedToolRegistry.change_address(arguments)
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
            }

    @staticmethod
    def issue_refund(args: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = args.get("customer_id")
        amount = args.get("amount")

        logger.info(f"[SIMULATED] Issuing refund: customer_id={customer_id}, amount={amount}")

        return {
            "success": True,
            "tool": "issue_refund",
            "customer_id": customer_id,
            "amount": amount,
            "status": "refund_queued",
            "estimated_processing_time": "5-7 business days",
        }

    @staticmethod
    def lookup_customer(args: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = args.get("customer_id")

        logger.info(f"[SIMULATED] Looking up customer: {customer_id}")

        return {
            "success": True,
            "tool": "lookup_customer",
            "customer_id": customer_id,
            "customer_tier": "standard",
            "account_age_days": 730,
            "previous_refunds": 1,
        }

    @staticmethod
    def cancel_subscription(args: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = args.get("customer_id")
        subscription_id = args.get("subscription_id")

        logger.info(f"[SIMULATED] Cancelling subscription: customer_id={customer_id}, subscription_id={subscription_id}")

        return {
            "success": True,
            "tool": "cancel_subscription",
            "customer_id": customer_id,
            "subscription_id": subscription_id,
            "status": "cancelled",
            "effective_date": "2026-08-27",
        }

    @staticmethod
    def change_address(args: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = args.get("customer_id")
        new_address = args.get("address")

        logger.info(f"[SIMULATED] Changing address: customer_id={customer_id}, address={new_address}")

        return {
            "success": True,
            "tool": "change_address",
            "customer_id": customer_id,
            "new_address": new_address,
            "status": "updated",
        }
