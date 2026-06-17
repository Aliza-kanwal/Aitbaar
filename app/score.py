from datetime import datetime

def calculate_trust_score(invoices: list, whatsapp_boost: int = 0) -> dict:
    if not invoices:
        return {"total_score": 0, "breakdown": {}}

    total = len(invoices)

    # 1. FREQUENCY SCORE (30%)
    if total >= 10:
        frequency_score = 30
    elif total >= 7:
        frequency_score = 25
    elif total >= 5:
        frequency_score = 20
    elif total >= 3:
        frequency_score = 15
    elif total >= 2:
        frequency_score = 10
    else:
        frequency_score = 5

    # 2. CONSISTENCY SCORE (25%)
    dates = []
    for inv in invoices:
        raw = inv.get("date")
        if raw:
            dates.append(raw)

    if len(dates) >= 8:
        consistency_score = 25
    elif len(dates) >= 5:
        consistency_score = 20
    elif len(dates) >= 3:
        consistency_score = 15
    elif len(dates) >= 1:
        consistency_score = 10
    else:
        consistency_score = 5

    # 3. GROWTH SCORE (25%)
    amounts = []
    for inv in invoices:
        try:
            amt = float(inv.get("total_amount", 0))
            if amt > 0:
                amounts.append(amt)
        except:
            pass

    if len(amounts) >= 2:
        half = len(amounts) // 2
        first_half = sum(amounts[:half]) / half
        second_half = sum(amounts[half:]) / (len(amounts) - half)
        growth = ((second_half - first_half) / first_half) * 100 if first_half > 0 else 0

        if growth >= 20:
            growth_score = 25
        elif growth >= 10:
            growth_score = 20
        elif growth >= 0:
            growth_score = 15
        else:
            growth_score = 8
    elif len(amounts) == 1:
        growth_score = 10
    else:
        growth_score = 5

    # 4. WALLET SCORE (20%) — mock wallet activity + WhatsApp order boost
    wallet = invoices[-1].get("wallet_data", {})
    txn_count = wallet.get("total_transactions", 0)

    if txn_count >= 20:
        wallet_score = 20
    elif txn_count >= 10:
        wallet_score = 15
    elif txn_count >= 5:
        wallet_score = 10
    else:
        wallet_score = 5

    # Add WhatsApp order-history boost (capped so wallet_score never exceeds 20)
    wallet_score = min(wallet_score + whatsapp_boost, 20)

    total_score = frequency_score + consistency_score + growth_score + wallet_score

    return {
        "total_score": min(total_score, 100),
        "breakdown": {
            "frequency": {"score": frequency_score, "max": 30, "label": "Purchase Frequency"},
            "consistency": {"score": consistency_score, "max": 25, "label": "Payment Consistency"},
            "growth": {"score": growth_score, "max": 25, "label": "Business Growth"},
            "wallet": {"score": wallet_score, "max": 20, "label": "Digital Wallet Activity"},
        },
        "total_invoices": total,
        "grade": "A" if total_score >= 80 else "B" if total_score >= 65 else "C" if total_score >= 50 else "D"
    }