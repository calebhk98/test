# Project: the Rome novel (working title *The Long Way Home*)

A novel written by many subagents, coordinated through canon files so no single
agent ever needs the whole book in context. This README is the map and the
status board.

## How the pipeline works
1. **Canon lives in `bible/`.** It is the single source of truth. Writers and
   reviewers read only the few files they need.
2. **The plan lives in `outline/`.** `master_outline.md` is the spine;
   `chapter_list.md` has a one-line brief and a status for every chapter.
3. **A writer subagent** drafts one chapter (or a small batch). It is told which
   bible files to read and is given the previous chapter's *summary* (not its
   full text) for continuity. It writes to `chapters/chNN.md`.
4. **A QA subagent** reviews the draft against `AGENT_RULES.md` and the canon.
   It writes a verdict to `qa/chNN_review.md` (PASS / REVISE + specifics).
5. **The coordinator** (top-level) updates `bible/08_canon_log.md` with any new
   established facts, marks the chapter status, commits, and pushes.

## Rules of the road for the coordinator
- Commit and push after every accepted chapter or batch. The container is
  ephemeral; unpushed work is lost work.
- Keep `08_canon_log.md` current. It is what prevents continuity drift.
- Never let an agent summarize a scene instead of writing it. That is "cheating"
  and is grounds for rejection.

## File map
- `AGENT_RULES.md` - writing law (anti-AI-tells, craft). Everyone reads it.
- `AGENT_WRITER_BRIEF.md` - the standing instructions handed to writer agents.
- `AGENT_QA_BRIEF.md` - the standing instructions handed to QA agents.
- `bible/00_premise.md` - logline, theme, the argument, tone, hard constraints.
- `bible/01_world.md` - Rome 98-138 AD canon (from research).
- `bible/02_characters.md` - roster and profiles.
- `bible/03_timeline.md` - master chronology (plot time) vs real history.
- `bible/04_tech_schedule.md` - what tech, when, how framed, what's "bait."
- `bible/05_world_rules.md` - the hard rules (phone lifespan, Latin acquisition,
  germ framing, no magic, limits on Daniel's knowledge).
- `bible/06_style_guide.md` - POV, tense, voice, mechanics.
- `bible/07_glossary.md` - Latin/invented terms, names, pronunciations.
- `bible/08_canon_log.md` - running log of facts established IN the prose.
- `research/` - raw research dumps (history, tech feasibility). Reference only.

## STATUS BOARD
- [x] Foundational docs (premise, style, agent rules, README, briefs)
- [x] Research ingested (history + tech feasibility)
- [x] World bible
- [x] Characters
- [x] Timeline
- [x] Tech schedule
- [x] World rules
- [x] Glossary
- [x] Master outline + chapter list (53 chapters, 7 parts + epilogue)
- [ ] Chapters drafted: 4 / 53
- [ ] Chapters accepted: 4 / 53

Update the counts as work proceeds.
