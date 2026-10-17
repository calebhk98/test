# agent-wiki

Turns YouTube videos into a markdown wiki that AI agents can search. Each video
becomes a page, each chapter of a video becomes its own page, and every page is
tagged, summarised and embedded. The wiki folder opens as an Obsidian vault, but
nothing needs Obsidian.

Design: [ARCHITECTURE.md](ARCHITECTURE.md). What was tested for real: [TESTING.md](TESTING.md).
What exists already and how other
people do this: [RESEARCH.md](RESEARCH.md).

## Setup

```bash
cd agent-wiki
pip install -e ".[all]"        # or just `pip install -e .` plus the extras you want
agentwiki init                 # writes config.toml, wiki/, data/
```

Everything runs on your machine. The defaults work without editing anything
except, possibly, YouTube access:

- **YouTube access.** YouTube sometimes refuses yt-dlp with "Sign in to confirm
  you're not a bot". Set `cookies_from_browser = "firefox"` (or chrome, edge...)
  under `[source]`, or try `player_clients = ["web_safari", "web_embedded"]`.
  A home connection is usually fine without either.
- **JavaScript runtime.** yt-dlp needs [deno](https://deno.com) or node for YouTube.
- **ffmpeg** on the PATH (yt-dlp and the Whisper audio decoding both use it).
- **Models download themselves** on first use from Hugging Face, no login.

`agentwiki status` shows the hardware it detected and so what "auto" picked.

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

## Hardware

Nothing needs configuring per machine. Whisper's model size, the in-process
LLM's size, the device (CUDA, Apple, CPU), precision and batch sizes are all
picked from the detected VRAM and RAM:

| machine | Whisper | in-process LLM |
| --- | --- | --- |
| GPU, 70 GB+ VRAM | large-v3-turbo, batched | Gemma 4 31B |
| GPU, 30 to 70 GB | large-v3-turbo, batched | Gemma 4 12B |
| GPU, 12 to 30 GB | large-v3-turbo, batched | Gemma 4 E4B |
| GPU, 6 to 12 GB | large-v3-turbo, batched | Gemma 4 E2B |
| GPU, 4 to 6 GB | large-v3-turbo, batched | chosen by RAM, as for CPU |
| CPU, 32 GB+ RAM | small | Gemma 4 E4B |
| CPU, 16 GB+ RAM | small | Gemma 4 E2B |
| CPU, 6 to 16 GB | small (12 GB+) or base | Qwen2.5 1.5B |
| phone or small board | base or tiny | Qwen2.5 0.5B, or better, no LLM |

Override any of them with an explicit `model = "..."`. The embedder is the one
thing that does not change with hardware, so a wiki built on a desktop can be
searched from a laptop.

## Without an LLM

Every feature works without one. The `local` enricher uses the embedding model
for tags (key phrases and topic categories) and summaries (the most
representative sentences), and patterns for facts like parameter counts,
VRAM, licence and censorship. Videos without chapters are split by topic with
the same embeddings. `ask` without an LLM returns the cited sources, which an
agent such as Claude Code reads and answers from.

With `[enricher] type = "llm"`, an unreachable LLM never stops anything: the
local enricher fills in, and the next `run` upgrades those videos from cache
once the LLM answers.

## Podcasts

`[source] type = "podcast"` reads RSS feeds instead of YouTube, with episode
chapters from `podcast:chapters` files. Same pipeline, same wiki.

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
