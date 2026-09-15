# Reader pass: chapters/32_the_money.md and chapters/33_the_other_one.md

Word count before: 32=2245, 33=2073
Word count after:  32=2222, 33=2060

## Chapter 32 findings addressed

### Theo's disclosure had two versions of the same reveal

Checked against the text: confirmed. In the Ruth-proof exchange, Theo already
says "the government cant show it and theyve had a dozen years" before Sam
and Nadia later wonder aloud whether anyone (specifically the government) has
looked, and before Theo's own deliberate, ceremonial disclosure of the file
("theyve had a file on the school since 2013" - a dozen years, matching
exactly). Theo's own character sheet is explicit that he "does not leak in a
slip, a hint, or a meaningful silence" and that his real disclosures come
with the whole chain and the caution stated first - so an early, offhand
"dozen years" is a slip that contradicts him as much as it confuses the
sequence.

Fixed by cutting the leak from the earlier line rather than restructuring the
later, correctly-staged reveal:

- "theo: the government cant show it and theyve had a dozen years" ->
  "theo: the government cant show it"

Ruth's next line ("the government is arguing from absence...") still follows
naturally from this shorter line.

### Ruth's "this isnt new" claims foreknowledge she doesn't have

Checked: Sam's "WHAT" and Chloe's "theo which four" both register this as
news, so Ruth's "this isnt new, sam" is either a private disclosure never
established, or (as the finding says) minimizing a live revelation. Cut the
false-foreknowledge framing and kept the actual analytic point, which stands
on its own as a response to Kavi's "a state doesnt leave four operators
walking" a line earlier:

- "ruth: this isnt new, sam, it just means there were two attempts" ->
  "ruth: sam, it just means there were two attempts, not one"

### Theo's "when it matters and not before" had no stated reason

Checked: this is narration, not a rule the finding asked me to leave alone,
and Theo's sheet gives a specific, established habit to reach for instead of
an unexplained withholding: he "checks a fact against its source before
repeating it to anybody." Used that:

- "and Theo says he will tell them when it matters and not before." ->
  "and Theo says he wants to check the file again first."

This gives him a concrete, in-character reason (verify names against the
file rather than name people from memory) instead of an unmotivated delay.

### Nadia's company vs. her parents' shop

Checked against chapter 27 and chapter 24: Nadia has two distinct
businesses, her own company (the job-application tool, run out of three
rooms over a laundromat) and her parents' shop (the till, the ledger, the
repairs). The finding is correct: chapter 32 opens the test against "Nadia's
company... on her own live books" and then every transaction that follows -
till, ledger, compressor motor, lawnmower blade, register - belongs to the
shop, not the company.

Fixed the mismatched opening clause; the very next sentence already says
"Nadia runs the shop," so no other changes were needed:

- "They test it for a month against Nadia's company, on her own live books,
  before it goes anywhere." -> "They test it for a month against the shop,
  on its own live books, before it goes anywhere."

### Time zone error had no stated cause

Checked: Nadia and the shop are in the same place, so "her local time"
differing from "the shop's own time zone" doesn't make sense as written. Eli
is building the tool remotely, so the natural source of a timestamp reading
wrong is the machine doing the logging, not Nadia herself. Renamed it as the
finding suggested:

- "a timestamp that's read her local time instead of the shop's own time
  zone" -> "a timestamp that's read off the server's clock instead of the
  shop's own time zone"

### Eli's build location vs. deployment location

Checked: the build paragraph implies Eli works somewhere other than his
employer's desk ("committed at 3:14 a.m. ... that will have him back at his
employer's desk before the morning is out"), but the deployment scene gives
him a "badge already logged out" and "the floor around him empties" - both
office-specific details that put him back at an employer's building, and
specifically an odd place to run financial-surveillance software against a
third party his own company has nothing to do with. Reworded the deployment
scene to keep him at his own desk, consistent with the build scene, and
dropped the badge/floor language that implied an employer's office:

