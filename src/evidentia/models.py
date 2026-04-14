from pydantic import BaseModel, ConfigDict, HttpUrl, StringConstraints
from typing import Annotated


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


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
    sources: list[SourceEvidence]
