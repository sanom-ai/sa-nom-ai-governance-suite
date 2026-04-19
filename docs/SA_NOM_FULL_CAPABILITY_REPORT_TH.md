# SA-NOM Full Capability Report (TH)

อัปเดตล่าสุด: 2026-04-20  
ฐานอ้างอิง: โค้ดใน repository ปัจจุบัน (`v0.7.16`), โมดูลหลัก 16 โมดูล, test files 63 ไฟล์, ชุดทดสอบล่าสุด `526 passed`

## 1. ขอบเขตและวิธีอ่านรายงาน

รายงานนี้สรุปความสามารถของระบบ SA-NOM แบบครบทั้งระดับหลักและย่อย โดยจัดจากหลักฐาน 4 ชั้น:

- โค้ดหลักใน `sa_nom_governance/*`
- สคริปต์ปฏิบัติการใน `scripts/*`
- ตัวอย่างใช้งานใน `examples/*`
- เอกสารระบบใน `docs/*`

สถานะในรายงาน:

- `✅ ใช้งานได้จริง`: มี implementation ชัดในโค้ด และมี test หรือ flow รองรับ
- `🧪 พร้อมทดสอบ/เดโม`: มี implementation และมี smoke/demo path
- `📘 ขอบเขตเชิงสถาปัตยกรรม/นโยบาย`: มีแบบและกติกาในเอกสารเพื่อกำกับการใช้งาน

## 2. ความสามารถระดับระบบ (System-Level Capabilities)

### 2.1 Command Surface และโครงหน้าใช้งาน

`✅ ใช้งานได้จริง`

- มี command surface สำหรับงานประจำวัน: `Home`, `Work Inbox`, `Cases`, `Documents`, `AI Actions`
- มีโหมด Governance แยกออกจากงานประจำ เพื่อแยก “ใช้งานงาน” กับ “ตั้งค่าควบคุมระบบ”
- รองรับ operator summary เพื่อดู posture, readiness, alert, integration และสถานะ runtime

อ้างอิง: `sa_nom_governance/dashboard/*`, `docs/SA_NOM_COMMAND_SURFACE_DOCTRINE.md`, `docs/CONTROL_ROOM_INFORMATION_ARCHITECTURE.md`

### 2.2 Governance > Control Room

`✅ ใช้งานได้จริง` + `📘 IA ชัด`

- รวมงาน setup, trust, recovery, integration, provider, retention, evidence ในพื้นที่ควบคุมเดียว
- รองรับแนวทาง “AI ทำงาน, Human กำกับที่จุดสำคัญ” ด้วยชั้นควบคุมแบบ role-based
- มีหมวดหลักสำหรับ:
  - Setup & Onboarding
  - AI Workforce & Roles
  - Structural Risk & Alignment
  - Trust & Evidence
  - Runtime & Recovery
  - Integrations & Providers
  - Access & Security
  - Master Data & Routing

อ้างอิง: `docs/CONTROL_ROOM_INFORMATION_ARCHITECTURE.md`

### 2.3 End-to-End Governed Runtime

`✅ ใช้งานได้จริง`

- รับ request เข้าระบบภายใต้ role/policy
- ประเมินสิทธิ์และขอบเขตอำนาจก่อน action
- รัน workflow ต่อเนื่องพร้อม state, lock, override, recovery
- เก็บ audit/evidence ตลอดสายงาน
- ส่งต่อเหตุการณ์ออก integration ได้แบบ governed

อ้างอิง: `sa_nom_governance/core/*`, `sa_nom_governance/api/api_engine.py`, `sa_nom_governance/integrations/*`

## 3. Capability Map ตามโมดูลหลัก 16 โมดูล

## 3.1 `core` (หัวใจ orchestration)

`✅ ใช้งานได้จริง`

- `authority_policy_engine.py`: policy decision สำหรับ allow/deny/human-required
- `core_engine.py`: orchestration หลักของ request lifecycle
- `decision_engine.py` + `decision_models.py`: decision flow และโมเดลผลลัพธ์
- `role_activation_router.py`: route การทำงานตาม role และ context
- `trigger_action_registry.py`: registry สำหรับ trigger/action
- `state_flow_engine.py`: state transition engine
- `workflow_state_store.py`: เก็บและเรียก workflow states
- `runtime_recovery_store.py`: เก็บสถานะ recovery/dead-letter ที่จุด runtime
- `lock_manager.py`: จัดการ lock/ชนกันของงาน
- `request_consistency.py`: consistency guard ของ request
- `hierarchy_registry.py`: โครง hierarchy ของ role/authority
- `role_transition_policy.py`: policy การเปลี่ยน role
- `policy_runtime_contracts.py`: runtime contract กำกับโครง policy
- `risk_scorer.py`, `result_builder.py`, `dispatcher.py`, `execution_context.py`: support layer ของ execution

