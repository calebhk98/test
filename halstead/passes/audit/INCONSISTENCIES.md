# Inconsistencies audit

Scope: the two sections of `passes/review/Feedback.md` headed **INCONSISTENCIES** and
**III. Illogical Sequences and Inconsistencies**, verified line by line against the
manuscript as it stands today, plus a sweep of the same four classes across all
thirty-six chapters:

1. chronology and age arithmetic
2. technical or numeric claims that do not compute
3. dialogue attribution
4. characters held to two different standards in different chapters

Every quotation below was re-grepped against `chapters/` immediately before being
written down. Four other agents are editing concurrently, so text is quoted rather
than cited by line number; where a line number appears it is a convenience, not a
guarantee.

**One edit was made.** `22_the_offer.md`, Meg's line, "at eighteen years old" →
"at seventeen years old". This is the only change in this pass. It qualifies under
the brief because the author has already ruled the birthday to August (the ruling is
executed in ch23 and ch30) and the consequence is a single unambiguous figure.
Everything else below is a report.

---

## Headline

- **Three of the nine seeds are already fixed** in the current text and need nothing:
  #4's neighbours (the stale "six years back" / "six years ago" figures), most of #8
  (the answer is on the page in ch16, just never restated), and the older
  "nine years old" chat figure. Details in each entry.
