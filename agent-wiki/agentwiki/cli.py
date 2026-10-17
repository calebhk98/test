"""Command line interface. Every command takes --json for agents.

Exit codes: 0 ok, 1 error, 2 bad usage, 3 another run holds the lock,
4 `has` found nothing, 5 the source is rate limiting or bot-checking.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from .app import App, Busy


def _global_options(suppress_defaults: bool) -> argparse.ArgumentParser:
    """--root, --config, --json and -v, accepted before or after the command
    (`agentwiki --json status` and `agentwiki status --json` both work). On
    the commands the defaults are suppressed so they never overwrite a value
    given before the command."""
    options = argparse.ArgumentParser(add_help=False)
    default = (lambda value: argparse.SUPPRESS) if suppress_defaults else (lambda value: value)
    options.add_argument("--root", default=default("."), help="folder holding config.toml, wiki/ and data/")
    options.add_argument("--config", default=default(None), help="config file (default: <root>/config.toml)")
    options.add_argument("--json", action="store_true", default=default(False), help="machine-readable output")
    options.add_argument("-v", "--verbose", action="store_true", default=default(False))
    return options


_COMMAND_OPTIONS = _global_options(suppress_defaults=True)


def _add_command(commands, name, help_text):
    return commands.add_parser(name, help=help_text, description=help_text, parents=[_COMMAND_OPTIONS])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentwiki", parents=[_global_options(suppress_defaults=False)],
                                     description="Searchable wiki built from YouTube videos and podcasts.")
    commands = parser.add_subparsers(dest="cmd", required=True)

    _add_command(commands, "init", "create config.toml, wiki/ and data/")

    subparser = _add_command(commands, "add", "add one video by URL or id, and process it now")
    subparser.add_argument("video")
    subparser.add_argument("--queue-only", action="store_true", help="queue it for the next `run`")
    subparser.add_argument("--force", action="store_true", help="process again even if already added")

    subparser = _add_command(commands, "has", "is this video already in the catalog? exit code 4 if not")
    subparser.add_argument("video")

    subparser = _add_command(commands, "channel", "manage subscribed channels")
    channel_commands = subparser.add_subparsers(dest="channel_cmd", required=True)
    channel_parser = _add_command(channel_commands, "add", "subscribe to a channel (URL or @handle) and queue its recent uploads")
    channel_parser.add_argument("url")
    channel_parser.add_argument("--backfill", action="store_true", help="also queue every past upload")
    channel_parser = _add_command(channel_commands, "remove", "unsubscribe")
    channel_parser.add_argument("channel")
    _add_command(channel_commands, "list", "list subscribed channels")

    subparser = _add_command(commands, "check", "queue new uploads from subscribed channels")
    subparser.add_argument("--channel")

    subparser = _add_command(commands, "backfill", "queue a channel's whole upload history at low priority")
    subparser.add_argument("channel")
    subparser.add_argument("--limit", type=int, help="only the newest N uploads")

    subparser = _add_command(commands, "run", "process the queue")
    subparser.add_argument("--limit", type=int, help="stop after N videos")
    subparser.add_argument("--max-minutes", type=float, help="stop after this long")
    subparser.add_argument("--sleep", type=float, help="seconds between downloads (default from config)")
    subparser.add_argument("--check", action="store_true", help="run `check` first")

    subparser = _add_command(commands, "status", "queue counts and index size, or one video's state")
    subparser.add_argument("video", nargs="?")
    subparser.add_argument("--list", dest="list_status",
                           choices=["queued", "processing", "done", "failed", "skipped"])
    subparser.add_argument("--limit", type=int, default=20)

    subparser = _add_command(commands, "search", "hybrid keyword + vector search")
    subparser.add_argument("query")
    subparser.add_argument("-k", type=int)
    subparser.add_argument("--kind", choices=["video", "section"])
    subparser.add_argument("--tag", action="append", dest="tags", help="repeatable")
    subparser.add_argument("--channel")
    subparser.add_argument("--since", help="YYYY-MM-DD")
    subparser.add_argument("--include-sponsor", action="store_true")

    subparser = _add_command(commands, "ask", "answer a question from the wiki with the configured LLM")
    subparser.add_argument("question")
    subparser.add_argument("-k", type=int, default=8)
    subparser.add_argument("--since")

    subparser = _add_command(commands, "show", "print a page by doc id, video id/URL, or wiki path")
    subparser.add_argument("key")

    subparser = _add_command(commands, "similar", "videos closest to this one (whole-video embeddings)")
    subparser.add_argument("video")
    subparser.add_argument("-k", type=int, default=8)

    subparser = _add_command(commands, "reprocess", "redo stages after changing a model, then `run`")
    subparser.add_argument("videos", nargs="*", help="default: every done video")
    subparser.add_argument("--from", dest="from_stage", default="enrich",
                           choices=["info", "transcript", "sections", "enrich", "pages", "index"])

    _add_command(commands, "reindex", "embed every chunk with the current embedder")
    _add_command(commands, "mcp", "serve the same commands as MCP tools over stdio")
    return parser


def _human(cmd: str, result: dict) -> str:
    if "error" in result and len(result) == 1:
        return f"error: {result['error']}"
    if cmd == "search":
        if not result["hits"]:
            return "no results"
        lines = []
        for position, hit in enumerate(result["hits"], 1):
            lines.append(f"{position}. [{hit['kind']}] {hit['title']}  ({hit['published'][:10]})")
            lines.append(f"   {hit['url']}")
            lines.append(f"   wiki: {hit['path']}.md   id: {hit['doc_id']}")
            lines.append(f"   {hit['snippet'][:240]}")
        return "\n".join(lines)
    if cmd == "ask":
        out = [result["answer"] or result.get("note", "")]
        out += [""] + [f"[{source['n']}] {source['title']} - {source['video']} "
                       f"({source['published']}) {source['url']}"
                       for source in result["sources"]]
        return "\n".join(out)
    if cmd == "show" and "content" in result:
        return result["content"]
    if cmd == "similar":
        return "\n".join(
            f"{hit['published'][:10]} {hit['title']}  ({hit['path']})" for hit in result["hits"]
        ) or "no results"
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr)
    if args.cmd == "mcp":
        from .mcp_server import serve
        return serve(args.root, args.config)

    app = App.open(args.root, args.config)
    try:
        result = dispatch(app, args)
    except Busy as error:
        result, code = {"error": str(error)}, 3
    except KeyboardInterrupt:
        return 130
    else:
        code = 1 if "error" in result else 0
        if args.cmd == "has" and not result.get("known"):
            code = 4 if "error" not in result else 1
        if args.cmd == "add" and result.get("status") == "failed":
            code = 1
        if result.get("blocked") or result.get("stopped"):
            code = 5
    print(json.dumps(result, ensure_ascii=False, default=str) if args.json else _human(args.cmd, result))
    return code


def dispatch(app: App, args) -> dict:
    command = args.cmd
    if command == "init":
        return app.init()
    if command == "add":
        return app.add(args.video, process=not args.queue_only, force=args.force)
    if command == "has":
        return app.has(args.video)
    if command == "channel":
        if args.channel_cmd == "add":
            return app.channel_add(args.url, backfill=args.backfill)
        if args.channel_cmd == "remove":
            return app.channel_remove(args.channel)
        return app.channel_list()
    if command == "check":
        return app.check(args.channel)
    if command == "backfill":
        return app.backfill(args.channel, args.limit)
    if command == "run":
        return app.run(args.limit, args.max_minutes, args.sleep, args.check)
    if command == "status":
        return app.status(args.video, args.list_status, args.limit)
    if command == "search":
        return app.search(args.query, args.k, args.kind, args.tags, args.channel, args.since,
                          args.include_sponsor)
    if command == "ask":
        return app.ask(args.question, args.k, args.since)
    if command == "show":
        return app.show(args.key)
    if command == "similar":
        return app.similar(args.video, args.k)
    if command == "reprocess":
        return app.reprocess(args.videos, args.from_stage)
    if command == "reindex":
        return app.reindex()
    raise SystemExit(f"unknown command {command}")


if __name__ == "__main__":
    sys.exit(main())