## 3.2 `ptag` (governance language + structural intelligence)

`✅ ใช้งานได้จริง`

- `ptag_parser.py`, `ptag_ast.py`, `ptag_validator.py`, `ptag_semantic.py`: parser/AST/semantic validation ครบวงจร
- `role_compiler.py`, `role_loader.py`: compile/load role pack เข้าระบบ
- `pt_oss_engine.py`, `pt_oss_models.py`: PT-OSS structural intelligence เพื่อประเมิน readiness/fragility/asymmetry

## 3.3 `studio` (Role Private Studio)

`✅ ใช้งานได้จริง`

- สร้างคำขอ role จาก input แบบเอกสารปกติ
- แปลง/เก็บ PTAG และ versioning
- diff ระหว่าง revision
- restore revision
- review decision
- publish flow
- validator และ simulator สำหรับ quality gate ก่อน publish

ไฟล์หลัก: `role_private_studio_service.py`, `role_private_studio_models.py`, `role_private_studio_diff.py`, `role_private_studio_validator.py`, `role_private_studio_simulator.py`

## 3.4 `human_ask` (report/meeting/human gate)

`✅ ใช้งานได้จริง`

- สร้างและจัดการ Human Ask session
- สรุปผลพร้อมขอบเขต (scope) และ presentation layer
- ทำงานร่วมกับ Human Decision Inbox
- เชื่อมกับ Studio record ได้

ไฟล์หลัก: `human_ask_service.py`, `human_ask_models.py`, `human_ask_scope.py`, `human_ask_presenter.py`

## 3.5 `actions` (governed action runtime)

`✅ ใช้งานได้จริง`

- create/list/get/execute actions
- action store + model สำหรับ persistence และ governance metadata

ไฟล์หลัก: `action_service.py`, `action_models.py`, `action_store.py`

## 3.6 `documents` (governed document runtime)

`✅ ใช้งานได้จริง`

- document model/service/store สำหรับงานเอกสารภายใต้ governance
- ใช้คู่กับกติกา authority/approval/retention ใน docs layer

ไฟล์หลัก: `document_service.py`, `document_models.py`, `document_store.py`

## 3.7 `audit` (audit chain + evidence)

`✅ ใช้งานได้จริง`

- audit logger พร้อม integrity check
- reseal audit chain
- evidence pack builder
- event contract schema สำหรับ traceability

ไฟล์หลัก: `audit_logger.py`, `audit_integrity.py`, `audit_reseal.py`, `auditor_evidence_pack.py`, `event_contract.py`

## 3.8 `compliance` (retention + trust registry + framework mapping)

`✅ ใช้งานได้จริง`

- compliance framework registry snapshot
- retention plan/report/enforcement
- trusted registry health และ refresh flow

ไฟล์หลัก: `compliance_registry.py`, `retention_manager.py`, `trusted_registry.py`, `trusted_registry_refresh.py`

## 3.9 `guards` (access/session/override authority)

`✅ ใช้งานได้จริง`

- access control
- access profile config/hash/rotate
- bootstrap access profiles
- session manager
- human override
- authority guard + ethics guard

ไฟล์หลัก: `access_control.py`, `session_manager.py`, `human_override.py`, `authority_guard.py`, `ethics_guard.py`, `bootstrap_access_profiles.py`

## 3.10 `integrations` (outbound + provider + dispatch contract)

`✅ ใช้งานได้จริง`

- integration registry
- outbound webhook dispatcher (retry/dead-letter policy)
- coordination layer
- provider registry
- dispatch contract สำหรับ provider lane (`dispatch_v1`)

ไฟล์หลัก: `integration_registry.py`, `webhook_dispatcher.py`, `coordination.py`, `model_provider_registry.py`, `provider_dispatch_contract.py`

## 3.11 `alignment` (Global Harmony / constitution / cultural alignment)

`✅ ใช้งานได้จริง`

- constitution ingestion + registry
- alignment runtime models/service
- cultural alignment evaluator
- evaluation models

ไฟล์หลัก: `alignment_service.py`, `constitution_ingestion.py`, `constitution_registry.py`, `cultural_alignment_evaluator.py`

## 3.12 `master_data` (people/team/routing data foundation)

`✅ ใช้งานได้จริง`

