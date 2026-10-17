# agent-wiki

A searchable markdown wiki built from YouTube videos and podcasts. Design in
ARCHITECTURE.md, real-world test results in TESTING.md.

## Names

Every name says what it holds. No names under three characters, including
loop counters, comprehension variables, lambda arguments and exception
variables: `for section in sections`, `for position, chapter in
enumerate(chapters)`, `except OSError as error`. No unexplained
abbreviations (`video_id`, not `vid`; `embedder`, not `emb`). The only short
names allowed are ones fixed by an outside interface, such as the CLI's `-k`
flag or yt-dlp's own option keys.

## Swappable, not hard-coded

Every model or method choice is a class registered with `@register(kind,
name)` and picked by `type` in config.toml. A new backend is a new class;
it never means editing the pipeline. Defaults (prompts, patterns, category
lists, thresholds) are constructor arguments so config can override them.

## Before committing

`python3 -m pytest -q` from this folder. Any change to enrichment, splitting
or search quality gets checked on real data too, and the result goes in
TESTING.md, including when it is worse.
