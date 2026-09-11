# Reader pass: chapters/35_nine_minutes.md

Word count before: 2106
Word count after: 2060

## Findings addressed

### Which tool is running (the main finding)

Checked the finding against `chapters/32_the_money.md` and `chapters/33_the_other_one.md`
headers, as instructed:

- Ch. 32, "The Money," is the financial worm: *November 2025 - February 2026*.
  It goes live partway through that window, disguised to sit "in the places
  where a badly maintained reconciliation job would sit."
- Ch. 33, "The Other One," is the government-file worm: *May 2026 - June 2026*.
  It is explicitly a one-shot job ("as long as it takes to get in and out
  once," a five-week test, then presumably shut down), not a tool meant to sit
  and monitor indefinitely.

Chapter 35 ("Nine Minutes") is dated June-July 2026 and describes a tool that
sits quietly and checks in on a schedule, disguised as a reconciliation job.
That persistent-monitoring design and the reconciliation-job disguise both
belong to the financial worm, not the one-time government job that chapter 34
had just been about. The "for over a year" line fit neither timeline: from a
November 2025 launch to June/July 2026 is roughly seven to eight months, not a
year, and the government tool didn't exist a year before this chapter at all.

Fix: named it explicitly in the opening line, and swapped the false duration
for one that matches the ch. 32 window without adding a banned number word:

- "The worm goes quiet on a Thursday in June." -> "The financial worm goes
  quiet on a Thursday in June."
- "The tool has run for over a year on a schedule..." -> "The tool has run
  since the winter on a schedule..." ("the winter" sits inside Nov-Feb and
  also can't be mistaken for the government tool, which launched in spring)

### Watcher's scope

"Kavi's watcher, whose entire job is to see anything that anybody else might
see" stated an absolute (it sees anything anyone could see) the chapter never
demonstrates. Reworded to scope it to Kavi's own design effort rather than an
established, objective capability:

"Kavi's watcher, built to catch anything he could think to make it watch for,
reports a healthy process across the window."

### Unchanged state

"State, position, byte for byte what it was" and its later echo didn't say
whose claim that was: the tool's own report, or verified reality. The second
instance already read "the report lands anyway: state, position, byte for
byte unchanged," which ties it to the report. Matched the first instance to
that same framing so both are clearly the tool's self-report, not a confirmed
fact about the world:

"But nine minutes later, the report reads exactly as it always does: state,
position, byte for byte what it was."

### Kept as instructed

- The missed-check-in beat where Eli finishes his sentence before he looks
  back at the corner. Untouched in substance; only the tap clause inside that
  same sentence was cut (see below).
- Chloe arranging coverage with Ruth before she sleeps ("watch the thread
  tonight, im out for a few hours" / "on it"). Untouched.

### Recurring gestures (also the word-budget source)

Cut the repeats that were diluting Eli's one meaningful stopped tap, per the
finding, while keeping that one stop:

- Cut "the two-finger tap against the desk edge running ahead of it the way
  it always does" from the first missed check-in (an ordinary, not-stopped
  instance of the tap, in the sentence the finding asked to keep).
- Cut "the tap keeping its own rhythm against the desk edge whether or not
  anybody's there to see him doing it" at the end of the third check-in
  paragraph, right after the one stopped-tap instance that has to carry the
  meaning.
- Cut "Kavi squares the pen on his desk against its mark, then" before "starts
  reading his own code," one instance of the "pens squared against marks" tic
  the note flagged as book-wide overused machinery.

Eli's single stopped tap ("the two-finger tap against the desk edge stopping
mid-beat when he notices the empty line") is now the only tap description left
in the chapter.

## Not changed

Nothing else in the finding conflicted with what's on the page, so nothing
else was touched. `measures/style_report.py` on the chapter shows the tic scan
at "none found," same as before the pass.
