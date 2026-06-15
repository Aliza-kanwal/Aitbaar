from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.ocr import extract_invoice_data
from app.score import calculate_trust_score
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import shutil, os, uuid
from datetime import datetime

load_dotenv()

# Firebase init
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS"))
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI(title="Aitbaar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Aitbaar API chal rahi hai ✅"}

# ─── Invoice Upload ───────────────────────────────────────────
@app.post("/upload-invoice")
async def upload_invoice(
    file: UploadFile = File(...),
    shop_id: str = "shop_001"
):
    # Save temp file
    temp_path = f"temp_{uuid.uuid4()}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract data
    invoice_data = extract_invoice_data(temp_path)
    os.remove(temp_path)

    if "error" in invoice_data:
        return invoice_data

    # Save to Firebase
    invoice_data["shop_id"] = shop_id
    invoice_data["uploaded_at"] = datetime.now().isoformat()
    db.collection("invoices").add(invoice_data)

    # Recalculate score
    invoices = db.collection("invoices")\
                 .where("shop_id", "==", shop_id)\
                 .stream()
    invoice_list = [doc.to_dict() for doc in invoices]
    score_data = calculate_trust_score(invoice_list)

    # Save score
    db.collection("scores").document(shop_id).set({
        **score_data,
        "shop_id": shop_id,
        "updated_at": datetime.now().isoformat()
    })

    return {
        "invoice": invoice_data,
        "trust_score": score_data
    }

# ─── Get Score ────────────────────────────────────────────────
@app.get("/score/{shop_id}")
def get_score(shop_id: str):
    doc = db.collection("scores").document(shop_id).get()
    if doc.exists:
        return doc.to_dict()
    return {"error": "Score nahi mila — pehle invoice upload karo"}

# ─── Loan Recommendation ──────────────────────────────────────
@app.get("/loan/{shop_id}")
def get_loan(shop_id: str):
    doc = db.collection("scores").document(shop_id).get()
    if not doc.exists:
        return {"error": "Score nahi mila"}

    score_data = doc.to_dict()
    score = score_data.get("total_score", 0)

    if score >= 75:
        status = "Approved ✅"
        amount = 50000
        message = "Mubarak! Aap Rs. 50,000 tak ka loan le sakte hain"
    elif score >= 55:
        status = "Conditional ⚠️"
        amount = 25000
        message = "Aap Rs. 25,000 tak ka loan le sakte hain"
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

# ─── Bank Dashboard ───────────────────────────────────────────
@app.get("/bank/all-shops")
def all_shops():
    docs = db.collection("scores").stream()
    shops = []
    for doc in docs:
        data = doc.to_dict()
        score = data.get("total_score", 0)
        shops.append({
            "shop_id": data.get("shop_id"),
            "trust_score": score,
            "loan_eligible": score >= 55,
            "updated_at": data.get("updated_at")
        })
    shops.sort(key=lambda x: x["trust_score"], reverse=True)
    return {"shops": shops, "total": len(shops)}