- **Six of the nine are live.** Two of those (#2 bar exam, #8 metadata) have an
  author ruling and need execution, not a decision. Four need a decision.
- **The single most valuable finding is not one of the nine.** The birthday chain is
  now clean everywhere except chapter 33 — but working it end to end turned up
  **chapter 24 contradicting itself inside one chapter** about when the chat's
  encryption was written, and **chapter 23's head of school contradicting chapter 23's
  narration three paragraphs later** about how long the class has been in the building.
- **Chapter 25's title number does not add up.** "Forty Targets" describes fifty
  exposures and then scores forty. This is a new find and a one-word fix.

---

## The birthday chain, worked end to end

**Anchor: Chloe Kessler is born in late August 2005.** This is the author's ruling
(recorded in `chronology/CALENDAR.md` §1) and it has already been executed in the
manuscript: ch23 now reads "she turns eighteen in August" and ch30 now reads "She's
twenty-one in August". The two June lines the reviewer worked from are gone.

The anchor is independently corroborated in Part 1 and never contradicted there:
Chloe answers `"Six."` on day one of camp in the second week of July 2012
(`04_pluto.md`), and the following February her mother says "she's seven years old"
(`09_february.md`). Six in July, seven by February, plus the author's summer-birthday
constraint, gives late August.

Halstead's year runs September–June, so a student who turns N in August is N for the
whole school year that follows. That single rule generates the entire spine:

| Ch | Date the chapter carries | Chloe's age | Text that states or implies it | Verdict |
|---|---|---|---|---|
| 1 | Sept 2011 – Feb 2012 | 6 | "She is six." | ✅ |
| 2–5 | Mar – Jul 2012 | 6 | `"Six."` (ch4) | ✅ |
| 6–7 | Aug – Oct 2012 | 6→7 | camp ends early Aug, birthday late Aug | ✅ |
| 8 | Oct 2012 – Jan 2013 | 7 | — | ✅ |
| 9 | Feb – Mar 2013 | 7 | "she's seven years old" | ✅ |
| 10 | Apr – Jun 2013 | 7 | starts Halstead | ✅ |
| 11 | Jun 2013 – Jun 2014 | 7→8 | title "Eight" | ✅ |
| 12 | Sept 2014 – Jul 2015 | 9 | "Nine-year-olds get eight" | ✅ |
| 13 | Sept 2015 – Apr 2016 | 10 | position + "at ten" back-references | ✅ |
| 14 | Sept 2016 – Apr 2017 | 11 | position | ✅ |
| 15 | Sept 2017 – Jan 2018 | 12 | "I'm twelve and I'm small" | ✅ |
| 16 | Sept 2018 – Jul 2019 | 13 | "Teaching starts at thirteen" | ✅ |
| 17 | Sept 2019 – Apr 2020 | 14 | teaches the thirteens | ✅ |
| 18 | Sept 2020 – Jul 2021 | 15 | "a fifteen-year-old" (Sandoval) | ✅ |
| 19 | Apr 2022 – Jun 2023 | 16→17 | bar at sixteen, retake Oct at 17 | ✅ |
| 20 | Jun 2022 | 16 | author's fix; ch36 "you were sixteen" | ✅ |
| 21 | Oct 2022 – Mar 2023 | 17 | "a seventeen-year-old picks things" | ✅ |
| 22 | Apr 2023 | 17 | Meg said **eighteen** | ⚠️ **fixed in this pass** |
| 23 | Jun 2023 | 17, turns 18 in Aug | "she turns eighteen in August" | ✅ |
| 24 | Sept 2023 | 18 | — | ✅ |
| 25 | Aug – Nov 2023 | (Sam) | — | ✅ |
| 26–27 | Feb – May 2024 | 18 | — | ✅ |
| 28 | Sept 2024 – Apr 2025 | 19 | title "Nineteen" | ✅ |
| 29 | Oct 2025 | (Theo) | "He was twelve that year" + "Eight years ago" = 20 | ✅ |
| 30 | Sept 2025 – Jan 2026 | 20 | "three weeks after she turns twenty" | ✅ |
| 31 | Oct 2023 – Nov 2025 | (Ruth) | — | ✅ |
| 32 | Nov 2025 – Feb 2026 | 20 | — | ✅ |
| 33 | May – Jun 2026 | **20** | says she **turns twenty-one** | ❌ **live error** |
| 34 | Jun 2026 | 20 | "five months into a job" (Jan start) | ✅ |
| 35 | Jun – Jul 2026 | 20 | — | ✅ |
| 36 | Oct 2026 | 21 | "nine months into the job" (Jan start) | ✅ |

Job-tenure markers cross-check cleanly and independently confirm a January 2026
start: ch33 "four months into that job" (May), ch34 "five months into a job" (June),
ch36 "nine months into the job" (October).

**Every statement of Chloe's age the chain contradicts, complete list:**

1. `33_the_other_one.md` — "Chloe turns twenty-one somewhere in the middle of it."
   She turns twenty-one in **August 2026**; chapter 33 is May–June 2026. **Live.**
2. `22_the_offer.md` — Meg: "at eighteen years old." She is **seventeen** in April 2023.
   **Fixed in this pass.**

Nothing else. Two other lines were checked and clear:

- `21_the_applications.md`, "She's sixteen, and she's in class until four." The author
  has confirmed the third author is not Chloe. Under the August-2005 calendar this
  survives on its own terms: the Caltech read falls in Dec 2022 – Jan 2023, and a
  cohort member born in early 2006 is sixteen then and seventeen at graduation. No change.
- `30_cleared.md`, "I started that April, a few months after I turned seven." August 2012
  to April 2013 is eight months. "A few" is loose for eight, in a chapter otherwise built
  on Chloe's precision, but it is not wrong. Optional: "the April after I turned seven."

---

# Part A — the nine seeds

## A1. Chloe turns twenty-one twice — **LIVE, needs a decision (small one)**

**Ch30, current:** "She starts in January. She's twenty-one in August."
**Ch33, current, chapter dated *May 2026 – June 2026*:** "Chloe turns twenty-one
somewhere in the middle of it. It gets mentioned afterward, once, in passing, the week
she finishes the last page; there's no clean place for a birthday inside a document
about federal sentencing exposure, so it waits."

Ch30 is right and is load-bearing (it is anchored by "three weeks after she turns twenty"
earlier in the same chapter and by three independent job-tenure counts). Ch33 is wrong.

**Options**

| | Fix | Cost |
|---|---|---|
| a | Cut the birthday paragraph from ch33 | 1 chapter, 1 paragraph. Loses a good beat. |
| b | Move the beat to ch35 or ch36, where August 2026 actually falls | 2 chapters. Ch35 runs June–July, ch36 is October — August sits in the seam between them, so it would have to open ch36 as a backward glance. |
| c | Rewrite the ch33 paragraph so it is not a birthday | 1 chapter. E.g. the anniversary of something, or "Chloe turns twenty-one four months later, and it gets mentioned once…" |
| d | Keep it and move the chapter | Not available — ch33's May–June is pinned by "four months into that job." |

**I would take (c).** The paragraph's actual work is *a private landmark going
unmarked because the group is busy committing a felony*, and that survives intact if
the landmark is deferred rather than concurrent. It preserves the beat, touches one
paragraph in one chapter, and requires no other chapter to move.

**Related, and separate:** Meg's "eighteen" in ch22 — corrected in this pass, see above.

---

## A2. The bar exam, real or internal — **LIVE, author has ruled**

**Ch16, Amberg, unchanged:** "So you're going to learn the law of your country, because
at sixteen you'll take the bar. That's the examination this country uses to check whether
a person knows it, and every citizen in this room ought to pass it."

**Ch19, unchanged:** "They take the bar in April, over two days, in the long examination
room on the second floor … and along the front sit the teachers who wrote the paper and
will mark it, proctoring the whole of it themselves."

**Ch30, Chloe to Whitaker, unchanged:**
> "There's also an internal law examination," Chloe says. "It's the school's own, not
> accredited anywhere outside it. It wouldn't hold up in an actual court."
>
> "Understood." He writes it down anyway.
>
> "You're recording something with no legal standing."
>
> "You told me about it straight," Whitaker says. "That's standing enough for what I
> need it for."

**Ch33, unchanged:** "All of them know the law cold. They had sat the same examination."

**The author's ruling:** *"The most likely interpretation is that the Bar exam is internal,
but when she mentions it to the investigator, she shouldn't know it's not accredited. She
would think it's just a standard HS exam you take to be a citizen."*

**What has to change:** only ch30, and only the four lines quoted above. Everything else
already complies, and better than the reviewer noticed:

- **Ch16 stays exactly as written.** Under the ruling Amberg's framing is not a lie he
  tells students — it is simply what the school believes and teaches, and it is what
  Chloe believes for the rest of the book. No acknowledgment line is owed anywhere.
- **Ch19 already does the reader's half of the job for free.** "the teachers who wrote
  the paper and will mark it" tells the reader the exam is the school's own while Chloe
  never says so. That is exactly the dramatic irony the ruling wants, and it is already
  on the page. Leave it.
- **Ch33's "They had sat the same examination" is agnostic.** No change.

**Ch30 rewrite shape.** Chloe reports the bar the way she reports the languages and the
classes — as a fact about her education, flatly, with no assessment attached. Whitaker
is the one who registers what it is, and the registering has to be a beat the reader
catches and Chloe does not. Roughly:

> "There's the bar as well," Chloe says. "Everyone sits it at sixteen. It's the one that
> checks you know the law of the country you live in."
>
> Whitaker's pen stops for the length of a word and starts again. "Where did you sit it."
>
> "At school. Both days, in the examination room."
>
> "Understood." He writes it down, and what he writes takes longer than what she said.

The count "eleven languages, two published papers, the bar" is unaffected. **One chapter,
four lines.** The current version's good beat — Whitaker recording something worthless
because she volunteered it straight — has to go, because it depends on Chloe knowing.
Something of equal weight should replace it; the pen stopping is the cheapest candidate.

---

## A3. The pairing-code arithmetic — **LIVE, arithmetic not yet ruled on**

**Ch15, Kavi, unchanged:** "It's AES-256," he says. "But, it's a six-digit pairing code and
they never changed it off default." He's already got the campus cluster chewing on it.
**"You just do a few billion codes and see which one gives you something that isn't
noise. It's four seconds of compute. It's not even interesting."**

A six-digit decimal code has **10⁶ = one million** combinations, not a few billion. The
author's ruling covers only *why the gear is commercial* (federal investigators running
black operations on civilian equipment so nothing traces back) and leaves the number
untouched. As written the best cryptographer in the building is wrong by three orders of
magnitude, in a chapter whose whole point is that he is not.