- master data service สำหรับ governance routing และ directory foundation

ไฟล์หลัก: `master_data_service.py`

## 3.13 `dashboard` (operator/control surface backend)

`✅ ใช้งานได้จริง`

- dashboard data aggregation layer
- dashboard server
- operator posture surfaces (runtime/trust/evidence/provider/integration)

ไฟล์หลัก: `dashboard_data.py`, `dashboard_server.py`

## 3.14 `deployment` (runbook/verification/recovery tooling)

`✅ ใช้งานได้จริง` + `🧪 พร้อมเดโม`

- deployment profile
- go-live readiness
- guided smoke test
- nontechnical demo path
- ollama demo environment
- provider demo/smoke flows
- private server smoke test
- runtime backup manager
- runtime performance baseline
- release preflight
- usability proof bundle

ไฟล์หลัก: `sa_nom_governance/deployment/*`

## 3.15 `api` (application service facade)

`✅ ใช้งานได้จริง`

- application assembly และ service methods สำหรับ orchestration, health, governance operations

ไฟล์หลัก: `api_engine.py`, `api_schemas.py`, `main.py`

## 3.16 `utils` (config/owner/persistence/registry)

`✅ ใช้งานได้จริง`

- app config
- owner identity + owner registration
- persistence abstraction
- role registry utilities

ไฟล์หลัก: `config.py`, `owner_identity.py`, `owner_registration.py`, `persistence.py`, `registry.py`

## 4. รายการ Service Operations ที่เรียกใช้งานได้ (EngineApplication)

จำนวนเมธอด service แบบ public: 59 รายการ

### 4.1 Runtime, Workflow, Recovery

- `health`
- `operational_readiness`
- `request`
- `list_workflow_states`
- `get_workflow_state`
- `list_runtime_recovery_records`
- `list_runtime_dead_letters`
- `resume_runtime_recovery`

### 4.2 Override, Locks, Sessions

- `list_overrides`
- `get_override`
- `approve_override`
- `veto_override`
- `list_locks`
- `list_sessions`
- `revoke_session`

### 4.3 Audit, Evidence, Retention, Backups

- `list_audit`
- `list_runtime_evidence`
- `audit_integrity`
- `reseal_audit_log`
- `list_runtime_backups`
- `runtime_backup_summary`
- `create_runtime_backup`
- `retention_report`
- `retention_plan`
- `enforce_retention`
- `list_evidence_packs`
- `list_workflow_proof_bundles`
- `evidence_pack_summary`
- `create_workflow_proof_bundle`
- `create_evidence_pack`

### 4.4 Role Library และ Role Private Studio

- `list_roles`
- `studio_snapshot`
- `list_studio_requests`
- `get_studio_request`
- `create_studio_request`
- `update_studio_request`
- `update_studio_request_ptag`
- `reset_studio_request_ptag`
- `refresh_studio_request`
- `restore_studio_request_revision`
- `review_studio_request`
- `publish_studio_request`

### 4.5 Human Ask และ Decision Inbox

- `human_ask_snapshot`
- `list_human_ask_sessions`
- `list_human_decision_inbox`
- `get_human_ask_session`
- `create_human_ask_session`
- `create_human_ask_studio_record`
- `list_callable_directory`

### 4.6 Action Runtime

- `action_runtime_snapshot`
- `list_actions`
- `get_action`
- `create_action`
- `execute_action`

### 4.7 Compliance, Integrations, Providers

- `compliance_snapshot`
- `integration_snapshot`
- `model_provider_snapshot`
- `probe_model_providers`
- `trigger_integration_test_event`

## 5. Integration และ Model Provider ที่รองรับ

## 5.1 Outbound Integration Targets (preset + custom)

`✅ ใช้งานได้จริง`

- Internal ledger
- SIEM bridge
- Slack bridge
- Teams bridge
- Jira Service Desk bridge
- ServiceNow bridge
- Custom webhook bridge

ความสามารถย่อย:

- event subscription
- notification channel mapping
- retry policy
- timeout/backoff
- signing policy (`none` / `hmac_sha256`)
- dead-letter posture

อ้างอิง: `resources/config/integration_targets.json`, `sa_nom_governance/integrations/*`

## 5.2 Provider Lanes

`✅ ใช้งานได้จริง` + `🧪 พร้อมเดโม`

- `ollama` (private-first default lane)
- `openai`
- `anthropic` (Claude)

พร้อม contract/examples สำหรับ dispatch:

