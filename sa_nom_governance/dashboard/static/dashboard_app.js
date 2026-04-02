import { buildHumanAskPayload, handleHumanAskAction, renderHumanAsk } from './dashboard_human_ask.js?v=0.7.3-ui15';

import { buildHumanAskOutcomeMessage } from './dashboard_human_ask.js?v=0.7.3-ui15';

const state = {
  view: 'overview',
  snapshot: null,
  session: null,
  token: window.localStorage.getItem('sanom_api_token') || '',
  sessionToken: window.localStorage.getItem('sanom_session_token') || '',
  authRequired: false,
  lastError: '',
  studioEditingRequestId: null,
  studioEditorDraft: null,
  studioGovernanceRequestId: null,
  studioGovernanceNotes: {},
  studioRevisionSelections: {},
  studioPtagDrafts: {},
  studioPtagHistory: {},
  actionContext: null,
};

const root = document.getElementById('dashboard-root');
const navList = document.getElementById('nav-list');
const viewTitle = document.getElementById('view-title');
const viewDescription = document.getElementById('view-description');
const environmentLabel = document.getElementById('environment-label');
const generatedAt = document.getElementById('generated-at');
const refreshButton = document.getElementById('refresh-button');
const logoutButton = document.getElementById('logout-button');
const sessionLabel = document.getElementById('session-label');
const sidebarViewTitle = document.getElementById('sidebar-view-title');
const sidebarViewDescription = document.getElementById('sidebar-view-description');
const sidebarOperatorLabel = document.getElementById('sidebar-operator-label');
const sidebarRuntimeLabel = document.getElementById('sidebar-runtime-label');
const sidebarGeneratedLabel = document.getElementById('sidebar-generated-label');
const topbarFocusLabel = document.getElementById('topbar-focus-label');
const topbarRuntimeLabel = document.getElementById('topbar-runtime-label');

const VIEW_TITLES = {
  overview: 'Overview',
  requests: 'Requests',
  cases: 'Cases',
  overrides: 'Overrides',
  conflicts: 'Conflicts & Locks',
  audit: 'Audit Trail',
  studio: 'Role Private Studio',
  human_ask: 'Human Ask',
  sessions: 'Sessions',
  policies: 'Roles & Policies',
  health: 'Runtime Health',
};

const VIEW_DESCRIPTIONS = {
  overview: 'See governance, runtime, and readiness posture in one scan.',
  requests: 'Submit governed work and follow where it goes next.',
  cases: 'Follow one governed issue across requests, overrides, Human Ask, and audit proof.',
  overrides: 'Work only the decisions that crossed a human boundary.',
  conflicts: 'Inspect locks, contention, and safe retry posture.',
  audit: 'Review chain integrity, evidence, and trusted history.',
  studio: 'Create, review, and publish governed AI roles.',
  human_ask: 'Start governed report or meeting records from one place.',
  sessions: 'Monitor short-lived access, expiry, and revocation.',
  policies: 'Inspect active role packs and policy boundaries.',
  health: 'Check deployment, storage, integrations, and runtime posture.',
};

const DEV_LANES = {
  viewer: {
    token: 'sanom-viewer-token',
    view: 'overview',
    title: 'Viewer lane',
    summary: 'Inspect the dashboard, runtime health, and audit posture before you start changing anything.',
    followup: 'Start with Overview, then move to Health and Audit.',
  },
  operator: {
    token: 'sanom-operator-token',
    view: 'requests',
    title: 'Operator lane',
    summary: 'Submit governed requests, watch queue posture, and follow runtime handoff lanes.',
    followup: 'Start with Requests, then check Overrides if a human boundary is triggered.',
  },
  reviewer: {
    token: 'sanom-reviewer-token',
    view: 'overrides',
    title: 'Reviewer lane',
    summary: 'Work the human approval queue with rationale, veto discipline, and audit continuity.',
    followup: 'Start with Overrides, then confirm the result in Audit.',
  },
};

const VIEW_INTELLIGENCE = {
  overview: {
    eyebrow: 'Executive Radar',
    title: 'Stewardship posture across the Director',
    narrative: 'Use this page first when you need the fastest read on whether the Director is calm, guarded, or blocked.',
    emphasis: 'executive posture',
  },
  requests: {
    eyebrow: 'Runtime Intake',
    title: 'Governed flow through active demand',
    narrative: 'Use this page to submit work and follow the governed intake path.',
    emphasis: 'flow control',
  },
  cases: {
    eyebrow: 'Case Backbone',
    title: 'One governed issue, one readable operating story',
    narrative: 'Use this page when you need the linked request, override, Human Ask, and audit trail in one place.',
    emphasis: 'end-to-end trace',
  },
  overrides: {
    eyebrow: 'Boundary Changes',
    title: 'Human intervention only where autonomy ended',
    narrative: 'Use this page when automation stopped and a real human decision is required.',
    emphasis: 'human boundary',
  },
  conflicts: {
    eyebrow: 'Contention Map',
    title: 'Where safe execution is under pressure',
    narrative: 'Use this page when requests stall behind locks, ordering, or shared resource pressure.',
    emphasis: 'contention pressure',
  },
  audit: {
    eyebrow: 'Evidence Ledger',
    title: 'Immutable history with trust posture visible',
    narrative: 'Use this page when you need the trusted record of what happened and why.',
    emphasis: 'integrity chain',
  },
  studio: {
    eyebrow: 'Hat Factory',
    title: 'Role creation with structural and governance discipline',
    narrative: 'Use this page when a role needs drafting, review, simulation, or publication.',
    emphasis: 'publication lane',
  },
  human_ask: {
    eyebrow: 'Record Surface',
    title: 'Human request, AI report, governed record',
    narrative: 'Use this page when one human needs a governed report or a multi-hat meeting record.',
    emphasis: 'record discipline',
  },
  sessions: {
    eyebrow: 'Access Discipline',
    title: 'Short-lived runtime identity under control',
    narrative: 'Use this page when access posture, expiry, or revocation needs review.',
    emphasis: 'session control',
  },
  policies: {
    eyebrow: 'PTAG Library',
    title: 'Trusted hats and their authority graph',
    narrative: 'Use this page when authority, safety ownership, or manifest trust needs inspection.',
    emphasis: 'policy library',
  },
  health: {
    eyebrow: 'Production Posture',
    title: 'Deployment readiness as an operating signal',
    narrative: 'Use this page when deployment posture, storage health, or integration readiness needs review.',
    emphasis: 'production hardening',
  },
};

const VIEW_USE_HINTS = {
  overview: { value: 'Start here', note: 'Open this first for the quickest full-system scan.', tone: 'accent' },
  requests: { value: 'Submit or trace work', note: 'Use this when you are creating a governed request or following its next lane.', tone: 'accent' },
  cases: { value: 'Trace the whole issue', note: 'Use this when one business issue spans requests, approvals, records, and evidence.', tone: 'accent' },
  overrides: { value: 'Resolve human decisions', note: 'Use this when the runtime paused and a human must approve or veto.', tone: 'warning' },
  conflicts: { value: 'Unblock stalled work', note: 'Use this when locks or contention stop safe execution.', tone: 'warning' },
  audit: { value: 'Prove what happened', note: 'Use this when you need evidence, reason, and chain integrity.', tone: 'accent' },
  studio: { value: 'Build or publish a role', note: 'Use this when a hat needs editing, simulation, review, or publication.', tone: 'accent' },
  human_ask: { value: 'Ask AI for a governed record', note: 'Use this for one-hat reports or multi-hat meeting records.', tone: 'accent' },
  sessions: { value: 'Check who still has access', note: 'Use this when you need issuance, expiry, or revocation status.', tone: 'accent' },
  policies: { value: 'Inspect role boundaries', note: 'Use this when authority, hierarchy, or safety ownership is unclear.', tone: 'accent' },
  health: { value: 'Check runtime readiness', note: 'Use this when deployment, storage, or integrations need operator attention.', tone: 'accent' },
};

const VIEW_PERMISSIONS = {
  overview: 'dashboard.read',
  requests: 'requests.read',
  cases: 'dashboard.read',
  overrides: 'overrides.read',
  conflicts: 'locks.read',
  audit: 'audit.read',
  studio: 'studio.read',
  human_ask: 'human_ask.read',
  sessions: 'sessions.read',
  policies: 'roles.read',
  health: 'health.read',
};

const ACTIONABLE_BUTTON_SELECTOR = [
  '[data-dev-lane]',
  '[data-view-jump]',
  '[data-case-scope-clear]',
  '[data-path-action]',
  '[data-studio-clear]',
  '[data-override-action]',
  '[data-session-revoke]',
  '[data-audit-action]',
  '[data-ops-action]',
  '[data-integration-action]',
  '[data-human-ask-action]',
  '[data-studio-governance-select]',
  '[data-studio-template-apply]',
  '[data-studio-panel-action]',
  '[data-studio-action]',
].join(', ');

navList.addEventListener('click', (event) => {
  const target = event.target.closest('.nav-item');
  if (!target) return;
  state.view = target.dataset.view;
  updateNav();
  render();
  scrollDashboardToTop();
});

refreshButton.addEventListener('click', () => withButtonBusy(refreshButton, () => loadDashboard(), 'Refreshing...'));
logoutButton.addEventListener('click', async () => {
  if (state.sessionToken) {
    try {
      await apiFetch('/api/session/logout', { method: 'POST' }, { useSession: true });
    } catch (error) {
      console.warn(error);
    }
  }
  state.token = '';
  state.sessionToken = '';
  state.snapshot = null;
  state.session = null;
  state.authRequired = true;
  state.studioEditingRequestId = null;
  state.studioEditorDraft = null;
  state.studioGovernanceRequestId = null;
  state.studioGovernanceNotes = {};
  state.studioRevisionSelections = {};
  state.studioPtagDrafts = {};
  state.studioPtagHistory = {};
  state.actionContext = null;
  window.localStorage.removeItem('sanom_api_token');
  window.localStorage.removeItem('sanom_session_token');
  render();
});

root.addEventListener('submit', async (event) => {
  if (event.target.id === 'token-form') {
    event.preventDefault();
    const token = document.getElementById('token-input').value.trim();
    if (!token) return;
    state.token = token;
    state.authRequired = false;
    state.lastError = '';
    window.localStorage.setItem('sanom_api_token', token);
    await loadDashboard();
    return;
  }

  if (event.target.id === 'request-form') {
    event.preventDefault();
    try {
      const response = await apiFetch('/api/request', {
        method: 'POST',
        body: JSON.stringify({
          requester: document.getElementById('request-requester').value.trim(),
          role_id: document.getElementById('request-role').value.trim(),
          action: document.getElementById('request-action').value.trim(),
          payload: parseJsonField('request-payload'),
          metadata: parseJsonField('request-metadata'),
        }),
      });
      const requestItem = response.item || response;
      const requestId = extractEntityId(response, ['request_id']);
      const targetView = inferRequestContinuationView(requestItem);
      state.lastError = requestId ? `Governed request ${requestId} submitted.` : 'Governed request submitted.';
      setActionContext({
        entityType: targetView === 'overrides' ? 'override' : 'request',
        entityId: requestId,
        view: targetView,
        title: requestId ? `Request ${requestId} entered the governed runtime.` : 'Governed request entered the runtime.',
        detail: targetView === 'overrides'
          ? 'The request crossed a human boundary, so the override lane is the next governed move.'
          : targetView === 'conflicts'
            ? 'The request is waiting in a blocked or conflicting lane, and the matching record is highlighted there.'
            : 'The request is now in the live runtime queue and its matching row stays highlighted for follow-through.',
        actionLabel: targetView === 'requests' ? 'Open runtime requests' : `Open ${VIEW_TITLES[targetView] || titleCase(targetView)}`,
      });
      state.view = targetView;
      updateNav();
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
    return;
  }

  if (event.target.id === 'studio-form') {
    event.preventDefault();
    try {
      const payload = studioPayloadFromForm();
      const editingRequestId = state.studioEditingRequestId;
      let studioResponse = null;
      if (state.studioEditingRequestId) {
        studioResponse = await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(state.studioEditingRequestId)}/update`, {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      } else {
        studioResponse = await apiFetch('/api/role-private-studio/requests', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }
      const requestId = editingRequestId || extractEntityId(studioResponse, ['request_id']);
      state.lastError = requestId
        ? (editingRequestId ? `Role Private Studio request ${requestId} updated.` : `Role Private Studio request ${requestId} created.`)
        : (editingRequestId ? 'Role Private Studio request updated.' : 'Role Private Studio request created.');
      setActionContext({
        entityType: 'studio_request',
        entityId: requestId,
        view: 'studio',
        title: requestId ? `Studio draft ${requestId} is ready in Role Private Studio.` : 'Role Private Studio draft saved.',
        detail: editingRequestId
          ? 'The updated draft remains highlighted so you can continue review or publication without hunting for it.'
          : 'The new draft now appears in the studio lanes and remains highlighted for the next governed step.',
        actionLabel: 'Open Role Private Studio',
      });
      if (editingRequestId) delete state.studioPtagDrafts[editingRequestId];
      clearStudioEditor();
      state.view = 'studio';
      updateNav();
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
  }

  if (event.target.id === 'human-ask-form') {
    event.preventDefault();
    try {
      const payload = buildHumanAskPayload(document);
      const response = await apiFetch('/api/human-ask/sessions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const sessionItem = response.item || response;
      const sessionId = extractEntityId(response, ['session_id']);
      state.lastError = buildHumanAskOutcomeMessage(sessionItem, 'Human Ask record created.');
      setActionContext({
        entityType: 'human_ask_session',
        entityId: sessionId,
        view: 'human_ask',
        title: sessionId ? `Human Ask record ${sessionId} is now active.` : 'Human Ask record created.',
        detail: 'The new governed record stays highlighted in the transcript lane so you can continue from the exact session that was just opened.',
        actionLabel: 'Open Human Ask records',
      });
      state.view = 'human_ask';
      updateNav();
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
    return;
  }

  if (event.target.id === 'owner-registration-form') {
    event.preventDefault();
    try {
      const payload = buildOwnerRegistrationPayload(document);
      const response = await apiFetch('/api/owner-registration', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const item = response.item || {};
      state.lastError = `Registration code ${item.registration_code || 'saved'} is active for ${item.organization_name || 'the current organization'} in ${item.deployment_mode || 'private'} mode.`;
      setActionContext({
        entityType: '',
        entityId: '',
        view: 'health',
        title: 'Owner registration saved.',
        detail: 'Runtime Health is the next governed lane because deployment, trust, and operator posture may have changed.',
        actionLabel: 'Open Runtime Health',
      });
      state.view = 'health';
      updateNav();
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
    return;
  }
});

root.addEventListener('input', (event) => {
  if (event.target.id === 'studio-governance-note' && state.studioGovernanceRequestId) {
    state.studioGovernanceNotes[state.studioGovernanceRequestId] = event.target.value;
  }
  if (event.target.id === 'studio-ptag-editor' && state.studioGovernanceRequestId) {
    const previousValue = state.studioPtagDrafts[state.studioGovernanceRequestId] || '';
    recordStudioPtagUndo(state.studioGovernanceRequestId, previousValue, event.target.value);
    state.studioPtagDrafts[state.studioGovernanceRequestId] = event.target.value;
    refreshStudioEditorAssist(state.studioGovernanceRequestId, event.target.value);
  }
});

root.addEventListener('scroll', (event) => {
  if (event.target.id === 'studio-ptag-editor') {
    const gutter = document.getElementById('studio-ptag-gutter');
    if (gutter) gutter.scrollTop = event.target.scrollTop;
  }
}, true);

root.addEventListener('change', (event) => {
  const compareSelect = event.target.closest('[data-studio-compare-select]');
  if (!compareSelect) return;
  const requestId = compareSelect.dataset.requestId || state.studioGovernanceRequestId;
  const item = getStudioRequestById(requestId);
  if (!item) return;
  const selection = ensureStudioRevisionSelection(item);
  const nextValue = Number.parseInt(compareSelect.value, 10) || 0;
  if (compareSelect.dataset.compareSide === 'current') selection.current_revision_number = nextValue;
  if (compareSelect.dataset.compareSide === 'previous') selection.previous_revision_number = nextValue;
  normalizeStudioRevisionSelection(item, selection, compareSelect.dataset.compareSide || '');
  state.studioRevisionSelections[requestId] = selection;
  render();
});

root.addEventListener('click', async (event) => {
  const actionableButton = event.target.closest(ACTIONABLE_BUTTON_SELECTOR);
  if (actionableButton) event.preventDefault();

  const devLaneButton = event.target.closest('[data-dev-lane]');
  if (devLaneButton) {
    const lane = DEV_LANES[devLaneButton.dataset.devLane || ''];
    if (!lane) return;
    state.token = lane.token;
    state.view = lane.view || 'overview';
    state.authRequired = false;
    state.lastError = '';
    window.localStorage.setItem('sanom_api_token', lane.token);
    await withButtonBusy(devLaneButton, () => loadDashboard(), 'Connecting...');
    scrollDashboardToTop();
    return;
  }

  const viewJumpButton = event.target.closest('[data-view-jump]');
  if (viewJumpButton) {
    const targetView = viewJumpButton.dataset.viewJump || state.view;
    const focusType = viewJumpButton.dataset.viewJumpFocusType || '';
    const focusId = viewJumpButton.dataset.viewJumpFocusId || '';
    const caseId = viewJumpButton.dataset.viewJumpCaseId || '';
    setActionContext({
      entityType: focusType,
      entityId: focusId,
      caseId,
      view: targetView,
      title: viewJumpButton.dataset.viewJumpTitle || `Moved to ${VIEW_TITLES[targetView] || titleCase(targetView)}.`,
      detail: viewJumpButton.dataset.viewJumpDetail || 'The linked governed item stays highlighted in the next lane so you can continue without hunting for it.',
      actionLabel: viewJumpButton.dataset.viewJumpActionLabel || `Open ${VIEW_TITLES[targetView] || titleCase(targetView)}`,
    });
    state.view = targetView;
    updateNav();
    render();
    scrollDashboardToTop();
    return;
  }

  const clearCaseScopeButton = event.target.closest('[data-case-scope-clear]');
  if (clearCaseScopeButton) {
    if (state.actionContext) {
      state.actionContext.caseId = '';
    }
    state.lastError = `Showing the full ${VIEW_TITLES[state.view] || titleCase(state.view)} lane again.`;
    render();
    scrollDashboardToTop();
    return;
  }

  const pathActionButton = event.target.closest('[data-path-action]');
  if (pathActionButton) {
    const action = pathActionButton.dataset.pathAction || '';
    const pathValue = pathActionButton.dataset.pathValue || '';
    try {
      if (action === 'copy') {
        await copyTextToClipboard(pathValue);
        state.lastError = `Copied: ${compactPathForDisplay(pathValue)}`;
        render();
        return;
      }
      if (action === 'open-folder') {
        const response = await apiFetch('/api/operator/open-path', { method: 'POST', body: JSON.stringify({ path: pathValue }) });
        const result = response.result || {};
        state.lastError = `Opened folder: ${compactPathForDisplay(result.opened_path || pathValue)}`;
        render();
        return;
      }
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
      return;
    }
  }

  const clearButton = event.target.closest('[data-studio-clear]');
  if (clearButton) {
    clearStudioEditor();
    render();
    return;
  }

  const overrideButton = event.target.closest('[data-override-action]');
  if (overrideButton) {
    const requestId = overrideButton.dataset.requestId;
    const action = overrideButton.dataset.overrideAction;
    const note = window.prompt(`${action === 'approve' ? 'Approve' : 'Veto'} override ${requestId} note`, action === 'approve' ? 'Approved from dashboard.' : 'Rejected from dashboard.');
    if (note === null) return;
    try {
      await apiFetch(`/api/overrides/${encodeURIComponent(requestId)}/${action}`, { method: 'POST', body: JSON.stringify({ note }) });
      state.lastError = `Override ${requestId} ${action === 'approve' ? 'approved' : 'vetoed'}.`;
      setActionContext({
        entityType: 'override',
        entityId: requestId,
        view: 'overrides',
        title: `Override ${requestId} ${action === 'approve' ? 'approved' : 'vetoed'}.`,
        detail: 'The override queue refreshed and the matching review row stays highlighted for follow-through.',
        actionLabel: 'Open override queue',
      });
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
    return;
  }

  const sessionButton = event.target.closest('[data-session-revoke]');
  if (sessionButton) {
    const sessionId = sessionButton.dataset.sessionId;
    const reason = window.prompt(`Revoke session ${sessionId} reason`, 'Revoked from dashboard.');
    if (reason === null) return;
    try {
      await apiFetch(`/api/sessions/${encodeURIComponent(sessionId)}/revoke`, { method: 'POST', body: JSON.stringify({ reason }) });
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
    return;
  }

  const auditButton = event.target.closest('[data-audit-action]');
  if (auditButton) {
    const action = auditButton.dataset.auditAction;
    if (action === 'reseal') {
      const confirmed = window.confirm('Reseal legacy audit entries and rebuild the active audit chain?');
      if (!confirmed) return;
      try {
        const response = await apiFetch('/api/audit/reseal', { method: 'POST', body: JSON.stringify({}) });
        const result = response.result || {};
        state.lastError = result.status === 'resealed'
          ? 'Audit log resealed. The maintenance event was added to the active chain.'
          : result.status === 'noop'
            ? 'Audit log is already fully sealed.'
            : `Audit reseal blocked: ${result.reason || 'unknown'}`;
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    return;
  }

  const opsButton = event.target.closest('[data-ops-action]');
  if (opsButton) {
    const action = opsButton.dataset.opsAction;
    if (action === 'backup') {
      const confirmed = window.confirm('Create a runtime operations backup bundle now?');
      if (!confirmed) return;
      try {
        const response = await apiFetch('/api/operations/backup', { method: 'POST', body: JSON.stringify({}) });
        const result = response.result || {};
        state.lastError = result.backup_id
          ? `Runtime backup created: ${result.backup_id}`
          : 'Runtime backup request completed.';
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    if (action === 'usability-proof') {
      const confirmed = window.confirm('Generate the v0.3.0 usability proof bundle now?');
      if (!confirmed) return;
      try {
        const response = await apiFetch('/api/operations/usability-proof', { method: 'POST', body: JSON.stringify({}) });
        const result = response.result || {};
        state.lastError = result.output_path
          ? `Usability proof generated: ${result.status || 'unknown'} at ${result.output_path}`
          : 'Usability proof bundle generation completed.';
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    if (action === 'usability-proof-refresh') {
      try {
        const response = await apiFetch('/api/operations/usability-proof');
        const item = response.item || {};
        state.lastError = `Latest proof status: ${item.status || 'unknown'} (available: ${String(Boolean(item.available))})`;
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    if (action === 'quick-start-doctor') {
      try {
        const response = await apiFetch('/api/operations/quick-start-doctor', { method: 'POST', body: JSON.stringify({}) });
        const result = response.result || {};
        state.lastError = `Quick-start doctor completed: ${result.status || 'unknown'} (required failed: ${String(result.summary?.required_failed_total || 0)})`;
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    if (action === 'quick-start-doctor-refresh') {
      try {
        const response = await apiFetch('/api/operations/quick-start-doctor');
        const item = response.item || {};
        state.lastError = `Latest quick-start doctor: ${item.status || 'missing'} (required failed: ${String(item.summary?.required_failed_total || 0)})`;
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    if (action === 'first-run-action-center-refresh') {
      try {
        const response = await apiFetch('/api/operations/first-run-action-center');
        const item = response.item || {};
        state.lastError = `First-run action center: ${item.status || 'blocked'} (required actions: ${String(item.required_total || 0)})`;
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    if (action === 'first-run-action-center-sync') {
      const confirmed = window.confirm('Run first-run action center now? This will generate usability proof and quick-start doctor artifacts.');
      if (!confirmed) return;
      try {
        const response = await apiFetch('/api/operations/first-run-action-center', { method: 'POST', body: JSON.stringify({}) });
        const result = response.result || {};
        const center = result.first_run_action_center || {};
        state.lastError = `First-run sync completed: ${center.status || 'unknown'} (required actions: ${String(center.required_total || 0)})`;
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    return;
  }

  const integrationButton = event.target.closest('[data-integration-action]');
  if (integrationButton) {
    const action = integrationButton.dataset.integrationAction;
    if (action === 'test-event') {
      try {
        const response = await apiFetch('/api/integrations/test-event', { method: 'POST', body: JSON.stringify({}) });
        const result = response.result || {};
        state.lastError = result.event_id
          ? `Integration test event dispatched: ${result.event_id}`
          : 'Integration test event completed.';
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    return;
  }

  const humanAskButton = event.target.closest('[data-human-ask-action]');
  if (humanAskButton) {
    try {
      const handled = await handleHumanAskAction({
        button: humanAskButton,
        apiFetch,
        setMessage: (message) => { state.lastError = message; },
        setHumanAskView: () => {
          state.view = 'human_ask';
          updateNav();
          scrollDashboardToTop();
        },
        setActionContext,
        loadDashboard,
        windowRef: window,
      });
      if (handled) return;
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
    return;
  }

  const governanceSelectButton = event.target.closest('[data-studio-governance-select]');
  if (governanceSelectButton) {
    state.studioGovernanceRequestId = governanceSelectButton.dataset.requestId || null;
    const item = getStudioRequestById(state.studioGovernanceRequestId);
    if (item) {
      ensureStudioGovernanceNote(item);
      ensureStudioRevisionSelection(item);
      ensureStudioPtagDraft(item);
    }
    render();
    scrollDashboardToTop();
    focusStudioGovernancePanel();
    return;
  }

  const templateButton = event.target.closest('[data-studio-template-apply]');
  if (templateButton) {
    const templateId = templateButton.dataset.templateId;
    const studio = state.snapshot?.role_private_studio || {};
    const library = Array.isArray(studio.template?.library) ? studio.template.library : [];
    const template = library.find((item) => item.template_id === templateId);
    if (!template || !template.payload) return;
    state.studioEditingRequestId = null;
    state.studioEditorDraft = template.payload;
    fillStudioForm(template.payload);
    state.lastError = `Applied template ${template.label || template.template_id} to the Studio form.`;
    setActionContext({
      entityType: '',
      entityId: '',
      view: 'studio',
      title: `Template ${template.label || template.template_id} loaded into the editor.`,
      detail: 'Continue by adjusting the draft fields and submitting the role request from the same studio lane.',
      actionLabel: 'Return to Role Private Studio',
    });
    render();
    scrollDashboardToTop();
    focusStudioEditor();
    return;
  }

  const studioPanelButton = event.target.closest('[data-studio-panel-action]');
  if (studioPanelButton) {
    const requestId = studioPanelButton.dataset.requestId;
    const action = studioPanelButton.dataset.studioPanelAction;
    const noteField = document.getElementById('studio-governance-note');
    const note = noteField ? noteField.value.trim() : (state.studioGovernanceNotes[requestId] || '').trim();
    if (noteField) state.studioGovernanceNotes[requestId] = noteField.value;
    const ptagField = document.getElementById('studio-ptag-editor');
    const ptagSource = ptagField ? ptagField.value : (state.studioPtagDrafts[requestId] || '');
    if (ptagField) state.studioPtagDrafts[requestId] = ptagField.value;
    const item = getStudioRequestById(requestId);
    const revisionSelection = item ? ensureStudioRevisionSelection(item) : { current_revision_number: 0 };
    try {
      if (action === 'load') {
        await loadStudioRequestIntoEditor(requestId);
        state.lastError = `Loaded ${requestId} into the Studio editor.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `Studio draft ${requestId} loaded into the editor.`,
          detail: 'The selected draft stays highlighted while the editor is ready for the next governed edit.',
          actionLabel: 'Open Role Private Studio',
        });
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `Studio draft ${requestId} loaded into the editor.`,
          detail: 'The selected draft stays highlighted while the editor is positioned for the next governed edit.',
          actionLabel: 'Open Role Private Studio',
        });
        state.view = 'studio';
        updateNav();
        render();
        scrollDashboardToTop();
        focusStudioEditor();
        return;
      }
      if (action === 'refresh') {
        await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}/refresh`, { method: 'POST', body: JSON.stringify({}) });
        delete state.studioPtagDrafts[requestId];
        state.lastError = `Studio draft ${requestId} refreshed from the governance panel.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `Studio draft ${requestId} refreshed.`,
          detail: 'The refreshed draft remains highlighted so review and publication can continue from the same governed lane.',
          actionLabel: 'Open Role Private Studio',
        });
      }
      if (action === 'save_ptag') {
        await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}/ptag`, { method: 'POST', body: JSON.stringify({ ptag_source: ptagSource }) });
        state.lastError = `PTAG draft for ${requestId} updated from the live editor.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `PTAG draft for ${requestId} updated.`,
          detail: 'The same studio draft stays highlighted so you can keep reviewing, simulating, or publishing without losing context.',
          actionLabel: 'Open Role Private Studio',
        });
      }
      if (action === 'reset_ptag') {
        await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}/ptag-reset`, { method: 'POST', body: JSON.stringify({}) });
        delete state.studioPtagDrafts[requestId];
        resetStudioPtagHistory(requestId);
        state.lastError = `PTAG editor for ${requestId} reverted to generated mode.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `PTAG editor for ${requestId} reset to generated mode.`,
          detail: 'The same studio draft remains highlighted for the next review move.',
          actionLabel: 'Open Role Private Studio',
        });
      }
      if (action === 'undo_ptag') {
        const nextValue = undoStudioPtagDraft(requestId);
        if (typeof nextValue === 'string') {
          if (ptagField) ptagField.value = nextValue;
          state.studioPtagDrafts[requestId] = nextValue;
          refreshStudioEditorAssist(requestId, nextValue);
          state.lastError = `PTAG editor for ${requestId} moved one step backward.`;
        }
        render();
        return;
      }
      if (action === 'redo_ptag') {
        const nextValue = redoStudioPtagDraft(requestId);
        if (typeof nextValue === 'string') {
          if (ptagField) ptagField.value = nextValue;
          state.studioPtagDrafts[requestId] = nextValue;
          refreshStudioEditorAssist(requestId, nextValue);
          state.lastError = `PTAG editor for ${requestId} moved one step forward.`;
        }
        render();
        return;
      }
      if (action === 'restore_revision') {
        await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}/restore-revision`, {
          method: 'POST',
          body: JSON.stringify({ revision_number: revisionSelection.current_revision_number }),
        });
        delete state.studioPtagDrafts[requestId];
        resetStudioPtagHistory(requestId);
        state.lastError = `Studio draft ${requestId} restored from revision ${revisionSelection.current_revision_number}.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `Studio draft ${requestId} restored from revision ${revisionSelection.current_revision_number}.`,
          detail: 'The restored draft remains highlighted so the next governance decision can continue immediately.',
          actionLabel: 'Open Role Private Studio',
        });
      }
      if (action === 'approve') {
        await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}/review`, { method: 'POST', body: JSON.stringify({ decision: 'approve', note: note || 'Approved for publish from the live governance panel.' }) });
        delete state.studioGovernanceNotes[requestId];
        state.lastError = `Studio draft ${requestId} approved.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `Studio draft ${requestId} approved for publication.`,
          detail: 'The approved draft remains highlighted in the studio publish lane for the next trusted action.',
          actionLabel: 'Open Role Private Studio',
        });
      }
      if (action === 'request_changes') {
        await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}/review`, { method: 'POST', body: JSON.stringify({ decision: 'request_changes', note: note || 'Please refine the role draft and resimulate it.' }) });
        delete state.studioGovernanceNotes[requestId];
        state.lastError = `Change request recorded for ${requestId}.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `Change request recorded for ${requestId}.`,
          detail: 'The same draft stays highlighted so the reviewer and author can continue from the exact governance item.',
          actionLabel: 'Open Role Private Studio',
        });
      }
      if (action === 'publish') {
        const confirmed = window.confirm(`Publish Role Private Studio request ${requestId} into the trusted registry?`);
        if (!confirmed) return;
        await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}/publish`, { method: 'POST', body: JSON.stringify({}) });
        delete state.studioGovernanceNotes[requestId];
        state.lastError = `Studio draft ${requestId} published into the trusted registry.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `Studio draft ${requestId} published into the trusted registry.`,
          detail: 'The published role remains highlighted so you can verify trust posture and rollout proof from the same lane.',
          actionLabel: 'Open Role Private Studio',
        });
      }
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
    return;
  }

  const studioButton = event.target.closest('[data-studio-action]');
  if (studioButton) {
    const requestId = studioButton.dataset.requestId;
    const action = studioButton.dataset.studioAction;
    try {
      if (action === 'load') {
        await loadStudioRequestIntoEditor(requestId);
        state.lastError = `Loaded ${requestId} into the Studio editor.`;
        state.view = 'studio';
        updateNav();
        render();
        scrollDashboardToTop();
        focusStudioEditor();
        return;
      }
      if (action === 'refresh') {
        await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}/refresh`, { method: 'POST', body: JSON.stringify({}) });
        delete state.studioPtagDrafts[requestId];
        state.lastError = `Studio draft ${requestId} refreshed.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: `Studio draft ${requestId} refreshed.`,
          detail: 'The refreshed draft stays highlighted in the studio lanes for continued review.',
          actionLabel: 'Open Role Private Studio',
        });
      }
      if (['approve', 'request_changes', 'publish'].includes(action)) {
        const item = getStudioRequestById(requestId);
        state.studioGovernanceRequestId = requestId;
        if (item) {
          ensureStudioRevisionSelection(item);
          ensureStudioGovernanceNote(item, defaultStudioGovernanceActionNote(item, action));
        }
        state.lastError = action === 'publish'
          ? `Publish confirmation is ready in the governance panel for ${requestId}.`
          : `Review action is ready in the governance panel for ${requestId}.`;
        setActionContext({
          entityType: 'studio_request',
          entityId: requestId,
          view: 'studio',
          title: action === 'publish'
            ? `Studio draft ${requestId} is positioned for trusted publication.`
            : `Studio draft ${requestId} is positioned for reviewer action.`,
          detail: 'The governance panel is now the correct next lane, and the selected draft stays highlighted there.',
          actionLabel: 'Open governance panel',
        });
        render();
        focusStudioGovernancePanel();
        return;
      }
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
  }
});

loadDashboard();

