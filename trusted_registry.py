import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_SIGNATURE_ALGORITHM = 'hmac_sha256'


@dataclass(slots=True)
class SignatureVerification:
    status: str
    trusted: bool
    algorithm: str | None
    key_id: str | None
    signed_at: str | None
    message: str


@dataclass(slots=True)
class VerifiedRoleSource:
    role_id: str
    file_name: str
    source: str
    source_origin: str
    sha256: str
    manifest_sha256: str
    trust_status: str
    signed_by: str
    signature_mode: str
    manifest_signature_status: str
    manifest_signature_key_id: str | None


class TrustedRegistryError(Exception):
    pass


class TrustedRegistry:
    def __init__(self, manifest_path: Path | None, cache_path: Path | None, signing_key: str | None = None, signature_required: bool = True) -> None:
        self.manifest_path = manifest_path
        self.cache_path = cache_path
        self.signing_key = signing_key
        self.signature_required = signature_required
        self.reload()

    def reload(self) -> None:
        self.manifest = self._load_json(self.manifest_path, default={'roles': {}})
        self.cache = self._load_json(self.cache_path, default={'entries': {}})
        self.signature_verification = self._verify_manifest_signature()

    def load_verified_source(self, role_id: str, role_path: Path) -> VerifiedRoleSource:
        self._ensure_manifest_trusted()
        manifest_entry = self._manifest_entry(role_id)
        expected_hash = str(manifest_entry['sha256'])
        file_name = str(manifest_entry.get('file_name', role_path.name))

        if role_path.exists():
            live_source = role_path.read_text(encoding='utf-8')
            live_hash = compute_sha256(live_source)
            if live_hash == expected_hash:
                self._update_cache(role_id=role_id, file_name=file_name, sha256=live_hash, source=live_source)
                return self._build_verified_source(role_id=role_id, file_name=file_name, source=live_source, source_origin='trusted_registry', sha256=live_hash, manifest_entry=manifest_entry)

        cached = self.cache.get('entries', {}).get(role_id)
        if cached and str(cached.get('sha256')) == expected_hash:
            return self._build_verified_source(role_id=role_id, file_name=file_name, source=str(cached['source']), source_origin='last_known_good', sha256=str(cached['sha256']), manifest_entry=manifest_entry)

        raise TrustedRegistryError(f'Trusted registry verification failed for role {role_id}.')

    def health(self) -> dict[str, object]:
        return {
            'manifest_path': str(self.manifest_path) if self.manifest_path else None,
            'cache_path': str(self.cache_path) if self.cache_path else None,
            'role_entries': len(self.manifest.get('roles', {})),
            'cached_entries': len(self.cache.get('entries', {})),
            'signature_required': self.signature_required,
            'signature_status': self.signature_verification.status,
            'signature_trusted': self.signature_verification.trusted,
            'signature_algorithm': self.signature_verification.algorithm,
            'signature_key_id': self.signature_verification.key_id,
            'signature_signed_at': self.signature_verification.signed_at,
            'signature_message': self.signature_verification.message,
        }

    def _build_verified_source(self, role_id: str, file_name: str, source: str, source_origin: str, sha256: str, manifest_entry: dict[str, object]) -> VerifiedRoleSource:
        return VerifiedRoleSource(role_id=role_id, file_name=file_name, source=source, source_origin=source_origin, sha256=sha256, manifest_sha256=str(manifest_entry['sha256']), trust_status=str(manifest_entry.get('trust_status', 'trusted')), signed_by=str(manifest_entry.get('signed_by', 'EXEC_OWNER')), signature_mode=str(manifest_entry.get('signature_mode', 'sha256_manifest_hmac')), manifest_signature_status=self.signature_verification.status, manifest_signature_key_id=self.signature_verification.key_id)

    def _manifest_entry(self, role_id: str) -> dict[str, object]:
        roles = self.manifest.get('roles', {})
        if role_id not in roles:
            raise TrustedRegistryError(f'Role {role_id} is not present in the trusted registry manifest.')
        return roles[role_id]

    def _ensure_manifest_trusted(self) -> None:
        if not self.signature_verification.trusted:
            raise TrustedRegistryError(f'Trusted registry signature verification failed: {self.signature_verification.message}')

    def _verify_manifest_signature(self) -> SignatureVerification:
        if self.manifest_path is None or not self.manifest_path.exists():
            return SignatureVerification(status='missing_manifest', trusted=not self.signature_required, algorithm=None, key_id=None, signed_at=None, message='Trusted registry manifest file is missing.')

        signature_block = self.manifest.get('signature')
        if not isinstance(signature_block, dict):
            return SignatureVerification(status='missing_signature', trusted=not self.signature_required, algorithm=None, key_id=None, signed_at=None, message='Trusted registry manifest has no signature block.')

        algorithm = str(signature_block.get('algorithm') or '')
        key_id = str(signature_block.get('key_id') or '') or None
        signed_at = str(signature_block.get('signed_at') or '') or None
        signature_value = str(signature_block.get('value') or '')

        if algorithm != DEFAULT_SIGNATURE_ALGORITHM:
            return SignatureVerification(status='unsupported_algorithm', trusted=False, algorithm=algorithm or None, key_id=key_id, signed_at=signed_at, message=f'Unsupported trusted registry signature algorithm: {algorithm or "unknown"}.')
        if not signature_value:
            return SignatureVerification(status='missing_signature_value', trusted=False, algorithm=algorithm, key_id=key_id, signed_at=signed_at, message='Trusted registry signature value is missing.')
        if not self.signing_key:
            return SignatureVerification(status='missing_key', trusted=False, algorithm=algorithm, key_id=key_id, signed_at=signed_at, message='No trusted registry signing key is configured.')

        expected_value = sign_manifest(self.manifest, self.signing_key)
        if hmac.compare_digest(signature_value, expected_value):
            return SignatureVerification(status='verified', trusted=True, algorithm=algorithm, key_id=key_id, signed_at=signed_at, message='Trusted registry manifest signature verified.')
        return SignatureVerification(status='invalid_signature', trusted=False, algorithm=algorithm, key_id=key_id, signed_at=signed_at, message='Trusted registry manifest signature does not match the configured key.')

    def _update_cache(self, role_id: str, file_name: str, sha256: str, source: str) -> None:
        self.cache.setdefault('entries', {})[role_id] = {'file_name': file_name, 'sha256': sha256, 'source': source, 'captured_at': utc_now()}
        self.cache['generated_at'] = utc_now()
        if self.cache_path is not None:
            self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding='utf-8')

    def _load_json(self, path: Path | None, default: dict[str, object]) -> dict[str, object]:
        if path is None or not path.exists():
            return default.copy()
        return json.loads(path.read_text(encoding='utf-8'))


