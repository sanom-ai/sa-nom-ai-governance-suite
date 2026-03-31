from pathlib import Path
from unittest.mock import patch

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_test_app(runtime_dir: Path):
    config = AppConfig(persist_runtime=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    config.audit_log_path = runtime_dir / 'runtime_audit_log.jsonl'
    config.override_store_path = runtime_dir / 'runtime_override_store.json'
    config.lock_store_path = runtime_dir / 'runtime_lock_store.json'
    config.consistency_store_path = runtime_dir / 'runtime_consistency_store.json'
    config.workflow_state_store_path = runtime_dir / 'runtime_workflow_state_store.json'
    config.runtime_recovery_store_path = runtime_dir / 'runtime_recovery_store.json'
    config.runtime_dead_letter_path = runtime_dir / 'runtime_dead_letter_log.jsonl'
    return build_engine_app(config)


def test_runtime_recovery_captures_dead_letter_when_retry_exhausted(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)

    with patch.object(app.engine, '_process_once', side_effect=ConnectionError('transient network')):
        result = app.request(
            requester='tester',
            role_id='GOV',
            action='review_audit',
            payload={'resource': 'audit', 'resource_id': 'REC-001'},
            metadata={'runtime_retry_max_attempts': 1},
        )

    assert result.outcome == 'retryable'
    records = app.list_runtime_recovery_records(status='dead_letter')
    assert len(records) == 1
    record = records[0]
    assert record['request_id'] == result.metadata['request_id']
    assert record['failure_classification'] == 'retry_exhausted'

    dead_letters = app.list_runtime_dead_letters(limit=10)
    assert any(item['request_id'] == result.metadata['request_id'] for item in dead_letters)


def test_runtime_recovery_resume_replays_dead_letter_request(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)

    with patch.object(app.engine, '_process_once', side_effect=TimeoutError('temporary timeout')):
        failed = app.request(
            requester='tester',
            role_id='GOV',
            action='review_audit',
            payload={'resource': 'audit', 'resource_id': 'REC-002'},
            metadata={'runtime_retry_max_attempts': 1},
        )

    assert failed.outcome == 'retryable'
    resumed = app.resume_runtime_recovery(failed.metadata['request_id'], resumed_by='EXEC_OWNER')
    assert resumed.outcome == 'approved'

    updated = app.list_runtime_recovery_records(limit=5)[0]
    assert updated['status'] == 'resumed'
    assert updated['resumed_by'] == 'EXEC_OWNER'
    assert updated['resumed_request_id'] == resumed.metadata['request_id']


def test_runtime_recovery_resume_is_fail_closed_for_non_resumable_outcome(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)

    with patch.object(app.engine, '_process_once', side_effect=PermissionError('forbidden')):
        failed = app.request(
            requester='tester',
            role_id='GOV',
            action='review_audit',
            payload={'resource': 'audit', 'resource_id': 'REC-003'},
            metadata={'runtime_retry_max_attempts': 1},
        )

    assert failed.outcome == 'rejected'
    try:
        app.resume_runtime_recovery(failed.metadata['request_id'], resumed_by='EXEC_OWNER')
    except ValueError as exc:
        assert 'fail-closed' in str(exc)
    else:
        raise AssertionError('Expected fail-closed recovery resume for non-resumable rejected outcome.')
