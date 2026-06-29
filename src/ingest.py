import os
import sys
import hashlib
import argparse
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
DOCS_PATH   = os.getenv("DOCS_PATH", "./docs")
COLLECTION  = "ros2_knowledge"
CHUNK_SIZE  = 800
CHUNK_OVERLAP = 100
EMBED_MODEL = "all-MiniLM-L6-v2"

SUPPORTED_EXTENSIONS = {".txt", ".md", ".yaml", ".yml", ".urdf", ".py", ".launch", ".cfg", ".ini", ".toml"}


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start+chunk_size])
        start += chunk_size - overlap
    return chunks

def load_file(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"  [WARN] {e}")
        return ""

def doc_id(filepath, chunk_index):
    h = hashlib.md5(f"{filepath}:{chunk_index}".encode()).hexdigest()[:8]
    return f"{Path(filepath).name}-chunk{chunk_index}-{h}"

def ingest(docs_path=DOCS_PATH):
    print(f"📂 Scanning: {docs_path}")
    docs_dir = Path(docs_path)
    if not docs_dir.exists():
        print(f"[ERROR] Not found: {docs_path}"); sys.exit(1)

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION, embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    files = [f for f in docs_dir.rglob("*") if f.suffix in SUPPORTED_EXTENSIONS and f.is_file()]
    print(f"📄 Found {len(files)} files\n")

    total = 0
    for fpath in files:
        print(f"  ↳ {fpath.relative_to(docs_dir)}")
        text = load_file(fpath)
        if not text.strip():
            print("     [SKIP]"); continue
        chunks = chunk_text(text)
        ids  = [doc_id(str(fpath), i) for i in range(len(chunks))]
        meta = [{"source": str(fpath.relative_to(docs_dir)), "chunk": i} for i in range(len(chunks))]
        for i in range(0, len(chunks), 50):
            collection.upsert(documents=chunks[i:i+50], ids=ids[i:i+50], metadatas=meta[i:i+50])
        total += len(chunks)
        print(f"     ✓ {len(chunks)} chunks")

    print(f"\n✅ Done — {total} chunks in {CHROMA_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", default=DOCS_PATH)
    args = parser.parse_args()
    ingest(args.docs)