from types import SimpleNamespace
from unittest.mock import patch

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


class _SessionEnvelope:
    def __init__(self, payload):
        self._payload = dict(payload)

    def to_dict(self):
        return dict(self._payload)



def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))



def test_list_roles_marks_semantic_missing_role_invalid(tmp_path, monkeypatch) -> None:
    app = build_test_app()
    broken_dir = tmp_path / 'roles'
    broken_dir.mkdir()
    (broken_dir / 'BROKEN.ptn').write_text('# broken role\n', encoding='utf-8')

    monkeypatch.setattr(app.registry, 'roles_dir', broken_dir)
    monkeypatch.setattr(
        app.loader,
        'load',
        lambda role_id: SimpleNamespace(
            roles={},
            authorities={},
            validation_issues=[],
            headers={'trusted_manifest_signature_status': 'invalid'},
        ),
    )

    roles = app.list_roles()

    assert roles[0]['status'] == 'invalid'
    assert roles[0]['load_error']['stage'] == 'semantic'
    assert roles[0]['load_error']['message'].startswith('Role BROKEN is missing')



def test_reseal_audit_log_and_retention_enforce_record_runtime_events(monkeypatch) -> None:
    app = build_test_app()
    events = []
    reloads = []

    monkeypatch.setattr(
        app.engine.audit_logger,
        'reseal_legacy_entries',
        lambda: {'status': 'resealed', 'before_integrity': {'status': 'legacy'}, 'after_integrity': {'status': 'verified'}},
    )
    monkeypatch.setattr(app.engine.audit_logger, 'health', lambda: {'status': 'verified'})
    monkeypatch.setattr(app.engine.audit_logger, 'record_event', lambda **kwargs: events.append(kwargs))
    monkeypatch.setattr(app.engine.audit_logger, 'reload', lambda: reloads.append('reloaded'))
    monkeypatch.setattr(
        app.retention_manager,
        'enforce',
        lambda dry_run=True: {
            'status': 'completed',
            'archived_total': 1,
            'purged_total': 0,
            'blocked_total': 0,
            'actions': ['archive'],
        },
    )

    reseal = app.reseal_audit_log('Owner')
    dry_run = app.enforce_retention(dry_run=True)
    enforced = app.enforce_retention(dry_run=False)

    assert reseal['final_integrity']['status'] == 'verified'
    assert dry_run['status'] == 'completed'
    assert enforced['status'] == 'completed'
    assert reloads == ['reloaded']
    assert any(event['action'] == 'audit_reseal' for event in events)
    assert any(event['action'] == 'retention_dry_run' for event in events)
    assert any(event['action'] == 'retention_enforce' for event in events)



