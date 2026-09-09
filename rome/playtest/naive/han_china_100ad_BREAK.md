# Breaking han_china_100ad (fog of war)

Session file: /home/user/test/rome/playtest/naive/han_china_100ad_BREAK.json
Invocation:
```
cd /home/user/test
python3 rome/sim/simulator.py agent --civ han_china_100ad --fog --session /home/user/test/rome/playtest/naive/han_china_100ad_BREAK.json
```

Protocol: one JSON object per line on stdin, one JSON reply per line on stdout.
Since --session persists to a file, each bash invocation below pipes a batch of
JSON lines in via stdin (heredoc) and the process exits at EOF, so I can drive
it turn-by-turn across many `Bash` calls without holding a live pty open.

## Startup banner (first run, empty stdin)

Command: ran with `< /dev/null`, i.e. immediately closed stdin.

Reply (the welcome/help blob) - not reproduced in full here, see below for key facts:
- commands: state, available, why <id>, start <id>, stop <id>, step <years>, buy,
  bounty <id>, path <id> (disabled under fog), save <file>, load <file>, help, quit
- buy: forest (hectares of coppice), mine (material+tonnes/yr), slaves (n), manumit (n)
- fog of war: ON. Can see built things + one-line summaries of what's startable +
  "heard of but not startable" things. Cannot see tech tree destinations. path
  disabled.
- "Knowing how a thing works is free. Building it is not."
- Starts in year 100, horizon year 600, no numeric score, goal is "how far you get".
- Charged for food, rent, appearances every year regardless of activity.

---

## Log

(entries added chronologically as testing proceeds)
