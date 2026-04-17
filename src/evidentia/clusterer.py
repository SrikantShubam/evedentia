from __future__ import annotations

from collections import Counter
from hashlib import sha1
import re

from evidentia.models import Anchor, DemandSignal, Slice


ENGLISH_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "how",
    "if",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "there",
    "these",
    "they",
    "this",
    "to",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "would",
    "you",
    "your",
    "into",
    "than",
    "then",
    "them",
    "very",
    "also",
    "been",
    "can",
}


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    stripped = re.sub(r"[^\w\s]", " ", lowered)
    return re.sub(r"\s+", " ", stripped).strip()


def _incumbent_stopwords(anchor: Anchor) -> set[str]:
    blocked: set[str] = set()
    for incumbent in anchor.incumbents:
        normalized = _normalize_text(incumbent)
        blocked.update(token for token in normalized.split() if len(token) >= 3)
    return blocked


def _tokenize(text: str, blocked_tokens: set[str]) -> set[str]:
    return {
        token
        for token in text.split()
        if len(token) >= 3 and token not in ENGLISH_STOPWORDS and token not in blocked_tokens
    }


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _subtype_compatible(left: DemandSignal, right: DemandSignal) -> bool:
    if left.signal_subtype == "unknown" or right.signal_subtype == "unknown":
        return True
    return left.signal_subtype == right.signal_subtype


def _mentions_cohort(text: str, cohort_hints: list[str]) -> bool:
    for hint in cohort_hints:
        normalized_hint = _normalize_text(hint)
        if not normalized_hint:
            continue
        if " " in normalized_hint:
            if normalized_hint in text:
                return True
            continue
        if normalized_hint in text.split():
            return True
    return False


def _dominant_subtype(signals: list[DemandSignal]) -> str:
    counts = Counter(signal.signal_subtype for signal in signals if signal.signal_subtype)
    if not counts:
        return "unknown"
    return counts.most_common(1)[0][0]


class _UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, index: int) -> int:
        if self.parent[index] != index:
            self.parent[index] = self.find(self.parent[index])
        return self.parent[index]

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if self.rank[root_left] < self.rank[root_right]:
            self.parent[root_left] = root_right
            return
        if self.rank[root_left] > self.rank[root_right]:
            self.parent[root_right] = root_left
            return
        self.parent[root_right] = root_left
        self.rank[root_left] += 1


def cluster_signals(
    anchor: Anchor,
    signals: list[DemandSignal],
    jaccard_threshold: float = 0.35,
    llm_labeler: callable | None = None,
) -> list[Slice]:
    if not signals:
        return []

    blocked_tokens = _incumbent_stopwords(anchor)
    prepared: list[dict] = []
    for signal in signals:
        normalized_text = _normalize_text(f"{signal.verbatim_quote} {signal.title or ''}")
        prepared.append(
            {
                "signal": signal,
                "normalized_text": normalized_text,
                "tokens": _tokenize(normalized_text, blocked_tokens),
                "cohort_hit": _mentions_cohort(normalized_text, anchor.cohort_hints),
            }
        )

    union_find = _UnionFind(len(prepared))
    for left in range(len(prepared)):
        for right in range(left + 1, len(prepared)):
            left_signal: DemandSignal = prepared[left]["signal"]
            right_signal: DemandSignal = prepared[right]["signal"]
            if not _subtype_compatible(left_signal, right_signal):
                continue
            similarity = _jaccard_similarity(prepared[left]["tokens"], prepared[right]["tokens"])
            if prepared[left]["cohort_hit"] or prepared[right]["cohort_hit"]:
                similarity += 0.15
            if similarity >= jaccard_threshold:
                union_find.union(left, right)

    members_by_root: dict[int, list[DemandSignal]] = {}
    for index, bundle in enumerate(prepared):
        root = union_find.find(index)
        members_by_root.setdefault(root, []).append(bundle["signal"])

    ordered_clusters = sorted(
        members_by_root.values(),
        key=lambda group: tuple(sorted(signal.signal_id for signal in group)),
    )

    slices: list[Slice] = []
    for index, cluster in enumerate(ordered_clusters, start=1):
        distinct_authors = {signal.author for signal in cluster if signal.author}
        if len(distinct_authors) < 2:
            continue
        signal_ids = sorted(signal.signal_id for signal in cluster)
        if llm_labeler is None:
            label = f"cluster_{index}"
        else:
            try:
                maybe_label = llm_labeler(quotes=[signal.verbatim_quote for signal in cluster])
                label = str(maybe_label).strip() or f"cluster_{index}"
            except Exception:  # noqa: BLE001
                label = f"cluster_{index}"
        slice_id = sha1(f"{anchor.slug}|{','.join(signal_ids)}".encode("utf-8")).hexdigest()[:16]
        slices.append(
            Slice(
                slice_id=slice_id,
                anchor_slug=anchor.slug,
                label=label,
                signal_ids=signal_ids,
                author_count=len(distinct_authors),
                dominant_subtype=_dominant_subtype(cluster),
            )
        )

    return slices