- "Eli stays at his desk long after the floor around him empties, badge
  already logged out, screen turned away from the doorway" -> "Eli stays at
  his own desk long after the rest of the building has gone quiet, screen
  turned away from the door"

### "Tighten the polling interval" is ambiguous

Checked: "tighten" reads naturally as checking more often, which runs against
the point of the whole design (staying boring, staying infrequent, reading
"like a bored auditor would skim past"). Swapped for an unambiguous word:

- "nadia: tighten the polling interval again" -> "nadia: widen the polling
  interval again"

### Repetitive physical business

The finding is right and matches the supervising note that this repeats
book-wide. Nadia's till-recounting is her own established habit from chapter
27, so I kept the two bracketing instances (the setup and the late-night
close) and cut the third, redundant instance in the middle of the chapter,
which also helped the word budget:

- "Sam finishing a set at a gym a long way from Nadia's shop, Nadia closing
  out a Tuesday's till a second time to be sure the number holds. Sam breaks
  it" -> "Sam finishing a set at a gym a long way from Nadia's shop. Sam
  breaks it"

Left Kavi's "turns an object over and sets it back exactly where it was" and
Eli's two-finger tap alone: both are documented, specific signature gestures
on their own character sheets, not generic filler.

## Chapter 33 findings addressed

### "Since before any of us could read"

Checked against the calendar: the government file starts in 2013, when the
cohort is seven or eight and already reading (Halstead only admits early
readers). The line manufactures a longer surveillance history than the book
supports. Fixed to a true claim that still carries Chloe's point:

- "someones had a file on us since before any of us could read" ->
  "someones had a file on us since before we were teenagers"

### Theo's job described as law enforcement

Checked against his sheet: his job is federal analyst - reading and weighing
intelligence, not enforcing law, and "rhetoric... working out who benefits
from a claim" is the description closest to what he actually does. "The law
i get paid to enforce" and rule-drafting being "the thing i do all day" both
overstate this into a different profession. Fixed both:

- "Theo could have written cleaner rules than anyone else at that table,
  since it is, more or less, his actual job, and he says so once." -> "Theo
  could have written cleaner rules than anyone else at that table, and he
  says so once." (cut the false-job claim; it was also a near-duplicate of
  the line right after it)
- "theo: i could write this. its the thing i do all day" -> "theo: i could
  write this. finding the hole in somebody elses plan is the thing i do all
  day" (reframes the boast around reading/critiquing, which is his actual
  work, not drafting)
