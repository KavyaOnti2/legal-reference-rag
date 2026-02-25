# src/rag.py
import os
import logging
from typing import List, Dict, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

# Pinecone v7.x
import pinecone

# Optional: OpenAI for final answer generation (if you want)
import openai

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# === Config (read from env) ===
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")  # pinecone environment (e.g. "us-west1-gcp")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "legal-index")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === Init model & clients ===
# Sentence transformer used for embeddings
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

try:
    model = SentenceTransformer(EMBED_MODEL_NAME)
except Exception as e:
    log.exception("Failed to load SentenceTransformer model: %s", e)
    raise

# init pinecone
if not PINECONE_API_KEY or not PINECONE_ENV:
    log.warning("Pinecone API key or env not set. Pinecone operations will fail if used.")
else:
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

# helper to get index handle
def get_index():
    if PINECONE_INDEX not in pinecone.list_indexes():
        raise ValueError(f"Pinecone index '{PINECONE_INDEX}' not found. Available: {pinecone.list_indexes()}")
    idx = pinecone.Index(PINECONE_INDEX)
    return idx

# optional openai init
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


# === Retrieval ===
def embed_text(text: str) -> List[float]:
    """Return embedding vector for text."""
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def retrieve(query: str, top_k: int = 5) -> List[Dict]:
    """
    Query Pinecone index and return top_k matches.
    Returns list of dicts with keys: id, score, metadata (should contain 'text' or similar).
    """
    if not PINECONE_API_KEY or not PINECONE_ENV:
        raise RuntimeError("Pinecone credentials missing in environment variables.")

    idx = get_index()
    qvec = embed_text(query)
    # query Pinecone index using the Index.query API (v7)
    res = idx.query(vector=qvec, top_k=top_k, include_metadata=True, include_values=False)
    matches = []
    # The structure: res.matches is a list of Match objects with id, score, metadata
    for m in res.get("matches", []):
        matches.append({
            "id": m.get("id"),
            "score": m.get("score"),
            "metadata": m.get("metadata", {}),
        })
    return matches


# === Simple aggregator ===
def build_context_from_matches(matches: List[Dict], max_chars: int = 1500) -> str:
    """
    Combine metadata text fields from matches into a single context for LM generation.
    Assumes each match.metadata contains a 'text' field (or 'chunk').
    """
    parts = []
    for m in matches:
        meta = m.get("metadata", {})
        text = meta.get("text") or meta.get("chunk") or meta.get("content") or ""
        if text:
            parts.append(text.strip())
    # join and trim
    combined = "\n\n---\n\n".join(parts)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "..."
    return combined


# === Optional OpenAI generation ===
def generate_answer_with_openai(query: str, context: str, model_name: str = "gpt-4o-mini") -> str:
    """
    Generate a concise answer using OpenAI given query + retrieved context.
    You can replace the model_name with one you have access to (gpt-4o-mini may not be available).
    """
    if not OPENAI_API_KEY:
        log.warning("OPENAI_API_KEY not set - returning context instead of generated answer.")
        return f"Context:\n{context}"

    # Compose prompt
    prompt = (
        "You are a legal assistant. Use the context snippets below (from trusted legal documents) "
        "to answer the user's question accurately and concisely. If context doesn't contain an answer, say 'No relevant information found'.\n\n"
        f"Context snippets:\n{context}\n\nUser question: {query}\n\nAnswer:"
    )
    try:
        resp = openai.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "system", "content": "You are a helpful legal assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.0,
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.exception("OpenAI generation failed: %s", e)
        # Fallback: return context
        return f"(Generation failed) Context:\n{context}"


# === Main API function ===
def answer_question(query: str, top_k: int = 5, use_openai: bool = True) -> str:
    """
    Returns an answer string for the query.
    - retrieves top_k chunks from Pinecone
    - builds context
    - optionally calls OpenAI to synthesize answer
    """
    if not query or not query.strip():
        return "Please ask a valid question."

    # 1) retrieve
    try:
        matches = retrieve(query, top_k=top_k)
    except Exception as e:
        log.exception("Retrieval failed: %s", e)
        return f"Retrieval error: {e}"

    if not matches:
        return "No relevant information found in the database."

    # 2) build context
    context = build_context_from_matches(matches)

    # 3) return either the context or an LLM answer
    if use_openai:
        # NOTE: many accounts do not have access to all models. If the model_name fails, change it to one you have.
        # e.g. "gpt-4o-mini" might not be available; try "gpt-4o" or "gpt-4o-mini-2024-12" or a different model,
        # or set use_openai=False to just return retrieved text.
        try:
            answer = generate_answer_with_openai(query, context)
        except Exception as e:
            log.exception("OpenAI call failed: %s", e)
            answer = f"Could not generate a synthesized answer. Showing retrieved context:\n\n{context}"
    else:
        answer = f"Retrieved context:\n\n{context}"

    # optionally include source ids/score summary
    src_info = "\n\nSources:\n" + "\n".join([f"- id:{m['id']} (score:{m['score']})" for m in matches])
    return answer + src_info
