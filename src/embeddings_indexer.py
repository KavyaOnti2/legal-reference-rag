import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
INDEX_NAME = os.getenv("INDEX_NAME")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# Load embedding model
print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Define folder where chunked JSONs are stored
chunks_dir = os.path.join("..", "data", "chunks")


# Collect all JSON files
files = [f for f in os.listdir(chunks_dir) if f.endswith(".json")]

for file in files:
    filepath = os.path.join(chunks_dir, file)
    with open(filepath, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"\nProcessing {file} with {len(chunks)} chunks...")

    vectors = []
    for i, chunk in enumerate(tqdm(chunks)):
        text = chunk["text"]
        embedding = model.encode(text).tolist()
        vector_id = f"{file}_{i}"
        metadata = {"source": file, "chunk_id": i, "text": text}
        vectors.append({"id": vector_id, "values": embedding, "metadata": metadata})

        # Upload in batches of 100
        if len(vectors) >= 100:
            index.upsert(vectors=vectors)
            vectors = []

    # Upload any remaining vectors
    if vectors:
        index.upsert(vectors=vectors)

    print(f"✅ Finished indexing {file}")

print("\n🎉 All documents successfully embedded and uploaded to Pinecone!")
