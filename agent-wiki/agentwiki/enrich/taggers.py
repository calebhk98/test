"""Taggers: section -> tags. Combine several in config; each adds its own kind of tag."""
from __future__ import annotations

from collections import Counter

import numpy as np

from ..registry import register
from .base import PartUnavailable, Tagger
from .gliner_model import DEFAULT_GLINER_MODEL, gliner_installed, load_gliner
from .text_tools import STOP_WORDS, maximal_marginal_relevance, phrase_candidates, text_windows

# tag -> what it means. Override with `categories = {...}` on any category tagger.
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
}


@register("tagger", "title-and-links")
class TitleAndLinkTagger(Tagger):
    """The chapter title when it is a name ("Flux 3"), and the labels of the
    links the description gives for it. Long titles are sentences, not tags."""

    def __init__(self, max_title_words: int = 3, max_links: int = 2):
        self.max_title_words = max_title_words
        self.max_links = max_links

    def tag_section(self, video_info, section):
        tags = [section.title] if len(section.title.split()) <= self.max_title_words else []
        tags += [link.label for link in section.links[: self.max_links]]
        if section.is_sponsor:
            tags.insert(0, "sponsor")
        return tags


@register("tagger", "embedding-categories")
class EmbeddingCategoryTagger(Tagger):
    """Zero-shot topic categories by embedding similarity, no extra model.

    Categories are embedded as search queries and the section as a document;
    retrieval-trained encoders rank much better that way round. A category is
    kept when its score stands out from the others (z-score), so the
    threshold does not depend on which encoder is configured."""

    def __init__(self, embedder, categories: dict[str, str] | None = None, max_categories: int = 3,
                 z_threshold: float = 1.7, max_characters: int = 6000):
        self.embedder = embedder
        self.categories = categories or DEFAULT_CATEGORIES
        self.max_categories = max_categories
        self.z_threshold = z_threshold
        self.max_characters = max_characters
        self._category_vectors = None

    @classmethod
    def from_config(cls, params, app=None):
        return cls(embedder=app.embedder, **params)

    @property
    def name(self) -> str:
        return f"embedding-categories[{self.embedder.name}]"

    def tag_section(self, video_info, section):
        if section.is_sponsor or not section.text:
            return []
        if self._category_vectors is None:
            self._category_vectors = np.vstack([
                self.embedder.embed_query(f"{name.replace('-', ' ')}: {description}")
                for name, description in self.categories.items()])
        section_vector = self.embedder.embed_documents(
            [f"{section.title}. {section.text[: self.max_characters]}"])[0]
        similarities = self._category_vectors @ section_vector
        z_scores = (similarities - similarities.mean()) / (similarities.std() + 1e-6)
        names = list(self.categories)
        best_first = np.argsort(-similarities)[: self.max_categories]
        return [names[position] for position in best_first if z_scores[position] >= self.z_threshold]


@register("tagger", "keyphrases")
class KeyphraseTagger(Tagger):
    """Key phrases from the section itself, ranked by similarity to the whole
    section with the embedder (the KeyBERT method). Finds specific terms
    like "flow matching" that no fixed category list has."""

    def __init__(self, embedder, count: int = 4, extra_stop_words: list[str] | None = None,
                 max_characters: int = 6000):
        self.embedder = embedder
        self.count = count
        self.stop_words = STOP_WORDS | {word.lower() for word in extra_stop_words or []}
        self.max_characters = max_characters

    @classmethod
    def from_config(cls, params, app=None):
        return cls(embedder=app.embedder, **params)

    @property
    def name(self) -> str:
        return f"keyphrases[{self.embedder.name}]"

    def tag_section(self, video_info, section):
        text = section.text[: self.max_characters]
        candidates = phrase_candidates(text, stop_words=self.stop_words)
        if not candidates:
            return []
        vectors = self.embedder.embed_documents([f"{section.title}. {text}"] + candidates)
        chosen = maximal_marginal_relevance(vectors[0], vectors[1:], self.count)
        return [candidates[position] for position in chosen]


