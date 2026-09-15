> Read `passes/HOUSE_RULES.md` first. Its constraints outrank every
> target in this brief, including the reading-grade bands, which have
> replaced the single Flesch-Kincaid 9.0 figure used below.

# Dialogue brief — the whole book

The measurement, before anything else. This manuscript's spoken sentences average **9.4 words**.
Twenty-one of twenty-seven chapters sit under ten. Eight sit inside the band occupied by the
easiest-reading books in the reference corpus (Hemingway, 6.2–8.7). Up to a third of spoken lines
in some chapters are three words or fewer.

The reference books that read hardest are not harder because of their vocabulary. Black Beauty
uses **shorter** words than this book — 1.272 syllables per word against 1.306 — and reads four and
a half grades higher. The entire difference is sentence length: 27 to 29 words against 15.7.

So this is not a vocabulary job and not a "make it fancier" job. It is people finishing their
sentences.

## The target

- **Two to three sentences per speech**, where the speech is a real turn in a conversation.
- **About 20 to 25 words per sentence.**
- **One-word and two-word answers are the thing to hunt.** "Yeah" becomes "Yeah, I know that. What
  I was actually saying was —". "I know" becomes "I already know that, but we could still do Y."
  Very, very rarely should a reply be that short.

## The rule that replaced the old one

An earlier pass ran on this test: *is the character choosing not to say something?* It licensed
almost everything, because almost any clipped line can be read as somebody withholding. It is
withdrawn.

The test now: **what would this person actually say here, if nothing were stopping them?** Write
that. Then cut back only where something specific and nameable is stopping them — a rule, a
listener who has hurt them, a thing that cannot be said in front of the person in the room.

"They are trained to be economical" covers the drill floor and the command register. It does not
cover breakfast, an argument with a friend, a parent asking a question, or a teacher explaining
something.

## What longer does not mean

**Not more words for the same thought.** The corpus books are longer because a speech carries its
own reasoning: the claim, then the because, then the consequence or the exception. From Little
Women: *"You'll spoil it if you do, for the interest of the story is more in the minds than in the
actions of the people, and it will be all a muddle if you don't explain as you go on."* Claim,
reason, conditional consequence — one breath, three joints.

**Not speeches.** Nobody orates, nobody monologues at someone who has not asked.

**Not uniform.** The corpus books are full of short lines too. What they do not have is *only*
short lines. Keep a flat "No" where a flat "No" is the whole answer to a yes-or-no question.

## Characters

Read `characters/NAME.md` for everyone who speaks. Their **relative** differences survive: Sam
stays the shortest and plainest, Ruth still states the assertion and then the reason and still
names the person she is correcting, Kavi is still either short or one unbroken technical run,
Chloe still builds a concrete parallel scenario and argues that.

What changes is the floor. Sam's one flat clause becomes one flat clause plus the reason for it,
not three sentences of introspection. Kavi's technical runs should actually appear; they are
currently almost absent. If a sheet's dial says 3/10 wordiness, that is a statement about him
relative to the others, not a licence for two-word lines.

**If you decide a character genuinely cannot be lengthened anywhere, you are almost certainly
wrong.** Say which lines and why, in the report, and expect to be argued with.

## Also flag, do not fix

**Summary inside a dialogue scene.** Narration that compresses an exchange the reader should have
watched: "they argue about it for a while," "she asks three times in three different ways and gets
the same answer," "he tells her about the whole afternoon." List every one you find with its line
number. Do not rewrite them in this pass.

## Measuring

Per chapter, before and after:

    python3 grade.py --one chapters/NN_name.md

and the spoken mean:

    python3 -c "
    import statistics as st, importlib.util, sys; sys.argv=['x']
    spec = importlib.util.spec_from_file_location('ds','dialogue_study.py')
    ds = importlib.util.module_from_spec(spec); spec.loader.exec_module(ds)
    t = open('chapters/NN_name.md').read()
    t,_ = ds.pg.strip_transcript(t)
    sp,_n = ds.spoken_and_narrated(t)
    sl = ds.sent_lengths(sp)
    print('spoken mean', round(st.fmean(sl),1), 'over', len(sl), 'sentences;',
          round(100*sum(1 for x in sl if x<=3)/len(sl)), '% are 1-3 words')
    "

**Aim for a spoken mean of 16 or better and 1–3 word lines under 8 per cent.** Report both.

Then `python3 build_manuscript.py`. Do not let negative space rise above 5 per cent — every agent
writing new prose into this book so far has spiked it, so check before you finish.

## Write as you go

The container has restarted twice and killed agents mid-run. Create your report file in your first
few tool calls and append after each chapter rather than composing it at the end.
