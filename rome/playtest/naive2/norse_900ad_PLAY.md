# Playtest: norse_900ad, fog of war ON

Agent-mode JSON protocol, session file `norse_900ad_PLAY.json`.
Notes written as I go.

## Setup

Started with:

    python3 rome/sim/simulator.py agent --civ norse_900ad --fog \
        --session /home/user/test/rome/playtest/naive2/norse_900ad_PLAY.json

The welcome banner is genuinely good — it tells me the premise in one
paragraph ("You are one person, dropped into a pre-industrial society,
carrying the knowledge of how modern technology works but none of the
industry that makes it"), lists every command, and is explicit that
"Knowing how a thing works is free. Building it is not". Horizon is 1400,
start 900, so 500 years. "There is no score but the state of what you
have built."

Fog of war: "You can see what you have built, what you could begin today
as a one line summary, and things you have heard of but cannot yet
begin. You cannot see where anything leads, and there is no way to view
the whole tree." `path` is disabled under fog.

