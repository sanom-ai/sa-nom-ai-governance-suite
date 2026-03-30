from dataclasses import dataclass, field

from sa_nom_governance.guards.human_override import HumanOverrideState


@dataclass(slots=True)
class DecisionTrace:
    source_type: str
    source_id: str
    matched_conditions: list[str] = field(default_factory=list)
    failed_conditions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DecisionComputation:
    outcome: str
    reason: str
    policy_basis: str
    trace: DecisionTrace
    human_override: HumanOverrideState | None = None
