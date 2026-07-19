"""Memo content: the rendered markdown must contain the actual assets a
reader pays for — per-idea verdicts and verbatim evidence quotes — not
only winner boilerplate. Written after the 2026-07-19 live proof produced
a 20-line empty memo (docs/LIVE_PROOF_FINDINGS.md)."""

from evidentia.cli import _memo_to_markdown


_MEMO = {
    "tournament_id": "t-1",
    "player_id": "solo",
    "winner": None,
    "strongest_argument_for": "No winner evidence available.",
    "strongest_argument_against": "No winner available.",
    "missing_evidence_checklist": ["Collect stronger first-person spend evidence for weak gates."],
    "reality_spike": None,
    "zero_winner_diagnosis": "gate x failed",
}

_STATES = [
    {
        "idea": {
            "id": "research-0",
            "label": "Multiple users report PRICING issues with existing Headspace apps",
            "evidence_texts": {
                "e1": "Was charged $60 anyways when I cancelled the trial.",
                "e2": "Playlists have been broken for me for weeks.",
            },
        },
        "terminal_verdict": "INSUFFICIENT_EVIDENCE",
        "confidence_score_so_far": 0.71,
        "gate_results": [
            {"gate_name": "three_first_person_voices", "outcome": "FAIL", "status": "COMPLETED"},
        ],
    }
]


def test_memo_markdown_lists_per_idea_verdicts():
    md = _memo_to_markdown(_MEMO, states=_STATES)
    assert "research-0" in md
    assert "INSUFFICIENT_EVIDENCE" in md


def test_memo_markdown_quotes_evidence_verbatim():
    md = _memo_to_markdown(_MEMO, states=_STATES)
    assert "charged $60 anyways" in md


def test_memo_markdown_backward_compatible_without_states():
    md = _memo_to_markdown(_MEMO)
    assert md.startswith("# Decision Memo")
