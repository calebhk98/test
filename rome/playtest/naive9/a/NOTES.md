# Playtest notes - naive9/a

(Playing blind: no source, no docs. Notes appended as I go.)

## Session 1 - first contact

Title screen: "ONE PERSON, AND EVERYTHING THEY KNOW". Nice premise, clearly written.
Five settings offered (Han 100, Rome 100, Viking 900, England 1300, Mexica 1500).

Immediate annoyance: when I piped an empty line in, it printed
    Which one? [1-5, or q to leave]    -- a number from 1 to 5.
    Which one? [1-5, or q to leave]
i.e. the error message is appended on the SAME line as the prompt, which reads oddly.

## Session 1 - opening moves (Rome, poor_scholar, fog on, no aging)

Goal revealed by `help`: "Build point-contact transistor, before the horizon at 600."
`why point_contact_transistor` is a great screen - it shows the full bill (33,970 den,
25 scholars, 20 artisans, 900 of my hours) and says "this needs 7 other things you have
not heard of yet". Good hook.

Things that worked well / pleasant surprises:
- `available all` gives a table with COST/HOURS/YEARS/RISK/EARNS/UPKEEP/STAFF, which is
  enough to do real ROI arithmetic. That is the best thing in the game so far.
- `money` ledger itemises revenue per concern and literally says "these add up to the
  revenue above" - very trustworthy.
- `risk` listing historical hazards with dates and "what would help" is excellent.
- The game auto-saves after every command and tells you the resume command. Nice.

Confusions / problems:
1. `state` uses the word RUNNING for two different things: "RUNNING (5)" = projects
   under construction, and "RUNNING AS CONCERNS: 1" = things earning money. I read the
   first as "these are earning" for a while. Suggest "BUILDING" vs "RUNNING".
2. `why <id>` does NOT mention that OPENING a finished thing costs money again.
   `why tex_horizontal_loom` said COST 225.8; after it completed, `ventures` showed a
   "TO OPEN 33.9" column I had never been told about. Small, but it is a hidden cost.
3. After my first `step`, I got:
      COMPLETED 100: Amphitheatre with tiered seating
      COMPLETED 100: Barrel vault
      COMPLETED 100: Rigid padded horse collar...
   I never started an amphitheatre or a barrel vault. I assume these are free
   "granted" techs the civ already has, but the log calls them COMPLETED next to the
   thing I actually built, which is misleading.
4. `quote hire artisan 1` -> "REFUSED: no such material: 'hire'. Mineable: coal, ...".
   `help commands` says "quote <what>: what something would cost before you commit to
   it; so far quote mine coal 500". So `quote` is really `quote mine`. The error
   message talks about materials, which is a confusing thing to be told when you asked
   about hiring.
5. Every fresh run writes a NEW session file into the repo root
   (rome_100ad_2.json ... rome_100ad_21.json). Twenty exploratory launches left twenty
   files lying around. It should reuse one, or put them somewhere.
6. The very first prompt, when fed a blank line, renders as
      Which one? [1-5, or q to leave]    -- a number from 1 to 5.
   the complaint is glued to the end of the prompt line.
7. Scandal appeared out of nowhere: after one `step` STANDING went from
   "scandal 0" to "scandal 4.1" with no event line explaining why. Nothing in the
   step output said I had done anything scandalous.
