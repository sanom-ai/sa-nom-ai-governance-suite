from pathlib import Path

from sa_nom_governance.compliance.trusted_registry import TrustedRegistry, VerifiedRoleSource


class RoleRegistry:
    def __init__(self, roles_dir: Path, manifest_path: Path | None = None, cache_path: Path | None = None, signing_key: str | None = None, signature_required: bool = True) -> None:
        self.roles_dir = roles_dir
        self.trusted_registry = TrustedRegistry(manifest_path=manifest_path, cache_path=cache_path, signing_key=signing_key, signature_required=signature_required)

    def resolve(self, role_id: str) -> Path:
        return self.roles_dir / f"{role_id}.ptn"

    def load_source(self, role_id: str) -> VerifiedRoleSource:
        return self.trusted_registry.load_verified_source(role_id=role_id, role_path=self.resolve(role_id))

    def reload(self) -> None:
        self.trusted_registry.reload()
