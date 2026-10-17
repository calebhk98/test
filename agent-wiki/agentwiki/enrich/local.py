"""Enrichment with the embedding model only, no LLM.

- Tags: key phrases from the text ranked by similarity to the whole section
  (the KeyBERT method), plus topic categories chosen by similarity to a short
  description of each category (zero-shot classification).
- Summary: the sentences closest to the section's overall meaning, in their
  original order (extractive, so it never says anything the video did not).
- Facts: pattern matches for size, hardware, licence, censorship and so on.
"""
from __future__ import annotations

import re
from collections import Counter

import numpy as np

from ..models import Enrichment, Section, VideoInfo
from ..registry import register
from .base import Enricher, normalize_tags
from .facts import extract_facts, sentences
from .keyword import _STOP

# tag -> what it means. Override or extend with [enricher] categories in config.
DEFAULT_CATEGORIES = {
    "text-to-video": "AI video generation models that turn a text prompt into a video clip, like Sora, Veo, Kling, Wan, LTX, Runway",
    "image-to-video": "animating a still photo or image into a moving video clip",
    "text-to-image": "AI image generators that create pictures from a prompt, like Flux, Midjourney, Stable Diffusion, Imagen, Ideogram",
    "image-editing": "editing an existing photo with AI: inpainting, changing objects, style transfer, background removal",
    "text-to-speech": "AI voice generation, text to speech, voice cloning, like ElevenLabs",
    "speech-recognition": "transcribing spoken audio to text, like Whisper",
    "music-generation": "AI that composes songs and music with vocals, like Suno and Udio",
    "world-model": "world models that generate interactive explorable environments or simulate physics for robots and games",
    "3d-generation": "generating 3D meshes, 3D assets, Gaussian splats or NeRF scenes from images or text",
    "llm": "large language model releases and chatbots like GPT, Claude, Gemini, Llama, Qwen, DeepSeek",
    "coding-agent": "AI agents that write software code or operate a computer",
    "ai-agent": "autonomous AI agents that plan and complete multi-step tasks with tools",
    "robotics": "physical robots, humanoid robots, robot arms and robot learning",
    "science": "AI used for scientific discovery in biology, chemistry, physics, materials",
    "math": "AI solving mathematics problems, proofs and conjectures",
    "medicine": "AI in medicine, diagnosis, drug discovery and health care",
    "hardware": "AI chips, GPUs, data centers and computing hardware",
    "open-source": "open source or open weights models you can download and run yourself",
    "benchmark": "benchmark scores and leaderboards comparing AI models",
    "avatar": "talking head avatars, lip sync and digital humans",
    "upscaling": "upscaling, restoring or enhancing the resolution of images and video",
    "ai-safety": "AI safety, security, alignment, regulation and policy",
    "sponsor": "an advertisement or sponsored segment promoting a product",
}


def _words(text: str) -> list[str]:
    text = re.sub(r"['\u2019]s\b", "", text)          # possessives: "people's" -> "people"
    return [w.rstrip(".") for w in re.findall(r"[A-Za-z0-9][\w.+-]*", text)]


def _candidates(text: str, title: str, limit: int = 60) -> list[str]:
    """Phrases of 1-3 words with no filler word anywhere in them. A phrase must
    repeat, unless it looks like a name (capitals or digits: "Flux 3", "LTX-2")."""
    words = _words(text)
    counts: Counter[str] = Counter()
    for n in (1, 2, 3):
        for i in range(len(words) - n + 1):
            gram = words[i:i + n]
            lw = [w.lower() for w in gram]
            if any(w in _STOP or len(w) < 2 for w in lw):
                continue
            if n == 1 and (len(lw[0]) < 3 or lw[0].isdigit()):
                continue
            counts[" ".join(gram)] += 1
    # A name: every word capitalised or containing a digit ("Black Forest Labs",
    # "Flux 3", "LTX-2"). "Daniel mentioned" is not one.
    named = lambda p: all(w[0].isupper() or any(ch.isdigit() for ch in w) for w in p.split())
    counts = Counter({p: c for p, c in counts.items() if c >= 2 or named(p)})
    # Names (capitals or digits, like "Flux 3", "GPT", "LTX-2") count double.
    scored = sorted(counts.items(),
                    key=lambda kv: -(kv[1] * (2 if re.search(r"[A-Z0-9]", kv[0]) else 1)))
    seen, out = set(), []
    for phrase, _ in scored:
        key = phrase.lower()
        if key not in seen:
            seen.add(key)
            out.append(phrase)
        if len(out) >= limit:
            break
    return out


