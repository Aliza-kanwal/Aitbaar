def calculate_trust_score(invoices: list) -> dict:
    if not invoices:
        return {"total_score": 0, "breakdown": {}}

    total = len(invoices)

    # 1. Frequency Score (30%) — kitne invoices hain
    if total >= 10:
        frequency_score = 30
    elif total >= 5:
        frequency_score = 20
    elif total >= 2:
        frequency_score = 10
    else:
        frequency_score = 5

    # 2. Consistency Score (25%) — dates ka variation
    dates = [inv.get("date") for inv in invoices if inv.get("date")]
    consistency_score = 25 if len(dates) >= 3 else 15 if len(dates) >= 1 else 5

    # 3. Amount Growth Score (25%) — total amounts
    amounts = []
    for inv in invoices:
        try:
            amt = float(inv.get("total_amount", 0))
            if amt > 0:
                amounts.append(amt)
        except:
            pass

    if len(amounts) >= 2 and amounts[-1] > amounts[0]:
        growth_score = 25
    elif len(amounts) >= 1:
        growth_score = 15
    else:
        growth_score = 5

    # 4. Wallet Score (20%) — placeholder for now
    wallet_score = 10  # Default jab tak wallet API na ho

    total_score = frequency_score + consistency_score + growth_score + wallet_score

    return {
        "total_score": min(total_score, 100),
        "breakdown": {
            "frequency": frequency_score,
            "consistency": consistency_score,
            "growth": growth_score,
            "wallet": wallet_score
        },
        "total_invoices": total
    }