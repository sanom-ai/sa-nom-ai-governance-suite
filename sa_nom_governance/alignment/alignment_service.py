from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sa_nom_governance.alignment.alignment_runtime_models import (
    ActiveAlignmentSelection,
    AlignmentRuntimeSnapshot,
    AlignmentSelectionIntent,
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
        default_region_id: str | None = None,
        registry: RegionalConstitutionRegistry | None = None,
        evaluator: CulturalAlignmentEvaluator | None = None,
    ) -> None:
        self.registry = registry or RegionalConstitutionRegistry(catalog_dir)
        self.evaluator = evaluator or CulturalAlignmentEvaluator()
        default_constitution, default_source, default_rationale = self._resolve_default_selection(default_region_id)
        self._active_selection = ActiveAlignmentSelection(
            region_id=default_constitution.region_id,
            constitutional_version=default_constitution.constitutional_version,
            source=default_source,
            selected_by="system",
            rationale=default_rationale,
            selected_at=self._utc_now(),
        )

    @property
    def active_selection(self) -> ActiveAlignmentSelection:
        return self._active_selection

    def _resolve_default_selection(self, default_region_id: str | None) -> tuple[object, str, str]:
        available_regions = self.registry.list_regions()
        if not available_regions:
            raise ValueError("Global Harmony alignment service requires at least one regional constitution.")
        available_region_ids = {str(item["region_id"]) for item in available_regions}
        requested_region_id = (default_region_id or "").strip()
        if requested_region_id:
            if requested_region_id not in available_region_ids:
                available = ", ".join(sorted(available_region_ids)) or "none"
                raise ValueError(
                    f"Unknown default regional constitution: {requested_region_id}. Available regions: {available}"
                )
            constitution = self.registry.load(requested_region_id)
            if requested_region_id == "eu":
                return constitution, "catalog-default", "Initialized from the deterministic catalog default constitution."
            return constitution, "configured-default", f"Initialized from explicit default region {requested_region_id}."
        if "eu" in available_region_ids:
            constitution = self.registry.load("eu")
            return constitution, "catalog-default", "Initialized from the deterministic catalog default constitution."
        if len(available_regions) == 1:
            region_id = str(available_regions[0]["region_id"])
            constitution = self.registry.load(region_id)
            return constitution, "single-region-default", "Initialized from the only available catalog constitution."
        available = ", ".join(sorted(available_region_ids)) or "none"
        raise ValueError(
            "Global Harmony alignment service requires an explicit default region when the catalog does not include the built-in default 'eu'. "
            f"Available regions: {available}"
        )

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

    def evaluate_selection_intent(
        self,
        region_id: str,
        *,
        selected_by: str,
        rationale: str = "",
        context: dict[str, object] | None = None,
        draft_text: str = "",
    ) -> tuple[AlignmentSwitchDecision, AlignmentSelectionIntent, dict[str, object] | None]:
        decision = self.assess_switch(region_id, selected_by=selected_by, rationale=rationale)
        if not decision.allowed:
            return decision, AlignmentSelectionIntent(
                action="blocked",
                approval_required=False,
                reasons=[decision.message],
            ), None
        if region_id == self._active_selection.region_id:
            return decision, AlignmentSelectionIntent(
                action="no_change",
                approval_required=False,
                reasons=["The requested constitution is already active."],
            ), None
        if context is None:
            return decision, AlignmentSelectionIntent(
                action="preview_only",
                approval_required=False,
                reasons=["No governed context was supplied, so the switch should stay in preview mode first."],
            ), None

        target_constitution = self.registry.load(region_id)
        evaluation = self.evaluator.evaluate(
            target_constitution,
            context=context,
            draft_text=draft_text,
        ).to_dict()
        normalized = dict(evaluation.get("normalized_context", {}))
        audience = str(normalized.get("audience", "internal"))
        channel = str(normalized.get("channel", "internal"))
        sensitivity = str(normalized.get("sensitivity", "normal"))
        reasons: list[str] = []

        if evaluation.get("status") == "escalated" or sensitivity in {"high", "legal_sensitive", "regulated"}:
            reasons.append("Sensitive or escalated context requires explicit approval before switching constitutions.")
            return decision, AlignmentSelectionIntent(
                action="require_approval",
                approval_required=True,
                evaluation_status=str(evaluation.get("status", "")),
                reasons=reasons,
            ), evaluation

        if audience in {"customer", "external", "public"} or channel in {"customer", "public", "press"}:
            reasons.append("Externally visible contexts should keep a named approval decision before switching constitutions.")
            return decision, AlignmentSelectionIntent(
                action="require_approval",
                approval_required=True,
                evaluation_status=str(evaluation.get("status", "")),
                reasons=reasons,
            ), evaluation

        if evaluation.get("status") == "guarded":
            reasons.append("Guarded alignment results should stay in preview until an operator confirms the intent.")
            return decision, AlignmentSelectionIntent(
                action="preview_only",
                approval_required=False,
                evaluation_status="guarded",
                reasons=reasons,
            ), evaluation

        reasons.append("Low-risk governed context can switch directly under the baseline policy.")
        return decision, AlignmentSelectionIntent(
            action="direct_switch",
            approval_required=False,
            evaluation_status=str(evaluation.get("status", "")),
            reasons=reasons,
        ), evaluation

    def preview_switch(
        self,
        region_id: str,
        *,
        selected_by: str,
        rationale: str = "",
        context: dict[str, object] | None = None,
        draft_text: str = "",
    ) -> dict[str, object]:
        decision, selection_intent, evaluation = self.evaluate_selection_intent(
            region_id,
            selected_by=selected_by,
            rationale=rationale,
            context=context,
            draft_text=draft_text,
        )
        target_constitution = self.registry.load(region_id)
        preview = AlignmentSwitchPreview(
            decision=decision,
            current_region_id=self._active_selection.region_id,
            target_region_id=target_constitution.region_id,
            target_safe_claim=target_constitution.safe_claim,
            selection_intent=selection_intent,
            evaluation=evaluation,
            audit_handoff=self._build_audit_handoff(
                requested_region_id=target_constitution.region_id,
                selected_by=selected_by,
                rationale=rationale,
                decision=decision,
                selection_intent=selection_intent,
                approved_by="",
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
        context: dict[str, object] | None = None,
        draft_text: str = "",
        approved_by: str = "",
    ) -> ActiveAlignmentSelection:
        decision, selection_intent, _ = self.evaluate_selection_intent(
            region_id,
            selected_by=selected_by,
            rationale=rationale,
            context=context,
            draft_text=draft_text,
        )
        if not decision.allowed:
            raise ValueError(decision.message)
        if selection_intent.action == "preview_only":
            raise ValueError("Alignment switch should remain in preview until the governed context is confirmed.")
        if selection_intent.action == "require_approval" and not approved_by.strip():
            raise ValueError("Alignment switch requires an approval actor in this context.")
        constitution = self.registry.load(region_id)
        effective_source = source if not approved_by.strip() else "approved-operator-selection"
        effective_rationale = rationale if not approved_by.strip() else f"{rationale} | approved_by={approved_by.strip()}"
        self._active_selection = ActiveAlignmentSelection(
            region_id=constitution.region_id,
            constitutional_version=constitution.constitutional_version,
            source=effective_source,
            selected_by=selected_by,
            rationale=effective_rationale,
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
            "preview_required_without_context": True,
            "approval_required_for_sensitive_context": True,
            "approval_required_for_external_context": True,
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
                selection_intent=AlignmentSelectionIntent(
                    action="active",
                    approval_required=False,
                    reasons=["The current alignment posture is already active and traceable."],
                ),
                approved_by="",
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
        selection_intent: AlignmentSelectionIntent,
        approved_by: str,
    ) -> dict[str, object]:
        return {
            "event_type": "alignment.selection",
            "requested_region_id": requested_region_id,
            "current_region_id": self._active_selection.region_id,
            "selected_by": selected_by,
            "approved_by": approved_by,
            "rationale": rationale,
            "decision": decision.to_dict(),
            "selection_intent": selection_intent.to_dict(),
            "recorded_at": self._utc_now(),
        }

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