def test_studio_runtime_methods_and_human_ask_dispatch_events(monkeypatch) -> None:
    app = build_test_app()
    dispatches = []
    reloads = []

    monkeypatch.setattr(
        app,
        '_dispatch_integration_event',
        lambda event_type, payload, **kwargs: dispatches.append((event_type, payload, kwargs)) or {'failed_total': 0, 'targets_matched': 1},
    )
    monkeypatch.setattr(
        app.role_private_studio,
        'create_request',
        lambda payload, requested_by: {
            'request_id': 'studio-1',
            'status': 'draft',
            'structured_jd': {'role_name': 'Finance Director', 'business_domain': 'finance'},
            'summary': {'role_id': 'FINANCE_DIRECTOR'},
        },
    )
    monkeypatch.setattr(app.role_private_studio, 'update_request', lambda request_id, payload, updated_by: {'request_id': request_id, 'updated_by': updated_by})
    monkeypatch.setattr(app.role_private_studio, 'update_request_ptag', lambda request_id, ptag_source, updated_by: {'request_id': request_id, 'ptag_source': ptag_source, 'updated_by': updated_by})
    monkeypatch.setattr(app.role_private_studio, 'reset_request_ptag', lambda request_id, updated_by: {'request_id': request_id, 'updated_by': updated_by, 'ptag_reset': True})
    monkeypatch.setattr(app.role_private_studio, 'refresh_request', lambda request_id: {'request_id': request_id, 'status': 'refreshed'})
    monkeypatch.setattr(
        app.role_private_studio,
        'restore_request_revision',
        lambda request_id, revision_number, restored_by: {
            'request_id': request_id,
            'status': 'restored',
            'summary': {'role_id': 'FINANCE_DIRECTOR'},
        },
    )
    monkeypatch.setattr(
        app.role_private_studio,
        'review_request',
        lambda request_id, reviewer, decision, note: {
            'request_id': request_id,
            'status': 'reviewed',
            'summary': {'role_id': 'FINANCE_DIRECTOR'},
            'publish_readiness': {'status': 'ready'},
        },
    )
    monkeypatch.setattr(
        app.role_private_studio,
        'publish_request',
        lambda request_id, published_by: {
            'request_id': request_id,
            'status': 'published',
            'publish_artifact': {'role_id': 'FINANCE_DIRECTOR', 'path': 'roles/FINANCE_DIRECTOR.ptn'},
        },
    )
    monkeypatch.setattr(app.engine.hierarchy_registry, 'reload', lambda: reloads.append('hierarchy'))
    monkeypatch.setattr(app.engine.role_transition_policy, 'reload', lambda: reloads.append('policy'))
    monkeypatch.setattr(app.human_ask, 'list_sessions', lambda status=None, limit=100: [{'session_id': 'session-1', 'status': status or 'active', 'limit': limit}])
    monkeypatch.setattr(app.human_ask, 'list_human_decision_inbox', lambda inbox_state=None, queue_lane=None, limit=100: [{'session_id': 'session-1', 'inbox_state': inbox_state or 'human_action_required', 'queue_lane': queue_lane}])
    monkeypatch.setattr(app.human_ask, 'get_session', lambda session_id: {'session_id': session_id})
    monkeypatch.setattr(app.human_ask, 'callable_directory', lambda limit=200: {'entries': [{'role_id': 'GOV'}], 'limit': limit})
    monkeypatch.setattr(
        app.human_ask,
        'create_session',
        lambda payload, requested_by: {
            'session_id': 'session-1',
            'status': 'open',
            'mode': 'report',
            'participant': {'role_id': 'GOV'},
            'decision_summary': {'posture': 'ready'},
        },
    )
    monkeypatch.setattr(
        app.human_ask,
        'create_studio_record_request',
        lambda studio_request_id, payload, requested_by: {
            'session_id': 'session-2',
            'status': 'open',
            'mode': 'meeting',
            'participant': {'role_id': 'FINANCE_DIRECTOR'},
            'decision_summary': {'posture': 'human_gate_open'},
        },
    )

    created = app.create_studio_request({'role_name': 'Finance Director'}, requested_by='Owner')
    updated = app.update_studio_request('studio-1', {'note': 'revise'}, updated_by='Owner')
    updated_ptag = app.update_studio_request_ptag('studio-1', 'ptag body', updated_by='Owner')
    reset_ptag = app.reset_studio_request_ptag('studio-1', updated_by='Owner')
    refreshed = app.refresh_studio_request('studio-1')
    restored = app.restore_studio_request_revision('studio-1', revision_number=2, restored_by='Owner')
    reviewed = app.review_studio_request('studio-1', reviewer='Reviewer', decision='approve', note='ready')
    published = app.publish_studio_request('studio-1', published_by='Owner')
    sessions = app.list_human_ask_sessions(status='active', limit=5)
    inbox = app.list_human_decision_inbox(inbox_state='human_action_required', queue_lane='review', limit=5)
    fetched_session = app.get_human_ask_session('session-1')
    directory = app.list_callable_directory(limit=10)
    human_session = app.create_human_ask_session({'mode': 'report'}, requested_by='Owner')
    studio_session = app.create_human_ask_studio_record('studio-1', {'mode': 'meeting'}, requested_by='Owner')

    assert created['request_id'] == 'studio-1'
    assert updated['updated_by'] == 'Owner'
    assert updated_ptag['ptag_source'] == 'ptag body'
    assert reset_ptag['ptag_reset'] is True
    assert refreshed['status'] == 'refreshed'
    assert restored['status'] == 'restored'
    assert reviewed['publish_readiness']['status'] == 'ready'
    assert published['publish_artifact']['role_id'] == 'FINANCE_DIRECTOR'
    assert reloads == ['hierarchy', 'policy']
    assert sessions[0]['limit'] == 5
    assert inbox[0]['queue_lane'] == 'review'
    assert fetched_session['session_id'] == 'session-1'
    assert directory['entries'][0]['role_id'] == 'GOV'
    assert human_session['session_id'] == 'session-1'
    assert studio_session['session_id'] == 'session-2'
    assert [item[0] for item in dispatches] == [
        'role_private_studio.request.created',
        'role_private_studio.request.restored',
        'role_private_studio.request.reviewed',
        'role_private_studio.request.published',
        'human_ask.session.created',
        'human_ask.session.created',
        'human_ask.session.recorded_from_studio',
    ]



