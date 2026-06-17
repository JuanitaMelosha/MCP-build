from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP("Phase 2 MCP Learning Lab")


@mcp.tool()
def get_customer(customer_id: str) -> dict[str, str]:
    """Look up a customer by id."""
    return {"id": customer_id, "name": "John Doe", "plan": "Premium"}


@mcp.tool()
def create_ticket(title: str, priority: str) -> dict[str, str]:
    """Create a customer support ticket."""
    return {"ticket_id": "T-1001", "status": "Created"}


@mcp.resource("company://policy", name="company_policy")
def company_policy() -> str:
    """Read the company support policy."""
    policy: dict[str, Any] = {
        "name": "Acme Support Policy",
        "support_hours": "24x7 for Premium customers",
        "sla": {
            "high": "Respond within 4 business hours",
            "normal": "Respond within 1 business day",
        },
        "rules": [
            "Never ask for a customer password.",
            "Verify account ownership before discussing billing.",
            "Escalate security issues immediately.",
        ],
    }
    return json.dumps(policy, indent=2)


@mcp.resource("company://product-catalog", name="product_catalog")
def product_catalog() -> str:
    """Read the product catalog."""
    catalog: dict[str, Any] = {
        "products": [
            {
                "sku": "CRM-PREMIUM",
                "name": "Acme CRM Premium",
                "price_usd": 99,
                "features": ["pipeline tracking", "AI summaries", "priority support"],
            },
            {
                "sku": "DESK-PRO",
                "name": "Acme Desk Pro",
                "price_usd": 49,
                "features": ["ticketing", "knowledge base", "SLA alerts"],
            },
        ]
    }
    return json.dumps(catalog, indent=2)


@mcp.prompt(name="customer_support_template")
def customer_support_template(customer_name: str = "the customer", issue: str = "the issue") -> str:
    """Create a support response prompt."""
    return (
        "You are a helpful customer support specialist.\n"
        f"Customer: {customer_name}\n"
        f"Issue: {issue}\n\n"
        "Write a clear, empathetic response with the next best action."
    )


@mcp.prompt(name="bug_report_template")
def bug_report_template(product: str = "the product", summary: str = "the bug") -> str:
    """Create an engineering bug report prompt."""
    return (
        "Create a concise bug report for engineering.\n"
        f"Product: {product}\n"
        f"Summary: {summary}\n\n"
        "Include observed behavior, expected behavior, reproduction steps, and impact."
    )


if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        raise SystemExit(0) from None
