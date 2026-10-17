# Prior art and choices (October 2026)

Summary of a research pass. **Unverified** marks claims taken from search
snippets or secondary write-ups rather than the source itself.

## Similar projects

- **Karpathy's "LLM Wiki"** (gist, around April 2026; the gist itself was not
  fetched, **unverified**). An LLM maintains an interlinked markdown wiki from raw
  sources, with Ingest, Query and Lint operations, steered by a CLAUDE.md or
  AGENTS.md schema file, and Obsidian as the viewer. It uses no vector search.
  This is probably what you heard about. It strains at large corpora, which is
  why this project adds an index.
- **Khoj** (github.com/khoj-ai/khoj): maintained, a full self-hosted "second
  brain" app with an Obsidian plugin. A whole app, not a YouTube pipeline.
- **basic-memory** (github.com/basicmachines-co/basic-memory): maintained,
  markdown knowledge graph over MCP, Obsidian-compatible. Good for agent notes.
- **Smart Connections** (Obsidian plugin): maintained, local embeddings inside
  Obsidian, aimed at people rather than agents.
- **QMD** (github.com/tobi/qmd, **unverified**): BM25 + vectors + LLM rerank over a
  folder of markdown, with CLI and MCP. The closest ready-made search layer; it
  could index this project's `wiki/` folder as an alternative to the built-in index.
- **Reor**: archived. Do not build on it.
- **Obsidian MCP servers**: several exist. The ones that read files directly
  (for example bitbonsai/mcpvault) work without Obsidian running.
- **YouTube-to-vault tools** (**unverified**, from snippets): several small
  scripts and agent skills fetch captions into notes. None found does chapter
  splitting, per-section pages and embeddings together.

## Is Obsidian the right tool?

As a viewer, yes. A vault is a folder of `.md` files, so the pipeline writes
files and Obsidian is optional: graph view, backlinks and Dataview work on the
output for free. Agents do not need it. The MCP servers that go through
Obsidian's REST plugin need the app open.

## Component choices

- **yt-dlp**: still the standard. YouTube now needs a JavaScript runtime
  (deno by default, node works) and sometimes cookies.
- **Transcription**: faster-whisper is the usual local choice. NVIDIA Parakeet
  TDT 0.6B v3 is reported as more accurate for English (**unverified**, vendor
  benchmarks). Either fits behind the `Transcriber` interface.
- **Embeddings** (context windows checked against the model cards on Hugging Face):

  | model | context | dims | licence, access |
  | --- | --- | --- | --- |
  | Qwen/Qwen3-Embedding-0.6B / 4B / 8B | 32K | 1024 / 2560 / 4096, Matryoshka | Apache 2.0, ungated |
  | google/embeddinggemma-2 (Gemma 4 based, Oct 2026) | 8K | 768, Matryoshka to 128 | Apache 2.0, ungated; text, image, audio, video |
  | nomic-embed-text-v1.5, BAAI/bge-m3, jina-embeddings-v3 | 8K | 768-1024 | various |
  | google/embeddinggemma-300m (Gemma 3 based) | 2K | 768 | gated, manual approval |

  A 40 minute talk is about 9K tokens, so only the Qwen3 models take a whole
  video in one pass. EmbeddingGemma 2 can also embed audio directly, which a
  future `Embedder` could use to skip transcription for search (untried).
  The raw Gemma 4 chat model is not an embedding model.
- **Index**: SQLite FTS5 + vectors with reciprocal rank fusion is the common
  low-friction choice for one person's corpus; sqlite-vec, LanceDB, Chroma and
  Qdrant are the usual upgrades.
- **Agent access**: MCP for Claude Code and desktop agents, a CLI with JSON
  output for anything that can run commands. This project has both.
- **Channel monitoring**: the RSS feed
  (`youtube.com/feeds/videos.xml?channel_id=...`) shows about the newest 15
  uploads; yt-dlp's channel listing covers the full backlog. This project uses
  yt-dlp for both and keeps its own processed-ID table.
