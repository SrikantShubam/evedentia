from evidentia.models import Idea, Provenance, QualifiedEvidence


def qualify_evidence(idea: Idea) -> dict[str, QualifiedEvidence]:
    qualified: dict[str, QualifiedEvidence] = {}
    for eid in idea.evidence_ids:
        provenance = idea.evidence_provenance.get(eid, "seed")
        if provenance == Provenance.SYNTHETIC.value:
            qualified[eid] = QualifiedEvidence(
                evidence_id=eid,
                provenance=Provenance.SYNTHETIC,
                verified=False,
                first_person=False,
                voice_key=None,
                ineligibility_reason="synthetic_placeholder",
            )
        elif provenance == Provenance.VERIFIED.value:
            qualified[eid] = QualifiedEvidence(
                evidence_id=eid,
                provenance=Provenance.VERIFIED,
                verified=True,
                first_person=True,
                voice_key=eid,
            )
        else:
            qualified[eid] = QualifiedEvidence(
                evidence_id=eid,
                provenance=Provenance.SEED,
                verified=False,
                first_person=True,
                voice_key=eid,
                ineligibility_reason="unverified",
            )
    return qualified
