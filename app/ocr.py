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

        # Total Amount — last number greater than 100
        all_numbers = re.findall(r'\b\d+(?:\.\d{1,2})?\b', full_text)
        amounts = [n for n in all_numbers if int(float(n)) > 100]
        total_amount = amounts[-1] if amounts else all_numbers[-1] if all_numbers else None

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
            "items": items,
            "raw_lines": lines
        }

    except Exception as e:
        return {"error": f"OCR failed: {str(e)}"}