import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sa_nom_governance.utils.config import AppConfig


class AuditorEvidencePackBuilder:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def create_pack(
        self,
        *,
        requested_by: str,
        runtime_health: dict[str, object],
        access_control_health: dict[str, object],
        compliance_snapshot: dict[str, object],
        roles: list[dict[str, object]],
        audit_entries: list[dict[str, object]],
        retention_report: dict[str, object],
        go_live_readiness: dict[str, object],
        operations: dict[str, object],
        studio_summary: dict[str, object],
    ) -> dict[str, object]:
        pack_id = self._build_pack_id()
        pack_dir = self.config.runtime_evidence_dir / pack_id
        artifacts_dir = pack_dir / 'artifacts'
        files_dir = pack_dir / 'files'
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        files_dir.mkdir(parents=True, exist_ok=True)

        artifact_records: list[dict[str, object]] = []
        for name, payload in [
            ('runtime_health.json', runtime_health),
            ('access_control_health.json', access_control_health),
            ('compliance_snapshot.json', compliance_snapshot),
            ('roles_snapshot.json', roles),
            ('audit_excerpt.json', audit_entries),
            ('retention_report.json', retention_report),
            ('go_live_readiness.json', go_live_readiness),
            ('operations_summary.json', operations),
            ('studio_summary.json', studio_summary),
        ]:
            artifact_records.append(self._write_json_artifact(artifacts_dir / name, payload, dataset=name.removesuffix('.json')))

        file_records: list[dict[str, object]] = []
        for dataset, path in self._tracked_paths():
            file_records.append(self._copy_file_record(dataset=dataset, path=path, files_dir=files_dir))

        manifest = {
            'pack_id': pack_id,
            'created_at': self._utc_now(),
            'requested_by': requested_by,
            'environment': self.config.environment,
            'export_path': str(pack_dir),
            'artifact_total': len(artifact_records),
            'file_total': len(file_records),
            'artifacts': artifact_records,
            'files': file_records,
            'compliance_summary': compliance_snapshot.get('summary', {}),
            'audit_integrity': runtime_health.get('audit_integrity', {}),
            'trusted_registry': runtime_health.get('trusted_registry', {}),
            'go_live_status': go_live_readiness.get('status', 'unknown'),
        }
        (pack_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return manifest

    def list_packs(self, limit: int = 20) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for manifest_path in self._manifest_paths()[:limit]:
            try:
                manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
            except Exception as error:
                items.append(
                    {
                        'pack_id': manifest_path.parent.name,
                        'created_at': None,
                        'requested_by': '-',
                        'export_path': str(manifest_path.parent),
                        'status': 'invalid_manifest',
                        'error': str(error),
                    }
                )
                continue
            items.append(
                {
                    'pack_id': manifest.get('pack_id', manifest_path.parent.name),
                    'created_at': manifest.get('created_at'),
                    'requested_by': manifest.get('requested_by', '-'),
                    'export_path': manifest.get('export_path', str(manifest_path.parent)),
                    'artifact_total': int(manifest.get('artifact_total', 0)),
                    'file_total': int(manifest.get('file_total', 0)),
                    'go_live_status': manifest.get('go_live_status', 'unknown'),
                    'covered_controls': manifest.get('compliance_summary', {}).get('covered_controls', 0),
                    'gap_controls': manifest.get('compliance_summary', {}).get('gap_controls', 0),
                    'status': 'ready',
                }
            )
        return items

    def create_workflow_proof_bundle(
        self,
        *,
        requested_by: str,
        workflow_id: str,
        workflow_state: dict[str, object],
        operational_readiness: dict[str, object],
        recovery_records: list[dict[str, object]],
        dead_letters: list[dict[str, object]],
        human_sessions: list[dict[str, object]],
        audit_entries: list[dict[str, object]],
    ) -> dict[str, object]:
        bundle_id = self._build_pack_id(prefix='workflow-proof')
        pack_dir = self.config.runtime_evidence_dir / bundle_id
        artifacts_dir = pack_dir / 'artifacts'
        files_dir = pack_dir / 'files'
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        files_dir.mkdir(parents=True, exist_ok=True)

        artifact_records: list[dict[str, object]] = []
        for name, payload in [
            ('workflow_state.json', workflow_state),
            ('operational_readiness.json', operational_readiness),
            ('recovery_records.json', recovery_records),
            ('dead_letters.json', dead_letters),
            ('human_sessions.json', human_sessions),
            ('audit_excerpt.json', audit_entries),
        ]:
            artifact_records.append(self._write_json_artifact(artifacts_dir / name, payload, dataset=name.removesuffix('.json')))

        file_records: list[dict[str, object]] = []
        for dataset, path in self._tracked_paths():
            file_records.append(self._copy_file_record(dataset=dataset, path=path, files_dir=files_dir))

        manifest = {
            'bundle_id': bundle_id,
            'bundle_type': 'workflow_proof',
            'workflow_id': workflow_id,
            'created_at': self._utc_now(),
            'requested_by': requested_by,
            'environment': self.config.environment,
            'export_path': str(pack_dir),
            'artifact_total': len(artifact_records),
            'file_total': len(file_records),
            'artifacts': artifact_records,
            'files': file_records,
            'workflow_state': {
                'current_state': workflow_state.get('current_state'),
                'role_state': workflow_state.get('role_state'),
                'request_id': workflow_state.get('request_id'),
                'action': workflow_state.get('action'),
            },
            'operational_status': operational_readiness.get('status', 'unknown'),
            'recovery_total': len(recovery_records),
            'dead_letter_total': len(dead_letters),
            'human_session_total': len(human_sessions),
            'audit_excerpt_total': len(audit_entries),
        }
        (pack_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return manifest

    def list_workflow_proof_bundles(self, limit: int = 20) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for manifest_path in self._workflow_proof_manifest_paths()[:limit]:
            try:
                manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
            except Exception as error:
                items.append(
                    {
                        'bundle_id': manifest_path.parent.name,
                        'created_at': None,
                        'requested_by': '-',
                        'export_path': str(manifest_path.parent),
                        'status': 'invalid_manifest',
                        'error': str(error),
                    }
                )
                continue
            items.append(
                {
                    'bundle_id': manifest.get('bundle_id', manifest_path.parent.name),
                    'workflow_id': manifest.get('workflow_id'),
                    'created_at': manifest.get('created_at'),
                    'requested_by': manifest.get('requested_by', '-'),
                    'export_path': manifest.get('export_path', str(manifest_path.parent)),
                    'artifact_total': int(manifest.get('artifact_total', 0)),
                    'file_total': int(manifest.get('file_total', 0)),
                    'operational_status': manifest.get('operational_status', 'unknown'),
                    'recovery_total': int(manifest.get('recovery_total', 0)),
                    'dead_letter_total': int(manifest.get('dead_letter_total', 0)),
                    'human_session_total': int(manifest.get('human_session_total', 0)),
                    'status': 'ready',
                }
            )
        return items

    def summary(self) -> dict[str, object]:
        packs = self._manifest_paths()
        proofs = self._workflow_proof_manifest_paths()
        latest = self.list_packs(limit=1)
        latest_proof = self.list_workflow_proof_bundles(limit=1)
        return {
            'evidence_dir': str(self.config.runtime_evidence_dir),
            'exports_total': len(packs),
            'workflow_proof_total': len(proofs),
            'latest_export': latest[0] if latest else None,
            'latest_workflow_proof': latest_proof[0] if latest_proof else None,
        }

    def _tracked_paths(self) -> list[tuple[str, Path | None]]:
        tracked: list[tuple[str, Path | None]] = [
            ('audit_log', self.config.audit_log_path),
            ('trusted_registry_manifest', self.config.trusted_registry_manifest_path),
            ('startup_smoke_report', self.config.startup_smoke_report_path),
            ('role_transition_matrix', self.config.role_transition_matrix_path),
            ('compliance_frameworks', self.config.compliance_frameworks_path),
        ]
        for role_path in sorted(self.config.roles_dir.glob('*.ptn')):
            tracked.append((f'role_pack:{role_path.name}', role_path))
        return tracked

    def _write_json_artifact(self, path: Path, payload: object, dataset: str) -> dict[str, object]:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
        path.write_text(encoded, encoding='utf-8')
        return {
            'dataset': dataset,
            'artifact_path': str(path),
            'bytes': path.stat().st_size,
            'sha256': self._sha256(path),
        }

    def _copy_file_record(self, dataset: str, path: Path | None, files_dir: Path) -> dict[str, object]:
        source_path = str(path) if path is not None else None
        if path is None or not path.exists() or path.is_dir():
            return {
                'dataset': dataset,
                'source_path': source_path,
                'present': False,
                'copy_path': None,
                'bytes': 0,
                'sha256': None,
            }
        target_name = path.name
        target_path = files_dir / target_name
        if target_path.exists():
            target_path = files_dir / f"{dataset.replace(':', '__')}__{target_name}"
        shutil.copy2(path, target_path)
        return {
            'dataset': dataset,
            'source_path': source_path,
            'present': True,
            'copy_path': str(target_path),
            'bytes': target_path.stat().st_size,
            'sha256': self._sha256(target_path),
        }

    def _manifest_paths(self) -> list[Path]:
        root = self.config.runtime_evidence_dir
        if not root.exists():
            return []
        manifests = [
            path
            for path in root.glob('*/manifest.json')
            if path.is_file() and self._manifest_kind(path) != 'workflow_proof'
        ]
        return sorted(manifests, key=lambda item: item.stat().st_mtime, reverse=True)

    def _workflow_proof_manifest_paths(self) -> list[Path]:
        root = self.config.runtime_evidence_dir
        if not root.exists():
            return []
        manifests = [
            path
            for path in root.glob('*/manifest.json')
            if path.is_file() and self._manifest_kind(path) == 'workflow_proof'
        ]
        return sorted(manifests, key=lambda item: item.stat().st_mtime, reverse=True)

    def _manifest_kind(self, path: Path) -> str:
        try:
            manifest = json.loads(path.read_text(encoding='utf-8-sig'))
        except Exception:
            return 'unknown'
        return str(manifest.get('bundle_type', 'evidence_pack'))

    def _build_pack_id(self, prefix: str = 'evidence') -> str:
        timestamp = datetime.now(timezone.utc).strftime(f'{prefix}-%Y%m%dT%H%M%SZ')
        candidate = timestamp
        root = self.config.runtime_evidence_dir
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