function scrollDashboardToTop() {
  window.requestAnimationFrame(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

function buildFocusKey(entityType, entityId) {
  const type = String(entityType || '').trim();
  const id = String(entityId || '').trim();
  return type && id ? `${type}:${id}` : '';
}

function setActionContext({ entityType = '', entityId = '', caseId = '', view = '', title = '', detail = '', actionLabel = '' } = {}) {
  const normalizedEntityType = String(entityType || '').trim();
  const normalizedEntityId = String(entityId || '').trim();
  const normalizedCaseId = String(caseId || (normalizedEntityType === 'case' ? normalizedEntityId : '')).trim();
  const focusKey = buildFocusKey(normalizedEntityType, normalizedEntityId);
  const targetView = view || state.view || 'overview';
  state.actionContext = {
    entityType: normalizedEntityType,
    entityId: normalizedEntityId,
    caseId: normalizedCaseId,
    focusKey,
    view: targetView,
    title: title || 'Latest governed result',
    detail: detail || 'The Director recorded the latest action and mapped the next governed move.',
    actionLabel: actionLabel || `Open ${VIEW_TITLES[targetView] || titleCase(targetView)}`,
    pendingFocus: Boolean(focusKey),
  };
}

function isFocusedEntity(entityType, entityId) {
  const current = state.actionContext?.focusKey || '';
  return current ? current === buildFocusKey(entityType, entityId) : false;
}

function extractEntityId(payload, preferredKeys = ['request_id', 'session_id', 'event_id', 'registration_code', 'id']) {
  const queue = [payload];
  const seen = new Set();
  while (queue.length) {
    const current = queue.shift();
    if (!current || typeof current !== 'object' || seen.has(current)) continue;
    seen.add(current);
    for (const key of preferredKeys) {
      const value = current[key];
      if (typeof value === 'string' && value.trim()) return value.trim();
    }
    const values = Array.isArray(current) ? current : Object.values(current);
    values.forEach((value) => { if (value && typeof value === 'object') queue.push(value); });
  }
  return '';
}

function collectResponseText(payload) {
  const queue = [payload];
  const seen = new Set();
  const parts = [];
  while (queue.length && parts.length < 32) {
    const current = queue.shift();
    if (current == null) continue;
    if (typeof current === 'string') {
      if (current.trim()) parts.push(current.trim());
      continue;
    }
    if (typeof current !== 'object' || seen.has(current)) continue;
    seen.add(current);
    const values = Array.isArray(current) ? current : Object.values(current);
    values.forEach((value) => {
      if (typeof value === 'string') {
        if (value.trim()) parts.push(value.trim());
      } else if (value && typeof value === 'object') {
        queue.push(value);
      }
    });
  }
  return parts.join(' ').toLowerCase();
}

function inferRequestContinuationView(payload) {
  const text = collectResponseText(payload);
  if (!text) return 'requests';
  if (text.includes('waiting_human') || text.includes('human_required') || text.includes('human override') || text.includes('out_of_scope') || text.includes('human_only_boundary') || text.includes('approval')) return 'overrides';
  if (text.includes('conflict') || text.includes('contention') || text.includes('lock') || text.includes('retry') || text.includes('fail_closed') || text.includes('blocked')) return 'conflicts';
  return 'requests';
}

function focusActionContextTarget() {
  if (!state.actionContext?.pendingFocus) return;
  const focusKey = state.actionContext.focusKey;
  if (!focusKey) {
    state.actionContext.pendingFocus = false;
    return;
  }
  window.requestAnimationFrame(() => {
    const target = Array.from(root.querySelectorAll('[data-focus-key], [data-focus-alt-key]')).find((node) => node.dataset.focusKey === focusKey || node.dataset.focusAltKey === focusKey);
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    target.classList.add('focus-pulse');
    window.setTimeout(() => { if (target.isConnected) target.classList.remove('focus-pulse'); }, 1400);
    state.actionContext.pendingFocus = false;
  });
}

function focusStudioEditor() {
  window.requestAnimationFrame(() => {
    const form = document.getElementById('studio-form');
    if (form) form.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

async function withButtonBusy(button, task, pendingLabel = 'Working...') {
  if (!button) return task();
  const originalLabel = button.textContent;
  button.disabled = true;
  button.dataset.busy = 'true';
  button.textContent = pendingLabel;
  try {
    return await task();
  } finally {
    if (button.isConnected) {
      button.disabled = false;
      button.dataset.busy = 'false';
      button.textContent = originalLabel;
    }
  }
}

async function loadDashboard() {
  if (!state.sessionToken && !state.token) {
    state.authRequired = true;
    render();
    return;
  }
  try {
    if (!state.sessionToken && state.token) {
      await loginWithAccessToken();
    }
    const snapshot = await apiFetch('/api/dashboard', {}, { useSession: Boolean(state.sessionToken) });
    state.snapshot = snapshot;
    state.session = snapshot.session || null;
    state.authRequired = false;
    render();
  } catch (error) {
    const message = String(error.message || error);
    if (message.includes('401')) {
      state.authRequired = true;
      state.session = null;
      state.snapshot = null;
      state.sessionToken = '';
      window.localStorage.removeItem('sanom_session_token');
    }
    state.lastError = message;
    render();
  }
}

async function loginWithAccessToken() {
  if (!state.token) return;
  const response = await apiFetch('/api/session/login', { method: 'POST' }, { useAccessToken: true });
  state.sessionToken = response.session_token || '';
  if (state.sessionToken) window.localStorage.setItem('sanom_session_token', state.sessionToken);
}

async function copyTextToClipboard(text) {
  const value = String(text || '').trim();
  if (!value) return;
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const field = document.createElement('textarea');
  field.value = value;
  field.setAttribute('readonly', 'true');
  field.style.position = 'fixed';
  field.style.opacity = '0';
  document.body.appendChild(field);
  field.select();
  document.execCommand('copy');
  document.body.removeChild(field);
}

async function apiFetch(path, options = {}, auth = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (auth.useSession && state.sessionToken) headers['X-SA-NOM-Session'] = state.sessionToken;
  else if (auth.useAccessToken && state.token) headers['X-SA-NOM-Token'] = state.token;
  else if (state.sessionToken) headers['X-SA-NOM-Session'] = state.sessionToken;
  else if (state.token) headers['X-SA-NOM-Token'] = state.token;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`);
  return response.json();
}

async function loadStudioRequestIntoEditor(requestId) {
  const response = await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}`);
  const item = response.item || null;
  if (!item) throw new Error(`Role Private Studio request not found: ${requestId}`);
  state.studioEditingRequestId = item.request_id;
  state.studioEditorDraft = item.structured_jd || {};
  fillStudioForm(item.structured_jd || {});
}

function render() {
  viewTitle.textContent = VIEW_TITLES[state.view];
  viewDescription.textContent = VIEW_DESCRIPTIONS[state.view];
  sidebarViewTitle.textContent = VIEW_TITLES[state.view];
  sidebarViewDescription.textContent = VIEW_DESCRIPTIONS[state.view];
  topbarFocusLabel.textContent = VIEW_TITLES[state.view];
  document.body.dataset.view = state.view;
  if (state.authRequired || !state.snapshot) {
    sessionLabel.textContent = 'disconnected';
    environmentLabel.textContent = 'token required';
    generatedAt.textContent = state.lastError ? `Last error: ${state.lastError}` : 'Enter API token to access live runtime data.';
    sidebarOperatorLabel.textContent = 'Disconnected';
    sidebarRuntimeLabel.textContent = 'Token required';
    sidebarGeneratedLabel.textContent = generatedAt.textContent;
    topbarRuntimeLabel.textContent = 'Awaiting session';
    root.innerHTML = renderAuthCard();
    updateNav();
    return;
  }

  const snapshot = state.snapshot;
  sessionLabel.textContent = state.session ? `${state.session.display_name} | ${state.session.role_name}` : 'connected';
  environmentLabel.textContent = `${snapshot.environment} environment`;
  generatedAt.textContent = `Live data: ${formatDateTime(snapshot.generated_at)}`;
  sidebarOperatorLabel.textContent = state.session ? state.session.display_name : 'Connected';
  sidebarRuntimeLabel.textContent = `${snapshot.environment} runtime`;
  sidebarGeneratedLabel.textContent = generatedAt.textContent;
  topbarRuntimeLabel.textContent = state.session ? state.session.role_name : `${snapshot.environment} runtime`;

  const requiredPermission = VIEW_PERMISSIONS[state.view];
  if (requiredPermission && !can(requiredPermission)) {
    root.innerHTML = renderPermissionNotice(requiredPermission);
    updateNav();
    return;
  }

  const scopedSnapshot = getCaseScopedSnapshot(snapshot);
  let viewContent = '';
  if (state.view === 'overview') viewContent = renderOverview(snapshot);
  if (state.view === 'requests') viewContent = renderRequests(scopedSnapshot);
  if (state.view === 'cases') viewContent = renderCases(snapshot);
  if (state.view === 'overrides') viewContent = renderOverridesView(scopedSnapshot);
  if (state.view === 'conflicts') viewContent = renderConflicts(scopedSnapshot);
  if (state.view === 'audit') viewContent = renderAudit(scopedSnapshot);
  if (state.view === 'studio') {
    viewContent = renderStudio(scopedSnapshot.role_private_studio || { summary: {}, requests: [], examples: [] });
    if (state.studioEditorDraft) fillStudioForm(state.studioEditorDraft);
  }
  if (state.view === 'human_ask') viewContent = renderHumanAsk(
    scopedSnapshot.human_ask || { summary: {}, sessions: [], callable_directory: { summary: {}, entries: [] } },
    {
      can,
      helpers: { escapeHtml, keyValue, metricCard, shortTime, statusBadge, titleCase, buildFocusKey, isFocusedEntity, renderCaseReferenceButton },
    },
  );
  if (state.view === 'sessions') viewContent = wrapTableCard('Sessions', sessionTable(snapshot.sessions || []), 'Live private-server sessions with rotation, idle discipline, and revocation control.');
  if (state.view === 'policies') viewContent = renderPolicies(snapshot.roles || []);
  if (state.view === 'health') viewContent = renderHealth(snapshot.runtime_health, snapshot.available_profiles || [], snapshot.retention || null, snapshot.operations || null, snapshot.integrations || null, snapshot.operator_notification_center || null, snapshot.operator_notification_delivery_readiness || null);
  const focusedInbox = state.view === 'overview' ? '' : renderFocusedWorkInbox(snapshot, state.view);
  const caseSpotlight = renderCaseSpotlight(snapshot);
  const workLanguageGuide = renderWorkLanguageGuide(snapshot);
  root.innerHTML = `${renderActionFeedback()}${renderActionContinuity()}${renderAlertRail(snapshot)}${renderViewPrelude(snapshot)}${renderWorkflowGuide(snapshot)}${caseSpotlight}${workLanguageGuide}${focusedInbox}${viewContent}`;
  updateNav();
  focusActionContextTarget();
}

function renderActionFeedback() {
  if (!state.lastError || state.authRequired) return '';
  const tone = classifyActionFeedbackTone(state.lastError);
  const title = tone === 'danger'
    ? 'Action blocked'
    : tone === 'warning'
      ? 'Action needs attention'
      : 'Latest action';
  return `<article class="card notice-card notice-${escapeHtml(tone)} stack"><div class="eyebrow muted">Runtime feedback</div><strong>${escapeHtml(title)}</strong><p class="muted">${escapeHtml(state.lastError)}</p></article>`;
}

function renderActionContinuity() {
  const context = state.actionContext;
  if (!context || state.authRequired) return '';
  const viewLabel = VIEW_TITLES[context.view] || titleCase(context.view || 'overview');
  const reference = context.entityId ? `<span class="pill">Ref ${escapeHtml(context.entityId)}</span>` : '';
  const focusNote = context.entityId
    ? 'The matching row or card stays highlighted so you can continue from the exact governed work item.'
    : 'The Director mapped the next lane for you so you do not need to guess where this action landed.';
  return `
    <article class="card action-continuity-card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Next governed move</div>
          <strong>${escapeHtml(context.title || 'Latest governed result')}</strong>
          <p class="muted">${escapeHtml(context.detail || focusNote)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge('latest result')}${statusBadge(viewLabel)}</div>
      </div>
      <div class="inline-actions">
        <button class="action-button action-button-muted" type="button" data-view-jump="${escapeHtml(context.view || 'overview')}">${escapeHtml(context.actionLabel || `Open ${viewLabel}`)}</button>
        ${reference}
      </div>
      <p class="muted">${escapeHtml(focusNote)}</p>
    </article>
  `;
}

function classifyActionFeedbackTone(message) {
  const text = String(message || '').toLowerCase();
  if (!text) return 'default';
  if (text.includes('api ') || text.includes('unauthorized') || text.includes('forbidden') || text.includes('error')) return 'danger';
  if (text.includes('blocked') || text.includes('waiting') || text.includes('paused') || text.includes('required') || text.includes('warning')) return 'warning';
  return 'success';
}
function renderAlertRail(snapshot) {
  const alerts = buildRuntimeAlerts(snapshot);
  if (!alerts.length) return '';
  return `
    <section class="alert-rail">
      ${alerts.map((alert) => `
        <article class="card notice-card notice-${escapeHtml(alert.tone || 'warning')} stack runtime-alert-card">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">${escapeHtml(alert.eyebrow || 'Runtime alert')}</div>
              <h3 class="card-title">${escapeHtml(alert.title)}</h3>
              <p class="card-subtitle">${escapeHtml(alert.message)}</p>
            </div>
            <div class="hero-chip-row">${statusBadge(alert.badge || alert.tone || 'warning')}</div>
          </div>
          ${alert.details?.length ? keyValue(alert.details) : ''}
          ${alert.view ? `<div class="inline-actions"><button class="action-button" data-view-jump="${escapeHtml(alert.view)}">${escapeHtml(alert.actionLabel || 'Open view')}</button></div>` : ''}
        </article>
      `).join('')}
    </section>
  `;
}

function buildRuntimeAlerts(snapshot) {
  if (Array.isArray(snapshot.runtime_alerts) && snapshot.runtime_alerts.length) {
    return snapshot.runtime_alerts.map((alert) => ({
      eyebrow: alert.eyebrow || 'Runtime alert',
      title: alert.title || 'Runtime attention needed',
      message: alert.message || 'A governed runtime condition needs attention.',
      tone: alert.tone || 'warning',
      badge: alert.badge || alert.tone || 'warning',
      view: alert.view || '',
      actionLabel: alert.action_label || 'Open view',
      details: Object.entries(alert.details || {}).map(([key, value]) => [titleCase(key), String(value)]),
    }));
  }
  const alerts = [];
  const humanAsk = snapshot.human_ask || {};
  const sessions = Array.isArray(humanAsk.sessions) ? humanAsk.sessions : [];
  const summary = humanAsk.summary || {};
  const outOfScopeSessions = sessions.filter((session) => (session.decision_summary?.metadata?.scope_status || '') === 'out_of_scope');
  const boundarySessions = sessions.filter((session) => {
    const scopeStatus = session.decision_summary?.metadata?.scope_status || '';
    return session.status === 'waiting_human' || scopeStatus === 'human_only_boundary';
  });
  const blockedSessions = sessions.filter((session) => session.status === 'blocked');
  if (outOfScopeSessions.length) {
    alerts.push({
      eyebrow: 'Scope boundary',
      title: 'AI stopped because some requests moved outside the loaded JD scope',
      message: 'These records need a real human decision. The Director correctly refused to keep automating beyond the approved role boundary.',
      tone: 'danger',
      badge: `${outOfScopeSessions.length} out of scope`,
      view: 'human_ask',
      actionLabel: 'Open Human Ask',
      details: [
        ['Out-of-scope records', String(outOfScopeSessions.length)],
        ['Waiting human', String(summary.waiting_human_total || boundarySessions.length)],
        ['Latest participant', outOfScopeSessions[0]?.participant?.display_name || outOfScopeSessions[0]?.summary?.participant || '-'],
      ],
    });
  } else if (boundarySessions.length || blockedSessions.length) {
    alerts.push({
      eyebrow: 'Human boundary',
      title: 'AI paused at a reserved human or structural boundary',
      message: 'Automation stopped at the correct handoff line. These records are waiting because the request crossed a human-only action, sensitive boundary, or blocked callable lane.',
      tone: blockedSessions.length ? 'danger' : 'warning',
      badge: `${Math.max(boundarySessions.length, blockedSessions.length)} attention`,
      view: 'human_ask',
      actionLabel: 'Review records',
      details: [
        ['Waiting human', String(summary.waiting_human_total || boundarySessions.length)],
        ['Blocked records', String(blockedSessions.length)],
        ['Latest participant', (boundarySessions[0] || blockedSessions[0])?.participant?.display_name || (boundarySessions[0] || blockedSessions[0])?.summary?.participant || '-'],
      ],
    });
  }
  return alerts;
}

function renderViewPrelude(snapshot) {
  const cues = buildViewCues(snapshot);
  const usageCue = buildViewUseHint();
  const visibleCues = usageCue ? [usageCue, ...cues] : cues;
  if (!visibleCues.length) return '';
  const profile = VIEW_INTELLIGENCE[state.view] || {
    eyebrow: 'View Intelligence',
    title: `${VIEW_TITLES[state.view]} focus`,
    narrative: VIEW_DESCRIPTIONS[state.view],
    emphasis: 'runtime posture',
  };
  return `
    <section class="view-prelude card view-prelude-${escapeHtml(state.view)}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(profile.eyebrow)}</div>
          <h3 class="card-title">${escapeHtml(profile.title)}</h3>
          <p class="card-subtitle">${escapeHtml(profile.narrative)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(profile.emphasis)}${statusBadge(snapshot.environment || 'runtime')}</div>
      </div>
      <div class="view-prelude-grid">
        ${visibleCues.map((cue) => `
          <article class="view-prelude-card${cue.tone ? ` view-prelude-card-${escapeHtml(cue.tone)}` : ''}">
            <span class="view-prelude-label">${escapeHtml(cue.label)}</span>
            <strong>${escapeHtml(String(cue.value))}</strong>
            <p class="muted">${escapeHtml(cue.note)}</p>
          </article>
        `).join('')}
      </div>
    </section>
  `;
}

function renderWorkflowGuide(snapshot) {
  const workflow = buildWorkflowGuide(snapshot);
  if (!workflow.primary && !workflow.related.length) return '';
  const primaryAction = workflow.primary
    ? (workflow.primary.view === state.view
      ? `<p class="permission-note workflow-current-note">${escapeHtml(workflow.primary.actionLabel || 'You are already in the right place.')}</p>`
      : `<div class="inline-actions"><button class="action-button" data-view-jump="${escapeHtml(workflow.primary.view)}">${escapeHtml(workflow.primary.actionLabel || `Open ${VIEW_TITLES[workflow.primary.view] || workflow.primary.view}`)}</button></div>`)
    : '';
  return `
    <section class="workflow-guide-grid">
      ${workflow.primary ? `
        <article class="card stack workflow-guide-card workflow-guide-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">${escapeHtml(workflow.primary.eyebrow || 'Next governed move')}</div>
              <h3 class="card-title">${escapeHtml(workflow.primary.title)}</h3>
              <p class="card-subtitle">${escapeHtml(workflow.primary.detail)}</p>
            </div>
            <div class="hero-chip-row">${statusBadge(workflow.primary.badge || 'next step')}</div>
          </div>
          ${workflow.primary.details?.length ? keyValue(workflow.primary.details) : ''}
          ${primaryAction}
        </article>
      ` : ''}
      ${workflow.related.length ? `
        <article class="card stack workflow-guide-card">
          <div>
            <div class="eyebrow muted">Related views</div>
            <h3 class="card-title">Keep the flow connected</h3>
            <p class="card-subtitle">These views usually come next or provide the proof needed to finish the current task.</p>
          </div>
          <div class="onboarding-grid workflow-related-grid">
            ${workflow.related.map((item) => `
              <article class="mini-card workflow-related-card">
                <div class="eyebrow muted">${escapeHtml(item.eyebrow || 'Related view')}</div>
                <strong>${escapeHtml(VIEW_TITLES[item.view] || item.view)}</strong>
                <p class="muted">${escapeHtml(item.note)}</p>
                <div class="inline-actions">
                  <button class="action-button action-button-muted" data-view-jump="${escapeHtml(item.view)}">${escapeHtml(item.actionLabel || `Open ${VIEW_TITLES[item.view] || item.view}`)}</button>
                </div>
              </article>
            `).join('')}
          </div>
        </article>
      ` : ''}
    </section>
  `;
}

function renderWorkLanguageGuide(snapshot) {
  if (!['overview', 'requests', 'overrides', 'studio', 'human_ask', 'conflicts'].includes(state.view)) return '';
  const summary = snapshot.unified_work_inbox?.summary || {};
  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Work Language</div>
          <h3 class="card-title">One set of words for every governed work item</h3>
          <p class="card-subtitle">Requests, approvals, report records, recovery items, and studio drafts should read like one operating system, not separate tools with separate vocabularies.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(summary.primary_title || 'Governed Work')}</div>
      </div>
      <div class="view-prelude-grid">
        <article class="view-prelude-card view-prelude-card-success">
          <span class="view-prelude-label">Ready</span>
          <strong>AI can keep moving</strong>
          <p class="muted">The governed lane is clear enough for the runtime to continue without a new human interruption.</p>
        </article>
        <article class="view-prelude-card view-prelude-card-accent">
          <span class="view-prelude-label">Monitoring</span>
          <strong>Visible, not yet stopping flow</strong>
          <p class="muted">A human should keep an eye on it, but the runtime is still allowed to operate inside policy.</p>
        </article>
        <article class="view-prelude-card view-prelude-card-warning">
          <span class="view-prelude-label">Human required</span>
          <strong>A real decision is now needed</strong>
          <p class="muted">The runtime crossed a human boundary and must wait for explicit review, approval, or clearance.</p>
        </article>
        <article class="view-prelude-card view-prelude-card-danger">
          <span class="view-prelude-label">Blocked</span>
          <strong>The runtime cannot continue</strong>
          <p class="muted">A governed path is fail-closed until someone resolves the issue or deliberately resumes it.</p>
        </article>
      </div>
      <div class="trace-box"><strong>Work item definition</strong><p class="muted">A governed work item can be a request, override, Human Ask record, recovery item, or Studio draft. The dashboard should always tell you who owns it, what state it is in, and what happens next.</p></div>
    </section>
  `;
}

function buildViewUseHint() {
  const hint = VIEW_USE_HINTS[state.view];
  if (!hint) return null;
  return {
    label: 'Use this page when',
    value: hint.value,
    note: hint.note,
    tone: hint.tone || 'accent',
  };
}

function buildViewCues(snapshot) {
  const summary = snapshot.summary || {};
  const studio = snapshot.role_private_studio?.summary || {};
  const humanAsk = snapshot.human_ask?.summary || {};
  const runtimeHealth = snapshot.runtime_health || {};
  const integrations = snapshot.integrations?.summary || {};
  const goLive = snapshot.go_live_readiness || runtimeHealth.go_live_readiness || {};
  const access = runtimeHealth.access_control || {};
  const audit = runtimeHealth.audit_integrity || {};
  const privilegedOperations = goLive.privileged_operations || runtimeHealth.privileged_operations || {};
  const studioStructural = goLive.studio_structural || runtimeHealth.studio_structural || {};
  const requests = snapshot.requests || [];
  const conflicts = requests.filter((item) => item.outcome === 'conflicted').length;
  const pendingOverrides = (snapshot.overrides || []).filter((item) => item.status === 'pending').length;

  if (state.view === 'overview') {
    return [
      { label: 'Go-live', value: goLive.status || 'blocked', note: 'Combined trust, smoke, delegated privilege coverage, and evidence gate across the runtime.', tone: goLive.status === 'ready' ? 'success' : goLive.status === 'guarded' ? 'warning' : 'danger' },
      { label: 'Studio ready', value: studio.ready_to_publish_total || 0, note: 'Draft hats that can move toward trusted publication now.', tone: 'success' },
      { label: 'Runtime alerts', value: summary.runtime_alert_total || 0, note: 'Boundary and readiness events where the Director paused or the runtime remains guarded.', tone: (summary.runtime_alert_critical_total || 0) ? 'danger' : (summary.runtime_alert_total || 0) ? 'warning' : 'success' },
    ];
  }
  if (state.view === 'requests') {
    return [
      { label: 'Queue volume', value: summary.requests_total || requests.length, note: 'Visible governed submissions currently flowing through runtime intake.', tone: 'accent' },
      { label: 'Pending overrides', value: pendingOverrides, note: 'Requests that crossed a human boundary and still need resolution.', tone: pendingOverrides ? 'warning' : 'success' },
      { label: 'Conflict exposure', value: conflicts, note: 'Requests currently colliding with resource locks or consistency pressure.', tone: conflicts ? 'warning' : 'success' },
    ];
  }
  if (state.view === 'conflicts') {
    return [
      { label: 'Active locks', value: summary.active_locks || (snapshot.locks || []).length, note: 'Resources under live protection against conflicting execution.', tone: 'warning' },
      { label: 'Conflicted requests', value: conflicts, note: 'Requests already blocked by contention or ordering pressure.', tone: conflicts ? 'warning' : 'success' },
      { label: 'Escalated lanes', value: summary.escalated_total || 0, note: 'Execution lanes already diverted into governed review paths.', tone: 'accent' },
    ];
  }
  if (state.view === 'audit') {
    return [
      { label: 'Integrity', value: audit.status || 'unknown', note: 'Current audit-chain trust posture.', tone: audit.status === 'verified' ? 'success' : 'warning' },
      { label: 'Hash mismatches', value: audit.hash_mismatches || 0, note: 'Any non-zero value should immediately elevate operator attention.', tone: (audit.hash_mismatches || 0) ? 'danger' : 'success' },
      { label: 'Legacy entries', value: audit.legacy_unsealed_entries || 0, note: 'Historic entries that still require sealing maintenance if present.', tone: (audit.legacy_unsealed_entries || 0) ? 'warning' : 'default' },
    ];
  }
  if (state.view === 'studio') {
    return [
      { label: 'Ready to publish', value: studio.ready_to_publish_total || 0, note: 'Studio drafts that already satisfy governance and structural gates.', tone: 'success' },
      { label: 'Structural review', value: studio.structural_guarded_total || 0, note: 'Drafts in guarded PT-OSS review before they can enter the publish lane.', tone: (studio.structural_guarded_total || 0) ? 'warning' : 'default' },
      { label: 'Revision load', value: studio.revisions_total || 0, note: 'Total revision volume currently inside the governed authoring loop.', tone: 'accent' },
    ];
  }
  if (state.view === 'human_ask') {
    return [
      { label: 'Recorded sessions', value: humanAsk.recorded_total || 0, note: 'Report and meeting records preserved by the Director surface.', tone: 'accent' },
      { label: 'Human boundary', value: humanAsk.waiting_human_total || 0, note: 'Sessions only waiting because they crossed scope or reserved decision boundaries.', tone: (humanAsk.waiting_human_total || 0) ? 'warning' : 'success' },
      { label: 'Callable hats', value: humanAsk.callable_total || 0, note: 'Roles or drafts that the Director can currently use for records.', tone: 'success' },
    ];
  }
  if (state.view === 'sessions') {
    return [
      { label: 'Profiles', value: summary.requests_total ? access.profiles_total || 0 : access.profiles_total || 0, note: 'Configured access profiles visible to the private server.', tone: 'accent' },
      { label: 'Active sessions', value: access.sessions_active || 0, note: 'Short-lived sessions currently valid in the runtime.', tone: 'success' },
      { label: 'Revoked sessions', value: access.sessions_revoked || 0, note: 'Revocation count visible in session control history.', tone: (access.sessions_revoked || 0) ? 'warning' : 'default' },
    ];
  }
  if (state.view === 'policies') {
    return [
      { label: 'Role packs', value: (snapshot.roles || []).length, note: 'Trusted hats currently available to the Director.', tone: 'accent' },
      { label: 'Manifest trust', value: runtimeHealth.trusted_registry?.signature_status || 'unknown', note: 'Registry signature posture for the live PTAG library.', tone: runtimeHealth.trusted_registry?.signature_status === 'verified' ? 'success' : 'warning' },
      { label: 'Hierarchy map', value: runtimeHealth.role_hierarchy?.roles_total || 0, note: 'Roles currently visible in the runtime authority graph.', tone: 'default' },
    ];
  }
  if (state.view === 'health') {
    return [
      { label: 'Go-live', value: goLive.status || 'blocked', note: 'Production readiness status of the private server right now.', tone: goLive.status === 'ready' ? 'success' : goLive.status === 'guarded' ? 'warning' : 'danger' },
      { label: 'Plain file tokens', value: access.plain_file_tokens || 0, note: 'This should trend to zero in hardened deployments.', tone: (access.plain_file_tokens || 0) ? 'danger' : 'success' },
      { label: 'Privileged ops', value: privilegedOperations.status || 'unknown', note: 'Whether non-owner profiles can operate privileged runtime surfaces.', tone: privilegedOperations.status === 'ok' ? 'success' : privilegedOperations.status === 'warning' ? 'warning' : 'danger' },
    ];
  }
  return [];
}

function buildWorkflowGuide(snapshot) {
  const summary = snapshot.summary || {};
  const studio = snapshot.role_private_studio?.summary || {};
  const humanAsk = snapshot.human_ask?.summary || {};
  const runtimeHealth = snapshot.runtime_health || {};
  const goLive = snapshot.go_live_readiness || runtimeHealth.go_live_readiness || {};
  const audit = runtimeHealth.audit_integrity || {};
  const trustedRegistry = runtimeHealth.trusted_registry || {};
  const requests = snapshot.requests || [];
  const overrides = snapshot.overrides || [];
  const roles = snapshot.roles || [];
  const caseSummary = snapshot.cases?.summary || {};
  const caseItems = Array.isArray(snapshot.cases?.items) ? snapshot.cases.items : [];
  const pendingOverrides = overrides.filter((item) => item.status === 'pending').length;
  const conflicts = requests.filter((item) => item.outcome === 'conflicted').length;
  const validationIssueTotal = roles.reduce((sum, role) => sum + ((role.validation_issues || []).length), 0);
  const related = [];
  let primary = null;

  if (state.view === 'cases') {
    const leadCase = caseItems[0] || null;
    if (leadCase) {
      const leadView = leadCase.primary_view || 'requests';
      primary = {
        view: leadView,
        eyebrow: 'Next governed move',
        title: 'Open the lead operating lane for the current case',
        detail: 'Cases group requests, approvals, Human Ask records, and audit proof so the next move stays attached to the same governed issue.',
        badge: leadCase.status || 'monitoring',
        actionLabel: `Open ${VIEW_TITLES[leadView] || leadView}`,
        details: [
          ['Case', leadCase.case_id || '-'],
          ['Timeline events', String(leadCase.timeline_total || 0)],
          ['Linked requests', String((leadCase.linked_request_ids || []).length)],
        ],
      };
      const relatedViews = [leadView, 'requests', 'overrides', 'human_ask', 'audit'].filter((value, index, array) => value && array.indexOf(value) === index && value !== leadView);
      related.push(...relatedViews.slice(0, 3).map((view) => ({
        view,
        eyebrow: 'Related view',
        note: 'Open the matching lane to keep the case, decision, and evidence story connected.',
        actionLabel: `Open ${VIEW_TITLES[view] || view}`,
      })));
    } else {
      primary = {
        view: 'requests',
        eyebrow: 'Next governed move',
        title: 'Start from Requests to create the first linked case',
        detail: 'Once a governed request, Human Ask record, or studio activity is recorded, this view will group the issue into one readable case.',
        badge: 'start case',
        actionLabel: 'Open Requests',
      };
      related.push({ view: 'overview', eyebrow: 'Related view', note: 'Overview is still the fastest place to read current runtime posture.', actionLabel: 'Open Overview' });
    }
  }

  if (state.view === 'overview') {
    if ((goLive.status || 'blocked') !== 'ready' || (summary.runtime_alert_total || 0)) {
      primary = {
        view: 'health',
        eyebrow: 'Next governed move',
        title: 'Inspect runtime readiness before trusting the posture',
        detail: 'Overview has surfaced a guarded or blocked runtime condition. Confirm the exact domain in Runtime Health before treating the Director as stable.',
        badge: 'runtime check',
        actionLabel: 'Open Runtime Health',
        details: [
          ['Go-live', goLive.status || 'blocked'],
          ['Runtime alerts', String(summary.runtime_alert_total || 0)],
        ],
      };
    } else if (pendingOverrides) {
      primary = {
        view: 'overrides',
        eyebrow: 'Next governed move',
        title: 'Clear the human queue before work drifts',
        detail: 'Runtime posture is readable, but there are still approvals waiting on a human decision. Resolve the queue so automation can continue safely.',
        badge: 'human boundary',
        actionLabel: 'Open Overrides',
        details: [['Pending overrides', String(pendingOverrides)]],
      };
    } else {
      primary = {
        view: 'requests',
        eyebrow: 'Next governed move',
        title: 'Move from posture into active governed work',
        detail: 'The system scan is stable enough to begin or trace governed demand through the request lane.',
        badge: 'start work',
        actionLabel: 'Open Requests',
        details: [['Active requests', String(summary.requests_total || requests.length)]],
      };
    }
    addWorkflowLink(related, 'requests', 'Open intake', 'Create or trace governed work after the posture scan.');
    addWorkflowLink(related, 'overrides', 'Review queue', 'Check whether human approvals are holding the runtime.');
    addWorkflowLink(related, 'audit', 'Inspect evidence', 'Confirm the reason and proof behind the current posture.');
  } else if (state.view === 'requests') {
    if (pendingOverrides) {
      primary = {
        view: 'overrides',
        eyebrow: 'Next governed move',
        title: 'A request crossed a human boundary',
        detail: 'Some governed requests cannot continue autonomously. Resolve the pending approvals before expecting downstream progress.',
        badge: 'approval lane',
        actionLabel: 'Open Overrides',
        details: [['Pending overrides', String(pendingOverrides)]],
      };
    } else if (conflicts) {
      primary = {
        view: 'conflicts',
        eyebrow: 'Next governed move',
        title: 'Resolve contention before retrying work',
        detail: 'Requests are colliding with locks or consistency pressure. Review the conflict lane before resubmitting or escalating.',
        badge: 'contention',
        actionLabel: 'Open Conflicts & Locks',
        details: [['Conflicted requests', String(conflicts)]],
      };
    } else {
      primary = {
        view: 'audit',
        eyebrow: 'Next governed move',
        title: 'Confirm the result in the audit trail',
        detail: 'Intake looks healthy. Use Audit Trail to prove what happened, what policy applied, and what evidence was captured.',
        badge: 'evidence',
        actionLabel: 'Open Audit Trail',
        details: [['Requests in view', String(summary.requests_total || requests.length)]],
      };
    }
    addWorkflowLink(related, 'overview', 'Back to overview', 'Return to the posture scan when the queue changes.');
    addWorkflowLink(related, 'audit', 'Review evidence', 'Trace reason, decision path, and chain integrity for request outcomes.');
    addWorkflowLink(related, 'policies', 'Inspect boundaries', 'Check authority and role packs behind routed work.');
  } else if (state.view === 'overrides') {
    primary = pendingOverrides
      ? {
          view: 'overrides',
          eyebrow: 'Next governed move',
          title: 'Stay in the approval lane until the queue is clear',
          detail: 'This is the right place while pending approvals remain. Work the queue, record rationale, then verify the result elsewhere.',
          badge: 'approve or veto',
          actionLabel: 'Continue reviewing here',
          details: [['Pending overrides', String(pendingOverrides)]],
        }
      : {
          view: 'audit',
          eyebrow: 'Next governed move',
          title: 'Queue is clear, now verify the governed outcome',
          detail: 'Once the approval queue is empty, confirm the audit trail and downstream runtime posture.',
          badge: 'evidence',
          actionLabel: 'Open Audit Trail',
        };
    addWorkflowLink(related, 'requests', 'Back to requests', 'Return to intake to confirm which request triggered the boundary.');
    addWorkflowLink(related, 'audit', 'Confirm evidence', 'Review the proof bundle and final queue outcome.');
    addWorkflowLink(related, 'overview', 'Check posture', 'See whether the Director is still calm, guarded, or blocked after review.');
  } else if (state.view === 'conflicts') {
    primary = conflicts
      ? {
          view: 'requests',
          eyebrow: 'Next governed move',
          title: 'Trace the blocked request lane',
          detail: 'Conflict handling starts by identifying which request stalled and whether it should retry, wait, or escalate.',
          badge: 'request trace',
          actionLabel: 'Open Requests',
          details: [['Conflicted requests', String(conflicts)]],
        }
      : {
          view: 'health',
          eyebrow: 'Next governed move',
          title: 'Contention is quiet, confirm runtime stability',
          detail: 'If no requests are colliding right now, Runtime Health is the next best place to verify storage and lock posture.',
          badge: 'runtime check',
          actionLabel: 'Open Runtime Health',
        };
    addWorkflowLink(related, 'requests', 'Trace requests', 'Follow the blocked request back to its governed intake record.');
    addWorkflowLink(related, 'health', 'Inspect runtime', 'Review lock store, consistency, and storage posture.');
    addWorkflowLink(related, 'audit', 'Check history', 'Confirm when the contention surfaced and how it was handled.');
  } else if (state.view === 'audit') {
    if ((audit.hash_mismatches || 0) || audit.status === 'warning') {
      primary = {
        view: 'health',
        eyebrow: 'Next governed move',
        title: 'Audit needs runtime repair context',
        detail: 'Evidence integrity is not fully clean. Move into Runtime Health to confirm which runtime domain needs repair or resealing.',
        badge: 'integrity watch',
        actionLabel: 'Open Runtime Health',
        details: [
          ['Integrity', audit.status || 'unknown'],
          ['Hash mismatches', String(audit.hash_mismatches || 0)],
        ],
      };
    } else {
      primary = {
        view: 'overview',
        eyebrow: 'Next governed move',
        title: 'Return to the executive posture scan',
        detail: 'Audit is clean. Go back to Overview to see the current posture with evidence already confirmed.',
        badge: 'posture scan',
        actionLabel: 'Open Overview',
      };
    }
    addWorkflowLink(related, 'requests', 'Back to intake', 'Reconnect evidence with the request or action that produced it.');
    addWorkflowLink(related, 'overrides', 'Review boundary', 'Inspect the human decision path behind approved or vetoed work.');
    addWorkflowLink(related, 'health', 'Inspect runtime', 'Use health when chain integrity or trust posture needs operator repair.');
  } else if (state.view === 'studio') {
    primary = (studio.ready_to_publish_total || 0)
      ? {
          view: 'studio',
          eyebrow: 'Next governed move',
          title: 'Finish the publication lane from this view',
          detail: 'You already have drafts that are structurally ready. Complete the publish review here, then verify the live role library.',
          badge: 'publish lane',
          actionLabel: 'Continue publishing here',
          details: [['Ready to publish', String(studio.ready_to_publish_total || 0)]],
        }
      : {
          view: 'policies',
          eyebrow: 'Next governed move',
          title: 'Inspect the live role library after authoring',
          detail: 'When no draft is publication-ready, switch to Roles & Policies to confirm what is already trusted and active.',
          badge: 'role library',
          actionLabel: 'Open Roles & Policies',
        };
    addWorkflowLink(related, 'policies', 'Open live library', 'Compare drafts against the published, trusted role packs.');
    addWorkflowLink(related, 'human_ask', 'Open governed record', 'Call a draft or published hat into a governed report lane.');
    addWorkflowLink(related, 'audit', 'Check evidence', 'Review trusted registry and publication evidence after changes.');
  } else if (state.view === 'human_ask') {
    primary = (humanAsk.waiting_human_total || 0)
      ? {
          view: 'overrides',
          eyebrow: 'Next governed move',
          title: 'Some records need a human decision',
          detail: 'A Human Ask record crossed a human-only boundary. Move to Overrides to resolve the blocked lane before opening new follow-ups.',
          badge: 'human boundary',
          actionLabel: 'Open Overrides',
          details: [['Waiting human', String(humanAsk.waiting_human_total || 0)]],
        }
      : {
          view: 'audit',
          eyebrow: 'Next governed move',
          title: 'Review the record trail and captured evidence',
          detail: 'The record lane is open and governed. Audit Trail is the next step when you need proof, history, or reasoning behind a response.',
          badge: 'record evidence',
          actionLabel: 'Open Audit Trail',
          details: [['Recorded sessions', String(humanAsk.recorded_total || 0)]],
        };
    addWorkflowLink(related, 'policies', 'Inspect roles', 'Check which hat boundaries and authority rules shaped the record.');
    addWorkflowLink(related, 'sessions', 'Check session posture', 'Review access continuity and revocation around human-facing runtime use.');
    addWorkflowLink(related, 'studio', 'Open Studio', 'Move back to role authoring when the record points to a hat gap.');
  } else if (state.view === 'sessions') {
    primary = {
      view: 'audit',
      eyebrow: 'Next governed move',
      title: 'Pair session posture with evidence',
      detail: 'Session control tells you who still has access. Audit Trail tells you what happened while that access existed.',
      badge: 'access evidence',
      actionLabel: 'Open Audit Trail',
      details: [['Active sessions', String(runtimeHealth.access_control?.sessions_active || 0)]],
    };
    addWorkflowLink(related, 'health', 'Check runtime health', 'Review token storage, session store, and access-control posture.');
    addWorkflowLink(related, 'overview', 'Back to overview', 'Return to the executive posture scan after access review.');
    addWorkflowLink(related, 'human_ask', 'Open records', 'Trace how governed record activity maps to session continuity.');
  } else if (state.view === 'policies') {
    primary = validationIssueTotal
      ? {
          view: 'studio',
          eyebrow: 'Next governed move',
          title: 'Policy issues usually route back to authoring',
          detail: 'Live role packs show validation issues or trust friction. Return to Studio to repair the hat before expecting safe runtime use.',
          badge: 'authoring repair',
          actionLabel: 'Open Role Private Studio',
          details: [['Validation issues', String(validationIssueTotal)]],
        }
      : {
          view: 'requests',
          eyebrow: 'Next governed move',
          title: 'Policies look trusted, now exercise them through work',
          detail: 'When the library looks clean, the next step is to use the hats through governed requests or records.',
          badge: 'use the library',
          actionLabel: 'Open Requests',
          details: [['Role packs', String(roles.length)]],
        };
    addWorkflowLink(related, 'studio', 'Repair or publish', 'Change a hat when the live contract is incomplete or guarded.');
    addWorkflowLink(related, 'audit', 'Check trust trail', 'Confirm manifest, hierarchy, and trusted-registry evidence.');
    addWorkflowLink(related, 'human_ask', 'Use a hat', 'Open a governed record against the active role library.');
  } else if (state.view === 'health') {
    if ((trustedRegistry.signature_status || 'unknown') !== 'verified' || (audit.hash_mismatches || 0)) {
      primary = {
        view: 'audit',
        eyebrow: 'Next governed move',
        title: 'Runtime health points back to trusted evidence',
        detail: 'Trust or integrity posture is not fully clean. Use Audit Trail to inspect the underlying proof chain before treating the runtime as repaired.',
        badge: 'trust evidence',
        actionLabel: 'Open Audit Trail',
        details: [
          ['Trusted registry', trustedRegistry.signature_status || 'unknown'],
          ['Hash mismatches', String(audit.hash_mismatches || 0)],
        ],
      };
    } else {
      primary = {
        view: 'overview',
        eyebrow: 'Next governed move',
        title: 'Health looks readable, return to the top-level posture',
        detail: 'Once runtime domains are understood, Overview becomes the fastest place to judge whether operations can continue safely.',
        badge: 'executive posture',
        actionLabel: 'Open Overview',
        details: [['Go-live', goLive.status || 'blocked']],
      };
    }
    addWorkflowLink(related, 'audit', 'Inspect evidence', 'Pair domain health with the trusted audit trail.');
    addWorkflowLink(related, 'policies', 'Inspect live library', 'Check the role and registry side of runtime readiness.');
    addWorkflowLink(related, 'sessions', 'Review access', 'Verify session posture when operator runtime behavior feels off.');
  }

  const workflowGuide = applyActionContextToWorkflowGuide(primary, related.filter((item) => item.view !== state.view));
  return {
    primary: workflowGuide.primary,
    related: workflowGuide.related.slice(0, 3),
  };
}

function addWorkflowLink(target, view, actionLabel, note, eyebrow = 'Related view') {
  if (!view || target.some((item) => item.view === view)) return;
  target.push({ view, actionLabel, note, eyebrow });
}

function applyActionContextToWorkflowGuide(primary, related) {
  const context = state.actionContext;
  if (!context || !context.view) return { primary, related };

  const contextView = context.view;
  const contextViewLabel = VIEW_TITLES[contextView] || titleCase(contextView);
  const continuityPrimary = contextView === state.view
    ? {
        view: contextView,
        eyebrow: 'Latest governed result',
        title: context.title || `Continue inside ${contextViewLabel}`,
        detail: context.detail || 'The latest affected work item is highlighted in this lane so you can continue without searching for it again.',
        badge: 'highlighted item',
        actionLabel: 'Continue in this lane',
        details: [
          ['Surface', contextViewLabel],
          ['Reference', context.entityId || '-'],
        ],
      }
    : {
        view: contextView,
        eyebrow: 'Latest governed result',
        title: context.title || `Continue in ${contextViewLabel}`,
        detail: context.detail || 'The latest affected governed item remains highlighted in the next lane so you can continue without searching for it.',
        badge: 'continue flow',
        actionLabel: context.actionLabel || `Open ${contextViewLabel}`,
        details: [
          ['Next lane', contextViewLabel],
          ['Reference', context.entityId || '-'],
        ],
      };

  const nextRelated = Array.isArray(related) ? [...related] : [];
  if (primary && primary.view && primary.view !== contextView) {
    addWorkflowLink(nextRelated, primary.view, primary.actionLabel || `Open ${VIEW_TITLES[primary.view] || primary.view}`, primary.detail || 'Return to the normal governed workflow suggestion for this lane.', primary.eyebrow || 'Workflow suggestion');
  }

  if (contextView !== state.view) {
    addWorkflowLink(nextRelated, state.view, `Back to ${VIEW_TITLES[state.view] || state.view}`, 'Return to the current lane after checking the latest affected governed result.', 'Current lane');
  }

  if (contextView !== 'audit') {
    addWorkflowLink(nextRelated, 'audit', 'Open Audit Trail', 'Confirm the result, policy basis, and evidence after following the latest action path.', 'Proof lane');
  }

  return {
    primary: continuityPrimary,
    related: nextRelated.filter((item) => item.view !== continuityPrimary.view),
  };
}

function getActionContextCaseId() {
  const context = state.actionContext || {};
  if (context.caseId) return String(context.caseId).trim();
  if (context.entityType === 'case' && context.entityId) return String(context.entityId).trim();
  return '';
}

function isCaseScopedView(view = state.view) {
  return ['requests', 'overrides', 'conflicts', 'audit', 'studio', 'human_ask'].includes(String(view || '').trim());
}

function getCaseById(snapshot, caseId = '') {
  const normalizedCaseId = String(caseId || '').trim();
  if (!normalizedCaseId) return null;
  const items = Array.isArray(snapshot?.cases?.items) ? snapshot.cases.items : [];
  return items.find((item) => String(item.case_id || '').trim() === normalizedCaseId) || null;
}

function filterRowsByCase(rows, caseId = '') {
  const normalizedCaseId = String(caseId || '').trim();
  if (!normalizedCaseId || !Array.isArray(rows)) return Array.isArray(rows) ? rows : [];
  return rows.filter((row) => String(row?.case_id || '').trim() === normalizedCaseId);
}

function getCurrentViewCaseLinkedTotal(item) {
  if (!item || typeof item !== 'object') return 0;
  if (state.view === 'requests') return Array.isArray(item.linked_request_ids) ? item.linked_request_ids.length : 0;
  if (state.view === 'overrides') return Array.isArray(item.linked_override_ids) ? item.linked_override_ids.length : 0;
  if (state.view === 'conflicts') return Array.isArray(item.linked_request_ids) ? item.linked_request_ids.length : 0;
  if (state.view === 'audit') return Number(item.audit_event_total || 0);
  if (state.view === 'studio') return Array.isArray(item.linked_studio_request_ids) ? item.linked_studio_request_ids.length : 0;
  if (state.view === 'human_ask') return Array.isArray(item.linked_session_ids) ? item.linked_session_ids.length : 0;
  return 0;
}

function getCaseScopedSnapshot(snapshot) {
  const caseId = getActionContextCaseId();
  if (!caseId || !isCaseScopedView(state.view)) return snapshot;
  const item = getCaseById(snapshot, caseId);
  if (!item) return snapshot;
  const requestIds = new Set(Array.isArray(item.linked_request_ids) ? item.linked_request_ids.map((value) => String(value)) : []);
  const overrideIds = new Set(Array.isArray(item.linked_override_ids) ? item.linked_override_ids.map((value) => String(value)) : []);
  const scopedLocks = Array.isArray(snapshot.locks)
    ? snapshot.locks.filter((row) => {
        const ownerRequestId = String(row?.owner_request_id || row?.request_id || '').trim();
        return ownerRequestId ? (requestIds.has(ownerRequestId) || overrideIds.has(ownerRequestId)) : false;
      })
    : [];
  return {
    ...snapshot,
    requests: filterRowsByCase(snapshot.requests || [], caseId),
    overrides: filterRowsByCase(snapshot.overrides || [], caseId),
    audit: filterRowsByCase(snapshot.audit || [], caseId),
    locks: scopedLocks,
    human_ask: snapshot.human_ask
      ? {
          ...snapshot.human_ask,
          sessions: filterRowsByCase(snapshot.human_ask.sessions || [], caseId),
        }
      : snapshot.human_ask,
    role_private_studio: snapshot.role_private_studio
      ? {
          ...snapshot.role_private_studio,
          requests: filterRowsByCase(snapshot.role_private_studio.requests || [], caseId),
        }
      : snapshot.role_private_studio,
  };
}

function renderCaseSpotlight(snapshot) {
  if (!isCaseScopedView(state.view)) return '';
  const caseId = getActionContextCaseId();
  if (!caseId) return '';
  const item = getCaseById(snapshot, caseId);
  if (!item) return '';
  const continuity = item.continuity || {};
  const primaryView = item.primary_view || continuity.next_view || 'requests';
  const primaryViewLabel = VIEW_TITLES[primaryView] || titleCase(primaryView || 'overview');
  const currentViewLabel = VIEW_TITLES[state.view] || titleCase(state.view || 'overview');
  const currentViewLinkedTotal = getCurrentViewCaseLinkedTotal(item);
  const primaryFocus = resolveCasePrimaryFocus(item, primaryView);
  const proofLabel = item.workflow_proof_total > 0
    ? 'workflow proof attached'
    : item.evidence_export_total > 0
      ? 'evidence export recorded'
      : 'proof still building';
  return `
    <section class="card stack case-spotlight-card${isFocusedEntity('case', item.case_id) ? ' focused-record' : ''}" data-focus-alt-key="${escapeHtml(buildFocusKey('case', item.case_id))}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Case in motion</div>
          <h3 class="card-title">${escapeHtml(item.case_id || 'Governed case')}</h3>
          <p class="card-subtitle">${escapeHtml(`The work ledger below is filtered to this case inside ${currentViewLabel}. ${continuity.next_detail || 'Keep the next action tied to the same governed issue so context, proof, and approvals stay connected.'}`)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(item.status || 'monitoring')}${statusBadge(proofLabel)}</div>
      </div>
      ${keyValue([
        ['Current lane', `${currentViewLabel} | ${String(currentViewLinkedTotal)} linked items`],
        ['Primary lane', primaryViewLabel],
        ['Next move', continuity.next_label || 'Continue governed work'],
        ['Audit events', String(item.audit_event_total || 0)],
        ['Workflow proof', String(item.workflow_proof_total || 0)],
      ])}
      <div class="inline-actions">
        <button class="action-button" type="button" ${buildViewJumpAttributes({
          view: primaryView,
          focusType: primaryFocus.entityType,
          focusId: primaryFocus.entityId,
          caseId: item.case_id,
          title: item.case_id ? `Case ${item.case_id} opened in ${primaryViewLabel}.` : `Opened ${primaryViewLabel}.`,
          detail: continuity.next_detail || 'The linked work item stays highlighted in its operating lane so you can continue from the same governed issue.',
          actionLabel: `Open ${primaryViewLabel}`,
        })}>${escapeHtml(`Continue in ${primaryViewLabel}`)}</button>
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view: 'cases',
          focusType: 'case',
          focusId: item.case_id,
          caseId: item.case_id,
          title: item.case_id ? `Case ${item.case_id} reopened in Cases.` : 'Opened Cases.',
          detail: 'Return to the canonical case lane when you need the full linked work, timeline, and proof story again.',
          actionLabel: 'Open Cases',
        })}>Open Cases</button>
        <button class="action-button action-button-muted" type="button" data-case-scope-clear="true">Show full ${escapeHtml(currentViewLabel)}</button>
      </div>
    </section>
  `;
}

function studioReadinessTone(readiness) {
  const status = String(readiness?.status || 'blocked');
  if (status === 'published' || status === 'ready') return 'success';
  if (status === 'guarded') return 'warning';
  return 'danger';
}

function updateNav() {
  for (const item of navList.querySelectorAll('.nav-item')) {
    const isActive = item.dataset.view === state.view;
    item.classList.toggle('is-active', isActive);
    item.setAttribute('aria-current', isActive ? 'page' : 'false');
  }
}

function renderAuthCard() {
  const laneCards = Object.entries(DEV_LANES).map(([laneKey, lane]) => `
    <article class="mini-card stack lane-card">
      <div>
        <strong>${escapeHtml(lane.title)}</strong>
        <p class="muted">${escapeHtml(lane.summary)}</p>
      </div>
      <div class="lane-chip-row">
        ${statusBadge(VIEW_TITLES[lane.view] || lane.view)}
        <span class="pill lane-token-pill">${escapeHtml(lane.token)}</span>
      </div>
      <p class="muted lane-followup">${escapeHtml(lane.followup)}</p>
      <div class="inline-actions">
        <button class="action-button action-button-muted" type="button" data-dev-lane="${escapeHtml(laneKey)}">Use ${escapeHtml(lane.title.toLowerCase())}</button>
      </div>
    </article>
  `).join('');
  return `
    <article class="card auth-card stack">
      <div>
        <div class="eyebrow muted">Private API Access</div>
        <h3 class="card-title">Connect to the governed private runtime</h3>
        <p class="card-subtitle">Use a SA-NOM server token to exchange for a short-lived session. For local evaluation, choose a lane below and the dashboard will start in the view that fits that role.</p>
      </div>
      <form id="token-form" class="auth-form">
        <input id="token-input" type="password" placeholder="SA-NOM API token" value="${escapeHtml(state.token)}" autofocus />
        <div class="inline-actions"><button class="action-button" type="submit">Connect</button></div>
      </form>
      <div class="onboarding-grid lane-picker-grid">${laneCards}</div>
      <div class="trace-box">
        <strong>Development tokens</strong>
        <p class="muted">Owner: sanom-dev-token, Operator: sanom-operator-token, Reviewer: sanom-reviewer-token, Auditor: sanom-auditor-token, Viewer: sanom-viewer-token</p>
      </div>
      <div class="trace-box">
        <strong>First-run path</strong>
        <p class="muted">1. Start with the Viewer lane to inspect Overview, Health, and Audit. 2. Switch to the Operator lane to submit or inspect governed runtime work. 3. Use the Reviewer lane when you want to finish a human-required approval or veto with rationale.</p>
      </div>
      <div class="trace-box">
        <strong>Manual token entry still works</strong>
        <p class="muted">If you already have an owner-issued token, paste it directly above. Lane buttons are only a shortcut for local evaluation and development tokens.</p>
      </div>
      <div class="trace-box">
        <strong>Private deployment note</strong>
        <p class="muted">These tokens are for local development and evaluation only. In a real private deployment, access should be issued by the runtime owner or platform administrator and mapped to an approved role.</p>
      </div>
      ${state.lastError ? `<div class="trace-box"><strong>Access error</strong><p class="muted">${escapeHtml(state.lastError)}</p></div>` : ''}
    </article>
  `;
}

function renderPermissionNotice(permission) {
  const currentRole = state.session ? state.session.role_name : 'unknown';
  const recommendedLanes = [
    DEV_LANES.viewer,
    DEV_LANES.operator,
    DEV_LANES.reviewer,
  ].map((lane) => `
    <article class="mini-card stack lane-card permission-lane-card">
      <div>
        <strong>${escapeHtml(lane.title)}</strong>
        <p class="muted">${escapeHtml(lane.summary)}</p>
      </div>
      <div class="lane-chip-row">
        ${statusBadge(VIEW_TITLES[lane.view] || lane.view)}
        <span class="pill lane-token-pill">${escapeHtml(lane.token)}</span>
      </div>
      <div class="inline-actions">
        <button class="action-button action-button-muted" type="button" data-dev-lane="${escapeHtml(Object.keys(DEV_LANES).find((key) => DEV_LANES[key] === lane) || '')}">Switch to ${escapeHtml(lane.title.toLowerCase())}</button>
      </div>
    </article>
  `).join('');
  return `
    <article class="card notice-card notice-warning stack">
      <div>
        <div class="eyebrow muted">Access restricted</div>
        <h3 class="card-title">Current profile cannot open this view</h3>
        <p class="card-subtitle">The active session is missing the required permission. Switch to the lane that matches the work you want to inspect instead of guessing where the runtime put the decision.</p>
      </div>
      ${keyValue([
        ['Required permission', permission],
        ['Current profile', state.session ? state.session.display_name : 'unknown'],
        ['Role', currentRole],
        ['Suggested next step', 'Switch to the lane that owns this governed view or go back to Overview for a broader runtime scan'],
      ])}
      <div class="trace-box">
        <strong>Common lane mapping</strong>
        <p class="muted">Viewer is best for Overview, Health, and Audit. Operator is best for Requests and flow inspection. Reviewer is best for Overrides and human-required decisions.</p>
      </div>
      <div class="onboarding-grid lane-picker-grid permission-lane-grid">${recommendedLanes}</div>
      <div class="inline-actions">
        <button class="action-button" type="button" data-view-jump="overview">Open Overview</button>
      </div>
    </article>
  `;
}

function renderOverview(snapshot) {
  const readiness = snapshot.go_live_readiness || {};
  const operationalReadiness = snapshot.operational_readiness || {};
  const firstRunReadiness = snapshot.first_run_readiness || {};
  const latestBackup = snapshot.operations?.summary?.latest_backup || null;
  const runtimeHealth = snapshot.runtime_health || {};
  const auditIntegrity = runtimeHealth.audit_integrity || {};
  const integrations = snapshot.integrations || {};
  const integrationSummary = integrations.summary || {};
  const operatorQueueHealth = snapshot.operator_queue_health || { items: [], policy: {} };
  const operatorNotificationCenter = snapshot.operator_notification_center || { items: [], policy: {} };
  const operatorNotificationDeliveryReadiness = snapshot.operator_notification_delivery_readiness || {};
  const runtimeAlerts = Array.isArray(snapshot.runtime_alerts) ? snapshot.runtime_alerts.slice(0, 4) : [];
  const backupLabel = latestBackup ? `${latestBackup.backup_id} | ${shortTime(latestBackup.created_at)}` : 'No runtime backup recorded yet.';
  const focusNote = state.lastError || 'All executive actions route through a governed runtime with policy oversight.';
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow">Private Governance Runtime</div>
            <h3 class="hero-title">Executive command surface for governed AI operations.</h3>
            <p class="hero-subtitle">Live oversight across runtime integrity, human approvals, role authoring, and operational continuity for SA-NOM AI Governance Suite.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(readiness.status || snapshot.summary.go_live_status || 'blocked')}
            <span class="pill">PTAG governed</span>
          </div>
        </div>
        <div class="hero-split">
          <div class="hero-note">
            <strong>Executive note</strong>
            <p>${escapeHtml(focusNote)}</p>
          </div>
          ${keyValue([
            ['Go-live', String(Boolean(readiness.ready))],
            ['Audit integrity', auditIntegrity.status || 'unknown'],
            ['PTAG role packs', String((snapshot.roles || []).length)],
            ['Active sessions', String((snapshot.sessions || []).length)],
          ])}
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Operational posture</div>
          <h3 class="card-title">Priority focus</h3>
          <p class="card-subtitle">Backup continuity, runtime pressure points, and publish readiness for the next governed role.</p>
        </div>
        ${keyValue([
          ['Operational readiness', operationalReadiness.status || snapshot.summary.operational_readiness_status || 'unknown'],
          ['First-run readiness', firstRunReadiness.status || snapshot.summary.first_run_readiness_status || 'blocked'],
          ['Workflow backlog', String(snapshot.summary.workflow_backlog_total || 0)],
          ['Human inbox open', String(snapshot.summary.human_inbox_open_total || 0)],
          ['Recovery pending', String(snapshot.summary.recovery_pending_total || 0)],
          ['Dead letters', String(snapshot.summary.dead_letter_total || 0)],
          ['Human-required lanes', String(snapshot.summary.operator_human_required_total || 0)],
          ['Blocked lanes', String(snapshot.summary.operator_blocked_total || 0)],
        ])}
        <div class="trace-box"><strong>Latest backup</strong><p class="muted">${escapeHtml(backupLabel)}</p></div>
      </article>
    </section>
      <section class="metrics-grid metrics-grid-luxury">
        ${metricCard('Requests', snapshot.summary.requests_total, 'default', 'Governed runtime submissions in the current live view.')}
      ${metricCard('Cases', snapshot.summary.cases_total || 0, 'accent', 'Linked governed issues tracked across request, approval, record, and evidence lanes.')}
        ${metricCard('Runtime alerts', snapshot.summary.runtime_alert_total || runtimeAlerts.length, (snapshot.summary.runtime_alert_critical_total || 0) ? 'danger' : (snapshot.summary.runtime_alert_total || runtimeAlerts.length) ? 'warning' : 'success', 'Conditions where the Director paused or governance pressure is still active.')}
        ${metricCard('Pending overrides', snapshot.summary.pending_overrides, 'warning', 'Human approvals waiting in the executive queue.')}
        ${metricCard('Active locks', snapshot.summary.active_locks, 'accent', 'Resources currently protected from conflicting execution.')}
        ${metricCard('Conflicts', snapshot.summary.conflicts_total, 'danger', 'Requests blocked by concurrency or governance contention.')}
        ${metricCard('Studio requests', snapshot.summary.studio_requests_total || 0, 'default', 'Role Private Studio drafts under review.')}
        ${metricCard('Studio ready', snapshot.summary.studio_ready_to_publish_total || 0, 'success', 'Role drafts ready for trusted publication.')}
        ${metricCard('Go-live', readiness.status || snapshot.summary.go_live_status || 'blocked', 'accent', 'Combined deployment gate across trust, smoke, and audit.')}
        ${metricCard('Operational readiness', operationalReadiness.status || snapshot.summary.operational_readiness_status || 'unknown', (operationalReadiness.status || snapshot.summary.operational_readiness_status) === 'ready' ? 'success' : ((operationalReadiness.status || snapshot.summary.operational_readiness_status) === 'monitoring' ? 'warning' : 'danger'), 'Operator-facing runtime posture across backlog, inbox, and recovery queues.')}
        ${metricCard('First-run blockers', snapshot.summary.first_run_blockers_total || 0, (snapshot.summary.first_run_blockers_total || 0) ? 'danger' : ((snapshot.summary.first_run_advisories_total || 0) ? 'warning' : 'success'), 'Blocking checks that still prevent a clean 5-10 minute first run.')}
        ${metricCard('Backups', snapshot.summary.backups_total || 0, 'default', 'Operational recovery bundles captured from the private runtime.')}
        ${metricCard('Integrations', snapshot.summary.integration_targets_total || 0, 'accent', 'Configured outbound targets across webhook, SIEM, and ticketing lanes.')}
        ${metricCard('Outbound deliveries', snapshot.summary.integration_deliveries_total || 0, snapshot.summary.integration_failures_total ? 'warning' : 'success', 'Outbound integration delivery records currently visible in the runtime ledger.')}
        ${metricCard('Operator attention', snapshot.summary.operator_attention_total || 0, (snapshot.summary.operator_attention_total || 0) ? 'warning' : 'success', 'Queue lanes that crossed the unified operator alert policy and now need attention.')}
      ${metricCard('Cases needing attention', snapshot.summary.cases_attention_total || 0, (snapshot.summary.cases_attention_total || 0) ? 'warning' : 'success', 'Cases that are blocked, waiting on a human, or need closer governed follow-through.')}
        ${metricCard('Operator critical', snapshot.summary.operator_critical_total || 0, (snapshot.summary.operator_critical_total || 0) ? 'danger' : 'success', 'Queue lanes that are critical or stale under the shared operator aging policy.')}
        ${metricCard('Notify candidates', snapshot.summary.operator_notification_candidates_total || 0, (snapshot.summary.operator_notification_candidates_total || 0) ? 'accent' : 'success', 'Queue lanes that would route through the unified operator notification plan.')}
      </section>
      ${renderUnifiedWorkInbox(snapshot)}
      ${renderOperatorNotificationPolicyCard(operatorNotificationCenter)}
      ${renderOperatorNotificationDeliveryCard(operatorNotificationCenter, integrations, operatorNotificationDeliveryReadiness)}
      ${renderFirstRunReadinessCard(firstRunReadiness)}
      ${renderOperatorDecisionLanes(snapshot.operator_decision_lanes || [])}
      ${renderNotificationCenter(runtimeAlerts)}
      <section class="split-grid">
        ${wrapTableCard('Recent Requests', requestTable((snapshot.requests || []).slice(0, 8)), 'Live governed requests with policy basis and consistency trace.') }
        <article class="card stack">
        <div><div class="eyebrow muted">Executive cadence</div><h3 class="card-title">Operator focus</h3><p class="card-subtitle">A concise view of the queues and assurances that matter before any privileged action is taken.</p></div>
        ${keyValue([
          ['Runtime backups', String(snapshot.summary.backups_total || 0)],
          ['Audit entries', String(snapshot.summary.audit_events || 0)],
          ['Review pack status', readiness.gates?.review_pack_present ? 'present' : 'missing'],
          ['Startup smoke', readiness.smoke_report?.status || '-'],
          ['Usability proof', snapshot.summary.usability_proof_status || 'missing'],
          ['Proof available', String(Boolean(snapshot.summary.usability_proof_available))],
          ['Proof criteria passed', `${snapshot.summary.usability_proof_criteria_passed_total || 0}/${snapshot.summary.usability_proof_criteria_total || 0}`],
          ['Proof criteria failed', `${snapshot.summary.usability_proof_criteria_failed_total || 0}`],
          ['Quick-start doctor', snapshot.summary.quick_start_doctor_status || 'missing'],
        ])}
        ${can('ops.manage') ? '<div class="inline-actions"><button class="action-button" data-ops-action="usability-proof">Generate Usability Proof</button><button class="action-button action-button-muted" data-ops-action="usability-proof-refresh">Refresh Latest Proof</button></div>' : ''}
      </article>
    </section>
      ${renderOwnerRegistrationPanel(snapshot.owner_registration || {}, { compact: true })}
      ${renderIntegrationSection(integrations)}
    `;
  }



