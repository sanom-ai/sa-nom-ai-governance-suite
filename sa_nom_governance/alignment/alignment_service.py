from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sa_nom_governance.alignment.alignment_runtime_models import (
    ActiveAlignmentSelection,
    AlignmentRuntimeSnapshot,
    AlignmentSwitchDecision,
    AlignmentSwitchPreview,
)
from sa_nom_governance.alignment.constitution_registry import RegionalConstitutionRegistry
from sa_nom_governance.alignment.cultural_alignment_evaluator import CulturalAlignmentEvaluator


class GlobalHarmonyAlignmentService:
    def __init__(
        self,
        catalog_dir: Path,
        *,
        registry: RegionalConstitutionRegistry | None = None,
        evaluator: CulturalAlignmentEvaluator | None = None,
    ) -> None:
        self.registry = registry or RegionalConstitutionRegistry(catalog_dir)
        self.evaluator = evaluator or CulturalAlignmentEvaluator()
        available_regions = self.registry.list_regions()
        if not available_regions:
            raise ValueError("Global Harmony alignment service requires at least one regional constitution.")
        default_region_id = str(available_regions[0]["region_id"])
        default_constitution = self.registry.load(default_region_id)
        self._active_selection = ActiveAlignmentSelection(
            region_id=default_constitution.region_id,
            constitutional_version=default_constitution.constitutional_version,
            source="catalog-default",
            selected_by="system",
            rationale="Initialized from the first available catalog constitution.",
            selected_at=self._utc_now(),
        )

    @property
    def active_selection(self) -> ActiveAlignmentSelection:
        return self._active_selection

    def assess_switch(
        self,
        region_id: str,
        *,
        selected_by: str,
        rationale: str = "",
    ) -> AlignmentSwitchDecision:
        self.registry.load(region_id)
        actor = selected_by.strip()
        note = rationale.strip()
        if not actor:
            return AlignmentSwitchDecision(
                allowed=False,
                severity="critical",
                message="Alignment switching requires a named actor.",
                required_note=True,
            )
        if region_id == self._active_selection.region_id:
            return AlignmentSwitchDecision(
                allowed=True,
                severity="info",
                message="Requested region is already active.",
                required_note=False,
            )
        if not note:
            return AlignmentSwitchDecision(
                allowed=False,
                severity="warning",
                message="Alignment switching requires a rationale so the change stays auditable.",
                required_note=True,
            )
        if len(note) < 12:
            return AlignmentSwitchDecision(
                allowed=False,
                severity="warning",
                message="Alignment switching rationale is too short to explain the operational need.",
                required_note=True,
            )
        return AlignmentSwitchDecision(
            allowed=True,
            severity="info",
            message="Alignment switch is allowed and should remain visible in the audit trail.",
            required_note=True,
        )

    def preview_switch(
        self,
        region_id: str,
        *,
        selected_by: str,
        rationale: str = "",
        context: dict[str, object] | None = None,
        draft_text: str = "",
    ) -> dict[str, object]:
        decision = self.assess_switch(region_id, selected_by=selected_by, rationale=rationale)
        target_constitution = self.registry.load(region_id)
        evaluation = None
        if context is not None:
            evaluation = self.evaluator.evaluate(
                target_constitution,
                context=context,
                draft_text=draft_text,
            ).to_dict()
        preview = AlignmentSwitchPreview(
            decision=decision,
            current_region_id=self._active_selection.region_id,
            target_region_id=target_constitution.region_id,
            target_safe_claim=target_constitution.safe_claim,
            evaluation=evaluation,
            audit_handoff=self._build_audit_handoff(
                requested_region_id=target_constitution.region_id,
                selected_by=selected_by,
                rationale=rationale,
                decision=decision,
            ),
        )
        return preview.to_dict()

    def select_region(
        self,
        region_id: str,
        *,
        selected_by: str,
        rationale: str = "",
        source: str = "operator-selection",
    ) -> ActiveAlignmentSelection:
        decision = self.assess_switch(region_id, selected_by=selected_by, rationale=rationale)
        if not decision.allowed:
            raise ValueError(decision.message)
        constitution = self.registry.load(region_id)
        self._active_selection = ActiveAlignmentSelection(
            region_id=constitution.region_id,
            constitutional_version=constitution.constitutional_version,
            source=source,
            selected_by=selected_by,
            rationale=rationale,
            selected_at=self._utc_now(),
        )
        return self._active_selection

    def get_active_constitution(self):
        return self.registry.load(self._active_selection.region_id)

    def build_runtime_snapshot(
        self,
        *,
        context: dict[str, object] | None = None,
        draft_text: str = "",
    ) -> dict[str, object]:
        constitution = self.get_active_constitution()
        evaluation = None
        notes = [
            "Global Harmony baseline remains operator-selected and auditable.",
            "This runtime snapshot does not claim legal compliance automation or full global coverage.",
        ]
        if context is not None:
            evaluation_result = self.evaluator.evaluate(
                constitution,
                context=context,
                draft_text=draft_text,
            )
            evaluation = evaluation_result.to_dict()
            notes.append(
                "Evaluation results should be interpreted as governed alignment signals, not as automatic cultural truth."
            )
        switch_policy = {
            "requires_named_actor": True,
            "requires_rationale": True,
            "minimum_rationale_length": 12,
            "active_region_id": self._active_selection.region_id,
        }
        snapshot = AlignmentRuntimeSnapshot(
            available_regions=self.registry.list_regions(),
            active_selection=self._active_selection,
            safe_claim=constitution.safe_claim,
            switch_policy=switch_policy,
            audit_handoff=self._build_audit_handoff(
                requested_region_id=self._active_selection.region_id,
                selected_by=self._active_selection.selected_by,
                rationale=self._active_selection.rationale,
                decision=AlignmentSwitchDecision(
                    allowed=True,
                    severity="info",
                    message="Active selection is audit-ready.",
                    required_note=True,
                ),
            ),
            evaluation=evaluation,
            notes=notes,
        )
        return snapshot.to_dict()

    def _build_audit_handoff(
        self,
        *,
        requested_region_id: str,
        selected_by: str,
        rationale: str,
        decision: AlignmentSwitchDecision,
    ) -> dict[str, object]:
        return {
            "event_type": "alignment.selection",
            "requested_region_id": requested_region_id,
            "current_region_id": self._active_selection.region_id,
            "selected_by": selected_by,
            "rationale": rationale,
            "decision": decision.to_dict(),
            "recorded_at": self._utc_now(),
        }

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
