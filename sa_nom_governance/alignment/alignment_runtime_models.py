from dataclasses import dataclass, field


@dataclass(slots=True)
class ActiveAlignmentSelection:
    region_id: str
    constitutional_version: str
    source: str
    selected_by: str
    rationale: str = ""
    selected_at: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "region_id": self.region_id,
            "constitutional_version": self.constitutional_version,
            "source": self.source,
            "selected_by": self.selected_by,
            "rationale": self.rationale,
            "selected_at": self.selected_at,
        }


@dataclass(slots=True)
class AlignmentRuntimeSnapshot:
    available_regions: list[dict[str, object]]
    active_selection: ActiveAlignmentSelection
    safe_claim: str
    evaluation: dict[str, object] | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "available_regions": [dict(item) for item in self.available_regions],
            "active_selection": self.active_selection.to_dict(),
            "safe_claim": self.safe_claim,
            "notes": list(self.notes),
        }
        if self.evaluation is not None:
            payload["evaluation"] = dict(self.evaluation)
        return payload
