from __future__ import annotations

from sa_nom_governance.alignment.constitution_models import (
    AlignmentPrinciple,
    ConstitutionIngestionRequest,
    ConstitutionIngestionResult,
    RegionalConstitution,
)


class ConstitutionIngestionService:
    REQUIRED_FIELDS = [
        "region_id",
        "display_name",
        "geography_scope",
        "default_locale",
        "constitutional_version",
    ]

    def ingest(self, request: ConstitutionIngestionRequest) -> ConstitutionIngestionResult:
        errors: list[str] = []
        warnings: list[str] = []
        payload = dict(request.payload)

        if not request.source_document_id.strip():
            errors.append("source_document_id is required for constitution ingestion.")
        if not request.requested_by.strip():
            errors.append("requested_by is required for constitution ingestion.")
        if request.rationale and len(request.rationale.strip()) < 12:
            warnings.append("Ingestion rationale is short; consider adding more operational context.")

        for field_name in self.REQUIRED_FIELDS:
            if not str(payload.get(field_name, "")).strip():
                errors.append(f"Missing required constitution field: {field_name}")

        principles_raw = payload.get("principles", [])
        if not isinstance(principles_raw, list) or not principles_raw:
            errors.append("Ingestion payload must define at least one principle.")

        principles: list[AlignmentPrinciple] = []
        for index, item in enumerate(principles_raw if isinstance(principles_raw, list) else []):
            principle = dict(item)
            for field_name in ["principle_id", "title", "category", "description"]:
                if not str(principle.get(field_name, "")).strip():
                    errors.append(f"principles[{index}] is missing required field: {field_name}")
            if errors:
                continue
            weight = str(principle.get("weight", "supporting")).strip().lower() or "supporting"
            if weight not in {"primary", "supporting"}:
                warnings.append(
                    f"principles[{index}] weight '{weight}' is not standard; using supporting in baseline ingestion."
                )
                weight = "supporting"
            principles.append(
                AlignmentPrinciple(
                    principle_id=str(principle["principle_id"]),
                    title=str(principle["title"]),
                    category=str(principle["category"]),
                    description=str(principle["description"]),
                    weight=weight,
                    keywords=[str(value) for value in principle.get("keywords", [])],
                )
            )

        if errors:
            return ConstitutionIngestionResult(
                accepted=False,
                constitution=None,
                summary={
                    "source_document_id": request.source_document_id,
                    "source_type": request.source_type,
                    "requested_by": request.requested_by,
                    "principles_total": len(principles),
                },
                errors=errors,
                warnings=warnings,
            )

        constitution = RegionalConstitution(
            region_id=str(payload["region_id"]),
            display_name=str(payload["display_name"]),
            geography_scope=str(payload["geography_scope"]),
            default_locale=str(payload["default_locale"]),
            constitutional_version=str(payload["constitutional_version"]),
            values=[str(value) for value in payload.get("values", [])],
            communication_posture={str(key): str(value) for key, value in dict(payload.get("communication_posture", {})).items()},
            regulatory_sources=[str(value) for value in payload.get("regulatory_sources", [])],
            principles=principles,
            notes=str(payload.get("notes", "")),
            safe_claim=str(payload.get("safe_claim", "")),
        )
        summary = {
            "source_document_id": request.source_document_id,
            "source_type": request.source_type,
            "requested_by": request.requested_by,
            "region_id": constitution.region_id,
            "constitutional_version": constitution.constitutional_version,
            "principles_total": len(principles),
            "accepted_values_total": len(constitution.values),
        }
        if not constitution.safe_claim:
            warnings.append("Ingested constitution does not define a safe_claim; public messaging should remain conservative.")

        return ConstitutionIngestionResult(
            accepted=True,
            constitution=constitution,
            summary=summary,
            errors=[],
            warnings=warnings,
        )