def test_action_runtime_accessors_and_model_provider_probe(monkeypatch) -> None:
    app = build_test_app()
    events = []

    monkeypatch.setattr(app.action_runtime, 'action_runtime_snapshot', lambda **kwargs: {'summary': kwargs, 'items': [{'action_id': 'ACT-1'}]})
    monkeypatch.setattr(app.action_runtime, 'get_action', lambda action_id: {'action_id': action_id})
    monkeypatch.setattr(app.action_runtime, 'create_and_execute_action', lambda payload, requested_by, case_snapshot=None: {'action_id': 'ACT-1', 'requested_by': requested_by, 'case_id': (case_snapshot or {}).get('case_id')})
    monkeypatch.setattr(app.action_runtime, 'execute_action', lambda action_id, requested_by, case_snapshot=None: {'action_id': action_id, 'requested_by': requested_by, 'case_id': (case_snapshot or {}).get('case_id')})
    monkeypatch.setattr(app.model_provider_registry, 'probe', lambda provider_id=None: {'failed_providers': 1, 'provider_id': provider_id})
    monkeypatch.setattr(app.engine.audit_logger, 'record_event', lambda **kwargs: events.append(kwargs))
    monkeypatch.setattr(app, '_dispatch_integration_event', lambda event_type, payload, **kwargs: {'event_type': event_type, 'payload': payload, **kwargs})
    monkeypatch.setattr(app, 'health', lambda: {'status': 'degraded'})

    snapshot = app.action_runtime_snapshot(status='running', action_type='draft_document', case_id='CASE-1', limit=5)
    action = app.get_action('ACT-1')
    created = app.create_action({'action_type': 'draft_document'}, requested_by='Owner', case_snapshot={'case_id': 'CASE-1'})
    executed = app.execute_action('ACT-1', requested_by='Owner', case_snapshot={'case_id': 'CASE-1'})
    probe = app.probe_model_providers('Owner', provider_id='provider-1')
    integration_test = app.trigger_integration_test_event('Owner', event_type='integration.test.manual')

    assert snapshot['summary']['case_id'] == 'CASE-1'
    assert action['action_id'] == 'ACT-1'
    assert created['case_id'] == 'CASE-1'
    assert executed['action_id'] == 'ACT-1'
    assert probe['provider_id'] == 'provider-1'
    assert integration_test['payload']['runtime_status'] == 'degraded'
    assert any(event['action'] == 'model_provider_probe' and event['outcome'] == 'partial' for event in events)



