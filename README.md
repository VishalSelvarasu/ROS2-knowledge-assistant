# 🤖 ROS 2 Robot Knowledge Assistant

A **RAG (Retrieval-Augmented Generation) + MCP** system that turns your robot's documentation — nav parameters, URDF files, launch configs, READMEs — into a queryable AI knowledge base.

Ask natural language questions like:
- *"What is the inflation radius in the local costmap?"*
- *"Which controller plugin is used for path following?"*
- *"What topics does the safety monitor subscribe to?"*

And get grounded, cited answers from your actual robot files.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your Robot Docs                      │
│   nav2_params.yaml │ robot_description.md │ URDF │ ...  │
└────────────────────────┬────────────────────────────────┘
                         │  ingest.py
                         ▼
              ┌──────────────────────┐
              │   ChromaDB (local)   │  ← vector store
              │   voyage-3 embeddings│
              └──────────┬───────────┘
                         │  retrieve top-k chunks
                         ▼
              ┌──────────────────────┐
              │    Claude Sonnet     │  ← generation
              │  (claude-sonnet-4-6) │
              └──────────┬───────────┘
                         │
           ┌─────────────┴──────────────┐
           │                            │
    ┌──────▼──────┐             ┌───────▼──────┐
    │  MCP Server │             │  FastAPI HTTP │
    │  (stdio)    │             │  :8000        │
    └──────┬──────┘             └───────┬───────┘
           │                            │
    Claude Desktop               curl / browser /
    or any MCP client            Streamlit UI
```

---

## Quickstart

### 1. Clone & setup

```bash
git clone https://github.com/YOUR_USERNAME/ros2-knowledge-assistant
cd ros2-knowledge-assistant

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Add your robot docs

Drop any `.md`, `.yaml`, `.yml`, `.urdf`, `.py`, or `.txt` files into the `docs/` folder.

Sample docs are included to test immediately.

### 3. Ingest documents

```bash
python src/ingest.py
```

You'll see each file chunked and embedded into ChromaDB:
```
📂 Scanning: ./docs
📄 Found 2 files to ingest

  ↳ nav2_params.yaml
     ✓ 12 chunks
  ↳ robot_description.md
     ✓ 5 chunks

✅ Ingestion complete — 17 chunks stored in ./chroma_db
```

### 4. Test the RAG pipeline

```bash
python src/rag.py "What is the MPPI controller's maximum linear velocity?"
```

---

## Using as an MCP Server (Claude Desktop)

1. Edit `claude_desktop_config.json` with your absolute paths
2. Add the contents to your Claude Desktop config at:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
3. Restart Claude Desktop
4. You'll see three new tools: `query_robot_knowledge`, `list_sources`, `get_collection_stats`

---

## Using the HTTP API

```bash
# Start the FastAPI server
uvicorn src.api:app --host 0.0.0.0 --port 8000

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the robot radius?"}'

# List ingested sources
curl http://localhost:8000/sources

# Stats
curl http://localhost:8000/stats
```

Interactive API docs: http://localhost:8000/docs

---

## Docker

```bash
# Build
docker compose build

# Step 1: Ingest
docker compose --profile ingest up ingest

# Step 2: Run API server
docker compose up api

# MCP server (stdio)
docker compose --profile mcp run mcp
```

---

## Project Structure

```
ros2-knowledge-assistant/
├── src/
│   ├── ingest.py          # Doc ingestion → ChromaDB
│   ├── rag.py             # Retrieval + Claude generation
│   ├── mcp_server.py      # MCP server (3 tools)
│   └── api.py             # FastAPI HTTP interface
├── docs/                  # Drop your robot docs here
│   ├── nav2_params.yaml   # (sample)
│   └── robot_description.md (sample)
├── chroma_db/             # Auto-created on first ingest
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── claude_desktop_config.json
└── README.md
```

---

## MCP Tools Reference

| Tool | Description | Input |
|------|-------------|-------|
| `query_robot_knowledge` | RAG query with cited answer | `question` (str), `top_k` (int, default 5) |
| `list_sources` | List all ingested files | — |
| `get_collection_stats` | Chunk count and DB path | — |

---

## CV Bullet Point

> Built a RAG + MCP system for ROS 2 robot documentation — ingests nav params, URDF, and launch files into ChromaDB (voyage-3 embeddings), retrieves context via cosine similarity, and generates grounded answers using Claude Sonnet. Exposed as an MCP server (compatible with Claude Desktop) and FastAPI HTTP endpoint; containerized with Docker Compose.

---

## Tech Stack

- **Embeddings**: Anthropic voyage-3 (via ChromaDB embedding function)
- **Vector store**: ChromaDB (persistent, local)
- **LLM**: Claude Sonnet 4.6 (`claude-sonnet-4-6`)
- **MCP**: `mcp` Python SDK (stdio transport)
- **API**: FastAPI + Uvicorn
- **Containerization**: Docker + Docker Compose

---

## Extending

**Add more doc types:** Extend `SUPPORTED_EXTENSIONS` in `ingest.py` (e.g., `.pdf` with PyMuPDF, `.bag` metadata extraction).

**Add ROS 2 bag support:** Parse rosbag2 metadata and topic summaries as text, ingest them — query your past robot runs in natural language.

**Add a Streamlit UI:** Call the FastAPI `/query` endpoint from a simple Streamlit app for a visual demo.

---

## License

MIT
