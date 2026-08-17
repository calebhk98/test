# What the character sheets will do to a reading-level pass

Four reviews, one per group, are in `CORE_SEVEN.md`, `OTHER_STUDENTS.md`, `STAFF.md`
and `ADULTS.md`. They were run separately and did not see each other's work. They
reached the same conclusion, which is the reason to trust it.

## The finding

The book sits at the 22nd percentile for reading maturity and loses to all 23
books in the comparison corpus on all twelve measures. The three devices that
most reliably carry a subordinate clause are figurative language, hedging, and
humour. **All three are ruled out, by name, across most of the cast.**

Counted directly from the dial tables in the 32 sheets:

| device | sheets that rule it out |
| :-- | --: |
| figurative language | 22 of 32 |
| hedging, at 0% | 25 of 32 |
| jokiness, at 0/10 | 16 of 32 |

Nineteen sheets rule out at least two of the three. Fourteen rule out all three,
and those fourteen are almost the entire adult cast: every Halstead teacher with
dialogue, and every outside adult with dialogue.

This is not a set of characters who happen to be terse. It is a rule, repeated
across the cast, against the specific grammar a maturity pass produces. A pass
that raises the register will contradict a written rule on almost every page it
touches, and whoever runs it will either break the characters or give up.

## Where it came from

The dial tables were filled in by measuring the manuscript. The manuscript is
flat, so the dials came back flat, and the flatness was then written down as
character. The sheets are an accurate description of a fourth-grade-reading-level
book, promoted into a specification for one.

Two sheets say so almost outright:

- `KAVI.md:52` rules out "ordinary conversational length, one or two medium
  sentences of six to fourteen words" and calls it "the one range his voice may
  never occupy". That is the range subordination lands in.
- `NADIA.md:11` says "she doesn't join ideas with 'and,' 'but,' or 'so'",
  removing the plainest way to build a longer sentence.

## What must not be changed

Two of these constraints are load-bearing and the pass has to work around them
rather than through them.

**Kayleigh and Bryce.** Their flat delivery is the book's test for a
matter-of-fact complaint against an insult, and the book's argument depends on
neither crossing it. `KAYLEIGH.md:40` bans a "because" clause; `BRYCE.md:38` bans
explaining a mechanism. Adding subordination here damages the argument, not just
the voice.

**The teachers' register.** `_CALIBRATION.md` says a teacher never lets a student
know they are exceptional. That is the mechanism behind every staff line. It
rules out warmth and praise. It does not rule out precision, difficulty, or being
funny in a dry way, and the staff sheets currently treat it as though it does.

**Owen.** Thin by design. `OWEN.md:38` holds the calibration exactly: "He wanted
to stay and could not do the work. The leaving was not a preference." He should
not become eloquent. Settle whether he ever gets a spoken line before a pass
starts, not during one.

## What is already carrying more than the sheets admit

The capacity exists and is on the page:

- Kavi's unbroken technical runs
- Theo, throughout, though he has only 26 lines and none before adulthood
- Sam's tactical monologue in chapter 15
- Priya, the one character who genuinely runs on, whose sheet warns against
  trimming her rather than expanding her
- Bell, Kowalczyk, Amberg, Baptiste and Sandoval, each of whom already produces
  multi-clause causal prose from a real personal mechanism

Five of nine teachers work. The other four, Hearn, Doyle, Pruitt and Sinclair,
are built from the shared institutional test rather than from a person, and their
voice sections describe what they withhold instead of what they say.

## The blurs

Each was flagged independently, and in most cases the sheets already carry a "do
not confuse with" note pointing at the other half of the pair, which means the
collision was sensed when they were written.

| pair | axis |
| :-- | :-- |
| Meg and Dave | worst in the book. Long stretches are unassignable without tags. `MEG.md` claims the flat phrase-repeat as hers alone, but Dave does it three times in the manuscript. Their one clean difference: Meg escalates with a question, Dave names a cost or a number. |
| Kavi and Eli | both deflect praise by naming the cost |
| Aldana and Vance | warm, tired, competent classroom manager |
| Vance and Prahl | warmth that fails structurally |
| Doyle, Pruitt, Sinclair | unimpressed institutional flatness, separable only by staging |

## Order of work

1. Amend the dials before touching prose. They are descriptions of a flat book
   being enforced as rules on the next draft.
2. Separate Meg and Dave. Their scenes have the most room to grow and are
   currently the least distinguishable.
3. Give Hearn, Doyle, Pruitt and Sinclair a mechanism each, the way the other
   five teachers already have one.
4. Then raise the register, protecting Kayleigh, Bryce, Owen and the teachers'
   no-praise rule.

## One caveat about these sheets

They quote the manuscript throughout, and the three line-edit passes rewrote or
removed 703 quoted spans. `verify_citations.py` reports 88 quotations that are no
longer in the text, against 73 before the passes. Roughly fifteen were orphaned by
our own edits, including a Doyle line his sheet still quotes. Re-quote the sheets
against the current text before relying on them.
