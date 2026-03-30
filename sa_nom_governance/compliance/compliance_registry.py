import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class CapabilitySnapshot:
    capability_id: str
    status: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "capability_id": self.capability_id,
            "status": self.status,
            "reason": self.reason,
        }


class ComplianceFrameworkRegistry:
    def __init__(self, catalog_path: Path) -> None:
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()

    def build_snapshot(
        self,
        *,
        runtime_health: dict[str, object],
        access_control_health: dict[str, object],
        roles: list[dict[str, object]],
        evidence_summary: dict[str, object] | None = None,
    ) -> dict[str, object]:
        capabilities = self._capability_statuses(
            runtime_health=runtime_health,
            access_control_health=access_control_health,
            roles=roles,
            evidence_summary=evidence_summary or {},
        )
        frameworks: list[dict[str, object]] = []
        covered_total = 0
        partial_total = 0
        gap_total = 0
        for framework in self.catalog.get("frameworks", []):
            control_rows: list[dict[str, object]] = []
            covered = partial = gap = 0
            for control in framework.get("controls", []):
                capability_ids = [str(value) for value in control.get("capabilities", [])]
                statuses = [capabilities[item].status for item in capability_ids if item in capabilities]
                if statuses and all(status == "covered" for status in statuses):
                    status = "covered"
                    covered += 1
                elif any(status in {"covered", "partial"} for status in statuses):
                    status = "partial"
                    partial += 1
                else:
                    status = "gap"
                    gap += 1
                control_rows.append(
                    {
                        "control_id": control.get("control_id"),
                        "title": control.get("title"),
                        "status": status,
                        "capabilities": capability_ids,
                    }
                )
            covered_total += covered
            partial_total += partial
            gap_total += gap
            frameworks.append(
                {
                    "framework_id": framework.get("framework_id"),
                    "name": framework.get("name"),
                    "version": framework.get("version"),
                    "description": framework.get("description"),
                    "profile_type": framework.get("profile_type", "baseline"),
                    "advisory_notice": framework.get("advisory_notice"),
                    "references": framework.get("references", []),
                    "controls_total": len(control_rows),
                    "covered_controls": covered,
                    "partial_controls": partial,
                    "gap_controls": gap,
                    "controls": control_rows,
                }
            )

        role_mappings = [
            {
                "role_id": role.get("role_id"),
                "title": role.get("title"),
                "controls": self.map_role_controls(role),
            }
            for role in roles
        ]

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "frameworks_total": len(frameworks),
                "covered_controls": covered_total,
                "partial_controls": partial_total,
                "gap_controls": gap_total,
            },
            "capabilities": {key: item.to_dict() for key, item in capabilities.items()},
            "frameworks": frameworks,
            "role_mappings": role_mappings,
        }

    def map_role_controls(self, role: dict[str, object]) -> list[dict[str, str]]:
        controls: list[dict[str, str]] = []
        if role.get("allow") or role.get("deny"):
            controls.extend(
                [
                    {"framework": "ISO_27001_BASELINE", "control_id": "ACCESS_BOUNDARY", "reason": "Role pack defines allow/deny authority boundaries."},
                    {"framework": "SOC2_BASELINE", "control_id": "LOGICAL_ACCESS", "reason": "Role pack exposes least-privilege access boundaries."},
                ]
            )
        if role.get("reports_to") or role.get("escalation_to"):
            controls.extend(
                [
                    {"framework": "NIST_CSF_BASELINE", "control_id": "GOVERNED_ROLE_ACTIVATION", "reason": "Role pack participates in governed hierarchy and escalation."},
                    {"framework": "SOC2_BASELINE", "control_id": "OVERSIGHT", "reason": "Role pack defines oversight and escalation ownership."},
                ]
            )
        if role.get("safety_owner"):
            controls.append(
                {
                    "framework": "PDPA_BASELINE",
                    "control_id": "SENSITIVE_REVIEW",
                    "reason": "Role pack assigns a safety owner for high-sensitivity review.",
                }
            )
        if role.get("trusted_manifest_signature_status") == "verified":
            controls.append(
                {
                    "framework": "ISO_27001_BASELINE",
                    "control_id": "CHANGE_GOVERNANCE",
                    "reason": "Role pack is anchored to a verified trusted-manifest signature.",
                }
            )
        return controls

    def _capability_statuses(
        self,
        *,
        runtime_health: dict[str, object],
        access_control_health: dict[str, object],
        roles: list[dict[str, object]],
        evidence_summary: dict[str, object],
    ) -> dict[str, CapabilitySnapshot]:
        trusted_registry = runtime_health.get("trusted_registry", {})
        audit_integrity = runtime_health.get("audit_integrity", {})
        retention = runtime_health.get("retention", {})
        backups = runtime_health.get("runtime_backups", {})
        hierarchy = runtime_health.get("role_hierarchy", {})
        transition_policy = runtime_health.get("role_transition_policy", {})
        model_providers = runtime_health.get("model_providers", {})

        authority_ready = all((role.get("allow") or role.get("deny")) for role in roles) if roles else False
        oversight_ready = any(role.get("escalation_to") or role.get("safety_owner") for role in roles)
        evidence_ready = int(evidence_summary.get("exports_total", 0) or 0) >= 0
        configured_providers = int(model_providers.get("configured_providers", 0) or 0)
        default_provider_requested = bool(model_providers.get("default_provider"))
        default_provider_ready = model_providers.get("default_provider_ready") is not False

        return {
            "authority_boundaries": CapabilitySnapshot(
                "authority_boundaries",
                "covered" if authority_ready else "gap",
                "All live role packs define explicit allow/deny authority boundaries." if authority_ready else "One or more live role packs still lack explicit authority boundary encoding.",
            ),
            "role_transition_governance": CapabilitySnapshot(
                "role_transition_governance",
                "covered" if int(transition_policy.get("configured_rules", 0) or 0) > 0 else "partial",
                "Role transitions are evaluated against a configured transition policy matrix." if int(transition_policy.get("configured_rules", 0) or 0) > 0 else "Runtime relies on fallback transition governance without explicit matrix rules.",
            ),
            "human_oversight": CapabilitySnapshot(
                "human_oversight",
                "covered" if oversight_ready and int(hierarchy.get("roles_total", 0) or 0) > 0 else "partial",
                "Hierarchy and escalation ownership are present for the live role library." if oversight_ready else "Live role packs need clearer escalation or safety ownership.",
            ),
            "trusted_publication": CapabilitySnapshot(
                "trusted_publication",
                "covered" if trusted_registry.get("signature_trusted") else "gap",
                "Trusted registry signature verification is active for live role publication." if trusted_registry.get("signature_trusted") else "Trusted registry signatures are not currently trusted.",
            ),
            "audit_chain": CapabilitySnapshot(
                "audit_chain",
                "covered" if audit_integrity.get("status") == "verified" else "partial",
                "The audit ledger is sealed and verified." if audit_integrity.get("status") == "verified" else "Audit integrity requires attention before claiming full evidence readiness.",
            ),
            "retention_lifecycle": CapabilitySnapshot(
                "retention_lifecycle",
                "covered" if int(retention.get("datasets", 0) or 0) > 0 else "partial",
                "Retention and legal-hold lifecycle is active across tracked datasets." if int(retention.get("datasets", 0) or 0) > 0 else "Retention lifecycle exists but no tracked datasets were reported.",
            ),
            "session_security": CapabilitySnapshot(
                "session_security",
                "covered" if int(access_control_health.get("plain_file_tokens", 0) or 0) == 0 else "partial",
                "Session and file-based access profiles are hardened with hashed tokens." if int(access_control_health.get("plain_file_tokens", 0) or 0) == 0 else "Plain file tokens are still present in access control.",
            ),
            "recovery_continuity": CapabilitySnapshot(
                "recovery_continuity",
                "covered" if "backup_dir" in backups else "partial",
                "Runtime backup continuity is available for private-server recovery." if "backup_dir" in backups else "Recovery continuity evidence is incomplete.",
            ),
            "evidence_export": CapabilitySnapshot(
                "evidence_export",
                "covered" if evidence_ready else "partial",
                "Auditor evidence export is available from the runtime.",
            ),
            "ai_provider_connectivity": CapabilitySnapshot(
                "ai_provider_connectivity",
                "covered" if configured_providers > 0 and default_provider_ready else "partial" if configured_providers > 0 or default_provider_requested else "gap",
                "At least one approved AI provider is configured and ready for governed runtime probing." if configured_providers > 0 and default_provider_ready else "One or more AI providers are configured but the default runtime path still needs attention." if configured_providers > 0 or default_provider_requested else "No approved AI provider is configured for governed runtime use.",
            ),
        }

    def _load_catalog(self) -> dict[str, object]:
        if not self.catalog_path.exists():
            return {"frameworks": []}
        return json.loads(self.catalog_path.read_text(encoding="utf-8-sig"))
