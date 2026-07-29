#!/bin/sh
# Mechanical register check. Run on a turn directory before any review agent reads it.
# Counts the tells that v2 failed on. These are counts, not judgements.
#
# usage: sh register-check.sh v3/turn-525-550

DIR="${1:-.}"

for f in "$DIR"/*.md; do
  [ -f "$f" ] || continue
  echo "=== $f"
  printf '  words                 %s\n' "$(wc -w < "$f")"
  printf '  em-dash (—)           %s\n' "$(grep -o '—' "$f" | wc -l)"
  printf '  spaced double hyphen  %s\n' "$(grep -oE ' -- ' "$f" | wc -l)"
  printf '  "is not X; it is"     %s\n' "$(grep -oiE 'is not [^.;]{1,40}(; it is|, it is|\. It is)' "$f" | wc -l)"
  printf '  "not X but Y"         %s\n' "$(grep -oiE 'not (a|an|the|merely|simply)? ?[a-z]+,? but ' "$f" | wc -l)"
  printf '  semicolons            %s\n' "$(grep -o ';' "$f" | wc -l)"
  printf '  bold+italic lines     %s\n' "$(grep -cE '\*\*\*|_\*\*' "$f")"
  printf '  "which is why"        %s\n' "$(grep -oi 'which is why' "$f" | wc -l)"
  printf '  "precisely"           %s\n' "$(grep -oi 'precisely' "$f" | wc -l)"
  printf '  "the real question"   %s\n' "$(grep -oi 'the real question' "$f" | wc -l)"
  printf '  first person (we/our) %s\n' "$(grep -owiE 'we|our|us' "$f" | wc -l)"
done
