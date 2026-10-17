"""Summarizers: section -> a short summary."""
from __future__ import annotations

import re

import numpy as np

from .. import hardware
from ..registry import register
from .base import PartUnavailable, Summarizer
from .text_tools import first_sentences, maximal_marginal_relevance, split_sentences, text_windows


@register("summarizer", "extractive")
class ExtractiveSummarizer(Summarizer):
    """The sentences closest to the section's overall meaning, quoted in their
    original order. Never says anything the video did not, but reads like
    speech. Skips questions and very short or very long sentences."""

    def __init__(self, embedder, sentence_count: int = 2, max_characters: int = 6000):
        self.embedder = embedder
        self.sentence_count = sentence_count
        self.max_characters = max_characters

    @classmethod
    def from_config(cls, params, app=None):
        return cls(embedder=app.embedder, **params)

    @property
    def name(self) -> str:
        return f"extractive[{self.embedder.name}]"

    def summarize_section(self, video_info, section):
        sentences = split_sentences(section.text[: self.max_characters])
        if not sentences:
            return ""
        vectors = self.embedder.embed_documents([f"{section.title}. {section.text[: self.max_characters]}"]
                                                + sentences)
        section_vector, sentence_vectors = vectors[0], vectors[1:]
        usable = np.array([not sentence.rstrip().endswith("?") and 6 <= len(sentence.split()) <= 45
                           for sentence in sentences])
        positions = np.flatnonzero(usable) if usable.any() else np.arange(len(sentences))
        chosen = maximal_marginal_relevance(section_vector, sentence_vectors[positions],
                                            self.sentence_count, diversity=0.3)
        return " ".join(sentences[positions[choice]] for choice in sorted(chosen))


@register("summarizer", "first-sentences")
class FirstSentencesSummarizer(Summarizer):
    def __init__(self, sentence_count: int = 2):
        self.sentence_count = sentence_count

    def summarize_section(self, video_info, section):
        return first_sentences(section.text, self.sentence_count)


@register("summarizer", "seq2seq")
class Seq2SeqSummarizer(Summarizer):
    """A model trained only to summarise (BART, PEGASUS, Long-T5). Writes new
    sentences, unlike the extractive summarizer, but was trained on news and
    papers rather than speech. On AI Search sections DistilBART wrote the most
    informative summaries of the three kinds tested, at about 4 s a section
    on CPU; see TESTING.md."""

    def __init__(self, model: str = "sshleifer/distilbart-cnn-12-6", max_summary_tokens: int = 90,
                 min_summary_tokens: int = 25, words_per_window: int = 600, device: str = "auto"):
        self.model_name = model
        self.max_summary_tokens = max_summary_tokens
        self.min_summary_tokens = min_summary_tokens
        self.words_per_window = words_per_window
        self.device = device
        self._tokenizer = None
        self._model = None

    @property
    def name(self) -> str:
        return f"seq2seq[{self.model_name}]"

    def is_available(self) -> bool:
        try:
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def _load(self):
        # Loaded directly: transformers 5 removed the "summarization" pipeline.
        if self._model is None:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            device = hardware.detect().device if self.device == "auto" else self.device
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(device).eval()
            except (OSError, ValueError) as error:
                raise PartUnavailable(f"could not load {self.model_name}: {error}") from error
        return self._tokenizer, self._model

    def summarize_section(self, video_info, section):
        if not section.text.strip():
            return ""
        import torch
        tokenizer, model = self._load()
        # Long sections: summarise the first window; chapters are usually short.
        window = text_windows(section.text, self.words_per_window, max_windows=1)[0]
        inputs = tokenizer(window, return_tensors="pt", truncation=True, max_length=1024).to(model.device)
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=self.max_summary_tokens,
                                    min_new_tokens=self.min_summary_tokens, num_beams=4, do_sample=False)
        summary = tokenizer.decode(output[0], skip_special_tokens=True).strip()
        # CNN-trained models put a space before every full stop ("beast .").
        return re.sub(r"\s+([.,!?])", r"\1", summary)
