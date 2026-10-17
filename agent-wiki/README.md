# agent-wiki

Turns YouTube videos into a markdown wiki that AI agents can search. Each video
becomes a page, each chapter of a video becomes its own page, and every page is
tagged, summarised and embedded. The wiki folder opens as an Obsidian vault, but
nothing needs Obsidian.

Design: [ARCHITECTURE.md](ARCHITECTURE.md). What exists already and how other
people do this: [RESEARCH.md](RESEARCH.md).

## Setup

```bash
cd agent-wiki
pip install -e ".[all]"        # or just `pip install -e .` plus the extras you want
agentwiki init                 # writes config.toml, wiki/, data/
```

Then edit `config.toml`:

- **Cookies.** YouTube often refuses yt-dlp with "Sign in to confirm you're not
  a bot". Set `cookies_from_browser = "firefox"` (or chrome, edge...) under
  `[source]`. This happened on every request from the cloud machine this was
  built on; a home connection is usually fine without cookies.
- **JavaScript runtime.** yt-dlp needs [deno](https://deno.com) or node for YouTube.
- **ffmpeg** on the PATH (yt-dlp and the Whisper audio decoding both use it).
- **LLM.** Defaults to Ollama. `ollama pull gemma3:12b`, or set any model you
  have. Without an LLM set `[enricher] type = "keyword"` and it still works,
  with cruder tags and summaries.
- **Embedder.** Defaults to `google/embeddinggemma-300m`, which is gated on
  Hugging Face: accept the licence on its page, then `hf auth login`.

## Use

```bash
agentwiki channel add https://www.youtube.com/@theAIsearch   # subscribe, queue recent uploads
agentwiki run --limit 1                                      # process one, check the result
agentwiki backfill @theAIsearch                              # queue every past upload
agentwiki run --max-minutes 120                              # drain the queue a bit at a time

agentwiki add https://youtu.be/lHmZoRHMZyM                   # one video, now
agentwiki has lHmZoRHMZyM                                    # exit code 0 if known, 4 if not
agentwiki check                                              # queue new uploads from subscriptions
agentwiki status

agentwiki search "open weights text to video model" --kind section
agentwiki ask "what is the fastest text to world model that keeps a consistent world"
agentwiki show lHmZoRHMZyM#14                                # a section page by id
agentwiki similar lHmZoRHMZyM
```

Every command takes `--json`. Run from the folder holding `config.toml`, or pass
`--root /path/to/kb`.

For a weekly channel and a slow backfill, a cron line like this does both:

```
0 */6 * * *  cd /path/to/kb && agentwiki run --check --max-minutes 90
```

## For agents

- `wiki/AGENTS.md` tells an agent how to use the wiki.
- Claude Code over MCP: `claude mcp add agent-wiki -- agentwiki --root /path/to/kb mcp`
  (needs the `mcp` extra). Tools: search, show, ask, similar, has_video,
  add_video, add_channel, list_channels, check_channels, run_queue, status.
- Any agent that can run shell commands can use the CLI with `--json` instead.

## Swapping models

Each model is a `[section]` in `config.toml` with a `type`. After changing one:

| changed | run |
| --- | --- |
| transcriber | `agentwiki reprocess --from transcript`, then `agentwiki run` (downloads audio again) |
| LLM or enricher | `agentwiki reprocess --from enrich`, then `agentwiki run` |
| segmenter | `agentwiki reprocess --from sections`, then `agentwiki run` |
| embedder | `agentwiki reindex` |

Transcripts are cached in `data/raw/`, so only a transcriber change downloads
anything again.

To add a backend, subclass the base class and register it:

```python
from agentwiki.embed.base import Embedder
from agentwiki.registry import register

@register("embedder", "my-encoder")
class MyEncoder(Embedder):
    def __init__(self, model: str):
        self.model = model
    def _embed(self, texts, is_query):
        ...   # return an (n, dim) numpy array
```

Put the module on the Python path, add `plugins = ["my_module"]` to config, and set
`[embedder] type = "my-encoder"`. The same pattern works for `source`,
`transcriber`, `segmenter`, `llm`, `enricher` and `index`.

## Tests

```bash
pip install -e ".[dev]" && pytest
```

The tests run offline against saved metadata from a real AI Search video
(`tests/fixtures/`), with fake download and transcription.
