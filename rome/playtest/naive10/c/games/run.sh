#!/bin/bash
# usage: run.sh <name> <<< commands  (reads cmds from stdin)
NAME=$1; shift
cat > /tmp/cmds_$NAME.txt
cd /home/user/test/rome/playtest/naive10/c/games
timeout 900 python3 /home/user/test/rome/sim/simulator.py < /tmp/cmds_$NAME.txt 2>&1
