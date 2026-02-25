🧠 AI-Based Legal Reference and Case Retrieval System

An intelligent Retrieval-Augmented Generation (RAG) based legal assistant that enables lawyers, students, and the public to retrieve precise legal provisions and case references using natural language queries.

The system ingests legal documents, builds a vector search index, and generates citation-backed answers through an LLM-powered conversational interface.

🚀 Key Features

🔍 Natural language legal query processing

📚 Citation-backed legal answers

🧠 RAG-based architecture

💬 Conversational memory support

⚡ Pinecone vector similarity search

🖥️ Interactive Chainlit UI

📄 Automated PDF ingestion pipeline

🏗️ System Architecture
User Query → Chainlit UI → Vector Search (Pinecone)
          → Retrieved Chunks → LLM (ChatOpenAI)
          → Citation-backed Answer → User
🧩 Tech Stack

Languages & Core

Python

LangChain

HuggingFace Transformers

AI / ML

Sentence Transformers (all-MiniLM-L6-v2)

Retrieval-Augmented Generation (RAG)

ChatOpenAI

Vector Database

Pinecone

Frontend

Chainlit

Document Processing

PyMuPDF

Memory

SQLChatMessageHistory

⚙️ Installation
git clone https://github.com/KavyaOnti2/legal-reference-rag.git
cd legal-reference-rag

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt
🔑 Environment Variables

Create a .env file:

OPENAI_API_KEY=your_key
PINECONE_API_KEY=your_key
PINECONE_ENV=your_env
▶️ Run the Application
chainlit run src/app_chainlit.py

Then open the local URL shown in terminal.

🧪 Example Queries

What are the ingredients of murder under IPC Section 300?

Which IPC sections apply to theft?

Explain mens rea in criminal law.

📁 Note on Dataset

Due to GitHub size limits, raw legal documents are not included in this repository.
You can add your own legal PDFs to the data/raw/ directory and run the ingestion pipeline.

🔮 Future Improvements

Streamlit/Web UI

Multi-language legal queries

Hybrid search (BM25 + Vector)

Judgment summarization

Production deployment

👩‍💻 Author

Kavya Onti
B.E. Computer Science | AI & ML Enthusiast
GitHub: https://github.com/KavyaOnti2
