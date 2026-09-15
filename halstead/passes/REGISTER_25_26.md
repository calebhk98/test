# Register pass: chapters 25 and 26

Readers flagged both chapters as noticeably more formal than the rest of the
book. Confirmed by the long-word measure (words of nine or more letters, as a
share of all words, narration + dialogue, title line excluded):

| chapter | before | after | words before | words after |
| --- | --- | --- | --- | --- |
| 25, Forty Targets | 5.55% | 2.81% | 3403 | 3380 |
| 26, The Exercise | 3.65% | 3.10% | 3616 | 3611 |

Both are now inside the range the rest of the book already occupies (book
median 2.54%), without being flattened down to the median. Word counts moved
by under 1% in both directions; nothing was cut, only substituted or unwound.
`style_report.py` was run on both chapters before and after: sentence-length
stats, the and-rate, section breaks, and the tic scan are all unchanged in
kind and magnitude (none of the pre-existing FAILs got worse, none newly
failed, tic scan still empty). No em dashes or curly quotes were introduced.
No new instance of the avoid-list constructions (`instead`, `both hands`,
`rather than`, etc.) was added; every occurrence still in the files predates
this pass. All named plot facts survive verbatim: the land-navigation
screening theory (tested and abandoned), the letters to the grandmother with
the six hundred kept out, Okoro, the root ball at the fence line, the culvert,
and the man at the end of the cut who says nothing gave him away.

## Method

Went sentence by sentence. Left technical and equipment vocabulary alone
(clipboard, harness, transmitter, controller, checkpoint, silhouettes,
barricade, intercept, land navigation, memorandum, counterintelligence,
qualification, sergeant/commander/captain rank terms) since these are
concrete, necessary nouns rather than ornate diction, and cutting them would
either lose accuracy or force an awkward paraphrase. Left officer dialogue
(the captain in 25, the major in 26) largely alone: a captain and a major are
expected to speak more formally than an enlisted private, and that contrast is
doing real characterization work, not drifting the narration. Two exceptions
went the other way: a line of Ruiz's dialogue ("every single word of this
conversation forgotten") and a line of Sam's own dialogue ("a considerable
amount of walking for very little, sir") were fixed, because a drill sergeant
and Sam himself are established as plain-spoken, and both lines had the same
formal tic as the narration around them.

## Constructions unwound (chapter 25)

- "Drill Sergeant Ruiz possesses a voice built for open ground and
  demonstrates no visible interest in owning the other kind." →
  "Drill Sergeant Ruiz has a voice built for open ground and shows no sign of
  owning the other kind."
- "in the manner of somebody settling in for the remainder of an argument he
  considers already concluded" → "the way somebody settles in for the rest of
  an argument he thinks is already over"
- "the men around him are being measured on something he has yet to be
  shown, are almost certainly holding a considerable amount back for it" →
  "...are almost certainly holding a good deal back for it" (and "an
  organization does when it wants to know who to send somewhere else" →
  "an outfit does when it wants to know who to send off")
- "with the particular variety of cold that reaches the fingers a
  considerable time before it reaches anything else" → "with the kind of cold
  that reaches the fingers well before it reaches anything else"
- The captain's paperwork paragraph (three memoranda) had the heaviest
  concentration of Latinate diction in the chapter: "describing" → "laying
  out," "conversation" → "talk," "specialised instruction from an
  unidentified source" → "special instruction from an unknown source,"
  "recommends that" → "says," "unexplained specialised training" →
  "unexplained special training," "reportable categories" → "flagged types,"
  "security questionnaire" → "security form," "establish whether" → "find out
  whether," "behavioral health referral...travels upward alongside" → "mental
  health referral...travels up with," "positioned well above the captain" →
  "well above the captain," "considerably older" → "far older."
- Smaller substitutions of the same shape throughout: possesses→has,
  eventually→later, whereupon/continues/entertaining cut, unhurried→
  slow/easy/taking his time (x3), precisely→exactly, satisfactory
  resolution→settling it, approximately→roughly, reconcilable→squares,
  comfortably→well, measurement→numbers, calendars→time, explanation/
  examination/experiment→idea/testing/test, progressively→getting,
  trailhead→head of the trail, cheerfully→gladly, distinctly→much,
  difficulty→trouble, reasonable→fair. "programme" (a stray British spelling)
  corrected to "program" for consistency with the rest of the book.
- `underneath`→`under` and `afterward`→`after` wherever they were pure
  prepositions doing no other work (four and three instances).
- `everybody`→`everyone` in narration only, three instances (left alone in
  Sam's own dialogue at line 85, where it's his word, not the narrator's).

## Constructions unwound (chapter 26)

- "the particular variety of cold..." pattern recurs here as "its own
  particular variety of long" → "its own kind of long."
- "the sky doing the slow work of turning into morning" → "the sky slowly
  turning to morning" (one of the two ch26 lines named directly in reader
  feedback).
- "worrying it like a bad weld" was left alone. It's a concrete, working
  trade image (Sam's family runs a hauling and equipment business), the kind
  of plain inherited-register simile the style rules want, not an ornate one.
- unhurried→easy (once) but kept once, deliberately, in "writes on the top
  sheet, unhurried" for the major, where a beat of formality suits an
  officer closing out a debrief; peculiarly→oddly, discharges→fires,
  Afterward→After that, method available→way, understands (kept once,
  reverted, see below)→largely left as-is, positioned (kept, see below),
  identical (kept, see below).
- Sam's own dialogue: "a considerable amount of walking for very little" →
  "a lot of walking for very little." This is the one line that actually
  contradicts his character sheet as written (he doesn't hedge or use a
  qualifying noun phrase like that), so the fix is a correctness fix as much
  as a register one.

## Overshoot and correction

A first pass on chapter 26 cut the long-word share to 2.24%, under the book
median. Per the brief ("without flattening them to the median"), about a
dozen of the more defensible original words were put back: `everything`,
`somewhere`, `identical`, `positioned` (x2), `following` (x2), `statement`
(x2), `temperature`, `regardless`, `throughout` (x2), both instances of
`unhurried`, `prohibited`/`whatsoever`/`authorised` in the safety-brief
paragraph (formal because it's a sergeant reading rules off a card verbatim,
which earns some formality), `simultaneously`/`confusing` in Ives's dialogue,
`understands`/`immediately`/`initiative`/`instructed`/`instructs`/
`returning`/`salvaging`/`arrangement`/`electronic`. Final figure: 3.10%.

## Left alone as Sam's own register, not the narration's

- "worrying it like a bad weld" (26) — concrete trade simile, in Sam's own
  head, earned by his family background.
- The captain's and major's set-piece speeches in both chapters — an
  officer correcting a private is allowed to sound like an officer; flattening
  those would have erased a real character distinction the book is using on
  purpose (enlisted plain speech vs. officer formality).
- Okoro's dry, elevated joke at the sinks ("If I were you I would build a
  considerably smaller theory on the evidence available") — his one clearly
  formal line, read as dry wit rather than narrator drift, and left standing.
- Technical/equipment nouns throughout (clipboard, harness, transmitter,
  controller, checkpoint, silhouettes, barricade, ammunition, projector,
  land navigation, counterintelligence, memorandum, qualification) — these
  are factual military vocabulary intrinsic to the scenes, not "ornate."