- `examples/dispatch_v1_openai.example.json`
- `examples/dispatch_v1_claude.example.json`
- `examples/dispatch_v1_gemini.example.json`
- `resources/config/dispatch_v1_request.schema.json`

## 6. Capability ด้าน Setup, Deploy, Operate (Scripts)

สคริปต์ปฏิบัติการที่มีให้ใช้งาน:

- `register_owner.py`
- `bootstrap_access_profiles.py`
- `guided_smoke_test.py`
- `quick_start_path.py`
- `run_private_server.py`
- `private_server_smoke_test.py`
- `provider_smoke_test.py`
- `provider_demo_flow.py`
- `dashboard_server.py`
- `runtime_backup.py`
- `runtime_performance_baseline.py`
- `public_release_preflight.py`
- `trusted_registry_refresh.py`
- `usability_proof_bundle.py`
- `audit_reseal.py`
- coverage/check scripts (`check_core_coverage.py`, `check_runtime_governance_coverage.py`, `check_enterprise_runtime_coverage.py`)

## 7. Capability ด้านทรัพยากร Governance ที่มากับระบบ

## 7.1 Role policy files ที่มากับ baseline

- `CHANGE_CONTROL.ptn`
- `core_terms.ptn`
- `GOV.ptn`
- `LEGAL.ptn`
- `OPS_REVIEW.ptn`
- `VENDOR_RISK.ptn`

## 7.2 Config artifacts สำคัญ

- `compliance_frameworks.json`
- `role_transition_matrix.json`
- `trusted_registry_manifest.json`
- `integration_targets.json`
- `dispatch_v1_request.schema.json`

## 7.3 Example assets พร้อมใช้

- Provider env examples: OpenAI / Claude / Ollama
- Owner/access bootstrap examples
- Runtime startup smoke example
- Role Private Studio example
- Role packs examples 14 ชุด
- Scenario examples 10 ชุด
- Helm production values example

## 8. Capability เชิงโดเมนงาน (Role Packs + Scenarios)

## 8.1 Role pack examples (14)

- accounting close exception
- banking treasury control
- delivery readiness
- document governance
- external audit response
- finance budget variance
- HR policy
- legal review
- new model launch readiness
- production line exception
- purchasing supplier risk
- quality audit readiness
- regulator response
- warehouse material shortage

## 8.2 Scenario examples (10)

- delivery readiness
- external audit response
- finance budget variance
- HR policy
- legal review
- new model launch readiness
- production line exception
- purchasing supplier risk
- quality audit readiness
- regulator response

## 9. Capability ด้านคุณภาพและความเชื่อมั่น (Quality/Confidence)

`✅ ใช้งานได้จริง`

- ชุดทดสอบอัตโนมัติ 63 test files
- ผลรันล่าสุด: `526 passed`
- total coverage ล่าสุด: `91.05%`
- runtime governance coverage ล่าสุด: `91.25%`
- มี coverage gate scripts แยกตาม core/runtime/enterprise runtime
- มี smoke/preflight/usability proof paths สำหรับก่อนขึ้นใช้งานจริง

อ้างอิง: `_support/tests/*`, `scripts/check_*_coverage.py`, `scripts/public_release_preflight.py`

## 10. สรุปความสามารถ “หลัก + ย่อย” ในประโยคเดียว

SA-NOM เป็นระบบ AI Governance Runtime ที่ทำงานครบตั้งแต่การนิยาม role/policy (PTAG), ประเมินโครงสร้างความเสี่ยง (PT-OSS), orchestration จริงใน runtime, human-gated control points, audit/evidence/retention, integration outbound, provider dispatch, dashboard/control room, ไปจนถึง deployment/backup/recovery และ quality gates สำหรับใช้งานจริงในองค์กรแบบ private-first.

## 11. ขอบเขตที่ต้องทราบเพื่อใช้งานจริงให้ถูกต้อง

- ความสามารถจำนวนมาก “พร้อมใช้งานทันที” แต่บางส่วนต้องมี setup ก่อน เช่น owner registration, access profiles, provider credentials, integration endpoints
- บางเอกสารใน `docs/` เป็นกรอบการใช้งานเชิง governance/operating blueprint เพื่อกำกับการออกแบบองค์กร ไม่ใช่หมายความว่าทุกส่วนเป็น automation แบบ full depth แล้วทั้งหมด
- แนวทางที่ถูกต้องคือใช้งานแบบ `structure-first`: ให้ AI รันงานในขอบเขตที่อนุมัติ และให้คนตัดสินใจเฉพาะจุด authority/escalation/override ที่ระบบกำหนด

