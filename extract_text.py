from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import pdfplumber
from docx import Document

# --- Extract from benefits.pdf using pdfplumber ---
print("=== EXTRACTING FROM benefits.pdf ===")
benefits_text = ""
with pdfplumber.open("benefits.pdf") as pdf:
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            benefits_text += page_text + "\n"

print(benefits_text)

# --- Extract from claims_process.docx using python-docx ---
print("\n=== EXTRACTING FROM claims_process.docx ===")
claims_text = ""
doc = Document("claims_process.docx")
for paragraph in doc.paragraphs:
    claims_text += paragraph.text + "\n"

print(claims_text)
# --- OCR on scanned enrollment form ---
print("\n=== EXTRACTING FROM enrollment_form.png (OCR) ===")

# Since this is already a PNG image (not a PDF), open it directly with PIL
enrollment_image = Image.open("enrollment_form.png")
enrollment_text = pytesseract.image_to_string(enrollment_image)

print(enrollment_text)