#!/usr/bin/env python3
"""Repair the JSON syntax faults branch authors actually make, then report what
materials and trades they asked for that the price list does not know about.

Silently dropping an unpriced material makes a technology look cheaper than it
is, which is worse than failing loudly, so this reports rather than deletes.
"""
import json, re, glob, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BR = os.path.join(ROOT, "data", "branches")

FIXES = [
    # a stray quote closing a numeric value:  "brass_kg": 15"}
    (re.compile(r'(:\s*-?\d+(?:\.\d+)?)"(\s*[},])'), r'\1\2'),
    # trailing comma before a close
    (re.compile(r',(\s*[}\]])'), r'\1'),
    # a bare fraction like 1/2 used as a number
    (re.compile(r':\s*(\d+)\s*/\s*(\d+)([,}])'), lambda m: ": %s%s" % (int(m.group(1)) / int(m.group(2)), m.group(3))),
]

def repair():
    fixed, broken = [], []
    for f in sorted(glob.glob(os.path.join(BR, "*.json"))):
        txt = open(f).read()
        new = txt
        for pat, rep in FIXES:
            new = pat.sub(rep, new)
        if new != txt:
            open(f, "w").write(new)
            fixed.append(os.path.basename(f))
        try:
            json.load(open(f))
        except Exception as e:
            broken.append((os.path.basename(f), str(e)))
    return fixed, broken

def survey():
    p = json.load(open(os.path.join(ROOT, "data", "prices.json")))
    goods = set(k for k in p["purchase_prices_denarii"] if not k.startswith("_"))
    wages = set(k for k in p["wage_rates_denarii_per_hour"] if not k.startswith("_"))
    mats, trades = collections.Counter(), collections.Counter()
    for f in glob.glob(os.path.join(BR, "*.json")):
        try:
            batch = json.load(open(f))
        except Exception:
            continue
        for n in batch:
            for m in n.get("mat", {}):
                if m not in goods:
                    mats[m] += 1
            for t in n.get("lab", {}):
                if t not in wages:
                    trades[t] += 1
    return mats, trades

if __name__ == "__main__":
    fixed, broken = repair()
    print("repaired: %s" % (", ".join(fixed) or "nothing"))
    for f, e in broken:
        print("STILL BROKEN  %-28s %s" % (f, e))
    mats, trades = survey()
    print("\nunknown trades   : %s" % dict(trades.most_common()))
    print("unknown materials: %d distinct, %d references" % (len(mats), sum(mats.values())))
    for k, v in mats.most_common(80):
        print("   %-30s %d" % (k, v))
    sys.exit(1 if broken else 0)
