from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from sa_nom_governance.ptag.pt_oss_models import PTOSSFoundationSpec, PTOSSMetricDefinition, PTOSSThresholdBand, load_pt_oss_foundation
from sa_nom_governance.studio.role_private_studio_models import (
    NormalizedRoleSpec,
    PTOSSAssessment,
    PTOSSIssue,
    PTOSSMetricScore,
    SimulationReport,
    StructuredJD,
    ValidationReport,
    utc_now,
)


@dataclass(slots=True)
class StructuralSignals:
    public_sector_mode: bool
    has_reports_to: bool
    has_escalation_to: bool
    has_safety_owner: bool
    has_wait_human: bool
    allowed_action_count: int
    handled_resource_count: int
    responsibility_count: int
    manual_override_active: bool
    high_sensitivity: bool


class PTOSSEngine:
    def __init__(self, foundation_path: Path) -> None:
        self.foundation_path = foundation_path
        self.foundation = load_pt_oss_foundation(foundation_path)
        self.metric_map = self.foundation.metric_map()

    def assess_role_draft(
        self,
        structured_jd: StructuredJD,
        normalized_spec: NormalizedRoleSpec | None,
        validation_report: ValidationReport | None,
        simulation_report: SimulationReport | None,
        current_ptag: str,
        generated_ptag: str,
    ) -> PTOSSAssessment:
        signals = self._build_structural_signals(
            structured_jd=structured_jd,
            normalized_spec=normalized_spec,
            current_ptag=current_ptag,
            generated_ptag=generated_ptag,
        )

        mode = self._select_mode(signals)
        metrics = [
            self._score_metric("HDI_S", self._compute_hdi_s(signals), "Structural dependency risk across manual overrides, wait-human paths, and missing structure."),
            self._score_metric("HDI_D", self._compute_hdi_d(signals), "Decision dependency risk based on authority concentration and escalation ownership."),
            self._score_metric("SFS", self._compute_sfs(signals, validation_report, simulation_report), "Structural fragility posture across validation, simulation, resources, and escalation integrity."),
            self._score_metric("KPIR", self._compute_kpir(signals), "Key-person concentration risk for this role draft."),
            self._score_metric("ASP", self._compute_asp(signals, validation_report, simulation_report), "Architectural stability posture derived from six baseline checks."),
            self._score_metric("HOIS", self._compute_hois(signals), "Human override integrity posture for the draft role pack."),
        ]
        if signals.public_sector_mode:
            metrics.append(self._score_metric("SPAI", self._compute_spai(signals), "Public-sector asymmetry risk for hierarchy, veto, and appeal structure."))

        blockers = self._build_blockers(metrics, signals)
        readiness_score = self._build_readiness_score(metrics, blockers)
        posture = self._resolve_posture(metrics, blockers)
        recommendations = self._build_recommendations(metrics, blockers)
        context = {
            "public_sector_mode": signals.public_sector_mode,
            "signals": {
                "reports_to": signals.has_reports_to,
                "escalation_to": signals.has_escalation_to,
                "safety_owner": signals.has_safety_owner,
                "wait_human": signals.has_wait_human,
                "manual_override_active": signals.manual_override_active,
                "allowed_action_count": signals.allowed_action_count,
                "handled_resource_count": signals.handled_resource_count,
                "responsibility_count": signals.responsibility_count,
                "high_sensitivity": signals.high_sensitivity,
            },
        }
        return PTOSSAssessment(
            assessment_id=f"ptoss_{uuid4().hex[:12]}",
            generated_at=utc_now(),
            mode=mode,
            posture=posture,
            readiness_score=readiness_score,
            metrics=metrics,
            blockers=blockers,
            recommendations=recommendations,
            context=context,
        )

    def _select_mode(self, signals: StructuralSignals) -> str:
        if signals.public_sector_mode:
            return "PT_OSS_FULL_CAL_TH"
        if signals.allowed_action_count <= 2 and signals.responsibility_count <= 2:
            return "PT_OSS_LITE"
        return "PT_OSS_FULL"

    def _build_structural_signals(
        self,
        structured_jd: StructuredJD,
        normalized_spec: NormalizedRoleSpec | None,
        current_ptag: str,
        generated_ptag: str,
    ) -> StructuralSignals:
        domain = f"{structured_jd.business_domain} {normalized_spec.domain if normalized_spec else ''}".lower()
        public_sector_mode = any(token in domain for token in ["public", "government", "ministry", "bureau", "public_sector", "state"])
        has_reports_to = bool(normalized_spec and normalized_spec.reports_to)
        has_escalation_to = "escalation_to:" in current_ptag
        has_safety_owner = "safety_owner:" in current_ptag
        wait_human_actions = []
        if normalized_spec is not None:
            wait_human_actions.extend(normalized_spec.wait_human_actions)
            wait_human_actions.extend(normalized_spec.auto_wait_human_actions)
        has_wait_human = bool(wait_human_actions or "require human_override" in current_ptag)
        allowed_action_count = len(normalized_spec.allowed_actions) if normalized_spec else 0
        handled_resource_count = len(normalized_spec.handled_resources) if normalized_spec else 0
        responsibility_count = len(normalized_spec.responsibilities) if normalized_spec else 0
        manual_override_active = bool(generated_ptag and current_ptag != generated_ptag)
        sensitivities = [
            structured_jd.financial_sensitivity,
            structured_jd.legal_sensitivity,
            structured_jd.compliance_sensitivity,
        ]
        high_sensitivity = any(value in {"high", "critical"} for value in sensitivities)
        return StructuralSignals(
            public_sector_mode=public_sector_mode,
            has_reports_to=has_reports_to,
            has_escalation_to=has_escalation_to,
            has_safety_owner=has_safety_owner,
            has_wait_human=has_wait_human,
            allowed_action_count=allowed_action_count,
            handled_resource_count=handled_resource_count,
            responsibility_count=responsibility_count,
            manual_override_active=manual_override_active,
            high_sensitivity=high_sensitivity,
        )

    def _compute_hdi_s(self, signals: StructuralSignals) -> float:
        score = 18.0
        if not signals.has_escalation_to:
            score += 18
        if not signals.has_wait_human and signals.high_sensitivity:
            score += 14
        if signals.handled_resource_count == 0:
            score += 12
        if signals.manual_override_active:
            score += 8
        if signals.responsibility_count <= 1:
            score += 10
        score += min(signals.allowed_action_count * 3, 18)
        return _clamp(score, 0, 100)

    def _compute_hdi_d(self, signals: StructuralSignals) -> float:
        score = 20.0
        if not signals.has_reports_to:
            score += 18
        if not signals.has_escalation_to:
            score += 18
        if signals.allowed_action_count >= 5:
            score += 14
        if signals.high_sensitivity and not signals.has_wait_human:
            score += 18
        if signals.handled_resource_count <= 1 and signals.allowed_action_count >= 3:
            score += 10
        return _clamp(score, 0, 100)

    def _compute_sfs(self, signals: StructuralSignals, validation_report: ValidationReport | None, simulation_report: SimulationReport | None) -> float:
        score = 18.0
        if validation_report is None or validation_report.blocked_publish:
            score += 22
        if simulation_report is None or simulation_report.status != "passed":
            score += 20
        if not signals.has_escalation_to:
            score += 12
        if signals.handled_resource_count == 0:
            score += 10
        if signals.responsibility_count <= 1:
            score += 8
        return _clamp(score, 0, 100)

    def _compute_kpir(self, signals: StructuralSignals) -> float:
        score = 14.0
        score += min(max(signals.allowed_action_count - 2, 0) * 8, 30)
        if not signals.has_reports_to:
            score += 18
        if signals.handled_resource_count <= 1 and signals.allowed_action_count >= 3:
            score += 16
        if signals.responsibility_count <= 1:
            score += 14
        return _clamp(score, 0, 100)

    def _compute_asp(self, signals: StructuralSignals, validation_report: ValidationReport | None, simulation_report: SimulationReport | None) -> float:
        checks = [
            signals.has_reports_to,
            signals.has_escalation_to,
            signals.handled_resource_count > 0,
            signals.has_wait_human or not signals.high_sensitivity,
            bool(validation_report is not None and not validation_report.blocked_publish),
            bool(simulation_report is not None and simulation_report.status == "passed"),
        ]
        return float(sum(1 for item in checks if item))

    def _compute_hois(self, signals: StructuralSignals) -> float:
        score = 42.0
        if signals.has_wait_human:
            score += 16
        else:
            score -= 12
        if signals.has_escalation_to:
            score += 16
        else:
            score -= 10
        if signals.has_reports_to:
            score += 12
        else:
            score -= 10
        if signals.high_sensitivity and not signals.has_safety_owner:
            score -= 10
        return _clamp(score, 0, 100)

    def _compute_spai(self, signals: StructuralSignals) -> float:
        score = 12.0
        if not signals.has_reports_to:
            score += 12
        if not signals.has_escalation_to:
            score += 18
        if not signals.has_safety_owner:
            score += 12
        if signals.manual_override_active:
            score += 8
        if signals.allowed_action_count >= 5:
            score += 10
        return _clamp(score, 0, 100)

    def _score_metric(self, metric_id: str, value: float, rationale: str) -> PTOSSMetricScore:
        definition = self.metric_map[metric_id]
        band = _resolve_threshold_band(definition, value)
        return PTOSSMetricScore(
            metric_id=definition.metric_id,
            name=definition.name,
            value=round(value, 2),
            unit=definition.unit,
            label=band.label,
            risk_level=band.risk_level,
            default_action=band.default_action,
            rationale=rationale,
        )

    def _build_blockers(self, metrics: list[PTOSSMetricScore], signals: StructuralSignals) -> list[PTOSSIssue]:
        blockers: list[PTOSSIssue] = []
        metric_index = {item.metric_id: item for item in metrics}

        if metric_index.get("HDI_D") and metric_index["HDI_D"].risk_level in {"high", "critical"}:
            blockers.append(PTOSSIssue("dependency", "critical", "Decision dependency is too concentrated for safe governed publication.", True))
        if metric_index.get("SFS") and metric_index["SFS"].risk_level in {"high", "critical"}:
            blockers.append(PTOSSIssue("fragility", "critical", "Structural fragility is above the safe publication threshold.", True))
        if metric_index.get("KPIR") and metric_index["KPIR"].risk_level in {"high", "critical"}:
            blockers.append(PTOSSIssue("key_person", "warning", "Key-person impact is elevated and should be reduced before scaling the role.", False))
        if metric_index.get("ASP") and metric_index["ASP"].label in {"unstable", "borderline"}:
            blockers.append(PTOSSIssue("stability", "critical", "Architectural stability checks are not strong enough for confident publication.", True))
        if metric_index.get("HOIS") and metric_index["HOIS"].risk_level in {"high", "critical"}:
            blockers.append(PTOSSIssue("override_integrity", "critical", "Human override integrity is too weak for a governed production role.", True))
        if signals.high_sensitivity and not signals.has_safety_owner:
            blockers.append(PTOSSIssue("safety", "critical", "High-sensitivity roles must declare a safety owner before publication.", True))
        if signals.public_sector_mode and metric_index.get("SPAI") and metric_index["SPAI"].risk_level in {"high", "critical"}:
            blockers.append(PTOSSIssue("power_asymmetry", "critical", "Public-sector asymmetry risk is too high and needs a counter-mechanism before publication.", True))
        return blockers

    def _build_readiness_score(self, metrics: list[PTOSSMetricScore], blockers: list[PTOSSIssue]) -> int:
        risk_weight = {"low": 92, "medium": 68, "high": 38, "critical": 12}
        if not metrics:
            return 0
        base = sum(risk_weight.get(item.risk_level, 50) for item in metrics) / len(metrics)
        penalty = sum(12 if item.blocks_publish else 5 for item in blockers)
        return max(0, min(100, int(round(base - penalty))))

    def _resolve_posture(self, metrics: list[PTOSSMetricScore], blockers: list[PTOSSIssue]) -> str:
        if any(item.blocks_publish and item.severity == "critical" for item in blockers):
            return "critical"
        if any(item.risk_level in {"high", "critical"} for item in metrics):
            return "elevated"
        if any(item.risk_level == "medium" for item in metrics):
            return "watch"
        return "healthy"

    def _build_recommendations(self, metrics: list[PTOSSMetricScore], blockers: list[PTOSSIssue]) -> list[str]:
        recommendations: list[str] = []
        for item in metrics:
            if item.risk_level in {"medium", "high", "critical"}:
                recommendations.append(f"{item.name}: {item.default_action.replace('_', ' ')}.")
        for item in blockers:
            recommendations.append(item.message)
        return list(dict.fromkeys(recommendations))


def _resolve_threshold_band(definition: PTOSSMetricDefinition, value: float) -> PTOSSThresholdBand:
    for band in definition.thresholds:
        if band.min <= value <= band.max:
            return band
    if not definition.thresholds:
        return PTOSSThresholdBand(0, 0, "unknown", "unknown", "review")
    return definition.thresholds[-1] if value > definition.thresholds[-1].max else definition.thresholds[0]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