function renderUnifiedWorkInbox(snapshot) {
  const inbox = snapshot.unified_work_inbox || { summary: {}, items: [] };
  const summary = inbox.summary || {};
  const items = Array.isArray(inbox.items) ? inbox.items.slice(0, 6) : [];
  if (!items.length) return '';
  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Unified Work Inbox</div>
          <h3 class="card-title">One work surface across approvals, blocked workflows, recovery, and studio promotion.</h3>
          <p class="card-subtitle">Use this as the executive queue: what needs a human now, what is blocked, and which governed lane is the best next move.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${summary.open_total || 0} open`)}${statusBadge(summary.primary_title || 'Autonomy ready')}</div>
      </div>
      ${keyValue([
        ['Open work', String(summary.open_total || 0)],
        ['Human required', String(summary.human_required_total || 0)],
        ['Blocked', String(summary.blocked_total || 0)],
        ['Monitoring', String(summary.monitoring_total || 0)],
        ['Ready lanes', String(summary.ready_total || 0)],
        ['Primary move', titleCase(summary.primary_view || 'overview')],
      ])}
      <div class="trace-box"><strong>Primary next move</strong><p class="muted">${escapeHtml(summary.primary_next_step || 'Continue governed execution.')}</p></div>
      <div class="view-prelude-grid">
        ${items.map((item) => renderUnifiedWorkInboxItem(item)).join('')}
      </div>
    </section>
  `;
}

function renderFocusedWorkInbox(snapshot, currentView) {
  const inbox = snapshot.unified_work_inbox || { summary: {}, items: [] };
  const summary = inbox.summary || {};
  const items = selectFocusedInboxItems(Array.isArray(inbox.items) ? inbox.items : [], currentView);
  if (!items.length) return '';
  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Next Governed Work</div>
          <h3 class="card-title">What matters most from this lane right now</h3>
          <p class="card-subtitle">Stay inside the current workflow, but keep the next human boundary or blocked path visible without going back to Overview.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(titleCase(currentView || 'overview'))}${statusBadge(`${summary.open_total || 0} open`)}</div>
      </div>
      <div class="view-prelude-grid">
        ${items.map((item) => renderUnifiedWorkInboxItem(item, { compact: true, currentView })).join('')}
      </div>
    </section>
  `;
}

function selectFocusedInboxItems(items, currentView) {
  if (!Array.isArray(items) || !items.length) return [];
  const relevant = items.filter((item) => item.view === currentView);
  if (relevant.length) return relevant.slice(0, 3);
  const primary = items[0] ? [items[0]] : [];
  const supporting = items.filter((item) => item.view !== currentView).slice(1, 3);
  return [...primary, ...supporting];
}

function renderUnifiedWorkInboxItem(item, { compact = false } = {}) {
  const refs = Array.isArray(item.sample_references) ? item.sample_references.slice(0, compact ? 2 : 3) : [];
  const toneClass = item.tone === 'danger'
    ? ' view-prelude-card-danger'
    : item.tone === 'warning'
      ? ' view-prelude-card-warning'
      : '';
  const queueSummary = `${item.total || 0} open | oldest about ${item.oldest_age_hours || 0}h | ref ${item.oldest_reference || '-'}`;
  return `
    <article class="view-prelude-card${toneClass}">
      <span class="view-prelude-label">${escapeHtml(titleCase(item.lane_id || 'lane'))}</span>
      <strong>${escapeHtml(item.title || 'Governed work lane')}</strong>
      <p class="muted">${escapeHtml(queueSummary)}</p>
      <div class="hero-chip-row">${statusBadge(item.disposition || 'monitoring')}${statusBadge(item.status || 'ready')}</div>
      <p class="muted">${escapeHtml(item.next_step || 'Review the next governed move.')}</p>
      ${refs.length ? `<div class="hero-chip-row">${refs.map((ref) => `<span class="pill">${escapeHtml(ref)}</span>`).join('')}</div>` : ''}
      <div class="inline-actions">
        <button class="action-button${compact ? ' action-button-muted' : ''}" type="button" data-view-jump="${escapeHtml(item.view || 'overview')}">${escapeHtml(item.action_label || `Open ${titleCase(item.view || 'overview')}`)}</button>
      </div>
    </article>
  `;
}


function renderFirstRunReadinessCard(firstRunReadiness) {
  if (!firstRunReadiness || typeof firstRunReadiness !== 'object') return '';
  const checks = Array.isArray(firstRunReadiness.checks) ? firstRunReadiness.checks : [];
  const blockers = checks.filter((item) => item.required && !item.passed);
  const advisories = checks.filter((item) => !item.required && !item.passed);
  const highlighted = blockers.length ? blockers.slice(0, 3) : advisories.slice(0, 3);
  const recommendedView = firstRunReadiness.recommended_view || 'overview';
  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">First-Run Control Plane</div>
          <h3 class="card-title">5-10 minute readiness gate</h3>
          <p class="card-subtitle">Deterministic startup checks for non-technical operators before they run live demo actions.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(firstRunReadiness.status || 'blocked')}</div>
      </div>
      ${keyValue([
        ['Status', String(firstRunReadiness.status || 'blocked')],
        ['Blockers', String(firstRunReadiness.blockers_total || blockers.length)],
        ['Advisories', String(firstRunReadiness.advisories_total || advisories.length)],
        ['Checks', String(checks.length)],
      ])}
      <div class="trace-box"><strong>Action focus</strong><p class="muted">${highlighted.length ? escapeHtml(highlighted.map((item) => `${item.title} (${item.detail || 'review required'})`).join(' | ')) : 'All first-run checks are green.'}</p></div>
      <div class="inline-actions">
        <button class="action-button" data-view-jump="${escapeHtml(recommendedView)}">Open ${escapeHtml(titleCase(recommendedView))}</button>
        ${can('ops.manage') ? '<button class="action-button action-button-muted" data-ops-action="usability-proof-refresh">Refresh Latest Proof</button>' : ''}
      </div>
    </section>
  `;
}


function renderOperatorDecisionLanes(lanes) {
  const items = Array.isArray(lanes) ? lanes.slice(0, 6) : [];
  if (!items.length) return '';
  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Human Required Control Plane</div>
          <h3 class="card-title">Deterministic operator decision lanes</h3>
          <p class="card-subtitle">Each lane maps runtime state to the next explicit operator action. Unknown states stay fail-closed.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${items.length} lanes`)}</div>
      </div>
      <div class="view-prelude-grid">
        ${items.map((lane) => `
          <article class="view-prelude-card${lane.disposition === 'blocked' ? ' view-prelude-card-danger' : lane.disposition === 'human_required' ? ' view-prelude-card-warning' : ''}">
            <span class="view-prelude-label">${escapeHtml(titleCase(lane.lane_id || 'lane'))}</span>
            <strong>${escapeHtml(lane.title || 'Operator lane')}</strong>
            <p class="muted">${escapeHtml(lane.operator_action || 'Review runtime posture before continuing.')}</p>
            <div class="hero-chip-row">${statusBadge(lane.disposition || 'monitoring')}</div>
            <p class="muted">${escapeHtml(lane.governance_outcome || '')}</p>
            ${lane.default_view ? `<div class="inline-actions"><button class="action-button" data-view-jump="${escapeHtml(lane.default_view)}">Open ${escapeHtml(titleCase(lane.default_view))}</button></div>` : ''}
          </article>
        `).join('')}
      </div>
    </section>
  `;
}

function renderOperatorQueueHealthCard(queueHealth) {
  const items = Array.isArray(queueHealth?.items) ? queueHealth.items.filter((item) => (item.total || 0) > 0).slice(0, 5) : [];
  const policy = queueHealth?.policy || {};
  const aging = policy.aging || {};
  const backlog = policy.backlog || {};
  if (!items.length) return '';
  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Operator Queue Health</div>
          <h3 class="card-title">One policy reads every waiting lane</h3>
          <p class="card-subtitle">A single operator alert policy watches human approvals, Human Ask queues, blocked workflows, recovery backlog, and dead letters without requiring separate threshold tuning for each lane.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${queueHealth.attention_total || 0} attention`)}</div>
      </div>
      ${keyValue([
        ['Warning age', `${aging.warning_hours || '-'} hours`],
        ['Critical age', `${aging.critical_hours || '-'} hours`],
        ['Stale age', `${aging.stale_hours || '-'} hours`],
        ['Backlog warning', String(backlog.warning_total || '-')],
        ['Backlog critical', String(backlog.critical_total || '-')],
      ])}
      <div class="view-prelude-grid">
        ${items.map((item) => `
          <article class="view-prelude-card${item.status === 'stale' || item.status === 'critical' ? ' view-prelude-card-danger' : item.status === 'warning' ? ' view-prelude-card-warning' : ''}">
            <span class="view-prelude-label">${escapeHtml(titleCase(item.lane_id || 'lane'))}</span>
            <strong>${escapeHtml(item.title || 'Queue lane')}</strong>
            <p class="muted">${escapeHtml(`${item.total || 0} queued | oldest about ${item.oldest_age_hours || 0} hours | ref ${item.oldest_reference || '-'}`)}</p>
            <div class="hero-chip-row">${statusBadge(item.status || 'monitoring')}</div>
            ${item.view ? `<div class="inline-actions"><button class="action-button" data-view-jump="${escapeHtml(item.view)}">Open ${escapeHtml(titleCase(item.view))}</button></div>` : ''}
          </article>
        `).join('')}
      </div>
    </section>
  `;
}

