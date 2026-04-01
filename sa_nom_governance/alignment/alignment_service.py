from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sa_nom_governance.alignment.alignment_runtime_models import (
    ActiveAlignmentSelection,
    AlignmentRuntimeSnapshot,
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

    def select_region(
        self,
        region_id: str,
        *,
        selected_by: str,
        rationale: str = "",
        source: str = "operator-selection",
    ) -> ActiveAlignmentSelection:
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
        snapshot = AlignmentRuntimeSnapshot(
            available_regions=self.registry.list_regions(),
            active_selection=self._active_selection,
            safe_claim=constitution.safe_claim,
            evaluation=evaluation,
            notes=notes,
        )
        return snapshot.to_dict()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
