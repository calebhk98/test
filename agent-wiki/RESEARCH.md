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
- **Embeddings**: EmbeddingGemma (308M, 768 dims, Matryoshka down to 128,
  built on Gemma 3) is confirmed on Google's docs page. The same page describes
  a Gemma 4 based "EmbeddingGemma 2" (multimodal, 768 dims) but with
  inconsistent parameter counts and no date, so check the model card before
  switching. The raw Gemma 4 chat model is not an embedding model.
- **Index**: SQLite FTS5 + vectors with reciprocal rank fusion is the common
  low-friction choice for one person's corpus; sqlite-vec, LanceDB, Chroma and
  Qdrant are the usual upgrades.
- **Agent access**: MCP for Claude Code and desktop agents, a CLI with JSON
  output for anything that can run commands. This project has both.
- **Channel monitoring**: the RSS feed
  (`youtube.com/feeds/videos.xml?channel_id=...`) shows about the newest 15
  uploads; yt-dlp's channel listing covers the full backlog. This project uses
  yt-dlp for both and keeps its own processed-ID table.
