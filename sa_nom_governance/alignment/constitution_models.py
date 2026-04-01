from dataclasses import dataclass, field


@dataclass(slots=True)
class AlignmentPrinciple:
    principle_id: str
    title: str
    category: str
    description: str
    weight: str = "supporting"
    keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "principle_id": self.principle_id,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "weight": self.weight,
            "keywords": list(self.keywords),
        }


@dataclass(slots=True)
class RegionalConstitution:
    region_id: str
    display_name: str
    geography_scope: str
    default_locale: str
    constitutional_version: str
    values: list[str] = field(default_factory=list)
    communication_posture: dict[str, str] = field(default_factory=dict)
    regulatory_sources: list[str] = field(default_factory=list)
    principles: list[AlignmentPrinciple] = field(default_factory=list)
    notes: str = ""
    safe_claim: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "region_id": self.region_id,
            "display_name": self.display_name,
            "geography_scope": self.geography_scope,
            "default_locale": self.default_locale,
            "constitutional_version": self.constitutional_version,
            "values": list(self.values),
            "communication_posture": dict(self.communication_posture),
            "regulatory_sources": list(self.regulatory_sources),
            "principles": [item.to_dict() for item in self.principles],
            "notes": self.notes,
            "safe_claim": self.safe_claim,
        }


@dataclass(slots=True)
class ConstitutionIngestionRequest:
    source_document_id: str
    source_type: str
    requested_by: str
    payload: dict[str, object]
    rationale: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "source_document_id": self.source_document_id,
            "source_type": self.source_type,
            "requested_by": self.requested_by,
            "payload": dict(self.payload),
            "rationale": self.rationale,
        }


@dataclass(slots=True)
class ConstitutionIngestionResult:
    accepted: bool
    constitution: RegionalConstitution | None
    summary: dict[str, object]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "accepted": self.accepted,
            "summary": dict(self.summary),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }
        if self.constitution is not None:
            payload["constitution"] = self.constitution.to_dict()
        return payload
