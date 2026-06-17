import pytesseract
from PIL import Image
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_invoice_data(image_path: str):
    try:
        image = Image.open(image_path)
        full_text = pytesseract.image_to_string(image, lang='eng')
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]

        # Invoice Number
        invoice_no = None
        for line in lines:
            match = re.search(r'invoice\s*no[:\.]?\s*(\w+)', line, re.IGNORECASE)
            if match:
                invoice_no = match.group(1)
                break

        # Date
        date = None
        date_pattern = re.search(
            r'(\d{1,2}[\s\-/](?:january|february|march|april|may|june|july|august|september|october|november|december)[\s\-/]\d{2,4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            full_text, re.IGNORECASE
        )
        if date_pattern:
            date = date_pattern.group(1)

        # Total Amount — smart detection
        # Step 1: handle comma-separated numbers properly (e.g. 56,550 -> 56550)
        comma_number_pattern = r'\b\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?\b'
        plain_number_pattern = r'\b\d+(?:\.\d{1,2})?\b'

        def clean_number(n):
            return n.replace(',', '')

        # Step 2: prioritize lines with "total" keyword (but not "sub-total")
        total_amount = None
        priority_keywords = ['grand total', 'total due', 'amount due', 'total:', 'total ']

        for line in lines:
            line_lower = line.lower()
            if 'sub-total' in line_lower or 'subtotal' in line_lower or 'sub total' in line_lower:
                continue
            if any(kw in line_lower for kw in priority_keywords):
                comma_matches = re.findall(comma_number_pattern, line)
                if comma_matches:
                    total_amount = clean_number(comma_matches[-1])
                    break
                plain_matches = re.findall(plain_number_pattern, line)
                plain_matches = [m for m in plain_matches if int(float(m)) > 50]
                if plain_matches:
                    total_amount = plain_matches[-1]
                    break

        # Step 3: fallback — largest comma-formatted number in whole text
        if not total_amount:
            comma_matches = re.findall(comma_number_pattern, full_text)
            if comma_matches:
                cleaned = [clean_number(m) for m in comma_matches]
                total_amount = str(max(cleaned, key=lambda x: float(x)))

        # Step 4: final fallback — largest plain number over 100
        if not total_amount:
            all_numbers = re.findall(plain_number_pattern, full_text)
            amounts = [n for n in all_numbers if int(float(n)) > 100]
            total_amount = max(amounts, key=lambda x: float(x)) if amounts else (all_numbers[-1] if all_numbers else None)

        # Distributor — check for known brand/company keywords
        known_distributors = [
            "unilever", "nestle", "nestlé", "colgate", "p&g", "procter",
            "national foods", "shan", "engro", "tapal", "lipton",
            "candyland", "mondelez", "haleeb", "olpers"
        ]
        distributor = None
        text_lower = full_text.lower()
        for name in known_distributors:
            if name in text_lower:
                distributor = name.title()
                break
        if not distributor:
            # fallback: look for "To:" or company-style line near top
            for line in lines[:6]:
                if re.search(r'(warehouse|distributors?|trading|enterprises|& co)', line, re.IGNORECASE):
                    distributor = line.strip()
                    break

        # Items list
        items = []
        for line in lines:
            match = re.match(r'(\d+)\s+\w+\s+(.+?)\s+(\d+)\s+(\d+)', line)
            if match:
                items.append({
                    "qty": match.group(1),
                    "description": match.group(2),
                    "unit_price": match.group(3),
                    "total": match.group(4)
                })

        return {
            "invoice_no": invoice_no,
            "date": date,
            "total_amount": total_amount,
            "distributor": distributor,
            "items": items,
            "raw_lines": lines
        }

    except Exception as e:
        return {"error": f"OCR failed: {str(e)}"}