Note that the error is not only the number: **"a few billion" makes the feat sound harder
than it is, which inverts the line's meaning.** Kavi's point is contempt — the search
space is trivial. "A few billion" is a boast; "a million" is the sneer the scene wants.

**Options**

| | Fix | Note |
|---|---|---|
| a | "You just do all million codes" | Cleanest. Keeps the rhythm, fixes the maths, and "all million" carries the contempt better than "a few billion" did. |
| b | "You just do a million codes" | Same, marginally flatter. |
| c | Make the code longer so "a few billion" is right | Would need ten digits. Wrong — real consumer radios use four to six, and the whole joke is that it is a factory default. Rejected. |

**I would take (a).** One word, one chapter, no knock-on. "Four seconds of compute" is
correct for a million trial decryptions and needs no change. Sam's later callback ("Four
seconds," Sam says, like it offends him) is unaffected.

---

## A4. "First to sneak out in ten years" — **LIVE, needs a decision, and it is coupled to A10**

**Ch20, first line, unchanged, chapter dated *June 2022*:**
"They are the first to sneak out in ten years, the entire reason it is worth doing."

**Ch3, July 2012, unchanged:** "The school's four years old, Meg, it says so on the page
about the school." → **the school opened around 2008.**

So in June 2022 Halstead has existed **fourteen years**, and "in ten years" asserts that
somebody snuck out in 2012. Nothing in the book supports a 2012 sneak-out, and the
clause "the entire reason it is worth doing" wants a record, not a ten-year interval.

The author's note — *"If they are 16 when they sneak out, then the 10 years refers to them
being 6 when they joined, so it is likely an error in the year somewhere?"* — was written
before chapter 20 was fixed at sixteen. With sixteen fixed and June 2022 on the chapter
header, the year is no longer in question. **The wrong figure is "ten".**

**Options**

| | Fix | Chapters touched |
|---|---|---|
| a | "They are the first to sneak out since the school opened" | 1. Removes the arithmetic entirely and is the strongest version of the line. |
| b | "the first to sneak out in fourteen years" | 1. Correct against ch3, but a reader who has to do 2022−2008 to feel it is a reader you have lost. |
| c | Leave "ten years" and accept an unnarrated 2012 sneak-out | 0, but the line stops meaning what it is doing at the top of the chapter. |
| d | Change the school's founding year in ch3 | Rejected — ch3's whole scene is her parents worrying at a school that new, and the founding year is already load-bearing for A10. |

**I would take (a).** It is one clause, one chapter, and it is the only option that makes
the second half of the sentence true.

**Coupled to A10 (below):** if the author instead resolves A10 by moving the founding year
back to 2006–07 to match the nineteen-year file, then (b)'s figure becomes "sixteen years"
and (a) is unaffected. **(a) is the option that is right under either resolution**, which
is a further reason to prefer it.

---

## A5. Clearance timing — **LIVE, needs a one-word decision**

Chapter 30, in order, all unchanged:

- "The background investigation takes **ten weeks** and involves a man named Whitaker who
  comes to see her twice."
- "Then he calls, **the second week of October**, to set a time."
- "**The first week of November** he comes back, in a coat this time…"
- "**The clearance comes through in the autumn**, on an ordinary Tuesday…"
- "She starts in January."

Ten weeks from the second week of October is **the third week of December**. Autumn ends
21 December, so the line is not quite impossible — but "in the autumn" reads as
September–November to every reader, it sits *after* a scene explicitly dated the first
week of November, and the very next sentence is "She starts in January," which wants a
December or early-January arrival. As written the paragraph reads as though the clearance
arrives before the second interview it follows.

**Options**

| | Fix | Note |
|---|---|---|
| a | "The clearance comes through just before Christmas" | Best. Lands the arithmetic exactly, keeps the "ordinary Tuesday" flatness, and sets up "She starts in January" with one week between them. |
| b | "in December" | Correct, duller. |
| c | "in the new year" | Also correct if the ten weeks is read from the questionnaire rather than the call, but it collapses the gap before "She starts in January." |
| d | Change "ten weeks" to "eleven months" so autumn works | Rejected — it would push the start past January and break ch33/34/36's tenure counts. |

