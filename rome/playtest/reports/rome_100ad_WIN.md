# rome_100ad / WIN

## STATUS: IN PROGRESS - plan written before play, will be updated as I go.

## Plan
Goal: reach `point_contact_transistor` as early as possible, playing straight (no exploits,
honest baseline). Civ: rome_100ad. Protocol only, via
`python3 rome/sim/simulator.py agent --civ rome_100ad`, driven by a small Python driver script
I will write to pipe JSON lines in and read replies, so I can hold hundreds of decisions without
hand-typing each one, while still making every "what to build" decision myself from
`available`/`why`/`path` output (no reading strategies/tech tree JSON to plan; no load_strategy).

Before playing I read:
- rome/playtest/BRIEF.md (the hard rule: JSON protocol only)
- rome/knowledge/03_SOCIAL_POLITICS.md — the assigned early read. Key takeaway: the technical
  dependency graph and the "real" (social/political) dependency graph differ. Success is claimed
  to be 0% without the social-politics module nodes (identity_cover -> patron_local ->
  citizenship -> freedman_staff -> collegium_licensed -> school_founded -> ...). School founding
  date is called the single highest-leverage decision in the game: founding it late costs more
  than 1:1 in years downstream because it compounds through every later node's labor pool.
  freedman_staff (buy+train+manumit) is presented as the *legitimate* route to a technical
  workforce, contrasted against a raw buy-slaves-and-manumit path called out as an exploit in a
  prior WEIRD-role report already patched in git history (397b2ab). As I'm playing straight I
  intend to use freedman_staff, not raw slave buy/manumit spam.
- Skimmed prior playtest reports rome_100ad_BREAK.md and rome_100ad_WEIRD.md for context (both
  found an already-patched slave/manumit exploit; not relevant to a straight play but good to
  know the exploit existed and is supposedly fixed).

Plan of attack:
1. Start the simulator, check `state` and `available`.
2. Use `path` on `point_contact_transistor` to see the full remaining dependency list at the
   start, and re-run it periodically to track progress and catch surprises.
3. Follow the social-politics chain early (identity_cover, patron_local, citizenship,
   freedman_staff, collegium_licensed, school_founded) per the knowledge doc's strong claim that
   skipping it is a guaranteed loss, while also picking up cheap/early technical prerequisites
   opportunistically via `available`/`why` so I'm not purely following the knowledge doc as a
   script (I will still reason from the game's own output, not from the doc, for order/timing).
4. Watch `state.living_cost` / `net_per_year` every few steps so I don't stall from running out
   of capital while founder_hours are committed to a long project.
5. Log findings below as I hit them: playability, surprises, anything misleading, anything
   punishing for the wrong reasons.

## What I did
(to be filled in as I play)

## Result
(to be filled in)

## FINDINGS
(to be filled in)
