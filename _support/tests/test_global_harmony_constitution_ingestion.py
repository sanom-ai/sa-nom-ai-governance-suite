from sa_nom_governance.alignment.constitution_ingestion import ConstitutionIngestionService
from sa_nom_governance.alignment.constitution_models import ConstitutionIngestionRequest


def test_constitution_ingestion_accepts_valid_payload() -> None:
    service = ConstitutionIngestionService()

    result = service.ingest(
        ConstitutionIngestionRequest(
            source_document_id="doc-001",
            source_type="governed-document",
            requested_by="operator.tawan",
            rationale="Pilot ASEAN constitution import for customer-facing flows.",
            payload={
                "region_id": "asean-pilot",
                "display_name": "ASEAN Pilot Constitution",
                "geography_scope": "ASEAN",
                "default_locale": "th-TH",
                "constitutional_version": "0.1",
                "values": ["respect", "coordination"],
                "communication_posture": {"tone": "polite"},
                "principles": [
                    {
                        "principle_id": "ASEAN_RESPECT",
                        "title": "Respectful Coordination",
                        "category": "cultural_posture",
                        "description": "Keep communication respectful and non-inflammatory.",
                        "weight": "primary",
                    }
                ],
                "safe_claim": "Pilot regional alignment profile for governed evaluation.",
            },
        )
    )

    assert result.accepted is True
    assert result.constitution is not None
    assert result.constitution.region_id == "asean-pilot"
    assert result.summary["principles_total"] == 1
    assert result.errors == []


def test_constitution_ingestion_rejects_missing_required_fields() -> None:
    service = ConstitutionIngestionService()

    result = service.ingest(
        ConstitutionIngestionRequest(
            source_document_id="",
            source_type="governed-document",
            requested_by="",
            rationale="short",
            payload={"region_id": "broken", "principles": []},
        )
    )

    assert result.accepted is False
    assert result.constitution is None
    assert any("source_document_id" in item for item in result.errors)
    assert any("requested_by" in item for item in result.errors)
    assert any("display_name" in item for item in result.errors)
    assert result.warnings


def test_constitution_ingestion_warns_for_missing_safe_claim() -> None:
    service = ConstitutionIngestionService()

    result = service.ingest(
        ConstitutionIngestionRequest(
            source_document_id="doc-002",
            source_type="uploaded-json",
            requested_by="operator.tawan",
            rationale="EU-style transparency pilot import.",
            payload={
                "region_id": "eu-pilot",
                "display_name": "EU Pilot Constitution",
                "geography_scope": "EU",
                "default_locale": "en-EU",
                "constitutional_version": "0.2",
                "principles": [
                    {
                        "principle_id": "EU_EXPLAIN",
                        "title": "Explain Limits",
                        "category": "transparency",
                        "description": "Keep limits visible in public-facing decisions.",
                    }
                ],
            },
        )
    )

    assert result.accepted is True
    assert any("safe_claim" in item for item in result.warnings)
