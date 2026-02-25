# src/query_tester.py
from rag import answer_question

if __name__ == "__main__":
    print("Local RAG query tester. Type 'exit' to quit.")
    while True:
        q = input("\nQuestion: ").strip()
        if q.lower() in ("exit", "quit"):
            break
        res = answer_question(q, top_k=4)
        if res.get("warning"):
            print("⚠️", res["warning"])
            continue
        print("\n=== Answer ===\n")
        print(res["answer"])
        print("\n=== Provenance (retrieved chunks) ===\n")
        for i, c in enumerate(res["chunks"], 1):
            print(f"[{i}] source: {c['source']}, chunk_id: {c['chunk_id']}, score: {c['score']:.4f}")
            print(c['text'][:600].replace("\n", " ") + ("..." if len(c['text']) > 600 else ""))
            print("-"*60)