**I would take (a).** One clause, one chapter.

**One further thing in the same chapter, lower confidence:** the exam is "three weeks
after she turns twenty" (early September 2025) and "The result arrives by mail weeks
later" — but Whitaker calls in the second week of October, and a background investigation
does not open before the result. It survives if "weeks later" means late September. Not
worth changing on its own; worth a glance if the paragraph is being touched anyway.

---

## A6. Duplicated Sam attribution in chapter 15 — **LIVE, needs a decision (trivial)**

Unchanged, and now **two directly adjacent paragraphs** with nothing between them:

> Kavi is going through the equipment: two bags, a laptop, a lockpick set, a pair of bolt
> cutters that are the wrong bolt cutters for the fence they came over. …
>
> "They didn't even do costumes properly," Sam says. "Look at this. Look at this guy's boots."
>
> "It worked," Sam says, looking pleased with himself.
>
> "It worked because they took the stairs," Ruth says. …

The second "Sam says" must stay Sam: the argument that follows is Sam-versus-Ruth about
Sam's plan ("They didn't go past the kitchens." / "They could have."), and "looking pleased
with himself" is Sam claiming credit for the stairs.

**The first line should be Kavi's.** The paragraph immediately above it has Kavi
inventorying the equipment and noticing that the bolt cutters are wrong for the fence;
"They didn't even do costumes properly … look at this guy's boots" is the same catalogue
of wrongness, one item further on. It also feeds Chloe's later paragraph directly — "The
bolt cutters wrong for that fence. The boots wrong. All of it wrong in the same direction"
— which currently draws on two speakers and would draw on one.

**Fix:** `"They didn't even do costumes properly," Kavi says.` One word, one chapter.

A systematic pass for the same defect across all thirty-six chapters found **no other
instance**. Ten other candidates flagged by the scan all have an intervening speaker or a
narration beat.

---

## A7. Theo's three different standards — **the text supports a deliberate reading, but does not state it**

The three instances, as they now stand:

| Ch | Date | What he does | Deliberation shown |
|---|---|---|---|
| 29 | Oct 2025 | Holds the file, posts "hypothetically / if you found something out about the school. from work. that you couldnt actually say / how badly would you want to know" | "It sits with him for two days," two full scenes, the grandmother call, "Several versions of the question get typed before he sends any of it" |
| 32 | ~Jan–Feb 2026 | Dumps the file's contents into the chat: nineteen years, wrong twice, the man on staff, the four operators | "Minutes pass before Theo posts again. Those minutes go where anything with real weight goes with him: laptop closed with both hands, out onto the back steps … a full glass of water next to the keyboard" |
| 33 | May 2026 | Refuses the second worm, then relents | "Theo says no, and keeps saying no for days," plus three paragraphs of tea, walking to work, small talk in the chat |

**Yes, the text supports a deliberate reading — and it is nearly there.** Two things
already on the page do most of the work:

1. **Ch32's disclosure is not the first move; it is the second half of a move begun in
   ch29 and left open for three months.** He asked the group the hypothetical, got Ruth's
   "bad", and then said nothing for a quarter of a year. On that reading the two days in
   ch29 *are* the deliberation for ch32, and the minutes on the back steps are the last
   step of a decision already made.
2. **He does not volunteer it.** He posts only after Nadia has independently reasoned her
   way to it — "the government tracks everything. if anyone has a file its them." He is
   confirming a deduction, not breaking news. And the first thing he types is a condition:
   "nobody repeats any of this. i mean it."

There is also a clean escalation of *kind* underneath the apparent inversion of *degree*:
ch29 is "may I say anything at all", ch32 is speech about a document, ch33 is a federal
computer intrusion he would personally be prosecuted for. Deliberation tracking legal
exposure rather than volume of information is characterful, not sloppy.

**What is missing is one sentence connecting (1) to the reader.** The ch32 paragraph
describes the minutes but does not say what he is deciding, and a reader who has not held
ch29 in mind for eight chapters reads it as an impulse. One clause in that paragraph —
that he had already made this decision in October and had been waiting three months for
somebody to ask the question that let him say it — converts the whole thing.

**Verdict: possibly deliberate, and cheap to make certainly deliberate. One sentence,
one chapter (32).** Not an error; do not restructure.

---

## A8. Metadata — **the author's answer is already in the text. It is in the wrong chapter.**

**Ch16, the lesson, unchanged:**
> Chloe breaks it inside a week, and the encryption holds the whole way: what she gets
> instead is that the school's network records which machine talked to which and when …
> "Knowing what we said is beside her point, because what she wants is that this table
> said something to each other at ten on Thursday and then went missing off breakfast on
> Saturday."

**Ch16, the fix, unchanged, and this is the author's ruling verbatim:**
> **Kavi has the first version running by the end of the month on the school's own
> machines, because a service inside the building looks like every other service in it**,
> and Ruth writes the encryption herself out of the term's material…
>
> …what comes out is slow and ugly and **pushes exactly as much traffic at three on a
> Sunday morning, with all of them asleep, as on a Thursday night with all of them typing.**

So: servers on school hardware, plus constant-rate cover traffic. The book has already
solved metadata, on the page, in the same chapter that taught the reader metadata was the
hole. **The author's ruling needs no new invention — only a restatement after graduation.**

