import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
import re
import os

def clean_text(text):
    """Strip extra whitespace and normalize encoding issues."""
    text = text.encode("utf-8", "ignore").decode("utf-8")
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()

os.makedirs("raw_text", exist_ok=True)

# --- 1. Benefits PDF ---
benefits_text = ""
with pdfplumber.open("benefits.pdf") as pdf:
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            benefits_text += page_text + "\n"

benefits_text = clean_text(benefits_text)
with open("raw_text/benefits.txt", "w", encoding="utf-8") as f:
    f.write(benefits_text)
print("✅ raw_text/benefits.txt saved")

# --- 2. Claims process Word doc ---
claims_text = ""
doc = Document("claims_process.docx")
for paragraph in doc.paragraphs:
    claims_text += paragraph.text + "\n"

claims_text = clean_text(claims_text)
with open("raw_text/claims_process.txt", "w", encoding="utf-8") as f:
    f.write(claims_text)
print("✅ raw_text/claims_process.txt saved")

# --- 3. Enrollment form OCR ---
enrollment_image = Image.open("enrollment_form.png")
enrollment_text = pytesseract.image_to_string(enrollment_image)

enrollment_text = clean_text(enrollment_text)
with open("raw_text/enrollment.txt", "w", encoding="utf-8") as f:
    f.write(enrollment_text)
print("✅ raw_text/enrollment.txt saved")

print("\nAll 3 files cleaned and saved to raw_text/")