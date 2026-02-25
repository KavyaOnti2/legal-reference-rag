from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_into_chunks(text: str, chunk_size=1000, overlap=100):
    """Split cleaned text into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap
    )
    return splitter.split_text(text)
