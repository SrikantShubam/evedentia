from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import warnings

import yaml

from evidentia import auditor
from evidentia.models import Anchor, DemandSignal


class AnchorVerificationError(RuntimeError):
    pass


def anchors_root() -> Path:
    return Path(__file__).resolve().parents[2] / "anchors"


def _signal_from_dict(data: dict) -> DemandSignal:
    source_url = str(data["source_url"])
    verbatim_quote = str(data["verbatim_quote"])
    timestamp = str(data.get("timestamp", ""))
    return DemandSignal(
        signal_id=DemandSignal.build_signal_id(source_url, verbatim_quote),
        source_url=source_url,
        verbatim_quote=verbatim_quote,
        timestamp=timestamp,
        source_kind="anchor_proof",
        signal_subtype="market_proof",
    )


def load_anchor(path: Path) -> Anchor:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    proof = _signal_from_dict(payload["proof_of_market"])
    return Anchor(
        slug=str(payload["slug"]),
        market_name=str(payload["market_name"]),
        incumbents=[str(item) for item in payload.get("incumbents", [])],
        proof_of_market=proof,
        cohort_hints=[str(item) for item in payload.get("cohort_hints", [])],
        primary_channel_queries=[str(item) for item in payload.get("primary_channel_queries", [])],
    )


def verify_anchor(anchor: Anchor) -> Anchor:
    verification = auditor.verify_quote(
        {
            "source_url": anchor.proof_of_market.source_url,
            "verbatim_quote": anchor.proof_of_market.verbatim_quote,
            "source_text": "",
        }
    )
    if not verification.get("verified") or verification.get("proof_level") == "none":
        raise AnchorVerificationError(
            f"anchor proof not verifiable for {anchor.slug}: {anchor.proof_of_market.source_url}"
        )
    verified_proof = replace(
        anchor.proof_of_market,
        verified=True,
        proof_level=str(verification.get("proof_level", "none")),
    )
    return replace(anchor, proof_of_market=verified_proof)


def load_all_anchors(root: Path | None = None) -> list[Anchor]:
    resolved_root = root or anchors_root()
    anchors: list[Anchor] = []
    for path in sorted(list(resolved_root.glob("*.yaml")) + list(resolved_root.glob("*.yml"))):
        try:
            anchors.append(verify_anchor(load_anchor(path)))
        except AnchorVerificationError as exc:
            warnings.warn(str(exc), RuntimeWarning)
    return anchors
