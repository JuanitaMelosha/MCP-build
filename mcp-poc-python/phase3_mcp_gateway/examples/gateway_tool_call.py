from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gateway import build_default_gateway


async def main() -> None:
    gateway = build_default_gateway()

    customer = await gateway.call_tool("customer.get_customer", {"customer_id": "123"})
    weather = await gateway.call_tool("weather.get_weather", {"city": "Chennai"})
    ticket = await gateway.call_tool(
        "ticket.create_ticket",
        {"title": "Login Issue", "priority": "High"},
    )

    print("customer.get_customer:")
    print(json.dumps(customer, indent=2))
    print("\nweather.get_weather:")
    print(json.dumps(weather, indent=2))
    print("\nticket.create_ticket:")
    print(json.dumps(ticket, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

