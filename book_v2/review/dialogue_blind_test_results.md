# Blind dialogue-attribution test — results

A fresh agent read ONLY the stripped quiz (28 lines + a 12-name roster), never the
answer key or chapters, and attributed each line by MANNER alone. I then graded its
guesses against the key. This measures cross-character distinctiveness empirically.

## Score
- **10 of 27 correct (~37%)** (line 25 excluded — it's an off-roster speaker the agent
  couldn't have placed).
- Random chance with a 12-name roster ≈ 8%. So **~4.6× better than chance** — the voices
  ARE differentiated, but the absolute hit-rate is modest.
- **Of the agent's 10 HIGH-confidence guesses, only 4 were right (40%).** It was
  *confidently* fooled more often than not — and always in the same way (see below).

### Correct (10): lines 1, 9, 10, 11, 12, 16, 18, 22, 24, 27
The reliably-distinct voices: Apollodorus's builder-aphorisms (10/11/12), Ulpia's child
boast (27), Hadrian's epigram (24), Celer's grim soldier line (9), Tyche's flat city
fact (16), Trajan's honesty-maxim (22).

## The blurs (every error fell inside a "voice family")
The misses are not random — they cluster into a handful of families, which is itself the
finding. The agent's own notes admit it collapsed the cast into ~4 buckets.

1. **Marcia ↔ Tyche (worldly/commercial women) — the worst blur.** Marcia's mercantile
   line 17 → guessed Tyche; Tyche's lines 20 & 21 → guessed Marcia. The two
   transactional women are nearly interchangeable on the page.
2. **Heras ↔ the blunt men (Macer / Celer / Apollodorus).** All four of Heras's dry-wit
   lines (2,3,4,6) were scattered across Macer, Celer, and Apollodorus. His irony reads
   as generic "blunt Roman man." (Note: the signature-map agent rated Heras distinct;
   the blind test disagrees — his *manner* didn't survive tag-removal.)
3. **Hermes ↔ Macer.** Hermes's signature "Tell me one number I can do twice" (14) was
   given to Macer with HIGH confidence — the two numbers-demanding craftsmen share a
   manner. (Again, the signature map called Hermes "most distinct"; the blind test
   shows his *content* is distinct but his *voice* blurs with Macer.)
4. **Trajan ↔ Hadrian (the two emperors).** Hadrian's line 23 → Trajan; both rulers
   speak in cool appraising maxims.
5. **Procula ↔ Apollodorus.** Procula's mechanical dictum (28) → Apollodorus; both
   render engineer's principles in the same chiastic "the X must rule the Y" shape.

## What this confirms
The blind test independently reproduces the signature-map's "weak seam": **the cast
shares a fondness for the polished, antithetical epigram**, so distinct *people* collapse
into a few distinct *registers* (blunt-craftsman, ruler-maxim, worldly-woman,
engineer-dictum). When a line leans on that shared epigram cadence, the speaker becomes
guessable only by domain/content, not by voice.

### Tension between the two methods
The signature-map (reading WITH tags) judged Hermes and Heras among the *most* distinct;
the blind test (tags removed) confused both. Reading a labeled scene, you perceive
distinctiveness that may actually be coming from *attribution + context*, not from the
words themselves. The blind result is the more honest measure of pure voice.

## Practical takeaway
Genuinely distinct, characterful standouts exist (Apollodorus, Ulpia, Hadrian, Tyche's
flattest lines) — so the cast is NOT homogenized. But to tighten it: (1) differentiate
Marcia from Tyche (give one of them a non-commercial register), (2) stop routing every
sharp character through the antithetical-epigram cadence, and (3) give Heras and Hermes
a syntactic tic that isn't just "blunt."

Files: quiz `parts/attribution_quiz.md`, key `parts/attribution_key.md`, guesses
`parts/attribution_guesses.md`.
