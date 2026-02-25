import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# --- Initialize Pinecone client ---
pc = Pinecone(api_key=PINECONE_API_KEY)

# --- Define index name ---
INDEX_NAME = "legal-index"

# --- Create index if it doesn't exist ---
if INDEX_NAME not in [index.name for index in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,  # for all-MiniLM-L6-v2 embeddings
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print(f"✅ Index '{INDEX_NAME}' created successfully.")
else:
    print(f"ℹ️ Index '{INDEX_NAME}' already exists.")

# --- Connect to the index ---
index = pc.Index(INDEX_NAME)

# --- Load embedding model ---
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Prepare legal data ---
legal_texts = [
    {"id": "1", "text": "Murder is defined as the unlawful killing of a human being with intent."},
    {"id": "2", "text": "IPC stands for Indian Penal Code, which is the main criminal code of India."},
    {"id": "3", "text": "Section 300 of IPC defines murder and its exceptions."},
    {"id": "4", "text": "Section 302 of IPC provides punishment for murder, which may be death or life imprisonment."},
    {"id": "5", "text": "The Constitution of India is the supreme law of the country."},
]

# --- Convert text into embeddings ---
vectors = []
for item in legal_texts:
    embedding = model.encode(item["text"]).tolist()
    vectors.append({
        "id": item["id"],
        "values": embedding,
        "metadata": {"text": item["text"]}
    })

# --- Upload data to Pinecone ---
index.upsert(vectors=vectors)
print(f"✅ Successfully uploaded {len(vectors)} legal documents to the index '{INDEX_NAME}'.")
