"""How many verbs a sentence carries, book against corpus.

A predicate is a VERB or AUX token that is not itself an auxiliary hanging off
another verb, which is as close to "how many things this sentence says happen"
as a small parser gets. Modal + participle ("has been taught") counts once.
"""
import glob, re, statistics as st, sys
from pathlib import Path
import spacy

HERE = Path("/home/user/test/halstead")
CORPUS = ["/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/scratchpad/agent_gutenberg/raw",
          "/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/scratchpad/agent_modern/texts"]
SLICE = 90000  # characters sampled from the middle of each reference book

nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
nlp.max_length = 2_000_000
AUXDEP = {"aux", "auxpass"}

def strip_gut(t):
    m = re.search(r"\*\*\* ?START OF.*?\*\*\*(.*?)\*\*\* ?END OF", t, re.S)
    return m.group(1) if m else t

def measure(text):
    text = re.sub(r"\s+", " ", text)
    counts, coord, words = [], [], 0
    for doc in nlp.pipe([text[i:i+90000] for i in range(0, len(text), 90000)]):
        for s in doc.sents:
            toks = [t for t in s if not t.is_punct and not t.is_space]
            if len(toks) < 3:
                continue
            v = sum(1 for t in s if t.pos_ in ("VERB", "AUX") and t.dep_ not in AUXDEP)
            counts.append(v)
            coord.append(sum(1 for t in s if t.dep_ == "conj" and t.pos_ in ("VERB", "AUX")
                             and t.head.pos_ in ("VERB", "AUX")))
            words += len(toks)
    n = len(counts)
    if not n:
        return None
    return {
        "sentences": n,
        "words/sent": words / n,
        "verbs/sent": sum(counts) / n,
        "verbs/100w": 100 * sum(counts) / words,
        "1 verb %": 100 * sum(1 for c in counts if c == 1) / n,
        "2+ verbs %": 100 * sum(1 for c in counts if c >= 2) / n,
        "3+ verbs %": 100 * sum(1 for c in counts if c >= 3) / n,
        "coord verbs/sent": sum(coord) / n,
        "sents w/ coord %": 100 * sum(1 for c in coord if c) / n,
        "5+ verbs %": 100 * sum(1 for c in counts if c >= 5) / n,
    }

book = measure("\n".join(Path(f).read_text() for f in sorted(glob.glob(str(HERE/"chapters"/"*.md")))))
ref = []
for d in CORPUS:
    for f in sorted(Path(d).rglob("*.txt")):
        if "stripped" in f.stem:
            continue
        t = strip_gut(f.read_text(encoding="utf-8", errors="replace"))
        if len(t) < 40000:
            continue
        mid = max(0, len(t)//2 - SLICE//2)
        r = measure(t[mid:mid+SLICE])
        if r:
            ref.append((f.stem, r))
        print("  ...", f.stem, file=sys.stderr)

keys = [k for k in book if k != "sentences"]
print(f"\n{len(ref)} reference books, {SLICE//1000}k characters sampled from the middle of each.\n")
print(f"  {'measure':<14}{'book':>9}{'corpus med':>12}{'corpus min':>12}{'corpus max':>12}{'ratio':>8}")
print("  " + "-"*67)
for k in keys:
    vals = sorted(r[k] for _, r in ref)
    med = st.median(vals)
    print(f"  {k:<14}{book[k]:>9.2f}{med:>12.2f}{min(vals):>12.2f}{max(vals):>12.2f}{book[k]/med:>8.2f}x")

print(f"\n  book sentences measured: {book['sentences']}")
print("\n  per reference book, verbs per sentence:")
for name, r in sorted(ref, key=lambda x: -x[1]["verbs/sent"]):
    print(f"    {name[:38]:<40}{r['verbs/sent']:>6.2f}{r['2+ verbs %']:>8.1f}%{r['words/sent']:>8.1f}")