**The gap is that nothing repeats it once they scatter.** Ch24 (Sept 2023) is the chapter
that re-establishes the chat as an object for the adult half of the book, and its opening
paragraph says only: "The chat is five years old. They wrote the encryption themselves in
their first year here…" — the encryption, not the hosting, and not the cover traffic. So
by the time ch34's file says the method is unknown and "collection against the channel
comes back empty every time it's tried," a reader who remembers the ch16 lesson has no
recent reason to believe the ch16 fix is still running for eight people on ordinary
carriers in eight states.

**Where one line fixes it.** Two candidates, and the first is enough:

- **Ch24, opening paragraph — best.** It is where the chat is introduced to the reader
  as a thing that has survived, and the clause costs nothing:
  *"…and none of them has ever used another. It still runs where Kavi first put it, on
  the school's own machines, still pushing the same weight of traffic at four in the
  morning as at four in the afternoon."*
- **Ch34, at Kavi's beat — optional second touch, and free.** He already reads the
  collection-failure sentence twice: "Kavi reads that part twice, the second time slower,
  the pen in his hand going still for exactly as long as it takes him to get through the
  sentence about collection failing." Giving him half a line of private satisfaction
  there closes the loop for the reader without anyone explaining anything.

**One chapter for the fix, two if you want the payoff.** Status: author has ruled; the
ruling is already true in the text; only the restatement is missing.

---

## A9. The chapter 18 → 19 gap — **real, structural, and the reviewer slightly mis-sized it**

Ch18 ends "On the last Sunday of July" plus "a week later" → early August 2021.
Ch19 opens "They take the bar in April" → April 2022.

The missing stretch is **September 2021 – March 2022**: not a whole year, but the autumn
and winter terms of the "Sixteen" year — and specifically the two terms of preparation for
the bar exam that opens chapter 19. Every other age-titled chapter opens in September; this
is the only one that opens in April, three-quarters of the way through its own year.

A second gap of exactly the same kind exists and is not in the review: **ch15 ends in
January 2018 and ch16 opens in September 2018**, so the spring term of the "Twelve" year
is also uncovered. That one is less exposed because nothing in ch16 refers back to it.

**Options for 18→19**

| | Fix | Cost |
|---|---|---|
| a | Leave it. Label ch19 honestly and let the white space stand | 0. It is a legitimate elision; the book skips summers routinely. |
| b | One paragraph at the head of ch19 covering the two terms of bar preparation | 1 chapter. Would also earn Sam's fourteen-page answer, which currently arrives with no preparation behind it. |
| c | Extend ch18 forward through the autumn | 1 chapter, more words, and ch18 already ends on a strong image (the grandmother and the hands). Rejected. |

**I would take (b).** Not because the gap is a defect — it is not — but because chapter 19
opens *mid-examination* on a subject the reader has heard about exactly once, three
chapters earlier, from Amberg. A short paragraph of run-up buys the whole chapter.

---

# Part B — new findings from the sweep

Ordered by how much a reader would notice.

## B1. Chapter 24 contradicts itself about when the encryption was written — **new**

Same chapter, two ends of it:

> **Opening line:** "The chat is five years old. They wrote the encryption themselves
> **in their first year here**, mostly to keep a teacher from reading it while they
> arranged getting out of the building, and none of them has ever used another."

> **Near the close:** "**The lock they built at thirteen** to get past a teacher is still
> the only thing standing between this chat and anyone outside it, one lock, **five years
> running**, untouched and unreplaced."

Their first year is 2013, age seven. Ch16 shows the lock being built at thirteen, in
2018 — which is what "five years old" in September 2023 requires, and what the second
quotation says. **"In their first year here" is wrong**, and it is almost certainly a
survival from the draft in which the chat was nine years old.

Ch12 independently confirms the timing: "cryptography happens at thirteen".

**Fix:** "They wrote the encryption themselves at thirteen" — or "in their first year of
cryptography". **One phrase, one chapter, no decision needed.** This is the cheapest
real error in the book.

## B2. "Forty Targets" describes fifty exposures — **new**

Ch25, chapter titled **Forty Targets**:

> "Qualification is the second Thursday of October, in the ninth week, and **it is forty
> targets**."
>
> "Pop-up silhouettes standing out from fifty metres to three hundred, **ten exposures
> from each of five positions**: standing, prone unsupported, prone supported, kneeling
> behind the barricade, standing behind the barricade."
>
> "**He hits forty. Every exposure.**"
>
> "**Forty out of forty.** That's the first I have signed for in two cycles…"

Ten exposures × five positions = **fifty**. The chapter states forty three separate times,
including in its own title and in the captain's dialogue.

**Fix: "eight exposures from each of five positions."** One word, one chapter. Do not
change the five positions — they are named individually and the list is good. Do not
change forty — it is the title, the score, and the captain's line.

## B3. Chapter 23's head of school describes a different school from the one in the same chapter — **carried forward from `SYNOPSIS_FROM_TEXT` §6.7, still live**

> "The head of school gives a short speech that is mostly logistics: **four years, some of
> them longer**; ninety-one names…"

Three paragraphs later, same chapter:

> "Then it's Kessler, and **eleven years** compress into thirty feet of plywood and four
> seconds of applause."

And in the same chapter Chloe reads the brass plates "as she has every single day **since
she was seven**." Chloe's cohort has been in the building since April 2013 — eleven school
years, and they are the oldest cohort in it.

**Options:** (a) "eleven years, some of them fewer" — accommodates the later entrants the
chapter itself mentions (Ruth's mother's younger child starting that September);
(b) cut the number from the speech entirely and leave "ninety-one names". **I would take
(a).** One clause, one chapter.

