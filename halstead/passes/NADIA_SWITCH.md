# Nadia's switch — pass record

Chapter 27 only. Two additions plus one required removal, all exact-string
edits, no line-index splicing.

## Her age

Stated directly in the chapter's own dialogue, no inference needed: when the
man at the folding table asks "How old are you," Nadia answers "Eighteen
since last June." The chapter is dated May 2024, so she has been eighteen for
about eleven months and will turn nineteen the following month. `NADIA.md`'s
book-specific section confirms the same year (born June 2005) and calls the
seventeen/eighteen span the one where "the emotional range has to be
widest... the first fear that has any weight in it." The friends' alarm in
the chat is written to that: ordinary fear for a very young friend who went
into a room alone, not tactical concern, and nobody says or implies she or
they are trained. That is the joke the book is playing and the addition
leaves it alone — nobody in the new chat lines comes anywhere near noticing
it.

## Beat one — what she says in the room

Inserted immediately after the men's rebuttal that nobody actually watched
her go up the stairs (the tire shop had already closed, so her earlier
"a shop full of people saw me go up" claim is undercut in the text before
mine runs). That is where a second, independent form of leverage belongs,
right after the first one gets taken away from her:

> "There's a file that sends itself if I don't stop it by nine tonight. It
> goes to the state attorney general's office and to two reporters, with
> this address in it, the agent's name, and the time I walked up here
> today. If I don't go home, it sends anyway. Then this isn't nine people
> phished for a routing number anymore. It's four men who kidnapped and
> killed an eighteen-year-old for saying a number out loud to their faces,
> and every one of you goes down for that."

Followed by one camera line — "The man at the window turns from the glass
and looks at the man behind the desk." — and then the scene continues into
her existing "I'm not calling the police" speech. No claim is made anywhere
about whether the file is real; per the brief, that is deliberately left
open. It works well enough that the confrontation proceeds on her terms from
there and she walks out under her own power at the end of the scene, unchanged
from the existing text.

## The required removal

`"Say that again," he says, "slower, so everybody in the room gets the
benefit of it."` was the exact construction the author has ruled out
(comma + "so" trailing explanatory clause, house rule 1's commonest form).
Replaced with:

> "Say that again," he says. "Slower."

This keeps the beat that follows it intact and even sharpens it: the next
line, "At the same speed, she gives it back to him," is the point of the
exchange — he tells her to slow down, and she doesn't — so "slower" had to
survive as content. Only the reader-facing justification for it was cut.

## Beat two — the chat

Appended to the existing post-confrontation chat block (`nadia`, `sam`,
`ruth`, `eli`, the same three friends already in that scene), after her
existing "eli if you go anywhere near it, it stops being over" line and
before the section break:

```
ruth: nadia what actually happened up there
nadia: i told them i had a file that sends itself if anything happens to me
nadia: it goes to the state and to two reporters. my name, the office address, the time i went up. if i dont come home by nine it goes out on its own
sam: youre eighteen years old
nadia: i know how old i am
ruth: there were four of them and you had nothing else up there if it went wrong
nadia: i had it covered. if anything happened to me the file still goes out and they still go down for it
eli: nadia a dead mans switch only pays off if youre already dead
eli: if they had called it you would be dead right now and it would have worked exactly like you built it
eli: that isnt you being safe up there. thats you being lucky
ruth: those are actual criminals. not a hiring committee that tells you no and lets you walk
nadia: i know what they are
sam: then why did you go up there alone
nadia: it was my name on the site. nobody else was going to stand in that room
eli: nadia do you get what were saying
nadia: yes
```

**Who says what:** Sam and Ruth carry the ordinary fear — his age, her
"there were four of them and you had nothing else up there" — neither one
tactical, neither one mentioning training or skill, because it hasn't
occurred to either of them that either of them has any. Nadia's own defense
is exactly the switch, twice: she "had it covered," and it was her name on
the site so nobody else was going to go stand in that room. **Eli takes the
switch apart** — the line that does the work of the author's own "you would
be dead right now if they called the bluff": "if they had called it you
would be dead right now and it would have worked exactly like you built it,"
followed by "that isnt you being safe up there. thats you being lucky."
Ruth then places the men correctly: "those are actual criminals. not a
hiring committee that tells you no and lets you walk" — a deliberate echo of
the chapter's own hiring-company material, not commented on by the
narration.

**Where it lands:** the last line is Nadia's, and it is "yes" — one word,
answering Eli's "do you get what were saying." She does not defend the
decision to go, does not concede she should have stayed home, does not
joke it off. It lands and she does not shrug it off, per the brief; she also
does not get talked into agreeing the trip itself was wrong, since nothing
in the new lines walks that back.

## Checks run

- `python3 measures/style_report.py chapters/27_nadia.md` — read for
  individual hits per the house instructions (never the pass/fail source).
  The two `[superlative] ... for the first time ...` tic hits it prints are
  both pre-existing lines untouched by this pass ("sits back in the chair
  for the first time since she came through the door" and "works the
  counter... for the first time since November"). No new tic-scan or
  trailing-explanatory-clause hits appear in the added text; I checked the
  new dialogue by hand for the banned comma + so/which/because pattern and
  for a bare `, because` inside any of it and found none.
- `python3 measures/check_edits.py --chapters 27` — 0 problems: no em
  dashes, no curly quotes, no hard-break lines, word count 4,823 (chapter
  was 4,501 before this pass; ceiling is 5,000, average-across-book target
  is a separate concern for whoever runs `grade.py`).
- Did not run `grade.py` (other agents active). Did not touch
  `HALSTEAD.md`. Did not open any other chapter.

## Things worth a second look

- I did not add "instead," "the whole/rest of it," or another instance of
  "same" anywhere in the new text, since the brief flagged those as at
  their ceiling already; worth re-checking with `absolutes.py` /
  `tics.py` on a full `grade.py` run once other agents are clear, since I
  did not run those two directly.
- The chat reveal assumes the reader already knows, from the room scene
  just above it, roughly what the file threat said; the chat restates the
  content rather than just referencing it, on the view that a group chat
  where someone says "i told them i had something" without saying what
  would read as coy in a way that doesn't fit how bluntly this cast talks
  to each other elsewhere in the book.
