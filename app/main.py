from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.ocr import extract_invoice_data
from app.score import calculate_trust_score
from app.whatsapp_parser import parse_whatsapp_chat, whatsapp_to_wallet_score_boost
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import shutil, os, uuid
from datetime import datetime
from typing import Optional

load_dotenv()

# Firebase init
import json
firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
if firebase_creds:
    cred_dict = json.loads(firebase_creds)
    cred = credentials.Certificate(cred_dict)
else:
    raise ValueError("FIREBASE_CREDENTIALS environment variable not set")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI(title="Aitbaar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Simple Auth Token (hackathon-level security) ─────────────
API_TOKEN = os.getenv("API_TOKEN", "aitbaar-secret-2026")

def verify_token(x_api_token: Optional[str] = Header(None)):
    """Bank-only endpoints require this header: x-api-token: aitbaar-secret-2026"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized — invalid or missing x-api-token header")
    return True


@app.get("/")
def root():
    return {"message": "Aitbaar API chal rahi hai ✅"}


def process_single_invoice(file_path: str, original_filename: str, shop_id: str):
    invoice_data = extract_invoice_data(file_path)
    if "error" in invoice_data:
        invoice_data["filename"] = original_filename
        return invoice_data

    # Auto-assign sequential invoice number per shop (1, 2, 3...)
    existing = db.collection("invoices").where("shop_id", "==", shop_id).stream()
    existing_count = sum(1 for _ in existing)
    invoice_data["ocr_invoice_no"] = invoice_data.get("invoice_no")  # keep raw OCR value
    invoice_data["invoice_no"] = str(existing_count + 1)

    invoice_data["filename"] = original_filename
    invoice_data["shop_id"] = shop_id
    invoice_data["uploaded_at"] = datetime.now().isoformat()
    db.collection("invoices").add(invoice_data)
    return invoice_data


def recalculate_score(shop_id: str):
    invoices = db.collection("invoices").where("shop_id", "==", shop_id).stream()
    invoice_list = [doc.to_dict() for doc in invoices]

    # Pull WhatsApp score boost (if any WhatsApp data was uploaded for this shop)
    whatsapp_boost = 0
    wa_doc = db.collection("whatsapp_data").document(shop_id).get()
    if wa_doc.exists:
        whatsapp_boost = wa_doc.to_dict().get("score_boost", 0)

    score_data = calculate_trust_score(invoice_list, whatsapp_boost)

    db.collection("scores").document(shop_id).set({
        **score_data,
        "shop_id": shop_id,
        "updated_at": datetime.now().isoformat()
    })
    return score_data


# ─── Single Invoice Upload ─────────────────────────────────────
@app.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...), shop_id: str = "shop_001"):
    temp_path = f"temp_{uuid.uuid4()}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    invoice_data = process_single_invoice(temp_path, file.filename, shop_id)
    os.remove(temp_path)

    if "error" in invoice_data:
        return invoice_data

    score_data = recalculate_score(shop_id)
    return {"invoice": invoice_data, "trust_score": score_data}


# ─── WhatsApp Order History Upload (NEW — bonus feature) ───────
@app.post("/upload-whatsapp")
async def upload_whatsapp(file: UploadFile = File(...), shop_id: str = "shop_001"):
    """Upload a WhatsApp chat export (.txt) to extract order history and boost wallet score"""
    content = await file.read()
    chat_text = content.decode("utf-8", errors="ignore")

    parsed = parse_whatsapp_chat(chat_text)
    boost = whatsapp_to_wallet_score_boost(parsed)

    db.collection("whatsapp_data").document(shop_id).set({
        **parsed,
        "shop_id": shop_id,
        "score_boost": boost,
        "uploaded_at": datetime.now().isoformat()
    })

    # Recalculate score immediately so the boost takes effect right away
    score_data = recalculate_score(shop_id)

    return {"parsed_data": parsed, "wallet_score_boost": boost, "trust_score": score_data}


# ─── Get Score ────────────────────────────────────────────────
@app.get("/score/{shop_id}")
def get_score(shop_id: str):
    doc = db.collection("scores").document(shop_id).get()
    if doc.exists:
        return doc.to_dict()
    return {"error": "Score nahi mila — pehle invoice upload karo"}


# ─── Get All Invoices for a Shop (NEW) ─────────────────────────
@app.get("/invoices/{shop_id}")
def get_invoices(shop_id: str):
    docs = db.collection("invoices").where("shop_id", "==", shop_id).stream()
    invoices = []
    for doc in docs:
        data = doc.to_dict()
        invoices.append({
            "invoice_no": data.get("invoice_no"),
            "date": data.get("date"),
            "total_amount": data.get("total_amount"),
            "distributor": data.get("distributor"),
            "filename": data.get("filename"),
            "uploaded_at": data.get("uploaded_at"),
            "items": data.get("items", [])
        })
    invoices.sort(key=lambda x: x.get("uploaded_at") or "", reverse=True)
    return {"shop_id": shop_id, "total": len(invoices), "invoices": invoices}


# ─── Loan Recommendation (70+ = auto approve) ──────────────────
@app.get("/loan/{shop_id}")
def get_loan(shop_id: str):
    doc = db.collection("scores").document(shop_id).get()
    if not doc.exists:
        return {"error": "Score nahi mila"}

    score_data = doc.to_dict()
    score = score_data.get("total_score", 0)

    if score >= 70:
        status = "Approved ✅ (Auto-Approved)"
        amount = 50000
        message = "Mubarak! Aap Rs. 50,000 tak ka loan auto-approve ho gaya hai"
    elif score >= 55:
        status = "Conditional ⚠️"
        amount = 25000
        message = "Aap Rs. 25,000 tak ka loan le sakte hain — manual review zaroori"
    else:
        status = "Rejected ❌"
        amount = 0
        message = "Score improve karo — zyada invoices upload karo"

    return {
        "shop_id": shop_id,
        "trust_score": score,
        "loan_status": status,
        "loan_amount": amount,
        "message": message
    }


# ─── Bank Dashboard (protected with token) ─────────────────────
@app.get("/bank/all-shops")
def all_shops(x_api_token: Optional[str] = Header(None)):
    verify_token(x_api_token)
    docs = db.collection("scores").stream()
    shops = []
    for doc in docs:
        data = doc.to_dict()
        score = data.get("total_score", 0)
        shops.append({
            "shop_id": data.get("shop_id"),
            "trust_score": score,
            "loan_eligible": score >= 70,
            "updated_at": data.get("updated_at")
        })
    shops.sort(key=lambda x: x["trust_score"], reverse=True)
    return {"shops": shops, "total": len(shops)}


# ─── Demo Reset (1-click wipe) ──────────────────────────────────
@app.post("/demo/reset")
def reset_demo_data(x_api_token: Optional[str] = Header(None)):
    """Deletes all invoices, scores, and whatsapp_data. Protected with token."""
    verify_token(x_api_token)

    collections = ["invoices", "scores", "whatsapp_data"]
    deleted_counts = {}

    for col_name in collections:
        docs = db.collection(col_name).stream()
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        deleted_counts[col_name] = count

    return {
        "message": "Demo data reset complete ✅",
        "deleted": deleted_counts
    }