from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from speech_mcp.sanitize import wrap_untrusted
from speech_mcp.state import get_store


def register_rag_tools(mcp: FastMCP):

    @mcp.tool()
    async def search_docs(
        query: Annotated[str, Field(description="Natural language search query.")],
        limit: Annotated[int, Field(description="Maximum number of results.")] = 5,
        ctx: Context = None,
    ) -> dict:
        """
        Semantic search over the speech-mcp knowledge base (RAG).

        Uses LanceDB + FastEmbed (BAAI/bge-small-en-v1.5) to find relevant documentation chunks.

        ## Return Format
        {"success": bool, "data": [{"filename": str, "score": float, "content": str}]}

        ## Examples
        await search_docs("expressive speech synthesis", limit=3)
        """
        results = get_store().search(query, limit=limit)
        return {
            "success": True,
            "data": [
                {
                    "filename": r["metadata"].get("filename", "unknown"),
                    "score": max(0.0, 1.0 - r.get("_distance", 0.0)),
                    "content": r["content"],
                }
                for r in results
            ],
        }

    @mcp.tool()
    async def ask_docs(
        question: Annotated[str, Field(description="Natural language question about speech AI.")],
        ctx: Context,
    ) -> dict:
        """
        Answer complex questions about speech AI using RAG + LLM sampling.

        Retrieves relevant documentation chunks from LanceDB, then uses
        FastMCP ctx.sample() to generate a grounded answer.

        ## Return Format
        {"success": bool, "answer": str, "sources": [str]}

        ## Examples
        await ask_docs("What providers does speech-mcp support?", ctx)
        """
        search_result = await search_docs(question, limit=8)
        if not search_result["success"]:
            return {**search_result, "recovery_options": ["Try search_docs directly"]}

        chunks = search_result["data"]
        context_text = "\n\n".join(f"SOURCE: {r['filename']}\nCONTENT: {r['content']}" for r in chunks)
        sources = list({r["filename"] for r in chunks})

        result = await ctx.sample(
            messages=f"Context:\n{context_text}\n\nQuestion: {wrap_untrusted(question, 'user_question')}",
            system_prompt=("You are a SOTA speech technology expert. Answer concisely based on the context."),
        )

        return {
            "success": True,
            "answer": result.text,
            "sources": sources,
        }
