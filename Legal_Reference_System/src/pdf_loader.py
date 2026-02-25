import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text
