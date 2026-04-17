from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha1
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints
from typing import Annotated


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Verdict(str, Enum):
    KILL = "KILL"
    REFINE = "REFINE"
    PURSUE = "PURSUE"


class SourceEvidence(BaseModel):
    source_url: HttpUrl
    verbatim_quote: NonEmptyStr


@dataclass
class DemandSignal:
    signal_id: str
    source_url: str
    verbatim_quote: str
    timestamp: str
    title: str | None = None
    source_text: str | None = None
    source_kind: str = "unknown"
    signal_subtype: str = "unknown"
    author: str | None = None
    verified: bool = False
    proof_level: str = "none"

    @staticmethod
    def build_signal_id(source_url: str, verbatim_quote: str) -> str:
        payload = f"{source_url}{verbatim_quote}".encode("utf-8")
        return sha1(payload).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Anchor:
    slug: str
    market_name: str
    incumbents: list[str]
    proof_of_market: DemandSignal
    cohort_hints: list[str] = field(default_factory=list)
    primary_channel_queries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Slice:
    slice_id: str
    anchor_slug: str
    label: str
    signal_ids: list[str]
    author_count: int
    dominant_subtype: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SliceVerdict:
    slice_id: str
    anchor_slug: str
    verdict: str
    gates: dict[str, bool]
    heuristics: dict[str, float]
    refine_reason: str | None
    next_test: str | None
    evidence_ids: list[str]
    schema_version: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


class Opportunity(BaseModel):
    opportunity_id: NonEmptyStr
    title: NonEmptyStr
    willingness_to_pay: NonEmptyStr
    distribution_channel: NonEmptyStr
    data_feasibility: NonEmptyStr


class ProductSpec(BaseModel):
    model_config = ConfigDict(strict=True)

    opportunity_id: NonEmptyStr
    title: NonEmptyStr
    approved: bool
    sources: Annotated[list[SourceEvidence], Field(min_length=1)]


class DeploymentMetadata(BaseModel):
    model_config = ConfigDict(strict=True)

    status: NonEmptyStr
    target: NonEmptyStr
    project_id: NonEmptyStr
    url: HttpUrl | None = None
    deployment_id: NonEmptyStr | None = None
    proof_level: NonEmptyStr
    detail: NonEmptyStr | None = None
