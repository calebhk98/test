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

## Second round: the real AI Search video, and dedicated models

YouTube still refused this IP, so the audio came from a YouTube-to-MP3
website (mp3youtube.cc), used in a headless browser the way a person uses it:
paste the link, click download. Sites that sit behind Cloudflare Turnstile or
sign their requests with obfuscated code were skipped rather than worked
around. The MP3 went into the `local-audio` source's folder, with metadata
from the earlier YouTube fetch.

| piece | result |
| --- | --- |
| the 40:29 AI Search video, end to end | 28 chapters, links matched, Luma flagged as sponsor, whole-video vector in one 32K pass; 13m53s on 4 CPU cores |
| "fastest text to world model with a consistent world" | Inspatio World 1.5 first, the right answer in that video |
| "good text to video models, sizes, censored" | weak with one video (a speech model ranked second); `--tag text-to-video` returned the right sections |
| facts without an LLM | "based off of 1.3b and this is only less than 6GB in size so you should be able to fit this on most consumer GPU"; GLiNER2 mislabelled that 6GB as a model size |

Topic tagging, 12 hand-labelled podcast sections (labels are my judgment):

| method | precision | recall | F1 | CPU time |
| --- | --- | --- | --- | --- |
| embedding zero-shot (Qwen3-Embedding-0.6B) | 44% | 58% | 0.50 | 1.2 s/section |
| GLiNER2.5 base classification, threshold 0.4 | 30% | 84% | 0.44 | 1.1 s |
| GLiNER2.5 base classification, threshold 0.6 | 32% | 68% | 0.43 | 1.2 s |
| NLI zero-shot, DeBERTa-v3-large | 83% | 26% | 0.40 | 49 s (busy CPU) |

None is good at topics on conversational speech. GLiNER2 is much better at
names (models, companies: "Flux 2" 0.95, "Black Forest Labs" 1.00), so the
`models` preset uses it for names and embeddings for topics.

Summaries, same four AI Search sections: DistilBART (a summarization-only
model) was the most informative, about 4 s a section; the in-process 1.5B LLM
was vaguer at 30-40 s; extractive quotes were fast but read like speech.
transformers 5 removed the `summarization` pipeline, so the model is loaded
directly.

## Scale

Measured here (4 CPU cores, another job running at the same time, so upper bounds):

| wiki size | index on disk | first search in a new process | later searches |
| --- | --- | --- | --- |
| 300 videos (9,300 chunks) | 71 MB | 0.6 s | 0.03 s |
| 1,000 videos (31,000 chunks) | 237 MB | 0.35 s | 0.15 s |
| 5,000 videos (155,000 chunks) | 1.2 GB | 6.1 s | 0.6 s |

Synthetic indexes with 1024-dim vectors, 31 chunks per video as the real AI
Search video produced. Each CLI call reloads the vectors; the MCP server keeps
them in memory. Past a few thousand videos, a `VectorIndex` on sqlite-vec or
LanceDB, or `dimensions = 512` on the embedder, would be the next step.

The real 40 minute video cost about 0.65 MB of index, 0.2 MB of cached stage
files and 0.2 MB of markdown (30 pages). Before a fix in this round, its cached
metadata was 10.8 MB, almost all auto-caption URLs for 176 languages; it is
now 15 KB.

AI Search had 428 uploads, 207 hours in total, when listed. On this 4-core CPU
a 40 minute video took about 14 minutes end to end with Whisper `small`, so a
full backfill would take roughly three days of CPU time. GPU speed was not
measured.

## Not tested here

- A full YouTube download and Whisper transcription of an AI Search video
  (blocked from this IP). The YouTube metadata, chapters and description
  parsing were tested on the real metadata.
- Any GPU path: CUDA batching, half precision, Gemma 4 sizes above 1.5B.
- Ollama, llama.cpp and other servers (no server here), the Anthropic backend,
  the MCP server (needs the `mcp` package and a client).
- EmbeddingGemma 2. Windows and Android.
- The `llm` preset with a real LLM after this restructure (the scripted test LLM covers the code path).

## Unit tests

`pytest` runs 33 offline tests with fakes for download and transcription and
the saved metadata of a real AI Search video.
