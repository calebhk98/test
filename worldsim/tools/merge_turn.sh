#!/usr/bin/env bash
# merge_turn.sh — append a period's DM-approved, player-voice slice into the ongoing canon.
# Runs ONLY after the DM has adjudicated and redlined; it is a mechanical append, not a writer.
#
# Usage: tools/merge_turn.sh <period> <nation>
#   e.g. tools/merge_turn.sh 50-100AD china
#
# Expects, in worldsim/turns/<period>/<nation>/:
#   canon.md       (required) the adjudicated HISTORY slice in the nation's own voice
#   state.md       (optional) the full replacement STATE for this nation
#   knowledge.md   (optional) newly-perceived facts to append to KNOWLEDGE
# Appends canon.md under a "## <period>" header in players/<nation>/HISTORY.md,
# overwrites STATE.md if state.md is present, and appends knowledge.md if present.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # worldsim/
period="${1:?period required, e.g. 50-100AD}"
nation="${2:?nation required, e.g. china}"

turn_dir="$ROOT/turns/$period/$nation"
player_dir="$ROOT/players/$nation"
canon="$turn_dir/canon.md"

[[ -d "$player_dir" ]] || { echo "ERROR: no such nation: $player_dir" >&2; exit 1; }
[[ -f "$canon" ]]      || { echo "ERROR: missing $canon (adjudicate + redline first)" >&2; exit 1; }

{ printf '\n\n## %s\n\n' "$period"; cat "$canon"; } >> "$player_dir/HISTORY.md"
echo "merged canon -> $player_dir/HISTORY.md (## $period)"

if [[ -f "$turn_dir/state.md" ]]; then
  cp "$turn_dir/state.md" "$player_dir/STATE.md"
  echo "replaced       -> $player_dir/STATE.md"
fi
if [[ -f "$turn_dir/knowledge.md" ]]; then
  { printf '\n\n## %s (newly perceived)\n\n' "$period"; cat "$turn_dir/knowledge.md"; } >> "$player_dir/KNOWLEDGE.md"
  echo "appended       -> $player_dir/KNOWLEDGE.md (## $period)"
fi
