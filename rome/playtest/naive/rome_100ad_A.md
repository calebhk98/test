# Playtest notes — rome_100ad_A

Playing "Rome 100ad" simulator, fog of war on. Rules I'm following: only look at
what the running game tells me, never read the repo source/docs. Session file:
rome/playtest/naive/rome_100ad_A.json

## Session log

### Start
Launched the simulator. It printed a welcome block explaining the premise:
I'm one person in 100 AD Rome with modern knowledge but no modern industry.
Building things costs my hours, other people's hours, money, materials, years.
Goal: advance as far as possible before the horizon at 600 AD. No score, just
what you've built.

Commands: state, available, why <id>, start <id>, stop <id>, step <years>, buy,
bounty <id>, path <id> (disabled under fog), save/load, help, quit.

Economy: buy forest (hectares of coppice -> charcoal), buy mine (tonnes/year,
takes years to sink), buy slaves, manumit (free slaves - "the decent thing").

First reaction: interesting that slavery is modeled explicitly and manumission
is editorialized in the help text itself ("it is the decent thing"). Notable
design choice to put a moral valence in the tool description rather than
leaving it neutral.
