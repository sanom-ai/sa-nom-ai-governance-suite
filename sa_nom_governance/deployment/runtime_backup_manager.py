import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sa_nom_governance.utils.config import AppConfig


class RuntimeBackupManager:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def create_backup(self, requested_by: str, metadata: dict[str, object] | None = None) -> dict[str, object]:
        backup_id = self._build_backup_id()
        backup_dir = self.config.runtime_backup_dir / backup_id
        files_dir = backup_dir / 'files'
        files_dir.mkdir(parents=True, exist_ok=True)

        file_records: list[dict[str, object]] = []
        bytes_total = 0
        for dataset, path in self._tracked_paths():
            record = self._copy_file_record(dataset=dataset, path=path, files_dir=files_dir)
            bytes_total += int(record.get('bytes', 0) or 0)
            file_records.append(record)

        manifest = {
            'backup_id': backup_id,
            'created_at': self._utc_now(),
            'requested_by': requested_by,
            'environment': self.config.environment,
            'backup_path': str(backup_dir),
            'files_total': len(file_records),
            'files_present': sum(1 for item in file_records if item.get('present')),
            'files_missing': sum(1 for item in file_records if not item.get('present')),
            'bytes_total': bytes_total,
            'metadata': metadata or {},
            'files': file_records,
        }
        (backup_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return manifest

    def list_backups(self, limit: int = 20) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for manifest_path in self._manifest_paths()[:limit]:
            try:
                manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
            except Exception as error:
                items.append({
                    'backup_id': manifest_path.parent.name,
                    'created_at': None,
                    'requested_by': '-',
                    'files_total': 0,
                    'files_present': 0,
                    'files_missing': 0,
                    'bytes_total': 0,
                    'backup_path': str(manifest_path.parent),
                    'status': 'invalid_manifest',
                    'error': str(error),
                })
                continue
            items.append({
                'backup_id': manifest.get('backup_id', manifest_path.parent.name),
                'created_at': manifest.get('created_at'),
                'requested_by': manifest.get('requested_by', '-'),
                'files_total': int(manifest.get('files_total', 0)),
                'files_present': int(manifest.get('files_present', 0)),
                'files_missing': int(manifest.get('files_missing', 0)),
                'bytes_total': int(manifest.get('bytes_total', 0)),
                'backup_path': manifest.get('backup_path', str(manifest_path.parent)),
                'status': 'ready',
            })
        return items

    def summary(self) -> dict[str, object]:
        manifests = self._manifest_paths()
        latest = self.list_backups(limit=1)
        return {
            'backup_dir': str(self.config.runtime_backup_dir),
            'backups_total': len(manifests),
            'latest_backup': latest[0] if latest else None,
        }

    def _tracked_paths(self) -> list[tuple[str, Path | None]]:
        tracked: list[tuple[str, Path | None]] = [
            ('audit_log', self.config.audit_log_path),
            ('override_store', self.config.override_store_path),
            ('lock_store', self.config.lock_store_path),
            ('consistency_store', self.config.consistency_store_path),
            ('session_store', self.config.session_store_path),
            ('role_private_studio_store', self.config.role_private_studio_store_path),
            ('startup_smoke_report', self.config.startup_smoke_report_path),
            ('access_profiles', self.config.access_profiles_path),
            ('trusted_registry_manifest', self.config.trusted_registry_manifest_path),
            ('trusted_registry_cache', self.config.trusted_registry_cache_path),
            ('legal_holds', self.config.legal_hold_path),
        ]
        for role_path in sorted(self.config.roles_dir.glob('*.ptn')):
            tracked.append((f'role_pack:{role_path.name}', role_path))
        return tracked

    def _copy_file_record(self, dataset: str, path: Path | None, files_dir: Path) -> dict[str, object]:
        source_path = str(path) if path is not None else None
        if path is None or not path.exists() or path.is_dir():
            return {
                'dataset': dataset,
                'source_path': source_path,
                'present': False,
                'backup_path': None,
                'bytes': 0,
                'sha256': None,
            }

        target_name = path.name
        target_path = files_dir / target_name
        if target_path.exists():
            safe_dataset = dataset.replace(':', '__').replace('/', '_')
            target_path = files_dir / f'{safe_dataset}__{target_name}'
        shutil.copy2(path, target_path)
        return {
            'dataset': dataset,
            'source_path': source_path,
            'present': True,
            'backup_path': str(target_path),
            'bytes': target_path.stat().st_size,
            'sha256': self._sha256(target_path),
        }

    def _manifest_paths(self) -> list[Path]:
        root = self.config.runtime_backup_dir
        if not root.exists():
            return []
        manifests = [path for path in root.glob('*/manifest.json') if path.is_file()]
        return sorted(manifests, key=lambda item: item.stat().st_mtime, reverse=True)

    def _build_backup_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime('backup-%Y%m%dT%H%M%SZ')
        candidate = timestamp
        root = self.config.runtime_backup_dir
        counter = 1
        while (root / candidate).exists():
            counter += 1
            candidate = f'{timestamp}-{counter}'
        return candidate

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(chunk)
        return digest.hexdigest()

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