function renderOperatorNotificationPolicyCard(center) {
  const policy = center?.policy || {};
  const notification = policy.notification || {};
  const severityChannels = notification.severity_channels || {};
  const cadence = notification.cadence || center?.cadence || {};
  const items = Array.isArray(center?.items) ? center.items.slice(0, 5) : [];
  const channels = Array.isArray(center?.channels) ? center.channels : [];
  if (!notification || !Object.keys(notification).length) return '';
  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Operator Notification Plan</div>
          <h3 class="card-title">One routing plan covers every waiting lane</h3>
          <p class="card-subtitle">The same operator policy that scores queue age and backlog also decides which channel should be used for warning, critical, and stale conditions.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(center?.enabled ? (center?.highest_severity || 'ready') : 'notifications disabled')}</div>
      </div>
      ${keyValue([
        ['Notifications enabled', String(Boolean(center?.enabled))],
        ['Default channels', (notification.default_channels || []).join(', ') || 'dashboard'],
        ['Re-alert cadence', `${cadence.realert_hours || '-'} hours`],
        ['Digest cadence', `${cadence.digest_hours || '-'} hours`],
        ['Dispatch candidates', String(center?.dispatch_candidates_total || 0)],
        ['Active channels', String(center?.active_channel_total || 0)],
      ])}
      <div class="view-prelude-grid">
        ${['warning', 'critical', 'stale'].map((level) => `
          <article class="view-prelude-card${level === 'stale' || level === 'critical' ? ' view-prelude-card-danger' : ' view-prelude-card-warning'}">
            <span class="view-prelude-label">${escapeHtml(titleCase(level))}</span>
            <strong>${escapeHtml((severityChannels[level] || []).join(', ') || 'dashboard')}</strong>
            <p class="muted">${escapeHtml(level === 'warning' ? 'Early operator attention before queues harden.' : level === 'critical' ? 'Escalated operator routing once age or backlog crosses the critical threshold.' : 'Strongest routing once queues are stale and executive follow-up is overdue.')}</p>
          </article>
        `).join('')}
      </div>
      ${channels.length ? `<div class="trace-box"><strong>Active routing footprint</strong><p class="muted">${escapeHtml(channels.map((item) => `${item.channel} (${item.active_total})`).join(' | '))}</p></div>` : '<div class="trace-box"><strong>Active routing footprint</strong><p class="muted">No queue lane currently requires notification routing.</p></div>'}
      ${items.length ? `
        <div class="view-prelude-grid">
          ${items.map((item) => `
            <article class="view-prelude-card${item.status === 'stale' || item.status === 'critical' ? ' view-prelude-card-danger' : ' view-prelude-card-warning'}">
              <span class="view-prelude-label">${escapeHtml(titleCase(item.lane_id || 'lane'))}</span>
              <strong>${escapeHtml(item.title || 'Queue lane')}</strong>
              <p class="muted">${escapeHtml(`${item.total || 0} queued | oldest about ${item.oldest_age_hours || 0} hours | channels ${Array.isArray(item.channels) ? item.channels.join(', ') : 'dashboard'}`)}</p>
              <div class="hero-chip-row">${statusBadge(item.status || 'warning')}</div>
              ${item.view ? `<div class="inline-actions"><button class="action-button action-button-muted" data-view-jump="${escapeHtml(item.view)}">Open ${escapeHtml(titleCase(item.view))}</button></div>` : ''}
            </article>
          `).join('')}
        </div>
      ` : ''}
    </section>
  `;
}

function renderOperatorNotificationDeliveryCard(center, integrations, deliveryReadiness = null) {
  const notification = center?.policy?.notification || {};
  const summary = integrations?.summary || {};
  const activeTargets = Number((deliveryReadiness?.active_targets ?? summary.active_targets) || 0);
  const deliveriesTotal = Number((deliveryReadiness?.deliveries_total ?? summary.deliveries_total) || 0);
  const failedTotal = Number((deliveryReadiness?.failed_total ?? summary.failed_total) || 0);
  const outboxTotal = Number((deliveryReadiness?.outbox_total ?? summary.outbox_total) || 0);
  const httpEnabled = Boolean((deliveryReadiness?.http_enabled ?? summary.http_enabled) || false);
  const coordinationBackend = summary.coordination_backend || '-';
  const coordinationMode = summary.coordination_mode || '-';
  const uniqueChannels = new Set();
  (notification.default_channels || []).forEach((channel) => uniqueChannels.add(String(channel)));
  Object.values(notification.severity_channels || {}).forEach((channels) => {
    (channels || []).forEach((channel) => uniqueChannels.add(String(channel)));
  });
  const channels = Array.from(uniqueChannels);
  if (!channels.length) return '';

  const describeChannel = (channel) => {
    if (channel === 'dashboard') {
      return {
        status: center?.enabled ? 'ready' : 'disabled',
        note: center?.enabled
          ? 'Always available inside the operator dashboard and alert rail.'
          : 'Dashboard routing is configured but notifications are globally disabled.',
      };
    }
    if (!httpEnabled) {
      return {
        status: 'setup_needed',
        note: 'Outbound HTTP integrations are disabled, so external routing is not ready yet.',
      };
    }
    if (activeTargets <= 0) {
      return {
        status: 'setup_needed',
        note: 'No active integration target is available for external delivery yet.',
      };
    }
    if (failedTotal > 0) {
      return {
        status: 'degraded',
        note: 'External routing exists, but recent delivery failures mean the channel needs review.',
      };
    }
    if (outboxTotal > 0) {
      return {
        status: 'pressured',
        note: 'Targets are present, but queued outbox jobs mean delivery is under pressure.',
      };
    }
    return {
      status: 'ready',
      note: deliveriesTotal > 0
        ? 'Targets are active and recent deliveries are visible in the runtime ledger.'
        : 'Targets are active and ready even if no recent delivery has been recorded yet.',
    };
  };

  const rows = channels.map((channel) => ({ channel, ...describeChannel(channel) }));
  const postureLabel = deliveryReadiness?.posture
    ? String(deliveryReadiness.posture).replace('_', ' ')
    : (rows.some((row) => row.status === 'degraded' || row.status === 'setup_needed') ? 'review routing' : 'delivery aligned');
  const priority = { degraded: 3, pressured: 2, setup_needed: 2, ready: 1, disabled: 0 };
  rows.sort((left, right) => (priority[right.status] - priority[left.status]) || left.channel.localeCompare(right.channel));

  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Notification Delivery Readiness</div>
          <h3 class="card-title">Will the chosen channels actually carry operator alerts?</h3>
          <p class="card-subtitle">This card compares the unified operator notification plan against the current integration posture so operators can see whether routing is dashboard-only, externally ready, or still needs setup.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(postureLabel)}</div>
      </div>
      ${keyValue([
        ['Active integration targets', String(activeTargets)],
        ['HTTP enabled', String(httpEnabled)],
        ['Deliveries visible', String(deliveriesTotal)],
        ['Failed deliveries', String(failedTotal)],
        ['Outbox jobs', String(outboxTotal)],
        ['Coordination', `${coordinationBackend} | ${coordinationMode}`],
      ])}
      <div class="view-prelude-grid">
        ${rows.map((row) => `
          <article class="view-prelude-card${row.status === 'degraded' || row.status === 'setup_needed' ? ' view-prelude-card-danger' : row.status === 'pressured' ? ' view-prelude-card-warning' : ''}">
            <span class="view-prelude-label">${escapeHtml(row.channel)}</span>
            <strong>${escapeHtml(titleCase(row.status.replace('_', ' ')))}</strong>
            <p class="muted">${escapeHtml(row.note)}</p>
          </article>
        `).join('')}
      </div>
      <div class="inline-actions">
        <button class="action-button action-button-muted" data-view-jump="health">Open Health</button>
      </div>
    </section>
  `;
}

function renderNotificationCenter(alerts) {
  if (!alerts.length) return '';
  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Notification Center</div>
          <h3 class="card-title">AI boundary and readiness alerts</h3>
          <p class="card-subtitle">A compact runtime history of where automation stopped, where PT-OSS is still applying pressure, and where production posture remains guarded.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${alerts.length} alerts`)}</div>
      </div>
      <div class="stack">
        ${alerts.map((alert) => `
          <article class="trace-box compact-trace notice-card notice-${escapeHtml(alert.tone || 'warning')}">
            <div class="hero-heading">
              <div>
                <strong>${escapeHtml(alert.title || 'Runtime alert')}</strong>
                <p class="muted">${escapeHtml(`${alert.eyebrow || 'Runtime alert'} | ${alert.timestamp ? shortTime(alert.timestamp) : 'Current runtime'}`)}</p>
              </div>
              <div class="hero-chip-row">${statusBadge(alert.badge || alert.tone || 'warning')}</div>
            </div>
            <p class="muted">${escapeHtml(alert.message || 'Runtime attention is required.')}</p>
            ${alert.details ? keyValue(Object.entries(alert.details).map(([key, value]) => [titleCase(key), String(value)])) : ''}
            ${alert.view ? `<div class="inline-actions"><button class="action-button action-button-muted" data-view-jump="${escapeHtml(alert.view)}">${escapeHtml(alert.action_label || 'Open view')}</button></div>` : ''}
          </article>
        `).join('')}
      </div>
    </section>
  `;
}


function renderCases(snapshot) {
  const casesSurface = snapshot.cases || { summary: {}, items: [] };
  const summary = casesSurface.summary || {};
  const items = Array.isArray(casesSurface.items) ? casesSurface.items : [];
  const leadCase = items[0] || null;
  const latestCaseLabel = leadCase
    ? `${leadCase.case_id} | ${shortTime(leadCase.updated_at)}`
    : 'No linked governed issue has been grouped into a case yet.';
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Canonical Case Backbone</div>
            <h2 class="hero-title">Track one governed issue across requests, approvals, records, and proof.</h2>
            <p class="hero-subtitle">Cases keep the working lane, human boundary, Human Ask record, and audit history tied to the same operating story so the next move is easier to see.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(summary.human_required_total ? 'human required' : (summary.blocked_total ? 'blocked paths present' : 'linked cases stable'))}
            ${statusBadge(summary.primary_view || 'overview')}
          </div>
        </div>
        <div class="hero-split">
          ${keyValue([
            ['Cases in view', String(summary.cases_total || 0)],
            ['Human required', String(summary.human_required_total || 0)],
            ['Blocked', String(summary.blocked_total || 0)],
            ['Attention', String(summary.attention_total || 0)],
            ['Primary lane', VIEW_TITLES[summary.primary_view] || titleCase(summary.primary_view || 'overview')],
          ])}
          <div class="hero-note">
            <strong>Operator standard</strong>
            <p>Stay with the case until the issue is either resolved, handed to the correct human boundary, or fully documented with enough proof for later review.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Case reading guide</div>
          <h3 class="card-title">What this lane answers quickly</h3>
          <p class="card-subtitle">Use Cases when the same business issue now spans more than one runtime surface and you do not want to reconstruct the story by hand.</p>
        </div>
        ${keyValue([
          ['Latest case', latestCaseLabel],
          ['Trace model', 'Request to override to record to audit'],
          ['Primary job', 'Follow the issue, not just the individual event'],
          ['Proof stance', 'Keep the human and AI narrative attached'],
        ])}
        <div class="trace-box"><strong>Case note</strong><p class="muted">A case is not a new source of truth. It is the stitched operating view built from the governed records the runtime already captured.</p></div>
      </article>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Cases', summary.cases_total || 0, 'accent', 'Linked governed issues currently visible in the dashboard work surface.')}
      ${metricCard('Human required', summary.human_required_total || 0, (summary.human_required_total || 0) ? 'warning' : 'success', 'Cases currently waiting on a real human decision or boundary confirmation.')}
      ${metricCard('Blocked', summary.blocked_total || 0, (summary.blocked_total || 0) ? 'danger' : 'success', 'Cases currently held behind a blocked outcome or vetoed path.')}
      ${metricCard('Attention', summary.attention_total || 0, (summary.attention_total || 0) ? 'warning' : 'success', 'Cases that still need extra operator follow-through even if they are not hard blocked.')}
    </section>
    <section class="case-grid">
      ${items.length ? items.map((item) => renderCaseCard(item)).join('') : renderCaseEmptyState()}
    </section>
  `;
}

function resolveCaseWorkItemFocus(workItem = {}) {
  const ids = Array.isArray(workItem.ids) ? workItem.ids : [];
  const firstId = ids[0] || '';
  switch (workItem.kind) {
    case 'request':
      return { entityType: 'request', entityId: firstId };
    case 'override':
      return { entityType: 'override', entityId: firstId };
    case 'human_ask':
      return { entityType: 'human_ask_session', entityId: firstId };
    case 'studio':
      return { entityType: 'studio_request', entityId: firstId };
    case 'audit':
      return { entityType: firstId ? 'request' : 'case', entityId: firstId || '' };
    default:
      return { entityType: 'case', entityId: '' };
  }
}

function renderCaseWorkItems(item) {
  const workItems = Array.isArray(item.work_items) ? item.work_items.filter((entry) => Number(entry.total || 0) > 0) : [];
  if (!workItems.length) return '';
  return `
    <div class="case-work-items">
      ${workItems.map((entry) => {
        const focus = resolveCaseWorkItemFocus(entry);
        const viewLabel = VIEW_TITLES[entry.view] || titleCase(entry.view || 'overview');
        const idPreview = (Array.isArray(entry.ids) ? entry.ids : []).slice(0, 2).filter(Boolean).join(' | ');
        return `
          <article class="mini-card case-work-item">
            <div class="eyebrow muted">${escapeHtml(entry.label || 'Work item')}</div>
            <div class="case-work-item-value">${escapeHtml(String(entry.total || 0))}</div>
            <p class="muted">${escapeHtml(idPreview || `Open ${viewLabel} to review linked work.`)}</p>
            <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
              view: entry.view || 'overview',
              focusType: focus.entityType,
              focusId: focus.entityId,
              title: item.case_id ? `Case ${item.case_id} opened in ${viewLabel}.` : `Opened ${viewLabel}.`,
              detail: `Use ${viewLabel} to inspect the linked ${String(entry.label || 'work').toLowerCase()}.`,
              actionLabel: `Open ${viewLabel}`,
            })}>${escapeHtml(`Open ${viewLabel}`)}</button>
          </article>
        `;
      }).join('')}
    </div>
  `;
}

function renderCaseContinuity(item) {
  const continuity = item.continuity || {};
  const nextView = continuity.next_view || item.primary_view || 'requests';
  const nextViewLabel = VIEW_TITLES[nextView] || titleCase(nextView || 'overview');
  const nextFocus = resolveCasePrimaryFocus(item, nextView);
  const latestProof = item.latest_proof_event || null;
  const followUps = Array.isArray(continuity.follow_up_actions) ? continuity.follow_up_actions : [];
  return `
    <div class="case-continuity-grid">
      <article class="mini-card case-continuity-card">
        <div class="eyebrow muted">Next governed move</div>
        <strong>${escapeHtml(continuity.next_label || `Open ${nextViewLabel}`)}</strong>
        <p class="muted">${escapeHtml(continuity.next_detail || 'Continue from the lead lane attached to this case.')}</p>
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view: nextView,
          focusType: nextFocus.entityType,
          focusId: nextFocus.entityId,
          title: item.case_id ? `Case ${item.case_id} opened in ${nextViewLabel}.` : `Opened ${nextViewLabel}.`,
          detail: continuity.next_detail || 'The linked work item stays highlighted in its operating lane so you can continue from the same governed issue.',
          actionLabel: `Open ${nextViewLabel}`,
        })}>${escapeHtml(`Open ${nextViewLabel}`)}</button>
      </article>
      <article class="mini-card case-continuity-card">
        <div class="eyebrow muted">Proof posture</div>
        <strong>${escapeHtml(continuity.evidence_posture || 'proof starting')}</strong>
        <p class="muted">${escapeHtml(continuity.evidence_detail || 'Case proof will strengthen as requests, decisions, and audit events accumulate.')}</p>
        <span class="permission-note">Audit ${escapeHtml(String(item.audit_event_total || 0))} | Exports ${escapeHtml(String(item.evidence_export_total || 0))} | Workflow proof ${escapeHtml(String(item.workflow_proof_total || 0))}</span>
        ${latestProof ? `<div class="case-proof-note"><strong>${escapeHtml(titleCase(latestProof.action || 'proof event'))}</strong><p class="muted">${escapeHtml(latestProof.detail || 'Latest proof artifact recorded.')}</p><span class="permission-note">${escapeHtml(shortTime(latestProof.timestamp))} | ${escapeHtml(latestProof.status || 'recorded')} | ${escapeHtml(latestProof.reference || '-')}</span></div>` : ''}
      </article>
    </div>
    ${followUps.length ? `<div class="case-follow-up-grid">${followUps.map((entry) => {
      const view = entry.view || 'overview';
      const viewLabel = VIEW_TITLES[view] || titleCase(view || 'overview');
      const focus = resolveCasePrimaryFocus(item, view);
      return `<article class="mini-card case-follow-up-item">
        <div class="eyebrow muted">Follow-up</div>
        <strong>${escapeHtml(entry.label || `Open ${viewLabel}`)}</strong>
        <p class="muted">${escapeHtml(entry.detail || 'Continue the governed flow from the linked lane.')}</p>
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view,
          focusType: focus.entityType,
          focusId: focus.entityId,
          caseId: item.case_id,
          title: item.case_id ? `Case ${item.case_id} opened in ${viewLabel}.` : `Opened ${viewLabel}.`,
          detail: entry.detail || 'Continue the governed flow from the linked lane.',
          actionLabel: `Open ${viewLabel}`,
        })}>${escapeHtml(`Open ${viewLabel}`)}</button>
      </article>`;
    }).join('')}</div>` : ''}
  `;
}

function renderCaseCard(item) {
  const timeline = Array.isArray(item.timeline) ? item.timeline : [];
  const linkedRefs = [
    ...(item.linked_request_ids || []).slice(0, 3),
    ...(item.linked_override_ids || []).slice(0, 2),
    ...(item.linked_session_ids || []).slice(0, 2),
    ...(item.linked_workflow_ids || []).slice(0, 2),
    ...(item.linked_studio_request_ids || []).slice(0, 2),
  ].filter(Boolean);
  const primaryView = item.primary_view || 'requests';
  const primaryFocus = resolveCasePrimaryFocus(item, primaryView);
  const primaryViewLabel = VIEW_TITLES[primaryView] || titleCase(primaryView);
  const secondaryView = primaryView !== 'audit' ? 'audit' : 'requests';
  const secondaryViewLabel = VIEW_TITLES[secondaryView] || titleCase(secondaryView);
  return `
    <article class="card stack case-card${isFocusedEntity('case', item.case_id) ? ' focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey('case', item.case_id))}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(item.case_id || 'CASE')}</div>
          <h3 class="card-title">${escapeHtml(item.title || item.case_id || 'Governed case')}</h3>
          <p class="card-subtitle">${escapeHtml(`Updated ${shortTime(item.updated_at)} | Opened ${shortTime(item.opened_at)}`)}</p>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(item.status || 'monitoring')}
          ${statusBadge(primaryViewLabel)}
        </div>
      </div>
      ${keyValue([
        ['Requests', String((item.linked_request_ids || []).length)],
        ['Overrides', String((item.linked_override_ids || []).length)],
        ['Human Ask', String((item.linked_session_ids || []).length)],
        ['Workflow refs', String((item.linked_workflow_ids || []).length)],
        ['Audit events', String(item.audit_event_total || 0)],
        ['Timeline', String(item.timeline_total || 0)],
      ])}
      ${renderCaseContinuity(item)}
      ${renderCaseWorkItems(item)}
      ${linkedRefs.length ? `<div class="case-reference-list">${linkedRefs.map((value) => `<span class="pill pill-muted">${escapeHtml(value)}</span>`).join('')}</div>` : ''}
      <div class="case-timeline">
        ${timeline.length ? timeline.map((entry) => renderCaseTimelineEntry(entry)).join('') : `<div class="empty-state">No case events are available yet.</div>`}
      </div>
      <div class="inline-actions">
        <button class="action-button" type="button" ${buildViewJumpAttributes({
          view: primaryView,
          focusType: primaryFocus.entityType,
          focusId: primaryFocus.entityId,
          caseId: item.case_id,
          title: item.case_id ? `Case ${item.case_id} opened in ${primaryViewLabel}.` : `Opened ${primaryViewLabel}.`,
          detail: 'The linked work item stays highlighted in its operating lane so you can continue from the same governed issue.',
          actionLabel: `Open ${primaryViewLabel}`,
        })}>${escapeHtml(`Open ${primaryViewLabel}`)}</button>
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view: secondaryView,
          caseId: item.case_id,
          title: item.case_id ? `Case ${item.case_id} opened in ${secondaryViewLabel}.` : `Opened ${secondaryViewLabel}.`,
          detail: secondaryView === 'audit' ? 'Use Audit to verify the evidence trail attached to this case.' : 'Use Requests to reopen the linked runtime intake lane.',
          actionLabel: `Open ${secondaryViewLabel}`,
        })}>${escapeHtml(`Open ${secondaryViewLabel}`)}</button>
      </div>
    </article>
  `;
}

function renderCaseTimelineEntry(entry) {
  return `
    <article class="mini-card stack case-timeline-item">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(shortTime(entry.timestamp))}</div>
          <strong>${escapeHtml(entry.title || 'Case event')}</strong>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(entry.status || 'recorded')}
          ${statusBadge(VIEW_TITLES[entry.view] || titleCase(entry.view || 'overview'))}
        </div>
      </div>
      <p class="muted">${escapeHtml(entry.detail || 'Governed case event recorded.')}</p>
      <span class="permission-note">Ref ${escapeHtml(entry.reference || '-')}</span>
    </article>
  `;
}

function renderCaseEmptyState() {
  return `
    <article class="card stack case-card case-card-empty">
      <div>
        <div class="eyebrow muted">Case lane empty</div>
        <h3 class="card-title">No linked governed case is visible yet</h3>
        <p class="card-subtitle">Start from Requests, Human Ask, or Role Private Studio. As soon as the runtime captures related work, this lane will stitch the issue into one readable case.</p>
      </div>
      <div class="inline-actions">
        <button class="action-button" type="button" data-view-jump="requests">Open Requests</button>
        <button class="action-button action-button-muted" type="button" data-view-jump="overview">Open Overview</button>
      </div>
    </article>
  `;
}

function buildViewJumpAttributes({ view = '', focusType = '', focusId = '', caseId = '', title = '', detail = '', actionLabel = '' } = {}) {
  const attrs = [`data-view-jump="${escapeHtml(view || 'overview')}"`];
  if (focusType) attrs.push(`data-view-jump-focus-type="${escapeHtml(focusType)}"`);
  if (focusId) attrs.push(`data-view-jump-focus-id="${escapeHtml(focusId)}"`);
  if (caseId) attrs.push(`data-view-jump-case-id="${escapeHtml(caseId)}"`);
  if (title) attrs.push(`data-view-jump-title="${escapeHtml(title)}"`);
  if (detail) attrs.push(`data-view-jump-detail="${escapeHtml(detail)}"`);
  if (actionLabel) attrs.push(`data-view-jump-action-label="${escapeHtml(actionLabel)}"`);
  return attrs.join(' ');
}

function renderCaseReferenceButton(caseId, caseStatus = '', { sourceView = 'overview', referenceId = '', contextLabel = 'governed work item', label = '' } = {}) {
  const normalizedCaseId = String(caseId || '').trim();
  if (!normalizedCaseId) return '';
  const sourceViewLabel = VIEW_TITLES[sourceView] || titleCase(sourceView || 'overview');
  const title = referenceId
    ? `Case ${normalizedCaseId} linked from ${contextLabel} ${referenceId}.`
    : `Case ${normalizedCaseId} linked from ${sourceViewLabel}.`;
  const detail = `This ${contextLabel} is already linked into the canonical Cases lane, so you can inspect the full operating story without leaving dashboard flow.`;
  return `
    <span class="case-reference-inline">
      <button class="pill pill-muted case-link-button" type="button" ${buildViewJumpAttributes({
        view: 'cases',
        focusType: 'case',
        focusId: normalizedCaseId,
        title,
        detail,
        actionLabel: 'Open Cases',
      })}>${escapeHtml(label || normalizedCaseId)}</button>
      ${caseStatus ? statusBadge(caseStatus) : ''}
    </span>
  `;
}

function resolveCasePrimaryFocus(item, primaryView = '') {
  const view = primaryView || item.primary_view || 'requests';
  if (view === 'overrides') {
    const overrideId = (item.linked_override_ids || [])[0] || (item.linked_request_ids || [])[0] || '';
    return { entityType: overrideId ? 'override' : '', entityId: overrideId };
  }
  if (view === 'human_ask') {
    const sessionId = (item.linked_session_ids || [])[0] || '';
    return { entityType: sessionId ? 'human_ask_session' : '', entityId: sessionId };
  }
  if (view === 'studio') {
    const studioRequestId = (item.linked_studio_request_ids || [])[0] || '';
    return { entityType: studioRequestId ? 'studio_request' : '', entityId: studioRequestId };
  }
  if (view === 'conflicts') {
    const requestId = (item.linked_request_ids || [])[0] || (item.linked_override_ids || [])[0] || '';
    return { entityType: requestId ? 'request' : '', entityId: requestId };
  }
  if (view === 'audit') {
    return { entityType: '', entityId: '' };
  }
  const requestId = (item.linked_request_ids || [])[0] || '';
  return { entityType: requestId ? 'request' : '', entityId: requestId };
}

function renderRequests(snapshot) {
  const requests = snapshot.requests || [];
  const overrides = snapshot.overrides || [];
  const pendingOverrides = overrides.filter((item) => item.status === 'pending');
  const conflicts = requests.filter((item) => item.outcome === 'conflicted');
  const uniqueRoles = new Set(requests.map((item) => item.active_role).filter(Boolean)).size;
  const routedRequests = requests.filter((item) => item.activation_source && item.activation_source !== 'requested_role').length;
  const switchedRequests = requests.filter((item) => item.previous_role && item.active_role && item.previous_role !== item.active_role).length;
  const escalatedTransitions = requests.filter((item) => item.escalated_to).length;
  const latestRequestLabel = requests.length
    ? `${requests[0].request_id} | ${shortTime(requests[0].timestamp)}`
    : 'No governed request has been recorded yet.';
  const composer = can('request.create')
    ? renderRequestComposer(snapshot.roles || [])
    : `<article class="card notice-card stack"><strong>Request composer</strong><p class="permission-note">This profile does not have request.create permission.</p></article>`;
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Runtime Intake Command</div>
            <h2 class="hero-title">Governed requests enter a disciplined execution corridor.</h2>
            <p class="hero-subtitle">Every submission is checked for role authority, policy coverage, consistency posture, role flow, and audit trace before any privileged work is allowed to continue.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(conflicts.length ? 'heightened watch' : 'stable queue')}
            ${statusBadge(pendingOverrides.length ? 'human review active' : 'clear override lane')}
          </div>
        </div>
        <div class="hero-split">
          ${keyValue([
            ['Requests in view', String(requests.length)],
            ['Roles represented', String(uniqueRoles)],
            ['Context routed', String(routedRequests)],
            ['Role switches', String(switchedRequests)],
            ['Pending overrides', String(pendingOverrides.length)],
            ['Escalations', String(escalatedTransitions)],
          ])}
          <div class="hero-note">
            <strong>Operator standard</strong>
            <p>Use runtime intake for actions that belong inside the governed server boundary. Context-aware routing, switch reasoning, and escalation lanes are now visible directly in the request ledger.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Submission posture</div>
          <h3 class="card-title">Queue discipline</h3>
          <p class="card-subtitle">The request surface is tuned for live operations, approval routing, and post-decision traceability.</p>
        </div>
        ${keyValue([
          ['Latest request', latestRequestLabel],
          ['Override queue', pendingOverrides.length ? 'active' : 'clear'],
          ['Conflict exposure', conflicts.length ? 'present' : 'none'],
          ['Execution model', 'Governed private runtime'],
          ['Activation surface', routedRequests ? 'context-aware live' : 'explicit or stable'],
        ])}
        <div class="trace-box"><strong>Submission note</strong><p class="muted">When metadata includes idempotency keys and event ordering, replay and out-of-order protection remain explicit in the runtime ledger alongside role transitions and escalation evidence.</p></div>
      </article>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Requests', requests.length, 'default', 'Governed submissions visible in the current runtime ledger.')}
      ${metricCard('Pending overrides', pendingOverrides.length, 'warning', 'Requests paused until a human review resolves the decision.')}
      ${metricCard('Conflicts', conflicts.length, 'danger', 'Requests blocked by resource contention or concurrency governance.')}
      ${metricCard('Context routed', routedRequests, 'accent', 'Requests that activated or switched hats through the live context router.')}
      ${metricCard('Role switches', switchedRequests, 'default', 'Requests that moved from one hat to another before execution.')}
      ${metricCard('Escalated to human', escalatedTransitions, 'warning', 'Requests that entered a governed escalation lane with an explicit target.')}
    </section>
    <section class="split-grid">
      ${composer}
      ${renderApprovalFlowCard({
        eyebrow: 'Approval corridor',
        title: 'How the governed approval flow works',
        subtitle: 'The runtime makes the autonomous-versus-human boundary visible before anyone forces work through.',
        queueStatus: pendingOverrides.length ? 'Human review is active in this snapshot.' : 'No active human review bottleneck is visible in this snapshot.',
        primaryActionView: 'overrides',
        primaryActionLabel: 'Open Overrides',
        secondaryActionView: 'audit',
        secondaryActionLabel: 'Open Audit',
        steps: [
          ['1. Submit into the runtime', 'The operator sends a governed request with action, payload, and metadata.'],
          ['2. Let SA-NOM classify the path', 'Policy coverage, role authority, consistency checks, and routing decide whether the request may continue autonomously.'],
          ['3. Stop at the human boundary when required', pendingOverrides.length ? 'Pending overrides already show where execution is paused for a real human decision.' : 'If risk, policy, or runtime posture requires it, the request is paused for human approval or veto.'],
          ['4. Resume only with evidence', 'Approval outcome, rationale, and audit trace remain attached before downstream execution continues.'],
        ],
      })}
    </section>
    <section class="split-grid">
      <article class="card stack">
        <div><div class="eyebrow muted">Submission protocol</div><h3 class="card-title">What strong requests look like</h3><p class="card-subtitle">Use this surface as the premium operator lane for runtime work that must remain reviewable after execution.</p></div>
        ${keyValue([
          ['Payload quality', 'Structured JSON with explicit resource context'],
          ['Consistency discipline', 'Idempotency key plus event ordering metadata'],
          ['Role targeting', 'Choose a trusted role or leave it blank for context-aware routing'],
          ['Review posture', pendingOverrides.length ? 'Monitor the human override queue after submit' : 'No active review bottleneck detected'],
        ])}
        <div class="trace-box"><strong>Recommended metadata</strong><p class="muted">Pair each governed request with an idempotency key, event stream, and event sequence whenever the action touches mutable records or recurring workflows.</p></div>
      </article>
      <article class="card stack">
        <div><div class="eyebrow muted">Onboarding checkpoint</div><h3 class="card-title">What to do after your first request</h3><p class="card-subtitle">Use the next view based on what happened to the request instead of guessing where the system stored the decision.</p></div>
        ${keyValue([
          ['If the request stayed autonomous', 'Open Audit to confirm outcome and policy basis'],
          ['If the request escalated', 'Open Overrides to see who must approve or veto'],
          ['If the request conflicted', 'Open Conflicts to inspect locks before retrying'],
          ['If the role changed', 'Stay in Runtime Requests to review activation source and switch reason'],
        ])}
        <div class="inline-actions">
          <button class="action-button" type="button" data-view-jump="audit">Open Audit</button>
          <button class="action-button action-button-muted" type="button" data-view-jump="conflicts">Open Conflicts</button>
        </div>
      </article>
    </section>
    ${wrapTableCard('Runtime Requests', requestTable(requests), 'Live governed requests with role flow, activation source, escalation target, consistency posture, and policy basis.')}
    ${wrapTableCard('Human Override Queue', overrideTable(overrides), 'Pending and resolved human reviews that control whether execution may continue.')}
  `;
}

