"""MCP server exposing the App methods as tools. `pip install mcp`.

Register with Claude Code:
    claude mcp add agent-wiki -- agentwiki --root /path/to/kb mcp
"""
from __future__ import annotations

from .app import App, Busy


def serve(root: str = ".", config: str | None = None) -> int:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise SystemExit("the MCP server needs the `mcp` package: pip install 'agent-wiki[mcp]'")

    app = App.open(root, config)
    mcp = FastMCP("agent-wiki")

    def safe(function, *args, **options):
        try:
            return function(*args, **options)
        except Busy as error:
            return {"error": str(error)}

    @mcp.tool()
    def search(query: str, top_k: int = 8, kind: str | None = None, tags: list[str] | None = None,
               channel: str | None = None, since: str | None = None) -> dict:
        """Hybrid keyword + semantic search over the wiki. kind: "section" (one topic of a
        video, usually what you want) or "video". since: YYYY-MM-DD. Returns hits with a
        timestamped YouTube url, wiki path, snippet and doc_id for `show`."""
        return app.search(query, top_k, kind, tags, channel, since)

    @mcp.tool()
    def show(key: str) -> dict:
        """Full markdown of a page, by doc_id from search, video id/URL, or wiki path."""
        return app.show(key)

    @mcp.tool()
    def ask(question: str, top_k: int = 8, since: str | None = None) -> dict:
        """Answer with the wiki's configured LLM, citing sources. Without an LLM configured,
        returns the sources only."""
        return app.ask(question, top_k, since)

    @mcp.tool()
    def similar(video_id: str, top_k: int = 8) -> dict:
        """Videos whose whole transcript is closest to this one."""
        return app.similar(video_id, top_k)

    @mcp.tool()
    def has_video(video: str) -> dict:
        """Whether a video (URL or id) is already in the catalog, and its status."""
        return app.has(video)

    @mcp.tool()
    def add_video(video: str, process_now: bool = False) -> dict:
        """Add one video by URL or id. process_now=False queues it (fast); True downloads,
        transcribes and indexes it before returning, which takes minutes."""
        return safe(app.add, video, process=process_now)

    @mcp.tool()
    def add_channel(url: str, backfill: bool = False) -> dict:
        """Subscribe to a channel and queue its recent uploads; backfill queues all of them."""
        return app.channel_add(url, backfill)

    @mcp.tool()
    def list_channels() -> dict:
        """Subscribed channels."""
        return app.channel_list()

    @mcp.tool()
    def check_channels(channel: str | None = None) -> dict:
        """Queue new uploads from subscribed channels (or one channel)."""
        return app.check(channel)

    @mcp.tool()
    def run_queue(limit: int = 1, max_minutes: float = 30) -> dict:
        """Process queued videos. Slow: each video is downloaded and transcribed."""
        return safe(app.run, limit, max_minutes)

    @mcp.tool()
    def status(video: str | None = None) -> dict:
        """Queue counts and index size, or one video's processing state."""
        return app.status(video)

    mcp.run()
    return 0