## B4. The government file predates the school — **carried forward, still live, and it is coupled to A4**

- Ch3, July 2012: the school is "four years old" → **opened ~2008**.
- Ch29, Oct 2025: "There is a file on his own school. **It goes back nineteen years**."
  → **opened ~2006.**
- Ch34, June 2026: "a case number nineteen years old"; "**Nineteen years of updates** sit
  stacked under that first page."
- Restated as "nineteen years" five more times across ch32, ch33 and ch36.

The file is two years older than the thing it is about, and nobody in the book remarks on
it. There is a second, smaller problem inside ch34: every individual file "starts the same
way … a line noting that contact with the family went no further than the one letter" —
the recruiting letter, which for this cohort arrived in 2012 — yet "nineteen years of
updates" sit under that page. From 2012 to 2026 is fourteen.

**Options**

| | Fix | Chapters touched |
|---|---|---|
| a | Make it deliberate: one clause somewhere in ch29 noting that the file opens two years before the doors do, on the money rather than the school | 1. **Strongest option** — it converts an error into evidence, and it is exactly the kind of thing Theo would notice. It also strengthens ch32's "around 1998 or 2001" money trail. |
| b | Change "nineteen" to "seventeen" throughout | 5 chapters, ~9 instances, and it breaks the motif's rhythm ("nineteen years of being wrong in detail"). |
| c | Move the school's founding to 2006 in ch3 ("six years old") | 1 chapter, but ch3's scene depends on the school being *very* new, and it pushes A4's arithmetic around. |

**I would take (a).** It is one clause, it touches one chapter, it makes the number
correct, and it makes the number mean something. Under (a) the ch34 "nineteen years of
updates" line should become "years of updates" or "a decade and more of updates", since
those genuinely start with the letter.

**Note on the frozen number:** "nineteen years" is used unchanged from ch29 (Oct 2025)
through ch36 (Oct 2026). If the file opened in late 2006 this is defensible everywhere
except ch36, which is a full year on from ch29. Low priority; if ch36's instance is being
touched anyway, "twenty" is right there.

## B5. Chapter 34 relocates the chapter 20 robbery — **carried forward, still live**

**Ch20:** they leave the diner, walk on, and find "a shopping cart in the lot behind a
hardware store"; the seven men arrive there; Chloe's speech names the spot — "standing
behind a hardware store at two in the morning taking phones off teenagers."

**Ch34, the federal incident report:** "sat in a Waffle House for two hours, and
afterwards were **in the car park** pushing each other around in a shopping trolley. /
Seven men come **across the car park** to rob them."

The report puts the robbery in the diner's own car park. Chapter 20 puts it several blocks
away behind a different building.

This one has a defence the others do not: it is a report reconstructed from seven
witnesses who "None of the men agrees with the others about the order of it," so
compression is in character for the document. **But nothing marks it as compression**,
and the chapter's own footage paragraph is written as though everything happened within
sight of the Waffle House.

**Options:** (a) change "car park" to "a lot behind a hardware store four blocks on" in
the incident report — one sentence, one chapter, and the footage paragraph still works
because the students *are* on Waffle House cameras earlier that night; (b) leave it and
add nothing, accepting the document's unreliability as texture. **I would take (a)** —
the report is otherwise scrupulously accurate (Ruth's twenty-two seconds matches to the
second, and the chapter makes a point of that), so a geographic error inside it reads as
the book's error rather than the document's.

## B6. Ruth is in a dorm room in chapter 33 and an apartment on either side — **carried forward, still live**

- Ch32 (Nov 2025 – Feb 2026): "The work happens on **the floor of her own apartment**…"
  and later "Ruth still on her apartment floor with the strip of paper rolled up beside her".
- **Ch33 (May – June 2026): "Ruth is already in it, cross-legged on her own dorm room
  floor in Cambridge with a roommate asleep two feet away" — and again, "Ruth reads that
  twice from the floor of her dorm room."**
- Ch34 (June 2026): a lab in Cambridge.
- Ch35 (June – July 2026): "She's on **the floor of her own apartment** when it lands".

She is in her third year at MIT in ch33. The dorm-and-roommate detail is a near-verbatim
carry-forward from ch24's September 2023 line ("a dorm room in Cambridge with a roommate
she's met twice"), which was correct then.

**Fix:** apartment, twice, in ch33. The "roommate asleep two feet away" clause has to go
or become something else — a neighbour's television, the radiator. **One chapter, two
sentences.** No decision needed; ch32 and ch35 agree against ch33.

## B7. "Aymar" is used as though it were somebody other than Ruth — **carried forward, still live**

Ruth's surname is established in ch10: `"Aymar. A, Y, M, A, R."`

Ch17, four lines apart:
> "It's seven and about a fifth, because I've timed thirty of them and the mechanism
> resets slow every time," **Aymar** says…
>
> A different card is taped to the bench later that week with a different number on it,
> and **Ruth** spends the rest of the term making sure people know the stopwatch it came
> off was **Aymar's**.

That last sentence reads as two people. Ch18 has "**Aymar** asks why, out loud, in the
tone of somebody asking on behalf of ninety people," in a chapter where she is otherwise
always Ruth.

The instructor Voss addressing her by surname is right and should stay. The **narration**
using it is what breaks. **Fix:** narration says Ruth; dialogue may say Aymar. Touches the
one sentence in ch17 and the one in ch18. **Two chapters, two sentences.**

