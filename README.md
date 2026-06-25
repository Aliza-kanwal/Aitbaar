# اعتبار — Aitbaar
### AI-Powered Kiryana Credit Scoring Engine
**UBL Hackathon Pakistan 2026 | Team Saudagar**

---

## The Problem

Pakistan has **3.5 million kiryana stores** whose owners maintain financial records on paper registers and WhatsApp messages. When they apply for bank loans, they get rejected — not because their businesses aren't viable, but because their informal data isn't in a bank-readable format.

## Our Solution

Aitbaar converts a shopkeeper's informal daily records into a structured **Trust Score (0–100)** that banks can use to make real-time loan decisions.

---

## How It Works

```
Invoice Photo → OCR Extraction → Trust Score → Loan Recommendation
WhatsApp Chat → Order Parser  ↗
Wallet Data   → Activity Score ↗
```

1. **Shopkeeper uploads** a wholesale invoice photo or WhatsApp chat export
2. **AI extracts** transaction data (amount, date, distributor) using OCR
3. **Scoring engine** calculates a Trust Score based on 4 factors
4. **UBL Bank dashboard** shows all merchants ranked by score and loan eligibility

---

## Trust Score Formula

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Purchase Frequency | 30% | How many invoices uploaded |
| Payment Consistency | 25% | Date regularity across invoices |
| Business Growth | 25% | Amount trend over time |
| Digital Wallet Activity | 20% | Easypaisa/JazzCash transaction history |

**Score 70+** → Auto-approved (Rs. 50,000)
**Score 55–69** → Conditional (Rs. 25,000)
**Score <55** → Rejected (more data needed)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| OCR | Tesseract OCR |
| Database | Firebase Firestore |
| Frontend | React + Vite + Tailwind CSS |
| WhatsApp Parser | Custom NLP (Python regex) |
| Auth | Token-based API security |

---

## Project Structure

```
AITBAAR/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI — all endpoints
│       ├── ocr.py               # Tesseract invoice extraction
│       ├── score.py             # Trust Score algorithm
│       ├── whatsapp_parser.py   # WhatsApp chat order extractor
│       └── fraud_detection.py   # Cross-source verification
├── frontend/
│   └── src/
│       ├── App.jsx              # Full React app (4 screens)
│       └── index.css            # Design system
└── seed_data.py                 # Demo data generator
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload-invoice` | Upload invoice image → OCR → score update |
| POST | `/upload-whatsapp` | Upload WhatsApp .txt → parse → score boost |
| GET | `/score/{shop_id}` | Get current Trust Score |
| GET | `/loan/{shop_id}` | Get loan recommendation |
| GET | `/invoices/{shop_id}` | Get all uploaded invoices |
| GET | `/bank/all-shops` | Bank dashboard — all merchants ranked |
| POST | `/demo/reset` | Reset demo data (protected) |

---

## Running Locally

**Backend:**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# API running at http://127.0.0.1:8000
# Docs at http://127.0.0.1:8000/docs
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# App running at http://localhost:5173
```

---

## Team Saudagar

| Member | Role |
|--------|------|
| Aliza | Backend — FastAPI, OCR, Scoring Engine, Firebase |
| Sameen | Frontend — React, UI/UX Design, Pitch |

---

*Aitbaar — because every kiryana store deserves financial trust.*
