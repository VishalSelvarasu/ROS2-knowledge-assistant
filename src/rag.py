from dotenv import load_dotenv
load_dotenv()

import os, sys
from typing import Optional
import chromadb
from chromadb.utils import embedding_functions
from anthropic import Anthropic

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION  = "ros2_knowledge"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K       = 5
MODEL       = "claude-sonnet-4-6"
MAX_TOKENS  = 1024

SYSTEM_PROMPT = """You are a ROS 2 robotics assistant with access to a knowledge base of
robot configuration files, documentation, launch files, URDF descriptions, and navigation
parameters. Answer using the provided context. Cite source files. Don't hallucinate values."""

client = Anthropic()

def get_collection():
    cc = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    return cc.get_or_create_collection(name=COLLECTION, embedding_function=ef, metadata={"hnsw:space": "cosine"})

def retrieve(question, top_k=TOP_K):
    results = get_collection().query(query_texts=[question], n_results=top_k, include=["documents","metadatas","distances"])
    return [{"text": d, "source": m.get("source","?"), "score": round(1-dist,3)}
            for d, m, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0])]

def query(question, top_k=TOP_K, conversation_history=None):
    chunks = retrieve(question, top_k)
    context = "\n\n---\n\n".join(f"[Source: {c['source']} | score: {c['score']}]\n{c['text']}" for c in chunks)
    messages = (conversation_history or []) + [{"role": "user", "content": f"<context>\n{context}\n</context>\n\nQuestion: {question}"}]
    resp = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM_PROMPT, messages=messages)
    return {"answer": resp.content[0].text, "sources": list({c["source"] for c in chunks}),
            "usage": {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}}

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What navigation parameters are configured?"
    print(f"\n🔍 Query: {q}\n")
    r = query(q)
    print(f"💬 Answer:\n{r['answer']}\n")
    print(f"📎 Sources: {', '.join(r['sources'])}")