def test_workflow_proof_bundle_and_evidence_pack_keep_case_context(monkeypatch) -> None:
    app = build_test_app()
    audit_events = []
    dispatches = []

    monkeypatch.setattr(app, 'get_workflow_state', lambda workflow_id: {'workflow_id': workflow_id, 'request_id': 'REQ-1'})
    monkeypatch.setattr(
        app,
        'list_runtime_recovery_records',
        lambda limit=400: [
            {'request_id': 'REQ-1', 'metadata': {}},
            {'request_id': 'REQ-2', 'resumed_request_id': 'REQ-1', 'metadata': {'execution_plan': {'plan_id': 'WF-1'}}},
        ],
    )
    monkeypatch.setattr(app, 'list_runtime_dead_letters', lambda limit=400: [{'request_id': 'REQ-2'}])
    monkeypatch.setattr(app.human_ask.store, 'list_sessions', lambda: [_SessionEnvelope({'metadata': {'origin_request_id': 'REQ-1'}}), _SessionEnvelope({'metadata': {'execution_plan': {'plan_id': 'WF-1'}}})])
    monkeypatch.setattr(app, 'list_audit', lambda limit=400: [{'action': 'workflow_proof_export', 'request_id': 'REQ-1'}])
    monkeypatch.setattr(app, 'operational_readiness', lambda limit=50, health=None: {'status': 'attention_required'})
    monkeypatch.setattr(app, 'health', lambda: {'status': 'ok'})
    monkeypatch.setattr(
        app.evidence_builder,
        'create_workflow_proof_bundle',
        lambda **kwargs: {'bundle_id': 'bundle-1', 'export_path': '/tmp/bundle-1', 'artifact_total': 3},
    )
    monkeypatch.setattr(app.engine.audit_logger, 'record_event', lambda **kwargs: audit_events.append(kwargs))
    monkeypatch.setattr(app, 'list_roles', lambda: [{'role_id': 'GOV', 'status': 'ready'}])
    monkeypatch.setattr(app, '_base_health', lambda roles=None: {'status': 'ok'})
    monkeypatch.setattr(app.access_control, 'health', lambda: {'status': 'ok'})
    monkeypatch.setattr(app.evidence_builder, 'summary', lambda: {'exports_total': 1})
    monkeypatch.setattr(app.compliance_registry, 'build_snapshot', lambda **kwargs: {'summary': {'frameworks_total': 2}})
    monkeypatch.setattr(
        app.evidence_builder,
        'create_pack',
        lambda **kwargs: {'pack_id': 'pack-1', 'export_path': '/tmp/pack-1', 'artifact_total': 5, 'file_total': 2},
    )
    monkeypatch.setattr(app, 'retention_report', lambda: {'status': 'ok'})
    monkeypatch.setattr(app, 'runtime_backup_summary', lambda: {'status': 'ready'})
    monkeypatch.setattr(app, 'list_runtime_backups', lambda limit=10: [{'backup_id': 'backup-1'}])
    monkeypatch.setattr(app, 'studio_snapshot', lambda limit=20: {'summary': {'requests_total': 1}})
    monkeypatch.setattr(
        app,
        '_dispatch_integration_event',
        lambda event_type, payload, **kwargs: dispatches.append((event_type, payload, kwargs)) or {'failed_total': 0, 'targets_matched': 1},
    )

    workflow_bundle = app.create_workflow_proof_bundle('WF-1', requested_by='Owner')
    with patch('sa_nom_governance.api.api_engine.build_go_live_readiness', return_value={'status': 'blocked'}):
        evidence_pack = app.create_evidence_pack('Owner')

    assert workflow_bundle['bundle_id'] == 'bundle-1'
    assert evidence_pack['pack_id'] == 'pack-1'
    assert any(event['action'] == 'workflow_proof_export' for event in audit_events)
    assert any(event['action'] == 'evidence_export' for event in audit_events)
    assert dispatches[0][0] == 'governance.evidence.exported'



def test_workflow_matching_helpers_cover_request_and_plan_links() -> None:
    app = build_test_app()

    assert app._workflow_matches_runtime_record('WF-1', 'REQ-1', {'request_id': 'REQ-1'}) is True
    assert app._workflow_matches_runtime_record('WF-1', 'REQ-1', {'metadata': {'execution_plan': {'plan_id': 'WF-1'}}}) is True
    assert app._workflow_matches_runtime_record('WF-1', 'REQ-1', {'metadata': []}) is False

    assert app._workflow_matches_human_session('WF-1', 'REQ-1', {'metadata': {'origin_request_id': 'REQ-1'}}) is True
    assert app._workflow_matches_human_session('WF-1', 'REQ-1', {'metadata': {'execution_plan': {'plan_id': 'WF-1'}}}) is True
    assert app._workflow_matches_human_session('WF-1', 'REQ-1', {'metadata': {'human_decision_inbox': {'execution_plan': {'plan_id': 'WF-1'}}}}) is True
    assert app._workflow_matches_human_session('WF-1', 'REQ-1', {'metadata': []}) is False

    assert app._workflow_matches_audit_entry('WF-1', 'REQ-1', {'workflow_id': 'WF-1'}) is True
    assert app._workflow_matches_audit_entry('WF-1', 'REQ-1', {'request_id': 'REQ-1'}) is True
    assert app._workflow_matches_audit_entry('WF-1', 'REQ-1', {'request_id': 'REQ-2'}) is False