function renderOverridesView(snapshot) {
  const overrides = snapshot.overrides || [];
  const pendingOverrides = overrides.filter((item) => item.status === 'pending');
  const approvedOverrides = overrides.filter((item) => item.status === 'approved');
  const vetoedOverrides = overrides.filter((item) => item.status === 'vetoed');
  const requesters = new Set(overrides.map((item) => item.requester).filter(Boolean)).size;
  const latestOverrideLabel = overrides.length
    ? `${overrides[0].request_id} | ${shortTime(overrides[0].created_at)}`
    : 'No human override records are visible yet.';
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Human Decision Lane</div>
            <h2 class="hero-title">Execution stays paused until a human approval outcome is recorded.</h2>
            <p class="hero-subtitle">This lane shows which governed requests crossed a human boundary, who must decide next, and whether the runtime can resume or must remain blocked.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(pendingOverrides.length ? 'approval action required' : 'queue stable')}
            ${statusBadge(vetoedOverrides.length ? 'veto history present' : 'no recent veto')}
          </div>
        </div>
        <div class="hero-split">
          ${keyValue([
            ['Overrides in view', String(overrides.length)],
            ['Pending approvals', String(pendingOverrides.length)],
            ['Approved', String(approvedOverrides.length)],
            ['Vetoed', String(vetoedOverrides.length)],
            ['Requesters represented', String(requesters)],
          ])}
          <div class="hero-note">
            <strong>Human-control standard</strong>
            <p>Approve only when the governed request, policy basis, and rationale align. A veto is a first-class control signal and should be used when the runtime must remain fail-closed.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Review posture</div>
          <h3 class="card-title">Queue reading guide</h3>
          <p class="card-subtitle">Use this view to answer the two questions operators always ask: who owns the next decision, and what evidence will justify it later?</p>
        </div>
        ${keyValue([
          ['Latest override', latestOverrideLabel],
          ['Decision model', 'Approve or veto before resume'],
          ['Execution stance', pendingOverrides.length ? 'paused behind human boundary' : 'no current pause detected'],
          ['Audit expectation', 'Rationale and outcome should remain reviewable'],
        ])}
        <div class="trace-box"><strong>Reviewer note</strong><p class="muted">If you need the end-to-end context first, open Runtime Requests before deciding so the role flow, action, and escalation target remain visible beside the approval packet.</p></div>
      </article>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Pending', pendingOverrides.length, 'warning', 'Requests waiting for a human decision before execution may continue.')}
      ${metricCard('Approved', approvedOverrides.length, 'success', 'Requests that received a human green light and may continue under audit trace.')}
      ${metricCard('Vetoed', vetoedOverrides.length, 'danger', 'Requests that were intentionally stopped by a human control decision.')}
      ${metricCard('Distinct requesters', requesters, 'default', 'How many submitting identities are represented in the current override queue.')}
    </section>
    <section class="split-grid">
      ${renderApprovalFlowCard({
        eyebrow: 'Review flow',
        title: 'How to review a human-required request',
        subtitle: 'This view is where the private runtime hands control to a real person without losing auditability.',
        queueStatus: pendingOverrides.length ? 'There are pending packets that still need a human decision.' : 'No pending approval packets are visible right now.',
        primaryActionView: 'requests',
        primaryActionLabel: 'Open Requests',
        secondaryActionView: 'audit',
        secondaryActionLabel: 'Open Audit',
        steps: [
          ['1. Inspect the governed request', 'Use the request id, role, action, and requester to understand what the runtime paused.'],
          ['2. Confirm why the human boundary was triggered', 'Check required-by, policy basis, and execution outcome so the decision is tied to governance rather than intuition.'],
          ['3. Approve or veto explicitly', 'An approval lets the governed path continue; a veto keeps the runtime fail-closed and records a control decision.'],
          ['4. Preserve the rationale', 'Follow up in audit-oriented views so the decision remains explainable to operators, reviewers, and future investigations.'],
        ],
      })}
      <article class="card stack">
        <div><div class="eyebrow muted">Reviewer checklist</div><h3 class="card-title">What to verify before approving</h3><p class="card-subtitle">Keep the human intervention disciplined so this lane strengthens governance instead of bypassing it.</p></div>
        ${keyValue([
          ['Role authority', 'The active role should match the kind of work being requested'],
          ['Action fit', 'The requested action should be covered by the role and policy basis'],
          ['Execution context', 'Check requester, required-by, and current execution outcome'],
          ['Auditability', 'Only approve when the later explanation will still make sense to another reviewer'],
        ])}
      </article>
    </section>
    ${wrapTableCard('Overrides', overrideTable(overrides), 'Human approvals and vetoes that gate governed execution before it may resume.')}
  `;
}

function renderApprovalFlowCard({ eyebrow, title, subtitle, queueStatus, primaryActionView, primaryActionLabel, secondaryActionView, secondaryActionLabel, steps }) {
  const renderedSteps = Array.isArray(steps) ? steps : [];
  return `
    <article class="card stack approval-flow-card">
      <div>
        <div class="eyebrow muted">${escapeHtml(eyebrow || 'Approval flow')}</div>
        <h3 class="card-title">${escapeHtml(title || 'How the approval path works')}</h3>
        <p class="card-subtitle">${escapeHtml(subtitle || 'Make the AI-to-human boundary obvious before you act.')}</p>
      </div>
      <div class="approval-step-list">
        ${renderedSteps.map(([label, body]) => `
          <article class="mini-card stack approval-step">
            <strong>${escapeHtml(label)}</strong>
            <p class="muted">${escapeHtml(body)}</p>
          </article>
        `).join('')}
      </div>
      <div class="trace-box"><strong>Queue status</strong><p class="muted">${escapeHtml(queueStatus || 'No queue status available.')}</p></div>
      <div class="inline-actions">
        ${primaryActionView ? `<button class="action-button" type="button" data-view-jump="${escapeHtml(primaryActionView)}">${escapeHtml(primaryActionLabel || 'Open view')}</button>` : ''}
        ${secondaryActionView ? `<button class="action-button action-button-muted" type="button" data-view-jump="${escapeHtml(secondaryActionView)}">${escapeHtml(secondaryActionLabel || 'Open secondary view')}</button>` : ''}
      </div>
    </article>
  `;
}

function renderRequestComposer(roles) {
  const roleOptions = ['<option value="">AUTO_ROUTE | Context-aware role activation</option>', ...roles.map((role) => `<option value="${escapeHtml(role.role_id)}">${escapeHtml(role.role_id)} | ${escapeHtml(role.title || role.role_id)}</option>`)].join('');
  return `
    <article class="card stack">
      <div><div class="eyebrow muted">Operator Action</div><h3 class="card-title">Create runtime request</h3><p class="card-subtitle">Submit a governed request directly into the private server runtime, with optional context-aware role routing.</p></div>
      <form id="request-form" class="composer-grid">
        <div><label class="permission-note" for="request-requester">Requester</label><input id="request-requester" value="${escapeHtml(state.session?.display_name || '')}" /></div>
        <div><label class="permission-note" for="request-role">Role</label><select id="request-role">${roleOptions}</select></div>
        <div><label class="permission-note" for="request-action">Action</label><input id="request-action" placeholder="review_audit" /></div>
        <div><label class="permission-note" for="request-payload">Payload JSON</label><textarea id="request-payload" class="span-2" placeholder='{"resource":"contract","resource_id":"C-100","amount":3000000}'></textarea></div>
        <div><label class="permission-note" for="request-metadata">Metadata JSON</label><textarea id="request-metadata" class="span-2" placeholder='{"idempotency_key":"REQ-1001","event_stream":"contract:C-100","event_sequence":1}'></textarea></div>
        <div class="span-2 inline-actions"><button class="action-button" type="submit">Submit Request</button></div>
      </form>
    </article>
  `;
}

function renderConflicts(snapshot) {
  const locks = snapshot.locks || [];
  const conflicts = (snapshot.requests || []).filter((item) => item.outcome === 'conflicted');
  const resources = new Set([...locks.map((item) => item.resource).filter(Boolean), ...conflicts.map((item) => item.resource).filter(Boolean)]).size;
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Conflict Command</div>
            <h2 class="hero-title">Resource protection stays visible when concurrency pressure rises.</h2>
            <p class="hero-subtitle">Locks and conflicted requests are surfaced together so operators can distinguish intentional protection from unresolved operational friction.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(conflicts.length ? 'attention required' : 'contention clear')}
          </div>
        </div>
        <div class="hero-split">
          ${keyValue([
            ['Active locks', String(locks.length)],
            ['Conflicted requests', String(conflicts.length)],
            ['Affected resources', String(resources)],
            ['Resolution posture', conflicts.length ? 'review required' : 'monitoring only'],
          ])}
          <div class="hero-note">
            <strong>Concurrency stance</strong>
            <p>SA-NOM holds the resource boundary first. Conflicted requests are a safety signal, not a failure of the runtime, and should be reviewed before manual retries are attempted.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Lock narrative</div>
          <h3 class="card-title">Operational interpretation</h3>
          <p class="card-subtitle">This view helps distinguish active work, approval-held reservations, and requests that need another scheduling path.</p>
        </div>
        ${keyValue([
          ['Protected boundary', locks.length ? 'engaged' : 'idle'],
          ['Retry guidance', conflicts.length ? 'wait for release or review policy' : 'no retry pressure'],
          ['Human review overlap', snapshot.overrides?.some((item) => item.status === 'pending') ? 'possible' : 'none detected'],
          ['Runtime mode', 'fail closed on resource contention'],
        ])}
        <div class="trace-box"><strong>Operator note</strong><p class="muted">If a lock is held by a pending override, resolve the human decision before retrying downstream work on the same protected resource.</p></div>
      </article>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Locks', locks.length, 'accent', 'Resources actively reserved to prevent conflicting execution.')}
      ${metricCard('Conflicts', conflicts.length, 'danger', 'Requests rejected from the active path because the resource was protected.')}
      ${metricCard('Resources', resources, 'default', 'Distinct governed resources touched by the current contention set.')}
      ${metricCard('Override overlap', snapshot.overrides?.filter((item) => item.status === 'pending').length || 0, 'warning', 'Pending human reviews that may be extending lock duration.')}
    </section>
    <section class="split-grid">
      ${wrapTableCard('Active Locks', lockTable(locks), 'Resources currently reserved to prevent concurrent mutation across the governed runtime.')}
      ${wrapTableCard('Conflicted Requests', requestTable(conflicts), 'Requests withheld until lock release, policy changes, or manual review resolves the path.')}
    </section>
  `;
}

function renderAudit(snapshot) {
  const integrity = snapshot.runtime_health?.audit_integrity || {};
  const auditRows = snapshot.audit || [];
  const roleTransitionEvents = auditRows.filter((row) => ['role_activation', 'role_switch', 'role_escalation'].includes(row.action));
  const canReseal = can('audit.manage');
  const maintenanceAction = canReseal && integrity.status === 'legacy_verified'
    ? `<div class="inline-actions"><button class="action-button" data-audit-action="reseal">Reseal Legacy Entries</button></div>`
    : '';
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Audit Command</div>
            <h2 class="hero-title">The audit chain remains a first-class control surface.</h2>
            <p class="hero-subtitle">Integrity state, sealing posture, maintenance readiness, and role-transition trace are visible in one place before anyone touches privileged audit operations.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(integrity.status || 'unknown')}
          </div>
        </div>
        <div class="hero-split">
          ${keyValue([
            ['Integrity status', integrity.status || 'unknown'],
            ['Sealed entries', String(integrity.sealed_entries || 0)],
            ['Role transition events', String(roleTransitionEvents.length)],
            ['Last hash', integrity.last_hash ? integrity.last_hash.slice(0, 12) : '-'],
          ])}
          <div class="hero-note">
            <strong>Ledger posture</strong>
            <p>The audit surface now shows not only what happened, but how hats were activated, switched, and escalated before runtime decisions were allowed to land.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Transition evidence</div>
          <h3 class="card-title">Role movement stays explainable</h3>
          <p class="card-subtitle">Review the exact path from previous role to active role, how activation was sourced, and where the escalation lane now points.</p>
        </div>
        ${keyValue([
          ['Role activation events', String(auditRows.filter((row) => row.action === 'role_activation').length)],
          ['Role switch events', String(auditRows.filter((row) => row.action === 'role_switch').length)],
          ['Role escalation events', String(auditRows.filter((row) => row.action === 'role_escalation').length)],
          ['Maintenance action', canReseal ? 'Available when integrity is legacy_verified' : 'Read only'],
        ])}
        ${maintenanceAction}
      </article>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Audit events', auditRows.length, 'default', 'Current ledger window returned by the private runtime.')}
      ${metricCard('Role transitions', roleTransitionEvents.length, 'accent', 'Activation, switch, and escalation records visible in the ledger.')}
      ${metricCard('Hash mismatches', integrity.hash_mismatches || 0, 'danger', 'Any mismatch should stop trust immediately.')}
      ${metricCard('Sequence drift', integrity.sequence_mismatches || 0, 'warning', 'Ordering defects visible across the chained audit sequence.')}
    </section>
    ${wrapTableCard('Audit Trail', auditTable(auditRows), 'Tamper-evident runtime ledger across requests, role transitions, overrides, sessions, backups, and governance maintenance.')}
  `;
}

function renderStudio(studio) {
  const editing = Boolean(state.studioEditingRequestId);
  const templateFieldCount = Array.isArray(studio.template?.fields) ? studio.template.fields.length : 0;
  const templateLibrary = Array.isArray(studio.template?.library) ? studio.template.library : [];
  const examples = studio.examples || [];
  const requests = studio.requests || [];
  const summary = studio.summary || {};
  const focusedRequest = requests.find((item) => item.request_id === state.studioGovernanceRequestId)
    || requests.find((item) => (item.publish_readiness?.status === 'ready') || item.status === 'approved')
    || requests[0]
    || null;
  state.studioGovernanceRequestId = focusedRequest ? focusedRequest.request_id : null;
  if (focusedRequest) {
    ensureStudioGovernanceNote(focusedRequest);
    ensureStudioRevisionSelection(focusedRequest);
    ensureStudioPtagDraft(focusedRequest);
  }
  const form = can('studio.create') ? `
    <article class="card stack">
      <div>
        <div class="eyebrow muted">Governed Role Authoring</div>
        <h3 class="card-title">${editing ? 'Revise an existing Role Private Studio request' : 'Create a Role Private Studio request'}</h3>
        <p class="card-subtitle">${editing ? 'You are editing the current structured job definition for an existing draft. A new revision will be generated after submit.' : 'Enter the structured job definition. The system will normalize it, generate PTAG, validate it, simulate it, and route it for review.'}</p>
      </div>
      <div class="trace-box"><strong>Studio context</strong><p class="muted">${editing ? `Editing request ${escapeHtml(state.studioEditingRequestId)}` : `Template fields: ${templateFieldCount} | Library templates: ${templateLibrary.length}`}</p></div>
      <form id="studio-form" class="composer-grid">
        <div><label class="permission-note" for="studio-role-name">Role name</label><input id="studio-role-name" placeholder="Contract Review Analyst" /></div>
        <div><label class="permission-note" for="studio-reporting-line">Reporting line</label><input id="studio-reporting-line" value="GOV" /></div>
        <div class="span-2"><label class="permission-note" for="studio-purpose">Purpose</label><textarea id="studio-purpose" placeholder="Review contract packets and route risky documents for human attention."></textarea></div>
        <div><label class="permission-note" for="studio-business-domain">Business domain</label><input id="studio-business-domain" placeholder="legal_operations" /></div>
        <div><label class="permission-note" for="studio-operating-mode">Operating mode</label><select id="studio-operating-mode"><option value="direct">direct</option><option value="indirect">indirect</option></select></div>
        <div><label class="permission-note" for="studio-seat-id">Seat id</label><input id="studio-seat-id" placeholder="OPS-LEGAL" /></div>
        <div><label class="permission-note" for="studio-assigned-user-id">Assigned user id</label><input id="studio-assigned-user-id" placeholder="LEGAL_MANAGER_01" /></div>
        <div><label class="permission-note" for="studio-executive-owner-id">Executive owner id</label><input id="studio-executive-owner-id" value="${escapeHtml(studioExecutiveOwnerId())}" /></div>
        <div><label class="permission-note" for="studio-handled-resources">Handled resources</label><textarea id="studio-handled-resources" placeholder="contract"></textarea></div>
        <div><label class="permission-note" for="studio-allowed-actions">Allowed actions</label><textarea id="studio-allowed-actions" placeholder="review_contract
flag_risk
advise_compliance"></textarea></div>
        <div><label class="permission-note" for="studio-forbidden-actions">Forbidden actions</label><textarea id="studio-forbidden-actions" placeholder="sign_contract"></textarea></div>
        <div><label class="permission-note" for="studio-wait-human-actions">Wait-human actions</label><textarea id="studio-wait-human-actions" placeholder="approve_budget"></textarea></div>
        <div><label class="permission-note" for="studio-responsibilities">Responsibilities</label><textarea id="studio-responsibilities" placeholder="review incoming contracts
flag risk"></textarea></div>
        <div><label class="permission-note" for="studio-sample-scenarios">Sample scenarios</label><textarea id="studio-sample-scenarios" placeholder="normal review
high-value escalation"></textarea></div>
        <div><label class="permission-note" for="studio-financial-sensitivity">Financial sensitivity</label>${selectField('studio-financial-sensitivity')}</div>
        <div><label class="permission-note" for="studio-legal-sensitivity">Legal sensitivity</label>${selectField('studio-legal-sensitivity')}</div>
        <div><label class="permission-note" for="studio-compliance-sensitivity">Compliance sensitivity</label>${selectField('studio-compliance-sensitivity')}</div>
        <div class="span-2"><label class="permission-note" for="studio-operator-notes">Operator notes</label><textarea id="studio-operator-notes" placeholder="Should never sign or approve contracts directly."></textarea></div>
        <div class="span-2 inline-actions">
          <button class="action-button" type="submit">${editing ? 'Update Draft Revision' : 'Create Role Request'}</button>
          ${editing ? '<button class="action-button action-button-muted" type="button" data-studio-clear="true">Clear Editor</button>' : ''}
        </div>
      </form>
      ${examples.length ? `<div class="trace-box"><strong>Example</strong><p class="muted">${escapeHtml(`${examples[0].role_name}: ${examples[0].purpose}`)}</p></div>` : ''}
    </article>` : `<article class="card notice-card stack"><strong>Role request form</strong><p class="permission-note">This profile does not have studio.create permission.</p></article>`;

  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Role Private Studio</div>
            <h2 class="hero-title">Author new hats as governed role packs, not informal prompts.</h2>
            <p class="hero-subtitle">Structured job definitions become reviewable PTAG drafts with validation, simulation, revision history, and publish governance before they ever enter the trusted registry.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(editing ? 'editing draft' : 'authoring ready')}
            ${statusBadge((summary.ready_to_publish_total || 0) ? 'publish candidates' : 'review in motion')}
          </div>
        </div>
        <div class="hero-split">
        ${keyValue([
          ['Requests total', String(summary.requests_total || 0)],
          ['Ready to publish', String(summary.ready_to_publish_total || 0)],
          ['Published', String(summary.published_total || 0)],
          ['Revision volume', String(summary.revisions_total || 0)],
          ])}
          <div class="hero-note">
            <strong>Authoring principle</strong>
            <p>Every hat is treated as governed infrastructure. Role Private Studio is where authority, constraints, and operational sensitivity are shaped into a publishable role pack with traceable review history.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Studio control</div>
          <h3 class="card-title">Editorial posture</h3>
          <p class="card-subtitle">Use this surface to maintain disciplined role creation even when the company runs lean and every AI sibling carries meaningful operational weight.</p>
        </div>
        ${keyValue([
          ['Template fields', String(templateFieldCount)],
          ['Template library', String(templateLibrary.length)],
          ['Examples loaded', String(examples.length)],
          ['Changes requested', String(summary.changes_requested_total || 0)],
          ['Current mode', editing ? 'revision editing' : 'new draft authoring'],
        ])}
        <div class="trace-box"><strong>Studio note</strong><p class="muted">${escapeHtml(examples.length ? `${examples[0].role_name}: ${examples[0].purpose}` : 'No example loaded. Build the next governed hat from the structured form at left.')}</p></div>
      </article>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Studio requests', summary.requests_total || 0, 'default', 'Structured job definitions currently tracked by the studio.')}
      ${metricCard('Ready to publish', summary.ready_to_publish_total || 0, 'success', 'Drafts that cleared validation, simulation, and review gates.')}
      ${metricCard('Blocked', summary.blocked_total || 0, 'danger', 'Drafts that still have blockers before publication can proceed.')}
      ${metricCard('Published', summary.published_total || 0, 'accent', 'Role hats already promoted into the trusted registry.')}
      ${metricCard('Revisions', summary.revisions_total || 0, 'default', 'Total revision count across all tracked studio drafts.')}
      ${metricCard('Changes requested', summary.changes_requested_total || 0, 'warning', 'Drafts pushed back for another governed revision cycle.')}
      ${metricCard('Templates', templateLibrary.length, 'accent', 'Reusable governed starting points for faster role creation.')}
    </section>
    <section class="split-grid">
      ${form}
      <article class="card stack">
        <div><div class="eyebrow muted">Publish discipline</div><h3 class="card-title">What makes a hat production worthy</h3><p class="card-subtitle">A Role Private Studio draft is not finished when it looks plausible. It is ready only when governance gates, simulation posture, and review history say it can be trusted.</p></div>
        ${keyValue([
          ['Authoring path', 'Structured JD -> PTAG -> validation -> simulation -> approval -> publish'],
          ['Registry destination', 'Trusted role registry with manifest verification'],
          ['Review expectation', (summary.ready_to_publish_total || 0) ? 'Candidates available for governed publish review' : 'No publish-ready drafts yet'],
          ['Operational stance', 'No direct publish without review evidence'],
        ])}
        <div class="trace-box"><strong>Operator note</strong><p class="muted">Use responsibilities, sensitivities, and handled resources to shape the hat. Those details influence authority boundaries, simulation quality, and publish readiness.</p></div>
      </article>
    </section>
    ${renderTemplateLibrary(templateLibrary)}
    ${renderStudioGovernanceScreen(requests)}
    ${renderStudioGovernancePanel(focusedRequest)}
    <section class="card-grid">${requests.length ? requests.map(renderStudioRequestCard).join('') : `<div class="empty-state">No Role Private Studio requests yet.</div>`}</section>
  `;
}

function renderStudioGovernanceScreen(requests) {
  const structuralReview = requests.filter((item) => item.publish_readiness?.status === 'guarded');
  const publishReady = requests.filter((item) => (item.publish_readiness?.status === 'ready') || item.status === 'approved');
  const reviewQueue = requests.filter(
    (item) => item.status !== 'published' && !publishReady.includes(item) && !structuralReview.includes(item),
  );
  const published = requests.filter((item) => item.status === 'published');
  return `
    <section class="split-grid">
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Publish Governance</div>
          <h3 class="card-title">Promotion into the trusted registry happens through a visible governance lane.</h3>
          <p class="card-subtitle">This screen separates publish-ready hats, PT-OSS structural review, editorial review, and already published hats so the Studio reads like a disciplined promotion pipeline instead of a pile of drafts.</p>
        </div>
        ${keyValue([
          ['Ready lane', String(publishReady.length)],
          ['Structural lane', String(structuralReview.length)],
          ['Review lane', String(reviewQueue.length)],
          ['Published lane', String(published.length)],
          ['Registry mode', 'Human-governed publication'],
        ])}
        <div class="trace-box"><strong>Governance note</strong><p class="muted">Publish only from the ready lane. Drafts in structural review should resolve PT-OSS pressure before they become trusted hats, while drafts outside those lanes should receive clearer review or revision.</p></div>
      </article>
      <article class="card stack">
        <div><div class="eyebrow muted">Promotion rules</div><h3 class="card-title">What this screen is for</h3><p class="card-subtitle">A focused area for reviewers and publishers to decide what advances, what returns for revision, and what already counts as a trusted operational hat.</p></div>
        ${keyValue([
          ['Ready signal', 'Approved status or readiness gate marked ready'],
          ['Structural signal', 'PT-OSS marked the draft guarded before publication'],
          ['Review signal', 'Anything not published and not yet structurally or promotion ready'],
          ['Published signal', 'Role pack already promoted into the trusted registry'],
          ['Decision style', 'Structure first, review second, publish only from clear readiness'],
        ])}
      </article>
    </section>
    <section class="studio-governance-grid">
      ${renderStudioGovernanceLane('Ready for Publish', 'Trusted promotion lane', 'Drafts that cleared review and can be published into the registry.', publishReady, 'ready', 'success')}
      ${renderStudioGovernanceLane('Structural Review', 'PT-OSS mitigation lane', 'Drafts that need structural mitigation or stronger resilience posture before publication.', structuralReview, 'structural', 'warning')}
      ${renderStudioGovernanceLane('Needs Review', 'Editorial and governance lane', 'Drafts that still need approval, changes, or another revision before promotion.', reviewQueue, 'review', 'accent')}
      ${renderStudioGovernanceLane('Published Hats', 'Registry confirmation lane', 'Drafts already promoted into trusted operational use.', published, 'published', 'default')}
    </section>
  `;
}

function renderTemplateLibrary(library) {
  if (!library.length) return '';
  return `
    <section class="split-grid">
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Template Library</div>
          <h3 class="card-title">Start from governed patterns instead of rebuilding every hat from zero.</h3>
          <p class="card-subtitle">Templates accelerate authoring while keeping sensitivity, escalation, and operational shape inside a disciplined baseline.</p>
        </div>
        ${keyValue([
          ['Template count', String(library.length)],
          ['Categories', Array.from(new Set(library.map((item) => item.category).filter(Boolean))).join(', ') || '-'],
          ['Workflow', 'Preview -> Apply -> Refine -> Validate -> Simulate -> Review'],
          ['Purpose', 'Reusable but still fully governed'],
        ])}
      </article>
      <article class="card stack">
        <div><div class="eyebrow muted">Apply flow</div><h3 class="card-title">Preview then apply</h3><p class="card-subtitle">Applying a template fills the Studio authoring form. It does not bypass validation, simulation, or review.</p></div>
        <div class="trace-box"><strong>Template note</strong><p class="muted">Templates are accelerators, not shortcuts. Every applied template still becomes a normal governed draft and must pass the full Role Private Studio flow.</p></div>
      </article>
    </section>
    <section class="card-grid">
      ${library.map((item) => `
        <article class="card stack template-card">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">${escapeHtml(item.category || 'template')}</div>
              <h3 class="card-title">${escapeHtml(item.label || item.template_id || 'Template')}</h3>
              <p class="card-subtitle">${escapeHtml(item.summary || 'Governed role template.')}</p>
            </div>
            <div class="hero-chip-row">${statusBadge(item.category || 'template')}</div>
          </div>
          ${keyValue([
            ['Role name', item.payload?.role_name || '-'],
            ['Reports to', item.payload?.reporting_line || '-'],
            ['Domain', item.payload?.business_domain || '-'],
            ['Mode', item.payload?.operating_mode || 'direct'],
            ['Allowed actions', String((item.payload?.allowed_actions || []).length)],
          ])}
          <div class="trace-box compact-trace"><strong>Template preview</strong><p class="muted">${escapeHtml((item.payload?.responsibilities || []).join(' | ') || 'No responsibilities listed.')}</p></div>
          ${can('studio.create') ? `<div class="inline-actions"><button class="action-button" data-studio-template-apply="true" data-template-id="${escapeHtml(item.template_id || '')}">Apply Template</button></div>` : '<div class="trace-box compact-trace"><p class="muted">Read only</p></div>'}
        </article>
      `).join('')}
    </section>
  `;
}