@register("tagger", "word-counts")
class WordCountTagger(Tagger):
    """Most frequent non-filler words. Needs nothing at all; crude."""

    def __init__(self, count: int = 6):
        self.count = count

    def tag_section(self, video_info, section):
        words = [word.lower() for word in section.text.split()]
        counts = Counter(word.strip(".,!?") for word in words
                         if word.strip(".,!?") not in STOP_WORDS and len(word) > 2)
        return [word for word, _ in counts.most_common(self.count)]


DEFAULT_ENTITY_LABELS = {
    "AI model": "name of a specific AI model, tool or product, such as Flux 2, GPT 6, Veo 4, Whisper",
    "company": "company, lab or organization that builds AI, such as Black Forest Labs, NVIDIA, OpenAI",
}


@register("tagger", "gliner-entities")
class GlinerEntityTagger(Tagger):
    """Names of models, tools and companies, found by a dedicated extraction
    model (GLiNER2). On real transcripts it found "Flux 2", "Black Forest
    Labs", "Suno" with high confidence, which key phrases miss."""

    def __init__(self, model: str = DEFAULT_GLINER_MODEL, labels: dict[str, str] | None = None,
                 min_confidence: float = 0.8, max_tags: int = 6, device: str = "auto"):
        self.model_name = model
        self.labels = labels or DEFAULT_ENTITY_LABELS
        self.min_confidence = min_confidence
        self.max_tags = max_tags
        self.device = device

    @property
    def name(self) -> str:
        return f"gliner-entities[{self.model_name}]"

    def is_available(self) -> bool:
        return gliner_installed()

    def tag_section(self, video_info, section):
        if section.is_sponsor:
            return []
        model = load_gliner(self.model_name, self.device)
        confidence_by_name: dict[str, float] = {}
        for window in text_windows(section.text):
            try:
                result = model.extract_entities(window, self.labels, include_confidence=True)
            except RuntimeError as error:   # out of memory and similar
                raise PartUnavailable(str(error)) from error
            for found in result.get("entities", {}).values():
                for entity in found:
                    if entity["confidence"] >= self.min_confidence:
                        key = entity["text"].strip()
                        confidence_by_name[key] = max(confidence_by_name.get(key, 0), entity["confidence"])
        ranked = sorted(confidence_by_name, key=confidence_by_name.get, reverse=True)
        return ranked[: self.max_tags]


@register("tagger", "zero-shot-categories")
class ZeroShotCategoryTagger(Tagger):
    """Topic categories from an NLI zero-shot classifier, a model trained only
    to decide whether a text is about a given label. Slower than the
    embedding tagger; see TESTING.md for how they compared."""

    def __init__(self, model: str = "MoritzLaurer/deberta-v3-large-zeroshot-v2.0",
                 categories: dict[str, str] | None = None, min_probability: float = 0.8,
                 max_categories: int = 3, max_windows: int = 2, device: str = "auto"):
        self.model_name = model
        self.categories = categories or DEFAULT_CATEGORIES
        self.min_probability = min_probability
        self.max_categories = max_categories
        self.max_windows = max_windows
        self.device = device
        self._classifier = None

    @property
    def name(self) -> str:
        return f"zero-shot-categories[{self.model_name}]"

    def is_available(self) -> bool:
        try:
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def tag_section(self, video_info, section):
        if section.is_sponsor or not section.text:
            return []
        if self._classifier is None:
            from .. import hardware
            from transformers import pipeline
            device = hardware.detect().device if self.device == "auto" else self.device
            try:
                self._classifier = pipeline("zero-shot-classification", model=self.model_name,
                                            device=0 if device == "cuda" else device)
            except OSError as error:
                raise PartUnavailable(f"could not load {self.model_name}: {error}") from error
        names, descriptions = list(self.categories), list(self.categories.values())
        best_probability: dict[str, float] = {}
        for window in text_windows(section.text, max_windows=self.max_windows):
            result = self._classifier(window, descriptions, multi_label=True,
                                      hypothesis_template="This text is about {}.")
            for description, probability in zip(result["labels"], result["scores"]):
                category = names[descriptions.index(description)]
                best_probability[category] = max(best_probability.get(category, 0), probability)
        ranked = sorted(best_probability, key=best_probability.get, reverse=True)[: self.max_categories]
        return [category for category in ranked if best_probability[category] >= self.min_probability]
