# agent-wiki architecture

A local knowledge base that turns YouTube videos (and later other sources) into
an Obsidian-compatible markdown wiki plus a search index that AI agents query
through a CLI or an MCP server.

## Goals

1. Ingest a video: metadata, audio, transcript, then delete the audio.
2. Write one wiki page per video and one per sub-part (chapter), linked both ways.
3. Tag, summarise and embed every page.
4. Answer questions like "what text-to-video models are there, how big are they,
   are they censored" by searching sections and citing timestamped links.
5. Watch channels for new videos, backfill whole channels slowly, add single
   videos by hand, and never process the same video twice.
6. Every model (transcriber, LLM, embedder) is swappable from config, without
   touching code, because the best choice changes every few months.
7. Everything an agent needs is a command with `--json` output.

## Decisions and why

| decision | reason |
| --- | --- |
| Markdown files are the source of truth for reading; SQLite holds the index | A vault is just a folder of `.md` files. Obsidian is an optional viewer. The index is disposable and can be rebuilt from cached data. |
| Cache every stage in `data/raw/<video_id>/` | Swapping the LLM or embedder later means re-running from cache, never re-downloading. Only audio is thrown away. |
| Split on creator chapters first, time windows as fallback | AI Search videos have 20 to 30 chapters each, and the description lists one link per chapter. That is better than any topic model. |
| SQLite FTS5 (BM25) plus vectors, merged with reciprocal rank fusion | Model names like "Flux 3" or "Wan 2.6" are exact strings that embeddings handle badly and BM25 handles well. Descriptive questions are the opposite. |
| Brute-force numpy cosine over vectors in SQLite | One channel is tens of thousands of chunks, which numpy scans in milliseconds. `VectorIndex` is abstract so sqlite-vec or LanceDB can replace it later. |
| Whole-video embedding = mean of its chunk vectors | No current local encoder takes a 40 minute transcript (EmbeddingGemma's context is 2048 tokens). The whole text is still encoded, in chunks, and pooled for "find similar videos". |
| A component registry keyed by `type` strings | Config says `type = "ollama"`; adding a new backend is one class with `@register`. Third-party classes load through `plugins = ["my_module"]`. |
| CLI first, MCP server as a thin wrapper | A CLI works with any agent that can run shell commands, including small local models. MCP gives Claude Code typed tools. Both call the same `App` methods. |

## Layout on disk

```
<root>/
  config.toml
  wiki/                         <- open this folder in Obsidian if you want
    AGENTS.md                   <- how an agent should use this wiki
    channels/ai-search.md       <- hub page, list of videos
    videos/2026-10-04-gemini-4-gpt-6-1-...-lHmZoRHMZyM.md
    sections/lHmZoRHMZyM/06-claude-sonnet-5-5.md
  data/
    catalog.sqlite              <- videos, channels, status, errors
    index.sqlite                <- docs, chunks, FTS, vectors
    raw/<video_id>/info.json        stage 1
    raw/<video_id>/transcript.json  stage 2
    raw/<video_id>/sections.json    stage 3
    raw/<video_id>/enrichment.json  stage 4
    tmp/                        <- audio lives here only while transcribing
```

## Components (each an abstract base class with swappable implementations)

```
VideoSource      list_channel(), fetch_info(), download_audio()
  YtDlpSource         yt-dlp as a library; cookies and JS runtime from config

Transcriber      transcribe(info, audio_path) -> Transcript(segments with start/end)
  FasterWhisperTranscriber   local Whisper (CPU or GPU)
  YouTubeCaptionsTranscriber uses YouTube auto-captions, no audio needed, fast
  ChainTranscriber           try A, fall back to B

Segmenter        split(info, transcript) -> [Section]
  ChapterSegmenter       creator chapters, links matched from the description,
                         sponsor chapters flagged
  FixedWindowSegmenter   N-minute windows cut on segment boundaries
  ChainSegmenter         first segmenter that returns something wins

LLM              complete(prompt, system) -> str, complete_json()
  OllamaLLM, OpenAICompatLLM (llama.cpp, LM Studio, vLLM, OpenAI), AnthropicLLM, NullLLM

Enricher         enrich_section(), enrich_video() -> summary, tags, facts
  LLMEnricher       asks the LLM for JSON; section facts include model names,
                    sizes, licence, censorship, hardware, speed
  KeywordEnricher   no model; frequency-based tags, first sentences as summary

Embedder         embed_documents([str]), embed_query(str), name, dim
  SentenceTransformerEmbedder  EmbeddingGemma and anything on Hugging Face
  OllamaEmbedder, OpenAICompatEmbedder
  HashingEmbedder              deterministic, dependency-free, for tests

VectorIndex      upsert_doc(), search(), similar(), embedders()
  SQLiteIndex      FTS5 + numpy, hybrid RRF, filters on kind/tag/channel/date
```

Supporting, not swappable: `Catalog` (SQLite state), `WikiWriter` (markdown
rendering), `Pipeline` (runs stages with resume), `App` (the facade that the
CLI and MCP server call).

## Pipeline for one video

```
queued
  -> info        fetch_info()                      raw/<id>/info.json
  -> transcript  download audio to tmp/, transcribe, delete audio (always, in finally)
  -> sections    segment and attach transcript text
  -> enrich      per section, then video summary built from section summaries
  -> pages       write video page, section pages, channel hub
  -> index       chunk, embed, upsert; video vector = mean of chunk vectors
done
```

Each stage skips itself when its cache file exists, so a crash or a Ctrl-C
resumes where it stopped. `reprocess --from enrich` deletes the cache from that
stage on and reruns, which is how a model upgrade gets applied to old videos.

## Discovery and the queue

- `channel add URL` subscribes. `check` lists the newest N uploads of each
  subscribed channel and queues the ones the catalog has not seen.
- `backfill CHANNEL` queues the whole upload list at low priority.
- `add URL` queues one video at high priority and, by default, processes it now.
- `run --limit N --max-minutes M` drains the queue in priority order, sleeping
  between downloads, with a lock file so two cron jobs cannot collide. Failures
  are recorded with the error and retried up to `max_attempts`.
- Filters: skip live streams, premieres that have not aired, and videos shorter
  than `min_duration` (Shorts).

## Page format

Frontmatter is YAML (written as JSON-style scalars, which YAML accepts), so
Obsidian, Dataview and any script can read it. Links are path wikilinks so they
stay unique. Every section page links to its parent and its neighbours, and has
a timestamped YouTube link. Tags are normalised to kebab-case, which is what
Obsidian accepts.

## Agent interface

```
agentwiki search "text to video model open weights" --kind section --json
agentwiki ask "what text to video models are there, what size, are they censored"
agentwiki show <video_id or path>
agentwiki has <video_id>          exit code 0 if already added
agentwiki add <url>   |  channel add <url>  |  check  |  backfill <channel>  |  run
agentwiki status --json
agentwiki similar <video_id>
agentwiki reprocess --from enrich --all   |   reindex
agentwiki mcp                     MCP server over stdio (optional dependency)
```

## Known limits

- YouTube blocks some IPs (cloud servers especially) with "confirm you're not a
  bot". Set `cookies_from_browser` or `cookies_file` in config. yt-dlp also needs
  a JavaScript runtime (deno or node) for YouTube now.
- Brute-force vector search is fine to roughly a few hundred thousand chunks;
  past that, implement a `VectorIndex` on sqlite-vec or LanceDB.
- Changing the embedder makes old vectors unusable for search; `reindex`
  re-embeds from cache. Vectors are stored per embedder name, so nothing breaks
  in between, results are just missing until the reindex finishes.
