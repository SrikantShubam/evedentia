from enum import Enum
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


class DemandSignal(BaseModel):
    source_url: HttpUrl
    verbatim_quote: NonEmptyStr
    signal_type: NonEmptyStr
    source_strength: NonEmptyStr


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