function renderStudioGovernanceLane(title, eyebrow, subtitle, items, lane, tone = 'default') {
  return `
    <article class="card stack studio-governance-lane studio-governance-lane-${escapeHtml(tone)}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(eyebrow)}</div>
          <h3 class="card-title">${escapeHtml(title)}</h3>
          <p class="card-subtitle">${escapeHtml(subtitle)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${items.length} items`)}${statusBadge(title)}</div>
      </div>
      ${items.length ? `<div class="stack">${items.slice(0, 4).map((item) => renderStudioGovernanceItem(item, lane)).join('')}</div>` : `<div class="empty-state">No items in this lane.</div>`}
    </article>
  `;
}

function renderStudioGovernanceItem(item, lane) {
  const readiness = item.publish_readiness || { status: 'blocked', blockers: [] };
  const summary = item.summary || {};
  const validation = item.validation_report || {};
  const simulation = item.simulation_report || {};
  const canApprove = can('studio.review') && !['published', 'approved'].includes(item.status);
  const canRequestChanges = can('studio.review') && item.status !== 'published';
  const canPublish = can('studio.publish') && item.status === 'approved';
  const canEdit = can('studio.create') && item.status !== 'published';
  const isSelected = state.studioGovernanceRequestId === item.request_id;
  const laneNote = lane === 'ready'
    ? 'Ready for trusted publication.'
    : lane === 'structural'
      ? (readiness.structural_gate_reason || (readiness.advisories || []).join(' | ') || 'Awaiting PT-OSS structural mitigation before it can return to the publish lane.')
    : lane === 'published'
      ? (item.publish_artifact ? `${item.publish_artifact.role_path}` : 'Published into the trusted registry.')
      : readiness.status === 'guarded'
        ? (readiness.structural_gate_reason || (readiness.advisories || []).join(' | ') || 'Awaiting PT-OSS structural mitigation.')
        : (readiness.blockers?.length ? readiness.blockers.join(' | ') : 'Awaiting review movement.');
  return `
    <div class="trace-box stack governance-lane-item${isSelected ? ' is-selected' : ''}${isFocusedEntity('studio_request', item.request_id) ? ' focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey('studio_request', item.request_id))}">
      <div class="hero-heading">
        <div>
          <strong>${escapeHtml(item.structured_jd?.role_name || item.request_id)}</strong>
          <p class="muted">${escapeHtml(`${summary.role_id || item.request_id} | Revision ${summary.current_revision || 0}`)}</p>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(item.status)}
          ${statusBadge(readiness.status || 'blocked')}
        </div>
      </div>
      ${keyValue([
        ['Requested by', item.requested_by],
        ['Simulation', simulation.status || 'not_run'],
        ['Validation blocked', String(validation.blocked_publish ?? true)],
        ['Blockers', String((readiness.blockers || []).length)],
        ['Structural gate', readiness.structural_state || 'blocked'],
      ])}
      <p class="muted">${escapeHtml(laneNote)}</p>
      <div class="governance-mini-grid">
        <div class="trace-box compact-trace"><strong>Change scope</strong><p class="muted">${escapeHtml(renderLatestDiff(summary.latest_diff || {}))}</p></div>
        <div class="trace-box compact-trace"><strong>Review signal</strong><p class="muted">${escapeHtml(renderPublishDecisionSummary(item, readiness, validation, simulation))}</p></div>
      </div>
      <div class="inline-actions">
        <button class="action-button ${isSelected ? '' : 'action-button-muted'}" data-studio-governance-select="true" data-request-id="${escapeHtml(item.request_id)}">${isSelected ? 'Selected' : 'Open Panel'}</button>
        ${can('human_ask.create') ? `<button class="action-button action-button-muted" data-human-ask-action="studio-record" data-request-id="${escapeHtml(item.request_id)}" data-entry-label="${escapeHtml(item.structured_jd?.role_name || item.request_id)}">Start Report</button>` : ''}
        ${canEdit ? `<button class="action-button action-button-muted" data-studio-action="load" data-request-id="${escapeHtml(item.request_id)}">Load</button>` : ''}
        ${canApprove ? `<button class="action-button action-button-muted" data-studio-action="approve" data-request-id="${escapeHtml(item.request_id)}">Approve</button>` : ''}
        ${canRequestChanges ? `<button class="action-button action-button-muted" data-studio-action="request_changes" data-request-id="${escapeHtml(item.request_id)}">Changes</button>` : ''}
        ${canPublish ? `<button class="action-button" data-studio-action="publish" data-request-id="${escapeHtml(item.request_id)}">Publish</button>` : ''}
      </div>
    </div>
  `;
}

function renderStudioGovernancePanel(item) {
  if (!item) {
    return '<article class="card stack"><div><div class="eyebrow muted">Governance panel</div><h3 class="card-title">No draft selected</h3><p class="card-subtitle">Select a Role Private Studio draft from the governance lanes to review or publish it here.</p></div></article>';
  }
  const readiness = item.publish_readiness || { status: 'blocked', blockers: [], gates: {} };
  const validation = item.validation_report || {};
  const simulation = item.simulation_report || {};
  const summary = item.summary || {};
  const workflow = item.publication_workflow || {};
  const coverage = item.coverage_summary || {};
  const ptOss = item.pt_oss_assessment || {};
  const noteValue = ensureStudioGovernanceNote(item);
  const revisionCompare = buildStudioRevisionCompare(item, true);
  const ptagDraft = ensureStudioPtagDraft(item);
   const editorCompare = summary.editor_compare || readiness.editor_compare || {};
   const reviewTimeline = summary.review_timeline || workflow.review_timeline || [];
   const simulationHistory = summary.simulation_history || [];
   const selectedRevision = ensureStudioRevisionSelection(item);
  const canApprove = can('studio.review') && !['published', 'approved'].includes(item.status);
  const canRequestChanges = can('studio.review') && item.status !== 'published';
  const canPublish = can('studio.publish') && item.status === 'approved';
  const canRefresh = can('studio.create') && item.status !== 'published';
  const canLoad = can('studio.create') && item.status !== 'published';
  const canEditPtag = can('studio.create') && item.status !== 'published';
  const canRestore = can('studio.create') && item.status !== 'published' && (selectedRevision.current_revision_number || 0) > 0;
  const diagnostics = buildStudioPtagDiagnostics(item, ptagDraft);
  return `
    <section class="split-grid${isFocusedEntity('studio_request', item.request_id) ? ' focused-record' : ''}" id="studio-governance-panel-anchor" data-focus-key="${escapeHtml(buildFocusKey('studio_request', item.request_id))}">
      <article class="card hero-card hero-card-secondary studio-governance-panel">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Live publish approval panel</div>
            <h3 class="card-title">${escapeHtml(item.structured_jd?.role_name || item.request_id)}</h3>
            <p class="card-subtitle">Use this panel to review, request changes, refresh, or publish the selected hat without leaving the governance screen.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(item.status)}
            ${statusBadge(readiness.status || 'blocked')}
          </div>
        </div>
        ${keyValue([
          ['Request', item.request_id],
          ['Role id', summary.role_id || '-'],
          ['Mode', summary.operating_mode || item.structured_jd?.operating_mode || 'direct'],
          ['Assigned user', summary.assigned_user_id || item.structured_jd?.assigned_user_id || '-'],
          ['Executive owner', summary.executive_owner_id || item.structured_jd?.executive_owner_id || studioExecutiveOwnerId()],
          ['Seat', summary.seat_id || item.structured_jd?.seat_id || '-'],
          ['Revision', String(summary.current_revision || 0)],
          ['Requested by', item.requested_by],
          ['Latest review', summary.latest_review_decision || 'none'],
          ['Simulation', simulation.status || 'not_run'],
          ['PT-OSS posture', summary.pt_oss_posture || ptOss.posture || 'unknown'],
          ['Structural gate', readiness.structural_state || 'blocked'],
          ['PTAG mode', summary.ptag_source_mode || 'generated'],
        ])}
        <div class="trace-box"><strong>Decision guidance</strong><p class="muted">${escapeHtml(renderPublishDecisionSummary(item, readiness, validation, simulation))}</p></div>
        ${readiness.structural_gate_reason ? `<div class="trace-box compact-trace"><strong>Structural gate note</strong><p class="muted">${escapeHtml(readiness.structural_gate_reason)}</p></div>` : ''}
        ${renderPublicationWorkflow(workflow)}
      </article>
      <article class="card stack studio-governance-panel">
        <div><div class="eyebrow muted">Governance note</div><h3 class="card-title">Reviewer and publisher actions</h3><p class="card-subtitle">Record the note that should travel with the decision, then take the action from here.</p></div>
        <textarea id="studio-governance-note" class="studio-governance-note" placeholder="Approved for publish because validation passed, simulation passed, and authority boundaries are appropriate.">${escapeHtml(noteValue)}</textarea>
        ${renderGateSummary(readiness.gates || {})}
        <div class="inline-actions">
          ${can('human_ask.create') ? `<button class="action-button action-button-muted" data-human-ask-action="studio-record" data-request-id="${escapeHtml(item.request_id)}" data-entry-label="${escapeHtml(item.structured_jd?.role_name || item.request_id)}">Start Report</button>` : ''}
          ${canLoad ? `<button class="action-button action-button-muted" data-studio-panel-action="load" data-request-id="${escapeHtml(item.request_id)}">Load into Editor</button>` : ''}
          ${canRefresh ? `<button class="action-button action-button-muted" data-studio-panel-action="refresh" data-request-id="${escapeHtml(item.request_id)}">Refresh Draft</button>` : ''}
          ${canRestore ? `<button class="action-button action-button-muted" data-studio-panel-action="restore_revision" data-request-id="${escapeHtml(item.request_id)}">Restore Review Revision</button>` : ''}
          ${canApprove ? `<button class="action-button" data-studio-panel-action="approve" data-request-id="${escapeHtml(item.request_id)}">Approve</button>` : ''}
          ${canRequestChanges ? `<button class="action-button action-button-muted" data-studio-panel-action="request_changes" data-request-id="${escapeHtml(item.request_id)}">Request Changes</button>` : ''}
          ${canPublish ? `<button class="action-button" data-studio-panel-action="publish" data-request-id="${escapeHtml(item.request_id)}">Publish Now</button>` : ''}
        </div>
        ${renderReadinessSummary(readiness, coverage)}
      </article>
    </section>
    <section class="studio-governance-grid">
      <article class="card stack studio-governance-panel">
        <div><div class="eyebrow muted">Readiness reporting</div><h3 class="card-title">Publish posture at a glance</h3><p class="card-subtitle">Coverage, blockers, and readiness score are grouped here so reviewers can judge the hat quickly without scanning every raw report first.</p></div>
        ${renderCoverageSummary(coverage)}
      </article>
      <article class="card stack studio-governance-panel">
        <div><div class="eyebrow muted">PT-OSS structural intelligence</div><h3 class="card-title">Structural readiness and fragility posture</h3><p class="card-subtitle">Use PT-OSS to judge whether the hat is structurally safe, resilient, and governed strongly enough before publication.</p></div>
        ${renderPtOssAssessment(ptOss)}
      </article>
      <article class="card stack studio-governance-panel">
        <div><div class="eyebrow muted">Review timeline</div><h3 class="card-title">Decision history</h3><p class="card-subtitle">Every approval and change request remains visible as a reviewer-facing audit trail.</p></div>
        ${renderReviewTimeline(reviewTimeline)}
      </article>
      <article class="card stack studio-governance-panel">
        <div><div class="eyebrow muted">Simulation history</div><h3 class="card-title">Simulation runs across revisions</h3><p class="card-subtitle">See whether the hat is getting safer or drifting before you publish it.</p></div>
        ${renderSimulationHistory(simulationHistory)}
      </article>
    </section>
    <section class="split-grid">
      <article class="card stack studio-governance-panel">
        <div><div class="eyebrow muted">PTAG live editor</div><h3 class="card-title">Refine the role pack directly before publication</h3><p class="card-subtitle">Edit the PTAG source for the selected hat, keep it inside governance, then revalidate and resimulate through the Studio runtime.</p></div>
        <div class="trace-box compact-trace"><strong>Editing mode</strong><p class="muted">${escapeHtml(summary.ptag_override_present ? 'Manual PTAG override is active for this revision.' : 'Generated PTAG is currently active. Save a draft here to switch the revision into manual PTAG mode.')}</p></div>
        <div class="studio-editor-shell">
          <pre id="studio-ptag-gutter" class="studio-ptag-gutter">${escapeHtml(renderLineNumbers(ptagDraft))}</pre>
          <textarea id="studio-ptag-editor" class="studio-ptag-editor" placeholder="role NEW_ROLE { ... }">${escapeHtml(ptagDraft)}</textarea>
        </div>
        <div class="inline-actions">
          ${canEditPtag ? `<button class="action-button" data-studio-panel-action="save_ptag" data-request-id="${escapeHtml(item.request_id)}">Save PTAG Draft</button>` : ''}
          ${canEditPtag ? `<button class="action-button action-button-muted" data-studio-panel-action="reset_ptag" data-request-id="${escapeHtml(item.request_id)}">Reset to Generated</button>` : ''}
          ${canEditPtag ? `<button class="action-button action-button-muted" data-studio-panel-action="undo_ptag" data-request-id="${escapeHtml(item.request_id)}">Undo</button>` : ''}
          ${canEditPtag ? `<button class="action-button action-button-muted" data-studio-panel-action="redo_ptag" data-request-id="${escapeHtml(item.request_id)}">Redo</button>` : ''}
        </div>
        <div id="studio-ptag-diagnostics">${renderPtagDiagnostics(diagnostics)}</div>
      </article>
      <article class="card stack studio-governance-panel">
        <div><div class="eyebrow muted">Publication workflow</div><h3 class="card-title">Role publication approval path</h3><p class="card-subtitle">Use this path to verify where the hat sits now: authored, validated, simulated, approved, or already promoted into the trusted registry.</p></div>
        ${renderPublicationWorkflow(workflow, true)}
        ${renderBlockerGroups(readiness)}
      </article>
    </section>
    <section class="split-grid">
      <article class="card stack studio-governance-panel">
        <div><div class="eyebrow muted">Generated versus manual</div><h3 class="card-title">Baseline compare</h3><p class="card-subtitle">Judge the edited PTAG against the generator baseline before you approve or publish it.</p></div>
        ${renderEditorCompare(editorCompare, item.system_generated_ptag || '', ptagDraft)}
      </article>
      <article class="card stack studio-governance-panel">
        <div><div class="eyebrow muted">Approval summary</div><h3 class="card-title">Publisher-ready summary cards</h3><p class="card-subtitle">This condensed view keeps the final publish decision anchored to evidence, not memory.</p></div>
        ${renderApprovalSummaryCards(readiness, validation, simulation, workflow)}
      </article>
    </section>
    <article class="card stack studio-governance-panel">
      <div><div class="eyebrow muted">Revision control</div><h3 class="card-title">Compare any governed revision pair before the publish decision</h3><p class="card-subtitle">Choose the revision under review and the revision it should be judged against. This keeps review grounded in evidence instead of memory.</p></div>
      ${renderStudioRevisionCompare(revisionCompare, { requestId: item.request_id, selectable: true, currentLabel: 'Review revision', previousLabel: 'Compare against' })}
    </article>
  `;
}

function defaultStudioGovernanceNote(item) {
  if (item.status === 'approved') return 'Approved for publish from the live governance panel.';
  if (item.status === 'published') return 'Already published into the trusted registry.';
  return 'Reviewed from the live governance panel.';
}

function defaultStudioGovernanceActionNote(item, action) {
  if (action === 'approve') return 'Approved for publish from the live governance panel.';
  if (action === 'request_changes') return 'Please refine the role draft, regenerate the PTAG pack, and resimulate before returning it to the publish lane.';
  if (action === 'publish') {
    return item?.publish_artifact
      ? 'Already published into the trusted registry.'
      : 'Publishing into the trusted registry from the live governance panel.';
  }
  return defaultStudioGovernanceNote(item || { status: '' });
}

function getStudioRequestById(requestId) {
  const requests = state.snapshot?.role_private_studio?.requests || [];
  return requests.find((item) => item.request_id === requestId) || null;
}

function ensureStudioGovernanceNote(item, forcedNote = null) {
  if (!item) return '';
  if (typeof forcedNote === 'string') {
    state.studioGovernanceNotes[item.request_id] = forcedNote;
    return forcedNote;
  }
  if (Object.prototype.hasOwnProperty.call(state.studioGovernanceNotes, item.request_id)) {
    return state.studioGovernanceNotes[item.request_id];
  }
  const note = defaultStudioGovernanceNote(item);
  state.studioGovernanceNotes[item.request_id] = note;
  return note;
}

function ensureStudioPtagDraft(item, forcedSource = null) {
  if (!item) return '';
  if (typeof forcedSource === 'string') {
    state.studioPtagDrafts[item.request_id] = forcedSource;
    ensureStudioPtagHistory(item.request_id, forcedSource);
    return forcedSource;
  }
  if (Object.prototype.hasOwnProperty.call(state.studioPtagDrafts, item.request_id)) {
    return state.studioPtagDrafts[item.request_id];
  }
  const source = item.generated_ptag || '';
  state.studioPtagDrafts[item.request_id] = source;
  ensureStudioPtagHistory(item.request_id, source);
  return source;
}

function ensureStudioPtagHistory(requestId, source = '') {
  if (!requestId) return null;
  if (!state.studioPtagHistory[requestId]) {
    state.studioPtagHistory[requestId] = { undo: [], redo: [], current: source };
  }
  if (typeof source === 'string' && !state.studioPtagHistory[requestId].current) {
    state.studioPtagHistory[requestId].current = source;
  }
  return state.studioPtagHistory[requestId];
}

function recordStudioPtagUndo(requestId, previousValue, nextValue) {
  if (!requestId || previousValue === nextValue) return;
  const history = ensureStudioPtagHistory(requestId, previousValue);
  if (!history) return;
  if (!history.undo.length || history.undo[history.undo.length - 1] !== previousValue) {
    history.undo.push(previousValue);
    if (history.undo.length > 60) history.undo.shift();
  }
  history.current = nextValue;
  history.redo = [];
}

function resetStudioPtagHistory(requestId) {
  if (!requestId) return;
  delete state.studioPtagHistory[requestId];
}

function undoStudioPtagDraft(requestId) {
  const history = ensureStudioPtagHistory(requestId);
  if (!history || !history.undo.length) return null;
  const previousValue = history.undo.pop();
  history.redo.push(history.current || '');
  history.current = previousValue;
  return previousValue;
}

function redoStudioPtagDraft(requestId) {
  const history = ensureStudioPtagHistory(requestId);
  if (!history || !history.redo.length) return null;
  const nextValue = history.redo.pop();
  history.undo.push(history.current || '');
  history.current = nextValue;
  return nextValue;
}

function renderPublicationWorkflow(workflow, expanded = false) {
  const stages = Array.isArray(workflow?.stages) ? workflow.stages : [];
  if (!stages.length) return '<div class="trace-box"><strong>Workflow</strong><p class="muted">No publication workflow is available for this draft yet.</p></div>';
  const rows = stages.map((stage) => `
    <div class="workflow-stage">
      <div>
        <strong>${escapeHtml(stage.label || stage.id || 'Stage')}</strong>
        ${expanded ? `<p class="muted">${escapeHtml(renderWorkflowStageExplanation(stage))}</p>` : ''}
      </div>
      ${statusBadge(stage.status || 'pending')}
    </div>
  `).join('');
  const meta = [];
  if (workflow.latest_reviewer) meta.push(['Latest reviewer', workflow.latest_reviewer]);
  if (workflow.latest_review_decision) meta.push(['Latest decision', workflow.latest_review_decision]);
  if (workflow.published_by) meta.push(['Published by', workflow.published_by]);
  if (workflow.published_at) meta.push(['Published at', shortTime(workflow.published_at)]);
  return `
    <div class="workflow-shell">
      <div class="workflow-stage-list">${rows}</div>
      ${meta.length ? `<div class="trace-box compact-trace">${keyValue(meta)}</div>` : ''}
      ${expanded && workflow.latest_review_note ? `<div class="trace-box compact-trace"><strong>Latest review note</strong><p class="muted">${escapeHtml(workflow.latest_review_note)}</p></div>` : ''}
    </div>
  `;
}

function renderReadinessSummary(readiness, coverage) {
  const score = Number(readiness.readiness_score || 0);
  return `
    <section class="publish-gate-grid">
      ${metricCard('Readiness score', score, score >= 80 ? 'success' : score >= 55 ? 'warning' : 'danger', 'Overall publish posture across validation, simulation, review, and coverage.')}
      ${metricCard('Blockers', (readiness.blockers || []).length, (readiness.blockers || []).length ? 'danger' : 'success', 'Current blockers attached to the active revision.')}
      ${metricCard('Structural gate', readiness.structural_state || 'blocked', studioReadinessTone(readiness), 'PT-OSS gate applied to the active revision before publication.')}
      ${metricCard('Structural advisories', (readiness.advisories || []).length, (readiness.advisories || []).length ? 'warning' : 'success', 'PT-OSS advisories that still shape publication movement even without hard blockers.')}
      ${metricCard('Policy coverage', `${coverage.policy?.covered_actions || 0}/${coverage.policy?.total_actions || 0}`, coverage.policy?.status === 'ready' ? 'success' : 'warning', 'Allowed actions currently covered by policy validation.')}
      ${metricCard('Simulation', coverage.simulation?.status || 'not_run', coverage.simulation?.status === 'passed' ? 'success' : coverage.simulation?.status === 'failed' ? 'danger' : 'warning', 'Latest simulation posture for the active revision.')}
    </section>
  `;
}

function renderCoverageSummary(coverage) {
  return `
    <section class="governance-mini-grid">
      <article class="trace-box compact-trace">
        <strong>Policy coverage</strong>
        ${keyValue([
          ['Status', coverage.policy?.status || 'unknown'],
          ['Covered actions', `${coverage.policy?.covered_actions || 0}/${coverage.policy?.total_actions || 0}`],
          ['Gaps', (coverage.policy?.gaps || []).length ? coverage.policy.gaps.join(' | ') : 'None'],
        ])}
      </article>
      <article class="trace-box compact-trace">
        <strong>Hierarchy coverage</strong>
        ${keyValue([
          ['Status', coverage.hierarchy?.status || 'unknown'],
          ['Reports to', coverage.hierarchy?.reports_to || '-'],
          ['Escalation field', coverage.hierarchy?.escalation_defined ? 'present' : 'missing'],
          ['Safety owner', coverage.hierarchy?.safety_owner_defined ? 'present' : 'missing'],
        ])}
      </article>
      <article class="trace-box compact-trace">
        <strong>Escalation and safety</strong>
        ${keyValue([
          ['Status', coverage.escalation?.status || 'unknown'],
          ['Wait-human actions', (coverage.escalation?.wait_human_actions || []).join(', ') || '-'],
          ['Auto safety upgrades', (coverage.escalation?.auto_wait_human_actions || []).join(', ') || '-'],
        ])}
      </article>
      <article class="trace-box compact-trace">
        <strong>Simulation posture</strong>
        ${keyValue([
          ['Status', coverage.simulation?.status || 'not_run'],
          ['Scenarios', String(coverage.simulation?.scenario_count || 0)],
          ['Failed', String(coverage.simulation?.failed_count || 0)],
          ['Categories', (coverage.simulation?.categories || []).join(', ') || '-'],
        ])}
      </article>
    </section>
  `;
}

function renderPtOssAssessment(assessment) {
  if (!assessment || !assessment.metrics) {
    return '<div class="trace-box"><strong>Structural assessment</strong><p class="muted">PT-OSS assessment is not available for this draft yet.</p></div>';
  }
  const metrics = Array.isArray(assessment.metrics) ? assessment.metrics : [];
  const blockers = Array.isArray(assessment.blockers) ? assessment.blockers : [];
  const recommendations = Array.isArray(assessment.recommendations) ? assessment.recommendations : [];
  return `
    <section class="publish-gate-grid">
      ${metricCard('Structural score', assessment.readiness_score || 0, (assessment.readiness_score || 0) >= 80 ? 'success' : (assessment.readiness_score || 0) >= 55 ? 'warning' : 'danger', 'PT-OSS structural readiness for the active draft.')}
      ${metricCard('Posture', assessment.posture || 'unknown', assessment.posture === 'healthy' ? 'success' : assessment.posture === 'watch' ? 'warning' : 'danger', 'Overall PT-OSS structural posture.')}
      ${metricCard('Blocking issues', assessment.blocking_issue_count || blockers.filter((item) => item.blocks_publish).length, (assessment.blocking_issue_count || blockers.filter((item) => item.blocks_publish).length) ? 'danger' : 'success', 'Structural blockers that should stop publish.')}
      ${metricCard('Mode', assessment.mode || 'PT_OSS_FULL', 'accent', 'PT-OSS mode selected for this draft.')}
    </section>
    <section class="governance-mini-grid">
      ${metrics.map((item) => `
        <article class="trace-box compact-trace">
          <strong>${escapeHtml(item.metric_id || item.name || 'Metric')}</strong>
          ${keyValue([
            ['Value', `${item.value ?? '-'} ${item.unit || ''}`.trim()],
            ['Band', item.label || 'unknown'],
            ['Risk', item.risk_level || 'unknown'],
            ['Action', item.default_action ? titleCase(String(item.default_action).replace(/_/g, ' ')) : '-'],
          ])}
          <p class="muted">${escapeHtml(item.rationale || 'No rationale recorded.')}</p>
        </article>
      `).join('')}
    </section>
    <section class="split-grid">
      <article class="trace-box compact-trace">
        <strong>Structural blockers</strong>
        <p class="muted">${escapeHtml(blockers.length ? blockers.map((item) => `${item.category}: ${item.message}`).join(' | ') : 'No PT-OSS structural blockers are active for this draft.')}</p>
      </article>
      <article class="trace-box compact-trace">
        <strong>Recommendations</strong>
        <p class="muted">${escapeHtml(recommendations.length ? recommendations.join(' | ') : 'No PT-OSS recommendations were generated.')}</p>
      </article>
    </section>
  `;
}

function renderReviewTimeline(timeline) {
  if (!timeline.length) return '<p class="muted">No reviewer decisions recorded yet.</p>';
  return timeline.map((item) => `
    <div class="trace-box compact-trace timeline-card">
      <div class="hero-heading">
        <div>
          <strong>${escapeHtml(titleCase(item.decision || 'review'))}</strong>
          <p class="muted">${escapeHtml(`Revision ${item.revision_number || 0} ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¾ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â· ${item.reviewer || '-'}`)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(item.decision || 'review')}</div>
      </div>
      <p class="muted">${escapeHtml(item.note || 'No reviewer note recorded.')}</p>
      <p class="muted">${escapeHtml(shortTime(item.created_at))}</p>
    </div>
  `).join('');
}

function renderSimulationHistory(history) {
  if (!history.length) return '<p class="muted">No simulation history recorded yet.</p>';
  return history.map((item) => `
    <div class="trace-box compact-trace timeline-card">
      <div class="hero-heading">
        <div>
          <strong>${escapeHtml(`Revision ${item.revision_number || 0}`)}</strong>
          <p class="muted">${escapeHtml(`${item.trigger || 'refresh'} ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¾ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â· ${shortTime(item.generated_at)}`)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(item.status || 'not_run')}</div>
      </div>
      ${keyValue([
        ['Scenarios', String(item.scenario_count || 0)],
        ['Passed', String(item.passed_count || 0)],
        ['Failed', String(item.failed_count || 0)],
        ['Waiting human', String(item.waiting_human_count || 0)],
      ])}
    </div>
  `).join('');
}

function renderEditorCompare(compare, generatedBaseline, currentDraft) {
  const baselinePreview = renderPtagPreview(generatedBaseline || 'No generated PTAG baseline recorded.');
  const currentPreview = renderPtagPreview(currentDraft || 'No PTAG draft available.');
  return `
    <section class="revision-compare-grid">
      <article class="trace-box compact-trace compare-panel">
        <strong>Generated baseline</strong>
        ${keyValue([
          ['Mode', compare.manual_override_active ? 'generated baseline' : compare.mode || 'generated'],
          ['Lines', String(compare.generated_line_count || 0)],
        ])}
        <pre class="code-preview">${escapeHtml(baselinePreview)}</pre>
      </article>
      <article class="trace-box compact-trace compare-panel">
        <strong>Current draft</strong>
        ${keyValue([
          ['Mode', compare.mode || 'generated'],
          ['Lines', String(compare.current_line_count || 0)],
          ['Delta', `+${compare.added_lines || 0} / -${compare.removed_lines || 0}`],
        ])}
        <pre class="code-preview">${escapeHtml(currentPreview)}</pre>
      </article>
    </section>
  `;
}

function renderApprovalSummaryCards(readiness, validation, simulation, workflow) {
  const reviewTimeline = workflow.review_timeline || [];
  return `
    <section class="governance-mini-grid">
      ${metricCard('Stage status', workflow.status || 'blocked', workflow.status === 'published' ? 'success' : workflow.status === 'publisher_ready' ? 'accent' : workflow.status === 'structural_review' ? 'warning' : 'warning', 'Current publication stage outcome.')}
      ${metricCard('Structural gate', readiness.structural_state || 'blocked', studioReadinessTone(readiness), 'PT-OSS decision posture applied to the active revision.')}
      ${metricCard('Critical findings', (validation.critical_findings || []).length, (validation.critical_findings || []).length ? 'danger' : 'success', 'Critical validation issues still attached to the draft.')}
      ${metricCard('Simulation failed', simulation.failed_count || 0, (simulation.failed_count || 0) ? 'danger' : 'success', 'Failure cases from the latest simulation report.')}
      ${metricCard('Reviewer history', reviewTimeline.length, reviewTimeline.length ? 'accent' : 'default', 'Review decisions recorded against this draft.')}
    </section>
  `;
}

function renderBlockerGroups(readiness) {
  const groups = readiness.blocker_groups || {};
  const advisoryGroups = readiness.advisory_groups || {};
  const categories = Object.keys(groups);
  const advisoryCategories = Object.keys(advisoryGroups);
  if (!categories.length && !advisoryCategories.length) return '<div class="trace-box"><strong>Publish blockers</strong><p class="muted">No publish blockers or structural advisories for the current revision.</p></div>';
  return `
    <div class="stack">
      ${categories.map((category) => `
        <article class="trace-box compact-trace">
          <div class="hero-heading">
            <div>
              <strong>${escapeHtml(titleCase(category))}</strong>
              <p class="muted">${escapeHtml(`${groups[category].length} blocker(s)`)} </p>
            </div>
            <div class="hero-chip-row">${groups[category].map((entry) => statusBadge(entry.severity || 'warning')).join('')}</div>
          </div>
          <p class="muted">${escapeHtml(groups[category].map((entry) => entry.message).join(' | '))}</p>
        </article>
      `).join('')}
      ${advisoryCategories.map((category) => `
        <article class="trace-box compact-trace">
          <div class="hero-heading">
            <div>
              <strong>${escapeHtml(`${titleCase(category)} advisory`)}</strong>
              <p class="muted">${escapeHtml(`${advisoryGroups[category].length} advisory note(s)`)}</p>
            </div>
            <div class="hero-chip-row">${advisoryGroups[category].map((entry) => statusBadge(entry.severity || 'warning')).join('')}</div>
          </div>
          <p class="muted">${escapeHtml(advisoryGroups[category].map((entry) => entry.message).join(' | '))}</p>
        </article>
      `).join('')}
    </div>
  `;
}

function buildStudioPtagDiagnostics(item, source) {
  const currentSource = String(source || '');
  const lines = currentSource.split(/\r?\n/);
  const openBraces = (currentSource.match(/\{/g) || []).length;
  const closeBraces = (currentSource.match(/\}/g) || []).length;
  const missingBlocks = ['role', 'authority', 'constraint', 'policy'].filter((keyword) => !new RegExp(`\\b${keyword}\\b`).test(currentSource));
  const generatedBaseline = item?.system_generated_ptag || '';
  const compare = item?.summary?.editor_compare || {};
  const warnings = [];
  if (openBraces !== closeBraces) warnings.push('Brace balance looks off.');
  if (missingBlocks.length) warnings.push(`Missing PTAG blocks: ${missingBlocks.join(', ')}.`);
  if (item?.ptag_source_mode === 'manual' && !generatedBaseline.trim()) warnings.push('Manual mode is active without a recorded generated baseline.');
  if (!lines.some((line) => line.includes('language "PTAG"'))) warnings.push('Language header is missing.');
  return {
    line_count: lines.length,
    open_braces: openBraces,
    close_braces: closeBraces,
    missing_blocks: missingBlocks,
    warnings,
    compare,
  };
}

function renderPtagDiagnostics(diagnostics) {
  return `
    <section class="diff-grid">
      <article class="trace-box compact-trace">
        <strong>Editor diagnostics</strong>
        ${keyValue([
          ['Lines', String(diagnostics.line_count || 0)],
          ['Brace balance', `${diagnostics.open_braces || 0}/${diagnostics.close_braces || 0}`],
          ['Missing blocks', diagnostics.missing_blocks?.length ? diagnostics.missing_blocks.join(', ') : 'None'],
        ])}
      </article>
      <article class="trace-box compact-trace">
        <strong>Generated vs manual</strong>
        ${keyValue([
          ['Mode', diagnostics.compare?.mode || 'generated'],
          ['Added lines', String(diagnostics.compare?.added_lines || 0)],
          ['Removed lines', String(diagnostics.compare?.removed_lines || 0)],
        ])}
      </article>
    </section>
    <div class="trace-box compact-trace">
      <strong>Validation hints</strong>
      <p class="muted">${escapeHtml(diagnostics.warnings.length ? diagnostics.warnings.join(' | ') : 'No immediate editor hints. Save PTAG Draft to run full validation and simulation again.')}</p>
    </div>
  `;
}

function renderLineNumbers(source) {
  const total = Math.max(1, String(source || '').split(/\r?\n/).length);
  return Array.from({ length: total }, (_item, index) => index + 1).join('\n');
}

function refreshStudioEditorAssist(requestId, source) {
  const item = getStudioRequestById(requestId);
  if (!item) return;
  const gutter = document.getElementById('studio-ptag-gutter');
  if (gutter) gutter.textContent = renderLineNumbers(source);
  const diagnostics = document.getElementById('studio-ptag-diagnostics');
  if (diagnostics) diagnostics.innerHTML = renderPtagDiagnostics(buildStudioPtagDiagnostics(item, source));
}

function renderWorkflowStageExplanation(stage) {
  const explanations = {
    authoring: 'Structured JD is present and the hat exists as an authored draft.',
    validation: 'PTAG syntax and semantic checks passed for the selected revision.',
    simulation: 'Scenario simulation produced a safe enough outcome to continue.',
    structural: 'PT-OSS structural intelligence decided whether this draft is blocked, guarded, or ready for publication.',
    review: 'A reviewer has either approved the current revision or returned it for changes.',
    publication: 'The role pack is either ready for a publisher, blocked, or already promoted into the registry.',
  };
  return explanations[stage.id] || 'Governed publication stage.';
}

function renderPolicies(roles) {
  if (!roles.length) return renderNoWorkState('No PTAG role packs are available yet.', { eyebrow: 'Policy library idle', title: 'No trusted hats are published in this runtime yet.', detail: 'Publish the first governed hat through Role Private Studio, then come back here to inspect trust, hierarchy, and boundaries.', primaryActionView: 'studio', primaryActionLabel: 'Open Role Private Studio', secondaryActionView: 'overview', secondaryActionLabel: 'Open Overview', pills: ['library empty', 'publish first hat'] });
  const verifiedTotal = roles.filter((role) => role.trusted_manifest_signature_status === 'verified').length;
  const validationIssueTotal = roles.reduce((sum, role) => sum + ((role.validation_issues || []).length), 0);
  const allowTotal = roles.reduce((sum, role) => sum + ((role.allow || []).length), 0);
  const denyTotal = roles.reduce((sum, role) => sum + ((role.deny || []).length), 0);
  const hierarchyReadyTotal = roles.filter((role) => role.stratum || role.reports_to || role.escalation_to).length;
  const safetyOwners = new Set(roles.map((role) => role.safety_owner).filter(Boolean)).size;
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Policy Library</div>
            <h2 class="hero-title">Trusted hats read like an enterprise operating constitution.</h2>
            <p class="hero-subtitle">Each published role pack carries authority, constraints, hierarchy, escalation posture, policies, and registry trust metadata so operators can inspect both power and provenance before activating work.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(verifiedTotal === roles.length ? 'registry verified' : 'verification watch')}
          </div>
        </div>
        <div class="hero-split">
          ${keyValue([
            ['Role packs', String(roles.length)],
            ['Verified manifests', String(verifiedTotal)],
            ['Validation issues', String(validationIssueTotal)],
            ['Hierarchy ready', String(hierarchyReadyTotal)],
            ['Safety owners', String(safetyOwners)],
          ])}
          <div class="hero-note">
            <strong>Governance posture</strong>
            <p>The policy library is more than a catalog. It is the visible contract between each AI hat, the private runtime, and the human authority that stands above it, including where each hat escalates when pressure rises.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Registry posture</div>
          <h3 class="card-title">Trust and boundaries</h3>
          <p class="card-subtitle">Inspect manifest integrity, validation posture, role hierarchy, and the balance between allowed and forbidden action surfaces.</p>
        </div>
        ${keyValue([
          ['Allowed actions', String(allowTotal)],
          ['Denied actions', String(denyTotal)],
          ['Registry coverage', `${verifiedTotal}/${roles.length} verified`],
          ['Warning posture', validationIssueTotal ? 'review advised' : 'clean view'],
          ['Role source', 'Trusted private registry'],
          ['Escalation map', hierarchyReadyTotal ? 'live in policy cards' : 'incomplete'],
        ])}
        <div class="trace-box"><strong>Library note</strong><p class="muted">Role packs shown here are the live hats the runtime can load. Review provenance, hierarchy, and escalation posture before expanding authority or publishing new hats.</p></div>
      </article>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Roles', roles.length, 'default', 'Published role hats currently available in the runtime library.')}
      ${metricCard('Verified', verifiedTotal, 'success', 'Role packs with verified trusted-manifest signatures.')}
      ${metricCard('Validation issues', validationIssueTotal, 'warning', 'Non-fatal findings still visible across the current role library.')}
      ${metricCard('Hierarchy ready', hierarchyReadyTotal, 'accent', 'Roles that expose stratum, reporting line, or escalation data to the runtime.')}
      ${metricCard('Safety owners', safetyOwners, 'warning', 'Distinct escalation owners visible across the current live hat library.')}
    </section>
    <section class="card-grid">${roles.map((role) => `
      <article class="card stack">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">${escapeHtml(role.role_id)}</div>
            <h3 class="card-title">${escapeHtml(role.title || role.role_id)}</h3>
            <p class="card-subtitle">${escapeHtml(role.purpose || 'No purpose provided.')}</p>
          </div>
          <div class="hero-chip-row">${statusBadge(role.trusted_manifest_signature_status || 'unknown')}</div>
        </div>
        ${renderRoleHierarchyLane(role)}
        ${keyValue([
          ['Policies', String(role.policies.length)],
          ['Constraints', String(role.constraints.length)],
          ['Stratum', role.stratum || '-'],
          ['Reports to', role.reports_to || '-'],
          ['Escalates to', role.escalation_to || '-'],
          ['Safety owner', role.safety_owner || '-'],
          ['Business domain', role.business_domain || '-'],
          ['Source', role.trusted_source_origin || 'unknown'],
          ['Manifest', role.trusted_manifest_signature_status || 'unknown'],
          ['Registry key', role.trusted_manifest_key_id || '-'],
          ['Allow', role.allow.join(', ') || '-'],
          ['Deny', role.deny.join(', ') || '-'],
          ['Handled resources', Array.isArray(role.handled_resources) && role.handled_resources.length ? role.handled_resources.join(', ') : '-'],
        ])}
        <div class="trace-box"><strong>Validation issues</strong><p class="muted">${role.validation_issues.length ? escapeHtml(role.validation_issues.map((issue) => issue.code).join(', ')) : 'No validation warnings.'}</p></div>
      </article>`).join('')}</section>
  `;
}