def _mmr(doc: np.ndarray, cands: np.ndarray, k: int, diversity: float = 0.5) -> list[int]:
    """Maximal marginal relevance: relevant to the doc, different from each other."""
    if len(cands) == 0:
        return []
    rel = cands @ doc
    chosen = [int(np.argmax(rel))]
    while len(chosen) < min(k, len(cands)):
        sim_to_chosen = (cands @ cands[chosen].T).max(axis=1)
        score = (1 - diversity) * rel - diversity * sim_to_chosen
        score[chosen] = -np.inf
        chosen.append(int(np.argmax(score)))
    return chosen


@register("enricher", "local")
class LocalEnricher(Enricher):
    def __init__(self, embedder, max_tags: int = 10, keyphrases: int = 5, summary_sentences: int = 2,
                 categories: dict[str, str] | None = None, max_categories: int = 3,
                 category_z: float = 1.7, max_chars: int = 6000):
        self.embedder = embedder
        self.max_tags = max_tags
        self.keyphrases = keyphrases
        self.summary_sentences = summary_sentences
        self.categories = categories or DEFAULT_CATEGORIES
        self.max_categories = max_categories
        self.category_z = category_z
        self.max_chars = max_chars
        self._cat_vecs = None

    @classmethod
    def from_config(cls, params, ctx=None):
        return cls(embedder=ctx.embedder, **params)

    @property
    def name(self) -> str:
        return f"local[{self.embedder.name}]"

    def _category_tags(self, vec: np.ndarray) -> list[str]:
        names = list(self.categories)
        if self._cat_vecs is None:
            # Categories as queries, the section as a document: retrieval-trained
            # encoders (Qwen3, EmbeddingGemma) rank much better asymmetrically.
            # On a real image-generation section, symmetric scoring ranked
            # 3d-generation first and text-to-image fourth; this puts it first.
            self._cat_vecs = np.vstack([self.embedder.embed_query(f"{n.replace('-', ' ')}: {d}")
                                        for n, d in self.categories.items()])
        sims = self._cat_vecs @ vec
        z = (sims - sims.mean()) / (sims.std() + 1e-6)
        order = np.argsort(-sims)
        return [names[i] for i in order[: self.max_categories] if z[i] >= self.category_z]

    def enrich_section(self, info: VideoInfo, section: Section) -> Enrichment:
        text = section.text[: self.max_chars]
        sents = sentences(text)
        cands = _candidates(text, section.title)
        if not text or not sents:
            return Enrichment(tags=normalize_tags([section.title]), model=self.name)
        vecs = self.embedder.embed_documents([f"{section.title}. {text}"] + cands + sents)
        doc, cand_v, sent_v = vecs[0], vecs[1:1 + len(cands)], vecs[1 + len(cands):]

        phrases = [cands[i] for i in _mmr(doc, cand_v, self.keyphrases)]
        cats = ["sponsor"] if section.is_sponsor else \
            [c for c in self._category_tags(doc) if c != "sponsor"]
        # A short title is a name ("Flux 3") and makes a good tag; a long one
        # ("Why Robots Need Open Models") is a sentence and does not.
        named = [section.title] if len(section.title.split()) <= 3 else []
        tags = normalize_tags(named + [l.label for l in section.links[:2]] + cats + phrases,
                              self.max_tags)

        # Summaries should be statements, not the host's questions or rambles.
        weight = np.array([0.0 if s.rstrip().endswith("?") or not 6 <= len(s.split()) <= 45 else 1.0
                           for s in sents])
        usable = weight > 0
        if usable.any():
            idx = np.flatnonzero(usable)
            picked = sorted(idx[i] for i in _mmr(doc, sent_v[idx], self.summary_sentences, diversity=0.3))
        else:
            picked = sorted(_mmr(doc, sent_v, self.summary_sentences, diversity=0.3))
        summary = " ".join(sents[i] for i in picked)
        return Enrichment(summary=summary, tags=tags, facts=extract_facts(section.text),
                          model=self.name)

    def enrich_video(self, info, sections, transcript_text) -> Enrichment:
        topics = [s.title for s in sections if not s.is_sponsor]
        summary = ""
        if info.description:
            first = sentences(info.description.split("\n")[0])
            summary = first[0] if first else ""
        if topics:
            summary = (summary + " " if summary else "") + f"Covers {len(topics)} topics: " + \
                      ", ".join(topics) + "."
        counts = Counter(t for s in sections if not s.is_sponsor for t in s.tags)
        cat_counts = [t for t, _ in counts.most_common() if t in self.categories]
        tags = normalize_tags(info.source_tags + cat_counts + [t for t, _ in counts.most_common(8)],
                              self.max_tags + 5)
        return Enrichment(summary=summary, tags=tags, model=self.name)
