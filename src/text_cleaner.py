import re

def clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    # Remove page numbers
    text = re.sub(r'\n\d+\n', '\n', text)
    # Fix broken hyphenated words
    text = re.sub(r'-\n', '', text)
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