def compute_sha256(source: str) -> str:
    return hashlib.sha256(source.encode('utf-8')).hexdigest()


def canonical_manifest_payload(manifest: dict[str, object]) -> str:
    return json.dumps({key: value for key, value in manifest.items() if key != 'signature'}, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sign_manifest(manifest: dict[str, object], signing_key: str) -> str:
    payload = canonical_manifest_payload(manifest)
    return hmac.new(signing_key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()


def build_trusted_registry_artifacts(roles_dir: Path, role_ids: list[str], signing_key: str, key_id: str, signed_by: str = 'EXEC_OWNER') -> tuple[dict[str, object], dict[str, object]]:
    if not signing_key:
        raise ValueError('A trusted registry signing key is required.')
    roles: dict[str, object] = {}
    cache_entries: dict[str, object] = {}
    for role_id in role_ids:
        role_path = roles_dir / f'{role_id}.ptn'
        source = role_path.read_text(encoding='utf-8')
        sha256 = compute_sha256(source)
        roles[role_id] = {'file_name': role_path.name, 'sha256': sha256, 'trust_status': 'trusted', 'signed_by': signed_by, 'signature_mode': 'sha256_manifest_hmac', 'registered_at': utc_now()}
        cache_entries[role_id] = {'file_name': role_path.name, 'sha256': sha256, 'source': source, 'captured_at': utc_now()}
    manifest = {'registry_name': 'SA-NOM Trusted PTAG Registry', 'generated_at': utc_now(), 'roles': roles}
    manifest['signature'] = {'algorithm': DEFAULT_SIGNATURE_ALGORITHM, 'key_id': key_id, 'signed_by': signed_by, 'signed_at': utc_now(), 'value': sign_manifest(manifest, signing_key)}
    cache = {'registry_name': 'SA-NOM Trusted PTAG Cache', 'generated_at': utc_now(), 'entries': cache_entries}
    return manifest, cache


def write_trusted_registry_files(roles_dir: Path, manifest_path: Path, cache_path: Path, role_ids: list[str], signing_key: str, key_id: str, signed_by: str = 'EXEC_OWNER') -> tuple[dict[str, object], dict[str, object]]:
    manifest, cache = build_trusted_registry_artifacts(roles_dir=roles_dir, role_ids=role_ids, signing_key=signing_key, key_id=key_id, signed_by=signed_by)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest, cache


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