## B8. Chapter 30 skips four of the six stages chapter 23 was built around — **new, and it is the two-standards case in the Chloe thread**

**Ch23 sets the clock explicitly:**
> "Twenty years old to sit it. **Twenty-one to be sworn in**, once the file behind it
> clears, and she turns eighteen in August."
>
> "…the age floor at twenty, the training year that sits behind the floor once you clear
> it, and **the six stages between passing the written test and actually being sworn in,
> each carrying its own open-ended timeline.** Then she runs the numbers forward from
> eighteen and shows him where a person would already have to be standing, at each of
> those stages, for the total to land anywhere close to twenty-one."
>
> "Six, roughly. Written test, personal narrative, oral assessment, medical, security
> review, the roster itself. **You only find out how long any of them actually takes once
> you're already inside it.**"

**Ch30 delivers:** written test (September 2025) → security review (October–December
2025) → "She starts in January." Four months. The personal narrative, the oral
assessment, the medical and the register never appear. And she starts in January 2026 at
**twenty**, against ch23's flat statement that you are sworn in at twenty-one.

This is the chapter-23 Chloe — who reads an eligibility page three times to be sure the
readings agreed, and builds two years of her life around its arithmetic — being handed a
process that ignores its own rules. It is also the only place in the book where the
research she did turns out not to have mattered.

There is a reading that saves it: **ch30 never names the January job.** Ch33 calls it
only "a job with a security clearance"; ch35 describes it as "the job of a government that
has been trying to find this man"; ch36 has her running searches in federal records. None
of that is the Foreign Service. If the January job is an intermediate federal post — the
kind ch23 itself gestures at, "half the internships that turn into a clearance start
walking distance from wherever I'm living" — then nothing contradicts anything, and the
Foreign Service is still ahead of her at the end of the book.

**But the text never says so**, and ch30 spends its whole second half on the Foreign
Service exam and then hands her a job, so the reader joins them.

**Options**

| | Fix | Chapters touched |
|---|---|---|
| a | One clause in ch30 naming the January job as something other than the appointment — and, ideally, one sentence acknowledging that the other four stages are still ahead of her | 1. Costs almost nothing and makes ch23's arithmetic pay off instead of evaporate. |
| b | Move the start past her August 2026 birthday | Rejected — ch33, ch34 and ch36 all count tenure from January. |
| c | Change ch23's "Twenty-one to be sworn in" to "twenty" | Rejected — the twenty-one rule is what generates the two-year Georgetown decision, which is the chapter's whole point. |

**I would take (a).** This is a decision the author needs to make, not a repair: it turns
on whether the book intends Chloe to have reached the Foreign Service by chapter 36 or to
still be two stages short of it.

## B9. Chloe's own two standards on confidentiality — **possibly deliberate, reporting for a decision**

Ch30, to a federal investigator holding her clearance:
> "There's a third one," Chloe says. "It's internal. I can tell you I worked on it, I can
> tell you when, I can tell you who ran it. **I've been asked not to say what it's about,
> and I said I wouldn't.**" … "Would you tell me if I said it was necessary?" … "I'd want
> to talk to her first."

Ch33, four months into the job that clearance bought:
> chloe: someones had a file on us since before any of us could read. if we get a chance
> to read theirs back i dont see what there is to decide

and ch34: "Chloe reads hers at her own desk, five months into a job whose clearance she is
stretching a long way past its purpose to do this."

She will not name a research topic to a cleared investigator because a researcher asked
her not to; she will help break into a classified federal file without visible
deliberation. **This is coherent characterisation — the loyalty runs to people and not to
institutions, and it has run that way since chapter 9 — and it is arguably the book's
thesis.** Ch33's line is the closest the text comes to saying so out loud.

**No fix required. Reported because it is the same class as A7 and because, unlike A7,
nobody in the book ever notices it.** If one line of notice is wanted, ch33's paragraph
beginning "A clearance is a piece of paper that says the government has already decided
to trust her" is where it already almost happens: "What that actually costs her she works
through exactly once, on the drive home … and the thought ends in about as long as it
takes a light to change." That sentence is doing the job. It may be enough.

---

# Part C — checked and clear, or too small to act on alone

Recorded so the next pass does not re-litigate them.

**Already fixed in the current text (the reviewer worked from an older draft):**

- `24_the_chat.md` — "The chat is nine years old" is now **five**. Correct. (But see B1 —
  the second half of the same sentence was not updated with it.)
- `29_the_file.md` — the loading-dock intrusion is now "**Eight years ago**", not six.
  Correct: winter 2017–18 to October 2025.
- `32_the_money.md` — "and **eight years ago** they sent people over the fence". Correct
  and now matches ch29.
- `34_the_files.md` — the incident report is now "**four years back**", not six. Correct:
  June 2022 to June 2026.
- `20_the_parking_lot.md` — Ruth's box is now "the box she built **at thirteen**", not
  "the year before". Correct.
- `23_the_first_one.md` / `30_cleared.md` — both June birthdays are now **August**.
- `23_the_first_one.md` — the corner joint is now "first cut **as children**", not "at
  fourteen". Correct against ch14.
- `30_cleared.md` — "I started **that April**, a few months after I turned seven" replaces
  the old "the September I turned seven", which contradicted ch7–ch10.
- `32_the_money.md` — Theo's ch32 disclosure now has the back-steps paragraph. It does not
  fully answer A7 but it is no longer undeliberated.
