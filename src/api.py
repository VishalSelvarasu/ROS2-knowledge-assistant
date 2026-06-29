import os, sys
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions

sys.path.insert(0, os.path.dirname(__file__))
from rag import query as rag_query, CHROMA_PATH, COLLECTION, EMBED_MODEL

app = FastAPI(
    title="ROS 2 Robot Knowledge Assistant",
    description="RAG-powered API for querying robot configurations and documentation",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    usage: dict

@app.get("/health")
def health():
    return {"status": "ok", "service": "ros2-knowledge-assistant"}

@app.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty")
    try:
        result = rag_query(req.question, top_k=req.top_k)
        return QueryResponse(answer=result["answer"], sources=result["sources"], usage=result["usage"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sources")
def list_sources():
    try:
        cc = chromadb.PersistentClient(path=CHROMA_PATH)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
        collection = cc.get_or_create_collection(name=COLLECTION, embedding_function=ef)
        results = collection.get(include=["metadatas"])
        sources = sorted({m.get("source", "unknown") for m in results["metadatas"]})
        return {"sources": sources, "count": len(sources)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def stats():
    try:
        cc = chromadb.PersistentClient(path=CHROMA_PATH)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
        collection = cc.get_or_create_collection(name=COLLECTION, embedding_function=ef)
        return {"collection": COLLECTION, "chunk_count": collection.count(), "chroma_path": CHROMA_PATH}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))