"""
Demo Data Seeder for Aitbaar
Creates 3 realistic fake shopkeepers with invoice history + mock wallet data.
Run this once: python seed_data.py
"""

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import random

load_dotenv(dotenv_path="app/.env")

cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS"))
firebase_admin.initialize_app(cred)
db = firestore.client()


def mock_wallet_data(level: str):
    """level: 'low', 'medium', 'high' — simulates Easypaisa/JazzCash activity"""
    if level == "high":
        return {
            "provider": "JazzCash",
            "total_transactions": random.randint(22, 35),
            "monthly_inflow": random.randint(80000, 150000),
            "active_months": 8
        }
    elif level == "medium":
        return {
            "provider": "Easypaisa",
            "total_transactions": random.randint(10, 18),
            "monthly_inflow": random.randint(35000, 70000),
            "active_months": 5
        }
    else:
        return {
            "provider": "NayaPay",
            "total_transactions": random.randint(2, 6),
            "monthly_inflow": random.randint(8000, 20000),
            "active_months": 2
        }


def generate_invoices(shop_id, distributor, count, base_amount, growth_pattern, wallet_level):
    """Generate `count` fake invoices with realistic growth pattern"""
    invoices = []
    start_date = datetime(2026, 1, 5)

    for i in range(count):
        amount = base_amount + (growth_pattern * i) + random.randint(-500, 800)
        invoice_date = start_date + timedelta(days=i * 12)

        invoice = {
            "invoice_no": f"INV-{1000 + i}",
            "date": invoice_date.strftime("%d %B %Y"),
            "total_amount": str(max(amount, 1000)),
            "items": [
                {"qty": str(random.randint(5, 25)), "description": "Assorted Grocery Items",
                 "unit_price": str(random.randint(20, 60)), "total": str(max(amount, 1000))}
            ],
            "raw_lines": [f"Invoice from {distributor}"],
            "filename": f"demo_invoice_{shop_id}_{i+1}.jpg",
            "shop_id": shop_id,
            "uploaded_at": invoice_date.isoformat(),
            "distributor": distributor,
            "wallet_data": mock_wallet_data(wallet_level)
        }
        invoices.append(invoice)
    return invoices


def calculate_and_save_score(shop_id, invoice_list):
    """Same scoring logic as app/score.py — duplicated here so script is standalone"""
    total = len(invoice_list)

    if total >= 10: frequency_score = 30
    elif total >= 7: frequency_score = 25
    elif total >= 5: frequency_score = 20
    elif total >= 3: frequency_score = 15
    elif total >= 2: frequency_score = 10
    else: frequency_score = 5

    dates = [inv.get("date") for inv in invoice_list if inv.get("date")]
    if len(dates) >= 8: consistency_score = 25
    elif len(dates) >= 5: consistency_score = 20
    elif len(dates) >= 3: consistency_score = 15
    elif len(dates) >= 1: consistency_score = 10
    else: consistency_score = 5

    amounts = [float(inv.get("total_amount", 0)) for inv in invoice_list if inv.get("total_amount")]
    if len(amounts) >= 2:
        half = len(amounts) // 2
        first_half = sum(amounts[:half]) / half
        second_half = sum(amounts[half:]) / (len(amounts) - half)
        growth = ((second_half - first_half) / first_half) * 100 if first_half > 0 else 0
        if growth >= 20: growth_score = 25
        elif growth >= 10: growth_score = 20
        elif growth >= 0: growth_score = 15
        else: growth_score = 8
    else:
        growth_score = 10

    wallet = invoice_list[-1].get("wallet_data", {})
    txn_count = wallet.get("total_transactions", 0)
    if txn_count >= 20: wallet_score = 20
    elif txn_count >= 10: wallet_score = 15
    elif txn_count >= 5: wallet_score = 10
    else: wallet_score = 5

    total_score = min(frequency_score + consistency_score + growth_score + wallet_score, 100)
    grade = "A" if total_score >= 80 else "B" if total_score >= 65 else "C" if total_score >= 50 else "D"

    score_data = {
        "total_score": total_score,
        "breakdown": {
            "frequency": {"score": frequency_score, "max": 30, "label": "Purchase Frequency"},
            "consistency": {"score": consistency_score, "max": 25, "label": "Payment Consistency"},
            "growth": {"score": growth_score, "max": 25, "label": "Business Growth"},
            "wallet": {"score": wallet_score, "max": 20, "label": "Digital Wallet Activity"},
        },
        "total_invoices": total,
        "grade": grade,
        "shop_id": shop_id,
        "updated_at": datetime.now().isoformat()
    }
    db.collection("scores").document(shop_id).set(score_data)
    return score_data


def seed_shop(shop_id, shop_name, distributor, count, base_amount, growth, wallet_level):
    print(f"\n🏪 Creating {shop_name} ({shop_id})...")

    invoices = generate_invoices(shop_id, distributor, count, base_amount, growth, wallet_level)

    for inv in invoices:
        db.collection("invoices").add(inv)

    score = calculate_and_save_score(shop_id, invoices)
    print(f"   ✅ {count} invoices added | Score: {score['total_score']}/100 | Grade: {score['grade']}")
    return score


if __name__ == "__main__":
    print("🚀 Seeding Aitbaar demo data...\n")

    # Shop 1: Strong performer — Karachi kiryana store, consistent growth, active wallet
    seed_shop(
        shop_id="shop_002",
        shop_name="Al-Madina General Store (Karachi)",
        distributor="Unilever Pakistan",
        count=12,
        base_amount=15000,
        growth=1200,
        wallet_level="high"
    )

    # Shop 2: Medium performer — Lahore, moderate consistency
    seed_shop(
        shop_id="shop_003",
        shop_name="Hassan Kiryana Store (Lahore)",
        distributor="Nestlé Pakistan",
        count=6,
        base_amount=9000,
        growth=400,
        wallet_level="medium"
    )

    # Shop 3: New/weak performer — fewer invoices, low wallet activity
    seed_shop(
        shop_id="shop_004",
        shop_name="Bilal Store (Faisalabad)",
        distributor="Local Distributor",
        count=2,
        base_amount=6000,
        growth=100,
        wallet_level="low"
    )

    print("\n✅ Done! 3 demo shops created: shop_002, shop_003, shop_004")
    print("👉 Test via: http://127.0.0.1:8000/bank/all-shops")