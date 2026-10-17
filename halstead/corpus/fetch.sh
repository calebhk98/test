#!/bin/sh
# Rebuild the 23-book reference corpus from Project Gutenberg.
#
# The measures that need raw text (tics, number_report, quotable, quote_length)
# read every *.txt in this directory. They are not committed by default: see
# PROVENANCE.md for why, and run this to restore them.
#
#   sh halstead/corpus/fetch.sh
#
# Verify afterwards with:
#   python3 measures/prose_grade.py --build-reference corpus --reference /tmp/check.json
# and diff /tmp/check.json against prose_reference.json. 19 of 23 books should
# reproduce every metric exactly.
set -e
cd "$(dirname "$0")"
sed -n 's/^| \([0-9][0-9]*\) | \([A-Za-z_]*\) |$/\1 \2/p' PROVENANCE.md | while read id name; do
  [ -s "$name.txt" ] && { echo "have   $name"; continue; }
  echo "fetch  $name (pg$id)"
  curl -sSL --retry 4 --retry-delay 2 -o "$name.txt" \
    "https://www.gutenberg.org/cache/epub/$id/pg$id.txt"
done
echo "$(ls -1 *.txt 2>/dev/null | wc -l) books present"
