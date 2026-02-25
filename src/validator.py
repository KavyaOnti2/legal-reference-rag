import random

def validate_chunks(chunks):
    """Print random chunk samples for validation."""
    print(f"✅ Total chunks: {len(chunks)}")
    if not chunks:
        return
    print("\n🔹 Random sample preview:")
    for chunk in random.sample(chunks, min(3, len(chunks))):
        print("-----")
        print(chunk[:300])  # preview first 300 chars
