"""
mcp_server.py — MCP server that exposes the ROS 2 RAG pipeline as tools.

Tools exposed:
  - query_robot_knowledge  : RAG query against the knowledge base
  - list_sources           : List all ingested source files
  - get_collection_stats   : Show how many chunks are in the DB
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(__file__))
from rag import query, get_collection

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("ros2-knowledge-assistant")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="query_robot_knowledge",
            description=(
                "Query the ROS 2 robot knowledge base using RAG. "
                "Ask questions about robot configuration, navigation parameters, "
                "URDF structure, launch files, sensor setup, and more. "
                "Returns a grounded answer with source citations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask about the robot system",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of relevant chunks to retrieve (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["question"],
            },
        ),
        types.Tool(
            name="list_sources",
            description="List all source files currently ingested in the knowledge base.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_collection_stats",
            description="Get statistics about the knowledge base (chunk count, collection info).",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    if name == "query_robot_knowledge":
        question = arguments.get("question", "")
        top_k = arguments.get("top_k", 5)
        if not question:
            return [types.TextContent(type="text", text="Error: 'question' is required.")]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: query(question, top_k=top_k))
        output = f"**Answer:**\n{result['answer']}\n\n"
        output += "**Sources:**\n" + "\n".join(f"- `{s}`" for s in result["sources"])
        output += f"\n\n*Tokens used: {result['usage']['input_tokens']} in / {result['usage']['output_tokens']} out*"
        return [types.TextContent(type="text", text=output)]

    elif name == "list_sources":
        try:
            collection = get_collection()
            results = collection.get(include=["metadatas"])
            sources = sorted({m.get("source", "unknown") for m in results["metadatas"]})
            text = f"**Ingested sources ({len(sources)} files):**\n"
            text += "\n".join(f"- `{s}`" for s in sources)
        except Exception as e:
            text = f"Error listing sources: {e}"
        return [types.TextContent(type="text", text=text)]

    elif name == "get_collection_stats":
        try:
            collection = get_collection()
            count = collection.count()
            text = (
                f"**Knowledge Base Stats**\n"
                f"- Collection: `ros2_knowledge`\n"
                f"- Total chunks: {count}\n"
                f"- DB path: `{os.getenv('CHROMA_PATH', './chroma_db')}`\n"
            )
        except Exception as e:
            text = f"Error getting stats: {e}"
        return [types.TextContent(type="text", text=text)]

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    sys.stderr.write("🤖 ROS 2 Knowledge Assistant MCP Server starting...\n")
    sys.stderr.flush()
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
