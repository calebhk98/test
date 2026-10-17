from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..embed.base import Embedder
from ..models import SearchHit
from ..registry import Component


@dataclass
class IndexDoc:
    doc_id: str                  # "<video_id>" or "<video_id>#<section index>"
    kind: str                    # "video" | "section"
    video_id: str
    title: str
    path: str
    url: str
    text: str
    channel: str = ""
    published: str = ""
    tags: list[str] = field(default_factory=list)
    is_sponsor: bool = False


@dataclass
class SearchFilters:
    kind: str | None = None
    channel: str | None = None
    tags: list[str] = field(default_factory=list)
    since: str | None = None     # ISO date
    exclude_sponsor: bool = True


class VectorIndex(Component, ABC):
    @abstractmethod
    def upsert(self, docs: list[IndexDoc], embedder: Embedder) -> None: ...

    @abstractmethod
    def delete_video(self, video_id: str) -> None: ...

    @abstractmethod
    def pool_video(self, video_id: str, embedder: Embedder) -> None:
        """Store a whole-video vector: the mean of its section chunk vectors."""

    @abstractmethod
    def set_doc_vector(self, doc_id: str, embedder: Embedder, vec) -> None:
        """Store a vector for a whole document, used by `similar`."""

    @abstractmethod
    def search(self, query: str, embedder: Embedder, k: int = 8,
               filters: SearchFilters | None = None) -> list[SearchHit]: ...

    @abstractmethod
    def similar(self, video_id: str, embedder: Embedder, k: int = 8) -> list[SearchHit]: ...

    @abstractmethod
    def stats(self) -> dict: ...
