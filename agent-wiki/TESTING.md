# What has been tested, and how

Run on a cloud machine: 4 CPU cores, 15.7 GB RAM, no GPU, October 2026.

## Real components, real data

| piece | test | result |
| --- | --- | --- |
| yt-dlp source, YouTube | metadata for an AI Search video | works with `player_clients = ["web_safari", "web_embedded"]`; the default clients hit "confirm you're not a bot" from this IP |
| yt-dlp source, YouTube | audio download | refused (HTTP 403) from this IP even when metadata worked; then rate limited (429) for hours. Untested from a home connection |
| block handling | real 429 from YouTube | run stopped, video kept queued with its retry budget, exit code 5 |
| podcast source | Practical AI RSS feed, 2 episodes (47 and 48 min) | feed, chapters (`podcast:chapters`), sponsor chapters, audio download all worked |
| faster-whisper, `model = "auto"` | 95 minutes of real speech | picked `small` on this CPU; about 4x faster than real time (47 min in 11.3 min); accurate apart from names ("Klein" heard as "Client") |
| chapter splitting | podcast chapters | 15 and 17 sections, sponsor chapters flagged and kept out of search |
| topic splitting (no chapters) | same episodes with chapters hidden, scored against the real chapters | finds about 80% of real chapter boundaries within 60 s; about 60% of its cuts match a real boundary, the rest split long chapters into sub-topics |
| Qwen3-Embedding-0.6B | indexing, search, whole-video single-pass vectors | works on CPU; search questions return the right sections first |
| local enricher (no LLM) | both episodes | topic categories correct after one fix (see below); facts found by pattern include "Flux 2 was a 32B model", "4k generations up to 15 seconds", "the weights were open"; extractive summaries readable but conversational |
| LLM unreachable | Ollama configured, not running | both episodes finished with local enrichment, marked degraded |
| automatic upgrade | switched to the in-process LLM, ran `run` | both degraded episodes requeued from cache, re-enriched, no download |
| in-process LLM, `model = "auto"` | Qwen2.5-1.5B picked for 15.7 GB RAM, CPU | about 43 s per section; good summaries, some invented detail, dropped a number the pattern matcher caught (now merged) |
| `ask` | in-process LLM, 4 sources | sensible answer in 41 s; the 1.5B model does not cite inline |
| reprocess from cache | `reprocess --from enrich` after changing the enricher | re-enriched and re-indexed both episodes in 3.5 min, no download or transcription |

Fixes that came out of the real run: key-phrase tags allowed filler words
inside phrases and broke possessives; long chapter titles became tags;
summaries picked the host's questions; category scoring ranked
`3d-generation` above `text-to-image` for an image-generation talk
(fixed by scoring categories as queries); topic splitting over-cut and gave
every part of a video the same title.

## Not tested here

- A full YouTube download and Whisper transcription of an AI Search video
  (blocked from this IP). The YouTube metadata, chapters and description
  parsing were tested on the real metadata.
- Any GPU path: CUDA batching, half precision, Gemma 4 sizes above 1.5B.
- Ollama, llama.cpp and other servers (no server here), the Anthropic backend,
  the MCP server (needs the `mcp` package and a client).
- EmbeddingGemma 2. Windows and Android.

## Unit tests

`pytest` runs 27 offline tests with fakes for download and transcription and
the saved metadata of a real AI Search video.