function renderHealth(runtimeHealth, availableProfiles, retentionReport, operations, integrations, operatorNotificationCenter, operatorNotificationDeliveryReadiness) {
  const goLive = runtimeHealth.go_live_readiness || null;
  const backupSummary = operations?.summary || runtimeHealth.runtime_backups || {};
  const integrationSummary = integrations?.summary || runtimeHealth.integration_deliveries || {};
  const trustedRegistry = runtimeHealth.trusted_registry || {};
  const accessControl = runtimeHealth.access_control || {};
  const sessionStore = runtimeHealth.session_store || {};
  const requestConsistency = runtimeHealth.request_consistency || {};
  const privilegedOperations = runtimeHealth.privileged_operations || goLive?.privileged_operations || {};
  const studioStructural = runtimeHealth.studio_structural || goLive?.studio_structural || {};
  const ownerRegistration = runtimeHealth.owner_registration || currentOwnerRegistration();
  const cards = Object.entries(runtimeHealth)
    .filter(([key]) => !['go_live_readiness', 'runtime_backups', 'privileged_operations', 'studio_structural', 'owner_registration'].includes(key))
    .map(([key, value]) => typeof value === 'object' && value !== null
        ? `<article class="card stack runtime-domain-card"><div><div class="eyebrow muted">Runtime domain</div><h3 class="card-title">${titleCase(key)}</h3><p class="card-subtitle">Current posture for ${escapeHtml(titleCase(key).toLowerCase())}.</p></div>${keyValue(Object.entries(value).map(([entryKey, entryValue]) => [titleCase(entryKey), typeof entryValue === 'object' && entryValue !== null ? JSON.stringify(entryValue) : String(entryValue)]))}</article>`
        : metricCard(titleCase(key), String(value), 'default', 'Scalar runtime posture signal.'))
    .join('');
  const profileRows = availableProfiles.map((profile) => [profile.display_name, `${profile.role_name} | ${profile.permissions.length} permissions`]);
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Runtime Health</div>
            <h2 class="hero-title">Enterprise readiness is visible as an operating posture, not a hidden checklist.</h2>
            <p class="hero-subtitle">Health brings go-live, trust, storage, and recovery signals into one operator view.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(goLive?.status || 'blocked')}
          </div>
        </div>
        <div class="hero-split">
            ${keyValue([
              ['Go-live status', goLive?.status || 'blocked'],
              ['Trusted registry', trustedRegistry.signature_status || '-'],
              ['Active profiles', String(availableProfiles.length)],
              ['Backups total', String(backupSummary.backups_total || 0)],
              ['Privileged ops', privilegedOperations.delegated ? 'delegated' : (privilegedOperations.status || '-')],
              ['Integration targets', String(integrations?.summary?.targets_total || runtimeHealth.integration_registry?.targets_total || 0)],
              ['Hidden empty stores', String(hiddenRuntimeDomainTotal)],
            ])}
          <div class="hero-note">
            <strong>Executive reading</strong>
            <p>This view should answer one question quickly: can the private server be trusted to operate, recover, and explain itself right now. Every other card exists to support that answer.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Operational posture</div>
          <h3 class="card-title">Readiness indicators</h3>
          <p class="card-subtitle">A concise signal across access control, session discipline, consistency handling, and recovery continuity.</p>
        </div>
          ${keyValue([
            ['Access posture', accessControl.plain_file_tokens_zero ? 'hardened' : 'review required'],
            ['Session status', sessionStore.status || '-'],
            ['Consistency store', requestConsistency.status || '-'],
            ['Studio structural', studioStructural.status || 'clear'],
            ['Latest backup', backupSummary.latest_backup?.backup_id || '-'],
            ['Delivery log', integrationSummary.status || '-'],
          ])}
          <div class="trace-box"><strong>Retention note</strong><p class="muted">${escapeHtml(retentionReport?.next_expiry_at ? `Next scheduled expiry at ${retentionReport.next_expiry_at}.` : 'No retention expiry is currently queued in the visible report.')}</p></div>
        </article>
    </section>
      <section class="metrics-grid metrics-grid-luxury">
        ${metricCard('Go-live', goLive?.status || 'blocked', goLive?.status === 'ready' ? 'success' : goLive?.status === 'guarded' ? 'warning' : 'danger', 'Combined deployment gate across trust, smoke, delegated privilege coverage, and operational evidence.')}
        ${metricCard('Deployment mode', ownerRegistration.deployment_mode || 'private', ownerRegistration.deployment_mode === 'multi' ? 'accent' : 'success', 'Identity posture of this runtime: single-organization private or multi-org governance surface.')}
        ${metricCard('Profiles', availableProfiles.length, 'default', 'Configured private-server access profiles visible to the operator surface.')}
        ${metricCard('Privileged ops', privilegedOperations.delegated ? 'delegated' : (privilegedOperations.status || 'unknown'), privilegedOperations.delegated ? 'success' : privilegedOperations.status === 'warning' ? 'warning' : 'danger', 'Whether privileged runtime surfaces can be operated beyond the owner token.')}
        ${metricCard('Studio structural', studioStructural.status || 'clear', studioStructural.status === 'clear' ? 'success' : studioStructural.status === 'guarded' ? 'warning' : 'danger', 'Current PT-OSS publication posture across Studio drafts.')}
        ${metricCard('Backups', backupSummary.backups_total || 0, 'success', 'Operational recovery bundles currently retained in the runtime backup store.')}
        ${metricCard('Retention datasets', retentionReport?.datasets?.length || 0, 'warning', 'Datasets currently tracked by the retention and legal-hold engine.')}
        ${metricCard('Outbound deliveries', integrationSummary.deliveries_total || 0, integrationSummary.failed_total ? 'warning' : 'success', 'Integration dispatch records across the current runtime window.')}
      </section>
    ${renderHealthNotificationPostureCard(operatorNotificationCenter, integrations, operatorNotificationDeliveryReadiness)}
    ${renderOwnerRegistrationPanel(ownerRegistration)}
    <section class="health-grid">${goLive ? renderGoLiveReadinessCard(goLive) : ''}${cards}</section>
    ${renderOperationsSection(operations || { summary: runtimeHealth.runtime_backups || {}, backups: [] })}
    ${renderIntegrationSection(integrations || { summary: runtimeHealth.integration_deliveries || {}, targets: [], deliveries: [] })}
    ${renderRetentionSection(retentionReport)}
    <article class="card stack"><div><div class="eyebrow muted">Access Profiles</div><h3 class="card-title">Configured private-server profiles</h3><p class="card-subtitle">Profiles available to enter the governed private runtime surface.</p></div>${keyValue(profileRows.length ? profileRows : [['Profiles', 'No access profiles available.']])}</article>
  `;
}

function renderRuntimeDomainSurface(key, value) {
  if (typeof value === 'object' && value !== null) {
    return `<article class="card stack runtime-domain-card"><div><div class="eyebrow muted">Runtime domain</div><h3 class="card-title">${titleCase(key)}</h3><p class="card-subtitle">Current posture for ${escapeHtml(titleCase(key).toLowerCase())}.</p></div>${keyValue(Object.entries(value).map(([entryKey, entryValue]) => [titleCase(entryKey), typeof entryValue === 'object' && entryValue !== null ? JSON.stringify(entryValue) : String(entryValue)]))}</article>`;
  }
  return metricCard(titleCase(key), String(value), 'default', 'Scalar runtime posture signal.');
}

function shouldHideRuntimeDomain(key, value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const status = String(value.status || '').toLowerCase();
  const path = String(value.path || '');
  const bytes = Number(value.bytes || 0);
  const likelyFeatureStore = key.endsWith('_store') || /_store\.json$/i.test(path);
  if (!likelyFeatureStore) return false;
  if (!['missing', 'uninitialized', 'not_initialized'].includes(status)) return false;
  if (bytes !== 0) return false;
  const meaningfulKeys = Object.entries(value)
    .filter(([entryKey]) => !['status', 'path', 'bytes', 'available', 'initialized'].includes(entryKey))
    .filter(([_entryKey, entryValue]) => {
      if (entryValue === null || entryValue === undefined) return false;
      if (Array.isArray(entryValue)) return entryValue.length > 0;
      if (typeof entryValue === 'object') return Object.keys(entryValue).length > 0;
      const text = String(entryValue).trim().toLowerCase();
      return text !== '' && text !== '0' && text !== 'false' && text !== 'missing';
    });
  return meaningfulKeys.length === 0;
}
function renderHealthNotificationPostureCard(center, integrations, deliveryReadiness = null) {
  const policy = center?.policy || {};
  const notification = policy.notification || {};
  if (!notification || !Object.keys(notification).length) return '';
  const summary = integrations?.summary || {};
  const severityChannels = notification.severity_channels || {};
  const hasExternal = Boolean((deliveryReadiness?.external_routing_ready ?? (Boolean(summary.http_enabled) && Number(summary.active_targets || 0) > 0)));
  const failedTotal = Number((deliveryReadiness?.failed_total ?? summary.failed_total) || 0);
  const outboxTotal = Number((deliveryReadiness?.outbox_total ?? summary.outbox_total) || 0);
  const dispatchCandidates = Number((deliveryReadiness?.dispatch_candidates_total ?? center?.dispatch_candidates_total) || 0);
  const highestSeverity = deliveryReadiness?.highest_severity || center?.highest_severity || 'ready';
  const posture = deliveryReadiness?.posture || (!center?.enabled
    ? 'disabled'
    : failedTotal > 0
      ? 'degraded'
      : outboxTotal > 0
        ? 'pressured'
        : hasExternal || dispatchCandidates <= 0
          ? 'ready'
          : 'dashboard only');
  const nextActions = Array.isArray(deliveryReadiness?.next_actions) && deliveryReadiness.next_actions.length
    ? deliveryReadiness.next_actions.map((item) => [item.label || 'Action', item.detail || '-'])
    : [];
  if (!center?.enabled) nextActions.push(['Immediate action', 'Re-enable operator notifications or keep a strict dashboard-review routine until routing is restored.']);
  if (!summary.http_enabled) nextActions.push(['Routing setup', 'Enable outbound HTTP integrations before expecting external email or webhook-style routing.']);
  if (summary.http_enabled && Number(summary.active_targets || 0) <= 0) nextActions.push(['Target setup', 'Add at least one active integration target so external routing can leave the dashboard.']);
  if (failedTotal > 0) nextActions.push(['Failure review', 'Inspect failed deliveries and dead letters to restore trusted operator notification routing.']);
  if (outboxTotal > 0) nextActions.push(['Queue pressure', 'Review queued outbox jobs and coordination state before alert latency grows.']);
  if (!nextActions.length) nextActions.push(['Current posture', 'Notification routing is aligned with the current runtime and does not need immediate operator repair.']);
  return `
    <article class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Operator Notification Posture</div>
          <h3 class="card-title">Runtime readiness for governed alert routing</h3>
          <p class="card-subtitle">Health translates the notification policy into an operational answer: are operator alerts confined to the dashboard, externally routable, or currently degraded by delivery pressure?</p>
        </div>
        <div class="hero-chip-row">${statusBadge(posture)}</div>
      </div>
      ${keyValue([
        ['Notifications enabled', String(Boolean(center?.enabled))],
        ['Highest queue severity', String(highestSeverity)],
        ['Dispatch candidates', String(dispatchCandidates)],
        ['External routing ready', String(hasExternal)],
        ['Failed deliveries', String(failedTotal)],
        ['Outbox pressure', String(outboxTotal)],
      ])}
      <div class="trace-box compact-trace">
        <strong>Severity routing</strong>
        <p class="muted">${escapeHtml(['warning', 'critical', 'stale'].map((level) => `${level}: ${((severityChannels[level] || []).join(', ') || 'dashboard')}`).join(' | '))}</p>
      </div>
      <div class="trace-box compact-trace">
        <strong>Operator reading</strong>
        <p class="muted">${escapeHtml(!center?.enabled
          ? 'The queue policy is still evaluating risk, but notifications are globally disabled so only manual dashboard review is available.'
          : failedTotal > 0
            ? 'Alert routing exists, but recent integration failures mean operators should treat external delivery as degraded until Health and Integrations are reviewed.'
            : outboxTotal > 0
              ? 'Routing is configured, but queued jobs show pressure in the delivery path. Watch for delayed alerts.'
              : hasExternal
                ? 'The runtime has an external delivery path for governed alerts in addition to the dashboard.'
                : 'The unified policy is active, but current routing is effectively dashboard-only until an external target is enabled.')}</p>
      </div>
      <div class="trace-box compact-trace">
        <strong>Recommended next actions</strong>
        ${keyValue(nextActions)}
      </div>
      <div class="inline-actions">
        <button class="action-button action-button-muted" data-view-jump="health">Open Health</button>
        <button class="action-button action-button-muted" data-view-jump="overview">Back to Overview</button>
      </div>
    </article>
  `;
}

function renderOwnerRegistrationPanel(ownerRegistration, options = {}) {
  const compact = Boolean(options.compact);
  const registration = ownerRegistration || {};
  const registered = Boolean(registration.registered);
  const editable = isOwnerSession();
  const registrationCode = registration.registration_code || '';
  const deploymentMode = registration.deployment_mode || 'private';
  const ownerName = registration.owner_name || '';
  const ownerDisplayName = registration.owner_display_name || ownerName;
  const organizationName = registration.organization_name || '';
  const organizationId = registration.organization_id || '';
  const executiveOwnerId = registration.executive_owner_id || studioExecutiveOwnerId();
  const trustedRegistrySignedBy = registration.trusted_registry_signed_by || ownerName || '';
  const summaryRows = [
    ['Registered', registered ? 'yes' : 'no'],
    ['Registration code', registrationCode || '-'],
    ['Deployment mode', deploymentMode],
    ['Organization', organizationName || '-'],
    ['Organization id', organizationId || '-'],
    ['Owner', ownerDisplayName || '-'],
    ['Executive owner id', executiveOwnerId || '-'],
    ['Registry signer', trustedRegistrySignedBy || '-'],
  ];
  const intro = compact
    ? 'One code anchors the runtime before delegated profiles enter.'
    : 'Register once with a simple code. The suite derives organization and executive-owner identity automatically so onboarding stays lightweight.';
  const form = editable ? `
      <form id="owner-registration-form" class="composer-grid owner-registration-form">
        <div>
          <label class="permission-note" for="owner-registration-registration-code">Registration code</label>
          <input id="owner-registration-registration-code" value="${escapeHtml(registrationCode)}" placeholder="TWN-HQ-001" />
        </div>
        <div>
          <label class="permission-note" for="owner-registration-deployment-mode">Deployment mode</label>
          <select id="owner-registration-deployment-mode">
            <option value="private"${deploymentMode === 'private' ? ' selected' : ''}>private</option>
            <option value="multi"${deploymentMode === 'multi' ? ' selected' : ''}>multi</option>
          </select>
        </div>
        <div class="span-2 inline-actions">
          <button class="action-button" type="submit">${registered ? 'Update Registration Code' : 'Register Runtime Code'}</button>
        </div>
      </form>
      <div class="trace-box compact-trace">
        <strong>Derived automatically</strong>
        <p class="muted">Organization id, executive owner id, display name, and trusted-registry signer are derived from the registration code unless you later change them through governed internal tooling.</p>
      </div>
    ` : `
      <div class="trace-box compact-trace">
        <strong>Owner-only change surface</strong>
        <p class="muted">Only the owner session may update runtime registration. Delegated profiles can inspect the registration posture but cannot change it.</p>
      </div>
    `;
  return `
    <section class="card stack owner-registration-panel${compact ? ' owner-registration-panel-compact' : ''}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${compact ? 'Deployment identity' : 'Registration Code'}</div>
          <h3 class="card-title">${registered ? 'Runtime registration is active' : 'Runtime registration still needs attention'}</h3>
          <p class="card-subtitle">${escapeHtml(intro)}</p>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(registered ? 'registered' : 'missing')}
          ${statusBadge(deploymentMode)}
        </div>
      </div>
      ${keyValue(summaryRows)}
      ${registration.path ? `<div class="trace-box compact-trace"><strong>Registration file</strong>${keyValue([['Path', registration.path]])}</div>` : ''}
      ${form}
    </section>
  `;
}

function renderGoLiveReadinessCard(item) {
  const blockers = Array.isArray(item.blockers) && item.blockers.length ? item.blockers.join(' | ') : 'No blockers.';
  const advisories = Array.isArray(item.advisories) && item.advisories.length ? item.advisories.join(' | ') : 'No advisories.';
  const gates = item.gates || {};
  const smoke = item.smoke_report || {};
  const reviewPack = item.review_pack || {};
  const privilegedOperations = item.privileged_operations || {};
  const studioStructural = item.studio_structural || {};
  return `<article class="card stack"><div><div class="eyebrow muted">Go-Live Gate</div><h3 class="card-title">${escapeHtml(item.status || 'blocked')}</h3><p class="card-subtitle">Combined enterprise deployment posture.</p></div>${keyValue([['Ready', String(Boolean(item.ready))], ['Deployment', String(Boolean(gates.deployment_ready))], ['Trusted registry', String(Boolean(gates.trusted_registry_verified))], ['Audit integrity', String(Boolean(gates.audit_integrity_verified))], ['Plain tokens zero', String(Boolean(gates.plain_file_tokens_zero))], ['Privileged ops delegated', String(Boolean(gates.delegated_privileged_operations))], ['Studio structural clear', String(Boolean(gates.studio_structural_clear))], ['Startup smoke', String(Boolean(gates.startup_smoke_passed))], ['Review pack', String(Boolean(gates.review_pack_present))], ['Smoke report', smoke.status || '-'], ['Review pack generated', reviewPack.generated_at || '-']])}<section class="governance-mini-grid"><article class="trace-box compact-trace"><strong>Privileged runtime operations</strong>${keyValue([['Status', privilegedOperations.status || 'unknown'], ['Delegated', privilegedOperations.delegated ? 'yes' : 'no']])}<p class="muted">${escapeHtml(privilegedOperations.message || 'Delegated privileged-operation coverage is unavailable.')}</p></article><article class="trace-box compact-trace"><strong>Studio structural posture</strong>${keyValue([['Status', studioStructural.status || 'clear'], ['Guarded drafts', String(studioStructural.guarded_total || 0)], ['Blocked drafts', String(studioStructural.blocked_total || 0)], ['Ready drafts', String(studioStructural.ready_total || 0)]])}<p class="muted">PT-OSS structural pressure from Role Private Studio is surfaced here so go-live never hides publication fragility.</p></article></section><div class="trace-box"><strong>Blockers</strong><p class="muted">${escapeHtml(blockers)}</p></div><div class="trace-box"><strong>Advisories</strong><p class="muted">${escapeHtml(advisories)}</p></div></article>`;
}

function renderRetentionSection(retentionReport) {
  if (!retentionReport || !Array.isArray(retentionReport.datasets) || !retentionReport.datasets.length) return '';
  return `<article class="table-card"><h3 class="table-title">Retention & Legal Hold</h3><div class="trace-box"><strong>Summary</strong><p class="muted">Expired candidates: ${escapeHtml(String(retentionReport.expired_candidate_total || 0))}, Hold-blocked: ${escapeHtml(String(retentionReport.hold_blocked_total || 0))}, Next expiry: ${escapeHtml(retentionReport.next_expiry_at || '-')}</p></div><div class="table-wrapper">${retentionTable(retentionReport.datasets)}</div></article>`;
}

function renderOperationsSection(operations) {
  if (!operations) return '';
  const summary = operations.summary || {};
  const backups = Array.isArray(operations.backups) ? operations.backups : [];
  const usabilityProof = operations.usability_proof || {};
  const quickStartDoctor = operations.quick_start_doctor || {};
  const firstRunActionCenter = operations.first_run_action_center || {};
  const criteria = Array.isArray(usabilityProof.pass_criteria) ? usabilityProof.pass_criteria : [];
  const criteriaRows = criteria.length
    ? criteria.map((row) => `${statusBadge(row.passed ? 'passed' : 'failed')} ${escapeHtml(row.criterion || 'criterion')}`).join('<br>')
    : 'No criteria loaded yet.';
  const failedCriteria = Array.isArray(usabilityProof.failed_criteria) ? usabilityProof.failed_criteria : [];
  const failedHint = failedCriteria.length
    ? `Failing criteria: ${escapeHtml(failedCriteria.join(', '))}`
    : 'All loaded criteria are currently passing.';
  const firstRunRows = Array.isArray(firstRunActionCenter.items) && firstRunActionCenter.items.length
    ? firstRunActionCenter.items.slice(0, 4).map((item) => `${statusBadge(item.severity === 'required' ? 'blocked' : 'monitoring')} ${escapeHtml(item.title || item.action_id || 'action')} ${item.ops_action ? `-> ${escapeHtml(item.ops_action)}` : ''}`).join('<br>')
    : 'No first-run actions are currently queued.';
  const action = can('ops.manage')
    ? `<div class="inline-actions"><button class="action-button" data-ops-action="backup">Create Runtime Backup</button><button class="action-button" data-ops-action="usability-proof">Generate Usability Proof</button><button class="action-button action-button-muted" data-ops-action="usability-proof-refresh">Refresh Latest Proof</button><button class="action-button" data-ops-action="quick-start-doctor">Run Quick-Start Doctor</button><button class="action-button action-button-muted" data-ops-action="quick-start-doctor-refresh">Refresh Doctor Status</button><button class="action-button" data-ops-action="first-run-action-center-sync">Run First-Run Sync</button><button class="action-button action-button-muted" data-ops-action="first-run-action-center-refresh">Refresh First-Run Actions</button></div>`
    : '';
  return `<article class="table-card"><h3 class="table-title">Operations Backup</h3>${action}<div class="trace-box"><strong>Summary</strong><p class="muted">Backups total: ${escapeHtml(String(summary.backups_total || 0))}, Latest backup: ${escapeHtml(summary.latest_backup?.backup_id || '-')}, Latest time: ${escapeHtml(summary.latest_backup?.created_at || '-')}</p></div><div class="trace-box"><strong>First-run action center</strong><p class="muted">Status: ${escapeHtml(String(firstRunActionCenter.status || 'blocked'))}, Ready: ${escapeHtml(String(Boolean(firstRunActionCenter.ready)))}, Required actions: ${escapeHtml(String(firstRunActionCenter.required_total || 0))}, Total actions: ${escapeHtml(String(firstRunActionCenter.items_total || 0))}, Recommended action: ${escapeHtml(String(firstRunActionCenter.recommended_action || 'none'))}</p><p class="muted">${firstRunRows}</p></div><div class="trace-box"><strong>Usability proof</strong><p class="muted">Status: ${escapeHtml(String(usabilityProof.status || 'missing'))}, Available: ${escapeHtml(String(Boolean(usabilityProof.available)))}, Generated: ${escapeHtml(String(usabilityProof.generated_at || '-'))}, Path: ${escapeHtml(String(usabilityProof.path || '-'))}, Criteria: ${escapeHtml(String(usabilityProof.criteria_passed_total || 0))}/${escapeHtml(String(usabilityProof.criteria_total || 0))}, Failed: ${escapeHtml(String(usabilityProof.criteria_failed_total || 0))}</p><p class="muted">${failedHint}</p><p class="muted">${criteriaRows}</p></div><div class="trace-box"><strong>Quick-start doctor</strong><p class="muted">Status: ${escapeHtml(String(quickStartDoctor.status || 'missing'))}, Available: ${escapeHtml(String(Boolean(quickStartDoctor.available)))}, Generated: ${escapeHtml(String(quickStartDoctor.generated_at || '-'))}, Required failed: ${escapeHtml(String(quickStartDoctor.required_failed_total || 0))}, Advisory failed: ${escapeHtml(String(quickStartDoctor.advisory_failed_total || 0))}, Checks: ${escapeHtml(String(quickStartDoctor.checks_total || 0))}</p><p class="muted">${escapeHtml(Array.isArray(quickStartDoctor.next_actions) && quickStartDoctor.next_actions.length ? quickStartDoctor.next_actions.slice(0, 2).join(' | ') : 'No recommended next actions.')}</p></div><div class="table-wrapper">${backupTable(backups)}</div></article>`;
}

function renderIntegrationSection(integrations) {
  if (!integrations) return '';
  const summary = integrations.summary || {};
  const targets = Array.isArray(integrations.targets) ? integrations.targets : [];
  const outbox = Array.isArray(integrations.outbox) ? integrations.outbox : [];
  const deliveries = Array.isArray(integrations.deliveries) ? integrations.deliveries : [];
  const deadLetters = Array.isArray(integrations.dead_letters) ? integrations.dead_letters : [];
  const hasExternal = Boolean(summary.http_enabled) && Number(summary.active_targets || 0) > 0;
  const routingPosture = !summary.http_enabled
    ? 'dashboard only'
    : Number(summary.failed_total || 0) > 0
      ? 'degraded'
      : Number(summary.outbox_total || 0) > 0
        ? 'pressured'
        : hasExternal
          ? 'ready'
          : 'setup needed';
  const routingActions = [];
  if (!summary.http_enabled) routingActions.push(['Enable HTTP', 'Turn on outbound HTTP integrations before expecting email or webhook-style alert delivery.']);
  if (summary.http_enabled && Number(summary.active_targets || 0) <= 0) routingActions.push(['Add active target', 'Create at least one active target so alert routing can leave the dashboard.']);
  if (Number(summary.failed_total || 0) > 0) routingActions.push(['Review failed deliveries', 'Inspect delivery failures and dead letters before trusting external alert routing.']);
  if (Number(summary.outbox_total || 0) > 0) routingActions.push(['Reduce queue pressure', 'Work through outbox backlog and coordination pressure to avoid delayed notifications.']);
  if (!routingActions.length) routingActions.push(['Current posture', 'Integration routing is aligned with the current operator notification plan.']);
  const testAction = can('integration.manage')
    ? `<div class="inline-actions"><button class="action-button" data-integration-action="test-event">Send Test Event</button></div>`
    : '';
  return `<article class="table-card"><h3 class="table-title">Integration Foundation</h3>${testAction}<div class="trace-box"><strong>Summary</strong><p class="muted">Targets: ${escapeHtml(String(summary.targets_total || 0))}, Active: ${escapeHtml(String(summary.active_targets || 0))}, Deliveries: ${escapeHtml(String(summary.deliveries_total || 0))}, Retries: ${escapeHtml(String(summary.retry_records_total || 0))}, Dead letters: ${escapeHtml(String(summary.dead_letters_total || 0))}, Outbox jobs: ${escapeHtml(String(summary.outbox_total || 0))}, Coordination: ${escapeHtml(String(summary.coordination_backend || '-'))} (${escapeHtml(String(summary.coordination_mode || '-'))}), Signed targets: ${escapeHtml(String(summary.signed_targets || 0))}, HTTP enabled: ${escapeHtml(String(Boolean(summary.http_enabled)))}</p></div><div class="trace-box compact-trace"><strong>Alert-routing fit</strong><p class="muted">${escapeHtml(`Posture: ${routingPosture} | External routing ready: ${String(hasExternal)} | Failed deliveries: ${String(summary.failed_total || 0)} | Outbox jobs: ${String(summary.outbox_total || 0)}`)}</p></div><div class="trace-box compact-trace"><strong>Recommended next actions</strong>${keyValue(routingActions)}</div><div class="table-wrapper">${integrationTargetTable(targets)}</div><div class="table-wrapper">${integrationOutboxTable(outbox)}</div><div class="table-wrapper">${integrationDeliveryTable(deliveries)}</div><div class="table-wrapper">${integrationDeadLetterTable(deadLetters)}</div></article>`;
}

function renderStudioRequestCard(item) {
  const validation = item.validation_report || {};
  const simulation = item.simulation_report || {};
  const summary = item.summary || {};
  const readiness = item.publish_readiness || { status: 'blocked', blockers: [], gates: {} };
  const workflow = item.publication_workflow || {};
  const ptOss = item.pt_oss_assessment || {};
  const latestDiff = summary.latest_diff || {};
  const latestChanges = summary.latest_change_summary || [];
  const revisionCompare = buildStudioRevisionCompare(item);
  const revisions = item.revisions || [];
  const canReview = can('studio.review');
  const canPublish = can('studio.publish');
  const canEdit = can('studio.create') && item.status !== 'published';
  const structuralTone = studioReadinessTone(readiness);
  const structuralNote = readiness.status === 'guarded'
    ? (readiness.structural_gate_reason || 'PT-OSS is holding this hat in structural review before publication.')
    : readiness.status === 'ready'
      ? 'Structural posture is clear enough for trusted publication.'
      : (readiness.blockers?.[0] || 'This draft still needs validation, simulation, or review movement before publication.');
  const caseReference = renderCaseReferenceButton(item.case_id, item.case_status, {
    sourceView: 'studio',
    referenceId: item.request_id,
    contextLabel: 'studio draft',
    label: item.case_id,
  });
  return `
    <article class="card stack${isFocusedEntity('studio_request', item.request_id) ? ' focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey('studio_request', item.request_id))}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(summary.role_id || item.request_id)}</div>
          <h3 class="card-title">${escapeHtml(item.structured_jd.role_name || item.request_id)}</h3>
          <p class="card-subtitle">${escapeHtml(item.structured_jd.purpose || 'No purpose provided.')}</p>
          ${caseReference ? `<div class="table-case-reference">${caseReference}</div>` : ''}
        </div>
        <div class="hero-chip-row">
          ${statusBadge(item.status)}
          ${statusBadge(readiness.status || 'blocked')}
        </div>
      </div>
      <section class="governance-mini-grid">
        ${metricCard('Structural gate', readiness.structural_state || 'blocked', structuralTone, 'PT-OSS publication posture for the active revision.')}
        ${metricCard('Workflow', workflow.status || 'blocked', workflow.status === 'published' ? 'success' : workflow.status === 'publisher_ready' ? 'accent' : workflow.status === 'structural_review' ? 'warning' : 'default', 'Current publication workflow stage for this hat.')}
        ${metricCard('PT-OSS score', ptOss.readiness_score || 0, (ptOss.readiness_score || 0) >= 80 ? 'success' : (ptOss.readiness_score || 0) >= 68 ? 'warning' : 'danger', 'Structural readiness score carried by the active draft.')}
      </section>
      ${keyValue([
          ['Status', item.status],
          ['Requested by', item.requested_by],
          ['Revision', String(summary.current_revision || 0)],
          ['Publish readiness', readiness.status || 'blocked'],
        ['Blockers', String((readiness.blockers || []).length)],
        ['Validation blocked', String(validation.blocked_publish ?? true)],
        ['Simulation status', simulation.status || 'not_run'],
          ['Reviews', String(summary.review_count || 0)],
          ['PTAG mode', summary.ptag_source_mode || 'generated'],
      ])}
      <div class="trace-box studio-signal-strip">
        <strong>Structural reading</strong>
        <p class="muted">${escapeHtml(structuralNote)}</p>
      </div>
      <div class="inline-actions">
        ${can('human_ask.create') ? `<button class="action-button action-button-muted" data-human-ask-action="studio-record" data-request-id="${escapeHtml(item.request_id)}" data-entry-label="${escapeHtml(item.structured_jd?.role_name || item.request_id)}">Start Report</button>` : ''}
        ${canEdit ? `<button class="action-button action-button-muted" data-studio-action="load" data-request-id="${escapeHtml(item.request_id)}">Load into Editor</button>` : ''}
        ${canEdit ? `<button class="action-button action-button-muted" data-studio-action="refresh" data-request-id="${escapeHtml(item.request_id)}">Refresh</button>` : ''}
        ${canReview && item.status !== 'published' ? `<button class="action-button" data-studio-action="approve" data-request-id="${escapeHtml(item.request_id)}">Approve</button>` : ''}
        ${canReview && item.status !== 'published' ? `<button class="action-button action-button-muted" data-studio-action="request_changes" data-request-id="${escapeHtml(item.request_id)}">Request Changes</button>` : ''}
        ${canPublish && item.status === 'approved' ? `<button class="action-button" data-studio-action="publish" data-request-id="${escapeHtml(item.request_id)}">Publish</button>` : ''}
      </div>
      <section class="diff-grid">
        <article class="trace-box stack compact-trace">
          <strong>Latest change summary</strong>
          <p class="muted">${latestChanges.length ? escapeHtml(latestChanges.join(' | ')) : 'No change summary yet.'}</p>
        </article>
        <article class="trace-box stack compact-trace">
          <strong>Diff overview</strong>
          <p class="muted">${escapeHtml(renderLatestDiff(latestDiff))}</p>
          ${renderDiffFactList(latestDiff)}
        </article>
      </section>
      <section class="publish-gate-grid">
        <article class="trace-box stack compact-trace">
          <strong>Publish decision</strong>
          <p class="muted">${escapeHtml(renderPublishDecisionSummary(item, readiness, validation, simulation))}</p>
          ${renderGateSummary(readiness.gates || {})}
        </article>
        <article class="trace-box stack compact-trace">
          <strong>Validation and simulation</strong>
          <p class="muted">${validation.findings?.length ? escapeHtml(validation.findings.map((finding) => `${finding.severity}:${finding.code}`).join(', ')) : 'No validation findings.'}</p>
          <p class="muted">${escapeHtml(`Scenarios: ${simulation.scenario_count || 0}, Passed: ${simulation.passed_count || 0}, Failed: ${simulation.failed_count || 0}`)}</p>
        </article>
      </section>
      ${renderPublicationWorkflow(workflow)}
      ${renderStudioRevisionCompare(revisionCompare)}
      <div class="trace-box"><strong>Publish blockers</strong><p class="muted">${readiness.blockers?.length ? escapeHtml(readiness.blockers.join(' | ')) : 'No publish blockers for the current revision.'}</p></div>
      ${item.publish_artifact ? `<div class="trace-box"><strong>Published</strong><p class="muted">${escapeHtml(`${item.publish_artifact.role_path} | ${item.publish_artifact.trusted_sha256}`)}</p></div>` : ''}
      <details class="trace-box"><summary><strong>Revision history</strong></summary>${renderStudioRevisionHistory(revisions)}</details>
      <details class="trace-box"><summary><strong>PTAG preview</strong></summary><pre>${escapeHtml(item.generated_ptag || 'No PTAG draft generated yet.')}</pre></details>
    </article>
  `;
}

function renderStudioRevisionHistory(revisions) {
  if (!revisions.length) return '<p class="muted">No revisions recorded yet.</p>';
  const items = [...revisions].reverse().map((revision) => {
    const changes = (revision.change_summary || []).join(' | ');
    return `<div class="trace-box"><strong>Revision ${escapeHtml(String(revision.revision_number || 0))}</strong><p class="muted">${escapeHtml(`${revision.trigger || 'refresh'} | ${shortTime(revision.generated_at)}`)}</p><p class="muted">${escapeHtml(changes || 'No change summary recorded.')}</p></div>`;
  }).join('');
  return items;
}

function renderLatestDiff(diff) {
  const ptag = diff.ptag || {};
  const structured = diff.structured_jd || {};
  const changedFields = Array.isArray(structured.changed_fields) && structured.changed_fields.length ? structured.changed_fields.join(', ') : 'none';
  return `Fields: ${changedFields}; PTAG +${ptag.added_lines || 0} / -${ptag.removed_lines || 0}`;
}
function renderDiffFactList(diff) {
  const ptag = diff.ptag || {};
  const structured = diff.structured_jd || {};
  const changedFields = Array.isArray(structured.changed_fields) && structured.changed_fields.length
    ? structured.changed_fields.join(', ')
    : 'none';
  return keyValue([
    ['Changed fields', changedFields],
    ['PTAG added', String(ptag.added_lines || 0)],
    ['PTAG removed', String(ptag.removed_lines || 0)],
  ]);
}

function renderGateSummary(gates) {
  const entries = Object.entries(gates || {});
  if (!entries.length) return '<p class="muted">No publish gates reported.</p>';
  return `<div class="key-value">${entries.map(([key, value]) => `<div class="key-value-row"><span class="muted">${escapeHtml(titleCase(key))}</span>${statusBadge(value ? 'ready' : 'blocked')}</div>`).join('')}</div>`;
}

function renderPublishDecisionSummary(item, readiness, validation, simulation) {
  if (item.status === 'published') return 'This hat has already been promoted into the trusted registry.';
  if (readiness.status === 'guarded') return readiness.structural_gate_reason || 'PT-OSS is keeping this draft in guarded structural review before publication.';
  if (readiness.status === 'ready' || item.status === 'approved') return 'This draft has enough evidence to move through publication once the publisher confirms the promotion.';
  if (validation.blocked_publish) return 'Validation is still blocking publication and the draft should not advance yet.';
  if ((simulation.failed_count || 0) > 0) return 'Simulation still shows failure cases that should be resolved before promotion.';
  if ((readiness.pt_oss_summary?.blocking_issue_count || 0) > 0) return 'PT-OSS structural blockers are still preventing trusted publication.';
  if ((readiness.blockers || []).length) return 'There are active publish blockers that still need reviewer attention.';
  return 'This draft is still moving through the governed review path.';
}

function renderStudioRevisionCompare(compare, options = {}) {
  if (!compare || !compare.current_revision_number) return '';
  const currentLabel = options.currentLabel || 'Current revision';
  const previousLabel = options.previousLabel || 'Previous revision';
  const hasPrevious = Boolean(compare.previous_revision_number);
  const selector = options.selectable
    ? renderStudioRevisionSelector(options.requestId || '', compare.available_revisions || [], compare.current_revision_number, compare.previous_revision_number)
    : '';
  return `
    <section class="revision-compare-shell stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Revision compare</div>
          <h3 class="card-title">Side-by-side revision reading</h3>
          <p class="card-subtitle">Compare the latest governed revision against the previous one before sending the hat forward.</p>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(`r${compare.current_revision_number}`)}
          ${hasPrevious ? statusBadge(`vs r${compare.previous_revision_number}`) : statusBadge('first revision')}
        </div>
      </div>
      ${selector}
      ${hasPrevious
        ? `<section class="revision-compare-grid">${renderStudioRevisionPanel(currentLabel, compare.current_revision_number, compare.current_generated_at, compare.current_trigger, compare.current_structured_jd, compare.current_generated_ptag, compare.current_change_summary || [])}${renderStudioRevisionPanel(previousLabel, compare.previous_revision_number, compare.previous_generated_at, compare.previous_trigger, compare.previous_structured_jd, compare.previous_generated_ptag, compare.previous_change_summary || [])}</section>`
        : `<div class="trace-box"><strong>First revision</strong><p class="muted">There is no earlier revision to compare yet. Once the draft is regenerated, this section will show a full side-by-side comparison.</p></div>`}
    </section>
  `;
}

function renderStudioRevisionSelector(requestId, availableRevisions, currentRevisionNumber, previousRevisionNumber) {
  if (!availableRevisions.length) return '';
  const buildOptions = (selectedRevisionNumber) => availableRevisions.map((revision) => {
    const revisionNumber = revision.revision_number || 0;
    const label = `Revision ${revisionNumber} ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¾ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â· ${revision.trigger || 'refresh'} ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¾ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â· ${shortTime(revision.generated_at)}`;
    const selected = revisionNumber === selectedRevisionNumber ? ' selected' : '';
    return `<option value="${escapeHtml(String(revisionNumber))}"${selected}>${escapeHtml(label)}</option>`;
  }).join('');
  return `
    <section class="revision-selector-grid">
      <article class="trace-box compact-trace stack revision-selector-card">
        <strong>Review revision</strong>
        <p class="muted">The revision you are evaluating right now.</p>
        <select data-studio-compare-select="true" data-request-id="${escapeHtml(requestId)}" data-compare-side="current">${buildOptions(currentRevisionNumber)}</select>
      </article>
      <article class="trace-box compact-trace stack revision-selector-card">
        <strong>Compare against</strong>
        <p class="muted">The revision that gives the clearest baseline for change.</p>
        <select data-studio-compare-select="true" data-request-id="${escapeHtml(requestId)}" data-compare-side="previous">${buildOptions(previousRevisionNumber)}</select>
      </article>
    </section>
    <div class="trace-box compact-trace revision-selector-note">
      <strong>Revision discipline</strong>
      <p class="muted">Choose any two governed revisions to inspect how the hat changed before you approve, request changes, or publish it.</p>
    </div>
  `;
}

function renderStudioRevisionPanel(label, revisionNumber, generatedAt, trigger, structuredJd, generatedPtag, changeSummary) {
  return `
    <article class="trace-box stack compare-panel">
      <div class="hero-heading">
        <div>
          <strong>${escapeHtml(label)}</strong>
          <p class="muted">${escapeHtml(`Revision ${revisionNumber || 0} | ${trigger || 'refresh'}`)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(generatedAt ? shortTime(generatedAt) : 'pending')}</div>
      </div>
      ${renderStructuredJDSummary(structuredJd)}
      <div class="trace-box compact-trace">
        <strong>Change summary</strong>
        <p class="muted">${changeSummary.length ? escapeHtml(changeSummary.join(' | ')) : 'No change summary recorded for this revision.'}</p>
      </div>
      <div class="trace-box compact-trace">
        <strong>PTAG preview</strong>
        <pre class="code-preview">${escapeHtml(renderPtagPreview(generatedPtag))}</pre>
      </div>
    </article>
  `;
}

function ensureStudioRevisionSelection(item) {
  const revisions = Array.isArray(item?.revisions) ? item.revisions : [];
  const ordered = revisions
    .map((revision) => Number.parseInt(revision.revision_number, 10) || 0)
    .filter(Boolean)
    .sort((left, right) => left - right);
  const latest = ordered[ordered.length - 1] || 0;
  const previous = ordered.length > 1 ? ordered[ordered.length - 2] : latest;
  const existing = state.studioRevisionSelections[item.request_id] || {};
  const selection = {
    current_revision_number: ordered.includes(existing.current_revision_number) ? existing.current_revision_number : latest,
    previous_revision_number: ordered.includes(existing.previous_revision_number) ? existing.previous_revision_number : previous,
  };
  normalizeStudioRevisionSelection(item, selection);
  state.studioRevisionSelections[item.request_id] = selection;
  return selection;
}

function normalizeStudioRevisionSelection(item, selection, changedSide = '') {
  const revisions = Array.isArray(item?.revisions) ? item.revisions : [];
  const ordered = revisions
    .map((revision) => Number.parseInt(revision.revision_number, 10) || 0)
    .filter(Boolean)
    .sort((left, right) => left - right);
  if (!ordered.length) {
    selection.current_revision_number = 0;
    selection.previous_revision_number = 0;
    return selection;
  }
  if (!ordered.includes(selection.current_revision_number)) selection.current_revision_number = ordered[ordered.length - 1];
  if (!ordered.includes(selection.previous_revision_number)) selection.previous_revision_number = ordered.length > 1 ? ordered[ordered.length - 2] : selection.current_revision_number;
  if (ordered.length > 1 && selection.current_revision_number === selection.previous_revision_number) {
    if (changedSide === 'current') {
      selection.previous_revision_number = ordered.slice().reverse().find((revisionNumber) => revisionNumber !== selection.current_revision_number) || ordered[0];
    } else {
      selection.current_revision_number = ordered.slice().reverse().find((revisionNumber) => revisionNumber !== selection.previous_revision_number) || ordered[ordered.length - 1];
    }
  }
  return selection;
}

function buildStudioRevisionCompare(item, selectable = false) {
  if (!item) return null;
  const revisions = Array.isArray(item.revisions) ? item.revisions : [];
  if (!revisions.length) return item.summary?.revision_compare || null;
  const selection = selectable ? ensureStudioRevisionSelection(item) : null;
  const currentRevisionNumber = selection?.current_revision_number || revisions[revisions.length - 1]?.revision_number || 0;
  const previousRevisionNumber = selection?.previous_revision_number
    || (revisions.length > 1 ? revisions[revisions.length - 2]?.revision_number || 0 : 0);
  const currentRevision = findStudioRevision(revisions, currentRevisionNumber) || revisions[revisions.length - 1];
  const previousRevision = findStudioRevision(revisions, previousRevisionNumber);
  return {
    current_revision_number: currentRevision?.revision_number || 0,
    previous_revision_number: previousRevision?.revision_number || 0,
    current_trigger: currentRevision?.trigger || null,
    previous_trigger: previousRevision?.trigger || null,
    current_generated_at: currentRevision?.generated_at || null,
    previous_generated_at: previousRevision?.generated_at || null,
    current_structured_jd: currentRevision?.structured_jd_snapshot || null,
    previous_structured_jd: previousRevision?.structured_jd_snapshot || null,
    current_generated_ptag: currentRevision?.generated_ptag || '',
    previous_generated_ptag: previousRevision?.generated_ptag || '',
    current_change_summary: currentRevision?.change_summary || [],
    previous_change_summary: previousRevision?.change_summary || [],
    available_revisions: [...revisions]
      .sort((left, right) => (right.revision_number || 0) - (left.revision_number || 0))
      .map((revision) => ({
        revision_number: revision.revision_number || 0,
        generated_at: revision.generated_at || null,
        trigger: revision.trigger || 'refresh',
      })),
  };
}

function findStudioRevision(revisions, revisionNumber) {
  return revisions.find((revision) => Number.parseInt(revision.revision_number, 10) === Number.parseInt(revisionNumber, 10)) || null;
}

function renderStructuredJDSummary(jd) {
  if (!jd) return '<p class="muted">No structured job definition snapshot.</p>';
  return keyValue([
    ['Role name', jd.role_name || '-'],
    ['Reporting line', jd.reporting_line || '-'],
    ['Business domain', jd.business_domain || '-'],
    ['Operating mode', jd.operating_mode || 'direct'],
    ['Assigned user', jd.assigned_user_id || '-'],
    ['Executive owner', jd.executive_owner_id || studioExecutiveOwnerId()],
    ['Seat id', jd.seat_id || '-'],
    ['Allowed actions', Array.isArray(jd.allowed_actions) && jd.allowed_actions.length ? jd.allowed_actions.join(', ') : '-'],
    ['Forbidden actions', Array.isArray(jd.forbidden_actions) && jd.forbidden_actions.length ? jd.forbidden_actions.join(', ') : '-'],
    ['Wait-human', Array.isArray(jd.wait_human_actions) && jd.wait_human_actions.length ? jd.wait_human_actions.join(', ') : '-'],
    ['Handled resources', Array.isArray(jd.handled_resources) && jd.handled_resources.length ? jd.handled_resources.join(', ') : '-'],
  ]);
}

function renderPtagPreview(source, maxLines = 18) {
  if (!source) return 'No PTAG source available.';
  const lines = String(source).split(/\r?\n/);
  const preview = lines.slice(0, maxLines).join('\n');
  return lines.length > maxLines ? `${preview}\n...` : preview;
}

function requestTable(rows) {
  if (!rows.length) return emptyState('No request records available.');
  return `<table class="data-table"><thead><tr><th>Time</th><th>Request</th><th>Role Flow</th><th>Action</th><th>Outcome</th><th>Resource</th><th>Consistency</th><th>Activation & Escalation</th><th>Basis</th></tr></thead><tbody>${rows.map((row) => {
    const focused = isFocusedEntity('request', row.request_id) || isFocusedEntity('override', row.request_id);
    const caseReference = renderCaseReferenceButton(row.case_id, row.case_status, {
      sourceView: 'requests',
      referenceId: row.request_id,
      contextLabel: 'request',
      label: row.case_id,
    });
    return `<tr class="${focused ? 'focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey('request', row.request_id))}" data-focus-alt-key="${escapeHtml(buildFocusKey('override', row.request_id))}"><td>${escapeHtml(shortTime(row.timestamp))}</td><td><strong>${escapeHtml(row.request_id)}</strong>${caseReference ? `<div class="table-case-reference">${caseReference}</div>` : ''}<div class="muted">${escapeHtml(row.requester)}</div></td><td>${renderRoleFlowCell(row)}</td><td><strong>${escapeHtml(row.action)}</strong><div class="muted">${escapeHtml(row.requested_role || row.active_role || '-')}</div></td><td>${statusBadge(row.outcome)}</td><td><strong>${escapeHtml(row.resource || '-')}</strong><div class="muted">${escapeHtml(row.resource_id || row.business_domain || '-')}</div></td><td><div>${escapeHtml(row.idempotency_status || 'none')}</div><div class="muted">${escapeHtml(row.ordering_status || 'none')}</div></td><td>${renderActivationCell(row)}</td><td><div>${escapeHtml(row.policy_basis || '-')}</div><div class="muted">${escapeHtml(row.switch_reason || row.reason || '-')}</div></td></tr>`;
  }).join('')}</tbody></table>`;
}

function overrideTable(rows) {
  if (!rows.length) return emptyState('No overrides available.');
  return `<table class="data-table"><thead><tr><th>Override</th><th>Role</th><th>Action</th><th>Status</th><th>Required by</th><th>Requester</th><th>Execution</th><th>Review</th></tr></thead><tbody>${rows.map((row) => {
    const focused = isFocusedEntity('override', row.request_id) || isFocusedEntity('request', row.request_id);
    const caseReference = renderCaseReferenceButton(row.case_id, row.case_status, {
      sourceView: 'overrides',
      referenceId: row.request_id,
      contextLabel: 'override packet',
      label: row.case_id,
    });
    return `<tr class="${focused ? 'focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey('override', row.request_id))}" data-focus-alt-key="${escapeHtml(buildFocusKey('request', row.request_id))}"><td><strong>${escapeHtml(row.request_id)}</strong>${caseReference ? `<div class="table-case-reference">${caseReference}</div>` : ''}<div class="muted">${escapeHtml(shortTime(row.created_at))}</div></td><td>${escapeHtml(row.active_role)}</td><td>${escapeHtml(row.action)}</td><td>${statusBadge(row.status)}</td><td>${escapeHtml(row.required_by)}</td><td>${escapeHtml(row.requester)}</td><td>${escapeHtml(row.execution_outcome || '-')}</td><td>${row.status === 'pending' && can('override.review') ? `<div class="inline-actions"><button class="action-button" data-override-action="approve" data-request-id="${escapeHtml(row.request_id)}">Approve</button><button class="action-button action-button-muted" data-override-action="veto" data-request-id="${escapeHtml(row.request_id)}">Veto</button></div>` : '<span class="muted">Read only</span>'}</td></tr>`;
  }).join('')}</tbody></table>`;
}

function lockTable(rows) {
  if (!rows.length) return emptyState('No active locks.');
  return `<table class="data-table"><thead><tr><th>Resource</th><th>Request owner</th><th>Role</th><th>Action</th><th>Status</th><th>Updated</th></tr></thead><tbody>${rows.map((row) => `<tr><td><strong>${escapeHtml(row.resource_key)}</strong></td><td>${escapeHtml(row.owner_request_id)}</td><td>${escapeHtml(row.active_role)}</td><td>${escapeHtml(row.action)}</td><td>${statusBadge(row.status)}</td><td>${escapeHtml(shortTime(row.updated_at))}</td></tr>`).join('')}</tbody></table>`;
}

function sessionTable(rows) {
  if (!rows.length) return emptyState('No session records available.');
  return `<table class="data-table"><thead><tr><th>Session</th><th>Profile</th><th>Role</th><th>Status</th><th>Auth</th><th>Last Seen</th><th>Expiry</th><th>Control</th></tr></thead><tbody>${rows.map((row) => `<tr><td><strong>${escapeHtml(row.session_id)}</strong></td><td>${escapeHtml(row.display_name)}<div class="muted">${escapeHtml(row.profile_id)}</div></td><td>${escapeHtml(row.role_name)}</td><td>${statusBadge(row.status)}</td><td>${escapeHtml(row.auth_method || '-')}</td><td>${escapeHtml(shortTime(row.last_seen_at))}</td><td>${escapeHtml(shortTime(row.expires_at))}</td><td>${row.status === 'active' && can('session.manage') ? `<button class="action-button action-button-muted" data-session-revoke="true" data-session-id="${escapeHtml(row.session_id)}">Revoke</button>` : '<span class="muted">Read only</span>'}</td></tr>`).join('')}</tbody></table>`;
}

function auditTable(rows) {
  if (!rows.length) return emptyState('No audit events available.');
  return `<table class="data-table"><thead><tr><th>Time</th><th>Event</th><th>Role Flow</th><th>Outcome</th><th>Activation & Escalation</th><th>Reason</th></tr></thead><tbody>${rows.map((row) => {
    const requestId = row.request_id || row.metadata?.request_id || row.metadata?.context?.request_id || row.metadata?.context?.metadata?.origin_request_id || '';
    const focused = isFocusedEntity('request', requestId) || isFocusedEntity('override', requestId);
    const caseReference = renderCaseReferenceButton(row.case_id, row.case_status, {
      sourceView: 'audit',
      referenceId: requestId || row.action || '',
      contextLabel: 'audit event',
      label: row.case_id,
    });
    return `<tr class="${focused ? 'focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey('request', requestId))}" data-focus-alt-key="${escapeHtml(buildFocusKey('override', requestId))}"><td>${escapeHtml(shortTime(row.timestamp))}</td><td><strong>${escapeHtml(titleCase(row.action || '-'))}</strong>${caseReference ? `<div class="table-case-reference">${caseReference}</div>` : ''}<div class="muted">${escapeHtml(requestId || '-')}</div></td><td>${renderRoleFlowCell(row)}</td><td>${statusBadge(row.outcome)}</td><td>${renderActivationCell(row)}</td><td><div>${escapeHtml(row.reason || '-')}</div><div class="muted">${escapeHtml(row.requester || row.metadata?.requester || '-')}</div></td></tr>`;
  }).join('')}</tbody></table>`;
}

function retentionTable(rows) {
  if (!rows.length) return emptyState('No retention datasets available.');
  return `<table class="data-table"><thead><tr><th>Dataset</th><th>Records</th><th>Retention</th><th>Expired</th><th>Legal hold</th><th>Next expiry</th></tr></thead><tbody>${rows.map((row) => `<tr><td><strong>${escapeHtml(row.dataset)}</strong><div class="muted">${escapeHtml(row.file_path || '-')}</div></td><td>${escapeHtml(String(row.records))}</td><td>${escapeHtml(String(row.retention_days))} days</td><td>${escapeHtml(String(row.expired_candidates))}</td><td>${row.legal_hold_active ? statusBadge('active') : statusBadge('clear')}</td><td>${escapeHtml(row.next_expiry_at || '-')}</td></tr>`).join('')}</tbody></table>`;
}

function backupTable(rows) {
  if (!rows.length) return emptyState('No runtime backups created yet.');
  return `<table class="data-table"><thead><tr><th>Backup</th><th>Created</th><th>Requested by</th><th>Files</th><th>Bytes</th><th>Path</th></tr></thead><tbody>${rows.map((row) => `<tr><td><strong>${escapeHtml(row.backup_id)}</strong></td><td>${escapeHtml(shortTime(row.created_at))}</td><td>${escapeHtml(row.requested_by || '-')}</td><td>${escapeHtml(`${row.files_present || 0}/${row.files_total || 0}`)}</td><td>${escapeHtml(String(row.bytes_total || 0))}</td><td class="muted">${escapeHtml(row.backup_path || '-')}</td></tr>`).join('')}</tbody></table>`;
}

function integrationTargetTable(rows) {
  if (!rows.length) return emptyState('No integration targets configured.');
  return `<table class="data-table"><thead><tr><th>Target</th><th>Category</th><th>Status</th><th>Mode</th><th>Retry</th><th>Signing</th><th>Subscriptions</th><th>Destination</th></tr></thead><tbody>${rows.map((row) => `<tr><td><strong>${escapeHtml(row.name || row.target_id)}</strong><div class="muted">${escapeHtml(row.target_id || '-')}</div></td><td>${escapeHtml(row.category || '-')}</td><td>${statusBadge(row.status || 'unknown')}</td><td>${escapeHtml(row.delivery_mode || '-')}</td><td><strong>${escapeHtml(String(row.max_attempts || 1))}</strong><div class="muted">${escapeHtml(String(row.retry_backoff_ms || 0))} ms</div></td><td>${escapeHtml(row.signing_policy || 'none')}</td><td>${escapeHtml(Array.isArray(row.subscribed_events) && row.subscribed_events.length ? row.subscribed_events.join(', ') : '-')}</td><td class="muted">${escapeHtml(row.endpoint_url || '-')}</td></tr>`).join('')}</tbody></table>`;
}

function integrationDeliveryTable(rows) {
  if (!rows.length) return emptyState('No integration deliveries recorded yet.');
  return `<table class="data-table"><thead><tr><th>Event</th><th>Target</th><th>Status</th><th>Attempt</th><th>Signing</th><th>Attempted</th><th>Reason</th></tr></thead><tbody>${rows.map((row) => `<tr><td><strong>${escapeHtml(row.event_type || '-')}</strong><div class="muted">${escapeHtml(row.event_id || '-')}</div></td><td>${escapeHtml(row.target_name || row.target_id || '-')}</td><td>${statusBadge(row.status || 'unknown')}</td><td><strong>${escapeHtml(String(row.attempt_number || 1))}</strong><div class="muted">of ${escapeHtml(String(row.max_attempts || 1))}</div></td><td>${escapeHtml(row.signing_policy || 'none')}</td><td>${escapeHtml(shortTime(row.attempted_at))}</td><td class="muted">${escapeHtml(row.reason || '-')}</td></tr>`).join('')}</tbody></table>`;
}

function integrationOutboxTable(rows) {
  if (!rows.length) return emptyState('No integration outbox jobs recorded yet.');
  return `<table class="data-table"><thead><tr><th>Job</th><th>Channel</th><th>Status</th><th>Attempts</th><th>Updated</th><th>Worker</th><th>Error</th></tr></thead><tbody>${rows.map((row) => `<tr><td><strong>${escapeHtml(row.job_id || '-')}</strong><div class="muted">${escapeHtml(row.payload?.event_type || '-')}</div></td><td>${escapeHtml(row.channel || '-')}</td><td>${statusBadge(row.status || 'unknown')}</td><td>${escapeHtml(String(row.attempts || 0))}</td><td>${escapeHtml(shortTime(row.updated_at || row.created_at))}</td><td>${escapeHtml(row.worker_id || '-')}</td><td class="muted">${escapeHtml(row.last_error || '-')}</td></tr>`).join('')}</tbody></table>`;
}

function integrationDeadLetterTable(rows) {
  if (!rows.length) return emptyState('No integration dead letters recorded.');
  return `<table class="data-table"><thead><tr><th>Event</th><th>Target</th><th>Final Status</th><th>Attempts</th><th>Signing</th><th>Dead-lettered</th><th>Reason</th></tr></thead><tbody>${rows.map((row) => `<tr><td><strong>${escapeHtml(row.event_type || '-')}</strong><div class="muted">${escapeHtml(row.event_id || '-')}</div></td><td>${escapeHtml(row.target_name || row.target_id || '-')}</td><td>${statusBadge(row.final_status || 'failed')}</td><td><strong>${escapeHtml(String(row.attempts_used || 1))}</strong><div class="muted">of ${escapeHtml(String(row.max_attempts || 1))}</div></td><td>${escapeHtml(row.signing_policy || 'none')}</td><td>${escapeHtml(shortTime(row.dead_lettered_at))}</td><td class="muted">${escapeHtml(row.reason || '-')}</td></tr>`).join('')}</tbody></table>`;
}

function buildTableEmptyGuidance(title) {
  const guidance = {
    'Recent Requests': {
      title: 'No governed requests are visible yet.',
      detail: 'Start with Runtime Intake when the next governed task is ready, then come back here to follow its lane.',
      primaryActionView: 'requests',
      primaryActionLabel: 'Open Requests',
      secondaryActionView: 'studio',
      secondaryActionLabel: 'Open Studio',
      pills: ['intake first', 'live queue'],
    },
    'Runtime Requests': {
      title: 'The runtime request ledger is empty.',
      detail: 'Submit work from this lane to start governed execution, then follow the same request here after routing and policy checks.',
      primaryActionView: 'requests',
      primaryActionLabel: 'Stay in Requests',
      secondaryActionView: 'overview',
      secondaryActionLabel: 'Open Overview',
      pills: ['submit work', 'follow queue'],
    },
    'Human Override Queue': {
      title: 'No human approvals are waiting right now.',
      detail: 'This is healthy when automation stayed in bounds. If you expected a pause, inspect Runtime Requests first.',
      primaryActionView: 'requests',
      primaryActionLabel: 'Open Requests',
      secondaryActionView: 'audit',
      secondaryActionLabel: 'Open Audit',
      pills: ['human boundary clear', 'automation running'],
    },
    'Overrides': {
      title: 'No override packets are visible in this lane.',
      detail: 'When the Director crosses a human boundary, the approval packet will appear here with the next decision owner attached.',
      primaryActionView: 'requests',
      primaryActionLabel: 'Open Requests',
      secondaryActionView: 'overview',
      secondaryActionLabel: 'Open Overview',
      pills: ['queue stable', 'no pending review'],
    },
    'Active Locks': {
      title: 'No protected resources are locked right now.',
      detail: 'The runtime is currently contention-free. If work still appears blocked, inspect the conflicted request lane next.',
      primaryActionView: 'conflicts',
      primaryActionLabel: 'Open Conflicts',
      secondaryActionView: 'requests',
      secondaryActionLabel: 'Open Requests',
      pills: ['contention clear', 'safe to proceed'],
    },
    'Conflicted Requests': {
      title: 'No conflicted requests are waiting for release.',
      detail: 'No requests are currently being held by resource or ordering pressure in this runtime window.',
      primaryActionView: 'requests',
      primaryActionLabel: 'Open Requests',
      secondaryActionView: 'overview',
      secondaryActionLabel: 'Open Overview',
      pills: ['no blocked work', 'queue flowing'],
    },
    'Audit Trail': {
      title: 'No audit events are visible yet.',
      detail: 'Once the Director starts processing governed work, the evidence ledger will begin filling with requests, decisions, and maintenance events.',
      primaryActionView: 'requests',
      primaryActionLabel: 'Open Requests',
      secondaryActionView: 'health',
      secondaryActionLabel: 'Open Runtime Health',
      pills: ['evidence starts with work', 'chain ready'],
    },
    'Sessions': {
      title: 'No runtime sessions are visible in this snapshot.',
      detail: 'When profiles log in, their session posture, expiry, and revocation controls will appear here.',
      primaryActionView: 'health',
      primaryActionLabel: 'Open Runtime Health',
      secondaryActionView: 'overview',
      secondaryActionLabel: 'Open Overview',
      pills: ['access idle', 'session lane clear'],
    },
    'Integration Deliveries': {
      title: 'No outbound deliveries have been recorded yet.',
      detail: 'Targets may still be configured. Send a test event or let governed work emit the first delivery through the runtime.',
      primaryActionView: 'health',
      primaryActionLabel: 'Open Runtime Health',
      secondaryActionView: 'overview',
      secondaryActionLabel: 'Open Overview',
      pills: ['routing idle', 'targets may still be ready'],
    },
    'Integration Outbox': {
      title: 'No integration jobs are queued right now.',
      detail: 'The outbox is clear. Jobs will appear here when governed events are buffered for outbound delivery.',
      primaryActionView: 'health',
      primaryActionLabel: 'Open Runtime Health',
      secondaryActionView: 'overview',
      secondaryActionLabel: 'Open Overview',
      pills: ['queue clear', 'delivery idle'],
    },
    'Integration Dead Letters': {
      title: 'No dead letters are waiting for recovery.',
      detail: 'Outbound delivery is not currently leaving failed events behind in the dead-letter lane.',
      primaryActionView: 'health',
      primaryActionLabel: 'Open Runtime Health',
      secondaryActionView: 'overview',
      secondaryActionLabel: 'Open Overview',
      pills: ['recovery clear', 'delivery clean'],
    },
    'Retention Datasets': {
      title: 'No retention datasets are visible yet.',
      detail: 'Retention posture becomes meaningful once governed documents, audit data, or workflow artifacts are being preserved.',
      primaryActionView: 'health',
      primaryActionLabel: 'Open Runtime Health',
      secondaryActionView: 'audit',
      secondaryActionLabel: 'Open Audit',
      pills: ['retention not seeded', 'archive idle'],
    },
    'Runtime Backups': {
      title: 'No runtime backups have been created yet.',
      detail: 'Generate the first recovery bundle from Runtime Health so restore posture is visible before production pressure arrives.',
      primaryActionView: 'health',
      primaryActionLabel: 'Open Runtime Health',
      secondaryActionView: 'overview',
      secondaryActionLabel: 'Open Overview',
      pills: ['recovery not seeded', 'backup lane empty'],
    },
  };
  return guidance[title] || null;
}

function renderNoWorkState(message, options = {}) {
  const pills = Array.isArray(options.pills) ? options.pills.filter(Boolean) : [];
  return `
    <section class="empty-state-shell" data-empty-state="true">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(options.eyebrow || 'No governed work in this lane')}</div>
          <strong>${escapeHtml(options.title || 'Nothing needs action here right now.')}</strong>
          <p class="muted">${escapeHtml(options.detail || message || 'This lane will populate as the Director begins processing real work.')}</p>
        </div>
        ${pills.length ? `<div class="hero-chip-row">${pills.map((pill) => `<span class="pill">${escapeHtml(pill)}</span>`).join('')}</div>` : ''}
      </div>
      ${message ? `<p class="muted">${escapeHtml(message)}</p>` : ''}
      ${(options.primaryActionView || options.secondaryActionView) ? `
        <div class="inline-actions">
          ${options.primaryActionView ? `<button class="action-button" type="button" data-view-jump="${escapeHtml(options.primaryActionView)}">${escapeHtml(options.primaryActionLabel || 'Open view')}</button>` : ''}
          ${options.secondaryActionView ? `<button class="action-button action-button-muted" type="button" data-view-jump="${escapeHtml(options.secondaryActionView)}">${escapeHtml(options.secondaryActionLabel || 'Open next view')}</button>` : ''}
        </div>
      ` : ''}
    </section>
  `;
}

function wrapTableCard(title, tableHtml, subtitle = '') {
  const isEmpty = String(tableHtml || '').includes('data-empty-state="true"');
  const guidance = isEmpty ? buildTableEmptyGuidance(title) : null;
  const tableBody = isEmpty && guidance
    ? renderNoWorkState(tableHtml.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim(), { eyebrow: 'Work lane status', ...guidance })
    : tableHtml;
  return `<article class="table-card${isEmpty ? ' table-card-empty' : ''}"><div class="table-card-head"><div><div class="eyebrow muted">Runtime Table</div><h3 class="table-title">${escapeHtml(title)}</h3>${subtitle ? `<p class="card-subtitle">${escapeHtml(subtitle)}</p>` : ''}</div></div><div class="table-wrapper${isEmpty ? ' table-wrapper-empty' : ''}">${tableBody}</div></article>`;
}

function looksLikePathValue(key, value) {
  const normalizedKey = String(key || '').toLowerCase();
  const text = String(value || '').trim();
  if (!text || text === '-') return false;
  if (normalizedKey.includes('path') || normalizedKey.includes('file') || normalizedKey.includes('directory') || normalizedKey.includes('manifest') || normalizedKey.includes('archive') || normalizedKey.includes('store')) {
    return true;
  }
  if (/^[a-z]:\\/i.test(text) || text.startsWith('\\')) return true;
  if (/^https?:\/\//i.test(text)) return text.length > 52;
  if (text.includes('/') || text.includes('\\')) {
    return /(_runtime|resources|docs|examples|\.jsonl?$|\.md$|\.ptn$|\.log$|\.zip$|\.ya?ml$|\.txt$|\.csv$)/i.test(text);
  }
  return false;
}

function looksLikeLocalFilePath(value) {
  const text = String(value || '').trim();
  return /^[a-z]:\\/i.test(text) || text.startsWith('\\');
}

function compactPathForDisplay(value) {
  const text = String(value || '');
  if (text.length <= 56) return text;
  if (/^https?:\/\//i.test(text)) {
    try {
      const url = new URL(text);
      const tail = url.pathname.length > 26 ? `...${url.pathname.slice(-26)}` : (url.pathname || '/');
      return `${url.origin}${tail}`;
    } catch (error) {
      // Ignore malformed URLs and fall through to generic compaction.
    }
  }
  const separator = text.includes('\\') ? '\\' : '/';
  const parts = text.split(/[\\/]+/).filter(Boolean);
  if (parts.length >= 2) return `...${separator}${parts.slice(-2).join(separator)}`;
  return `${text.slice(0, 22)}...${text.slice(-18)}`;
}

function renderPathActionButtons(rawValue, pathLike) {
  const text = String(rawValue || '').trim();
  if (!pathLike || !text || text === '-') return '';
  const localPath = looksLikeLocalFilePath(text);
  const copyLabel = localPath ? 'Copy path' : 'Copy value';
  const actions = [
    `<button class="action-button action-button-muted key-value-action" type="button" data-path-action="copy" data-path-value="${escapeHtml(text)}">${copyLabel}</button>`,
  ];
  if (localPath) {
    actions.push(`<button class="action-button action-button-muted key-value-action" type="button" data-path-action="open-folder" data-path-value="${escapeHtml(text)}">Open folder</button>`);
  }
  return `<span class="key-value-path-actions">${actions.join('')}</span>`;
}

function renderKeyValueValue(key, value) {
  const rawValue = String(value ?? '-');
  const pathLike = looksLikePathValue(key, rawValue);
  const displayValue = pathLike ? compactPathForDisplay(rawValue) : rawValue;
  const titleAttr = rawValue && displayValue !== rawValue ? ` title="${escapeHtml(rawValue)}"` : '';
  const classes = ['key-value-value'];
  if (pathLike) classes.push('key-value-path');
  const valueLabel = `<span class="${classes.join(' ')}"${titleAttr}>${escapeHtml(displayValue)}</span>`;
  const actions = renderPathActionButtons(rawValue, pathLike);
  if (!actions) return valueLabel;
  return `<span class="key-value-value-shell">${valueLabel}${actions}</span>`;
}

function keyValue(rows) {
  return `<div class="key-value">${rows.map(([key, value]) => `<div class="key-value-row"><span class="muted">${escapeHtml(key)}</span>${renderKeyValueValue(key, value)}</div>`).join('')}</div>`;
}

function metricCard(label, value, tone = 'default', caption = '') {
  const normalizedValue = formatMetricValue(value);
  const normalizedLabel = String(label || '');
  const normalizedCaption = String(caption || '');
  const cardClasses = [
    'card',
    'metric-card',
    `metric-card-${escapeHtml(String(tone))}`,
  ];
  const valueLength = normalizedValue.length;
  const captionLength = normalizedCaption.length;
  const labelLength = normalizedLabel.length;
  const isStatusLike = /^[A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*$/.test(normalizedValue) && valueLength <= 22;
  if (valueLength <= 2 && captionLength <= 72) cardClasses.push('metric-card-compact');
  if (valueLength >= 14 || captionLength >= 96 || labelLength >= 20) cardClasses.push('metric-card-wide');
  if (valueLength >= 22 || captionLength >= 140) cardClasses.push('metric-card-feature');
  if (isStatusLike) cardClasses.push('metric-card-status');
  return `<article class="${cardClasses.join(' ')}"><span class="metric-label">${escapeHtml(normalizedLabel)}</span><span class="metric-value">${escapeHtml(normalizedValue)}</span>${normalizedCaption ? `<span class="metric-caption">${escapeHtml(normalizedCaption)}</span>` : ''}</article>`;
}

function emptyState(message) {
  return `<div class="empty-state" data-empty-state="true">${escapeHtml(message)}</div>`;
}

function statusBadge(value) {
  const raw = String(value);
  const css = `status-badge status-${raw.replace(/[^a-z0-9_]+/gi, '_').toLowerCase()}`;
  return `<span class="${css}">${escapeHtml(formatStatusLabel(raw))}</span>`;
}

function formatStatusLabel(value) {
  const raw = String(value ?? '').trim();
  if (!raw) return '-';
  if (/^\d+\s+[a-z]/i.test(raw)) return raw;
  const normalized = raw.toLowerCase();
  const known = {
    ready: 'Ready',
    monitoring: 'Monitoring',
    blocked: 'Blocked',
    degraded: 'Degraded',
    disabled: 'Disabled',
    active: 'Active',
    missing: 'Missing',
    present: 'Present',
    clear: 'Clear',
    approved: 'Approved',
    vetoed: 'Vetoed',
    pending: 'Pending',
    published: 'Published',
    passed: 'Passed',
    failed: 'Failed',
    direct: 'Direct',
    partial: 'Partial',
    settled: 'Settled',
    unknown: 'Unknown',
    conflicted: 'Conflict',
    escalated: 'Escalated',
    switched: 'Switched',
    steady: 'Steady',
    autonomy_ready: 'Autonomy Ready',
    human_required: 'Human Required',
    waiting_human: 'Waiting Human Review',
    human_gated: 'Human Gated',
    attention_required: 'Attention Required',
    clearance_required: 'Clearance Required',
    guarded_follow_up: 'Guarded Follow-Up',
    notifications_disabled: 'Notifications Disabled',
    queue_stable: 'Queue Stable',
    approval_action_required: 'Approval Action Required',
  };
  if (known[normalized]) return known[normalized];
  if (/^[a-z0-9]+(?:[_-][a-z0-9]+)+$/.test(normalized)) {
    return normalized
      .replace(/[_-]+/g, ' ')
      .split(' ')
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }
  if (/^[a-z][a-z0-9\s-]*$/.test(raw)) {
    return raw
      .split(/\s+/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }
  return raw;
}

function extractRoleTransition(row) {
  const transition = row.role_transition || row.transition || row.metadata?.transition || {};
  return {
    previous_role: row.previous_role ?? transition.previous_role ?? null,
    new_role: row.new_role ?? transition.new_role ?? row.active_role ?? null,
    requested_role: row.requested_role ?? transition.requested_role ?? null,
    activation_source: row.activation_source ?? transition.activation_source ?? null,
    switch_reason: row.switch_reason ?? transition.switch_reason ?? null,
    business_domain: row.business_domain ?? transition.business_domain ?? null,
  };
}

function extractHierarchyEscalation(row) {
  const escalation = row.hierarchy_escalation || row.metadata?.hierarchy_escalation || row.role_hierarchy_escalation || {};
  return {
    escalated_to: row.escalated_to ?? escalation.escalated_to ?? null,
    rule_id: escalation.rule_id ?? null,
    reason: escalation.reason ?? null,
  };
}

function renderRoleFlowCell(row) {
  const transition = extractRoleTransition(row);
  const previousRole = transition.previous_role;
  const newRole = transition.new_role || row.active_role || '-';
  const requestedRole = transition.requested_role || row.requested_role || '-';
  const changed = previousRole && previousRole !== newRole;
  const requestChip = requestedRole && requestedRole !== '-' ? `<span class="status-chip">Requested ${escapeHtml(requestedRole)}</span>` : '';
  const flow = changed
    ? `<div class="transition-route"><span class="transition-node">${escapeHtml(previousRole)}</span><span class="transition-arrow">?</span><span class="transition-node transition-node-active">${escapeHtml(newRole)}</span></div>`
    : `<div class="transition-route"><span class="transition-node transition-node-active">${escapeHtml(newRole)}</span></div>`;
  const meta = transition.switch_reason || transition.business_domain || row.reason || '-';
  return `<div class="transition-stack">${flow}<div class="transition-chip-row">${requestChip}${changed ? statusBadge('switched') : statusBadge('steady')}</div><div class="transition-meta">${escapeHtml(meta)}</div></div>`;
}

function renderActivationCell(row) {
  const transition = extractRoleTransition(row);
  const escalation = extractHierarchyEscalation(row);
  const chips = [
    statusBadge(transition.activation_source || 'direct'),
    escalation.escalated_to ? statusBadge(`to ${escalation.escalated_to}`) : '',
  ].filter(Boolean).join('');
  const lines = [
    ['Activation', transition.activation_source || '-'],
    ['Escalated to', escalation.escalated_to || '-'],
    ['Rule', escalation.rule_id || '-'],
  ];
  const detail = transition.switch_reason || escalation.reason || row.reason || '-';
  return `<div class="transition-panel"><div class="transition-chip-row">${chips}</div>${keyValue(lines)}<div class="transition-meta">${escapeHtml(detail)}</div></div>`;
}

function renderRoleHierarchyLane(role) {
  const chips = [
    role.stratum ? statusBadge(role.stratum) : '',
    role.business_domain ? statusBadge(role.business_domain) : '',
    role.safety_owner ? statusBadge(`safety ${role.safety_owner}`) : '',
  ].filter(Boolean).join('');
  const route = role.reports_to
    ? `<div class="transition-route"><span class="transition-node">${escapeHtml(role.role_id)}</span><span class="transition-arrow">?</span><span class="transition-node">${escapeHtml(role.reports_to)}</span><span class="transition-arrow">?</span><span class="transition-node transition-node-active">${escapeHtml(role.escalation_to || role.reports_to)}</span></div>`
    : `<div class="transition-route"><span class="transition-node transition-node-active">${escapeHtml(role.role_id)}</span></div>`;
  return `<section class="transition-panel role-hierarchy-panel"><div class="transition-chip-row">${chips}</div>${route}<div class="transition-meta">Reports to ${escapeHtml(role.reports_to || '-')} | Escalates to ${escapeHtml(role.escalation_to || '-')} | Safety owner ${escapeHtml(role.safety_owner || '-')}</div></section>`;
}

function selectField(id) {
  return `<select id="${id}"><option value="low">low</option><option value="medium" selected>medium</option><option value="high">high</option><option value="critical">critical</option></select>`;
}

function currentOwnerRegistration() {
  return state.snapshot?.owner_registration || state.snapshot?.runtime_health?.owner_registration || {};
}

function isOwnerSession() {
  return state.session?.role_name === 'owner';
}

function buildOwnerRegistrationPayload(documentRef) {
  return {
    registration_code: documentRef.getElementById('owner-registration-registration-code')?.value.trim() || '',
    deployment_mode: documentRef.getElementById('owner-registration-deployment-mode')?.value.trim() || 'private',
  };
}

function studioExecutiveOwnerId() {
  return state.snapshot?.owner_registration?.executive_owner_id || state.snapshot?.runtime_health?.owner_registration?.executive_owner_id || 'EXEC_OWNER';
}

function studioPayloadFromForm() {
  return {
    role_name: valueOf('studio-role-name'),
    purpose: valueOf('studio-purpose'),
    reporting_line: valueOf('studio-reporting-line') || 'GOV',
    business_domain: valueOf('studio-business-domain'),
    operating_mode: valueOf('studio-operating-mode') || 'direct',
    assigned_user_id: valueOf('studio-assigned-user-id'),
    executive_owner_id: valueOf('studio-executive-owner-id') || studioExecutiveOwnerId(),
    seat_id: valueOf('studio-seat-id'),
    responsibilities: parseListField('studio-responsibilities'),
    allowed_actions: parseListField('studio-allowed-actions'),
    forbidden_actions: parseListField('studio-forbidden-actions'),
    wait_human_actions: parseListField('studio-wait-human-actions'),
    handled_resources: parseListField('studio-handled-resources'),
    financial_sensitivity: valueOf('studio-financial-sensitivity') || 'medium',
    legal_sensitivity: valueOf('studio-legal-sensitivity') || 'medium',
    compliance_sensitivity: valueOf('studio-compliance-sensitivity') || 'medium',
    sample_scenarios: parseListField('studio-sample-scenarios'),
    operator_notes: valueOf('studio-operator-notes'),
  };
}

function clearStudioEditor() {
  state.studioEditingRequestId = null;
  state.studioEditorDraft = null;
  fillStudioForm({
    role_name: '',
    purpose: '',
    reporting_line: 'GOV',
    business_domain: '',
    operating_mode: 'direct',
    assigned_user_id: '',
    executive_owner_id: studioExecutiveOwnerId(),
    seat_id: '',
    responsibilities: [],
    allowed_actions: [],
    forbidden_actions: [],
    wait_human_actions: [],
    handled_resources: [],
    financial_sensitivity: 'medium',
    legal_sensitivity: 'medium',
    compliance_sensitivity: 'medium',
    sample_scenarios: [],
    operator_notes: '',
  });
}

function fillStudioForm(jd) {
  setFieldValue('studio-role-name', jd.role_name || '');
  setFieldValue('studio-purpose', jd.purpose || '');
  setFieldValue('studio-reporting-line', jd.reporting_line || 'GOV');
  setFieldValue('studio-business-domain', jd.business_domain || '');
  setSelectValue('studio-operating-mode', jd.operating_mode || 'direct');
  setFieldValue('studio-assigned-user-id', jd.assigned_user_id || '');
  setFieldValue('studio-executive-owner-id', jd.executive_owner_id || studioExecutiveOwnerId());
  setFieldValue('studio-seat-id', jd.seat_id || '');
  setFieldValue('studio-responsibilities', (jd.responsibilities || []).join('\n'));
  setFieldValue('studio-allowed-actions', (jd.allowed_actions || []).join('\n'));
  setFieldValue('studio-forbidden-actions', (jd.forbidden_actions || []).join('\n'));
  setFieldValue('studio-wait-human-actions', (jd.wait_human_actions || []).join('\n'));
  setFieldValue('studio-handled-resources', (jd.handled_resources || []).join('\n'));
  setFieldValue('studio-sample-scenarios', (jd.sample_scenarios || []).join('\n'));
  setFieldValue('studio-operator-notes', jd.operator_notes || '');
  setSelectValue('studio-financial-sensitivity', jd.financial_sensitivity || 'medium');
  setSelectValue('studio-legal-sensitivity', jd.legal_sensitivity || 'medium');
  setSelectValue('studio-compliance-sensitivity', jd.compliance_sensitivity || 'medium');
}
function setFieldValue(id, value) {
  const element = document.getElementById(id);
  if (element) element.value = value;
}

function setSelectValue(id, value) {
  const element = document.getElementById(id);
  if (element) element.value = value;
}

function parseJsonField(id) {
  const raw = document.getElementById(id).value.trim();
  return raw ? JSON.parse(raw) : {};
}

function parseListField(id) {
  return document.getElementById(id).value.split(/\n|,/).map((item) => item.trim()).filter(Boolean);
}

function valueOf(id) {
  return document.getElementById(id).value.trim();
}

function can(permission) {
  return Boolean(state.session && Array.isArray(state.session.permissions) && (state.session.permissions.includes('*') || state.session.permissions.includes(permission)));
}

function shortTime(value) {
  if (!value) return '-';
  return new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

function focusStudioGovernancePanel() {
  window.requestAnimationFrame(() => {
    const anchor = document.getElementById('studio-governance-panel-anchor');
    if (anchor) anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const note = document.getElementById('studio-governance-note');
    if (note) note.focus({ preventScroll: true });
  });
}

function formatDateTime(value) {
  if (!value) return '-';
  return new Date(value).toLocaleString([], { dateStyle: 'full', timeStyle: 'medium' });
}

function titleCase(value) {
  return String(value).replace(/_/g, ' ').split(' ').filter(Boolean).map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(' ');
}

function formatMetricValue(value) {
  const text = String(value ?? '-').trim();
  if (!text) return '-';
  if (/^[a-z]+(?:[_-][a-z0-9]+)+$/.test(text)) {
    return text
      .replace(/[_-]+/g, ' ')
      .split(' ')
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }
  return text;
}

function formatHumanAskModeLabel(value) {
  const mode = String(value || 'report');
  if (mode === 'report') return 'Report';
  return titleCase(mode);
}

function escapeHtml(value) {
  return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}