- "the law i get paid to enforce" -> "the government i get paid to read"
  (same length, same rhythm, no longer claims he's an enforcer)

### Sam's "food at basic" joke read as current, not a callback

Checked: I could find the line (it's narrated, not quoted, in the "small
talk" list at the top of the chapter), so the supervising note's doubt about
its existence is resolved - it's there. The finding's actual complaint
holds: listed alongside "the weather outside his building" as live chat
content, it reads as something happening now, almost three years after Sam's
arrival, rather than an old bit. Marked it as a standing joke instead:

- "a joke Sam makes about the food at basic" -> "an old joke of Sam's about
  the food at basic"

### File "a dozen years out of date" contradicts chapter 32

Checked: chapter 32 has Ruth and Theo agree the file is "a dozen years of
being wrong in detail" and that this is "worth more than nothing" because
"they know things about our own school that we dont." Chapter 33's "out of
date" flattens that into worthless, which is the opposite of what chapter 32
established and of the reason Theo gives for wanting to read it. Fixed to
match:

- "a file on their own school that's a dozen years out of date" -> "a file
  on their own school that's a dozen years deep and mostly wrong"

### "Four who never held a badge" - checked the arithmetic, it holds

Worked out who the seven signers are (Eli, Nadia, Kavi, Sam, Ruth, Chloe,
Theo - the full sign-off list at the end of the chapter) and who among them
plausibly "holds a badge": Theo (federal analyst), Chloe (a job with a
security clearance, stated explicitly in this same chapter), and Sam (still
active-duty Army as of chapters 35-36). That's three, leaving exactly four
(Eli, Nadia, Kavi, Ruth) who don't - the arithmetic in the chapter is
actually sound. Priya was never one of the seven and isn't implicated by this
line at all; she simply isn't part of this operation.

The finding is still right that "badge" is the wrong word to carry this,
since Sam's military service and Eli's own literal employee badge (chapter
24) make "badge" ambiguous rather than a clean two-way split. Reworded to
the thing that actually separates the three from the four - having signed
something for the government - rather than leaving readers to guess at
badge rules:

- "what happens to the four of them who never held a badge if this goes
  wrong" -> "what happens to the four of them who never signed anything for
  the government if this goes wrong"

### Drafting and testing order

Checked the sequence closely. Two genuine problems, one deliberate choice I
left alone:

- "Eli signs first, hours after he sends the document" can't be true on the
  timeline as written - Eli sent his own 12-page proposal document weeks
  earlier, long before Chloe's rules exist to sign. The "document" being
  signed is Chloe's finished rules, not Eli's. Fixed the pronoun:
  "hours after he sends the document" -> "hours after Chloe sends it"
- "They sign off one at a time over the following week" directly conflicts
  with "Theo signs off last, at the far end of the test," five weeks later.
  Widened the frame so both are true:
  "over the following week" -> "over the weeks that follow"
- Left Theo's sign-off actually arriving at the end of the five-week test
  alone: this reads as deliberate characterization (he's the one who states
  the formal objection and needs the test's own clean results before he'll
  commit), not an error, and changing it would cut against his sheet's "he
  states an objection for the record and then does the thing" pattern.

### Repetitive physical business

Chloe's document-writing paragraph repeated, almost verbatim, the
kitchen-counter/coffee-going-cold image she'd already been given twenty
lines earlier reading the thread. Cut the second instance rather than the
first, since the first also carries the "reads the men-over-the-fence line
again" beat that needs the counter scene to land:

- "Chloe spends most of that stretch at her own kitchen counter, most
  nights, the coffee going cold before she remembers it's there." -> "Chloe
  spends most of that stretch working after the apartment goes quiet."

Also cut one instance of the "reads it twice" construction, which appears
three times across the chapter (Ruth, Chloe, and the stop-clause rule) - the
version in the rules-summary sentence was the least load-bearing:

- "and the rule everybody reads twice, that any of them can end it" -> "and
  the rule that any of them can end it"

Left Kavi's "turning whatever's on the table over in his hands and setting
it back down exactly where it was" and Nadia's sleeves-up tell alone: both
are documented, specific character-sheet gestures, not generic filler.

## Verification

- Word counts: `python3 -c "import re;print(len(re.findall(r\"[A-Za-z']+\",open('chapters/32_the_money.md').read())))"`
  -> 2222 (was 2245). Same command for chapter 33 -> 2060 (was 2073). Both
  shorter, both well inside the 2000-5000 band.
- `python3 measures/check_edits.py --chapters 32 33` -> 0 problems (no em
  dashes, no curly quotes, no hard-break lines, word counts recorded).
- `python3 measures/style_report.py chapters/32_the_money.md` and the same
  for chapter 33: no tics found in either (narration only, quoted spans
  removed); "and" share, section-break count, and the pass/fail pattern on
  every other line match what the same script reports on the pre-edit text
  (verified by reverse-applying my own diff, rerunning, then reapplying it) -
  nothing regressed and nothing newly failed.
- `python3 grade.py --one chapters/32_the_money.md` and chapter 33: reading
  grade (Flesch-Kincaid 11.2 / 9.7, ARI 12.3 / 10.5) both stay comfortably
  above the adult-band floor of 7.2-9, matching the pre-edit values (11.3/9.8
  and 12.5/10.6) almost exactly. The script errors out afterward on a
  missing `dialogue_study.py` path, which is a pre-existing bug in grade.py
  unrelated to these edits (it looks for the file at the repo root instead
  of `measures/`).
