# Playtest notes: mexica_1500, fog of war, naive3

Session file: /home/user/test/rome/playtest/naive3/mexica_1500_PLAY.json
Command: `python3 rome/sim/simulator.py agent --civ mexica_1500 --fog --session .../mexica_1500_PLAY.json`

Format: I write EXPECTATION (what I think a command will do/cost/unlock and why)
before running it, then ACTUAL (what happened), then a note if I was surprised.

## Setup / orientation

Ran `{"cmd":"help"}` with no args first to read the welcome text. Key lines quoted:

- "You are one person, dropped into a pre-industrial society, carrying the knowledge
  of how modern technology works but none of the industry that makes it. You are
  playing The Mexica Triple Alliance, beginning in 1500. Knowing how a thing works is
  free. Building it is not: it takes your own hours, other people's hours, money,
  materials, and years."
- "You begin projects, then advance time. Nothing happens unless you make it. You are
  charged for food, rent and appearances every year whether or not you are building
  anything."
- "Advance as far as you can before the horizon at 2000. There is no score but the
  state of what you have built."
- "No employees, no slaves, nobody who owes you anything. Anyone who works for you is
  hired, taught, commissioned or bought."
- The four core commands: `state`, `available`, `why <id>`, `step <years>`.

Next: reading the other help topics (commands, labour, economy, money, automatic,
sittings, fog) before doing anything that costs money or time.
