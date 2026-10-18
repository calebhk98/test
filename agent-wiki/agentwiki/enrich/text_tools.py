"""Text helpers shared by the model-free parts and the topic segmenter."""
from __future__ import annotations

import re
from collections import Counter

import numpy as np

STOP_WORDS = set("""a about above after again against all also am an and any are as at be because been
before being below between both but by can could did do does doing down during each few for from
further had has have having he her here hers him his how i if in into is it its itself just like
me more most my no nor not now of off on once only or other our out over own really right same
says she should so some such than that the their them then there these they this those through
to too under until up very was way we were what when where which while who whom why will with
would you your yours gonna wanna yeah okay ok um uh let lets thing things going get got go see
one two three new also basically actually here's it's that's there's you're we're they're i'm
don't can't isn't won't just video videos look looks pretty much even still know make makes
want well super quite every given instead kind maybe lot bit stuff something anything
everything someone people person able around always another back being better big called
come comes coming different done enough far first give good great guess huh hey human idea
important interesting last little long made many mean means mm need needs never next
nice part probably put rather said say saying sense show since sort start sure take talk
talking tell thank thanks think thinking thought time today together try trying turn use
used uses using whether work working works yes yet year years""".split())


def split_sentences(text: str, window_words: int = 28) -> list[str]:
    """Sentences, or fixed word windows when the text has almost no punctuation
    (YouTube auto-captions, and Whisper on fast speech)."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if len(sentences) * 60 < len(text.split()):
        words = text.split()
        sentences = [" ".join(words[start:start + window_words])
                     for start in range(0, len(words), window_words)]
    return sentences


def first_sentences(text: str, count: int, max_characters: int = 600) -> str:
    joined = " ".join(split_sentences(text)[:count]).strip()
    return joined if len(joined) < max_characters else joined[: max_characters - 3] + "..."


def _words(text: str) -> list[str]:
    text = re.sub(r"['’]s\b", "", text)          # possessives: "people's" -> "people"
    return [word.rstrip(".") for word in re.findall(r"[A-Za-z0-9][\w.+-]*", text)]


def looks_like_name(phrase: str) -> bool:
    """Every word capitalised or containing a digit: "Black Forest Labs", "Flux 3"."""
    return all(word[0].isupper() or any(char.isdigit() for char in word) for word in phrase.split())


def phrase_candidates(text: str, limit: int = 60, stop_words: set[str] = STOP_WORDS) -> list[str]:
    """Phrases of 1-3 words with no filler word anywhere in them. A phrase must
    repeat, unless it looks like a name."""
    words = _words(text)
    counts: Counter[str] = Counter()
    for phrase_length in (1, 2, 3):
        for start in range(len(words) - phrase_length + 1):
            phrase_words = words[start:start + phrase_length]
            lowered = [word.lower() for word in phrase_words]
            if any(word in stop_words or len(word) < 2 for word in lowered):
                continue
            if phrase_length == 1 and (len(lowered[0]) < 3 or lowered[0].isdigit()):
                continue
            counts[" ".join(phrase_words)] += 1
    kept = {phrase: count for phrase, count in counts.items() if count >= 2 or looks_like_name(phrase)}
    # Names count double when ranking.
    ranked = sorted(kept.items(), key=lambda item: -(item[1] * (2 if looks_like_name(item[0]) else 1)))
    seen_lowercase, unique_phrases = set(), []
    for phrase, _ in ranked:
        if phrase.lower() not in seen_lowercase:
            seen_lowercase.add(phrase.lower())
            unique_phrases.append(phrase)
        if len(unique_phrases) >= limit:
            break
    return unique_phrases


def maximal_marginal_relevance(document_vector: np.ndarray, candidate_vectors: np.ndarray, count: int,
                               diversity: float = 0.5) -> list[int]:
    """Indices of candidates relevant to the document and different from each other."""
    if len(candidate_vectors) == 0:
        return []
    relevance = candidate_vectors @ document_vector
    chosen = [int(np.argmax(relevance))]
    while len(chosen) < min(count, len(candidate_vectors)):
        similarity_to_chosen = (candidate_vectors @ candidate_vectors[chosen].T).max(axis=1)
        combined_score = (1 - diversity) * relevance - diversity * similarity_to_chosen
        combined_score[chosen] = -np.inf
        chosen.append(int(np.argmax(combined_score)))
    return chosen


def text_windows(text: str, words_per_window: int = 300, max_windows: int = 6) -> list[str]:
    """Pieces short enough for 512-token encoders (GLiNER, NLI classifiers)."""
    words = text.split()
    return [" ".join(words[start:start + words_per_window])
            for start in range(0, len(words), words_per_window)][:max_windows] or [""]
