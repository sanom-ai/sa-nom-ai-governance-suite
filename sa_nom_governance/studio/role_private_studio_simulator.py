import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from sa_nom_governance.core.core_engine import CoreEngine
from sa_nom_governance.utils.registry import RoleRegistry
from sa_nom_governance.ptag.role_loader import RoleLoader
from sa_nom_governance.studio.role_private_studio_models import RolePrivateStudioRequest, SimulationReport, SimulationScenarioResult, utc_now
from sa_nom_governance.compliance.trusted_registry import write_trusted_registry_files


class RolePrivateStudioSimulator:
    def __init__(self, signing_key: str) -> None:
        self.signing_key = signing_key or "role-private-studio-sim-key"

    def simulate(self, request: RolePrivateStudioRequest) -> SimulationReport:
        scenarios = self._build_scenarios(request)
        if not request.generated_ptag or request.validation_report is None or not request.validation_report.syntax_passed:
            return SimulationReport(
                report_id=f"sr_{uuid4().hex[:12]}",
                generated_at=utc_now(),
                status="blocked",
                scenario_results=[
                    SimulationScenarioResult(
                        scenario_id="simulation_blocked",
                        category="validation_blocked",
                        expected_outcome="simulation_ready",
                        observed_outcome="blocked",
                        passed=False,
                        reason="Simulation skipped because the PTAG draft did not pass syntax validation.",
                        notes=["Fix validation blockers before running Role Private Studio simulation."],
                    )
                ],
            )

        with self._workspace_temp_dir() as temp_path:
            role_id = request.normalized_spec.role_id if request.normalized_spec else "NEW_ROLE"
            (temp_path / f"{role_id}.ptn").write_text(request.generated_ptag, encoding="utf-8")
            manifest_path = temp_path / "trusted_registry_manifest.json"
            cache_path = temp_path / "trusted_registry_cache.json"
            write_trusted_registry_files(
                roles_dir=temp_path,
                manifest_path=manifest_path,
                cache_path=cache_path,
                role_ids=[role_id],
                signing_key=self.signing_key,
                key_id="ROLE_PRIVATE_STUDIO_SIM",
                signed_by="ROLE_PRIVATE_STUDIO",
            )
            registry = RoleRegistry(
                temp_path,
                manifest_path=manifest_path,
                cache_path=cache_path,
                signing_key=self.signing_key,
                signature_required=True,
            )
            engine = CoreEngine(
                RoleLoader(registry),
                audit_log_path=temp_path / "runtime_audit_log.jsonl",
                override_store_path=temp_path / "runtime_override_store.json",
                lock_store_path=temp_path / "runtime_lock_store.json",
                consistency_store_path=temp_path / "runtime_consistency_store.json",
            )
            results = [self._execute(engine, role_id, scenario) for scenario in scenarios]

        status = "passed" if results and all(item.passed for item in results) else "failed"
        return SimulationReport(report_id=f"sr_{uuid4().hex[:12]}", generated_at=utc_now(), status=status, scenario_results=results)

    @contextmanager
    def _workspace_temp_dir(self):
        source_base = Path(__file__).resolve().parents[2]
        runtime_tmp = source_base / "_runtime" / "tmp_studio_sim"
        runtime_tmp.mkdir(parents=True, exist_ok=True)
        temp_path = runtime_tmp / f"studio_sim_{uuid4().hex[:12]}"
        temp_path.mkdir(parents=True, exist_ok=True)
        try:
            yield temp_path
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)

    def _build_scenarios(self, request: RolePrivateStudioRequest) -> list[dict[str, object]]:
        spec = request.normalized_spec
        if spec is None:
            return []
        allowed_actions = list(spec.allowed_actions)
        safe_actions = [action for action in allowed_actions if action not in spec.wait_human_actions]
        primary_action = safe_actions[0] if safe_actions else (allowed_actions[0] if allowed_actions else "review_request")
        wait_action = spec.wait_human_actions[0] if spec.wait_human_actions else primary_action
        forbidden_action = spec.forbidden_actions[0] if spec.forbidden_actions else "unauthorized_action"
        resource = spec.handled_resources[0] if spec.handled_resources else "general_resource"

        def payload(resource_id: str, amount: int, topic: str = "standard_review") -> dict[str, object]:
            return {"resource": resource, "resource_id": resource_id, "amount": amount, "topic": topic}

        high_risk_expected = "waiting_human" if primary_action in spec.wait_human_actions else "escalated"
        return [
            {"scenario_id": "scenario_normal", "category": "normal_request_path", "requester": "studio_operator", "action": primary_action, "payload": payload("normal-001", 100000), "expected_outcome": "approved"},
            {"scenario_id": "scenario_denied", "category": "denied_request_path", "requester": "studio_operator", "action": forbidden_action, "payload": payload("denied-001", 100000), "expected_outcome": "rejected"},
            {"scenario_id": "scenario_escalated", "category": "escalated_request_path", "requester": "studio_operator", "action": primary_action, "payload": payload("risk-001", 9000000), "expected_outcome": "escalated"},
            {"scenario_id": "scenario_waiting_human", "category": "waiting_human_path", "requester": "studio_operator", "action": wait_action, "payload": payload("review-001", 250000), "expected_outcome": "waiting_human" if spec.wait_human_actions else "not_applicable", "skip_reason": None if spec.wait_human_actions else "No explicit wait-human action was generated for this role draft."},
            {"scenario_id": "scenario_conflict", "category": "resource_conflict_path", "requester": "studio_operator", "action": wait_action, "payload": payload("conflict-001", 250000), "expected_outcome": "conflicted"},
            {"scenario_id": "scenario_high_risk", "category": "high_risk_payload_path", "requester": "studio_operator", "action": primary_action, "payload": payload("high-risk-001", 12000000), "expected_outcome": high_risk_expected},
        ]

    def _execute(self, engine: CoreEngine, role_id: str, scenario: dict[str, object]) -> SimulationScenarioResult:
        if scenario.get("skip_reason"):
            return SimulationScenarioResult(
                scenario_id=str(scenario["scenario_id"]),
                category=str(scenario["category"]),
                expected_outcome=str(scenario["expected_outcome"]),
                observed_outcome="not_applicable",
                passed=True,
                reason=str(scenario["skip_reason"]),
                notes=[str(scenario["skip_reason"])],
                input_request={"requester": scenario["requester"], "action": scenario["action"], "payload": scenario["payload"]},
            )
        if scenario["category"] == "resource_conflict_path":
            return self._execute_conflict(engine, role_id, scenario)
        outcome, reason, policy_basis, failed_conditions, notes = self._run_request(engine, role_id, scenario, sequence=1)
        if outcome == "waiting_human":
            self._cleanup_overrides(engine)
        return SimulationScenarioResult(
            scenario_id=str(scenario["scenario_id"]),
            category=str(scenario["category"]),
            expected_outcome=str(scenario["expected_outcome"]),
            observed_outcome=outcome,
            passed=outcome == scenario["expected_outcome"],
            policy_basis=policy_basis,
            reason=reason,
            failed_conditions=failed_conditions,
            notes=notes,
            input_request={"requester": scenario["requester"], "action": scenario["action"], "payload": scenario["payload"]},
        )

    def _execute_conflict(self, engine: CoreEngine, role_id: str, scenario: dict[str, object]) -> SimulationScenarioResult:
        first_outcome, _, _, _, notes = self._run_request(engine, role_id, scenario, sequence=1)
        if first_outcome != "waiting_human":
            context = engine.dispatcher.dispatch(
                requester="studio_lock_seed",
                action=str(scenario["action"]),
                role_id=role_id,
                payload=dict(scenario["payload"]),
                metadata=self._seed_metadata(scenario),
            )
            engine.request_consistency.prepare(context)
            engine.lock_manager.acquire(context)
            engine.lock_manager.mark_waiting(context.request_id)
            manual_request_id = context.request_id
        else:
            manual_request_id = None
            context = None
        second_outcome, second_reason, second_basis, second_failed, second_notes = self._run_request(engine, role_id, scenario, sequence=2)
        if manual_request_id is not None and context is not None:
            engine.lock_manager.release_by_request(manual_request_id)
            engine.request_consistency.abort(context)
        self._cleanup_overrides(engine)
        return SimulationScenarioResult(
            scenario_id=str(scenario["scenario_id"]),
            category=str(scenario["category"]),
            expected_outcome="conflicted",
            observed_outcome=second_outcome,
            passed=second_outcome == "conflicted",
            policy_basis=second_basis,
            reason=second_reason,
            failed_conditions=second_failed,
            notes=[*notes, *second_notes],
            input_request={"requester": scenario["requester"], "action": scenario["action"], "payload": scenario["payload"]},
        )

    def _run_request(self, engine: CoreEngine, role_id: str, scenario: dict[str, object], sequence: int):
        try:
            result = engine.process(
                requester=str(scenario["requester"]),
                role_id=role_id,
                action=str(scenario["action"]),
                payload=dict(scenario["payload"]),
                metadata=self._metadata(scenario, sequence),
            )
            trace = result.decision_trace or {}
            return (result.outcome, result.reason, result.policy_basis, trace.get("failed_conditions", []), trace.get("notes", []))
        except PermissionError as error:
            return ("rejected", str(error), "authority_guard", [], ["Authority guard rejected the simulated request."])
        except Exception as error:
            return ("error", str(error), "simulation_error", [], ["Simulation raised an unexpected runtime error."])

    def _metadata(self, scenario: dict[str, object], sequence: int) -> dict[str, object]:
        return {
            "idempotency_key": f"{scenario['scenario_id']}:{sequence}",
            "event_stream": f"role_private_studio:{scenario['scenario_id']}",
            "event_sequence": sequence,
        }

    def _seed_metadata(self, scenario: dict[str, object]) -> dict[str, object]:
        return {
            "idempotency_key": f"{scenario['scenario_id']}:seed",
            "event_stream": f"role_private_studio_seed:{scenario['scenario_id']}",
            "event_sequence": 1,
        }

    def _cleanup_overrides(self, engine: CoreEngine) -> None:
        for item in engine.list_override_requests(status="pending"):
            engine.review_override(item["request_id"], resolved_by="ROLE_PRIVATE_STUDIO_SIM", decision="veto", note="Simulation cleanup.")
