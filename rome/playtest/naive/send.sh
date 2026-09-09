#!/bin/bash
# usage: send.sh '<json>'
LINES_BEFORE=$(wc -l < game.out)
echo "$1" > control.fifo
# wait for output to grow
for i in $(seq 1 50); do
  sleep 0.2
  LINES_AFTER=$(wc -l < game.out)
  if [ "$LINES_AFTER" -gt "$LINES_BEFORE" ]; then
    sleep 0.3
    break
  fi
done
tail -n +$((LINES_BEFORE+1)) game.out
