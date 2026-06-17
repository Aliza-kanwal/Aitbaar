"""
WhatsApp Order History Parser
Parses exported WhatsApp chat .txt files to extract order/payment patterns.
WhatsApp export format: [DD/MM/YY, HH:MM:SS] Sender: Message
"""

import re
from datetime import datetime


def parse_whatsapp_chat(chat_text: str):
    """
    Extracts order-related messages from a WhatsApp chat export.
    Looks for amounts, order keywords, and message frequency over time.
    """
    lines = chat_text.split("\n")

    message_pattern = re.compile(
        r'\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*-?\s*([^:]+):\s*(.+)'
    )

    order_keywords = ["order", "mal", "maal", "bill", "rupees", "rs", "rs.", "payment", "paid", "received"]

    orders = []
    all_dates = []

    for line in lines:
        match = message_pattern.match(line.strip())
        if not match:
            continue

        date_str, time_str, sender, message = match.groups()
        message_lower = message.lower()

        all_dates.append(date_str)

        # check if message mentions an order/amount
        has_keyword = any(kw in message_lower for kw in order_keywords)
        amounts = re.findall(r'\b\d{3,7}\b', message)

        if has_keyword and amounts:
            orders.append({
                "date": date_str,
                "time": time_str,
                "sender": sender.strip(),
                "message": message.strip(),
                "amount": amounts[0]
            })

    total_orders = len(orders)
    total_messages_with_dates = len(all_dates)
    unique_dates = len(set(all_dates))

    amounts_found = [int(o["amount"]) for o in orders if o["amount"].isdigit()]
    total_value = sum(amounts_found)
    avg_order_value = total_value / len(amounts_found) if amounts_found else 0

    return {
        "total_orders_detected": total_orders,
        "active_days": unique_dates,
        "total_order_value": total_value,
        "average_order_value": round(avg_order_value, 2),
        "orders": orders[:20],  # cap preview to first 20
        "summary": (
            f"{total_orders} order-related messages found across {unique_dates} active days. "
            f"Estimated total order value: Rs. {total_value:,}"
        )
    }


def whatsapp_to_wallet_score_boost(parsed_data: dict) -> int:
    """
    Converts WhatsApp order activity into a bonus score (0-10)
    that can be added to the wallet/activity component.
    """
    orders = parsed_data.get("total_orders_detected", 0)
    if orders >= 15:
        return 10
    elif orders >= 8:
        return 7
    elif orders >= 3:
        return 4
    elif orders >= 1:
        return 2
    return 0