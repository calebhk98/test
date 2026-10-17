"""Command line interface. Every command takes --json for agents.

Exit codes: 0 ok, 1 error, 2 bad usage, 3 another run holds the lock,
4 `has` found nothing.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from .app import App, Busy


def _p(sub, name, help_):
    return sub.add_parser(name, help=help_, description=help_)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="agentwiki", description="Searchable wiki built from YouTube videos.")
    ap.add_argument("--root", default=".", help="folder holding config.toml, wiki/ and data/")
    ap.add_argument("--config", help="config file (default: <root>/config.toml)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    _p(sub, "init", "create config.toml, wiki/ and data/")

    s = _p(sub, "add", "add one video by URL or id, and process it now")
    s.add_argument("video")
    s.add_argument("--queue-only", action="store_true", help="queue it for the next `run`")
    s.add_argument("--force", action="store_true", help="process again even if already added")

    s = _p(sub, "has", "is this video already in the catalog? exit code 4 if not")
    s.add_argument("video")

    s = _p(sub, "channel", "manage subscribed channels")
    csub = s.add_subparsers(dest="channel_cmd", required=True)
    c = _p(csub, "add", "subscribe to a channel (URL or @handle) and queue its recent uploads")
    c.add_argument("url")
    c.add_argument("--backfill", action="store_true", help="also queue every past upload")
    c = _p(csub, "remove", "unsubscribe")
    c.add_argument("channel")
    _p(csub, "list", "list subscribed channels")

    s = _p(sub, "check", "queue new uploads from subscribed channels")
    s.add_argument("--channel")

    s = _p(sub, "backfill", "queue a channel's whole upload history at low priority")
    s.add_argument("channel")
    s.add_argument("--limit", type=int, help="only the newest N uploads")

    s = _p(sub, "run", "process the queue")
    s.add_argument("--limit", type=int, help="stop after N videos")
    s.add_argument("--max-minutes", type=float, help="stop after this long")
    s.add_argument("--sleep", type=float, help="seconds between downloads (default from config)")
    s.add_argument("--check", action="store_true", help="run `check` first")

    s = _p(sub, "status", "queue counts and index size, or one video's state")
    s.add_argument("video", nargs="?")
    s.add_argument("--list", dest="list_status", choices=["queued", "processing", "done", "failed", "skipped"])
    s.add_argument("--limit", type=int, default=20)

    s = _p(sub, "search", "hybrid keyword + vector search")
    s.add_argument("query")
    s.add_argument("-k", type=int)
    s.add_argument("--kind", choices=["video", "section"])
    s.add_argument("--tag", action="append", dest="tags", help="repeatable")
    s.add_argument("--channel")
    s.add_argument("--since", help="YYYY-MM-DD")
    s.add_argument("--include-sponsor", action="store_true")

    s = _p(sub, "ask", "answer a question from the wiki with the configured LLM")
    s.add_argument("question")
    s.add_argument("-k", type=int, default=8)
    s.add_argument("--since")

    s = _p(sub, "show", "print a page by doc id, video id/URL, or wiki path")
    s.add_argument("key")

    s = _p(sub, "similar", "videos closest to this one (whole-video embeddings)")
    s.add_argument("video")
    s.add_argument("-k", type=int, default=8)

    s = _p(sub, "reprocess", "redo stages after changing a model, then `run`")
    s.add_argument("videos", nargs="*", help="default: every done video")
    s.add_argument("--from", dest="from_stage", default="enrich",
                   choices=["info", "transcript", "sections", "enrich", "pages", "index"])

    _p(sub, "reindex", "embed every chunk with the current embedder")
    _p(sub, "mcp", "serve the same commands as MCP tools over stdio")
    return ap


def _human(cmd: str, r: dict) -> str:
    if "error" in r and len(r) == 1:
        return f"error: {r['error']}"
    if cmd == "search":
        if not r["hits"]:
            return "no results"
        lines = []
        for i, h in enumerate(r["hits"], 1):
            lines.append(f"{i}. [{h['kind']}] {h['title']}  ({h['published'][:10]})")
            lines.append(f"   {h['url']}")
            lines.append(f"   wiki: {h['path']}.md   id: {h['doc_id']}")
            lines.append(f"   {h['snippet'][:240]}")
        return "\n".join(lines)
    if cmd == "ask":
        out = [r["answer"] or r.get("note", "")]
        out += [""] + [f"[{s['n']}] {s['title']} - {s['video']} ({s['published']}) {s['url']}"
                       for s in r["sources"]]
        return "\n".join(out)
    if cmd == "show" and "content" in r:
        return r["content"]
    if cmd == "similar":
        return "\n".join(f"{h['published'][:10]} {h['title']}  ({h['path']})" for h in r["hits"]) or "no results"
    return json.dumps(r, indent=2, ensure_ascii=False, default=str)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr)
    if args.cmd == "mcp":
        from .mcp_server import serve
        return serve(args.root, args.config)

    app = App.open(args.root, args.config)
    try:
        r = dispatch(app, args)
    except Busy as e:
        r, code = {"error": str(e)}, 3
    except KeyboardInterrupt:
        return 130
    else:
        code = 1 if "error" in r else 0
        if args.cmd == "has" and not r.get("known"):
            code = 4 if "error" not in r else 1
        if args.cmd == "add" and r.get("status") == "failed":
            code = 1
    print(json.dumps(r, ensure_ascii=False, default=str) if args.json else _human(args.cmd, r))
    return code


def dispatch(app: App, a) -> dict:
    c = a.cmd
    if c == "init":
        return app.init()
    if c == "add":
        return app.add(a.video, process=not a.queue_only, force=a.force)
    if c == "has":
        return app.has(a.video)
    if c == "channel":
        if a.channel_cmd == "add":
            return app.channel_add(a.url, backfill=a.backfill)
        if a.channel_cmd == "remove":
            return app.channel_remove(a.channel)
        return app.channel_list()
    if c == "check":
        return app.check(a.channel)
    if c == "backfill":
        return app.backfill(a.channel, a.limit)
    if c == "run":
        return app.run(a.limit, a.max_minutes, a.sleep, a.check)
    if c == "status":
        return app.status(a.video, a.list_status, a.limit)
    if c == "search":
        return app.search(a.query, a.k, a.kind, a.tags, a.channel, a.since, a.include_sponsor)
    if c == "ask":
        return app.ask(a.question, a.k, a.since)
    if c == "show":
        return app.show(a.key)
    if c == "similar":
        return app.similar(a.video, a.k)
    if c == "reprocess":
        return app.reprocess(a.videos, a.from_stage)
    if c == "reindex":
        return app.reindex()
    raise SystemExit(f"unknown command {c}")


if __name__ == "__main__":
    sys.exit(main())
