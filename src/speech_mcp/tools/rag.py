from fastmcp import Context, FastMCP

from speech_mcp.state import get_store


def register_rag_tools(mcp: FastMCP):

    @mcp.tool()
    def search_docs(query: str, limit: int = 5) -> dict:
        """
        Semantic search over the speech-mcp knowledge base (RAG).

        Uses LanceDB + FastEmbed (BAAI/bge-small-en-v1.5) to find relevant
        documentation chunks.

        Args:
            query (str): Natural language search query.
            limit (int): Maximum number of results to return. Default: 5.
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
    async def ask_docs(question: str, ctx: Context) -> dict:
        """
        Ask complex questions about speech AI using RAG + LLM sampling.

        Retrieves relevant documentation chunks from LanceDB, then uses
        FastMCP 3.x ctx.sample() to generate a grounded answer.

        Args:
            question (str): Natural language question.
            ctx (Context): FastMCP context.
        """
        search_result = search_docs(question, limit=8)
        if not search_result["success"]:
            return {**search_result, "recovery_options": ["Try search_docs directly"]}

        chunks = search_result["data"]
        context_text = "\n\n".join(f"SOURCE: {r['filename']}\nCONTENT: {r['content']}" for r in chunks)
        sources = list({r["filename"] for r in chunks})

        result = await ctx.sample(
            messages=f"Context:\n{context_text}\n\nQuestion: {question}",
            system_prompt=("You are a SOTA speech technology expert. Answer concisely based on the context."),
        )

        return {
            "success": True,
            "answer": result.text,
            "sources": sources,
        }
