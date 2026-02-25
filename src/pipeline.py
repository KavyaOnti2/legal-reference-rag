import os, json
from pdf_loader import extract_text_from_pdf
from text_cleaner import clean_text
from chunker import split_into_chunks
from validator import validate_chunks

RAW_DIR = "../data/raw/"
PROCESSED_DIR = "../data/processed/"
CHUNKS_DIR = "../data/chunks/"
MANIFEST = "../data/manifest.json"

def process_document(file_name, title, doc_type, source):
    pdf_path = os.path.join(RAW_DIR, file_name)

    # Step 1: Extract text
    raw_text = extract_text_from_pdf(pdf_path)

    # Step 2: Clean
    cleaned_text = clean_text(raw_text)

    # Step 3: Save cleaned text
    processed_path = os.path.join(PROCESSED_DIR, file_name.replace(".pdf", ".txt"))
    with open(processed_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

    # Step 4: Split into chunks
    chunks = split_into_chunks(cleaned_text)

    # Step 5: Save chunks
    chunk_path = os.path.join(CHUNKS_DIR, file_name.replace(".pdf", ".json"))
    with open(chunk_path, "w", encoding="utf-8") as f:
        json.dump([{"chunk_id": i+1, "text": c} for i, c in enumerate(chunks)], f, indent=2)

    # Step 6: Validate
    validate_chunks(chunks)

    # Step 7: Update manifest
    update_manifest({
        "filename": file_name,
        "title": title,
        "type": doc_type,
        "source": source
    })

def update_manifest(entry):
    if not os.path.exists(MANIFEST):
        data = []
    else:
        with open(MANIFEST, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append(entry)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    # Automatically process all PDFs in raw folder
    for file in os.listdir(RAW_DIR):
        if file.endswith(".pdf"):
            print(f"\n🔹 Processing {file}...")
            process_document(
                file_name=file,
                title=file.replace(".pdf", "").upper(),
                doc_type="Statute",
                source="local"
            )