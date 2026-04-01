from dataclasses import dataclass, field


@dataclass(slots=True)
class AlignmentMatch:
    principle_id: str
    title: str
    category: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "principle_id": self.principle_id,
            "title": self.title,
            "category": self.category,
            "reason": self.reason,
        }


@dataclass(slots=True)
class AlignmentConcern:
    code: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass(slots=True)
class AlignmentEvaluationResult:
    status: str
    human_review_required: bool
    resonance_score: int
    resonance_band: str
    normalized_context: dict[str, object]
    matched_principles: list[AlignmentMatch] = field(default_factory=list)
    concerns: list[AlignmentConcern] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "human_review_required": self.human_review_required,
            "resonance_score": self.resonance_score,
            "resonance_band": self.resonance_band,
            "normalized_context": dict(self.normalized_context),
            "matched_principles": [item.to_dict() for item in self.matched_principles],
            "concerns": [item.to_dict() for item in self.concerns],
            "rationale": list(self.rationale),
        }