- `34_the_files.md` — "The unit assigned to observation of the school had their own
  recordings of that night. Those are gone too." This is new and it substantially changes
  the footage-erasure complaint in the review's §IV; it is handled in
  `passes/audit/AUTHOR_FIAT.md`, not here.

**Checked and consistent — no action:**

- The 10v1 progression. 4→6→11 seconds at ten (ch13); 24 by Christmas at twelve (ch15); a
  best of 50 and a year average of 45 at fourteen (ch17); an average of 41 at fifteen
  against "forty-five at fourteen" (ch18). The dip is deliberate and Kowalczyk explains it.
  Sam's 14 at ten (ch13) and Odile's 67 at fifteen (ch18) fit.
- Sam's PT test: "Six events, a hundred points available on each" → "The score is six
  hundred." ✅ *(One reading wobble in the same sentence: "Sam is meeting four of them for
  the first occasion in his life:" is followed by a list of six. The four are meant to be
  a subset, but the colon hands the reader all six. Half a comma's worth of work.)*
- Sam's forty percent: "since I was fifteen" (ch25) against "He's been there since he
  started" (ch19) — consistent; the intercept work begins at fifteen in ch18. *(Ch25's
  earlier "Forty percent, every year I was there" is looser than the same chapter's own
  "since I was fifteen"; worth an eye if the passage is touched.)*
- Chloe's eleven languages. Ch30 lists exactly eleven; ch23 says eleven. ✅
- Priya "sixty-fourth out of ninety-one … bottom third". ✅ (61–91 is the bottom third.)
- "Twelve seconds a name" × 91 names ≈ 18 minutes of reading. ✅
- "Seven men. Three firearms." (ch34) against "Seven, three armed." (ch20). ✅
- Twenty-two seconds: Ruth's count in ch20 against the report's in ch34. ✅ — and the
  report makes a point of it being the only figure that matches, which is good work.
- "Four students" in ch34 against four going over the fence in ch20 (Kavi drops out). ✅
- Sixteen weeks for the financial worm: ch32 opening against ch35's "settled it in sixteen
  weeks". ✅
- Job tenure: four / five / nine months in ch33 / ch34 / ch36 all count from January 2026. ✅
- Ruth's silence: ch28 has her go quiet in April; ch29's October post is "the first thing
  Ruth has posted in six months." ✅
- Amberg's "in two years most of you will be driving" said to thirteen-year-olds, against
  Chloe learning to drive at fifteen in ch18. ✅

**Small, low-confidence, listed only for completeness:**

- Ch34: Nadia's file crosses "a background check a competing job board ran on her
  **eighteen months ago**" — December 2024. The competing-job-board affair the book shows
  is ch27, May 2024, which is two years back. It survives if this is a separate later
  check; the laundromat detail is fine for December 2024 either way.
- Ch30 lists **Arabic** among Chloe's eleven. Arabic is Ruth's language everywhere else
  it appears (ch13, ch14, ch15). Korean and Swahili appear nowhere else at all. Probably
  intended as offstage coverage; Arabic is the one that reads as a swap.
- Ch16: "the school's network records which machine talked to which and when" and there
  are "a hundred and sixty machines" checking in — against ch23's "eight hundred children
  who are not graduating today". Not a contradiction (the machine count is the network
  segment, not the school), but the two numbers sit oddly if a reader tries to reconcile them.
- The eight-foot chain link fence in ch20 is in the review's **AUTHOR FIAT** section, not
  this one, and is handled in `passes/audit/AUTHOR_FIAT.md`.

---

# Decision list

**Already ruled by the author — execute, do not re-decide:**

| | Item | Work |
|---|---|---|
| A2 | Bar exam is internal; Chloe does not know it | Rewrite four lines of ch30 |
| A8 | Metadata solved by school-hardware hosting | One clause in ch24; optional second in ch34 |
| A1 | Birthday is August 2005 | Ch22 done in this pass; ch33 paragraph still to do |

**Needs a decision, in order of how much a reader would notice:**

| | Item | Chapters | My recommendation |
|---|---|---|---|
| A1 | Ch33's twenty-first birthday | 1 | Defer the birthday in the paragraph, don't cut it |
| B4 | File predates the school by two years | 1 (as fiat: 5) | Make it deliberate with one clause in ch29 |
| B8 | Ch30 skips four of ch23's six stages | 1 | Name the January job as not-the-appointment |
| A4 | "First to sneak out in ten years" | 1 | "since the school opened" |
| A5 | Clearance "in the autumn" | 1 | "just before Christmas" |
| B5 | Ch34 relocates the robbery to the car park | 1 | Correct the report's geography |
| A9 | The ch18–19 gap | 1 | Add a paragraph of bar-exam run-up to ch19 |
| A7 | Theo's ch32 deliberation | 1 | One sentence linking it back to ch29 |

**Unambiguous repairs, no decision required:**

| | Item | Chapters | Fix |
|---|---|---|---|
| B1 | Ch24 "in their first year here" | 1 | "at thirteen" |
| A3 | "a few billion codes" | 1 | "all million codes" |
| B2 | "ten exposures from each of five positions" | 1 | "eight exposures" |
| A6 | Duplicated Sam attribution | 1 | First line becomes Kavi |
| B6 | Ruth's dorm room in ch33 | 1 | Apartment, twice |
| B7 | "Aymar" in narration | 2 | Narration says Ruth |
| B3 | "four years, some of them longer" | 1 | "eleven years, some of them fewer" |
