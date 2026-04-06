import { buildHumanAskPayload, buildHumanAskOutcomeMessage, handleHumanAskAction, renderHumanAsk } from './dashboard_human_ask.js?v=0.7.8-ui1';

const state = {
  view: getInitialDashboardView(),
  snapshot: null,
  session: null,
  token: window.localStorage.getItem('sanom_api_token') || '',
  sessionToken: window.localStorage.getItem('sanom_session_token') || '',
  authRequired: false,
  lastError: '',
  documentEditingId: null,
  studioEditingRequestId: null,
  studioEditorDraft: null,
  studioGovernanceRequestId: null,
  studioGovernanceNotes: {},
  studioRevisionSelections: {},
  studioPtagDrafts: {},
  studioPtagHistory: {},
  actionContext: null,
  directorySearchQuery: '',
  documentFilters: {
    query: '',
    status: '',
    documentClass: '',
    caseId: '',
    activeOnly: false,
  },
  documentSearchResult: null,
  controlRoomTool: getInitialControlRoomTool(),
  liveClock: {
    timerId: null,
    sourceIso: '',
    sourceMs: 0,
    clientStartedMs: 0,
  },
  lastRenderedView: '',
  laneTransition: null,
};

const LANE_TRANSITION_WINDOW_MS = 2200;

const root = document.getElementById('dashboard-root');
const navList = document.getElementById('nav-list');
const viewTitle = document.getElementById('view-title');
const viewDescription = document.getElementById('view-description');
const topbarActionStrip = document.getElementById('topbar-action-strip');
const environmentLabel = document.getElementById('environment-label');
const organizationSelector = document.getElementById('organization-selector');
const askAiButton = document.getElementById('ask-ai-button');
const governanceLauncher = document.getElementById('governance-launcher');
const governanceSheet = document.getElementById('governance-sheet');
const governanceSheetClose = document.getElementById('governance-sheet-close');
const governanceSheetSearch = document.getElementById('governance-sheet-search');
const governanceSheetSearchCount = document.getElementById('governance-sheet-search-count');
const governanceSheetEmpty = document.getElementById('governance-sheet-empty');
const governanceModePriority = document.getElementById('governance-mode-priority');
const governanceModeAll = document.getElementById('governance-mode-all');
const governanceSheetRecent = document.getElementById('governance-sheet-recent');
const governanceSheetRecentGrid = document.getElementById('governance-sheet-recent-grid');
const generatedAt = document.getElementById('generated-at');
const refreshButton = document.getElementById('refresh-button');
const logoutButton = document.getElementById('logout-button');
const sessionLabel = document.getElementById('session-label');
const sidebarViewTitle = document.getElementById('sidebar-view-title');
const sidebarViewDescription = document.getElementById('sidebar-view-description');
const sidebarDirectorCard = document.getElementById('sidebar-director-card');
const sidebarDirectorMode = document.getElementById('sidebar-director-mode');
const sidebarDirectorCopy = document.getElementById('sidebar-director-copy');
const sidebarDirectorBadgePrimary = document.getElementById('sidebar-director-badge-primary');
const sidebarDirectorBadgeSecondary = document.getElementById('sidebar-director-badge-secondary');
const sidebarNextMoveTitle = document.getElementById('sidebar-next-move-title');
const sidebarNextMoveDetail = document.getElementById('sidebar-next-move-detail');
const sidebarOperatorLabel = document.getElementById('sidebar-operator-label');
const sidebarRuntimeLabel = document.getElementById('sidebar-runtime-label');
const sidebarGeneratedLabel = document.getElementById('sidebar-generated-label');
const sidebarPressureCard = document.getElementById('sidebar-pressure-card');
const sidebarPressureLabel = document.getElementById('sidebar-pressure-label');
const sidebarPressureDetail = document.getElementById('sidebar-pressure-detail');
const topbarFocusLabel = document.getElementById('topbar-focus-label');
const topbarRuntimeLabel = document.getElementById('topbar-runtime-label');
let governanceSheetReturnFocus = null;
const GOVERNANCE_RECENT_KEY = 'sanom_governance_recent_lanes';
const GOVERNANCE_RECENT_LIMIT = 4;
const GOVERNANCE_MODE_KEY = 'sanom_governance_launch_mode';
let governanceLaunchMode = 'priority';
let governanceRecentLanes = [];

function governanceLaneIdentity(view, controlRoomTool) {
  return `${String(view || 'overview')}::${String(controlRoomTool || '-')}`;
}

function loadGovernanceLaunchMode() {
  try {
    const saved = String(window.localStorage.getItem(GOVERNANCE_MODE_KEY) || '').trim();
    if (saved === 'all' || saved === 'priority') return saved;
  } catch (error) {
    console.warn(error);
  }
  return 'priority';
}

function loadGovernanceRecentLanes() {
  try {
    const raw = window.localStorage.getItem(GOVERNANCE_RECENT_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((lane) => ({
        view: String(lane?.view || 'overview'),
        controlRoomTool: String(lane?.controlRoomTool || ''),
        title: String(lane?.title || ''),
        caption: String(lane?.caption || ''),
      }))
      .filter((lane) => lane.title)
      .slice(0, GOVERNANCE_RECENT_LIMIT);
  } catch (error) {
    console.warn(error);
    return [];
  }
}

function persistGovernanceRecentLanes() {
  try {
    window.localStorage.setItem(GOVERNANCE_RECENT_KEY, JSON.stringify(governanceRecentLanes.slice(0, GOVERNANCE_RECENT_LIMIT)));
  } catch (error) {
    console.warn(error);
  }
}

function setGovernanceLaunchMode(mode, { persist = true } = {}) {
  const normalized = mode === 'all' ? 'all' : 'priority';
  governanceLaunchMode = normalized;
  if (governanceModePriority) {
    const active = normalized === 'priority';
    governanceModePriority.classList.toggle('is-active', active);
    governanceModePriority.setAttribute('aria-selected', active ? 'true' : 'false');
  }
  if (governanceModeAll) {
    const active = normalized === 'all';
    governanceModeAll.classList.toggle('is-active', active);
    governanceModeAll.setAttribute('aria-selected', active ? 'true' : 'false');
  }
  if (persist) {
    try {
      window.localStorage.setItem(GOVERNANCE_MODE_KEY, normalized);
    } catch (error) {
      console.warn(error);
    }
  }
  applyGovernanceSheetFilter(governanceSheetSearch?.value || '');
}

function renderGovernanceRecentLanes() {
  if (!governanceSheetRecent || !governanceSheetRecentGrid) return;
  if (!governanceRecentLanes.length) {
    governanceSheetRecent.hidden = true;
    governanceSheetRecentGrid.innerHTML = '';
    return;
  }
  governanceSheetRecentGrid.innerHTML = governanceRecentLanes.map((lane) => {
    const detail = lane.caption || 'Recent governance lane';
    return `<button class="nav-item nav-subitem governance-sheet-item governance-sheet-recent-item" type="button" data-view="${escapeHtml(lane.view)}"${lane.controlRoomTool ? ` data-control-room-tool="${escapeHtml(lane.controlRoomTool)}"` : ''}><span class="nav-item-title">${escapeHtml(lane.title)}</span><span class="nav-item-caption">${escapeHtml(detail)}</span></button>`;
  }).join('');
  governanceSheetRecent.hidden = false;
}

function rememberGovernanceLane(target) {
  if (!target) return;
  const view = String(target.dataset.view || 'overview').trim() || 'overview';
  const controlRoomTool = String(target.dataset.controlRoomTool || '').trim();
  const title = String(target.querySelector('.nav-item-title')?.textContent || '').trim();
  const caption = String(target.querySelector('.nav-item-caption')?.textContent || '').trim();
  if (!title) return;
  const identity = governanceLaneIdentity(view, controlRoomTool);
  const lane = { view, controlRoomTool, title, caption };
  governanceRecentLanes = [
    lane,
    ...governanceRecentLanes.filter((item) => governanceLaneIdentity(item.view, item.controlRoomTool) !== identity),
  ].slice(0, GOVERNANCE_RECENT_LIMIT);
  persistGovernanceRecentLanes();
  renderGovernanceRecentLanes();
}

function applyGovernanceSheetFilter(rawQuery = '') {
  if (!governanceSheet) return;
  const query = String(rawQuery || '').trim().toLowerCase();
  const searchActive = query.length > 0;
  let visibleCount = 0;

  let recentVisibleCount = 0;
  if (governanceSheetRecent && governanceSheetRecentGrid) {
    for (const recentItem of governanceSheetRecentGrid.querySelectorAll('.governance-sheet-recent-item')) {
      const haystack = `${recentItem.dataset.view || ''} ${recentItem.dataset.controlRoomTool || ''} ${recentItem.textContent || ''}`.toLowerCase();
      const visible = !query || haystack.includes(query);
      recentItem.hidden = !visible;
      if (visible) recentVisibleCount += 1;
    }
    governanceSheetRecent.hidden = recentVisibleCount === 0;
    visibleCount += recentVisibleCount;
  }

  for (const group of governanceSheet.querySelectorAll('.governance-sheet-group')) {
    const groupMode = String(group.dataset.governanceGroup || 'all').trim();
    const modeAllowed = searchActive ? true : governanceLaunchMode === 'all' || groupMode === 'priority';
    const items = Array.from(group.querySelectorAll('.governance-sheet-item'));
    let groupVisibleCount = 0;
    for (const item of items) {
      if (!modeAllowed) {
        item.hidden = true;
        continue;
      }
      const haystack = `${item.dataset.view || ''} ${item.dataset.controlRoomTool || ''} ${item.textContent || ''}`.toLowerCase();
      const visible = !query || haystack.includes(query);
      item.hidden = !visible;
      if (visible) groupVisibleCount += 1;
    }
    group.hidden = groupVisibleCount === 0;
    visibleCount += groupVisibleCount;
  }

  if (governanceSheetSearchCount) {
    governanceSheetSearchCount.textContent = `${visibleCount} lane${visibleCount === 1 ? '' : 's'}`;
  }
  if (governanceSheetEmpty) {
    governanceSheetEmpty.hidden = visibleCount !== 0;
  }
}

function resetGovernanceSheetFilter() {
  if (governanceSheetSearch) {
    governanceSheetSearch.value = '';
  }
  applyGovernanceSheetFilter('');
}

function closeGovernanceSheet() {
  if (!governanceSheet) return;
  governanceSheet.hidden = true;
  governanceSheet.setAttribute('aria-hidden', 'true');
  governanceLauncher?.setAttribute('aria-expanded', 'false');
  document.body.classList.remove('governance-sheet-open');
  resetGovernanceSheetFilter();
  if (governanceSheetReturnFocus && document.contains(governanceSheetReturnFocus)) {
    governanceSheetReturnFocus.focus({ preventScroll: true });
  }
  governanceSheetReturnFocus = null;
}

function openGovernanceSheet() {
  if (!governanceSheet) return;
  governanceSheetReturnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : governanceLauncher;
  governanceSheet.hidden = false;
  governanceSheet.setAttribute('aria-hidden', 'false');
  governanceLauncher?.setAttribute('aria-expanded', 'true');
  document.body.classList.add('governance-sheet-open');
  renderGovernanceRecentLanes();
  applyGovernanceSheetFilter(governanceSheetSearch?.value || '');
  window.requestAnimationFrame(() => {
    if (governanceSheetSearch) {
      governanceSheetSearch.focus({ preventScroll: true });
      governanceSheetSearch.select();
      return;
    }
    const focusTarget = governanceSheet.querySelector('.governance-sheet-item, #governance-sheet-close');
    focusTarget?.focus({ preventScroll: true });
  });
}

function navigateFromGovernanceTarget(target) {
  if (!target || target.hidden) return;
  const nextView = target.dataset.view || 'overview';
  const controlRoomTool = String(target.dataset.controlRoomTool || '').trim();
  rememberGovernanceLane(target);
  state.view = nextView;
  if (nextView === 'control_room') {
    state.controlRoomTool = controlRoomTool || getInitialControlRoomTool();
  }
  closeGovernanceSheet();
  updateNav();
  render();
  scrollDashboardToTop();
}

governanceLaunchMode = loadGovernanceLaunchMode();
governanceRecentLanes = loadGovernanceRecentLanes();
renderGovernanceRecentLanes();
setGovernanceLaunchMode(governanceLaunchMode, { persist: false });

function setLiveTimestampLabel(text) {
  generatedAt.textContent = text;
  sidebarGeneratedLabel.textContent = text;
}
function stopLiveTimestampTicker() {
  if (state.liveClock.timerId) {
    window.clearInterval(state.liveClock.timerId);
    state.liveClock.timerId = null;
  }
  state.liveClock.sourceIso = '';
  state.liveClock.sourceMs = 0;
  state.liveClock.clientStartedMs = 0;
}

function renderLiveTimestampTick() {
  if (!state.liveClock.sourceMs) return;
  const nowMs = Date.now();
  const elapsedMs = Math.max(0, nowMs - state.liveClock.clientStartedMs);
  const liveTimestamp = new Date(state.liveClock.sourceMs + elapsedMs);
  setLiveTimestampLabel(`Live data: ${formatDateTime(liveTimestamp)}`);
  refreshSessionContinuityTick(nowMs);
}

function formatRemainingDuration(remainingMs) {
  if (!Number.isFinite(remainingMs)) return '-';
  if (remainingMs <= 0) return 'Expired';
  const totalSeconds = Math.max(0, Math.floor(remainingMs / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) return `${hours}h ${String(minutes).padStart(2, '0')}m left`;
  if (minutes > 0) return `${minutes}m ${String(seconds).padStart(2, '0')}s left`;
  return `${seconds}s left`;
}

function hasStoredAccessToken() {
  return Boolean(String(state.token || '').trim());
}

function buildSessionContinuityState(session, nowMs = Date.now()) {
  const idleTarget = session.session_idle_expires_at ? new Date(session.session_idle_expires_at).getTime() : Number.NaN;
  const signedTarget = session.session_expires_at ? new Date(session.session_expires_at).getTime() : Number.NaN;
  const idleLabel = Number.isNaN(idleTarget)
    ? `${session.session_idle_timeout_minutes || '-'} minute idle window`
    : formatRemainingDuration(idleTarget - nowMs);
  const signedLabel = Number.isNaN(signedTarget)
    ? `${session.session_ttl_minutes || '-'} minute signed session`
    : formatRemainingDuration(signedTarget - nowMs);
  const canReconnect = hasStoredAccessToken();
  const continuityStatus = String(session.session_continuity_status || '').trim() || String(session.session_status || 'inactive');
  const shape = {
    status: continuityStatus,
    title: String(session.session_continuity_title || ''),
    note: String(session.session_continuity_note || ''),
    action: String(session.session_continuity_action || ''),
    badge: continuityStatus,
    actionLabel: 'Keep working',
    helper: canReconnect
      ? 'A stored private access token can renew this tablet session without leaving Home.'
      : 'This device will need the private access token again once the current session cools down.',
    idleLabel,
    signedLabel,
  };

  if (!canReconnect && continuityStatus === 'standby') {
    shape.status = 'sign_in_again';
    shape.badge = 'sign in again';
    shape.actionLabel = 'Sign in again';
    shape.title = shape.title || 'Sign in again to reopen the private runtime';
    shape.note = shape.note || 'No active tablet session is available and this device is not holding a stored access token for silent reconnect.';
    return shape;
  }
  if (continuityStatus === 'reconnect_now' || continuityStatus === 'standby') {
    shape.badge = continuityStatus === 'standby' ? 'standby' : 'reconnect now';
    shape.actionLabel = canReconnect ? 'Reconnect now' : 'Sign in again';
    shape.title = shape.title || (canReconnect ? 'Reconnect now to keep work moving' : 'Sign in again to continue tablet work');
    shape.note = shape.note || (canReconnect
      ? 'The private session is no longer active. Reconnect from Home before you continue touch-first work.'
      : 'The private session is no longer active and needs a fresh sign-in before work can continue.');
    return shape;
  }
  if (continuityStatus === 'idle_lock_soon') {
    shape.badge = 'renew now';
    shape.actionLabel = 'Renew session';
    return shape;
  }
  if (continuityStatus === 'renew_soon') {
    shape.badge = 'renew soon';
    shape.actionLabel = 'Renew soon';
    return shape;
  }
  shape.status = 'ready';
  shape.badge = 'ready';
  shape.actionLabel = 'Stay in lane';
  shape.title = shape.title || 'The private session is live and stable';
  shape.note = shape.note || 'This private session is warm and ready for touch-first work.';
  return shape;
}

function refreshSessionContinuityTick(nowMs = Date.now()) {
  const continuity = buildSessionContinuityState(state.session || {}, nowMs);
  document.querySelectorAll('[data-session-clock="idle"]').forEach((node) => {
    node.textContent = continuity.idleLabel;
  });
  document.querySelectorAll('[data-session-clock="signed"]').forEach((node) => {
    node.textContent = continuity.signedLabel;
  });
  document.querySelectorAll('[data-session-clock="note"]').forEach((node) => {
    node.textContent = continuity.note;
  });
  document.querySelectorAll('[data-session-clock="title"]').forEach((node) => {
    node.textContent = continuity.title;
  });
  document.querySelectorAll('[data-session-clock="helper"]').forEach((node) => {
    node.textContent = continuity.helper;
  });
  document.querySelectorAll('[data-session-clock="action-label"]').forEach((node) => {
    node.textContent = continuity.actionLabel;
  });
}

function startLiveTimestampTicker(value) {
  const parsedMs = value ? new Date(value).getTime() : Number.NaN;
  if (Number.isNaN(parsedMs)) {
    stopLiveTimestampTicker();
    setLiveTimestampLabel('Live data unavailable');
    return;
  }
  const sourceIso = String(value);
  if (state.liveClock.timerId && state.liveClock.sourceIso === sourceIso) {
    renderLiveTimestampTick();
    return;
  }
  stopLiveTimestampTicker();
  state.liveClock.sourceIso = sourceIso;
  state.liveClock.sourceMs = parsedMs;
  state.liveClock.clientStartedMs = Date.now();
  renderLiveTimestampTick();
  state.liveClock.timerId = window.setInterval(renderLiveTimestampTick, 1000);
}

function getInitialDashboardView() {
  const path = window.location.pathname || '/';
  if (path === '/control-room' || path === '/governance/control-room') return 'control_room';
  return 'overview';
}

function getInitialControlRoomTool() {
  return 'health';
}

const VIEW_TITLES = {
  overview: 'Home',
  requests: 'Work Inbox',
  cases: 'Cases',
  directory: 'Directory & Search',
  documents: 'Documents',
  actions: 'AI Actions',
  setup: 'Setup Assistant',
  overrides: 'Overrides',
  conflicts: 'Conflicts & Locks',
  audit: 'Audit Trail',
  studio: 'Role Private Studio',
  human_ask: 'Human Ask',
  sessions: 'Sessions',
  policies: 'Roles & Policies',
  health: 'Runtime Health',
  control_room: 'Control Room',
  backup_restore: 'Backup & Restore',
  admin_settings: 'Admin Settings',
  owner_registration: 'Owner Registration',
  retention: 'Documents & Records',
  integrations: 'Integrations',
  model_providers: 'Model Providers',
  evidence_exports: 'Trust & Evidence',
  master_data: 'Master Data & Routing',
  structural_risk: 'Structural Risk & Alignment',
};

const VIEW_DESCRIPTIONS = {
  overview: 'See posture, choose a lane, and move in seconds.',
  requests: 'Process governed intake and keep the queue moving.',
  cases: 'Track one issue across requests, decisions, and proof.',
  directory: 'Find real owners quickly and route work with confidence.',
  documents: 'Advance draft, review, and publish flows with governance intact.',
  actions: 'Run governed AI actions and monitor side effects in one lane.',
  setup: 'Complete first-run setup and pilot checks quickly.',
  overrides: 'Resolve human-required decisions without losing continuity.',
  conflicts: 'Clear contention fast and resume stalled work safely.',
  audit: 'Verify chain integrity, rationale, and exportable evidence.',
  studio: 'Create and publish governed AI roles from one place.',
  human_ask: 'Start governed reports and meeting records fast.',
  sessions: 'Review issued access, expiry, and revocation posture.',
  policies: 'Inspect role boundaries and trusted policy packs.',
  health: 'Check runtime readiness, risks, and operational posture.',
  control_room: 'Operate advanced governance tools in one protected surface.',
  backup_restore: 'Manage backup posture and recovery readiness.',
  admin_settings: 'Set organization defaults, access policy, and routing.',
  owner_registration: 'Verify owner identity and deployment ownership posture.',
  retention: 'Govern retention windows and legal-hold controls.',
  integrations: 'Review outbound routing and integration readiness.',
  model_providers: 'Check provider readiness and default execution lane.',
  evidence_exports: 'Export trusted evidence packs and audit proof.',
  master_data: 'Govern people, teams, assignments, and searchable routing.',
  structural_risk: 'Review PT-OSS structural risk and alignment posture.',
};

const DEV_LANES = {
  viewer: {
    token: 'sanom-viewer-token',
    view: getInitialDashboardView(),
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
    narrative: 'Use this page when you need the linked request, override, Human Ask, document, and audit trail in one place.',
    emphasis: 'end-to-end trace',
  },
  directory: {
    eyebrow: 'Org Work Graph',
    title: 'Real people, real teams, real assignments, one searchable operating map',
    narrative: 'Use this page when you need to route work to a real owner, inspect who sits where, or search continuity across cases, documents, and AI actions.',
    emphasis: 'people and ownership',
  },
  documents: {
    eyebrow: 'Document Runtime',
    title: 'Governed documents as live operating objects',
    narrative: 'Use this page when a draft, review, publish, or supersede flow must stay tied to runtime proof and case continuity.',
    emphasis: 'document lifecycle',
  },
  actions: {
    eyebrow: 'AI Runtime',
    title: 'Governed AI work with explicit authority, side effects, and proof',
    narrative: 'Use this page when AI should act inside a case instead of only reporting on it.',
    emphasis: 'action execution',
  },
  setup: {
    eyebrow: 'First-Run Assistant',
    title: 'Make the runtime pilot-ready without dropping into plumbing first',
    narrative: 'Use this page when onboarding, diagnostics, doctor results, and pilot hardening need one governed setup lane.',
    emphasis: 'pilot readiness',
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
  cases: { value: 'Trace the whole issue', note: 'Use this when one business issue spans requests, approvals, records, documents, and evidence.', tone: 'accent' },
  directory: { value: 'Route work to real owners', note: 'Use this when ownership, assignment, team context, or search continuity matters.', tone: 'accent' },
  documents: { value: 'Work the governed document lane', note: 'Use this when draft, review, publish, archive, or active-version logic matters.', tone: 'accent' },
  actions: { value: 'Let AI execute governed work', note: 'Use this when a case is ready for summarize, document draft, or human handoff actions.', tone: 'accent' },
  setup: { value: 'Finish pilot setup', note: 'Use this when onboarding, diagnostics, and pilot hardening still need guided action.', tone: 'warning' },
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
  directory: 'dashboard.read',
  documents: 'documents.read',
  actions: 'actions.read',
  setup: 'dashboard.read',
  overrides: 'overrides.read',
  conflicts: 'locks.read',
  audit: 'audit.read',
  studio: 'studio.read',
  human_ask: 'human_ask.read',
  sessions: 'sessions.read',
  policies: 'roles.read',
  health: 'health.read',
};

const TOPBAR_QUICK_ACTIONS = {
  overview: [
    { view: 'requests', label: 'Open Work Inbox', detail: 'Process incoming governed work.' },
    { view: 'cases', label: 'Open Cases', detail: 'Continue the linked operating story.' },
    { view: 'control_room', controlRoomTool: 'health', label: 'Open Runtime & Recovery', detail: 'Check governance posture quickly.' },
  ],
  requests: [
    { view: 'cases', label: 'Open Cases', detail: 'Trace continuity across lanes.' },
    { view: 'actions', label: 'Open AI Actions', detail: 'Run governed execution safely.' },
    { view: 'overrides', label: 'Open Overrides', detail: 'Resolve human boundaries now.' },
  ],
  cases: [
    { view: 'requests', label: 'Open Work Inbox', detail: 'Follow upstream intake context.' },
    { view: 'documents', label: 'Open Documents', detail: 'Continue document-side follow-through.' },
    { view: 'audit', label: 'Open Audit Trail', detail: 'Validate reasons and proof.' },
  ],
  directory: [
    { view: 'cases', label: 'Open Cases', detail: 'Route ownership into active issues.' },
    { view: 'requests', label: 'Open Work Inbox', detail: 'Reconnect intake and assignment.' },
    { view: 'control_room', controlRoomTool: 'master_data', label: 'Open Master Data & Routing', detail: 'Tune governance routing posture.' },
  ],
  documents: [
    { view: 'actions', label: 'Open AI Actions', detail: 'Continue AI-assisted follow-through.' },
    { view: 'cases', label: 'Open Cases', detail: 'Return to the canonical case story.' },
    { view: 'audit', label: 'Open Audit Trail', detail: 'Confirm document evidence chain.' },
  ],
  actions: [
    { view: 'cases', label: 'Open Cases', detail: 'Anchor results to one issue.' },
    { view: 'documents', label: 'Open Documents', detail: 'Continue governed artifacts.' },
    { view: 'audit', label: 'Open Audit Trail', detail: 'Verify authority and side effects.' },
  ],
  overrides: [
    { view: 'requests', label: 'Open Work Inbox', detail: 'Reconnect approved work to intake.' },
    { view: 'audit', label: 'Open Audit Trail', detail: 'Confirm decision proof chain.' },
    { view: 'overview', label: 'Open Home', detail: 'Recheck overall posture.' },
  ],
  conflicts: [
    { view: 'requests', label: 'Open Work Inbox', detail: 'Inspect stalled request lanes.' },
    { view: 'health', label: 'Open Runtime Health', detail: 'Review lock/runtime pressure.' },
    { view: 'audit', label: 'Open Audit Trail', detail: 'Trace contention history.' },
  ],
  audit: [
    { view: 'overview', label: 'Open Home', detail: 'Return to executive posture scan.' },
    { view: 'requests', label: 'Open Work Inbox', detail: 'Reconnect proof with live work.' },
    { view: 'health', label: 'Open Runtime Health', detail: 'Check operational integrity context.' },
  ],
  studio: [
    { view: 'control_room', controlRoomTool: 'studio', label: 'Open Role Private Studio', detail: 'Continue role authoring and publish flow.' },
    { view: 'policies', label: 'Open Roles & Policies', detail: 'Verify trusted role packs.' },
    { view: 'audit', label: 'Open Audit Trail', detail: 'Confirm publication evidence.' },
  ],
  human_ask: [
    { view: 'overrides', label: 'Open Overrides', detail: 'Resolve waiting human decisions.' },
    { view: 'documents', label: 'Open Documents', detail: 'Continue governed artifacts.' },
    { view: 'audit', label: 'Open Audit Trail', detail: 'Review record evidence chain.' },
  ],
  sessions: [
    { view: 'audit', label: 'Open Audit Trail', detail: 'Pair access posture with evidence.' },
    { view: 'health', label: 'Open Runtime Health', detail: 'Check token/session runtime state.' },
    { view: 'overview', label: 'Open Home', detail: 'Return to overall command posture.' },
  ],
  policies: [
    { view: 'studio', label: 'Open Role Private Studio', detail: 'Repair or publish role packs.' },
    { view: 'requests', label: 'Open Work Inbox', detail: 'Exercise trusted roles in live flow.' },
    { view: 'audit', label: 'Open Audit Trail', detail: 'Verify trust and manifest evidence.' },
  ],
  health: [
    { view: 'audit', label: 'Open Audit Trail', detail: 'Confirm proof behind health posture.' },
    { view: 'overview', label: 'Open Home', detail: 'Return to mission-level posture.' },
    { view: 'sessions', label: 'Open Sessions', detail: 'Check access continuity signals.' },
  ],
  control_room: [
    { view: 'control_room', controlRoomTool: 'health', label: 'Open Runtime & Recovery', detail: 'Run diagnostics and recovery checks.' },
    { view: 'control_room', controlRoomTool: 'setup', label: 'Open Setup & Onboarding', detail: 'Handle first-run and quick-start tasks.' },
    { view: 'control_room', controlRoomTool: 'evidence_exports', label: 'Open Trust & Evidence', detail: 'Prepare audit and evidence exports.' },
  ],
};

const CONTROL_ROOM_TOOLS = new Set(['health', 'conflicts', 'audit', 'policies', 'sessions', 'backup_restore', 'admin_settings', 'owner_registration', 'retention', 'integrations', 'model_providers', 'evidence_exports', 'master_data', 'structural_risk']);
const GOVERNANCE_EMBEDDED_VIEWS = new Set(['setup', 'studio']);

const ACTIONABLE_BUTTON_SELECTOR = [
  '[data-dev-lane]',
  '[data-view-jump]',
  '[data-case-scope-clear]',
  '[data-path-action]',
  '[data-directory-search-clear]',
  '[data-studio-clear]',
  '[data-override-action]',
  '[data-session-revoke]',
  '[data-session-renew]',
  '[data-audit-action]',
  '[data-ops-action]',
  '[data-integration-action]',
  '[data-retention-action]',
  '[data-human-ask-action]',
  '[data-action-runtime-action]',
  '[data-control-room-tool]',
  '[data-studio-governance-select]',
  '[data-studio-template-apply]',
  '[data-studio-panel-action]',
  '[data-studio-action]',
  '[data-team-quick-access]',
].join(', ');

navList.addEventListener('click', (event) => {
  const target = event.target.closest('.nav-item');
  if (!target) return;
  const nextView = target.dataset.view || 'overview';
  const controlRoomTool = String(target.dataset.controlRoomTool || '').trim();
  state.view = nextView;
  if (nextView === 'control_room') {
    state.controlRoomTool = controlRoomTool || getInitialControlRoomTool();
  }
  closeGovernanceSheet();
  updateNav();
  render();
  scrollDashboardToTop();
});

governanceLauncher?.addEventListener('click', () => {
  if (governanceSheet?.hidden) {
    openGovernanceSheet();
  } else {
    closeGovernanceSheet();
  }
});

governanceSheetClose?.addEventListener('click', () => {
  closeGovernanceSheet();
});

governanceModePriority?.addEventListener('click', () => {
  setGovernanceLaunchMode('priority');
});

governanceModeAll?.addEventListener('click', () => {
  setGovernanceLaunchMode('all');
});

governanceSheetSearch?.addEventListener('input', () => {
  applyGovernanceSheetFilter(governanceSheetSearch.value);
});

governanceSheetSearch?.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter') return;
  const firstVisible = governanceSheet?.querySelector('.governance-sheet-item:not([hidden])');
  if (firstVisible instanceof HTMLElement) {
    event.preventDefault();
    navigateFromGovernanceTarget(firstVisible);
  }
});

governanceSheet?.addEventListener('click', (event) => {
  if (event.target.closest('[data-governance-sheet-close]')) {
    closeGovernanceSheet();
    return;
  }
  const target = event.target.closest('.governance-sheet-item');
  if (target) {
    navigateFromGovernanceTarget(target);
  }
});

document.addEventListener('keydown', (event) => {
  if (!governanceSheet || governanceSheet.hidden) return;
  if (event.key === 'Escape') {
    closeGovernanceSheet();
    return;
  }
  if (event.key === '/' && governanceSheetSearch && document.activeElement !== governanceSheetSearch) {
    event.preventDefault();
    governanceSheetSearch.focus({ preventScroll: true });
    governanceSheetSearch.select();
  }
});

topbarActionStrip?.addEventListener('click', async (event) => {
  const viewJumpButton = event.target.closest('[data-view-jump]');
  if (!viewJumpButton) return;
  event.preventDefault();
  await handleViewJumpAction(viewJumpButton);
});

refreshButton.addEventListener('click', () => withButtonBusy(refreshButton, () => loadDashboard(), 'Refreshing...'));
askAiButton?.addEventListener('click', () => {
  state.view = 'human_ask';
  updateNav();
  render();
  scrollDashboardToTop();
});
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
  state.documentEditingId = null;
  state.studioEditorDraft = null;
  state.studioGovernanceRequestId = null;
  state.studioGovernanceNotes = {};
  state.studioRevisionSelections = {};
  state.studioPtagDrafts = {};
  state.studioPtagHistory = {};
  state.actionContext = null;
  state.documentFilters = {
    query: '',
    status: '',
    documentClass: '',
    caseId: '',
    activeOnly: false,
  };
  state.documentSearchResult = null;
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
      state.view = canAccessControlRoom() ? 'control_room' : 'studio';
      if (canAccessControlRoom()) state.controlRoomTool = 'studio';
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

  if (event.target.id === 'document-form') {
    event.preventDefault();
    try {
      const payload = buildDocumentPayload(document);
      const editingDocumentId = state.documentEditingId;
      const response = await apiFetch(editingDocumentId ? `/api/documents/${encodeURIComponent(editingDocumentId)}/update` : '/api/documents', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const item = response.item || response;
      const documentId = extractEntityId(response, ['document_id']) || editingDocumentId;
      const documentLabel = item.document_number || documentId || 'document';
      state.lastError = editingDocumentId
        ? `Governed document ${documentLabel} saved into the runtime.`
        : `Governed document ${documentLabel} created in the runtime.`;
      setActionContext({
        entityType: 'document',
        entityId: documentId,
        caseId: item.case_id || '',
        view: 'documents',
        title: editingDocumentId
          ? `Document ${documentLabel} is ready for the next governed move.`
          : `Document ${documentLabel} entered the governed document lane.`,
        detail: editingDocumentId
          ? 'The updated draft remains highlighted so review, publish, or archive can continue without hunting for it.'
          : 'The new governed document stays highlighted in the Documents lane and is stitched back into case continuity when a case id is present.',
        actionLabel: 'Open Documents',
      });
      clearDocumentEditor();
      state.view = 'documents';
      updateNav();
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
    return;
  }

  if (event.target.id === 'document-search-form') {
    event.preventDefault();
    syncDocumentFiltersFromForm(document);
    try {
      await withButtonBusy(event.submitter, () => refreshDocumentSearchResults({ silent: false }), 'Searching...');
      state.view = 'documents';
      updateNav();
      scrollDashboardToTop();
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
      const registrationTargetView = state.view === 'setup' ? 'setup' : 'health';
      state.lastError = `Registration code ${item.registration_code || 'saved'} is active for ${item.organization_name || 'the current organization'} in ${item.deployment_mode || 'private'} mode.`;
      setActionContext({
        entityType: '',
        entityId: '',
        view: registrationTargetView,
        title: state.view === 'setup' ? 'Owner registration saved inside Setup Assistant.' : 'Owner registration saved.',
        detail: state.view === 'setup'
          ? 'The setup lane refreshed so pilot readiness, doctor status, and next setup actions stay visible in one place.'
          : 'Runtime Health is the next governed lane because deployment, trust, and operator posture may have changed.',
        actionLabel: state.view === 'setup' ? 'Stay in Setup Assistant' : 'Open Runtime Health',
      });
      state.view = registrationTargetView;
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
  if (event.target.id === 'directory-search-input') {
    state.directorySearchQuery = event.target.value || '';
    render();
    return;
  }
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

async function handleViewJumpAction(viewJumpButton) {
  if (!viewJumpButton) return false;
  const targetView = viewJumpButton.dataset.viewJump || state.view;
  const focusType = viewJumpButton.dataset.viewJumpFocusType || '';
  const focusId = viewJumpButton.dataset.viewJumpFocusId || '';
  const caseId = viewJumpButton.dataset.viewJumpCaseId || '';
  const controlRoomTool = viewJumpButton.dataset.viewJumpControlRoomTool || '';
  const resolvedTarget = normalizeActionContextTarget({
    view: targetView,
    controlRoomTool,
    title: viewJumpButton.dataset.viewJumpTitle || `Moved to ${VIEW_TITLES[targetView] || titleCase(targetView)}.`,
    detail: viewJumpButton.dataset.viewJumpDetail || 'The linked governed item stays highlighted in the next lane so you can continue without hunting for it.',
    actionLabel: viewJumpButton.dataset.viewJumpActionLabel || `Open ${VIEW_TITLES[targetView] || titleCase(targetView)}`,
  });
  setActionContext({
    entityType: focusType,
    entityId: focusId,
    caseId,
    view: resolvedTarget.view,
    controlRoomTool: resolvedTarget.controlRoomTool,
    title: resolvedTarget.title,
    detail: resolvedTarget.detail,
    actionLabel: resolvedTarget.actionLabel,
  });
  state.view = resolvedTarget.view;
  if (resolvedTarget.controlRoomTool) state.controlRoomTool = resolvedTarget.controlRoomTool;
  updateNav();
  if (resolvedTarget.view === 'documents' && documentFiltersActive()) {
    try {
      await refreshDocumentSearchResults({ silent: true, skipRender: true });
    } catch (error) {
      state.lastError = String(error.message || error);
    }
  }
  render();
  scrollDashboardToTop();
  return true;
}

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

  const sessionRenewButton = event.target.closest('[data-session-renew]');
  if (sessionRenewButton) {
    await withButtonBusy(sessionRenewButton, () => renewPrivateSession({ manual: true }), 'Renewing...');
    scrollDashboardToTop();
    return;
  }

  const viewJumpButton = event.target.closest('[data-view-jump]');
  if (viewJumpButton) {
    await handleViewJumpAction(viewJumpButton);
    return;
  }

  const controlRoomToolButton = event.target.closest('[data-control-room-tool]');
  if (controlRoomToolButton) {
    state.view = 'control_room';
    state.controlRoomTool = controlRoomToolButton.dataset.controlRoomTool || 'health';
    updateNav();
    render();
    scrollDashboardToTop();
    return;
  }

  const teamQuickAccessButton = event.target.closest('[data-team-quick-access]');
  if (teamQuickAccessButton) {
    state.directorySearchQuery = teamQuickAccessButton.dataset.teamQuickAccess || '';
    state.view = 'directory';
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
    if (state.view === 'documents' && documentFiltersActive()) {
      try {
        await refreshDocumentSearchResults({ silent: true, skipRender: true });
      } catch (error) {
        state.lastError = String(error.message || error);
      }
    }
    state.lastError = `Showing the full ${VIEW_TITLES[state.view] || titleCase(state.view)} lane again.`;
    render();
    scrollDashboardToTop();
    return;
  }

  const directorySearchClearButton = event.target.closest('[data-directory-search-clear]');
  if (directorySearchClearButton) {
    state.directorySearchQuery = '';
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

  const clearDocumentFilterButton = event.target.closest('[data-document-filter-clear]');
  if (clearDocumentFilterButton) {
    clearDocumentFilters();
    state.lastError = 'Document runtime search cleared.';
    render();
    scrollDashboardToTop();
    return;
  }

  const useCurrentCaseFilterButton = event.target.closest('[data-document-filter-current-case]');
  if (useCurrentCaseFilterButton) {
    state.documentFilters.caseId = getActionContextCaseId() || '';
    try {
      await refreshDocumentSearchResults({ silent: false });
      scrollDashboardToTop();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
    }
    return;
  }

  const clearDocumentButton = event.target.closest('[data-document-clear]');
  if (clearDocumentButton) {
    clearDocumentEditor();
    state.lastError = 'Document editor cleared.';
    render();
    return;
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

  const documentButton = event.target.closest('[data-document-action]');
  if (documentButton) {
    const action = documentButton.dataset.documentAction || '';
    const documentId = documentButton.dataset.documentId || '';
    const item = getDocumentById(state.snapshot, documentId);
    const documentLabel = item?.document_number || documentId || 'document';
    try {
      if (action === 'load') {
        loadDocumentIntoEditor(documentId);
        state.lastError = `${documentLabel} loaded into the document editor.`;
        setActionContext({
          entityType: 'document',
          entityId: documentId,
          caseId: item?.case_id || '',
          view: 'documents',
          title: `${documentLabel} loaded into the document editor.`,
          detail: 'Continue in the same lane to update the working draft or prepare the next governed revision.',
          actionLabel: 'Open Documents',
        });
        render();
        scrollDashboardToTop();
        focusDocumentEditor();
        return;
      }

      let endpoint = '';
      let payload = {};
      if (action === 'submit-review') {
        const note = window.prompt(`Submit ${documentLabel} for review note`, 'Submitted from dashboard.');
        if (note === null) return;
        endpoint = `/api/documents/${encodeURIComponent(documentId)}/submit-review`;
        payload = { note };
      }
      if (action === 'approve') {
        const note = window.prompt(`Approve ${documentLabel} note`, 'Approved from dashboard.');
        if (note === null) return;
        endpoint = `/api/documents/${encodeURIComponent(documentId)}/approve`;
        payload = { note };
      }
      if (action === 'publish') {
        const note = window.prompt(`Publish ${documentLabel} note`, 'Published from dashboard.');
        if (note === null) return;
        endpoint = `/api/documents/${encodeURIComponent(documentId)}/publish`;
        payload = { note };
      }
      if (action === 'archive') {
        const note = window.prompt(`Archive ${documentLabel} note`, 'Archived from dashboard.');
        if (note === null) return;
        endpoint = `/api/documents/${encodeURIComponent(documentId)}/archive`;
        payload = { note };
      }
      if (!endpoint) return;

      const response = await apiFetch(endpoint, { method: 'POST', body: JSON.stringify(payload) });
      const updated = response.item || response;
      const nextDocumentId = extractEntityId(response, ['document_id']) || documentId;
      const nextLabel = updated.document_number || nextDocumentId || documentLabel;
      const nextStatus = formatStatusLabel(updated.status || action.replace('-', ' '));
      state.lastError = `${nextLabel} is now ${nextStatus}.`;
      setActionContext({
        entityType: 'document',
        entityId: nextDocumentId,
        caseId: updated.case_id || item?.case_id || '',
        view: 'documents',
        title: `${nextLabel} is now ${nextStatus}.`,
        detail: action === 'submit-review'
          ? 'The document stays highlighted in the review lane so the next reviewer can keep moving from the same governed record.'
          : action === 'approve'
            ? 'The approved document now sits in the publish-ready lane with the same case and active-version context.'
            : action === 'publish'
              ? 'The publish move keeps the same document highlighted so active-version and proof continuity can be verified immediately.'
              : 'The archived document remains traceable through the same lane and linked case story.',
        actionLabel: 'Open Documents',
      });
      if (state.documentEditingId === nextDocumentId) clearDocumentEditor();
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
    if (action === 'probe-model-providers') {
      try {
        const providerId = String(integrationButton.dataset.providerId || '').trim();
        const response = await apiFetch('/api/model-providers/probe', {
          method: 'POST',
          body: JSON.stringify(providerId ? { provider_id: providerId } : {}),
        });
        const result = response.result || {};
        state.lastError = providerId
          ? `Model provider probe for ${providerId} ${result.status || 'completed'}.`
          : `Model provider probe ${result.status || 'completed'}.`;
        await loadDashboard();
      } catch (error) {
        state.lastError = String(error.message || error);
        render();
      }
    }
    return;
  }

  const retentionButton = event.target.closest('[data-retention-action]');
  if (retentionButton) {
    try {
      const dryRun = String(retentionButton.dataset.retentionAction || 'dry-run') !== 'enforce-now';
      const response = await apiFetch('/api/retention/enforce', {
        method: 'POST',
        body: JSON.stringify({ dry_run: dryRun }),
      });
      const result = response.result || {};
      state.lastError = dryRun
        ? `Retention dry run ${result.status || 'completed'}.`
        : `Retention execution ${result.status || 'completed'}.`;
      await loadDashboard();
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
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


  const actionRuntimeButton = event.target.closest('[data-action-runtime-action]');
  if (actionRuntimeButton) {
    const runtimeAction = actionRuntimeButton.dataset.actionRuntimeAction || '';
    try {
      if (runtimeAction === 'create') {
        const actionType = actionRuntimeButton.dataset.actionType || '';
        const caseItem = getScopedActionCase(state.snapshot);
        if (!caseItem) {
          state.lastError = 'Open a case first, then launch the AI action inside that governed issue.';
          render();
          return;
        }
        const response = await apiFetch('/api/actions', {
          method: 'POST',
          body: JSON.stringify(buildActionRuntimePayload(actionType, caseItem, {
            label: actionRuntimeButton.dataset.actionLabel || '',
          })),
        });
        const item = response.item || response;
        const primary = resolveActionPrimaryFocus(item);
        const primaryView = primary.view || 'actions';
        const primaryViewLabel = VIEW_TITLES[primaryView] || titleCase(primaryView);
        state.lastError = `${item.label || titleCase(actionType || 'AI action')} created for ${caseItem.case_id}.`;
        setActionContext({
          entityType: primary.entityType || 'action',
          entityId: primary.entityId || item.action_id || '',
          caseId: item.case_id || caseItem.case_id || '',
          view: primaryView,
          title: `${item.label || titleCase(actionType || 'AI action')} completed its latest governed step.`,
          detail: item.next_action || 'The resulting work item stays linked to the same case and is ready in the next lane.',
          actionLabel: `Open ${primaryViewLabel}`,
        });
        await loadDashboard();
        return;
      }
      if (runtimeAction === 'execute') {
        const actionId = actionRuntimeButton.dataset.actionId || '';
        const currentItem = getActionById(state.snapshot, actionId);
        const response = await apiFetch(`/api/actions/${encodeURIComponent(actionId)}/execute`, {
          method: 'POST',
          body: JSON.stringify({}),
        });
        const item = response.item || response;
        const primary = resolveActionPrimaryFocus(item);
        const primaryView = primary.view || 'actions';
        const primaryViewLabel = VIEW_TITLES[primaryView] || titleCase(primaryView);
        state.lastError = `${item.label || currentItem?.label || actionId} re-ran in the governed AI runtime.`;
        setActionContext({
          entityType: primary.entityType || 'action',
          entityId: primary.entityId || item.action_id || actionId,
          caseId: item.case_id || currentItem?.case_id || '',
          view: primaryView,
          title: `${item.label || currentItem?.label || actionId} refreshed its governed result.`,
          detail: item.next_action || 'The refreshed action result is ready in the linked runtime lane.',
          actionLabel: `Open ${primaryViewLabel}`,
        });
        await loadDashboard();
        return;
      }
    } catch (error) {
      state.lastError = String(error.message || error);
      render();
      return;
    }
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
  state.documentEditingId = null;
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

function getActiveLaneTransition() {
  const laneTransition = state.laneTransition;
  if (!laneTransition || laneTransition.to !== state.view) return null;
  const startedAt = Number(laneTransition.startedAt || 0);
  if (startedAt && Date.now() - startedAt > LANE_TRANSITION_WINDOW_MS) return null;
  return laneTransition;
}

function humanizeCompassText(value, fallback = '-') {
  const raw = String(value || '').trim();
  if (!raw) return fallback;
  return raw.replace(/[_-]+/g, ' ');
}

function normalizeCompassTone(rawTone = '') {
  const value = String(rawTone || '').trim().toLowerCase();
  if (!value) return 'accent';
  if (value.includes('block') || value.includes('human') || value.includes('attention') || value.includes('warning')) return 'warning';
  if (value.includes('stable') || value.includes('ready') || value.includes('clear') || value.includes('calm') || value.includes('success')) return 'success';
  if (value.includes('idle') || value.includes('offline') || value.includes('paused')) return 'idle';
  return 'accent';
}

function getSidebarDirectorConsole(snapshot) {
  const intelligence = VIEW_INTELLIGENCE[state.view] || {};
  const useHint = VIEW_USE_HINTS[state.view] || {};
  const mission = snapshot?.command_surface?.mission_control || {};
  const transition = getActiveLaneTransition();
  const transitionFromLabel = transition?.from ? (VIEW_TITLES[transition.from] || titleCase(transition.from)) : '';
  const actionContext = state.actionContext || null;
  const nextMoveTitle = actionContext?.actionLabel
    || (state.view === 'overview'
      ? String(mission.top_move_title || 'Open the next governed lane')
      : String(useHint.value || `Open ${VIEW_TITLES[state.view] || titleCase(state.view)}`));
  const nextMoveDetail = actionContext?.detail
    || (state.view === 'overview'
      ? String(mission.top_move_detail || 'Open the linked governed lane and continue from the highest-pressure move.')
      : String(useHint.note || intelligence.narrative || 'Keep the next lane visible before moving deeper into the board.'));
  const worldPressure = String(mission.pressure_label || mission.world_state_title || 'Balanced world state').trim() || 'Balanced world state';
  const pressureDetailParts = [];
  if (mission.world_state_title && mission.world_state_title !== worldPressure) pressureDetailParts.push(String(mission.world_state_title));
  if (mission.ai_momentum_title) pressureDetailParts.push(String(mission.ai_momentum_title));
  pressureDetailParts.push(
    state.view === 'overview'
      ? String(mission.world_state_note || mission.ai_momentum_detail || 'Home keeps the whole operating picture readable.')
      : String(mission.ai_momentum_detail || mission.world_state_note || 'The broader world state stays visible while you work the current lane.')
  );
  const modeCopy = [
    transitionFromLabel ? `Entered from ${transitionFromLabel}.` : '',
    String(intelligence.narrative || useHint.note || 'Stay on the current lane until the next governed move is clear.'),
  ].filter(Boolean).join(' ');
  const modePrimaryBadge = humanizeCompassText(mission.world_state_badge || useHint.tone || 'guarded', 'guarded');
  const modeSecondaryBadge = transitionFromLabel ? `from ${transitionFromLabel}` : humanizeCompassText(intelligence.emphasis || 'director view', 'director view');
  const modeTone = normalizeCompassTone(actionContext ? 'accent' : String(mission.world_state_badge || useHint.tone || 'accent'));
  const pressureTone = normalizeCompassTone(worldPressure);
  return {
    modeTitle: state.view === 'overview' ? 'Mission control' : String(intelligence.eyebrow || 'Guided lane'),
    modeCopy,
    modePrimaryBadge,
    modeSecondaryBadge,
    modeTone,
    nextMoveTitle,
    nextMoveDetail,
    pressureLabel: worldPressure,
    pressureDetail: pressureDetailParts.filter(Boolean).join(' '),
    pressureTone,
  };
}

function setActionContext({ entityType = '', entityId = '', caseId = '', view = '', controlRoomTool = '', title = '', detail = '', actionLabel = '' } = {}) {
  const normalizedEntityType = String(entityType || '').trim();
  const normalizedEntityId = String(entityId || '').trim();
  const normalizedCaseId = String(caseId || (normalizedEntityType === 'case' ? normalizedEntityId : '')).trim();
  const focusKey = buildFocusKey(normalizedEntityType, normalizedEntityId);
  const normalizedTarget = normalizeActionContextTarget({
    view: view || state.view || 'overview',
    controlRoomTool,
    title,
    detail,
    actionLabel,
  });
  const targetView = normalizedTarget.view || 'overview';
  state.actionContext = {
    entityType: normalizedEntityType,
    entityId: normalizedEntityId,
    caseId: normalizedCaseId,
    focusKey,
    view: targetView,
    controlRoomTool: normalizedTarget.controlRoomTool || '',
    title: normalizedTarget.title || 'Latest governed result',
    detail: normalizedTarget.detail || 'The Director recorded the latest action and mapped the next governed move.',
    actionLabel: normalizedTarget.actionLabel || `Open ${VIEW_TITLES[targetView] || titleCase(targetView)}`,
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
    const snapshot = await apiFetch('/api/dashboard', {}, { useSession: Boolean(state.sessionToken), allowSessionRecovery: true });
    state.snapshot = snapshot;
    state.session = snapshot.session || null;
    state.authRequired = false;
    if (state.view === 'documents' && documentFiltersActive()) {
      await refreshDocumentSearchResults({ silent: true, skipRender: true });
    } else if (!documentFiltersActive()) {
      state.documentSearchResult = null;
    }
    render();
  } catch (error) {
    const message = String(error.message || error);
    if (message.includes('401')) {
      state.authRequired = true;
      state.session = null;
      state.snapshot = null;
      clearSessionToken();
    }
    state.lastError = message;
    render();
  }
}

function clearSessionToken() {
  state.sessionToken = '';
  window.localStorage.removeItem('sanom_session_token');
}

async function loginWithAccessToken() {
  if (!state.token) return;
  const response = await apiFetch('/api/session/login', { method: 'POST' }, { useAccessToken: true, allowSessionRecovery: false });
  state.sessionToken = response.session_token || '';
  if (state.sessionToken) {
    window.localStorage.setItem('sanom_session_token', state.sessionToken);
    state.authRequired = false;
  }
}

async function renewPrivateSession({ manual = false } = {}) {
  if (!state.token) {
    clearSessionToken();
    state.session = null;
    state.snapshot = null;
    state.authRequired = true;
    state.lastError = 'Private session can no longer be renewed from this device. Sign in again with the private access token.';
    render();
    return false;
  }
  clearSessionToken();
  await loginWithAccessToken();
  await loadDashboard();
  if (manual) {
    state.lastError = 'Private session renewed. Continue from the same command lane.';
    render();
  }
  return Boolean(state.sessionToken);
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


function getDocumentFilterState() {
  return {
    query: String(state.documentFilters?.query || '').trim(),
    status: String(state.documentFilters?.status || '').trim(),
    documentClass: String(state.documentFilters?.documentClass || '').trim(),
    caseId: String(state.documentFilters?.caseId || '').trim(),
    activeOnly: Boolean(state.documentFilters?.activeOnly),
  };
}

function getEffectiveDocumentFilterState() {
  const filters = getDocumentFilterState();
  if (!filters.caseId) {
    filters.caseId = getActionContextCaseId() || '';
  }
  return filters;
}

function documentFiltersActive(filters = getDocumentFilterState()) {
  return Boolean(filters.query || filters.status || filters.documentClass || filters.caseId || filters.activeOnly);
}

function syncDocumentFiltersFromForm(documentRef = document) {
  state.documentFilters = {
    query: documentRef.getElementById('document-search-query')?.value.trim() || '',
    status: documentRef.getElementById('document-search-status')?.value.trim() || '',
    documentClass: documentRef.getElementById('document-search-class')?.value.trim() || '',
    caseId: documentRef.getElementById('document-search-case-id')?.value.trim() || '',
    activeOnly: Boolean(documentRef.getElementById('document-search-active-only')?.checked),
  };
  return getDocumentFilterState();
}

function clearDocumentFilters() {
  state.documentFilters = {
    query: '',
    status: '',
    documentClass: '',
    caseId: '',
    activeOnly: false,
  };
  state.documentSearchResult = null;
}

function buildDocumentQueryString(filters = getEffectiveDocumentFilterState()) {
  const params = new URLSearchParams();
  if (filters.query) params.set('query', filters.query);
  if (filters.status) params.set('status', filters.status);
  if (filters.documentClass) params.set('document_class', filters.documentClass);
  if (filters.caseId) params.set('case_id', filters.caseId);
  if (filters.activeOnly) params.set('active_only', 'true');
  params.set('limit', '100');
  return params.toString();
}

async function refreshDocumentSearchResults({ silent = false, skipRender = false } = {}) {
  const filters = getDocumentFilterState();
  if (!documentFiltersActive(filters)) {
    state.documentSearchResult = null;
    if (!skipRender) render();
    return null;
  }
  const response = await apiFetch(`/api/documents?${buildDocumentQueryString(getEffectiveDocumentFilterState())}`);
  state.documentSearchResult = response.item || null;
  if (!silent) {
    const total = Number(state.documentSearchResult?.summary?.documents_total || 0);
    state.lastError = total
      ? `Showing ${total} governed document${total === 1 ? '' : 's'} from the current runtime search.`
      : 'No governed documents matched the current runtime search.';
  }
  if (!skipRender) render();
  return state.documentSearchResult;
}

function buildDocumentFilterPills(filters = getDocumentFilterState(), effectiveFilters = getEffectiveDocumentFilterState()) {
  const pills = [];
  if (filters.query) pills.push(`Query: ${filters.query}`);
  if (filters.status) pills.push(`Status: ${formatStatusLabel(filters.status)}`);
  if (filters.documentClass) pills.push(`Class: ${titleCase(filters.documentClass.replaceAll('_', ' '))}`);
  if (filters.caseId) pills.push(`Case: ${filters.caseId}`);
  if (filters.activeOnly) pills.push('Active only');
  if (effectiveFilters.caseId && !filters.caseId) pills.push(`Case scope: ${effectiveFilters.caseId}`);
  return pills;
}

async function apiFetch(path, options = {}, auth = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (auth.useSession && state.sessionToken) headers['X-SA-NOM-Session'] = state.sessionToken;
  else if (auth.useAccessToken && state.token) headers['X-SA-NOM-Token'] = state.token;
  else if (state.sessionToken) headers['X-SA-NOM-Session'] = state.sessionToken;
  else if (state.token) headers['X-SA-NOM-Token'] = state.token;
  const response = await fetch(path, { ...options, headers });
  const method = String(options.method || 'GET').toUpperCase();
  const canRecoverSession = response.status === 401
    && method === 'GET'
    && !auth.useAccessToken
    && Boolean(state.sessionToken)
    && hasStoredAccessToken()
    && auth.allowSessionRecovery !== false
    && !auth._retriedSession;
  if (canRecoverSession) {
    clearSessionToken();
    await loginWithAccessToken();
    if (state.sessionToken) {
      return apiFetch(path, options, { ...auth, useSession: true, allowSessionRecovery: false, _retriedSession: true });
    }
  }
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

function hydrateOrganizationSelector(snapshot) {
  if (!organizationSelector) return;
  const surface = snapshot.command_surface || {};
  const orgName = surface.organization_name || snapshot.owner_registration?.organization_name || snapshot.master_data?.summary?.organization_name || 'Organization';
  organizationSelector.innerHTML = `<option value="default">${escapeHtml(orgName)}</option>`;
}

function renderControlRoomDenied() {
  return `
    <article class="card notice-card notice-warning stack">
      <div>
        <div class="eyebrow muted">Governance access restricted</div>
        <h3 class="card-title">Control Room is reserved for Admin / IT / Founder sessions</h3>
        <p class="card-subtitle">Normal users stay on the simple command surface. Escalate to your governance lead if you need deeper runtime posture or evidence tooling.</p>
      </div>
      <div class="inline-actions">
        <button class="action-button" type="button" data-view-jump="overview">Open Home</button>
        <button class="action-button action-button-muted" type="button" data-view-jump="requests">Open Work Inbox</button>
      </div>
    </article>
  `;
}


function isControlRoomTool(view = '') {
  return CONTROL_ROOM_TOOLS.has(String(view || '').trim());
}

function resolveNavigationTarget({ view = '', controlRoomTool = '', title = '', detail = '', actionLabel = '' } = {}) {
  const normalizedView = String(view || 'overview').trim() || 'overview';
  if (normalizedView === 'control_room') {
    if (!canAccessControlRoom()) return null;
    const tool = String(controlRoomTool || state.controlRoomTool || getInitialControlRoomTool()).trim() || getInitialControlRoomTool();
    const toolLabel = VIEW_TITLES[tool] || titleCase(tool);
    return {
      view: 'control_room',
      controlRoomTool: tool,
      title: title || `Control Room opened on ${toolLabel}.`,
      detail: detail || `${toolLabel} is grouped inside the protected Control Room for advanced governance review.`,
      actionLabel: 'Open Control Room',
    };
  }
  if (GOVERNANCE_EMBEDDED_VIEWS.has(normalizedView)) {
    if (!canAccessControlRoom()) {
      return {
        view: normalizedView,
        controlRoomTool: '',
        title,
        detail,
        actionLabel,
      };
    }
    const tool = String(controlRoomTool || normalizedView).trim() || normalizedView;
    const toolLabel = VIEW_TITLES[tool] || titleCase(tool);
    return {
      view: 'control_room',
      controlRoomTool: tool,
      title: title || `Control Room opened on ${toolLabel}.`,
      detail: detail || `${toolLabel} now lives inside the protected Control Room instead of the simple command surface.`,
      actionLabel: 'Open Control Room',
    };
  }
  if (!isControlRoomTool(normalizedView)) {
    return {
      view: normalizedView,
      controlRoomTool: '',
      title,
      detail,
      actionLabel,
    };
  }
  if (!canAccessControlRoom()) return null;
  const tool = String(controlRoomTool || normalizedView).trim();
  const toolLabel = VIEW_TITLES[tool] || titleCase(tool);
  return {
    view: 'control_room',
    controlRoomTool: tool,
    title: title || `Control Room opened on ${toolLabel}.`,
    detail: detail || `${toolLabel} is available through the protected Control Room, not the simple command surface.`,
    actionLabel: 'Open Control Room',
  };
}

function normalizeActionContextTarget(options = {}) {
  const resolved = resolveNavigationTarget(options);
  if (resolved) return resolved;
  if (!isControlRoomTool(options.view) && String(options.view || '').trim() !== 'control_room') {
    return {
      view: String(options.view || 'overview').trim() || 'overview',
      controlRoomTool: '',
      title: options.title || '',
      detail: options.detail || '',
      actionLabel: options.actionLabel || '',
    };
  }
  return {
    view: 'overview',
    controlRoomTool: '',
    title: options.title || 'Advanced governance detail requires Control Room.',
    detail: 'This session stays on the simple command surface. Ask an Admin, IT, or Founder session to continue inside Control Room.',
    actionLabel: 'Open Home',
  };
}

function shouldRenderTabletLaneRail() {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia('(max-width: 1180px)').matches;
}

function shouldRenderFocusedInbox(view = state.view) {
  return ['requests', 'cases', 'directory', 'documents', 'actions', 'overrides', 'conflicts', 'audit', 'studio', 'human_ask', 'sessions', 'policies', 'health'].includes(view);
}

function shouldRenderWorkflowGuide(view = state.view) {
  return ['requests', 'cases', 'directory', 'documents', 'actions', 'overrides', 'conflicts', 'audit', 'studio', 'human_ask', 'sessions', 'policies', 'health'].includes(view);
}

function shouldRenderWorkLanguageGuide(view = state.view) {
  return ['overview', 'requests'].includes(view);
}

function isTopbarQuickActionAllowed(target) {
  if (!target) return false;
  if (target.view === 'setup' && !canAccessSetupAssistant()) return false;
  const permissionView = target.view === 'control_room' ? String(target.controlRoomTool || '').trim() : target.view;
  const permission = VIEW_PERMISSIONS[permissionView];
  if (!permission) return true;
  return can(permission);
}

function buildTopbarQuickActionCandidates(snapshot) {
  if (!snapshot || state.authRequired) {
    return [{
      view: 'overview',
      label: 'Open Home',
      title: 'Reconnect to continue',
      detail: 'Sign in, refresh live runtime, then continue governed work.',
      badge: 'reconnect',
    }];
  }
  const candidates = [];
  if (state.actionContext?.view) {
    const contextViewLabel = VIEW_TITLES[state.actionContext.view] || titleCase(state.actionContext.view);
    candidates.push({
      view: state.actionContext.view,
      controlRoomTool: state.actionContext.controlRoomTool || '',
      label: state.actionContext.actionLabel || `Continue in ${contextViewLabel}`,
      title: state.actionContext.title || `Continue in ${contextViewLabel}`,
      detail: state.actionContext.detail || `The latest governed item stays highlighted in ${contextViewLabel}.`,
      badge: 'continue',
    });
  }
  if (state.view === 'control_room') {
    const currentTool = String(state.controlRoomTool || getInitialControlRoomTool()).trim() || getInitialControlRoomTool();
    const currentToolLabel = VIEW_TITLES[currentTool] || titleCase(currentTool);
    candidates.push({
      view: 'control_room',
      controlRoomTool: currentTool,
      label: `Open ${currentToolLabel}`,
      title: `Continue in ${currentToolLabel}`,
      detail: 'Stay inside the current governance module and execute the next step quickly.',
      badge: currentToolLabel,
    });
  }
  candidates.push(...(TOPBAR_QUICK_ACTIONS[state.view] || []));
  if (!candidates.length) {
    candidates.push(
      { view: 'overview', label: 'Open Home', detail: 'Return to the executive posture scan.', badge: 'home' },
      { view: 'requests', label: 'Open Work Inbox', detail: 'Move directly into governed intake.', badge: 'intake' },
    );
  }
  return candidates;
}

function resolveTopbarQuickActions(snapshot) {
  const actions = [];
  const seen = new Set();
  for (const candidate of buildTopbarQuickActionCandidates(snapshot)) {
    const resolved = resolveNavigationTarget({
      view: candidate.view,
      controlRoomTool: candidate.controlRoomTool || '',
      title: candidate.title || '',
      detail: candidate.detail || '',
      actionLabel: candidate.label || candidate.actionLabel || '',
    });
    if (!resolved) continue;
    if (!isTopbarQuickActionAllowed(resolved)) continue;
    const identity = `${resolved.view}::${resolved.controlRoomTool || ''}`;
    if (seen.has(identity)) continue;
    seen.add(identity);
    const destinationLabel = resolved.view === 'control_room'
      ? (VIEW_TITLES[resolved.controlRoomTool || 'control_room'] || VIEW_TITLES.control_room)
      : (VIEW_TITLES[resolved.view] || titleCase(resolved.view));
    const label = candidate.label || resolved.actionLabel || `Open ${destinationLabel}`;
    actions.push({
      ...resolved,
      label,
      title: candidate.title || `Open ${destinationLabel}`,
      detail: candidate.detail || VIEW_DESCRIPTIONS[resolved.view] || `Open ${destinationLabel} to continue governed flow.`,
      actionLabel: candidate.actionLabel || label,
      badge: candidate.badge || destinationLabel,
    });
    if (actions.length >= 3) break;
  }
  return actions;
}

function renderTopbarActionStrip(snapshot) {
  if (!topbarActionStrip) return;
  const actions = resolveTopbarQuickActions(snapshot);
  if (!actions.length) {
    topbarActionStrip.hidden = true;
    topbarActionStrip.innerHTML = '';
    return;
  }
  const lead = actions[0];
  topbarActionStrip.hidden = false;
  topbarActionStrip.innerHTML = `
    <article class="topbar-action-strip-card">
      <div class="topbar-action-strip-copy">
        <span class="topbar-ribbon-label">Next actions</span>
        <strong>${escapeHtml(lead.title || 'Continue governed flow')}</strong>
        <span class="topbar-action-strip-note">${escapeHtml(lead.detail || 'Move to the next lane with one tap.')}</span>
      </div>
      <div class="topbar-action-strip-buttons">
        ${actions.map((action, index) => renderViewJumpButton({
          view: action.view,
          controlRoomTool: action.controlRoomTool || '',
          label: action.label,
          className: index === 0 ? 'action-button topbar-action-button-primary' : 'action-button action-button-muted topbar-action-button-secondary',
          title: action.title,
          detail: action.detail,
          actionLabel: action.actionLabel || action.label,
        })).join('')}
      </div>
    </article>
  `;
}

function normalizeWorkflowPrimary(primary) {
  if (!primary) return null;
  const resolved = resolveNavigationTarget(primary);
  if (resolved) return { ...primary, ...resolved };
  if (!isControlRoomTool(primary.view) && String(primary.view || '').trim() !== 'control_room') return primary;
  return {
    ...primary,
    view: state.view,
    controlRoomTool: '',
    title: 'Advanced governance detail requires Control Room.',
    detail: 'This session stays on the simple command surface. Keep work moving here and escalate to Admin, IT, or Founder if deeper runtime proof is required.',
    badge: 'governance escalation',
    actionLabel: `Stay in ${VIEW_TITLES[state.view] || titleCase(state.view)}`,
  };
}

function normalizeWorkflowRelated(related = []) {
  return (Array.isArray(related) ? related : [])
    .map((item) => {
      const resolved = resolveNavigationTarget(item);
      if (resolved) return { ...item, ...resolved };
      if (isControlRoomTool(item?.view) || String(item?.view || '').trim() === 'control_room') return null;
      return item;
    })
    .filter(Boolean);
}

function renderViewJumpButton({
  view = '',
  controlRoomTool = '',
  label = '',
  className = 'action-button',
  type = 'button',
  focusType = '',
  focusId = '',
  caseId = '',
  title = '',
  detail = '',
  actionLabel = '',
} = {}) {
  const resolved = resolveNavigationTarget({ view, controlRoomTool, title, detail, actionLabel: actionLabel || label });
  if (!resolved) return '';
  const buttonLabel = label || resolved.actionLabel || `Open ${VIEW_TITLES[resolved.view] || titleCase(resolved.view)}`;
  const attrs = buildViewJumpAttributes({
    view: resolved.view,
    controlRoomTool: resolved.controlRoomTool,
    focusType,
    focusId,
    caseId,
    title: resolved.title || title,
    detail: resolved.detail || detail,
    actionLabel: resolved.actionLabel || actionLabel || buttonLabel,
  });
  return `<button class="${escapeHtml(className)}" type="${escapeHtml(type)}" ${attrs}>${escapeHtml(buttonLabel)}</button>`;
}

function normalizeProtectedGovernanceView() {
  const requestedView = String(state.view || '').trim();
  if (!isControlRoomTool(requestedView)) return;
  state.controlRoomTool = requestedView;
  state.view = 'control_room';
}

function render() {
  if (!state.authRequired && state.snapshot) normalizeProtectedGovernanceView();
  viewTitle.textContent = VIEW_TITLES[state.view];
  viewDescription.textContent = VIEW_DESCRIPTIONS[state.view];
  sidebarViewTitle.textContent = VIEW_TITLES[state.view];
  sidebarViewDescription.textContent = VIEW_DESCRIPTIONS[state.view];
  topbarFocusLabel.textContent = VIEW_TITLES[state.view];
  document.body.dataset.view = state.view;
  const transitionFrom = state.lastRenderedView && state.lastRenderedView !== state.view ? state.lastRenderedView : '';
  if (transitionFrom) {
    state.laneTransition = { from: transitionFrom, to: state.view, startedAt: Date.now() };
  }
  const activeLaneTransition = getActiveLaneTransition();
  if (!activeLaneTransition && state.laneTransition && state.laneTransition.to === state.view) {
    state.laneTransition = null;
  }
  document.body.dataset.viewOrigin = activeLaneTransition ? activeLaneTransition.from : '';
  document.body.dataset.viewTransition = activeLaneTransition ? 'active' : 'idle';
  if (state.authRequired || !state.snapshot) {
    stopLiveTimestampTicker();
    sessionLabel.textContent = 'disconnected';
    environmentLabel.textContent = 'token required';
    setLiveTimestampLabel(state.lastError ? `Last error: ${state.lastError}` : 'Enter API token to access live runtime data.');
    sidebarDirectorMode.textContent = 'Awaiting session';
    sidebarDirectorCopy.textContent = 'Enter an API token to reconnect the Director and restore the governed command board.';
    sidebarDirectorBadgePrimary.textContent = 'offline';
    sidebarDirectorBadgeSecondary.textContent = 'token required';
    sidebarNextMoveTitle.textContent = 'Connect live runtime';
    sidebarNextMoveDetail.textContent = 'Authenticate first to reveal the next governed move, current lane pressure, and live director cues.';
    sidebarOperatorLabel.textContent = 'Disconnected';
    sidebarRuntimeLabel.textContent = 'Token required';
    sidebarPressureLabel.textContent = 'World state paused';
    sidebarPressureDetail.textContent = 'Live posture returns as soon as the private runtime reconnects.';
    sidebarDirectorCard.dataset.tone = 'idle';
    sidebarPressureCard.dataset.tone = 'idle';
    topbarRuntimeLabel.textContent = 'Awaiting session';
    renderTopbarActionStrip(null);
    root.innerHTML = renderAuthCard();
    updateNav();
    state.lastRenderedView = state.view;
    return;
  }

  const snapshot = state.snapshot;
  renderTopbarActionStrip(snapshot);
  const sidebarConsole = getSidebarDirectorConsole(snapshot);
  sessionLabel.textContent = state.session ? `${state.session.display_name} | ${state.session.role_name}` : 'connected';
  environmentLabel.textContent = `${snapshot.environment} environment`;
  startLiveTimestampTicker(snapshot.generated_at);
  sidebarDirectorMode.textContent = sidebarConsole.modeTitle;
  sidebarDirectorCopy.textContent = sidebarConsole.modeCopy;
  sidebarDirectorBadgePrimary.textContent = sidebarConsole.modePrimaryBadge;
  sidebarDirectorBadgeSecondary.textContent = sidebarConsole.modeSecondaryBadge;
  sidebarNextMoveTitle.textContent = sidebarConsole.nextMoveTitle;
  sidebarNextMoveDetail.textContent = sidebarConsole.nextMoveDetail;
  sidebarOperatorLabel.textContent = state.session ? state.session.display_name : 'Connected';
  sidebarRuntimeLabel.textContent = `${snapshot.environment} runtime`;
  sidebarPressureLabel.textContent = sidebarConsole.pressureLabel;
  sidebarPressureDetail.textContent = sidebarConsole.pressureDetail;
  sidebarDirectorCard.dataset.tone = sidebarConsole.modeTone;
  sidebarPressureCard.dataset.tone = sidebarConsole.pressureTone;
  topbarRuntimeLabel.textContent = state.session ? state.session.role_name : `${snapshot.environment} runtime`;
  syncCommandRoute();
  hydrateOrganizationSelector(snapshot);

  if (state.view === 'control_room' && !canAccessControlRoom()) {
    root.innerHTML = renderControlRoomDenied();
    updateNav();
    return;
  }
  if (state.view === 'setup' && !canAccessSetupAssistant()) {
    root.innerHTML = renderSetupAssistantDenied();
    updateNav();
    return;
  }
  const requiredPermission = VIEW_PERMISSIONS[state.view];
  if (requiredPermission && !can(requiredPermission)) {
    root.innerHTML = renderPermissionNotice(requiredPermission);
    updateNav();
    return;
  }

  const scopedSnapshot = getCaseScopedSnapshot(snapshot);
  let viewContent = '';
  if (state.view === 'overview') viewContent = renderCommandHome(snapshot);
  if (state.view === 'requests') viewContent = renderRequests(scopedSnapshot);
  if (state.view === 'cases') viewContent = renderCases(snapshot);
  if (state.view === 'directory') viewContent = renderDirectory(scopedSnapshot);
  if (state.view === 'documents') viewContent = renderDocuments(scopedSnapshot);
  if (state.view === 'actions') viewContent = renderActions(scopedSnapshot);
  if (state.view === 'setup') viewContent = renderSetupAssistant(snapshot);
  if (state.view === 'control_room') viewContent = renderControlRoom(snapshot);
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
  const compactCommandView = ['overview', 'control_room', 'setup'].includes(state.view);
  const focusedInbox = compactCommandView || !shouldRenderFocusedInbox(state.view) ? '' : renderFocusedWorkInbox(snapshot, state.view);
  const caseSpotlight = compactCommandView ? '' : renderCaseSpotlight(snapshot);
  const workLanguageGuide = compactCommandView || !shouldRenderWorkLanguageGuide(state.view) ? '' : renderWorkLanguageGuide(snapshot);
  const alertRail = compactCommandView ? '' : renderAlertRail(snapshot);
  const viewPrelude = compactCommandView ? '' : renderViewPrelude(snapshot);
  const tabletLaneRail = compactCommandView || !shouldRenderTabletLaneRail() ? '' : renderTabletLaneRail(snapshot);
  const workflowGuide = compactCommandView || !shouldRenderWorkflowGuide(state.view) ? '' : renderWorkflowGuide(snapshot);
  root.innerHTML = `${renderActionFeedback()}${renderActionContinuity()}${alertRail}${viewPrelude}${tabletLaneRail}${workflowGuide}${caseSpotlight}${workLanguageGuide}${focusedInbox}${viewContent}`;
  updateNav();
  state.lastRenderedView = state.view;
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
        ${renderViewJumpButton({ view: context.view || 'overview', controlRoomTool: context.controlRoomTool || '', label: context.actionLabel || `Open ${viewLabel}`, className: 'action-button action-button-muted', focusType: context.entityType, focusId: context.entityId, caseId: context.caseId, title: context.title || 'Latest governed result', detail: context.detail || focusNote, actionLabel: context.actionLabel || `Open ${viewLabel}` })}
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
          ${alert.view ? `<div class="inline-actions">${renderViewJumpButton({ view: alert.view, label: alert.actionLabel || 'Open view', className: 'action-button' })}</div>` : ''}
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
  const laneTransition = getActiveLaneTransition();
  const transitionFromLabel = laneTransition ? (VIEW_TITLES[laneTransition.from] || titleCase(laneTransition.from || 'overview')) : '';
  const currentViewLabel = VIEW_TITLES[state.view] || titleCase(state.view || 'overview');
  const continuationLabel = laneTransition
    ? (state.actionContext?.actionLabel || `Continue in ${currentViewLabel}`)
    : '';
  const entryTrace = laneTransition
    ? `<div class="trace-box view-entry-trace"><strong>Entered from ${escapeHtml(transitionFromLabel)}</strong><p class="muted">This lane now carries the next governed move, so the highlighted work stays easier to continue without re-scanning the whole board.</p><div class="transition-route"><span class="transition-node">${escapeHtml(transitionFromLabel)}</span><span class="transition-arrow">-&gt;</span><span class="transition-node transition-node-active">${escapeHtml(currentViewLabel)}</span></div><div class="transition-chip-row">${statusBadge(continuationLabel)}${statusBadge('continuity preserved')}</div></div>`
    : '';
  return `
    <section class="view-prelude card view-prelude-${escapeHtml(state.view)}${laneTransition ? ' view-prelude-entering' : ''}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(profile.eyebrow)}</div>
          <h3 class="card-title">${escapeHtml(profile.title)}</h3>
          <p class="card-subtitle">${escapeHtml(profile.narrative)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(profile.emphasis)}${laneTransition ? statusBadge(`from ${transitionFromLabel}`) : ''}${statusBadge(snapshot.environment || 'runtime')}</div>
      </div>
      ${entryTrace}
      <div class="view-prelude-grid">
        ${visibleCues.map((cue, index) => `
          <article class="view-prelude-card${cue.tone ? ` view-prelude-card-${escapeHtml(cue.tone)}` : ''}${laneTransition ? ' view-prelude-card-entering' : ''}"${laneTransition ? ` style="--lane-entry-index:${index}"` : ''}>
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
    ? (workflow.primary.view === state.view && !workflow.primary.controlRoomTool
      ? `<p class="permission-note workflow-current-note">${escapeHtml(workflow.primary.actionLabel || 'You are already in the right place.')}</p>`
      : `<div class="inline-actions">${renderViewJumpButton({ view: workflow.primary.view, controlRoomTool: workflow.primary.controlRoomTool || '', label: workflow.primary.actionLabel || `Open ${VIEW_TITLES[workflow.primary.view] || workflow.primary.view}`, className: 'action-button', title: workflow.primary.title, detail: workflow.primary.detail })}</div>`)
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
  if (!shouldRenderWorkLanguageGuide(state.view)) return '';
  const summary = snapshot.unified_work_inbox?.summary || {};
  return `
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Work language</div>
          <h3 class="card-title">Status language for fast decisions</h3>
          <p class="card-subtitle">Keep one simple vocabulary across queues so the next action is obvious at a glance.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(summary.primary_title || 'Governed work')}</div>
      </div>
      <div class="view-prelude-grid">
        <article class="view-prelude-card view-prelude-card-success">
          <span class="view-prelude-label">Ready</span>
          <strong>AI can continue</strong>
          <p class="muted">No extra human step is required right now.</p>
        </article>
        <article class="view-prelude-card view-prelude-card-warning">
          <span class="view-prelude-label">Human required</span>
          <strong>Decision needed</strong>
          <p class="muted">Runtime paused at a policy boundary and is waiting for review.</p>
        </article>
        <article class="view-prelude-card view-prelude-card-danger">
          <span class="view-prelude-label">Blocked</span>
          <strong>Fix before continue</strong>
          <p class="muted">A fail-closed condition is active and must be resolved first.</p>
        </article>
      </div>
      <div class="trace-box"><strong>Definition</strong><p class="muted">Every governed item must show owner, state, and next move immediately.</p></div>
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
      { label: 'Live demand', value: summary.requests_total || requests.length, note: 'How much governed work is currently entering or remaining visible in the intake lane.', tone: 'accent' },
      { label: 'Human boundaries', value: pendingOverrides, note: pendingOverrides ? 'These requests already need a real human decision before flow can continue.' : 'No request is currently waiting on a new human boundary.', tone: pendingOverrides ? 'warning' : 'success' },
      { label: 'Blocked by conflict', value: conflicts, note: conflicts ? 'Resolve contention here before asking the runtime to keep moving.' : 'The request lane is not currently stalled by lock or ordering pressure.', tone: conflicts ? 'danger' : 'success' },
    ];
  }
  if (state.view === 'cases') {
    const casesSummary = snapshot.cases?.summary || {};
    const leadCase = Array.isArray(snapshot.cases?.items) ? snapshot.cases.items[0] || null : null;
    const leadLane = VIEW_TITLES[leadCase?.primary_view || casesSummary.primary_view || 'requests'] || titleCase(leadCase?.primary_view || casesSummary.primary_view || 'requests');
    return [
      { label: 'Cases in motion', value: casesSummary.cases_total || 0, note: 'How many governed issues are currently stitched into one readable operating story.', tone: 'accent' },
      { label: 'Next lane', value: leadLane, note: leadCase ? 'The lead case already points at the lane that owns the next real move.' : 'Once work lands here, Cases will point you to the right governed lane automatically.', tone: leadCase ? 'accent' : 'default' },
      { label: 'Human boundaries', value: casesSummary.human_required_total || 0, note: 'Cases waiting for a real human decision rather than more clerical follow-through.', tone: (casesSummary.human_required_total || 0) ? 'warning' : 'success' },
    ];
  }
  if (state.view === 'directory') {
    return [
      { label: 'People', value: summary.directory_people_total || 0, note: 'Named runtime actors and organization members visible to the Director.', tone: 'accent' },
      { label: 'Assignments', value: summary.assignment_items_total || 0, note: 'Governed work items routed to real owners, seats, or fallback operators.', tone: (summary.assignment_human_required_total || 0) ? 'warning' : 'success' },
      { label: 'Search index', value: summary.search_index_total || 0, note: 'Searchable continuity across people, cases, documents, actions, evidence, and sessions.', tone: 'success' },
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
  if (state.view === 'actions') {
    const actionsSummary = snapshot.actions?.summary || {};
    return [
      { label: 'AI in flight', value: actionsSummary.running_total || 0, note: 'Governed actions actively moving right now inside case boundaries.', tone: (actionsSummary.running_total || 0) ? 'accent' : 'default' },
      { label: 'Human follow-through', value: actionsSummary.waiting_human_total || 0, note: (actionsSummary.waiting_human_total || 0) ? 'AI already reached the handoff line. A person now owns the next move.' : 'No AI action is currently paused behind a new human boundary.', tone: (actionsSummary.waiting_human_total || 0) ? 'warning' : 'success' },
      { label: 'Document side effects', value: actionsSummary.document_artifact_total || 0, note: 'Governed document artifacts created by the AI action runtime and kept inside the same story.', tone: (actionsSummary.document_artifact_total || 0) ? 'success' : 'default' },
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

  if (state.view === 'directory') {
    const directorySummary = snapshot.master_data?.summary || {};
    const assignmentSummary = snapshot.assignment_queue?.summary || {};
    const assignmentItems = Array.isArray(snapshot.assignment_queue?.items) ? snapshot.assignment_queue.items : [];
    const leadAssignment = assignmentItems[0] || null;
    if (leadAssignment) {
      primary = {
        view: leadAssignment.view || 'directory',
        eyebrow: 'Next governed move',
        title: 'Open the highest-pressure owned work item',
        detail: 'Directory turns ownership into action. Start from the most urgent assigned item so the runtime keeps moving through real people and teams.',
        badge: leadAssignment.status || leadAssignment.priority || 'attention_required',
        actionLabel: leadAssignment.action_label || `Open ${VIEW_TITLES[leadAssignment.view] || leadAssignment.view || 'Directory & Search'}`,
        details: [
          ['Owner', leadAssignment.owner_label || 'Unassigned'],
          ['Team', leadAssignment.team_label || 'Unassigned'],
          ['SLA', leadAssignment.sla_status || 'in_target'],
        ],
      };
      related.push(...['cases', leadAssignment.view || 'overview', 'requests', 'actions', 'documents']
        .filter((value, index, array) => value && array.indexOf(value) === index && value !== (leadAssignment.view || 'directory'))
        .slice(0, 3)
        .map((view) => ({
          view,
          eyebrow: 'Related view',
          note: 'Keep ownership, case continuity, and governed artifacts in one readable operating path.',
          actionLabel: `Open ${VIEW_TITLES[view] || view}`,
        })));
    } else {
      primary = {
        view: 'cases',
        eyebrow: 'Next governed move',
        title: 'Open Cases to seed real routed work',
        detail: 'Directory becomes most useful once governed work has owners, teams, and case-linked artifacts to route and search.',
        badge: 'seed work',
        actionLabel: 'Open Cases',
        details: [
          ['People', String(directorySummary.people_total || 0)],
          ['Teams', String(directorySummary.teams_total || 0)],
          ['Assignments', String(assignmentSummary.items_total || 0)],
        ],
      };
      related.push({ view: 'overview', eyebrow: 'Related view', note: 'Overview is still the fastest place to read overall posture before drilling into ownership.', actionLabel: 'Open Overview' });
    }
  }

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
        view: getInitialDashboardView(),
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
  } else if (state.view === 'actions') {
    const actionSummary = snapshot.actions?.summary || {};
    const currentCaseId = getActionContextCaseId();
    primary = currentCaseId
      ? {
          view: 'cases',
          eyebrow: 'Next governed move',
          title: 'Return to the canonical case after AI execution',
          detail: 'Use Cases to keep the action, document, human handoff, and proof trail attached to one governed issue.',
          badge: 'case continuity',
          actionLabel: 'Open Cases',
          details: [
            ['Case', currentCaseId],
            ['AI actions', String(actionSummary.actions_total || 0)],
            ['Waiting human', String(actionSummary.waiting_human_total || 0)],
          ],
        }
      : {
          view: 'cases',
          eyebrow: 'Next governed move',
          title: 'Open a case first, then let AI act inside it',
          detail: 'The AI action runtime is safest when launch, side effects, proof, and follow-up all stay attached to one canonical case.',
          badge: 'pick case',
          actionLabel: 'Open Cases',
        };
    addWorkflowLink(related, 'documents', 'Open Documents', 'Review governed document drafts or publish follow-through created by AI actions.');
    addWorkflowLink(related, 'human_ask', 'Open Human Ask', 'Follow human handoff records opened by the AI action runtime.');
    addWorkflowLink(related, 'audit', 'Open Audit Trail', 'Confirm authority basis, side effects, and proof after AI execution.');
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
        view: getInitialDashboardView(),
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
    primary: normalizeWorkflowPrimary(workflowGuide.primary),
    related: normalizeWorkflowRelated(workflowGuide.related).slice(0, 3),
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
  return ['requests', 'documents', 'actions', 'overrides', 'conflicts', 'audit', 'studio', 'human_ask'].includes(String(view || '').trim());
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
  if (state.view === 'documents') return Array.isArray(item.linked_document_ids) ? item.linked_document_ids.length : 0;
  if (state.view === 'actions') return Array.isArray(item.linked_action_ids) ? item.linked_action_ids.length : 0;
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
    documents: snapshot.documents
      ? {
          ...snapshot.documents,
          items: filterRowsByCase(snapshot.documents.items || [], caseId),
        }
      : snapshot.documents,
    actions: snapshot.actions
      ? {
          ...snapshot.actions,
          items: filterRowsByCase(snapshot.actions.items || [], caseId),
        }
      : snapshot.actions,
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
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view: 'actions',
          caseId: item.case_id,
          title: item.case_id ? `Case ${item.case_id} opened in AI Actions.` : 'Opened AI Actions.',
          detail: 'Launch or review governed AI execution inside the same canonical case.',
          actionLabel: 'Open AI Actions',
        })}>Open AI Actions</button>
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
  const controlRoomAllowed = canAccessControlRoom();
  const activeView = (isControlRoomTool(state.view) || GOVERNANCE_EMBEDDED_VIEWS.has(state.view)) ? 'control_room' : state.view;
  const guidedRawView = String(state.actionContext?.view || '').trim();
  const guidedView = (isControlRoomTool(guidedRawView) || GOVERNANCE_EMBEDDED_VIEWS.has(guidedRawView)) ? 'control_room' : guidedRawView;
  const guidedControlRoomTool = String(state.actionContext?.controlRoomTool || '').trim();
  if (governanceLauncher) {
    governanceLauncher.hidden = !controlRoomAllowed;
    const isGovernanceActive = activeView === 'control_room';
    const isGovernanceGuided = !isGovernanceActive && controlRoomAllowed && guidedView === 'control_room';
    governanceLauncher.classList.toggle('is-active', isGovernanceActive);
    governanceLauncher.classList.toggle('is-guided', isGovernanceGuided);
    governanceLauncher.dataset.navState = isGovernanceActive ? 'current' : isGovernanceGuided ? 'next' : 'idle';
    governanceLauncher.dataset.navLabel = isGovernanceActive ? 'current lane' : isGovernanceGuided ? 'next move' : '';
    governanceLauncher.setAttribute('aria-expanded', governanceSheet && !governanceSheet.hidden ? 'true' : 'false');
  }
  if (!controlRoomAllowed) {
    closeGovernanceSheet();
  }
  const activeControlRoomTool = String(state.controlRoomTool || getInitialControlRoomTool()).trim() || getInitialControlRoomTool();
  for (const item of navList.querySelectorAll('.nav-item')) {
    const itemView = item.dataset.view || '';
    const itemTool = String(item.dataset.controlRoomTool || '').trim();
    let isActive = itemView === activeView;
    let isGuided = !isActive && itemView === guidedView;
    if (itemView === 'control_room' && itemTool) {
      isActive = activeView === 'control_room' && itemTool === activeControlRoomTool;
      isGuided = !isActive && guidedView === 'control_room' && itemTool === (guidedControlRoomTool || getInitialControlRoomTool());
    } else if (itemView === 'control_room' && !itemTool) {
      isActive = activeView === 'control_room' && activeControlRoomTool === getInitialControlRoomTool();
      isGuided = !isActive && guidedView === 'control_room' && (guidedControlRoomTool || getInitialControlRoomTool()) === getInitialControlRoomTool();
    }
    item.classList.toggle('is-active', isActive);
    item.classList.toggle('is-guided', isGuided);
    item.dataset.navState = isActive ? 'current' : isGuided ? 'next' : 'idle';
    item.dataset.navLabel = isActive ? 'current lane' : isGuided ? 'next move' : '';
    item.setAttribute('aria-current', isActive ? 'page' : 'false');
  }
  if (governanceSheet) {
    for (const item of governanceSheet.querySelectorAll('.governance-sheet-item')) {
      const itemView = item.dataset.view || '';
      const itemTool = String(item.dataset.controlRoomTool || '').trim();
      let isActive = itemView === activeView;
      let isGuided = !isActive && itemView === guidedView;
      if (itemView === 'control_room' && itemTool) {
        isActive = activeView === 'control_room' && itemTool === activeControlRoomTool;
        isGuided = !isActive && guidedView === 'control_room' && itemTool === (guidedControlRoomTool || getInitialControlRoomTool());
      } else if (itemView === 'control_room' && !itemTool) {
        isActive = activeView === 'control_room' && activeControlRoomTool === getInitialControlRoomTool();
        isGuided = !isActive && guidedView === 'control_room' && (guidedControlRoomTool || getInitialControlRoomTool()) === getInitialControlRoomTool();
      }
      item.classList.toggle('is-active', isActive);
      item.classList.toggle('is-guided', isGuided);
      item.dataset.navState = isActive ? 'current' : isGuided ? 'next' : 'idle';
      item.setAttribute('aria-current', isActive ? 'page' : 'false');
    }
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
        <button class="action-button" type="button" data-view-jump="overview">Open Home</button>
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
            ['Governed documents', String(snapshot.summary.documents_total || 0)],
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
        ${metricCard('Documents', snapshot.summary.documents_total || 0, 'accent', 'Governed documents tracked with lifecycle, numbering, and case continuity.')}
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
  const primaryViewLabel = VIEW_TITLES[summary.primary_view] || titleCase(summary.primary_view || 'overview');
  const primaryActionLabel = summary.primary_action_label || `Review in ${primaryViewLabel}`;
  const primaryRouteNote = summary.primary_route_note || summary.primary_next_step || 'Open the lead governed lane and keep the next human boundary attached to the same work item.';
  const humanBoundaryLane = items.find((item) => item.disposition === 'human_required') || null;
  const blockedLane = items.find((item) => item.disposition === 'blocked') || null;
  const readyLane = items.find((item) => item.disposition === 'ready' || item.disposition === 'autonomy_ready') || items.find((item) => item.status === 'ready') || items[0] || null;
  return `
      <section class="card stack">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Operations Map</div>
            <h3 class="card-title">See where governed pressure is building before it becomes clerical chaos.</h3>
            <p class="card-subtitle">Use this as the live board for human boundaries, blocked paths, and recovery pressure across the runtime. Each lane should tell you what the next move is, not just what exists.</p>
          </div>
          <div class="hero-chip-row">${statusBadge(`${summary.open_total || 0} open`)}${statusBadge(`${summary.human_required_total || 0} human`)}</div>
        </div>
        ${keyValue([
          ['Open work', String(summary.open_total || 0)],
          ['Human required', String(summary.human_required_total || 0)],
          ['Blocked paths', String(summary.blocked_total || 0)],
          ['Ready lanes', String(summary.ready_total || 0)],
          ['Lead lane', primaryViewLabel],
        ])}
        <div class="trace-box"><strong>Lead move</strong><p class="muted">${escapeHtml(summary.primary_next_step || 'Open the lead governed lane and keep the next human boundary attached to the same work item.')}</p></div>
        <div class="trace-box compact-trace command-inbox-consequence-box"><strong>If the lead lane pauses</strong><p class="muted">${escapeHtml(summary.primary_consequence_note || 'Keep the same governed story visible while the next move is still live.')}</p></div>
        <div class="inline-actions">
          ${renderViewJumpButton({ view: summary.primary_view || 'overview', label: primaryActionLabel, className: 'action-button', focusType: summary.primary_focus_type || '', focusId: summary.primary_focus_id || '', caseId: summary.primary_case_id || '', title: `${summary.primary_title || primaryViewLabel} reopened from Work Inbox.`, detail: primaryRouteNote, actionLabel: primaryActionLabel })}
        </div>
        <div class="command-operation-shell">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Lane priorities</div>
              <h4 class="card-title">Which queue should move first</h4>
              <p class="card-subtitle">Keep the next human boundary, recovery path, and autonomy-ready lane visible without scanning every card in the inbox.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(summary.human_required_total ? 'human boundary live' : (summary.blocked_total ? 'recovery live' : 'lanes stable'))}</div>
          </div>
          <div class="command-operation-grid">
            ${renderWorkInboxMissionCard(humanBoundaryLane, {
              eyebrow: 'Human boundary now',
              fallbackTitle: 'No human boundary is waiting right now',
              fallbackDetail: 'When a real person must approve, veto, or confirm direction, that lane will surface here first.',
              fallbackView: summary.primary_view || 'overview',
              fallbackActionLabel: `Open ${primaryViewLabel}`,
              toneOverride: humanBoundaryLane ? 'warning' : 'success',
            })}
            ${renderWorkInboxMissionCard(blockedLane, {
              eyebrow: 'Recovery lane',
              fallbackTitle: 'No blocked lane is visible right now',
              fallbackDetail: 'If a governed path fails closed or collides with contention, this slot becomes the first recovery move.',
              fallbackView: 'conflicts',
              fallbackActionLabel: 'Open Conflicts',
              toneOverride: blockedLane ? 'danger' : 'success',
            })}
            ${renderWorkInboxMissionCard(readyLane, {
              eyebrow: 'Ready lane',
              fallbackTitle: 'No ready lane is visible yet',
              fallbackDetail: 'As soon as a lane can safely keep moving without a new human gate, it will surface here.',
              fallbackView: summary.primary_view || 'overview',
              fallbackActionLabel: `Open ${primaryViewLabel}`,
              toneOverride: readyLane ? (readyLane.disposition === 'human_required' ? 'warning' : readyLane.disposition === 'blocked' ? 'danger' : 'accent') : 'success',
            })}
          </div>
        </div>
        <div class="view-prelude-grid">
          ${items.map((item) => renderUnifiedWorkInboxItem(item)).join('')}
        </div>
      </section>
    `;
}


function buildLaneContinuityState(snapshot, currentView, leadItem = {}) {
  const summary = snapshot.unified_work_inbox?.summary || {};
  const currentViewLabel = VIEW_TITLES[currentView] || titleCase(currentView || 'overview');
  const caseId = getActionContextCaseId() || leadItem.case_id || summary.primary_case_id || '';
  const caseItem = getCaseById(snapshot, caseId) || (Array.isArray(snapshot?.cases?.items) ? snapshot.cases.items[0] || null : null);
  const continuity = caseItem?.continuity || {};
  const nextView = continuity.next_view || leadItem.view || summary.primary_view || currentView || 'overview';
  const nextViewLabel = VIEW_TITLES[nextView] || titleCase(nextView || 'overview');
  const nextFocus = caseItem
    ? resolveCasePrimaryFocus(caseItem, nextView)
    : { entityType: leadItem.focus_type || '', entityId: leadItem.focus_id || '' };
  const caseTitle = caseItem?.title || (caseId ? `Case ${caseId}` : (leadItem.title || 'No case anchor yet'));
  const questLabel = continuity.next_label || leadItem.action_label || `Open ${nextViewLabel}`;
  const questDetail = continuity.next_detail || leadItem.next_step || summary.primary_next_step || `Keep ${currentViewLabel} tied to the next governed move.`;
  const proofLabel = continuity.evidence_posture || ((caseItem?.workflow_proof_total || 0) > 0 ? 'proof attached' : 'proof starting');
  const pressureLabel = caseItem
    ? getCaseMissionBadge(caseItem)
    : (leadItem.disposition === 'human_required'
      ? 'human boundary'
      : leadItem.disposition === 'blocked'
        ? 'recovery'
        : leadItem.disposition === 'ready' || leadItem.disposition === 'autonomy_ready'
          ? 'move in flight'
          : 'continuity');
  const consequenceDetail = caseItem
    ? (String(caseItem.status || '').trim() === 'human_required'
      ? 'A real person owns the next safe move. Leaving the case here keeps the runtime at the approval boundary.'
      : String(caseItem.status || '').trim() === 'blocked'
        ? 'This story cannot safely advance until recovery clears the blocked path and reopens the case route.'
        : ((Number(caseItem.workflow_proof_total || 0) > 0 || Number(caseItem.evidence_export_total || 0) > 0)
          ? 'Proof and follow-through are already part of the mission. Carry them forward before opening fresh work.'
          : 'This lane can keep moving, but it should stay attached to the same governed story so context does not scatter.'))
    : (summary.primary_consequence_note || 'Keep the same governed story visible while the next move is still live.');
  return {
    currentViewLabel,
    caseId,
    caseItem,
    caseTitle,
    nextView,
    nextViewLabel,
    nextFocus,
    questLabel,
    questDetail,
    proofLabel,
    pressureLabel,
    consequenceDetail,
  };
}

function renderLaneContinuityBoard(continuityState) {
  if (!continuityState) return '';
  const hasCaseAnchor = Boolean(continuityState.caseId);
  return `
      <div class="lane-continuity-board">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Operation continuity</div>
            <h4 class="card-title">Keep the same governed story visible while moving through ${escapeHtml(continuityState.currentViewLabel)}</h4>
            <p class="card-subtitle">${escapeHtml(continuityState.questDetail)}</p>
          </div>
          <div class="hero-chip-row">${statusBadge(hasCaseAnchor ? `case ${continuityState.caseId}` : 'case anchor pending')}${statusBadge(continuityState.pressureLabel)}</div>
        </div>
        <div class="lane-continuity-grid">
          <article class="mini-card lane-continuity-card">
            <div class="eyebrow muted">Case anchor</div>
            <strong>${escapeHtml(continuityState.caseTitle)}</strong>
            <p class="muted">${escapeHtml(hasCaseAnchor ? `Use ${continuityState.caseId} as the canonical mission anchor while you move across lanes.` : 'Pick or generate a canonical case so the next move, proof, and follow-through stay attached.')}</p>
            ${renderViewJumpButton({
              view: 'cases',
              label: hasCaseAnchor ? 'Open anchor case' : 'Open Cases',
              className: 'action-button action-button-muted',
              focusType: hasCaseAnchor ? 'case' : '',
              focusId: continuityState.caseId || '',
              caseId: continuityState.caseId || '',
              title: hasCaseAnchor ? `Case ${continuityState.caseId} reopened in Cases.` : 'Cases reopened.',
              detail: 'Use Cases when you need the full linked story again before switching lanes.',
              actionLabel: hasCaseAnchor ? 'Open anchor case' : 'Open Cases',
            })}
          </article>
          <article class="mini-card lane-continuity-card lane-continuity-card-featured">
            <div class="eyebrow muted">Next governed move</div>
            <strong>${escapeHtml(continuityState.questLabel)}</strong>
            <p class="muted">${escapeHtml(continuityState.questDetail)}</p>
            ${renderViewJumpButton({
              view: continuityState.nextView,
              label: `Open ${continuityState.nextViewLabel}`,
              className: 'action-button',
              focusType: continuityState.nextFocus.entityType,
              focusId: continuityState.nextFocus.entityId,
              caseId: continuityState.caseId || '',
              title: continuityState.caseId ? `Case ${continuityState.caseId} reopened in ${continuityState.nextViewLabel}.` : `${continuityState.nextViewLabel} reopened.`,
              detail: continuityState.questDetail,
              actionLabel: `Open ${continuityState.nextViewLabel}`,
            })}
          </article>
          <article class="mini-card lane-continuity-card">
            <div class="eyebrow muted">If you pause here</div>
            <strong>${escapeHtml(continuityState.proofLabel)}</strong>
            <p class="muted">${escapeHtml(continuityState.consequenceDetail)}</p>
            <span class="permission-note">${escapeHtml(`Pressure: ${continuityState.pressureLabel} | Next lane: ${continuityState.nextViewLabel}`)}</span>
          </article>
        </div>
      </div>
    `;
}

function renderFocusedWorkInbox(snapshot, currentView) {
  const inbox = snapshot.unified_work_inbox || { summary: {}, items: [] };
  const summary = inbox.summary || {};
  const items = selectFocusedInboxItems(Array.isArray(inbox.items) ? inbox.items : [], currentView);
  if (!items.length) return '';
  const currentViewLabel = VIEW_TITLES[currentView] || titleCase(currentView || 'overview');
  const leadItem = items[0] || {};
  const continuityState = buildLaneContinuityState(snapshot, currentView, leadItem);
  return `
      <section class="card stack">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Next Governed Work</div>
            <h3 class="card-title">What should happen next from ${escapeHtml(currentViewLabel)}</h3>
            <p class="card-subtitle">Stay inside this workflow, but keep the next human boundary, blocked path, or case-continuity move visible without going back to Home.</p>
          </div>
          <div class="hero-chip-row">${statusBadge(currentViewLabel)}${statusBadge(`${summary.open_total || 0} open`)}${continuityState.caseId ? statusBadge(`case ${continuityState.caseId}`) : ''}</div>
        </div>
        <div class="trace-box"><strong>Lead move</strong><p class="muted">${escapeHtml(leadItem.next_step || summary.primary_next_step || 'Keep the next move visible from the same lane.')}</p></div>
        <div class="inline-actions">
          ${renderViewJumpButton({ view: leadItem.view || currentView || 'overview', label: leadItem.action_label || `Review in ${currentViewLabel}`, className: 'action-button', focusType: leadItem.focus_type || '', focusId: leadItem.focus_id || '', caseId: leadItem.case_id || '', title: `${leadItem.title || currentViewLabel} reopened from ${currentViewLabel}.`, detail: leadItem.route_note || leadItem.next_step || 'Continue from this governed lane without losing the case story.', actionLabel: leadItem.action_label || `Review in ${currentViewLabel}` })}
          ${continuityState.caseId ? renderViewJumpButton({ view: 'cases', label: 'Open anchor case', className: 'action-button action-button-muted', focusType: 'case', focusId: continuityState.caseId, caseId: continuityState.caseId, title: `Case ${continuityState.caseId} reopened in Cases.`, detail: 'Return to the canonical case when you need the full linked story, proof, and follow-through again.', actionLabel: 'Open anchor case' }) : ''}
        </div>
        ${renderLaneContinuityBoard(continuityState)}
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
      : item.tone === 'success'
        ? ' view-prelude-card-success'
        : ' view-prelude-card-accent';
  const pressureLabel = item.disposition === 'human_required'
    ? 'human boundary'
    : item.disposition === 'blocked'
      ? 'blocked path'
      : item.disposition === 'ready' || item.disposition === 'autonomy_ready'
        ? 'autonomy ready'
        : item.disposition || 'monitoring';
  const viewLabel = VIEW_TITLES[item.view] || titleCase(item.view || 'overview');
  const queueSummary = `${item.total || 0} open | oldest about ${item.oldest_age_hours || 0}h`;
  const operatorNote = item.operator_note || item.next_step || 'Review the next governed move.';
  const caseLabel = item.case_id ? `Case ${item.case_id}` : 'No case anchor';
  const routeNote = item.route_note || (item.case_id ? `Case ${item.case_id} stays attached to this lane.` : `Use ${viewLabel} to inspect the next governed route.`);
  const actionLabel = item.action_label || `Review in ${viewLabel}`;
  const focusType = item.focus_type || '';
  const focusId = item.focus_id || '';
  const focusClass = focusType && focusId && isFocusedEntity(focusType, focusId) ? ' focused-record' : '';
  const focusAttrs = focusType && focusId ? ` data-focus-key="${escapeHtml(buildFocusKey(focusType, focusId))}"` : '';
  return `
      <article class="view-prelude-card${toneClass}${focusClass}"${focusAttrs}>
        <span class="view-prelude-label">${escapeHtml(titleCase(item.lane_id || 'lane'))}</span>
        <strong>${escapeHtml(item.title || 'Governed work lane')}</strong>
        <div class="hero-chip-row">${statusBadge(pressureLabel)}${statusBadge(item.status || 'ready')}${statusBadge(viewLabel)}</div>
        <div class="transition-route command-inbox-route">
          <span class="transition-node transition-node-active">${escapeHtml(caseLabel)}</span>
          <span class="transition-arrow">&rarr;</span>
          <span class="transition-node">${escapeHtml(pressureLabel)}</span>
          <span class="transition-arrow">&rarr;</span>
          <span class="transition-node">${escapeHtml(viewLabel)}</span>
        </div>
        <p class="muted">${escapeHtml(item.next_step || 'Review the next governed move.')}</p>
        <p class="command-inbox-card-meta">${escapeHtml(queueSummary)}</p>
        <p class="muted small command-inbox-route-note">${escapeHtml(routeNote)}</p>
        ${compact ? '' : `<p class="muted small">${escapeHtml(operatorNote)}</p>`}
        ${refs.length ? `<div class="hero-chip-row">${refs.map((ref) => `<span class="pill">${escapeHtml(ref)}</span>`).join('')}</div>` : ''}
        <div class="inline-actions">
          <button class="action-button${compact ? ' action-button-muted' : ''}" type="button" ${buildViewJumpAttributes({
            view: item.view || 'overview',
            focusType,
            focusId,
            caseId: item.case_id || '',
            title: `${item.title || 'Governed work lane'} opened in ${viewLabel}.`,
            detail: item.next_step || operatorNote,
            actionLabel,
          })}>${escapeHtml(actionLabel)}</button>
        </div>
      </article>
    `;
}




function renderWorkInboxMissionCard(item, options = {}) {
  const fallbackView = options.fallbackView || 'overview';
  if (!item) {
    const fallbackViewLabel = VIEW_TITLES[fallbackView] || titleCase(fallbackView || 'overview');
    return `
      <article class="command-action-card tone-success command-workforce-card">
        <div class="eyebrow muted">${escapeHtml(options.eyebrow || 'Mission slot')}</div>
        <strong>${escapeHtml(options.fallbackTitle || 'No active mission')}</strong>
        <p class="muted">${escapeHtml(options.fallbackDetail || 'This slot will light up when a queue truly needs direction.')}</p>
        <div class="trace-box compact-trace"><strong>${escapeHtml(options.fallbackActionLabel || `Open ${fallbackViewLabel}`)}</strong><p class="muted">${escapeHtml(`Use ${fallbackViewLabel} when you want to inspect the broader queue instead of a single mission lane.`)}</p></div>
        ${renderViewJumpButton({ view: fallbackView, label: options.fallbackActionLabel || `Open ${fallbackViewLabel}`, className: 'action-button action-button-muted', title: `${fallbackViewLabel} reopened from Work Inbox.`, detail: options.fallbackDetail || `Use ${fallbackViewLabel} to inspect the next governed lane.`, actionLabel: options.fallbackActionLabel || `Open ${fallbackViewLabel}` })}
      </article>
    `;
  }
  const view = item.view || options.fallbackView || 'overview';
  const viewLabel = VIEW_TITLES[view] || titleCase(view || 'overview');
  const tone = options.toneOverride || (item.tone === 'danger' ? 'danger' : item.tone === 'warning' ? 'warning' : item.tone === 'success' ? 'success' : 'accent');
  const refs = Array.isArray(item.sample_references) ? item.sample_references.slice(0, 2).filter(Boolean).join(' | ') : '';
  const actionLabel = item.action_label || `Review in ${viewLabel}`;
  const routeNote = item.route_note || (item.case_id ? `Case ${item.case_id} stays attached to this lane.` : `Use ${viewLabel} to inspect the next governed route.`);
  const focusType = item.focus_type || '';
  const focusId = item.focus_id || '';
  const focusClass = focusType && focusId && isFocusedEntity(focusType, focusId) ? ' focused-record' : '';
  const focusAttrs = focusType && focusId ? ` data-focus-key="${escapeHtml(buildFocusKey(focusType, focusId))}"` : '';
  return `
    <article class="command-action-card tone-${escapeHtml(tone)} command-workforce-card${focusClass}"${focusAttrs}>
      <div class="eyebrow muted">${escapeHtml(options.eyebrow || 'Mission slot')}</div>
      <strong>${escapeHtml(item.title || 'Governed lane')}</strong>
      <div class="transition-route command-inbox-route">
        <span class="transition-node transition-node-active">${escapeHtml(item.case_id ? `Case ${item.case_id}` : 'Lead lane')}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(item.disposition || 'monitoring')}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(viewLabel)}</span>
      </div>
      <p class="muted">${escapeHtml(item.next_step || item.operator_note || 'Review the next governed move.')}</p>
      <p class="muted small command-inbox-route-note">${escapeHtml(routeNote)}</p>
      <div class="trace-box compact-trace command-inbox-consequence-box"><strong>${escapeHtml(item.disposition === 'human_required' ? 'If this waits here' : item.disposition === 'blocked' ? 'If this stays blocked' : 'If this keeps moving')}</strong><p class="muted">${escapeHtml(item.disposition === 'human_required' ? 'A real human still owns the safe next move for this case.' : item.disposition === 'blocked' ? 'Recovery must reopen the path before the wider operation can advance.' : 'Keep the same case visible so the next lane does not lose continuity.')}</p></div>
      <div class="trace-box compact-trace"><strong>${escapeHtml(actionLabel)}</strong><p class="muted">${escapeHtml(`${item.total || 0} open | oldest about ${item.oldest_age_hours || 0}h${refs ? ` | refs ${refs}` : ''}`)}</p></div>
      ${renderViewJumpButton({ view, label: actionLabel, className: 'action-button', focusType, focusId, caseId: item.case_id || '', title: `${item.title || 'Governed lane'} opened in ${viewLabel}.`, detail: item.next_step || item.operator_note || 'Continue from the lane that owns the next move.', actionLabel })}
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



function normalizedSearchQuery(value) {
  return String(value || '').trim().toLowerCase();
}

function directorySearchItems(snapshot) {
  const query = normalizedSearchQuery(state.directorySearchQuery);
  const caseId = getActionContextCaseId();
  const items = Array.isArray(snapshot.global_search?.items) ? snapshot.global_search.items : [];
  return items.filter((item) => {
    const matchesCase = !caseId || String(item.case_id || '') === caseId || !String(item.case_id || '');
    if (!query) return matchesCase;
    const haystack = normalizedSearchQuery(item.search_text || `${item.label || ''} ${item.detail || ''}`);
    return matchesCase && haystack.includes(query);
  });
}

function renderDirectoryEntityCard(item, kind = 'person') {
  if (!item) return '';
  const title = item.display_name || item.label || item.seat_id || item.team_id || item.person_id || 'Entity';
  const subtitle = kind === 'team'
    ? `${Array.isArray(item.member_ids) ? item.member_ids.length : 0} members`
    : kind === 'seat'
      ? (item.role_name || 'Governed seat')
      : (item.primary_role || item.permission_scope || 'Governed actor');
  const rows = [];
  if (kind === 'person') {
    rows.push(['Person Id', item.person_id || '-']);
    rows.push(['Primary role', item.primary_role || '-']);
    rows.push(['Teams', Array.isArray(item.team_labels) && item.team_labels.length ? item.team_labels.join(', ') : '-']);
  } else if (kind === 'seat') {
    rows.push(['Seat Id', item.seat_id || '-']);
    rows.push(['Occupant', item.occupant_label || item.occupant_id || '-']);
    rows.push(['Team', item.team_label || item.team_id || '-']);
  } else {
    rows.push(['Team Id', item.team_id || '-']);
    rows.push(['Domains', Array.isArray(item.domains) && item.domains.length ? item.domains.join(', ') : '-']);
    rows.push(['Members', String(Array.isArray(item.member_ids) ? item.member_ids.length : 0)]);
  }
  return `
    <article class="card stack directory-entity-card">
      <div class="row between start gap-sm wrap">
        <div class="stack gap-xs">
          <div class="eyebrow muted">${escapeHtml(titleCase(kind))}</div>
          <h3 class="card-title">${escapeHtml(title)}</h3>
          <p class="card-subtitle">${escapeHtml(subtitle)}</p>
        </div>
        ${statusBadge(item.status || 'active')}
      </div>
      ${keyValue(rows)}
    </article>
  `;
}

function renderDirectoryAssignmentCard(item) {
  if (!item) return '';
  const jumpAttrs = buildViewJumpAttributes({
    view: item.view || 'overview',
    focusType: item.focus_type || '',
    focusId: item.focus_id || '',
    caseId: item.case_id || '',
    title: item.title || 'Open governed assignment',
    detail: item.next_action || item.detail || 'Continue the assigned governed work.',
    actionLabel: item.action_label || `Open ${VIEW_TITLES[item.view] || titleCase(item.view || 'overview')}`,
  });
  return `
    <article class="card stack directory-assignment-card">
      <div class="row between start gap-sm wrap">
        <div class="stack gap-xs">
          <div class="eyebrow muted">${escapeHtml(titleCase(item.kind || 'assignment'))}</div>
          <h3 class="card-title">${escapeHtml(item.title || 'Assignment')}</h3>
          <p class="card-subtitle">${escapeHtml(item.detail || 'Governed work routed to a real owner.')}</p>
        </div>
        <div class="directory-meta">${statusBadge(item.status || 'monitoring')}${statusBadge(item.priority || 'normal')}</div>
      </div>
      ${keyValue([
        ['Owner', item.owner_label || 'Unassigned'],
        ['Team', item.team_label || 'Unassigned'],
        ['SLA', item.sla_status || 'in_target'],
        ['Age (hours)', formatMetricValue(item.age_hours || 0)],
      ])}
      ${item.case_id ? `<div class="case-reference-block">${renderCaseReferenceButton(item.case_id, item.status || '', { sourceView: 'directory', referenceId: item.reference_id || item.assignment_id || '', contextLabel: 'assignment' })}</div>` : ''}
      <div class="card-actions"><button class="action-button" type="button" ${jumpAttrs}>${escapeHtml(item.action_label || 'Open lane')}</button></div>
    </article>
  `;
}

function renderDirectorySearchResultCard(item) {
  if (!item) return '';
  const jumpAttrs = buildViewJumpAttributes({
    view: item.view || 'directory',
    focusType: item.focus_type || '',
    focusId: item.focus_id || item.id || '',
    caseId: item.case_id || '',
    title: item.label || 'Search result',
    detail: item.detail || 'Open the linked governed record.',
    actionLabel: `Open ${VIEW_TITLES[item.view] || titleCase(item.view || 'directory')}`,
  });
  return `
    <article class="card stack directory-search-result">
      <div class="row between start gap-sm wrap">
        <div class="stack gap-xs">
          <div class="eyebrow muted">${escapeHtml(item.kind_label || titleCase(item.kind || 'result'))}</div>
          <h3 class="card-title">${escapeHtml(item.label || 'Result')}</h3>
          <p class="card-subtitle">${escapeHtml(item.detail || 'Linked governed record')}</p>
        </div>
        ${item.status ? statusBadge(item.status) : ''}
      </div>
      ${keyValue([
        ['View', VIEW_TITLES[item.view] || titleCase(item.view || 'directory')],
        ['Owner', item.owner_label || item.owner_id || '-'],
        ['Team', item.team_label || item.team_id || '-'],
      ])}
      ${item.case_id ? `<div class="case-reference-block">${renderCaseReferenceButton(item.case_id, item.status || '', { sourceView: 'directory', referenceId: item.id || '', contextLabel: item.kind || 'search result' })}</div>` : ''}
      <div class="card-actions"><button class="action-button action-button-muted" type="button" ${jumpAttrs}>Open linked lane</button></div>
    </article>
  `;
}

function renderDirectory(snapshot) {
  const masterData = snapshot.master_data || { summary: {}, people: [], seats: [], teams: [] };
  const assignmentQueue = snapshot.assignment_queue || { summary: {}, items: [] };
  const globalSearch = snapshot.global_search || { summary: {}, items: [] };
  const summary = masterData.summary || {};
  const assignmentSummary = assignmentQueue.summary || {};
  const searchSummary = globalSearch.summary || {};
  const people = Array.isArray(masterData.people) ? masterData.people : [];
  const seats = Array.isArray(masterData.seats) ? masterData.seats : [];
  const teams = Array.isArray(masterData.teams) ? masterData.teams : [];
  const assignments = Array.isArray(assignmentQueue.items) ? assignmentQueue.items : [];
  const results = directorySearchItems(snapshot);
  const query = state.directorySearchQuery || '';
  const caseId = getActionContextCaseId();
  return `
    <section class="stack gap-lg">
      <section class="card stack">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Directory & Search</div>
            <h3 class="card-title">Ownership, assignment, and search continuity in one surface</h3>
            <p class="card-subtitle">Route governed work to real owners, inspect teams and seats, and search continuity across cases, documents, AI actions, and evidence without leaving the dashboard.</p>
          </div>
          <div class="hero-chip-row">${statusBadge(summary.search_ready ? 'search ready' : 'warming')}</div>
        </div>
        <div class="card-grid directory-metric-grid">
          ${metricCard('People', summary.people_total || 0, 'accent', 'Named runtime actors and organization members visible to the Director.')}
          ${metricCard('Seats', summary.seats_total || 0, 'default', 'Role seats that can own or inherit governed work.')}
          ${metricCard('Teams', summary.teams_total || 0, 'success', 'Organized team surfaces derived from roles, domains, and runtime activity.')}
          ${metricCard('Assignments', assignmentSummary.items_total || 0, (assignmentSummary.human_required_total || 0) ? 'warning' : 'accent', 'Governed work items currently routed to real owners or fallback operators.')}
        </div>
      </section>
      <section class="card stack directory-search-shell">
        <div class="row between end gap-sm wrap">
          <div class="stack gap-xs">
            <div class="eyebrow muted">Search continuity</div>
            <h3 class="card-title">Search people, teams, cases, documents, actions, and evidence</h3>
            <p class="card-subtitle">Use one search box to jump into the governed lane that already owns the work.</p>
          </div>
          <div class="directory-meta">${statusBadge(`${searchSummary.indexed_total || 0} indexed`)}</div>
        </div>
        <div class="directory-search-input-row">
          <input id="directory-search-input" class="text-input" type="search" value="${escapeHtml(query)}" placeholder="Search by name, team, role, case, document, action, evidence, or session" />
          <button type="button" class="action-button action-button-muted" data-directory-search-clear>Clear</button>
        </div>
        <div class="row between start gap-sm wrap muted small">
          <span>${caseId ? `Scoped to case ${escapeHtml(caseId)} when a case context is active.` : 'Showing all searchable governed entities across the runtime.'}</span>
          <span>${escapeHtml(`${results.length} results`)}</span>
        </div>
      </section>
      <section class="stack gap-md">
        <div class="row between end gap-sm wrap">
          <div>
            <div class="eyebrow muted">Assignment queue</div>
            <h3 class="card-title">Real owned work, ordered by urgency</h3>
          </div>
          <div class="directory-meta">${statusBadge(assignmentSummary.human_required_total ? 'human required' : assignmentSummary.items_total ? 'active queue' : 'clear')}</div>
        </div>
        <div class="directory-assignment-grid">${assignments.length ? assignments.slice(0, 6).map(renderDirectoryAssignmentCard).join('') : emptyState('No owned governed work is waiting right now.')}</div>
      </section>
      <section class="split-grid directory-entity-section">
        <div class="stack gap-md">
          <div>
            <div class="eyebrow muted">People</div>
            <h3 class="card-title">Who the runtime can route to</h3>
          </div>
          <div class="directory-entity-grid">${people.length ? people.slice(0, 6).map((item) => renderDirectoryEntityCard(item, 'person')).join('') : emptyState('No people are visible yet in the master data baseline.')}</div>
        </div>
        <div class="stack gap-md">
          <div>
            <div class="eyebrow muted">Teams & seats</div>
            <h3 class="card-title">How ownership is grouped and seated</h3>
          </div>
          <div class="directory-entity-grid">${teams.slice(0, 3).map((item) => renderDirectoryEntityCard(item, 'team')).join('')}${seats.slice(0, 3).map((item) => renderDirectoryEntityCard(item, 'seat')).join('') || (!teams.length && !seats.length ? emptyState('No teams or seats are visible yet in the master data baseline.') : '')}</div>
        </div>
      </section>
      <section class="stack gap-md">
        <div class="row between end gap-sm wrap">
          <div>
            <div class="eyebrow muted">Search results</div>
            <h3 class="card-title">Search once, continue in the right governed lane</h3>
          </div>
          <div class="directory-meta">${statusBadge(results.length ? 'results ready' : query ? 'no matches' : 'browse')}</div>
        </div>
        <div class="directory-result-grid">${results.length ? results.slice(0, 12).map(renderDirectorySearchResultCard).join('') : emptyState(query ? 'No searchable governed records matched that query.' : 'Type a search term to browse people, cases, documents, actions, evidence, and sessions from one place.')}</div>
      </section>
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
  const leadCaseView = leadCase?.primary_view || summary.primary_view || 'requests';
  const leadCaseViewLabel = VIEW_TITLES[leadCaseView] || titleCase(leadCaseView || 'requests');
  const leadCaseFocus = leadCase ? resolveCasePrimaryFocus(leadCase, leadCaseView) : { entityType: '', entityId: '' };
  const humanBoundaryCase = items.find((item) => String(item.status || '').trim() === 'human_required') || null;
  const blockedCase = items.find((item) => String(item.status || '').trim() === 'blocked') || null;
  const attentionCase = items.find((item) => String(item.status || '').trim() === 'attention_required') || null;
  const proofCase = items.find((item) => Number(item.workflow_proof_total || 0) > 0 || Number(item.evidence_export_total || 0) > 0) || null;
  const followThroughCase = blockedCase || attentionCase || proofCase || items[1] || leadCase;
  const missionPressure = summary.human_required_total
    ? 'Human boundary decisions are shaping the board right now.'
    : summary.blocked_total
      ? 'Recovery pressure is shaping the board right now.'
      : summary.attention_total
        ? 'Operator follow-through is shaping the board right now.'
        : 'The board is stable; keep the lead case moving and its proof attached.';
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Canonical Case Backbone</div>
            <h2 class="hero-title">Follow one governed issue across every lane without rebuilding the story by hand.</h2>
            <p class="hero-subtitle">Cases keep the working lane, human boundary, Human Ask record, AI actions, documents, and audit history tied to the same operating story so the next move is easier to see.</p>
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
            ['Primary lane', leadCaseViewLabel],
          ])}
          <div class="hero-note">
            <strong>Operator standard</strong>
            <p>Stay with the case until the issue is either resolved, handed to the correct human boundary, or fully documented with enough proof for later review. The case should feel like the mission, not just another record.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Lead case in view</div>
          <h3 class="card-title">${escapeHtml(leadCase ? (leadCase.title || leadCase.case_id || 'Lead governed case') : 'Open Requests to seed the first linked case')}</h3>
          <p class="card-subtitle">${escapeHtml(leadCase ? (leadCase.continuity?.next_detail || 'This case already points at the lane that owns the next governed move.') : 'Cases becomes powerful once a governed request, Human Ask record, or document flow has enough continuity to stitch into one operating story.')}</p>
        </div>
        ${keyValue([
          ['Latest case', latestCaseLabel],
          ['Next lane', leadCaseViewLabel],
          ['Proof stance', leadCase?.continuity?.evidence_posture || 'proof starting'],
          ['Timeline', String(leadCase?.timeline_total || 0)],
          ['Documents linked', String((leadCase?.linked_document_ids || []).length)],
        ])}
        <div class="inline-actions">
          ${leadCase ? renderViewJumpButton({ view: leadCaseView, label: `Open ${leadCaseViewLabel}`, className: 'action-button', focusType: leadCaseFocus.entityType, focusId: leadCaseFocus.entityId, caseId: leadCase.case_id, title: `Case ${leadCase.case_id} reopened in ${leadCaseViewLabel}.`, detail: leadCase.continuity?.next_detail || 'Continue the same governed issue from its lead lane.', actionLabel: `Open ${leadCaseViewLabel}` }) : renderViewJumpButton({ view: 'requests', label: 'Open Requests', className: 'action-button', title: 'Requests reopened from Cases.', detail: 'Start the first governed request so Cases has a linked issue to track.', actionLabel: 'Open Requests' })}
          ${renderViewJumpButton({ view: 'actions', label: 'Open AI Actions', className: 'action-button action-button-muted', caseId: leadCase?.case_id || '', title: leadCase?.case_id ? `Case ${leadCase.case_id} reopened in AI Actions.` : 'AI Actions reopened from Cases.', detail: 'Use AI Actions when the case is ready for governed execution inside the same story.', actionLabel: 'Open AI Actions' })}
        </div>
      </article>
    </section>
    <section class="case-mission-board">
      <div class="case-mission-board-head">
        <div>
          <div class="eyebrow muted">Mission board</div>
          <h3 class="card-title">Which governed stories need direction now</h3>
          <p class="card-subtitle">${escapeHtml(missionPressure)}</p>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(summary.human_required_total ? 'human boundary live' : (summary.blocked_total ? 'recovery in flight' : 'stable board'))}
        </div>
      </div>
      <div class="case-mission-priority-grid">
        ${renderCaseMissionPriorityCard(leadCase, {
          eyebrow: 'Lead mission',
          fallbackTitle: 'No lead case is visible yet',
          fallbackDetail: 'Open Requests and let the runtime stitch the first governed issue into a canonical case.',
          fallbackView: 'requests',
          fallbackActionLabel: 'Open Requests',
          titleOverride: leadCase ? (leadCase.title || leadCase.case_id || 'Lead governed case') : '',
          detailOverride: leadCase?.continuity?.next_detail || 'Keep the primary case moving so the rest of the board stays readable.',
        })}
        ${renderCaseMissionPriorityCard(humanBoundaryCase, {
          eyebrow: 'Human boundary now',
          fallbackTitle: 'No human boundary is waiting right now',
          fallbackDetail: 'When AI or workflow pressure crosses a real approval line, the case will surface here first.',
          fallbackView: leadCaseView,
          fallbackActionLabel: `Open ${leadCaseViewLabel}`,
          detailOverride: humanBoundaryCase?.continuity?.next_detail || 'A real human decision is now the only safe next move for this case.',
          badgeOverride: 'human boundary',
          toneOverride: humanBoundaryCase ? 'warning' : 'success',
        })}
        ${renderCaseMissionPriorityCard(followThroughCase, {
          eyebrow: blockedCase ? 'Recovery mission' : 'Follow-through queue',
          fallbackTitle: 'No stalled or proof-led mission is visible',
          fallbackDetail: 'Use this slot to keep recovery, proof follow-through, or operator pressure visible without reopening every case card.',
          fallbackView: 'audit',
          fallbackActionLabel: 'Open Audit',
          detailOverride: followThroughCase?.continuity?.next_detail || (blockedCase ? 'Recover the blocked path and reopen safe governed flow.' : 'Keep proof, audit, and operator follow-through attached to the same case story.'),
          badgeOverride: blockedCase ? 'recovery' : undefined,
          toneOverride: blockedCase ? 'danger' : undefined,
        })}
      </div>
    </section>
    <section class="split-grid">
      <article class="card stack case-lane-doctrine-card">
        <div><div class="eyebrow muted">Case mission</div><h3 class="card-title">What this lane should make easy</h3><p class="card-subtitle">Cases should answer what the issue is, what changed last, and which lane owns the next move.</p></div>
        ${keyValue([
          ['Trace model', 'Request to override to record to audit'],
          ['Primary job', 'Follow the issue, not just the individual event'],
          ['Proof stance', 'Keep the human and AI narrative attached'],
          ['Escalation discipline', 'Use the case to keep boundary changes visible'],
        ])}
      </article>
      <article class="card stack case-lane-doctrine-card">
        <div><div class="eyebrow muted">Use the right follow-through</div><h3 class="card-title">Keep the story moving from one lane to the next</h3><p class="card-subtitle">The case is the safest place to pivot between requests, human decisions, AI work, documents, and proof without losing continuity.</p></div>
        <div class="inline-actions">
          ${renderViewJumpButton({ view: leadCaseView, label: `Open ${leadCaseViewLabel}`, className: 'action-button', focusType: leadCaseFocus.entityType, focusId: leadCaseFocus.entityId, caseId: leadCase?.case_id || '', title: leadCase?.case_id ? `Case ${leadCase.case_id} reopened in ${leadCaseViewLabel}.` : `${leadCaseViewLabel} reopened from Cases.`, detail: 'Continue the lead lane that currently owns the issue.', actionLabel: `Open ${leadCaseViewLabel}` })}
          ${renderViewJumpButton({ view: 'audit', label: 'Open Audit', className: 'action-button action-button-muted', caseId: leadCase?.case_id || '', title: leadCase?.case_id ? `Case ${leadCase.case_id} reopened in Audit.` : 'Audit reopened from Cases.', detail: 'Use Audit when the next question is about proof, rationale, or what happened before.', actionLabel: 'Open Audit' })}
        </div>
      </article>
    </section>
    <section class="case-grid">
      ${items.length ? items.map((item) => renderCaseCard(item)).join('') : renderCaseEmptyState()}
    </section>
  `;
}

function getCaseMissionTone(item = {}) {
  const status = String(item?.status || '').trim();
  if (status === 'blocked') return 'danger';
  if (status === 'human_required' || status === 'attention_required') return 'warning';
  if (status === 'resolved' || status === 'completed') return 'success';
  return 'accent';
}

function getCaseMissionBadge(item = {}) {
  const status = String(item?.status || '').trim();
  if (status === 'human_required') return 'human boundary';
  if (status === 'blocked') return 'recovery';
  if (status === 'attention_required') return 'follow-through';
  if (status === 'active') return 'in motion';
  if (status) return status.replace(/_/g, ' ');
  return 'stable';
}

function renderCaseMissionPriorityCard(item, options = {}) {
  const fallbackView = options.fallbackView || 'requests';
  if (!item) {
    const fallbackViewLabel = VIEW_TITLES[fallbackView] || titleCase(fallbackView || 'requests');
    return `
      <article class="card stack case-mission-priority tone-success">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">${escapeHtml(options.eyebrow || 'Mission slot')}</div>
            <h3 class="card-title">${escapeHtml(options.fallbackTitle || 'No mission is active here')}</h3>
            <p class="card-subtitle">${escapeHtml(options.fallbackDetail || 'This slot will surface the next governed case when pressure appears.')}</p>
          </div>
          <div class="hero-chip-row">${statusBadge('stable')}</div>
        </div>
        <div class="trace-box compact-trace">
          <strong>${escapeHtml(options.fallbackActionLabel || `Open ${fallbackViewLabel}`)}</strong>
          <p>${escapeHtml(`Use ${fallbackViewLabel} to seed or review the next governed story.`)}</p>
        </div>
        ${renderViewJumpButton({ view: fallbackView, label: options.fallbackActionLabel || `Open ${fallbackViewLabel}`, className: 'action-button action-button-muted', title: `${fallbackViewLabel} reopened from Cases.`, detail: options.fallbackDetail || `Use ${fallbackViewLabel} to surface the next governed issue.`, actionLabel: options.fallbackActionLabel || `Open ${fallbackViewLabel}` })}
      </article>
    `;
  }
  const continuity = item.continuity || {};
  const nextView = continuity.next_view || item.primary_view || fallbackView;
  const nextViewLabel = VIEW_TITLES[nextView] || titleCase(nextView || 'requests');
  const focus = resolveCasePrimaryFocus(item, nextView);
  const linkedWorkTotal = [
    (item.linked_request_ids || []).length,
    (item.linked_override_ids || []).length,
    (item.linked_session_ids || []).length,
    (item.linked_action_ids || []).length,
    (item.linked_document_ids || []).length,
    (item.linked_workflow_ids || []).length,
    (item.linked_studio_request_ids || []).length,
  ].reduce((total, value) => total + Number(value || 0), 0);
  const tone = options.toneOverride || getCaseMissionTone(item);
  const badge = options.badgeOverride || getCaseMissionBadge(item);
  const questLabel = continuity.next_label || `Open ${nextViewLabel}`;
  const questPhaseLabel = continuity.quest_phase_label || 'Live motion';
  const questPhaseDetail = continuity.quest_phase_detail || 'Keep the governed story moving from the owning lane.';
  return `
    <article class="card stack case-mission-priority tone-${escapeHtml(tone)}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(options.eyebrow || 'Mission slot')}</div>
          <h3 class="card-title">${escapeHtml(options.titleOverride || item.title || item.case_id || 'Governed case')}</h3>
          <p class="card-subtitle">${escapeHtml(options.detailOverride || continuity.next_detail || 'Continue the governed issue from its owning lane.')}</p>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(badge)}
          ${statusBadge(nextViewLabel)}
        </div>
      </div>
      <div class="trace-box compact-trace">
        <strong>${escapeHtml(questLabel)}</strong>
        <p>${escapeHtml(`${questPhaseLabel} | ${item.case_id || 'Case'} | ${continuity.evidence_posture || 'proof starting'} | ${linkedWorkTotal} linked signals`)}</p>
      </div>
      <p class="muted small command-momentum-note">${escapeHtml(questPhaseDetail)}</p>
      ${keyValue([
        ['Updated', shortTime(item.updated_at)],
        ['Quest phase', questPhaseLabel],
        ['Timeline', String(item.timeline_total || 0)],
        ['Work linked', String(linkedWorkTotal)],
      ])}
      ${renderViewJumpButton({ view: nextView, label: `Open ${nextViewLabel}`, className: 'action-button', focusType: focus.entityType, focusId: focus.entityId, caseId: item.case_id, title: item.case_id ? `Case ${item.case_id} reopened in ${nextViewLabel}.` : `Opened ${nextViewLabel}.`, detail: continuity.next_detail || 'Continue the governed issue from its next owning lane.', actionLabel: `Open ${nextViewLabel}` })}
    </article>
  `;
}

function renderCaseQuestStep(item) {
  const continuity = item.continuity || {};
  const questPhaseLabel = continuity.quest_phase_label || item.quest_phase_label || 'Live motion';
  const questPhaseDetail = continuity.quest_phase_detail || item.quest_phase_detail || 'Keep the governed story moving from its owning lane.';
  const proofLabel = continuity.evidence_posture || 'proof starting';
  return `
    <div class="trace-box case-quest-step">
      <div class="case-quest-step-head">
        <div>
          <div class="eyebrow muted">Quest step</div>
          <strong>${escapeHtml(questPhaseLabel)}</strong>
        </div>
        <div class="hero-chip-row">${statusBadge(proofLabel)}</div>
      </div>
      <p class="muted">${escapeHtml(questPhaseDetail)}</p>
    </div>
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
    case 'document':
      return { entityType: 'document', entityId: firstId };
    case 'action':
      return { entityType: 'action', entityId: firstId };
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
              caseId: item.case_id,
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

function renderCaseProgressRoute(item) {
  const continuity = item.continuity || {};
  const primaryView = item.primary_view || 'requests';
  const primaryViewLabel = VIEW_TITLES[primaryView] || titleCase(primaryView || 'requests');
  const nextMoveLabel = continuity.next_label || 'Human boundary';
  const proofLabel = continuity.evidence_posture || 'Proof posture';
  return `
    <div class="case-progress-panel">
      <div class="eyebrow muted">Case route</div>
      <div class="transition-route">
        <span class="transition-node transition-node-active">${escapeHtml(primaryViewLabel)}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(nextMoveLabel)}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(proofLabel)}</span>
      </div>
      <p class="muted small command-momentum-note">${escapeHtml(continuity.next_detail || 'This case keeps the live route visible so the next governed move can be made without reopening the whole story.')}</p>
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
          caseId: item.case_id,
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
    ...(item.linked_action_ids || []).slice(0, 2),
    ...(item.linked_workflow_ids || []).slice(0, 2),
    ...(item.linked_studio_request_ids || []).slice(0, 2),
  ].filter(Boolean);
  const primaryView = item.primary_view || 'requests';
  const continuity = item.continuity || {};
  const primaryFocus = resolveCasePrimaryFocus(item, primaryView);
  const primaryViewLabel = VIEW_TITLES[primaryView] || titleCase(primaryView);
  const secondaryView = primaryView !== 'audit' ? 'audit' : 'requests';
  const secondaryViewLabel = VIEW_TITLES[secondaryView] || titleCase(secondaryView);
  const tone = getCaseMissionTone(item);
  const pressureBadge = getCaseMissionBadge(item);
  const questPhaseLabel = continuity.quest_phase_label || item.quest_phase_label || pressureBadge;
  return `
    <article class="card stack case-card case-card-tone-${escapeHtml(tone)}${isFocusedEntity('case', item.case_id) ? ' focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey('case', item.case_id))}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(item.case_id || 'CASE')}</div>
          <h3 class="card-title">${escapeHtml(item.title || item.case_id || 'Governed case')}</h3>
          <p class="card-subtitle">${escapeHtml(`Updated ${shortTime(item.updated_at)} | Opened ${shortTime(item.opened_at)} | ${questPhaseLabel} | ${continuity.next_label || `Continue in ${primaryViewLabel}`}`)}</p>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(item.status || 'monitoring')}
          ${statusBadge(questPhaseLabel)}
          ${statusBadge(primaryViewLabel)}
        </div>
      </div>
      ${keyValue([
        ['Requests', String((item.linked_request_ids || []).length)],
        ['Overrides', String((item.linked_override_ids || []).length)],
        ['Human Ask', String((item.linked_session_ids || []).length)],
        ['AI actions', String((item.linked_action_ids || []).length)],
        ['Documents', String((item.linked_document_ids || []).length)],
        ['Workflow refs', String((item.linked_workflow_ids || []).length)],
        ['Audit events', String(item.audit_event_total || 0)],
        ['Timeline', String(item.timeline_total || 0)],
      ])}
      ${renderCaseQuestStep(item)}
      ${renderCaseProgressRoute(item)}
      ${renderCaseContinuity(item)}
      ${renderCaseWorkItems(item)}
      ${linkedRefs.length ? `<div class="case-reference-list">${linkedRefs.map((value) => `<span class="pill pill-muted">${escapeHtml(value)}</span>`).join('')}</div>` : ''}
      <div class="case-timeline-shell">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Mission log</div>
            <h4 class="card-title">What changed across this governed story</h4>
          </div>
          <div class="hero-chip-row">${statusBadge(`${timeline.length} events`)}</div>
        </div>
        <div class="case-timeline">
          ${timeline.length ? timeline.map((entry) => renderCaseTimelineEntry(entry, item.case_id)).join('') : `<div class="empty-state">No case events are available yet.</div>`}
        </div>
      </div>
      <div class="inline-actions">
        <button class="action-button" type="button" ${buildViewJumpAttributes({
          view: primaryView,
          focusType: primaryFocus.entityType,
          focusId: primaryFocus.entityId,
          caseId: item.case_id,
          title: item.case_id ? `Case ${item.case_id} opened in ${primaryViewLabel}.` : `Opened ${primaryViewLabel}.`,
          detail: continuity.next_detail || 'The linked work item stays highlighted in its operating lane so you can continue from the same governed issue.',
          actionLabel: `Open ${primaryViewLabel}`,
        })}>${escapeHtml(`Open ${primaryViewLabel}`)}</button>
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view: secondaryView,
          caseId: item.case_id,
          title: item.case_id ? `Case ${item.case_id} opened in ${secondaryViewLabel}.` : `Opened ${secondaryViewLabel}.`,
          detail: secondaryView === 'audit' ? 'Use Audit to verify the evidence trail attached to this case.' : 'Use Requests to reopen the linked runtime intake lane.',
          actionLabel: `Open ${secondaryViewLabel}`,
        })}>${escapeHtml(`Open ${secondaryViewLabel}`)}</button>
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view: 'actions',
          caseId: item.case_id,
          title: item.case_id ? `Case ${item.case_id} opened in AI Actions.` : 'Opened AI Actions.',
          detail: 'Use the AI action runtime to summarize, draft, or hand off work inside this case.',
          actionLabel: 'Open AI Actions',
        })}>Open AI Actions</button>
      </div>
    </article>
  `;
}

function resolveCaseTimelineFocus(entry = {}) {
  const eventType = String(entry?.event_type || '').trim();
  const reference = String(entry?.reference || '').trim();
  if (!reference) return { entityType: 'case', entityId: '' };
  if (eventType === 'request') return { entityType: 'request', entityId: reference };
  if (eventType === 'override') return { entityType: 'override', entityId: reference };
  if (eventType === 'human_ask') return { entityType: 'human_ask_session', entityId: reference };
  if (eventType === 'studio') return { entityType: 'studio_request', entityId: reference };
  if (eventType === 'document') return { entityType: 'document', entityId: reference };
  if (eventType === 'action') return { entityType: 'action', entityId: reference };
  if (eventType === 'audit') return { entityType: 'request', entityId: reference };
  return { entityType: 'case', entityId: '' };
}

function renderCaseTimelineEntry(entry, caseId = '') {
  const view = entry.view || 'overview';
  const viewLabel = VIEW_TITLES[view] || titleCase(view || 'overview');
  const focus = resolveCaseTimelineFocus(entry);
  const tone = getCaseMissionTone({ status: entry.status });
  const actionVerb = entry.status === 'human_required'
    ? 'Review in'
    : entry.status === 'blocked'
      ? 'Recover in'
      : 'Continue in';
  return `
    <article class="mini-card stack case-timeline-item tone-${escapeHtml(tone)}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(shortTime(entry.timestamp))}</div>
          <strong>${escapeHtml(entry.title || 'Case event')}</strong>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(entry.status || 'recorded')}
          ${statusBadge(viewLabel)}
        </div>
      </div>
      <div class="transition-route case-timeline-route">
        <span class="transition-node transition-node-active">${escapeHtml(titleCase(String(entry.status || 'recorded').replace(/_/g, ' ')))}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(viewLabel)}</span>
      </div>
      <p class="muted">${escapeHtml(entry.detail || 'Governed case event recorded.')}</p>
      <span class="permission-note">Ref ${escapeHtml(entry.reference || '-')} | Next lane ${escapeHtml(viewLabel)}</span>
      <div class="inline-actions">
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view,
          focusType: focus.entityType,
          focusId: focus.entityId,
          caseId,
          title: caseId ? `Case ${caseId} opened in ${viewLabel}.` : `Opened ${viewLabel}.`,
          detail: `Continue this case from the ${viewLabel} lane using the linked event reference.`,
          actionLabel: `${actionVerb} ${viewLabel}`,
        })}>${escapeHtml(`${actionVerb} ${viewLabel}`)}</button>
      </div>
    </article>
  `;
}

function renderCaseEmptyState() {
  return `
    <article class="card stack case-card case-card-empty">
      <div>
        <div class="eyebrow muted">Case lane empty</div>
        <h3 class="card-title">No linked governed case is visible yet</h3>
        <p class="card-subtitle">Start from Requests, Human Ask, Role Private Studio, or Documents. As soon as the runtime captures related work, this lane will stitch the issue into one readable case.</p>
      </div>
      <div class="inline-actions">
        <button class="action-button" type="button" data-view-jump="requests">Open Requests</button>
        <button class="action-button action-button-muted" type="button" data-view-jump="documents">Open Documents</button>
      </div>
    </article>
  `;
}


function getScopedActionCase(snapshot = state.snapshot) {
  const caseId = getActionContextCaseId();
  return caseId ? getCaseById(snapshot, caseId) : null;
}

function getActionById(snapshot, actionId = '') {
  const normalizedActionId = String(actionId || '').trim();
  if (!normalizedActionId) return null;
  const items = Array.isArray(snapshot?.actions?.items) ? snapshot.actions.items : [];
  return items.find((item) => String(item.action_id || '').trim() === normalizedActionId) || null;
}

function buildActionRuntimePayload(actionType, caseItem, context = {}) {
  if (!caseItem) throw new Error('AI action runtime requires a live case context.');
  const payload = {
    action_type: actionType,
    case_id: caseItem.case_id,
    case_reference: caseItem.case_reference || caseItem.case_id,
    requested_role: state.session?.role_name || '',
    metadata: {
      source: 'dashboard_actions_lane',
      origin_view: state.view,
      origin_case_id: caseItem.case_id,
    },
  };
  if (actionType === 'draft_document') {
    payload.title = `${caseItem.title || caseItem.case_id} governed record`;
    payload.document_class = 'record';
    payload.tags = ['ai_action_runtime', 'dashboard'];
  }
  if (actionType === 'request_human') {
    payload.mode = 'report';
    payload.prompt = `Please review case ${caseItem.case_id}, summarize the governed posture, and state the next safe action.`;
  }
  if (context.label) payload.label = context.label;
  return payload;
}

function resolveActionArtifactFocus(artifact = {}) {
  const kind = String(artifact.kind || '').trim();
  const refId = String(artifact.ref_id || '').trim();
  const caseId = String(artifact.case_id || '').trim();
  if (kind === 'document') return { view: 'documents', entityType: refId ? 'document' : '', entityId: refId, caseId };
  if (kind === 'human_ask_session') return { view: 'human_ask', entityType: refId ? 'human_ask_session' : '', entityId: refId, caseId };
  if (kind === 'case_summary') return { view: 'cases', entityType: caseId ? 'case' : '', entityId: caseId || refId, caseId: caseId || refId };
  return { view: 'actions', entityType: refId ? 'action' : '', entityId: refId, caseId };
}

function resolveActionPrimaryFocus(item = {}) {
  const nextView = String(item.next_view || item.catalog?.primary_view || 'actions').trim() || 'actions';
  const artifacts = Array.isArray(item.artifacts) ? item.artifacts : [];
  const artifactFocus = artifacts.length ? resolveActionArtifactFocus(artifacts[0]) : null;
  if (nextView === 'documents' && artifactFocus?.view === 'documents') return artifactFocus;
  if (nextView === 'human_ask' && artifactFocus?.view === 'human_ask') return artifactFocus;
  if (nextView === 'cases') return { view: 'cases', entityType: 'case', entityId: item.case_id || '', caseId: item.case_id || '' };
  return { view: 'actions', entityType: item.action_id ? 'action' : '', entityId: item.action_id || '', caseId: item.case_id || '' };
}

function renderActionRegistryCard(entry, currentCase) {
  const canLaunch = Boolean(currentCase) && can('actions.create');
  return `
    <article class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(entry.action_type || 'action')}</div>
          <h3 class="card-title">${escapeHtml(entry.label || titleCase(entry.action_type || 'AI action'))}</h3>
          <p class="card-subtitle">${escapeHtml(entry.description || 'Governed AI runtime action.')}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(entry.primary_view || 'actions')}</div>
      </div>
      ${keyValue([
        ['Authority', String(entry.authority_boundary || '-')],
        ['Side effects', String(entry.side_effect_policy || '-')],
      ])}
      <div class="inline-actions">
        <button class="action-button" type="button" data-action-runtime-action="create" data-action-type="${escapeHtml(entry.action_type || '')}" ${canLaunch ? '' : 'disabled'}>${escapeHtml(canLaunch ? 'Run in current case' : 'Open a case first')}</button>
      </div>
    </article>
  `;
}

function renderActionArtifactCard(artifact = {}, actionItem = {}) {
  const focus = resolveActionArtifactFocus(artifact);
  const viewLabel = VIEW_TITLES[focus.view] || titleCase(focus.view || 'actions');
  return `
    <article class="mini-card stack">
      <div class="eyebrow muted">${escapeHtml(artifact.kind || 'artifact')}</div>
      <strong>${escapeHtml(artifact.label || artifact.ref_id || 'Artifact')}</strong>
      <p class="muted">${escapeHtml(artifact.detail || 'Governed artifact created by the AI runtime.')}</p>
      <div class="inline-actions">
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view: focus.view,
          focusType: focus.entityType,
          focusId: focus.entityId,
          caseId: focus.caseId || actionItem.case_id || '',
          title: `${artifact.label || artifact.ref_id || 'Artifact'} opened in ${viewLabel}.`,
          detail: 'The linked artifact stays attached to the same governed case and runtime story.',
          actionLabel: `Open ${viewLabel}`,
        })}>${escapeHtml(`Open ${viewLabel}`)}</button>
      </div>
    </article>
  `;
}

function renderActionCard(item) {
  const primary = resolveActionPrimaryFocus(item);
  const primaryViewLabel = VIEW_TITLES[primary.view] || titleCase(primary.view || 'actions');
  const canExecute = can('actions.execute') && ['planned', 'failed_closed'].includes(String(item.status || ''));
  const artifacts = Array.isArray(item.artifacts) ? item.artifacts : [];
  const executionLog = Array.isArray(item.execution_log) ? item.execution_log.slice(0, 3) : [];
  const meta = getActionBoardMeta(item);
  const tone = meta.tone || getActionMissionTone(item);
  return `
    <article class="card stack action-runtime-card action-runtime-card-tone-${escapeHtml(tone)}${isFocusedEntity('action', item.action_id) ? ' focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey('action', item.action_id))}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(item.action_id || 'action')}</div>
          <h3 class="card-title">${escapeHtml(item.label || titleCase(item.action_type || 'AI action'))}</h3>
          <p class="card-subtitle">${escapeHtml(item.output_summary || item.next_action || 'Governed AI runtime item.')}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(meta.tempoBadge || item.status || 'planned')}${statusBadge(item.action_type || 'action')}</div>
      </div>
      <div class="transition-route command-inbox-route">
        <span class="transition-node transition-node-active">${escapeHtml(item.case_id ? `Case ${item.case_id}` : 'AI runtime')}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(item.status || 'planned')}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(primaryViewLabel)}</span>
      </div>
      <p class="muted small action-runtime-route-note">${escapeHtml(meta.routePhase)}</p>
      ${keyValue([
        ['Case', String(item.case_id || '-')],
        ['Authority', String(item.authority_boundary || '-')],
        ['Side effects', String(item.side_effect_policy || '-')],
        ['Next lane', primaryViewLabel],
        ['Next owner', String(meta.nextOwner || '-')],
        ['Artifacts', String(item.artifacts_total || artifacts.length || 0)],
      ])}
      <div class="trace-box compact-trace action-runtime-consequence-box"><strong>${escapeHtml(meta.consequenceTitle || meta.eyebrow)}</strong><p class="muted">${escapeHtml(item.waiting_reason || item.latest_error || meta.consequenceDetail || meta.routePhase)}</p></div>
      <div class="trace-box compact-trace"><strong>Recommended move</strong><p class="muted">${escapeHtml(item.next_action || item.output_summary || `Open ${primaryViewLabel} to continue from the right governed lane.`)}</p></div>
      ${item.waiting_reason ? `<div class="trace-box"><strong>Waiting reason</strong><p class="muted">${escapeHtml(item.waiting_reason)}</p></div>` : ''}
      ${item.latest_error ? `<div class="trace-box trace-box-danger"><strong>Failure detail</strong><p class="muted">${escapeHtml(item.latest_error)}</p></div>` : ''}
      ${artifacts.length ? `<div class="card-grid">${artifacts.map((artifact) => renderActionArtifactCard(artifact, item)).join('')}</div>` : ''}
      ${executionLog.length ? `<div class="trace-box"><strong>Runtime trace</strong><p class="muted">${escapeHtml(executionLog.map((entry) => `${entry.status}: ${entry.title}`).join(' | '))}</p></div>` : ''}
      <div class="inline-actions">
        <button class="action-button" type="button" ${buildViewJumpAttributes({
          view: primary.view,
          focusType: primary.entityType,
          focusId: primary.entityId,
          caseId: primary.caseId || item.case_id || '',
          title: `${item.label || item.action_id} opened in ${primaryViewLabel}.`,
          detail: item.next_action || meta.consequenceDetail || 'Continue the governed flow from the linked runtime lane.',
          actionLabel: `Open ${primaryViewLabel}`,
        })}>${escapeHtml(`Open ${primaryViewLabel}`)}</button>
        <button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({
          view: 'cases',
          focusType: 'case',
          focusId: item.case_id || '',
          caseId: item.case_id || '',
          title: item.case_id ? `Case ${item.case_id} reopened from the AI action runtime.` : 'Opened Cases.',
          detail: 'Return to the canonical case to keep actions, documents, and human review in one story.',
          actionLabel: 'Open Cases',
        })}>Open Cases</button>
        ${canExecute ? `<button class="action-button action-button-muted" type="button" data-action-runtime-action="execute" data-action-id="${escapeHtml(item.action_id || '')}">Run again</button>` : ''}
      </div>
    </article>
  `;
}

function renderActionEmptyState(currentCase) {
  const title = currentCase ? `No AI action has run for ${currentCase.case_id} yet` : 'Open a case to start governed AI execution';
  const detail = currentCase
    ? 'Launch summarize, document draft, or human handoff actions from this lane and they will stay tied to the same case, evidence, and follow-up flow.'
    : 'The AI action runtime is case-bound. Open Cases first, select the governed issue, then return here to let AI work inside explicit authority and side-effect rules.';
  return `
    <article class="card stack">
      <div>
        <div class="eyebrow muted">AI action runtime</div>
        <h3 class="card-title">${escapeHtml(title)}</h3>
        <p class="card-subtitle">${escapeHtml(detail)}</p>
      </div>
      <div class="inline-actions">
        <button class="action-button" type="button" data-view-jump="cases">Open Cases</button>
        ${currentCase ? `<button class="action-button action-button-muted" type="button" data-view-jump="documents" data-view-jump-case-id="${escapeHtml(currentCase.case_id || '')}">Open Documents</button>` : ''}
      </div>
    </article>
  `;
}

function renderCommandHome(snapshot) {
  const surface = snapshot.command_surface || {};
  const posture = surface.posture_summary || {};
  const mission = surface.mission_control || {};
  const inbox = snapshot.unified_work_inbox || { summary: {}, items: [] };
  const inboxSummary = inbox.summary || {};
  const operationsMapItems = Array.isArray(inbox.items) ? inbox.items.slice(0, 4) : [];
  const activeOperations = Array.isArray(surface.active_operations) ? surface.active_operations.slice(0, 3) : [];
  const nextActions = buildHomeNextActions(snapshot, surface).slice(0, 5);
  const aiFeed = Array.isArray(surface.ai_activity_feed) ? surface.ai_activity_feed.slice(0, 5) : [];
  const departments = Array.isArray(surface.department_quick_access) ? surface.department_quick_access.slice(0, 6) : [];
  const session = state.session || {};
  const primaryViews = getTabletPrimaryViews(session);
  const quickLinks = orderCommandQuickLinksByPersona(Array.isArray(surface.quick_links) ? [...surface.quick_links] : [], primaryViews);
  if (canAccessSetupAssistant()) quickLinks.push({ view: 'setup', label: 'Setup Assistant' });
  const setupContinuation = renderHomeSetupContinuation(snapshot);
  const touchLaneSection = renderHomeTouchLaneSection(snapshot, primaryViews);
  const attentionTotal = Number(posture.attention_items_total || 0);
  const aiRunning = Number(posture.ai_actions_running || 0);
  const aiTotal = Number(posture.ai_actions_total || aiFeed.length || 0);
  const evidenceDate = posture.evidence_verified_at ? shortTime(posture.evidence_verified_at) : 'No recent verification';
  const evidenceLabel = formatStatusLabel(posture.evidence_status || 'verified');
  const modeNote = posture.operating_status === 'stable' ? 'Stable - green' : 'Guarded - review';
  const missionTopTitle = mission.top_move_title || nextActions[0]?.title || 'AI is operating without a new human boundary';
  const missionTopDetail = mission.top_move_detail || nextActions[0]?.detail || 'No human approvals are waiting right now. The AI workforce is still moving inside the governed lanes.';
  const missionWorldTitle = mission.world_state_title || 'Governed runtime posture';
  const missionWorldNote = mission.world_state_note || 'Use the posture cards and next actions below to keep the Director oriented.';
  const aiMomentumTitle = mission.ai_momentum_title || 'AI workforce';
  const aiMomentumDetail = mission.ai_momentum_detail || `${aiRunning} running | ${aiTotal} total governed actions`;
  const aiMomentumBadge = mission.ai_momentum_badge || (aiRunning ? 'AI moving' : aiFeed.length ? 'AI recent' : 'AI quiet');
  const missionPressureLabel = mission.pressure_label || `${attentionTotal} attention`;
  const inboxLeadLane = VIEW_TITLES[inboxSummary.primary_view] || titleCase(inboxSummary.primary_view || 'overview');
  const controlRoomAction = canAccessControlRoom()
    ? renderViewJumpButton({ view: 'control_room', label: 'Open Control Room', className: 'action-button action-button-muted' })
    : '<span class="pill pill-muted">Governance lead required</span>';
  return `
      <section class="command-home-stack stack gap-lg">
        <section class="command-home-hero">
          <article class="card hero-card hero-card-primary command-home-hero-primary">
            <div class="hero-heading">
              <div>
                <div class="eyebrow">Director Home</div>
                <h3 class="hero-title">Your Next Actions</h3>
                <p class="hero-subtitle">Start here first. This command surface answers posture and next move within five seconds, while deeper governance mechanics stay in Control Room.</p>
              </div>
              <div class="hero-chip-row">${statusBadge(posture.operating_status || 'guarded')}${statusBadge(missionPressureLabel)}${statusBadge(session.persona || session.role_name || 'operator')}</div>
            </div>
            <div class="inline-actions">
              ${renderViewJumpButton({ view: 'requests', label: 'Open Work Inbox', className: 'action-button' })}
              ${renderViewJumpButton({ view: 'actions', label: 'See AI Activity', className: 'action-button action-button-muted' })}
              ${controlRoomAction}
            </div>
          </article>
          <article class="card hero-card hero-card-secondary command-home-hero-secondary">
            <div>
              <div class="eyebrow muted">Lead governed move</div>
              <h3 class="card-title">${escapeHtml(missionTopTitle)}</h3>
              <p class="card-subtitle">${escapeHtml(missionTopDetail)}</p>
            </div>
            <div class="trace-box compact-trace"><strong>${escapeHtml(missionWorldTitle)}</strong><p class="muted">${escapeHtml(`${missionWorldNote} ${aiMomentumTitle}: ${aiMomentumDetail}`.trim())}</p></div>
          </article>
        </section>
        <section class="command-guidance-grid">
          ${renderCommandTabletFocusCard(session, primaryViews)}
          ${renderCommandSessionContinuityCard(session)}
        </section>
        <section class="card stack command-home-section">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">System Posture Summary</div>
              <h3 class="card-title">Five-second posture check</h3>
              <p class="card-subtitle">Only the signals a normal user needs right now. Technical evidence, signatures, and runtime internals stay behind the Control Room boundary.</p>
            </div>
          </div>
          <div class="command-summary-grid">
            ${renderHomePostureCard('Operating Mode', 'Governance-first', modeNote, posture.operating_status === 'stable' ? 'success' : 'warning', 'One governed operating model stays active across the Director.')}
            ${renderHomePostureCard('AI Workforce', `${aiRunning} actions running`, 'One core, many hats', aiRunning ? 'accent' : 'default', 'AI remains the primary workforce across active governed cases.')}
            ${renderHomePostureCard('Conflicts & Locks', `${attentionTotal} items need attention`, canAccessControlRoom() ? 'Open Control Room' : 'Escalate to governance lead', attentionTotal ? 'warning' : 'success', 'Only show pressure that could change the next human move.', canAccessControlRoom() ? 'control_room' : '')}
            ${renderHomePostureCard('Evidence Integrity', evidenceLabel, evidenceDate, posture.evidence_status === 'verified' ? 'success' : 'warning', 'Evidence remains verified while identifiers stay hidden by default.')}
          </div>
        </section>
        <section class="command-board-grid">
          <section class="card stack command-home-section command-home-section-operations command-home-section-lead">
            <div class="hero-heading">
              <div>
                <div class="eyebrow muted">Operations Map</div>
                <h3 class="card-title">Where pressure is building across the runtime</h3>
                <p class="card-subtitle">Read the live lanes like a command board: which queue is gating AI, which lane is blocked, and where the Director should step in next.</p>
              </div>
              <div class="hero-chip-row">${statusBadge(`${inboxSummary.human_required_total || 0} human`)}${statusBadge(`${inboxSummary.blocked_total || 0} blocked`)}</div>
            </div>
            ${keyValue([
              ['Open work', String(inboxSummary.open_total || 0)],
              ['Lead lane', inboxLeadLane],
              ['Human required', String(inboxSummary.human_required_total || 0)],
              ['Blocked paths', String(inboxSummary.blocked_total || 0)],
              ['Ready lanes', String(inboxSummary.ready_total || 0)],
            ])}
            <div class="trace-box"><strong>Lead move</strong><p class="muted">${escapeHtml(inboxSummary.primary_next_step || missionTopDetail)}</p></div>
            <div class="view-prelude-grid">${operationsMapItems.length ? operationsMapItems.map((item) => renderUnifiedWorkInboxItem(item, { compact: true })).join('') : renderCommandEmptyState('No operations map is visible yet.', 'As governed work starts moving, this board will show which lane owns the next real move.')}</div>
            ${activeOperations.length ? `<div class="command-operation-shell"><div class="hero-heading"><div><div class="eyebrow muted">Active operations</div><h3 class="card-title">Which governed stories are shaping the board</h3><p class="card-subtitle">Keep the most important cross-lane operations visible, not just the queues that generated them.</p></div><div class="hero-chip-row">${statusBadge(`${activeOperations.length} live`)}${statusBadge(activeOperations[0].cluster_label || 'Lead cluster')}</div></div>${renderActiveOperationCard(activeOperations[0], { featured: true })}${activeOperations.length > 1 ? `<div class="command-operation-cluster-head"><div class="eyebrow muted">${escapeHtml(activeOperations[1].cluster_label || 'Supporting cluster')}</div><p class="muted">Keep nearby operations visible so the lead move stays supported across teams and lanes.</p></div><div class="command-operation-grid">${activeOperations.slice(1).map((item) => renderActiveOperationCard(item)).join('')}</div>` : ''}</div>` : ''}
          </section>
          <div class="command-support-stack">
            <section class="card command-next-actions-card stack command-home-section command-home-section-support command-home-section-actions">
              <div class="hero-heading">
                <div>
                  <div class="eyebrow muted">Director moves</div>
                  <h3 class="card-title">Your Next Actions</h3>
                  <p class="card-subtitle">Only the approvals, blocked items, escalations, and follow-through that genuinely need a human director now.</p>
                </div>
                <div class="hero-chip-row">${statusBadge(`${nextActions.length} visible`)}</div>
              </div>
              <div class="command-next-grid">${nextActions.length ? nextActions.map((item, index) => renderHomeNextActionCard(item, { featured: index === 0 })).join('') : renderCommandEmptyState('No human actions are waiting right now.', 'AI is carrying the active workload. Open AI Actions if you want to inspect current execution.')}</div>
            </section>
            <section class="card stack command-home-section command-home-section-support command-home-section-feed">
              <div class="hero-heading">
                <div>
                  <div class="eyebrow muted">Runtime tempo</div>
                  <h3 class="card-title">What AI is doing now</h3>
                  <p class="card-subtitle">Recent governed AI execution across running, completed, and waiting-human actions.</p>
                </div>
                <div class="hero-chip-row">${statusBadge(`${aiFeed.length} recent`)}${statusBadge(aiMomentumBadge)}</div>
              </div>
              <div class="command-feed-list">${aiFeed.length ? aiFeed.map((item, index) => renderAiFeedCard({ ...item, featured: index === 0 || item.featured })).join('') : renderCommandEmptyState('No AI activity is visible yet.', 'Once actions start, this feed becomes the quickest way to see what AI finished and where it needs human input.')}</div>
            </section>
          </div>
        </section>
        ${setupContinuation}
        ${touchLaneSection}
        <section class="card stack command-home-section">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Quick Access by Department / Team</div>
              <h3 class="card-title">Jump into the team context that owns the work</h3>
              <p class="card-subtitle">These cards reuse master data and search continuity so you can route into the right business context without opening technical screens.</p>
            </div>
          </div>
          <div class="command-department-grid">${departments.length ? departments.map((item) => renderDepartmentQuickAccessCard(item)).join('') : renderCommandEmptyState('No department baseline is visible yet.', 'Master data will surface functional teams here once the runtime sees more real work.')}</div>
        </section>
        <section class="card stack command-home-section command-quick-links-card">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Quick Links</div>
              <h3 class="card-title">Continue in the right governed lane</h3>
            </div>
          </div>
          <div class="command-quick-links-row">${quickLinks.map((item) => renderHomeQuickLink(item)).join('')}${canAccessControlRoom() ? renderHomeQuickLink({ view: 'control_room', label: 'Control Room' }) : ''}</div>
        </section>
      </section>
    `;
}

function getTabletPrimaryViews(session = state.session || {}) {
  return (Array.isArray(session.tablet_primary_views) ? session.tablet_primary_views : [])
    .map((item) => String(item || '').trim())
    .filter((item) => item && VIEW_TITLES[item]);
}

function orderCommandQuickLinksByPersona(quickLinks, primaryViews = []) {
  const order = new Map(primaryViews.map((view, index) => [view, index]));
  return [...quickLinks].sort((left, right) => {
    const leftRank = order.has(left.view) ? order.get(left.view) : 999;
    const rightRank = order.has(right.view) ? order.get(right.view) : 999;
    if (leftRank != rightRank) return leftRank - rightRank;
    return String(left.label || left.view || '').localeCompare(String(right.label || right.view || ''));
  });
}

function renderCommandTabletFocusCard(session, primaryViews) {
  const focusTitle = session.tablet_focus_title || 'Department direction';
  const focusNote = session.tablet_focus_note || 'Stay on Home for posture first, then move through the next governed lane without opening deeper runtime plumbing.';
  const focusViews = primaryViews.slice(0, 4);
  const focusActions = focusViews.length
    ? focusViews.map((view) => renderViewJumpButton({
      view,
      label: VIEW_TITLES[view] || titleCase(view),
      className: 'action-button action-button-muted',
      title: `${VIEW_TITLES[view] || titleCase(view)} reopened from Home.`,
      detail: `Continue from ${VIEW_TITLES[view] || titleCase(view)} while staying inside the private tablet lane.`,
      actionLabel: VIEW_TITLES[view] || titleCase(view),
    })).join('')
    : renderViewJumpButton({ view: 'requests', label: 'Open Work Inbox', className: 'action-button action-button-muted' });
  return `
    <article class="card command-home-section command-guidance-card">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Tablet focus</div>
          <h3 class="card-title">${escapeHtml(focusTitle)}</h3>
          <p class="card-subtitle">${escapeHtml(focusNote)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(session.private_runtime_mode || 'private first')}${statusBadge(session.persona || session.role_name || 'operator')}</div>
      </div>
      <div class="command-focus-actions">${focusActions}</div>
      <p class="muted small">These are the lanes this persona should reach first on tablet before stepping into deeper governance tooling.</p>
    </article>
  `;
}

function renderCommandSessionContinuityCard(session) {
  const continuity = buildSessionContinuityState(session, Date.now());
  const authMethod = session.session_auth_method ? titleCase(String(session.session_auth_method).replaceAll('_', ' ')) : 'Private access token';
  const lastSeen = session.session_last_seen_at ? shortTime(session.session_last_seen_at) : 'Waiting for the first active tablet session';
  const primaryLane = getTabletPrimaryViews(session).find((view) => view && view !== 'overview') || 'requests';
  const primaryLaneLabel = VIEW_TITLES[primaryLane] || titleCase(primaryLane);
  const renewButton = continuity.action !== 'monitor'
    ? `<button class="action-button" type="button" data-session-renew="true"><span data-session-clock="action-label">${escapeHtml(continuity.actionLabel)}</span></button>`
    : `<button class="action-button action-button-muted" type="button" data-session-renew="true"><span data-session-clock="action-label">Renew session</span></button>`;
  return `
    <article class="card command-home-section command-guidance-card" data-session-continuity-root="true">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Private session continuity</div>
          <h3 class="card-title" data-session-clock="title">${escapeHtml(continuity.title)}</h3>
          <p class="card-subtitle">Keep the tablet session alive inside the private runtime without exposing lower-level runtime stores on Home.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(continuity.badge)}${statusBadge(authMethod)}</div>
      </div>
      <div class="key-value">
        <div class="key-value-row"><span class="muted">Last seen</span><span class="key-value-value">${escapeHtml(lastSeen)}</span></div>
        <div class="key-value-row"><span class="muted">Idle lock</span><span class="key-value-value" data-session-clock="idle">${escapeHtml(continuity.idleLabel)}</span></div>
        <div class="key-value-row"><span class="muted">Signed session</span><span class="key-value-value" data-session-clock="signed">${escapeHtml(continuity.signedLabel)}</span></div>
        <div class="key-value-row"><span class="muted">Auth method</span><span class="key-value-value">${escapeHtml(authMethod)}</span></div>
        <div class="key-value-row"><span class="muted">Active sessions</span><span class="key-value-value">${escapeHtml(String(session.active_session_count || 0))}</span></div>
      </div>
      <p class="muted small" data-session-clock="note">${escapeHtml(continuity.note)}</p>
      <p class="muted small" data-session-clock="helper">${escapeHtml(continuity.helper)}</p>
      <div class="inline-actions">${renewButton}${renderViewJumpButton({ view: primaryLane, label: `Open ${primaryLaneLabel}`, className: 'action-button action-button-muted', title: `${primaryLaneLabel} is the best adjacent lane for this persona on tablet.`, detail: `Continue in ${primaryLaneLabel} while the private session stays inside the governed runtime.`, actionLabel: `Open ${primaryLaneLabel}` })}</div>
    </article>
  `;
}

function getTabletLaneEmphasis(session = state.session || {}) {
  const emphasis = session.tablet_lane_emphasis;
  return emphasis && typeof emphasis === 'object' ? emphasis : {};
}

function buildCommandTouchLanes(snapshot, primaryViews = getTabletPrimaryViews(state.session || {})) {
  const inboxSummary = snapshot.unified_work_inbox?.summary || {};
  const caseSummary = snapshot.cases?.summary || {};
  const documentSummary = snapshot.documents?.summary || {};
  const actionSummary = snapshot.actions?.summary || {};
  const masterSummary = snapshot.master_data?.summary || {};
  const assignmentSummary = snapshot.assignment_queue?.summary || {};
  const laneEmphasis = getTabletLaneEmphasis(state.session || {});
  const laneMap = {
    requests: {
      view: 'requests',
      title: 'Work Inbox',
      countLabel: `${Number(inboxSummary.open_total || 0)} open`,
      note: Number(inboxSummary.human_required_total || 0)
        ? `${Number(inboxSummary.human_required_total || 0)} human-required items are waiting in the live queue.`
        : 'Stay in the owned work queue first when you need the next human move immediately.',
      badge: Number(inboxSummary.human_required_total || 0) ? 'human required' : 'active queue',
      actionLabel: 'Open Work Inbox',
    },
    cases: {
      view: 'cases',
      title: 'Cases',
      countLabel: `${Number(caseSummary.cases_total || 0)} cases`,
      note: Number(caseSummary.human_required_total || 0)
        ? `${Number(caseSummary.human_required_total || 0)} cases still need a real human boundary.`
        : 'Use the canonical case lane when one governed issue needs linked context, proof, and follow-through.',
      badge: Number(caseSummary.human_required_total || 0) ? 'human required' : 'linked cases',
      actionLabel: 'Open Cases',
    },
    documents: {
      view: 'documents',
      title: 'Documents',
      countLabel: `${Number(documentSummary.documents_total || 0)} documents`,
      note: Number(documentSummary.in_review_total || 0)
        ? `${Number(documentSummary.in_review_total || 0)} documents are in review right now.`
        : 'Open the document lane when governed artifacts themselves are the work object that needs action.',
      badge: Number(documentSummary.in_review_total || 0) ? 'review active' : 'document runtime',
      actionLabel: 'Open Documents',
    },
    actions: {
      view: 'actions',
      title: 'AI Actions',
      countLabel: `${Number(actionSummary.actions_total || 0)} governed actions`,
      note: Number(actionSummary.waiting_human_total || 0)
        ? `${Number(actionSummary.waiting_human_total || 0)} AI actions are waiting on human follow-through.`
        : 'Check AI execution when you want to see what the workforce is doing right now.',
      badge: Number(actionSummary.waiting_human_total || 0) ? 'waiting human' : 'ai active',
      actionLabel: 'Open AI Actions',
    },
    directory: {
      view: 'directory',
      title: 'Directory & Search',
      countLabel: `${Number(masterSummary.people_total || 0)} people`,
      note: Number(assignmentSummary.items_total || 0)
        ? `${Number(assignmentSummary.items_total || 0)} assignments are linked to real owners, teams, and seats.`
        : 'Use directory search when you need to route work through real people, teams, and seats.',
      badge: Number(masterSummary.search_ready || 0) ? 'search ready' : 'directory live',
      actionLabel: 'Open Directory',
    },
  };
  const orderedViews = (primaryViews.length ? primaryViews : ['requests', 'cases', 'documents', 'actions', 'directory'])
    .filter((view, index, views) => view && view !== 'overview' && laneMap[view] && views.indexOf(view) === index);
  return orderedViews.map((view, index) => {
    const emphasis = laneEmphasis[view] || {};
    const rank = emphasis.rank || (index === 0 ? 'primary' : index <= 2 ? 'secondary' : 'support');
    const emphasisLabel = emphasis.label || (rank === 'primary' ? 'Start here' : rank === 'secondary' ? 'Keep close' : 'Keep nearby');
    return {
      ...laneMap[view],
      emphasis: rank,
      emphasisLabel,
      emphasisNote: emphasis.note || '',
    };
  });
}

function renderCommandTouchLaneCard(item, compact = false) {
  if (!item) return '';
  const active = state.view === item.view;
  const emphasisClass = item.emphasis ? ` command-touch-card-emphasis-${item.emphasis}` : '';
  const flowLabel = item.emphasis === 'primary' ? 'Start here' : item.emphasis === 'secondary' ? 'Keep in flow' : 'Keep nearby';
  const buttonLabel = active ? `Stay in ${item.title}` : item.actionLabel || `Open ${item.title}`;
  const button = renderViewJumpButton({
    view: item.view,
    label: buttonLabel,
    className: active ? 'action-button action-button-muted' : 'action-button',
    title: `${item.title} reopened from the tablet command surface.`,
    detail: item.note || `Continue in ${item.title}.`,
    actionLabel: buttonLabel,
  });
  return `
    <article class="command-touch-card${active ? ' command-touch-card-active' : ''}${compact ? ' command-touch-card-compact' : ''}${emphasisClass}">
      <div class="hero-chip-row"><span class="pill">${escapeHtml(item.emphasisLabel || 'Lane')}</span>${statusBadge(item.badge || 'lane')}</div>
      <strong>${escapeHtml(item.title)}</strong>
      <p class="command-touch-count">${escapeHtml(item.countLabel || '0')}</p>
      <div class="transition-route command-touch-route">
        <span class="transition-node${active ? '' : ' transition-node-active'}">${escapeHtml(flowLabel)}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node${active ? ' transition-node-active' : ''}">${escapeHtml(item.title)}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(item.badge || 'lane')}</span>
      </div>
      <p class="muted">${escapeHtml(item.note || 'Continue in the governed lane that currently owns the work.')}</p>
      ${item.emphasisNote ? `<p class="muted small command-momentum-note">${escapeHtml(item.emphasisNote)}</p>` : ''}
      <div class="inline-actions">${button}</div>
    </article>
  `;
}

function renderHomeTouchLaneSection(snapshot, primaryViews) {
  const lanes = buildCommandTouchLanes(snapshot, primaryViews).slice(0, 4);
  if (!lanes.length) return '';
  return `
    <section class="card stack command-home-section">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Touch-first work lanes</div>
          <h3 class="card-title">Move with one tap into the right operating lane</h3>
          <p class="card-subtitle">These bigger lane cards are ordered for this persona so tablet work starts with the most relevant governed surface first.</p>
        </div>
      </div>
      <div class="command-touch-grid">${lanes.map((item) => renderCommandTouchLaneCard(item)).join('')}</div>
    </section>
  `;
}

function renderTabletLaneRail(snapshot) {
  const lanes = buildCommandTouchLanes(snapshot).slice(0, 4);
  if (!lanes.length) return '';
  return `
    <section class="card stack command-home-section tablet-lane-rail">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Tablet lane rail</div>
          <h3 class="card-title">Keep adjacent work lanes one tap away</h3>
          <p class="card-subtitle">Switch between the core operating lanes without falling back into low-level runtime navigation.</p>
        </div>
      </div>
      <div class="command-touch-grid command-touch-grid-compact">${lanes.map((item) => renderCommandTouchLaneCard(item, true)).join('')}</div>
    </section>
  `;
}

function renderHomePostureCard(label, value, note, tone = 'default', detail = '', view = '') {
  const action = view
    ? `<div class="inline-actions">${renderViewJumpButton({ view, label: 'Open', className: 'action-button action-button-muted' })}</div>`
    : '';
  return `
    <article class="command-summary-card tone-${escapeHtml(tone)}">
      <span class="command-summary-label">${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <p class="muted">${escapeHtml(note)}</p>
      ${detail ? `<p class="muted small">${escapeHtml(detail)}</p>` : ''}
      ${action}
    </article>
  `;
}

function buildHomeNextActions(snapshot, surface) {
  const assignments = Array.isArray(snapshot.assignment_queue?.items) ? snapshot.assignment_queue.items : [];
  const surfaced = Array.isArray(surface.next_actions) ? surface.next_actions : [];
  const session = state.session || {};
  const profileId = String(session.profile_id || '').toLowerCase();
  const displayName = String(session.display_name || '').toLowerCase();
  const roleName = String(session.role_name || '').toLowerCase();
  const ownershipScore = (item) => {
    let base = 0;
    const ownerId = String(item.owner_id || '').toLowerCase();
    const ownerLabel = String(item.owner_label || '').toLowerCase();
    const teamLabel = String(item.team_label || '').toLowerCase();
    if (profileId && ownerId === profileId) base += 10;
    if (displayName && ownerLabel === displayName) base += 8;
    if (roleName && (ownerId === roleName || ownerLabel.includes(roleName))) base += 6;
    if (teamLabel && roleName && teamLabel.includes(roleName)) base += 4;
    return base;
  };
  if (surfaced.length) {
    return [...surfaced]
      .sort((left, right) => {
        const delta = (Number(right.display_score || 0) + ownershipScore(right)) - (Number(left.display_score || 0) + ownershipScore(left));
        if (delta !== 0) return delta;
        return Number(right.age_hours || 0) - Number(left.age_hours || 0);
      })
      .slice(0, 6);
  }
  const fallbackScore = (item) => {
    let base = ownershipScore(item);
    if (item.status === 'human_required') base += 6;
    if (item.status === 'blocked') base += 5;
    if (item.priority === 'critical') base += 4;
    if (item.priority === 'high') base += 2;
    base += Math.min(Number(item.age_hours || 0), 72) / 24;
    return base;
  };
  return [...assignments].sort((left, right) => fallbackScore(right) - fallbackScore(left)).slice(0, 6);
}

function renderActiveOperationCard(item, options = {}) {
  const featured = Boolean(options.featured || item.featured);
  const toneClass = item.tone ? ` tone-${escapeHtml(item.tone)}` : '';
  const featuredClass = featured ? ' command-action-card-featured' : '';
  const featuredClass = featured ? ' command-operation-card-featured' : '';
  const clusterLabel = item.cluster_label || (featured ? 'Lead cluster' : 'Supporting cluster');
  const clusterDetail = item.cluster_detail || (featured
    ? 'This operation is shaping the board right now.'
    : 'Keep this operation nearby so the lead move stays readable across lanes.');
  const nextLaneLabel = item.next_view_label || VIEW_TITLES[item.next_view || 'cases'] || 'Cases';
  const openCaseButton = renderViewJumpButton({
    view: 'cases',
    label: featured ? 'Open lead case' : 'Open case',
    className: 'action-button',
    focusType: 'case',
    focusId: item.case_id || '',
    caseId: item.case_id || '',
    title: item.case_id ? `Case ${item.case_id} reopened from Home.` : 'Case reopened from Home.',
    detail: item.quest_note || 'Continue from the canonical case story.',
    actionLabel: featured ? 'Open lead case' : 'Open case',
  });
  const openLaneButton = renderViewJumpButton({
    view: item.next_view || 'cases',
    label: `Open ${nextLaneLabel}`,
    className: 'action-button action-button-muted',
    focusType: item.next_focus_type || '',
    focusId: item.next_focus_id || '',
    caseId: item.case_id || '',
    title: `${item.title || item.case_id || 'Operation'} reopened in ${nextLaneLabel}.`,
    detail: item.lead_move || item.quest_note || 'Continue the next governed move from the lead lane.',
    actionLabel: `Open ${nextLaneLabel}`,
  });
  return `
      <article class="command-action-card command-operation-card${toneClass}${featuredClass}" data-focus-key="${escapeHtml(buildFocusKey('case', item.case_id || ''))}">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">${escapeHtml(`${clusterLabel} | ${item.board_rank_label || item.case_id || 'Operation'}`)}</div>
            <strong>${escapeHtml(item.title || item.case_id || 'Governed operation')}</strong>
          </div>
          <div class="hero-chip-row">${statusBadge(item.pressure_badge || 'operation')}${statusBadge(`${escapeHtml(String(item.item_total || 0))} items`)}</div>
        </div>
        <div class="transition-route command-feed-route command-operation-route"><span class="transition-node">${escapeHtml(item.lead_team || 'Operations')}</span><span class="transition-arrow">&rarr;</span><span class="transition-node transition-node-active">${escapeHtml(nextLaneLabel)}</span></div>
        <p class="muted">${escapeHtml(item.quest_note || item.operation_label || 'Keep the operation visible across lanes.')}</p>
        <p class="muted small command-operation-cluster-note">${escapeHtml(clusterDetail)}</p>
        <div class="trace-box compact-trace"><strong>${escapeHtml(item.operation_label || 'Active operation')}</strong><p class="muted">${escapeHtml(item.lead_move || 'Continue from the lead governed lane.')}</p></div>
        <p class="muted small command-momentum-note">${escapeHtml(item.route_phase || 'The next governed lane is already visible from this operation.')}</p>
        <div class="command-action-meta">${escapeHtml(item.lead_team || 'Operations')} | ${escapeHtml(String(item.item_total || 0))} routed items | ${escapeHtml(item.lane_summary || nextLaneLabel)}</div>
        <div class="inline-actions">${openCaseButton}${openLaneButton}</div>
      </article>
    `;
}

function renderHomeNextActionCard(item, options = {}) {
  const featured = Boolean(options.featured);
  const focusType = item.focus_type || '';
  const focusId = item.focus_id || '';
  const caseId = item.case_id || '';
  const toneClass = item.tone ? ` tone-${escapeHtml(item.tone)}` : '';
  const primaryLabel = item.kind === 'override'
    ? 'Approve'
    : item.move_label || (item.status === 'blocked' ? 'Resolve Now' : 'Take Action');
  const primaryButton = item.kind === 'override'
    ? `<button class="action-button" type="button" data-override-action="approve" data-request-id="${escapeHtml(focusId || item.reference_id || '')}">${escapeHtml(primaryLabel)}</button>`
    : `<button class="action-button" type="button" ${buildViewJumpAttributes({ view: item.view || 'requests', focusType, focusId, caseId, title: `${item.title || 'Work item'} reopened from Home.`, detail: item.detail || item.next_action || 'Continue from the governed lane that owns this work.', actionLabel: primaryLabel })}>${escapeHtml(primaryLabel)}</button>`;
  const secondaryButton = item.kind === 'override'
    ? `<button class="action-button action-button-muted" type="button" data-override-action="veto" data-request-id="${escapeHtml(focusId || item.reference_id || '')}">Reject</button>`
    : `<button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({ view: item.view || 'requests', focusType, focusId, caseId, title: `${item.title || 'Work item'} reopened from Home.`, detail: item.detail || item.next_action || 'Continue from the governed lane that owns this work.', actionLabel: 'Details' })}>Details</button>`;
  return `
      <article class="command-action-card${featuredClass}${toneClass}" data-focus-key="${escapeHtml(buildFocusKey(focusType, focusId))}">
        <div class="hero-chip-row">${statusBadge(item.status_label || item.status || 'monitoring')}${statusBadge(item.priority_label || item.priority || 'normal')}</div>
        <strong>${escapeHtml(item.title || 'Governed work')}</strong>
        <p class="muted">${escapeHtml(item.detail || item.next_action || 'Continue the linked governed work.')}</p>
        ${item.why_now ? `<p class="muted small command-momentum-note">${escapeHtml(item.why_now)}</p>` : ''}
        <div class="command-action-meta">${escapeHtml(item.owner_label || 'Unassigned')} | ${escapeHtml(item.team_label || 'Operations')} | ${escapeHtml(item.case_id || 'No case')}</div>
        <div class="inline-actions">${primaryButton}${secondaryButton}</div>
      </article>
    `;
}

function renderAiFeedCard(item) {
  const featured = Boolean(item.featured);
  const toneClass = item.tone ? ` tone-${escapeHtml(item.tone)}` : '';
  const featuredClass = featured ? ' command-feed-card-featured' : '';
  const normalizedStatus = String(item.status || 'planned').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const stateClass = normalizedStatus ? ` command-feed-card-state-${escapeHtml(normalizedStatus)}` : '';
  const actionView = item.status === 'waiting_human' ? 'cases' : item.status === 'failed_closed' ? 'actions' : item.status === 'completed' ? 'documents' : 'actions';
  const actionViewLabel = VIEW_TITLES[actionView] || titleCase(actionView || 'actions');
  const actionLabel = item.status === 'waiting_human'
    ? 'Review handoff'
    : item.status === 'failed_closed'
      ? 'Inspect failure'
      : item.status === 'completed'
        ? 'Review result'
        : item.status === 'running'
          ? 'Watch action'
          : 'Details';
  const statusNote = item.status === 'waiting_human'
    ? 'A person now owns the next safe move.'
    : item.status === 'failed_closed'
      ? 'This path stopped behind a fail-closed boundary.'
      : item.status === 'completed'
        ? 'Outcome is recorded and ready for follow-through.'
        : item.status === 'running'
          ? 'AI is actively pushing this case forward.'
          : 'Visible for continuity across the governed runtime.';
  const momentumLabel = item.status === 'running'
    ? 'Momentum live'
    : item.status === 'waiting_human'
      ? 'Human boundary now'
      : item.status === 'failed_closed'
        ? 'Recovery needed'
        : item.status === 'completed'
          ? 'Follow-through ready'
          : 'Continuity visible';
  const ownerLabel = item.owner_label || (item.status === 'running'
    ? 'AI runtime'
    : item.status === 'waiting_human'
      ? 'Human director'
      : item.status === 'failed_closed'
        ? 'Recovery review'
        : item.status === 'completed'
          ? 'Follow-through lane'
          : 'Director watch');
  const consequenceNote = item.consequence_note || item.route_phase || statusNote;
  return `
      <article class="command-feed-card${toneClass}${stateClass}${featuredClass}">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">${escapeHtml(item.board_rank_label || titleCase(item.action_type || 'ai action'))}</div>
            <strong>${escapeHtml(item.label || item.action_type || 'AI action')}</strong>
          </div>
          <div class="hero-chip-row">${statusBadge(item.status || 'planned')}${statusBadge(item.tempo_badge || momentumLabel)}</div>
        </div>
        <div class="transition-route command-feed-route"><span class="transition-node">AI runtime</span><span class="transition-arrow">&rarr;</span><span class="transition-node transition-node-active">${escapeHtml(actionViewLabel)}</span></div>
        <p class="muted">${escapeHtml(item.activity_note || item.output_summary || item.next_action || 'Governed AI action is progressing inside the runtime.')}</p>
        <p class="muted small command-momentum-note">${escapeHtml(item.route_phase || statusNote)}</p>
        <div class="trace-box compact-trace command-feed-consequence-box"><strong>${escapeHtml(`If this pauses: ${ownerLabel}`)}</strong><p class="muted">${escapeHtml(consequenceNote)}</p></div>
        <div class="command-action-meta">${escapeHtml(item.case_id || 'No case')} | ${escapeHtml(ownerLabel)} | ${escapeHtml(shortTime(item.updated_at || item.created_at))}</div>
        <div class="inline-actions"><button class="action-button action-button-muted" type="button" ${buildViewJumpAttributes({ view: actionView, focusType: actionView === 'actions' ? 'action' : '', focusId: actionView === 'actions' ? (item.action_id || '') : '', caseId: item.case_id || '', title: `${item.label || 'AI action'} reopened from Home.`, detail: item.consequence_note || item.activity_note || item.next_action || 'Review the governed AI execution lane.', actionLabel })}>${escapeHtml(actionLabel)}</button></div>
      </article>
    `;
}

function renderDepartmentQuickAccessCard(item) {
  const filterValue = item.label || item.team_id || '';
  const contextNote = item.context_note || `${String(item.member_total || 0)} members | ${String(item.seat_total || 0)} seats`;
  const pressureLabel = item.pressure_label || (Number(item.assignment_total || 0) > 0 ? 'active queue' : 'ready lane');
  const pressureTone = pressureLabel === 'blocked path' ? 'danger' : pressureLabel === 'human boundary' || pressureLabel === 'active review' || Number(item.assignment_total || 0) > 0 ? 'warning' : 'success';
  const actionLabel = Number(item.assignment_total || 0) > 0 ? 'Open team queue' : 'Open team context';
  const leadLaneLabel = VIEW_TITLES[item.lead_view || 'requests'] || titleCase(item.lead_view || 'requests');
  const leadLaneButton = Number(item.assignment_total || 0) > 0 && item.lead_view
    ? renderViewJumpButton({
      view: item.lead_view || 'requests',
      label: 'Open lead lane',
      className: 'action-button action-button-muted',
      caseId: item.lead_case_id || '',
      title: `${item.label || item.team_id || 'Team'} reopened in ${leadLaneLabel}.`,
      detail: item.lead_move || contextNote,
      actionLabel: 'Open lead lane',
    })
    : '';
  return `
      <article class="command-department-card tone-${pressureTone}">
        <span class="command-summary-label">${escapeHtml(item.label || item.team_id || 'Team')}</span>
        <strong>${escapeHtml(String(item.assignment_total || 0))} active assignments</strong>
        <p class="muted">${escapeHtml(contextNote)}</p>
        ${item.lead_move ? `<div class="trace-box compact-trace"><strong>${escapeHtml(item.quest_label || 'Lead operation')}</strong><p class="muted">${escapeHtml(item.lead_move)}</p></div>` : ''}
        <div class="hero-chip-row">${statusBadge(pressureLabel)}${statusBadge(`${String(item.case_total || 0)} operations`)}${statusBadge(`${String(item.member_total || 0)} members`)}</div>
        <div class="inline-actions"><button class="action-button action-button-muted" type="button" data-team-quick-access="${escapeHtml(filterValue)}">${escapeHtml(actionLabel)}</button>${leadLaneButton}</div>
      </article>
    `;
}

function renderHomeQuickLink(item) {
  const label = item.label || VIEW_TITLES[item.view || 'overview'] || 'Open';
  return renderViewJumpButton({
    view: item.view || 'overview',
    label,
    className: 'action-button action-button-muted',
    title: `${label} reopened from Home.`,
    detail: 'Keep the command surface moving from one governed lane to the next without hunting through the dashboard.',
    actionLabel: label,
  });
}

function renderCommandEmptyState(title, note) {
  return `<article class="mini-card stack"><strong>${escapeHtml(title)}</strong><p class="muted">${escapeHtml(note)}</p></article>`;
}


function renderHomeSetupContinuation(snapshot) {
  if (!canAccessSetupAssistant()) return '';
  const firstRun = snapshot.first_run_readiness || {};
  const operations = snapshot.operations || {};
  const center = operations.first_run_action_center || {};
  const doctor = operations.quick_start_doctor || {};
  const proof = operations.usability_proof || {};
  const registration = snapshot.owner_registration || {};
  const requiredTotal = Number(center.required_total || firstRun.blockers_total || 0);
  const advisoryTotal = Number(center.items_total || firstRun.advisories_total || 0);
  if (Boolean(firstRun.ready) && requiredTotal <= 0 && String(doctor.status || 'ready') === 'ready') return '';
  return `
    <section class="card stack command-home-section">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Setup continuity</div>
          <h3 class="card-title">First-run assistant is still active</h3>
          <p class="card-subtitle">Pilot setup is not fully finished yet. Use the guided setup lane instead of hunting through Health, backups, and doctor details separately.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(firstRun.status || 'blocked')}${statusBadge(`${requiredTotal} required`)}</div>
      </div>
      <div class="command-summary-grid">
        ${renderHomePostureCard('Registration', registration.registered ? 'Active' : 'Missing', registration.organization_name || 'No organization yet', registration.registered ? 'success' : 'warning', 'Registration is the first anchor for setup continuity.', 'setup')}
        ${renderHomePostureCard('First-run status', formatStatusLabel(firstRun.status || 'blocked'), `${requiredTotal} required`, requiredTotal ? 'warning' : 'success', 'Registration, doctor, and readiness are grouped into one guided setup flow.', 'setup')}
        ${renderHomePostureCard('Doctor', formatStatusLabel(doctor.status || 'missing'), `${doctor.required_failed_total || 0} required failed`, doctor.required_failed_total ? 'warning' : 'success', 'Quick-start doctor shows whether the pilot path is truly usable.', 'setup')}
        ${renderHomePostureCard('Usability proof', formatStatusLabel(proof.status || 'missing'), `${proof.criteria_failed_total || 0} failed`, proof.criteria_failed_total ? 'warning' : 'accent', 'Pilot hardening uses evidence, not assumptions, before you call the runtime ready.', 'setup')}
      </div>
    </section>
  `;
}

function labelForOpsAction(action = '') {
  const normalized = String(action || '').trim();
  if (!normalized) return 'Run action';
  const known = {
    backup: 'Create backup',
    'usability-proof': 'Generate usability proof',
    'usability-proof-refresh': 'Refresh usability proof',
    'quick-start-doctor': 'Run quick-start doctor',
    'quick-start-doctor-refresh': 'Refresh doctor status',
    'first-run-action-center-sync': 'Run first-run sync',
    'first-run-action-center-refresh': 'Refresh first-run actions',
  };
  return known[normalized] || titleCase(normalized);
}

function renderSetupActionCard(item) {
  const detail = item.detail || item.message || item.note || item.description || 'Keep the setup lane moving until the runtime is pilot-ready.';
  const opsAction = String(item.ops_action || '').trim();
  const targetView = String(item.view || 'setup').trim() || 'setup';
  const primary = opsAction && can('ops.manage')
    ? `<button class="action-button" type="button" data-ops-action="${escapeHtml(opsAction)}">${escapeHtml(labelForOpsAction(opsAction))}</button>`
    : renderViewJumpButton({ view: targetView, label: 'Open details', className: 'action-button' });
  const secondary = targetView && targetView !== 'setup'
    ? renderViewJumpButton({
        view: targetView,
        label: `Open ${VIEW_TITLES[targetView] || titleCase(targetView)}`,
        className: 'action-button action-button-muted',
        title: `${item.title || 'Setup item'} reopened in ${VIEW_TITLES[targetView] || titleCase(targetView)}.`,
        detail,
      })
    : renderViewJumpButton({ view: 'overview', label: 'Back to Home', className: 'action-button action-button-muted' });
  return `
    <article class="command-action-card">
      <div class="hero-chip-row">${statusBadge(item.severity === 'required' ? 'blocked' : item.severity || 'monitoring')}${statusBadge(item.status || 'open')}</div>
      <strong>${escapeHtml(item.title || item.action_id || 'Setup action')}</strong>
      <p class="muted">${escapeHtml(detail)}</p>
      <div class="command-action-meta">${escapeHtml(item.action_id || 'setup')} | ${escapeHtml(item.ops_action || 'manual review')}</div>
      <div class="inline-actions">${primary}${secondary}</div>
    </article>
  `;
}

function renderSetupAssistant(snapshot) {
  const firstRun = snapshot.first_run_readiness || {};
  const operations = snapshot.operations || {};
  const center = operations.first_run_action_center || {};
  const doctor = operations.quick_start_doctor || {};
  const proof = operations.usability_proof || {};
  const registration = snapshot.owner_registration || {};
  const goLive = snapshot.go_live_readiness || {};
  const items = Array.isArray(center.items) ? center.items : [];
  const requiredItems = items.filter((item) => item.severity === 'required');
  const advisoryItems = items.filter((item) => item.severity !== 'required');
  const leadItems = (requiredItems.length ? requiredItems : advisoryItems).slice(0, 6);
  const readinessMessage = firstRun.ready
    ? 'Registration, doctor, and readiness are largely aligned. Finish pilot hardening and proof refresh before wider use.'
    : 'This page tells you what still blocks a serious pilot and what should happen next.';
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow">First-Run Assistant</div>
              <h3 class="hero-title">Setup, doctor, and pilot hardening in one guided lane</h3>
              <p class="hero-subtitle">Use this surface to finish registration, run diagnostics, review pilot blockers, and prove the runtime is ready without dropping into low-level operator plumbing first.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(firstRun.status || 'blocked')}${statusBadge(center.recommended_action || 'guided setup')}</div>
          </div>
          <div class="inline-actions">
            ${renderViewJumpButton({ view: 'overview', label: 'Back to Home', className: 'action-button' })}
            ${can('ops.manage') ? '<button class="action-button action-button-muted" type="button" data-ops-action="first-run-action-center-sync">Run Setup Sync</button>' : ''}
            ${can('ops.manage') ? '<button class="action-button action-button-muted" type="button" data-ops-action="quick-start-doctor-refresh">Refresh Doctor</button>' : ''}
          </div>
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">Current setup posture</div>
            <h3 class="card-title">${escapeHtml(firstRun.ready ? 'Pilot path is almost clear' : 'Pilot path still needs guided work')}</h3>
            <p class="card-subtitle">${escapeHtml(readinessMessage)}</p>
          </div>
          ${keyValue([
            ['Organization', registration.organization_name || '-'],
            ['Required actions', String(center.required_total || firstRun.blockers_total || 0)],
            ['Doctor', doctor.status || 'missing'],
            ['Usability proof', proof.status || 'missing'],
            ['Go-live', goLive.status || 'blocked'],
          ])}
        </article>
      </section>
      <section class="card stack">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Pilot readiness summary</div>
            <h3 class="card-title">What still blocks a serious pilot?</h3>
            <p class="card-subtitle">Keep the number of setup signals small and actionable. If this row is readable, the rest of the setup flow becomes manageable.</p>
          </div>
        </div>
        <div class="command-summary-grid">
          ${renderHomePostureCard('Registration', registration.registered ? 'Active' : 'Missing', registration.organization_name || 'No organization yet', registration.registered ? 'success' : 'warning', 'One registration code anchors the runtime identity before broader delegation begins.')}
          ${renderHomePostureCard('First-run status', formatStatusLabel(firstRun.status || 'blocked'), `${center.required_total || firstRun.blockers_total || 0} required`, firstRun.ready ? 'success' : 'warning', 'Blockers and advisories are grouped into one setup posture.')}
          ${renderHomePostureCard('Quick-start doctor', formatStatusLabel(doctor.status || 'missing'), `${doctor.required_failed_total || 0} required failed`, doctor.required_failed_total ? 'danger' : 'success', 'Diagnostics stay readable before you trust broader pilot rollout.')}
          ${renderHomePostureCard('Usability proof', formatStatusLabel(proof.status || 'missing'), `${proof.criteria_failed_total || 0} failed criteria`, proof.criteria_failed_total ? 'warning' : 'accent', 'Pilot hardening should be proven, not assumed.')}
        </div>
      </section>
      <section class="card stack">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Do these first</div>
            <h3 class="card-title">Guided setup actions</h3>
            <p class="card-subtitle">These are the next setup moves the system believes matter most before calling the runtime pilot-ready.</p>
          </div>
          <div class="hero-chip-row">${statusBadge(`${leadItems.length} visible`)}</div>
        </div>
        <div class="command-next-grid">${leadItems.length ? leadItems.map((item) => renderSetupActionCard(item)).join('') : renderCommandEmptyState('No guided setup actions are queued.', 'Open Home to continue normal governed work.')}</div>
      </section>
      <section class="split-grid">
        ${renderOwnerRegistrationPanel(snapshot.owner_registration || {}, { compact: false })}
        ${renderGoLiveReadinessCard(snapshot.go_live_readiness || {})}
      </section>
      ${renderOperationsSection(snapshot.operations || {})}
    </section>
  `;
}

function controlRoomToolLabel(tool) {
  return VIEW_TITLES[tool] || titleCase(String(tool || '').replaceAll('_', ' '));
}

function buildControlRoomCategoryGroups(snapshot) {
  const summary = snapshot.summary || {};
  const runtimeHealth = snapshot.runtime_health || {};
  const operations = snapshot.operations || {};
  const registration = snapshot.owner_registration || {};
  const firstRun = snapshot.first_run_readiness || {};
  const roleLibrary = runtimeHealth.role_library || {};
  const auditIntegrity = runtimeHealth.audit_integrity || {};
  const studioSummary = snapshot.role_private_studio?.summary || {};
  const integrationSummary = snapshot.integrations?.summary || {};
  const modelProviders = snapshot.model_providers || {};
  const backupSummary = operations.summary || {};
  const latestBackup = backupSummary.latest_backup || {};
  const retention = snapshot.retention || {};
  const sessions = Array.isArray(snapshot.sessions) ? snapshot.sessions : [];
  const evidenceSummary = snapshot.evidence_exports?.summary || {};
  const masterDataSummary = snapshot.master_data?.summary || {};
  const assignmentSummary = snapshot.assignment_queue?.summary || {};
  const searchSummary = snapshot.global_search?.summary || {};
  const studioStructural = runtimeHealth.studio_structural || snapshot.go_live_readiness?.studio_structural || {};
  const structuralAttention = Number(summary.studio_pt_oss_elevated_total || 0) + Number(summary.studio_pt_oss_critical_total || 0) + Number(summary.studio_pt_oss_blocking_issue_total || 0);
  return [
    {
      title: 'Setup & Onboarding',
      note: 'First-run setup, deployment identity, diagnostics, and pilot hardening stay here so Home can remain operationally simple.',
      items: [
        {
          tool: 'setup',
          label: 'Setup & Onboarding',
          value: firstRun.ready ? 'ready' : `${String(operations.first_run_action_center?.required_total || firstRun.blockers_total || 0)} required`,
          note: 'Setup Assistant, Quick-Start Doctor, usability proof, and first-run continuity in one advanced lane.',
          tone: firstRun.ready ? 'tone-success' : 'tone-warning',
          badges: [formatStatusLabel(firstRun.status || 'blocked')],
        },
        {
          tool: 'owner_registration',
          label: 'Owner Registration',
          value: registration.registered ? (registration.organization_name || 'registered') : 'sa-nom setup required',
          note: 'Private runtime identity, registration code, and executive-owner posture anchored during initial setup.',
          tone: registration.registered ? 'tone-success' : 'tone-warning',
          badges: [registration.registered ? 'registered' : 'missing', registration.deployment_mode || 'private'],
        },
      ].filter((item) => item.tool !== 'setup' || canAccessSetupAssistant()),
    },
    {
      title: 'AI Workforce & Roles',
      note: 'Role Private Studio and trusted role governance stay together because this is where the AI workforce is created, reviewed, and published.',
      items: [
        {
          tool: 'studio',
          label: 'Role Private Studio',
          value: `${String(studioSummary.publisher_ready_total || 0)} publish ready`,
          note: 'Operators fill a normal JD-style form, and the runtime turns it into PTAG, review posture, and publication governance behind the scenes.',
          tone: Number(studioSummary.trust_attention_total || 0) > 0 ? 'tone-warning' : 'tone-accent',
          badges: [Number(studioSummary.trust_attention_total || 0) > 0 ? 'trust attention' : 'studio live'],
        },
        {
          tool: 'policies',
          label: 'Role Library & Policies',
          value: roleLibrary.signature_status || roleLibrary.status || 'unknown',
          note: 'Trusted hats, manifest posture, hierarchy, authority boundaries, and publication trust remain visible here.',
          tone: String(roleLibrary.signature_status || roleLibrary.status || '').toLowerCase() === 'verified' ? 'tone-success' : 'tone-warning',
          badges: [roleLibrary.signature_status || roleLibrary.status || 'unknown'],
        },
      ],
    },
    {
      title: 'Structural Risk & Alignment',
      note: 'PT-OSS is a governance posture lane, not a setup wizard. It should stay visible as structural risk intelligence for advanced operators.',
      items: [
        {
          tool: 'structural_risk',
          label: 'Structural Risk & Alignment',
          value: structuralAttention > 0 ? `${String(structuralAttention)} risk signals` : 'monitoring',
          note: 'PT-OSS posture today, with Global Harmony and deeper alignment signals anchored in this same governance lane as data becomes active.',
          tone: structuralAttention > 0 ? 'tone-warning' : 'tone-success',
          badges: [summary.studio_pt_oss_critical_total ? 'critical posture' : summary.studio_pt_oss_elevated_total ? 'elevated posture' : 'healthy watch'],
        },
      ],
    },
    {
      title: 'Trust & Evidence',
      note: 'Use these tools when you must prove what happened, review export posture, or verify that trust and evidence continuity still hold.',
      items: [
        {
          tool: 'audit',
          label: 'Audit Trail',
          value: auditIntegrity.status || 'unknown',
          note: 'Audit chain integrity, tamper-evident history, and operator-readable trust posture.',
          tone: String(auditIntegrity.status || '').toLowerCase() === 'verified' ? 'tone-success' : 'tone-warning',
          badges: [auditIntegrity.status || 'unknown'],
        },
        {
          tool: 'evidence_exports',
          label: 'Evidence Exports',
          value: Number(evidenceSummary.exports_total || 0) > 0 ? `${String(evidenceSummary.exports_total || 0)} exports` : 'monitoring',
          note: 'Evidence packs, workflow proof bundles, export posture, and trusted mismatch attention.',
          tone: Number(evidenceSummary.attention_total || 0) > 0 || Number(evidenceSummary.trusted_role_mismatch_total || 0) > 0 ? 'tone-warning' : 'tone-accent',
          badges: [evidenceSummary.posture || 'unknown'],
        },
      ],
    },
    {
      title: 'Documents & Records',
      note: 'Retention, legal hold, and governed records live here instead of the normal document work surface.',
      items: [
        {
          tool: 'retention',
          label: 'Retention & Records',
          value: Number(retention.expired_candidate_total || 0) > 0 ? `${String(retention.expired_candidate_total || 0)} expiring` : 'monitoring',
          note: 'Retention windows, legal holds, archive posture, and governed records pressure.',
          tone: Number(retention.hold_blocked_total || 0) > 0 || Number(retention.expired_candidate_total || 0) > 0 ? 'tone-warning' : 'tone-accent',
          badges: [Number(retention.hold_blocked_total || 0) > 0 ? 'hold active' : 'records clear'],
        },
      ],
    },
    {
      title: 'Runtime & Recovery',
      note: 'Health, recovery bundles, diagnostics, and operational resilience belong here because they are advanced operator signals, not Home clutter.',
      items: [
        {
          tool: 'health',
          label: 'Runtime Health',
          value: runtimeHealth.status || 'unknown',
          note: 'Deployment, storage, runtime stores, diagnostics, and infrastructure posture.',
          tone: String(runtimeHealth.status || '').toLowerCase() === 'ok' ? 'tone-success' : 'tone-warning',
          badges: [runtimeHealth.status || 'unknown'],
        },
        {
          tool: 'backup_restore',
          label: 'Backup & Restore',
          value: latestBackup.backup_id || `${String(backupSummary.backups_total || 0)} bundles`,
          note: 'Recovery bundles, restore guidance, performance baseline, and pilot-hardening artifacts.',
          tone: latestBackup.backup_id ? 'tone-accent' : 'tone-warning',
          badges: [latestBackup.backup_id ? 'backup ready' : 'backup needed'],
        },
      ],
    },
    {
      title: 'Integrations & Providers',
      note: 'Outbound delivery, notification routing, and model provider readiness should stay grouped inside one advanced governance section.',
      items: [
        {
          tool: 'integrations',
          label: 'Integrations',
          value: Number(integrationSummary.active_targets || 0) > 0 ? `${String(integrationSummary.active_targets || 0)} active targets` : 'setup needed',
          note: 'Targets, delivery posture, outbox pressure, and outbound governance routing.',
          tone: Number(integrationSummary.failed_total || 0) > 0 ? 'tone-warning' : 'tone-accent',
          badges: [Number(integrationSummary.failed_total || 0) > 0 ? 'delivery pressure' : 'routing posture'],
        },
        {
          tool: 'model_providers',
          label: 'Model Providers',
          value: Number(modelProviders.configured_providers || 0) > 0 ? `${String(modelProviders.configured_providers || 0)} configured` : 'setup needed',
          note: 'Default provider readiness and AI workforce execution path inside the private-first boundary.',
          tone: Number(modelProviders.configured_providers || 0) > 0 && modelProviders.default_provider_ready !== false ? 'tone-success' : 'tone-warning',
          badges: [modelProviders.default_provider || 'no default'],
        },
      ],
    },
    {
      title: 'Access & Security',
      note: 'Session posture, authority boundaries, and protected resource pressure stay here for advanced governance review.',
      items: [
        {
          tool: 'sessions',
          label: 'Sessions',
          value: sessions.length ? `${String(sessions.length)} active` : 'clear',
          note: 'Issued sessions, expiry windows, continuity, and revocation posture.',
          tone: sessions.length ? 'tone-accent' : 'tone-success',
          badges: [sessions.length ? 'active access' : 'no pressure'],
        },
        {
          tool: 'conflicts',
          label: 'Authority Guard & Locks',
          value: `${String(summary.active_locks || 0)} items`,
          note: 'Contention, blocked execution, protected resources, and advanced pressure in governed lanes.',
          tone: Number(summary.active_locks || 0) > 0 ? 'tone-warning' : 'tone-success',
          badges: [Number(summary.active_locks || 0) > 0 ? 'attention' : 'clear'],
        },
      ],
    },
    {
      title: 'Master Data & Routing',
      note: 'People, teams, assignments, and searchable routing posture should be maintained here as governance infrastructure, not treated as raw directory plumbing.',
      items: [
        {
          tool: 'master_data',
          label: 'Master Data & Routing',
          value: Number(masterDataSummary.people_total || 0) > 0 ? `${String(masterDataSummary.people_total || 0)} people` : 'setup needed',
          note: 'Organization structure, assignment queue posture, team routing, and searchable governance continuity.',
          tone: Number(assignmentSummary.human_required_total || 0) > 0 ? 'tone-warning' : 'tone-accent',
          badges: [searchSummary.search_ready ? 'search ready' : 'index warming'],
        },
      ],
    },
    {
      title: 'Admin Settings',
      note: 'One place for organization identity, access, provider, routing, and operating posture when a founder or admin needs the current setting surface.',
      items: [
        {
          tool: 'admin_settings',
          label: 'Admin Settings',
          value: registration.registered ? (registration.organization_name || 'registered') : 'setup needed',
          note: 'Organization identity, access posture, provider posture, and routing configuration summary.',
          tone: registration.registered ? 'tone-accent' : 'tone-warning',
          badges: [registration.registered ? 'registered' : 'needs setup'],
        },
      ],
    },
  ];
}

function controlRoomPrimaryActionLabel(tool) {
  const labels = {
    setup: 'Continue setup',
    owner_registration: 'Review setup',
    studio: 'Open Studio',
    policies: 'Open library',
    structural_risk: 'Review posture',
    audit: 'Open audit',
    evidence_exports: 'Review trust',
    retention: 'Review records',
    health: 'Check runtime',
    backup_restore: 'Open recovery',
    integrations: 'Open integrations',
    model_providers: 'Open providers',
    sessions: 'Open sessions',
    conflicts: 'Review pressure',
    master_data: 'Open routing',
    admin_settings: 'Open settings',
  };
  return labels[tool] || 'Open';
}

function findControlRoomToolItem(groups, tool) {
  return groups.flatMap((group) => group.items || []).find((item) => item.tool === tool) || null;
}

function buildControlRoomMissionItems(snapshot, groups) {
  const preferredTools = canAccessSetupAssistant()
    ? ['setup', 'studio', 'structural_risk', 'evidence_exports', 'health']
    : ['studio', 'structural_risk', 'evidence_exports', 'health', 'master_data'];
  const noteOverrides = {
    setup: 'Finish owner bootstrap, first-run guidance, and doctor before broader pilot delegation.',
    studio: 'Create or revise governed AI workforce roles from a normal JD-style input form.',
    structural_risk: 'Use PT-OSS and alignment posture before trusted publication or wider delegation.',
    evidence_exports: 'Review proof, trusted registry posture, and export attention before calling anything auditor-ready.',
    health: 'Check diagnostics, backup posture, and recovery readiness before risky changes.',
    master_data: 'Keep people, teams, search, and routing calm before work drifts across the org.',
  };
  return preferredTools
    .map((tool) => findControlRoomToolItem(groups, tool))
    .filter(Boolean)
    .map((item) => ({
      ...item,
      note: noteOverrides[item.tool] || item.note,
      actionLabel: controlRoomPrimaryActionLabel(item.tool),
    }));
}

function renderControlRoomMissionCard(item, currentTool) {
  const isCurrent = currentTool === item.tool;
  const badges = Array.isArray(item.badges) ? item.badges.filter(Boolean) : [];
  return `
    <article class="command-summary-card control-room-mission-card ${escapeHtml(item.tone || 'tone-accent')}${isCurrent ? ' is-active' : ''}">
      <span class="command-summary-label">${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
      <p class="muted">${escapeHtml(item.note)}</p>
      ${badges.length ? `<div class="hero-chip-row">${badges.map((badge) => statusBadge(badge)).join('')}</div>` : ''}
      <div class="inline-actions">
        <button class="action-button${isCurrent ? ' action-button-muted' : ''}" type="button" data-control-room-tool="${escapeHtml(item.tool)}">${escapeHtml(isCurrent ? 'Current lane' : item.actionLabel || controlRoomPrimaryActionLabel(item.tool))}</button>
      </div>
    </article>
  `;
}

function renderControlRoomMissionSection(snapshot, groups, currentTool) {
  const missionItems = buildControlRoomMissionItems(snapshot, groups);
  if (!missionItems.length) return '';
  return `
    <section class="card stack control-room-mission-shell">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Mission control priorities</div>
          <h3 class="card-title">Open the right advanced lane in one tap</h3>
          <p class="card-subtitle">Control Room should point straight to setup, roles, structural risk, trust, and recovery instead of making tablet operators hunt through long panels.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${missionItems.length} primary lanes`)}</div>
      </div>
      <div class="control-room-mission-grid">
        ${missionItems.map((item) => renderControlRoomMissionCard(item, currentTool)).join('')}
      </div>
    </section>
  `;
}

function buildControlRoomActionDeck(snapshot) {
  const summary = snapshot.summary || {};
  const firstRun = snapshot.first_run_readiness || {};
  const firstRunCenter = snapshot.operations?.first_run_action_center || {};
  const runtimeHealth = snapshot.runtime_health || {};
  const studioSummary = snapshot.role_private_studio?.summary || {};
  const evidenceSummary = snapshot.evidence_exports?.summary || {};
  const integrationSummary = snapshot.integrations?.summary || {};

  const setupRequired = Number(firstRunCenter.required_total || firstRun.blockers_total || 0);
  const studioTrustAttention = Number(studioSummary.trust_attention_total || 0);
  const studioPublishReady = Number(studioSummary.publisher_ready_total || 0);
  const structuralAttention = Number(summary.studio_pt_oss_blocking_issue_total || 0)
    + Number(summary.studio_pt_oss_critical_total || 0)
    + Number(summary.studio_pt_oss_elevated_total || 0);
  const trustAttention = Number(evidenceSummary.attention_total || 0)
    + Number(evidenceSummary.trusted_role_mismatch_total || 0);
  const runtimeWarnings = Number(runtimeHealth.warning_total || runtimeHealth.attention_total || 0);
  const integrationFailures = Number(integrationSummary.failed_total || 0);

  const items = [
    {
      tool: 'setup',
      label: 'Setup Runway',
      value: setupRequired > 0 ? `${setupRequired} required` : 'ready',
      note: 'Setup Assistant, First-Run Action Center, and Quick-Start Doctor stay in one guided lane.',
      tone: setupRequired > 0 ? 'tone-warning' : 'tone-success',
      actionLabel: setupRequired > 0 ? 'Continue setup' : 'Review setup',
      priority: setupRequired > 0 ? 110 : 42,
    },
    {
      tool: 'studio',
      label: 'Role Private Studio',
      value: studioTrustAttention > 0 ? `${studioTrustAttention} trust alerts` : `${studioPublishReady} publish ready`,
      note: 'Create role specs from normal JD input and let the runtime compile governed PTAG in the background.',
      tone: studioTrustAttention > 0 ? 'tone-warning' : studioPublishReady > 0 ? 'tone-accent' : 'tone-success',
      actionLabel: studioTrustAttention > 0 ? 'Resolve trust alerts' : 'Open studio',
      priority: studioTrustAttention > 0 ? 100 : studioPublishReady > 0 ? 78 : 36,
    },
    {
      tool: 'structural_risk',
      label: 'Structural Risk & Alignment',
      value: structuralAttention > 0 ? `${structuralAttention} risk signals` : 'stable watch',
      note: 'PT-OSS posture and Global Harmony alignment are reviewed together before trusted publication.',
      tone: structuralAttention > 0 ? 'tone-warning' : 'tone-success',
      actionLabel: structuralAttention > 0 ? 'Review posture now' : 'Review posture',
      priority: structuralAttention > 0 ? 95 : 44,
    },
    {
      tool: 'evidence_exports',
      label: 'Trust & Evidence',
      value: trustAttention > 0 ? `${trustAttention} attention` : 'continuity clear',
      note: 'Audit chain, evidence packs, and trusted registry posture should stay export-ready.',
      tone: trustAttention > 0 ? 'tone-warning' : 'tone-accent',
      actionLabel: trustAttention > 0 ? 'Review trust now' : 'Open trust lane',
      priority: trustAttention > 0 ? 92 : 40,
    },
    {
      tool: 'health',
      label: 'Runtime & Recovery',
      value: runtimeWarnings > 0 ? `${runtimeWarnings} warnings` : formatStatusLabel(runtimeHealth.status || 'ok'),
      note: 'Diagnostics, backup posture, and recovery readiness should stay green before risky rollout moves.',
      tone: runtimeWarnings > 0 || String(runtimeHealth.status || '').toLowerCase() !== 'ok' ? 'tone-warning' : 'tone-success',
      actionLabel: runtimeWarnings > 0 ? 'Check runtime now' : 'Open runtime',
      priority: runtimeWarnings > 0 ? 90 : 38,
    },
    {
      tool: 'integrations',
      label: 'Integrations & Providers',
      value: integrationFailures > 0 ? `${integrationFailures} failed` : `${Number(integrationSummary.active_targets || 0)} active targets`,
      note: 'Outbound delivery pressure should be handled before delegation expands to external channels.',
      tone: integrationFailures > 0 ? 'tone-warning' : 'tone-accent',
      actionLabel: integrationFailures > 0 ? 'Fix delivery pressure' : 'Open integrations',
      priority: integrationFailures > 0 ? 88 : 34,
    },
  ].filter((item) => item.tool !== 'setup' || canAccessSetupAssistant());

  return items.sort((left, right) => right.priority - left.priority).slice(0, 4);
}

function renderControlRoomActionCard(item, currentTool) {
  const isCurrent = currentTool === item.tool;
  return `
    <article class="command-summary-card control-room-action-card ${escapeHtml(item.tone || 'tone-accent')}${isCurrent ? ' is-active' : ''}">
      <span class="command-summary-label">${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
      <p class="muted">${escapeHtml(item.note)}</p>
      <div class="inline-actions">
        <button class="action-button${isCurrent ? ' action-button-muted' : ''}" type="button" data-control-room-tool="${escapeHtml(item.tool)}">${escapeHtml(isCurrent ? 'Current lane' : item.actionLabel || controlRoomPrimaryActionLabel(item.tool))}</button>
      </div>
    </article>
  `;
}

function renderControlRoomActionSection(snapshot, currentTool) {
  const cards = buildControlRoomActionDeck(snapshot);
  if (!cards.length) return '';
  return `
    <section class="card stack control-room-action-shell">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Action center</div>
          <h3 class="card-title">Immediate moves for this governance session</h3>
          <p class="card-subtitle">Less reading, more action. Open the next high-impact lane directly from this mission board.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${cards.length} live actions`)}</div>
      </div>
      <div class="control-room-action-grid">
        ${cards.map((item) => renderControlRoomActionCard(item, currentTool)).join('')}
      </div>
    </section>
  `;
}

function renderControlRoomCategorySection(group, currentTool) {
  return `
    <section class="card stack control-room-category">
      <div class="control-room-category-head">
        <div>
          <div class="eyebrow muted">${escapeHtml(group.title)}</div>
          <h3 class="card-title">${escapeHtml(group.title)}</h3>
          <p class="card-subtitle">${escapeHtml(group.note)}</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${group.items.length} lanes`)}</div>
      </div>
      <div class="control-room-tool-grid">
        ${group.items.map((item) => renderControlRoomToolCard(item, currentTool)).join('')}
      </div>
    </section>
  `;
}

function renderControlRoomToolCard(item, currentTool) {
  const isCurrent = currentTool === item.tool;
  const badges = Array.isArray(item.badges) ? item.badges.filter(Boolean) : [];
  return `
    <article class="command-summary-card control-room-tool-card ${escapeHtml(item.tone || 'tone-accent')}${isCurrent ? ' is-active' : ''}">
      <span class="command-summary-label">${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
      <p class="muted">${escapeHtml(item.note)}</p>
      ${badges.length ? `<div class="hero-chip-row">${badges.map((badge) => statusBadge(badge)).join('')}</div>` : ''}
      <div class="inline-actions">
        <button class="action-button${isCurrent ? ' action-button-muted' : ''}" type="button" data-control-room-tool="${escapeHtml(item.tool)}">${escapeHtml(isCurrent ? 'Current lane' : controlRoomPrimaryActionLabel(item.tool))}</button>
      </div>
    </article>
  `;
}

function renderControlRoom(snapshot) {
  const currentTool = state.controlRoomTool || getInitialControlRoomTool();
  const groups = buildControlRoomCategoryGroups(snapshot);
  const currentToolLabel = controlRoomToolLabel(currentTool);
  const currentGroup = groups.find((group) => group.items.some((item) => item.tool === currentTool));
  const currentItem = findControlRoomToolItem(groups, currentTool);
  const embedded = renderControlRoomTool(snapshot, currentTool);
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow">Control Room</div>
              <h3 class="hero-title">Advanced governance setup, trust, and recovery in one protected mission console</h3>
              <p class="hero-subtitle">Home stays simple for normal users. Control Room is where advanced operators configure, verify, publish, recover, and govern the private-first runtime.</p>
            </div>
            <div class="hero-chip-row">${statusBadge('advanced governance')}${statusBadge(state.session?.role_name || 'admin')}</div>
          </div>
          <div class="inline-actions">
            ${renderViewJumpButton({ view: 'overview', label: 'Back to Home', className: 'action-button action-button-muted' })}
            ${canAccessSetupAssistant() ? '<button class="action-button action-button-muted" type="button" data-control-room-tool="setup">Open Setup & Onboarding</button>' : ''}
            <button class="action-button" type="button" data-control-room-tool="studio">Open Role Private Studio</button>
          </div>
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">Current focus</div>
            <h3 class="card-title">${escapeHtml(currentToolLabel)}</h3>
            <p class="card-subtitle">${escapeHtml(currentItem?.note || (currentGroup ? `${currentGroup.title} is the active Control Room section.` : 'Use the sections below to choose the advanced tool you need next.'))}</p>
          </div>
          <div class="control-room-focus-grid">
            ${renderCommandEmptyState('Current group', currentGroup?.title || 'Advanced governance')}
            ${renderCommandEmptyState('Next operator move', controlRoomPrimaryActionLabel(currentTool))}
            ${renderCommandEmptyState('Home boundary', 'Keep routine work on Home')}
          </div>
          <div class="inline-actions">
            <button class="action-button action-button-muted" type="button" data-control-room-tool="health">Open Runtime & Recovery</button>
            <button class="action-button action-button-muted" type="button" data-control-room-tool="evidence_exports">Open Trust & Evidence</button>
          </div>
        </article>
      </section>
      ${renderControlRoomActionSection(snapshot, currentTool)}
      ${renderControlRoomMissionSection(snapshot, groups, currentTool)}
      <section class="control-room-groups">
        ${groups.map((group) => renderControlRoomCategorySection(group, currentTool)).join('')}
      </section>
      <section class="stack gap-md control-room-detail-shell">${embedded}</section>
    </section>
  `;
}

function renderControlRoomTool(snapshot, tool) {
  if (tool === 'setup') return renderSetupAssistant(snapshot);
  if (tool === 'studio') return renderStudio(snapshot.role_private_studio || { summary: {}, requests: [], template: {}, examples: [] });
  if (tool === 'structural_risk') return renderStructuralRiskTool(snapshot);
  if (tool === 'audit') return renderAudit(snapshot);
  if (tool === 'evidence_exports') return renderEvidenceExportsTool(snapshot);
  if (tool === 'policies') return renderPolicies(snapshot.roles || []);
  if (tool === 'retention') return renderRetentionTool(snapshot);
  if (tool === 'health') return renderHealth(snapshot.runtime_health, snapshot.available_profiles || [], snapshot.retention || null, snapshot.operations || null, snapshot.integrations || null, snapshot.operator_notification_center || null, snapshot.operator_notification_delivery_readiness || null);
  if (tool === 'backup_restore') return renderBackupRestoreTool(snapshot);
  if (tool === 'integrations') return renderIntegrationsTool(snapshot);
  if (tool === 'model_providers') return renderModelProvidersTool(snapshot);
  if (tool === 'sessions') return wrapTableCard('Sessions', sessionTable(snapshot.sessions || []), 'Short-lived runtime sessions and revocation state for advanced governance review.');
  if (tool === 'conflicts') return renderConflicts(snapshot);
  if (tool === 'master_data') return renderMasterDataGovernanceTool(snapshot);
  if (tool === 'admin_settings') return renderAdminSettingsTool(snapshot);
  if (tool === 'owner_registration') return renderOwnerRegistrationTool(snapshot);
  return renderHealth(snapshot.runtime_health, snapshot.available_profiles || [], snapshot.retention || null, snapshot.operations || null, snapshot.integrations || null, snapshot.operator_notification_center || null, snapshot.operator_notification_delivery_readiness || null);
}

function renderStructuralRiskTool(snapshot) {
  const summary = snapshot.summary || {};
  const studioSummary = snapshot.role_private_studio?.summary || {};
  const studioStructural = snapshot.runtime_health?.studio_structural || snapshot.go_live_readiness?.studio_structural || {};
  const guardedTotal = Number(summary.studio_structural_guarded_total || studioSummary.structural_guarded_total || 0);
  const blockedTotal = Number(summary.studio_structural_blocked_total || studioSummary.structural_blocked_total || 0);
  const readyTotal = Number(summary.studio_structural_ready_total || studioSummary.structural_ready_total || 0);
  const elevatedTotal = Number(summary.studio_pt_oss_elevated_total || studioSummary.pt_oss_elevated_total || 0);
  const criticalTotal = Number(summary.studio_pt_oss_critical_total || studioSummary.pt_oss_critical_total || 0);
  const blockingIssueTotal = Number(summary.studio_pt_oss_blocking_issue_total || studioSummary.pt_oss_blocking_issue_total || 0);
  const healthyTotal = Number(summary.studio_pt_oss_healthy_total || studioSummary.pt_oss_healthy_total || 0);
  const publicSectorTotal = Number(summary.studio_pt_oss_public_sector_total || studioSummary.pt_oss_public_sector_mode_total || 0);
  const posture = studioStructural.status || (criticalTotal > 0 ? 'critical' : elevatedTotal > 0 || blockingIssueTotal > 0 ? 'elevated' : guardedTotal > 0 ? 'watch' : 'healthy');
  const harmony = snapshot.global_harmony || {};
  const harmonySummary = harmony.summary || {};
  const harmonySignals = Number(harmonySummary.signal_total || harmony.signal_total || summary.global_harmony_signal_total || 0);
  const harmonyStatusRaw = String(harmonySummary.status || harmony.status || summary.global_harmony_status || '').trim();
  const harmonyStatus = harmonyStatusRaw || (harmonySignals > 0 ? 'active' : 'awaiting data');
  const harmonyReady = harmonyStatus !== 'awaiting data' || harmonySignals > 0;
  const harmonyNote = String(
    harmonySummary.note
    || harmony.note
    || (harmonyReady
      ? 'Global Harmony telemetry is active in this same structural lane.'
      : 'Global Harmony telemetry will appear here once alignment data is connected.')
  ).trim();
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Structural Risk &amp; Alignment</div>
              <h2 class="hero-title">PT-OSS and Global Harmony alignment belong in one structural governance lane.</h2>
              <p class="hero-subtitle">Use this lane to understand whether the AI workforce is calm enough for trusted publication, delegated execution, and alignment-sensitive change before advanced operators approve the next move.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(posture)}${statusBadge(publicSectorTotal > 0 ? 'public sector mode' : 'private sector mix')}</div>
          </div>
          <div class="metrics-grid metrics-grid-luxury">
            ${metricCard('Guarded drafts', guardedTotal, guardedTotal > 0 ? 'warning' : 'success', 'Draft hats that still need structural review before trusted publication.')}
            ${metricCard('Blocked drafts', blockedTotal, blockedTotal > 0 ? 'danger' : 'success', 'Role packs blocked by structural readiness or fragility concerns.')}
            ${metricCard('Elevated posture', elevatedTotal, elevatedTotal > 0 ? 'warning' : 'success', 'PT-OSS elevated signals that still need operator attention.')}
            ${metricCard('Critical posture', criticalTotal, criticalTotal > 0 ? 'danger' : 'success', 'Highest structural risk posture currently visible across governed hats.')}
            ${metricCard('Blocking issues', blockingIssueTotal, blockingIssueTotal > 0 ? 'warning' : 'success', 'Explicit PT-OSS blocking issues that stop publication or governed movement.')}
            ${metricCard('Healthy lanes', healthyTotal || readyTotal, healthyTotal || readyTotal ? 'success' : 'default', 'Hats and structural lanes that are calm enough to move without extra pressure.')}
          </div>
          <div class="inline-actions">
            <button class="action-button" type="button" data-control-room-tool="studio">Open Role Private Studio</button>
            <button class="action-button action-button-muted" type="button" data-control-room-tool="policies">Open Role Library &amp; Policies</button>
          </div>
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">What this means</div>
            <h3 class="card-title">Structural posture should guide publication and delegation</h3>
            <p class="card-subtitle">PT-OSS belongs in Control Room because it explains why a role is structurally safe, guarded, or blocked before advanced operators trust it in the real organization.</p>
          </div>
          ${keyValue([
            ['Current posture', formatStatusLabel(posture)],
            ['Guarded total', String(guardedTotal)],
            ['Blocked total', String(blockedTotal)],
            ['Critical total', String(criticalTotal)],
            ['Public-sector mode hats', String(publicSectorTotal)],
            ['Global Harmony status', formatStatusLabel(harmonyStatus)],
            ['Global Harmony signals', String(harmonySignals)],
            ['Structural note', studioStructural.note || studioStructural.message || 'PT-OSS posture is active on this runtime.'],
          ])}
        </article>
      </section>
      <section class="split-grid">
        <article class="card stack">
          <div>
            <div class="eyebrow muted">Publication pressure</div>
            <h3 class="card-title">What must settle before the next trusted publish</h3>
            <p class="card-subtitle">Advanced operators should review guarded or blocked drafts before publication, especially when elevated or critical PT-OSS signals are still live.</p>
          </div>
          <div class="hero-split">
            <div class="trace-box"><strong>Guarded lane</strong><p class="muted">${escapeHtml(guardedTotal > 0 ? `${guardedTotal} draft hats still require structural review before trusted release.` : 'No guarded drafts are waiting right now.')}</p></div>
            <div class="trace-box"><strong>Blocked lane</strong><p class="muted">${escapeHtml(blockedTotal > 0 ? `${blockedTotal} hats are blocked because structural pressure still prevents safe publication.` : 'No blocked studio drafts are visible right now.')}</p></div>
          </div>
        </article>
        <article class="card stack">
          <div>
            <div class="eyebrow muted">Alignment home</div>
            <h3 class="card-title">Global Harmony has a clear home in this same lane</h3>
            <p class="card-subtitle">PT-OSS stays visible as the structural baseline. When alignment telemetry is connected, Global Harmony signals appear here without creating a second governance home.</p>
          </div>
          <div class="hero-chip-row">${statusBadge('pt-oss visible')}${statusBadge(harmonyStatus)}</div>
          <div class="trace-box compact-trace"><strong>Alignment signal</strong><p class="muted">${escapeHtml(harmonyNote)}</p></div>
        </article>
      </section>
    </section>
  `;
}
function renderEvidenceExportsTool(snapshot) {
  const evidence = snapshot.evidence_exports || { summary: {}, exports: [], workflow_proofs: [] };
  const summary = evidence.summary || {};
  const exports = Array.isArray(evidence.exports) ? evidence.exports : [];
  const proofs = Array.isArray(evidence.workflow_proofs) ? evidence.workflow_proofs : [];
  const latestExport = summary.latest_export || exports[0] || {};
  const latestProof = summary.latest_workflow_proof || proofs[0] || {};
  const auditIntegrity = snapshot.runtime_health?.audit_integrity || {};
  const trustedRegistry = snapshot.runtime_health?.trusted_registry || {};
  const exportCards = exports.slice(0, 4).map((item) => {
    const exportId = item.evidence_pack_id || item.export_id || item.bundle_id || 'evidence export';
    return `
      <article class="trace-box compact-trace">
        <div class="hero-chip-row">${statusBadge(item.posture || 'ready')}</div>
        <strong>${escapeHtml(exportId)}</strong>
        ${keyValue([
          ['Created', item.created_at || item.exported_at || '-'],
          ['Requested by', item.requested_by || item.exported_by || '-'],
          ['Workflow proof total', String(item.workflow_proof_total || 0)],
          ['Trusted mismatches', String(item.trusted_role_mismatch_total || 0)],
          ['Export path', item.export_path || '-'],
        ])}
      </article>
    `;
  }).join('');
  const proofCards = proofs.slice(0, 4).map((item) => {
    const workflowId = item.workflow_id || item.bundle_id || 'workflow proof';
    return `
      <article class="trace-box compact-trace">
        <div class="hero-chip-row">${statusBadge(item.posture || 'ready')}</div>
        <strong>${escapeHtml(workflowId)}</strong>
        ${keyValue([
          ['Created', item.created_at || '-'],
          ['Requested by', item.requested_by || '-'],
          ['Human sessions', String(item.human_session_total || 0)],
          ['Audit events', String(item.audit_event_total || 0)],
          ['Export path', item.export_path || '-'],
        ])}
      </article>
    `;
  }).join('');
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Trust &amp; Evidence</div>
              <h2 class="hero-title">Evidence exports and workflow proof bundles keep trust readable without leaking low-level identifiers onto Home.</h2>
              <p class="hero-subtitle">Use this advanced lane when a founder, admin, or IT operator needs to confirm export posture, workflow proof continuity, or trusted mismatch attention before treating a case as auditor-ready.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(summary.posture || auditIntegrity.status || 'unknown')}${statusBadge(trustedRegistry.signature_status || trustedRegistry.status || 'registry status')}</div>
          </div>
          <div class="metrics-grid metrics-grid-luxury">
            ${metricCard('Evidence exports', summary.exports_total || 0, Number(summary.exports_total || 0) > 0 ? 'accent' : 'default', 'Exported evidence packs currently visible from the private runtime.')}
            ${metricCard('Workflow proofs', summary.workflow_proof_total || 0, Number(summary.workflow_proof_total || 0) > 0 ? 'accent' : 'default', 'Workflow proof bundles that already tie human, document, and audit context together.')}
            ${metricCard('Attention', summary.attention_total || 0, Number(summary.attention_total || 0) > 0 ? 'warning' : 'success', 'Evidence or proof exports that still require operator review.')}
            ${metricCard('Trusted mismatches', summary.trusted_role_mismatch_total || 0, Number(summary.trusted_role_mismatch_total || 0) > 0 ? 'danger' : 'success', 'Exports that surfaced trust drift between live role material and the trusted registry manifest.')}
          </div>
          <div class="inline-actions">
            <button class="action-button" type="button" data-control-room-tool="audit">Open Audit Trail</button>
            <button class="action-button action-button-muted" type="button" data-control-room-tool="policies">Open Role Library &amp; Policies</button>
          </div>
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">Latest trust signals</div>
            <h3 class="card-title">The newest export and proof bundle stay visible together</h3>
            <p class="card-subtitle">Evidence should read as one trust story. Export posture, workflow proof, audit integrity, and trusted registry posture belong in the same advanced decision lane.</p>
          </div>
          ${keyValue([
            ['Audit integrity', auditIntegrity.status || '-'],
            ['Registry signature', trustedRegistry.signature_status || trustedRegistry.status || '-'],
            ['Latest export', latestExport.evidence_pack_id || latestExport.export_id || latestExport.bundle_id || '-'],
            ['Latest proof', latestProof.workflow_id || latestProof.bundle_id || '-'],
            ['Latest export posture', latestExport.posture || summary.posture || '-'],
            ['Latest proof posture', latestProof.posture || '-'],
          ])}
        </article>
      </section>
      <section class="card-grid">
        <article class="card stack">
          <div>
            <div class="eyebrow muted">Recent exports</div>
            <h3 class="card-title">Evidence packs</h3>
            <p class="card-subtitle">Use exports when you need a portable bundle of audit, trust, and workflow material.</p>
          </div>
          ${exportCards || emptyState('No evidence exports have been created yet.')}
        </article>
        <article class="card stack">
          <div>
            <div class="eyebrow muted">Recent workflow proofs</div>
            <h3 class="card-title">Workflow proof bundles</h3>
            <p class="card-subtitle">Workflow proof bundles connect document, audit, human handoff, and runtime action continuity into one review-ready package.</p>
          </div>
          ${proofCards || emptyState('No workflow proof bundles have been created yet.')}
        </article>
      </section>
    </section>
  `;
}
function renderMasterDataGovernanceTool(snapshot) {
  const masterData = snapshot.master_data || { summary: {}, people: [], seats: [], teams: [] };
  const masterSummary = masterData.summary || {};
  const assignmentQueue = snapshot.assignment_queue || { summary: {}, items: [] };
  const assignmentSummary = assignmentQueue.summary || {};
  const assignmentItems = Array.isArray(assignmentQueue.items) ? assignmentQueue.items.slice(0, 4) : [];
  const search = snapshot.global_search || { summary: {}, items: [] };
  const searchSummary = search.summary || {};
  const searchItems = Array.isArray(search.items) ? search.items.slice(0, 4) : [];
  const teams = Array.isArray(masterData.teams) ? masterData.teams.slice(0, 4) : [];
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Master Data &amp; Routing</div>
              <h2 class="hero-title">Keep people, teams, routing, and searchable ownership readable as governance infrastructure.</h2>
              <p class="hero-subtitle">This is the advanced lane for governing organization structure, assignment ownership, fallback routing, and searchable continuity across cases, documents, and AI work. Normal users should not need to inspect this just to do daily work.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(searchSummary.search_ready ? 'search ready' : 'index warming')}${statusBadge(Number(assignmentSummary.human_required_total || 0) > 0 ? 'human routing active' : 'routing clear')}</div>
          </div>
          <div class="metrics-grid metrics-grid-luxury">
            ${metricCard('People', masterSummary.people_total || 0, Number(masterSummary.people_total || 0) > 0 ? 'accent' : 'default', 'Directory people available to route governed work.')}
            ${metricCard('Seats', masterSummary.seats_total || 0, Number(masterSummary.seats_total || 0) > 0 ? 'accent' : 'default', 'Governed seats attached to teams, owners, or workflow lanes.')}
            ${metricCard('Teams', masterSummary.teams_total || 0, Number(masterSummary.teams_total || 0) > 0 ? 'accent' : 'default', 'Business teams visible to the routing and search layer.')}
            ${metricCard('Assignments', assignmentSummary.items_total || 0, Number(assignmentSummary.items_total || 0) > 0 ? 'accent' : 'default', 'Governed assignment items currently routed through the runtime.')}
            ${metricCard('Human required', assignmentSummary.human_required_total || 0, Number(assignmentSummary.human_required_total || 0) > 0 ? 'warning' : 'success', 'Assignments that still need an explicit human boundary move.')}
            ${metricCard('Indexed records', searchSummary.indexed_total || 0, Number(searchSummary.indexed_total || 0) > 0 ? 'success' : 'default', 'Searchable objects currently visible through the global directory and retrieval layer.')}
          </div>
          <div class="inline-actions">
            ${renderViewJumpButton({ view: 'directory', label: 'Open Directory & Search', className: 'action-button' })}
            ${renderViewJumpButton({ view: 'requests', label: 'Open Work Inbox', className: 'action-button action-button-muted' })}
          </div>
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">Routing governance</div>
            <h3 class="card-title">Search, assignment, and fallback ownership belong together</h3>
            <p class="card-subtitle">Master data becomes governance infrastructure when the runtime can route work to a real owner, explain why, and still let advanced operators trace search continuity back through the command surface.</p>
          </div>
          ${keyValue([
            ['Organization', masterSummary.organization_name || '-'],
            ['Primary view', assignmentSummary.primary_view || searchSummary.primary_view || 'directory'],
            ['Critical assignments', String(assignmentSummary.critical_total || 0)],
            ['High priority', String(assignmentSummary.high_priority_total || 0)],
            ['Search ready', searchSummary.search_ready ? 'yes' : 'no'],
            ['Indexed types', String(searchSummary.indexed_types_total || 0)],
          ])}
        </article>
      </section>
      <section class="card-grid">
        <article class="card stack">
          <div>
            <div class="eyebrow muted">Teams in scope</div>
            <h3 class="card-title">Governed routing map</h3>
            <p class="card-subtitle">Use this to confirm the team layer exists before expecting clean assignment or department-driven quick access.</p>
          </div>
          ${teams.length ? `<div class="stack gap-sm">${teams.map((item) => renderDirectoryEntityCard(item, 'team')).join('')}</div>` : emptyState('No teams are seeded yet.')}
        </article>
        <article class="card stack">
          <div>
            <div class="eyebrow muted">Assignment pressure</div>
            <h3 class="card-title">Current routed work</h3>
            <p class="card-subtitle">Assignment governance should show who owns the next move, not force operators to guess where work landed.</p>
          </div>
          ${assignmentItems.length ? `<div class="stack gap-sm">${assignmentItems.map((item) => renderDirectoryAssignmentCard(item)).join('')}</div>` : emptyState('No assignment items are visible yet.')}
        </article>
        <article class="card stack">
          <div>
            <div class="eyebrow muted">Search continuity</div>
            <h3 class="card-title">Recent searchable objects</h3>
            <p class="card-subtitle">Search belongs in Control Room here because advanced operators need to verify index health and routing discoverability, not because normal users should see search internals on Home.</p>
          </div>
          ${searchItems.length ? `<div class="stack gap-sm">${searchItems.map((item) => renderDirectorySearchResultCard(item)).join('')}</div>` : emptyState('Global search has not indexed any records yet.')}
        </article>
      </section>
    </section>
  `;
}
function renderOwnerRegistrationTool(snapshot) {
  const registration = snapshot.owner_registration || snapshot.runtime_health?.owner_registration || {};
  const setupAssistant = snapshot.operations?.first_run_action_center || {};
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Owner Registration</div>
              <h2 class="hero-title">Anchor deployment identity before delegated work fans out across the organization.</h2>
              <p class="hero-subtitle">This is where the private runtime keeps organization identity, executive ownership, and registration posture aligned before additional operators or AI workforce roles are trusted.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(registration.registered ? 'registered' : 'setup needed')}${statusBadge(registration.deployment_mode || 'private')}</div>
          </div>
          ${renderOwnerRegistrationPanel(registration)}
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">Setup continuity</div>
            <h3 class="card-title">Identity should stay connected to first-run readiness</h3>
            <p class="card-subtitle">Registration is not a detached setup field. It shapes onboarding, diagnostics, trusted publication, and the default ownership line used across the suite.</p>
          </div>
          ${keyValue([
            ['Setup status', formatStatusLabel(setupAssistant.status || 'blocked')],
            ['Required actions', String(setupAssistant.required_total || 0)],
            ['Recommended action', setupAssistant.recommended_action || 'none'],
            ['Organization', registration.organization_name || '-'],
            ['Executive owner id', registration.executive_owner_id || '-'],
            ['Registry signer', registration.trusted_registry_signed_by || '-'],
          ])}
          <div class="inline-actions">
            <button class="action-button action-button-muted" type="button" data-control-room-tool="setup">Open Setup &amp; Onboarding</button>
            <button class="action-button action-button-muted" type="button" data-control-room-tool="admin_settings">Open Admin Settings</button>
          </div>
        </article>
      </section>
    </section>
  `;
}

function renderRetentionTool(snapshot) {
  const retentionReport = snapshot.retention || {};
  const retentionPlan = snapshot.retention_plan || {};
  const datasets = Array.isArray(retentionReport.datasets) ? retentionReport.datasets : [];
  const canManageRetention = can('retention.manage');
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Documents &amp; Records</div>
              <h2 class="hero-title">Retention, legal hold, and governed records posture live here inside Control Room.</h2>
              <p class="hero-subtitle">Normal users work documents from the command surface. This advanced lane is for retention policy, expiry pressure, legal hold posture, and recovery-sensitive record management.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(datasets.length ? 'present' : 'setup needed')}${statusBadge((retentionReport.hold_blocked_total || 0) > 0 ? 'human required' : 'monitoring')}</div>
          </div>
          <div class="hero-split">
            ${keyValue([
              ['Datasets', String(datasets.length)],
              ['Expired candidates', String(retentionReport.expired_candidate_total || 0)],
              ['Hold blocked', String(retentionReport.hold_blocked_total || 0)],
              ['Next expiry', retentionReport.next_expiry_at || '-'],
              ['Retention mode', retentionPlan.mode || 'governed'],
              ['Archive root', retentionPlan.archive_path || '-'],
            ])}
            <div class="hero-note"><strong>Records doctrine</strong><p>Documents, audit material, and governed runtime artifacts should age predictably. This lane exists to keep retention readable without leaking raw stores back into Home.</p></div>
          </div>
          ${canManageRetention ? '<div class="inline-actions"><button class="action-button" type="button" data-retention-action="enforce-now">Run retention policy</button></div>' : ''}
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">Linked governance</div>
            <h3 class="card-title">Retention should stay connected to audit and recovery</h3>
            <p class="card-subtitle">Operators should review retention together with evidence, restore posture, and go-live expectations rather than treating record lifecycle as an isolated maintenance chore.</p>
          </div>
          <div class="inline-actions">
            <button class="action-button action-button-muted" type="button" data-control-room-tool="audit">Open Trust &amp; Evidence</button>
            <button class="action-button action-button-muted" type="button" data-control-room-tool="backup_restore">Open Backup &amp; Restore</button>
          </div>
        </article>
      </section>
      ${renderRetentionSection(retentionReport) || renderNoWorkState('No retention datasets are visible yet.', {
        eyebrow: 'Records posture',
        title: 'Retention has not been seeded yet.',
        detail: 'As governed documents, audit events, and workflow artifacts accumulate, the records and retention lane will show expiry, hold, and archive posture here.',
        primaryActionView: 'documents',
        primaryActionLabel: 'Open Documents',
        secondaryActionView: 'audit',
        secondaryActionLabel: 'Open Audit',
        pills: ['records lane', 'retention ready'],
      })}
    </section>
  `;
}

function renderModelProvidersPanel(modelProviders, options = {}) {
  const summary = modelProviders || {};
  const providers = Array.isArray(summary.providers) ? summary.providers : [];
  const compact = Boolean(options.compact);
  if (!providers.length) {
    return renderNoWorkState('No model providers are configured yet.', {
      eyebrow: compact ? 'Provider posture' : 'AI provider posture',
      title: 'The AI workforce has no provider lane yet.',
      detail: 'Configure at least one provider before expecting governed AI actions to execute from the private runtime.',
      primaryActionView: 'actions',
      primaryActionLabel: 'Open AI Actions',
      secondaryActionView: 'overview',
      secondaryActionLabel: 'Back to Home',
      pills: ['provider setup', 'private-first'],
    });
  }
  return `
    <section class="control-room-provider-grid">
      ${providers.map((provider) => `
        <article class="trace-box compact-trace control-room-provider-card">
          <div class="hero-chip-row">${statusBadge(provider.ready ? 'ready' : 'monitoring')}${provider.is_default ? statusBadge('default') : ''}</div>
          <strong>${escapeHtml(provider.provider_id || provider.label || 'provider')}</strong>
          ${keyValue([
            ['Status', provider.status || (provider.ready ? 'ready' : 'monitoring')],
            ['Default', provider.is_default ? 'yes' : 'no'],
            ['Model', provider.model || '-'],
            ['Endpoint', provider.endpoint || '-'],
          ])}
          <p class="muted">${escapeHtml(provider.note || provider.message || 'Provider posture is available for governed AI execution routing.')}</p>
        </article>
      `).join('')}
    </section>
  `;
}

function renderModelProvidersTool(snapshot) {
  const modelProviders = snapshot.model_providers || {};
  const hasProviders = Number(modelProviders.configured_providers || 0) > 0;
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Model Providers</div>
              <h2 class="hero-title">Keep AI workforce execution inside one readable provider posture lane.</h2>
              <p class="hero-subtitle">This advanced tool is where operators review default-provider readiness, probe model execution posture, and confirm the workforce can still execute inside the private runtime boundary.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(hasProviders ? 'configured' : 'setup needed')}${statusBadge(modelProviders.default_provider_ready === false ? 'attention required' : 'ready')}</div>
          </div>
          <div class="hero-split">
            ${keyValue([
              ['Configured providers', String(modelProviders.configured_providers || 0)],
              ['Default provider', modelProviders.default_provider || '-'],
              ['Default ready', modelProviders.default_provider_ready === false ? 'no' : 'yes'],
              ['Partial providers', String(modelProviders.partial_providers || 0)],
              ['Status', formatStatusLabel(modelProviders.status || 'missing')],
            ])}
            <div class="hero-note"><strong>Workforce doctrine</strong><p>AI remains the primary workforce. Provider posture exists here so Home can stay simple while Control Room keeps the execution dependency visible for admins and founders.</p></div>
          </div>
          ${can('integration.manage') ? '<div class="inline-actions"><button class="action-button" type="button" data-integration-action="probe-model-providers">Probe model providers</button></div>' : ''}
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">Linked governance</div>
            <h3 class="card-title">Provider health should stay close to actions and integrations</h3>
            <p class="card-subtitle">Use this with AI Actions when workforce execution looks paused, and with Integrations when the output lane depends on provider health.</p>
          </div>
          <div class="inline-actions">
            <button class="action-button action-button-muted" type="button" data-view-jump="actions">Open AI Actions</button>
            <button class="action-button action-button-muted" type="button" data-control-room-tool="integrations">Open Integrations</button>
          </div>
        </article>
      </section>
      ${renderModelProvidersPanel(modelProviders)}
    </section>
  `;
}

function renderIntegrationsTool(snapshot) {
  const integrations = snapshot.integrations || {};
  const modelProviders = snapshot.model_providers || {};
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Integrations &amp; Providers</div>
              <h2 class="hero-title">Outbound routing, delivery posture, and provider readiness belong together in Control Room.</h2>
              <p class="hero-subtitle">This lane keeps webhook targets, delivery failures, model providers, and workforce execution dependencies in one place so advanced operators can troubleshoot without leaking plumbing onto Home.</p>
            </div>
            <div class="hero-chip-row">${statusBadge((integrations.summary?.active_targets || 0) > 0 ? 'configured' : 'setup needed')}${statusBadge(modelProviders.default_provider_ready === false ? 'monitoring' : 'ready')}</div>
          </div>
          <div class="inline-actions">
            <button class="action-button action-button-muted" type="button" data-control-room-tool="model_providers">Open Model Providers</button>
            <button class="action-button action-button-muted" type="button" data-view-jump="actions">Open AI Actions</button>
          </div>
        </article>
      </section>
      ${renderIntegrationSection(integrations)}
      <article class="table-card stack control-room-compact-panel">
        <div class="table-card-head">
          <div>
            <div class="eyebrow muted">Provider snapshot</div>
            <h3 class="table-title">Model provider posture</h3>
            <p class="card-subtitle">A compact provider reading stays here so integration routing and AI execution can be read together.</p>
          </div>
        </div>
        ${renderModelProvidersPanel(modelProviders, { compact: true })}
      </article>
    </section>
  `;
}

function renderBackupRestoreTool(snapshot) {
  const operations = snapshot.operations || {};
  const summary = operations.summary || {};
  const backups = Array.isArray(operations.backups) ? operations.backups : [];
  const proof = operations.usability_proof || {};
  const doctor = operations.quick_start_doctor || {};
  const baseline = operations.runtime_performance_baseline || {};
  const runtimeHealth = snapshot.runtime_health || {};
  const goLive = snapshot.go_live_readiness || {};
  const registration = snapshot.owner_registration || {};
  const latestBackup = summary.latest_backup || {};
  const formatMs = (value) => Number.isFinite(Number(value)) && Number(value) > 0 ? `${Number(value).toFixed(1)} ms` : '-';
  const managementActions = can('ops.manage')
    ? `<div class="inline-actions"><button class="action-button" type="button" data-ops-action="backup">Create Runtime Backup</button><button class="action-button action-button-muted" type="button" data-ops-action="quick-start-doctor">Run Quick-Start Doctor</button><button class="action-button action-button-muted" type="button" data-ops-action="usability-proof">Generate Usability Proof</button><button class="action-button action-button-muted" type="button" data-ops-action="first-run-action-center-sync">Run First-Run Sync</button></div>`
    : '';
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Backup & Restore</div>
              <h2 class="hero-title">Recovery bundles, restore playbook, and pilot-hardening artifacts in one governed surface.</h2>
              <p class="hero-subtitle">Use this tool when the runtime needs a sealed backup, when an operator must rehearse recovery, or when proof and diagnostics must be refreshed immediately after operational change.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(latestBackup.backup_id ? 'backup ready' : 'backup needed')}${statusBadge(goLive.status || 'blocked')}</div>
          </div>
          ${managementActions}
          <div class="hero-split">
            ${keyValue([
              ['Latest backup', latestBackup.backup_id || 'No backup yet'],
              ['Backups total', String(summary.backups_total || 0)],
              ['Latest created', latestBackup.created_at || '-'],
              ['Latest bundle bytes', latestBackup.bytes_total != null ? String(latestBackup.bytes_total) : '-'],
              ['Go-live posture', formatStatusLabel(goLive.status || 'blocked')],
            ])}
            <div class="hero-note"><strong>Restore doctrine</strong><p>Recover backup, evidence, registry, and owner identity together. A restore is not complete until doctor and proof artifacts are refreshed and reviewed again.</p></div>
          </div>
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">Pilot-hardening artifacts</div>
            <h3 class="card-title">Proof and diagnostics must move with recovery</h3>
            <p class="card-subtitle">A backup by itself is not enough. The runtime should also carry doctor, proof, and performance posture so the restored system is readable within minutes.</p>
          </div>
          ${keyValue([
            ['Quick-start doctor', formatStatusLabel(doctor.status || 'missing')],
            ['Usability proof', formatStatusLabel(proof.status || 'missing')],
            ['Performance baseline', formatStatusLabel(baseline.status || 'missing')],
            ['Slowest metric', baseline.slowest_metric || '-'],
            ['Slowest elapsed', formatMs(baseline.slowest_elapsed_ms)],
            ['Warnings', String(baseline.warning_total || 0)],
          ])}
        </article>
      </section>
      <section class="split-grid">
        <article class="table-card stack">
          <div class="table-card-head">
            <div>
              <h3 class="table-title">Restore playbook</h3>
              <p class="muted">Keep recovery steps human-readable so one operator can rehydrate the runtime without falling into low-level store hunting.</p>
            </div>
          </div>
          <div class="trace-box compact-trace"><strong>Restore sequence</strong>${keyValue([
            ['1. Freeze risky changes', 'Pause publish, review, and high-risk execution before choosing a restore source.'],
            ['2. Inspect the newest bundle', latestBackup.backup_path || summary.backup_dir || 'Create a backup first so a restore source exists.'],
            ['3. Restore governed runtime files', 'Bring stores, evidence, registry artifacts, and registration identity back together as one operating state.'],
            ['4. Re-run doctor and proof', 'Refresh quick-start doctor, usability proof, and baseline artifacts immediately after restore.'],
          ])}</div>
          <div class="trace-box compact-trace"><strong>Critical paths</strong>${keyValue([
            ['Backup directory', summary.backup_dir || runtimeHealth.runtime_backup_dir?.path || '-'],
            ['Evidence directory', runtimeHealth.runtime_evidence_dir?.path || '-'],
            ['Archive directory', runtimeHealth.retention_archive_dir?.path || '-'],
            ['Owner registration', registration.path || '-'],
            ['Trusted manifest', runtimeHealth.trusted_registry_manifest?.path || '-'],
          ])}</div>
          <div class="trace-box compact-trace"><strong>Latest artifact state</strong>${keyValue([
            ['Doctor next actions', Array.isArray(doctor.next_actions) && doctor.next_actions.length ? doctor.next_actions.slice(0, 2).join(' | ') : 'No recommended next actions.'],
            ['Proof failed criteria', Array.isArray(proof.failed_criteria) && proof.failed_criteria.length ? proof.failed_criteria.join(' | ') : 'No failing proof criteria.'],
            ['Performance criticals', String(baseline.critical_total || 0)],
            ['Performance failed', String(baseline.failed_total || 0)],
          ])}</div>
        </article>
        <article class="table-card stack">
          <div class="table-card-head">
            <div>
              <h3 class="table-title">Runtime backup history</h3>
              <p class="muted">Use the latest sealed bundle as the primary restore anchor, then verify proof and doctor continuity from the same Control Room.</p>
            </div>
          </div>
          <div class="table-wrapper">${backupTable(backups)}</div>
        </article>
      </section>
    </section>
  `;
}

function renderAdminSettingsTool(snapshot) {
  const registration = snapshot.owner_registration || {};
  const runtimeHealth = snapshot.runtime_health || {};
  const accessControl = runtimeHealth.access_control || {};
  const integrations = snapshot.integrations || {};
  const integrationSummary = integrations.summary || {};
  const modelProviders = snapshot.model_providers || {};
  const masterSummary = snapshot.master_data?.summary || {};
  const retention = snapshot.retention || {};
  const alertPolicy = snapshot.operator_alert_policy || {};
  const availableProfiles = Array.isArray(snapshot.available_profiles) ? snapshot.available_profiles : [];
  const profilePreview = availableProfiles.length
    ? availableProfiles.slice(0, 4).map((item) => item.display_name || item.profile_id || 'profile').join(' | ')
    : 'No access profiles are visible.';
  const aging = alertPolicy.aging || {};
  const onboardingActions = `
    <div class="inline-actions">
      ${canAccessSetupAssistant() ? renderViewJumpButton({ view: 'setup', label: 'Open Setup Assistant', className: 'action-button' }) : ''}
      ${renderViewJumpButton({ view: 'directory', label: 'Open Directory & Search', className: 'action-button action-button-muted' })}
      ${renderViewJumpButton({ view: 'health', label: 'Open Runtime Health', className: 'action-button action-button-muted' })}
    </div>
  `;
  return `
    <section class="stack gap-lg">
      <section class="overview-hero">
        <article class="card hero-card hero-card-primary">
          <div class="hero-heading">
            <div>
              <div class="eyebrow muted">Admin Settings</div>
              <h2 class="hero-title">Organization identity, access, providers, and routing posture without exposing raw plumbing first.</h2>
              <p class="hero-subtitle">Use this tool when you need the living operating settings of the runtime: who the organization is, how access behaves, how AI providers are configured, and whether routing and retention still match pilot expectations.</p>
            </div>
            <div class="hero-chip-row">${statusBadge(registration.registered ? 'registered' : 'setup needed')}${statusBadge(modelProviders.status || 'providers unknown')}</div>
          </div>
          ${onboardingActions}
          <div class="hero-split">
            ${keyValue([
              ['Organization', registration.organization_name || masterSummary.organization_name || 'Unregistered runtime'],
              ['Deployment mode', registration.deployment_mode || snapshot.environment || 'private'],
              ['Profiles active', String(accessControl.profiles_active || 0)],
              ['Providers configured', String(modelProviders.configured_providers || 0)],
              ['Active integrations', String(integrationSummary.active_targets || 0)],
            ])}
            <div class="hero-note"><strong>Admin principle</strong><p>Settings should answer whether the runtime is governable, assignable, and pilot-ready. Editing deeper internals still belongs in Setup Assistant or the underlying runtime tools.</p></div>
          </div>
        </article>
        <article class="card hero-card hero-card-secondary">
          <div>
            <div class="eyebrow muted">Operator-facing settings posture</div>
            <h3 class="card-title">Small enough to read, deep enough to act</h3>
            <p class="card-subtitle">The goal is not to expose every config knob. The goal is to show the few settings that explain why Home, AI Actions, routing, and governance behave the way they do.</p>
          </div>
          ${keyValue([
            ['Session TTL', accessControl.session_ttl_minutes != null ? `${accessControl.session_ttl_minutes} minutes` : '-'],
            ['Idle timeout', accessControl.session_idle_timeout_minutes != null ? `${accessControl.session_idle_timeout_minutes} minutes` : '-'],
            ['Token gate', runtimeHealth.token_gate || 'unknown'],
            ['Access config', accessControl.access_profile_configuration_valid ? 'valid' : 'needs review'],
            ['Search ready', masterSummary.search_ready ? 'yes' : 'no'],
            ['Retention datasets', String(retention.dataset_count || 0)],
          ])}
        </article>
      </section>
      <section class="split-grid">
        <article class="table-card stack">
          <div class="table-card-head">
            <div>
              <h3 class="table-title">Organization & runtime identity</h3>
              <p class="muted">These settings define which organization the runtime serves and who anchors ownership when advanced governance decisions happen.</p>
            </div>
          </div>
          ${keyValue([
            ['Organization', registration.organization_name || masterSummary.organization_name || '-'],
            ['Organization id', registration.organization_id || '-'],
            ['Executive owner id', registration.executive_owner_id || '-'],
            ['Registration code', registration.registration_code || '-'],
            ['Deployment mode', registration.deployment_mode || snapshot.environment || '-'],
            ['Registration file', registration.path || '-'],
          ])}
          <div class="trace-box compact-trace"><strong>Why this matters</strong><p class="muted">Identity drift here changes who may govern the runtime, how cases are labeled, and which private deployment story the pilot actually represents.</p></div>
        </article>
        <article class="table-card stack">
          <div class="table-card-head">
            <div>
              <h3 class="table-title">Access & operator control</h3>
              <p class="muted">These signals explain whether the right people can enter the runtime and whether sessions behave like a controlled private product instead of an ad-hoc dev surface.</p>
            </div>
          </div>
          ${keyValue([
            ['Profiles total', String(accessControl.profiles_total || availableProfiles.length || 0)],
            ['Profiles active', String(accessControl.profiles_active || 0)],
            ['Sessions active', String(accessControl.sessions_active || 0)],
            ['Rotation required', String(accessControl.profiles_rotation_required || 0)],
            ['Plain tokens', String(accessControl.plain_tokens || 0)],
            ['Visible profiles', profilePreview],
          ])}
          <div class="trace-box compact-trace"><strong>Operator alert policy</strong>${keyValue([
            ['Warning age', aging.warning_hours != null ? `${aging.warning_hours} hours` : '-'],
            ['Critical age', aging.critical_hours != null ? `${aging.critical_hours} hours` : '-'],
            ['Stale age', aging.stale_hours != null ? `${aging.stale_hours} hours` : '-'],
          ])}</div>
        </article>
      </section>
      <section class="split-grid">
        <article class="table-card stack">
          <div class="table-card-head">
            <div>
              <h3 class="table-title">AI providers & integration routing</h3>
              <p class="muted">Use this to confirm whether the AI workforce has a healthy provider path and whether outbound routing is ready when the runtime escalates beyond the dashboard.</p>
            </div>
          </div>
          ${keyValue([
            ['Provider status', modelProviders.status || 'unknown'],
            ['Configured providers', String(modelProviders.configured_providers || 0)],
            ['Default provider', modelProviders.default_provider || '-'],
            ['Active targets', String(integrationSummary.active_targets || 0)],
            ['Notification channels', String(integrationSummary.notification_channels_active || 0)],
            ['Signed targets', String(integrationSummary.signed_targets || 0)],
            ['HTTP enabled', String(Boolean(integrationSummary.http_enabled))],
          ])}
          <div class="trace-box compact-trace"><strong>Routing note</strong><p class="muted">Normal users should not have to think about routing internals. This surface exists so advanced operators can confirm that alerts, tickets, and webhook delivery are ready when governance needs them.</p></div>
        </article>
        <article class="table-card stack">
          <div class="table-card-head">
            <div>
              <h3 class="table-title">Master data, retention, and pilot discipline</h3>
              <p class="muted">These settings keep the runtime grounded in real people and teams while still protecting records, evidence, and archive posture as the pilot expands.</p>
            </div>
          </div>
          ${keyValue([
            ['People', String(masterSummary.people_total || 0)],
            ['Teams', String(masterSummary.teams_total || 0)],
            ['Seats', String(masterSummary.seats_total || 0)],
            ['Archive candidates', String(retention.archive_candidate_total || 0)],
            ['Expired candidates', String(retention.expired_candidate_total || 0)],
            ['Legal hold datasets', String(retention.legal_hold_datasets || 0)],
            ['Archive directory', retention.archive_dir || runtimeHealth.retention_archive_dir?.path || '-'],
          ])}
          <div class="trace-box compact-trace"><strong>Pilot hardening note</strong><p class="muted">If master data is thin, assignment becomes guesswork. If retention is unclear, evidence becomes fragile. Productization depends on both staying readable to one human governor.</p></div>
        </article>
      </section>
    </section>
  `;
}

function getActionMissionTone(item = {}) {
  const status = String(item?.status || '').trim();
  if (status === 'failed_closed' || status === 'blocked') return 'danger';
  if (status === 'waiting_human' || status === 'human_required') return 'warning';
  if (status === 'completed') return 'success';
  return 'accent';
}

function getActionBoardMeta(item = {}) {
  const status = String(item?.status || '').trim();
  if (status === 'running') {
    return {
      eyebrow: 'AI moving now',
      tempoBadge: 'live now',
      routePhase: 'AI currently owns the move inside this case. Stay nearby, but intervene only if the runtime crosses a new boundary.',
      consequenceTitle: 'Keep the move in flight',
      consequenceDetail: 'No new human step is needed yet. Monitor the route and keep the case attached until the runtime surfaces a boundary or a proof-ready result.',
      nextOwner: 'AI runtime',
      tone: 'accent',
    };
  }
  if (status === 'waiting_human') {
    return {
      eyebrow: 'Human boundary now',
      tempoBadge: 'human step now',
      routePhase: 'A real person now owns the next safe move. Keep the case and handoff record attached before sending AI forward again.',
      consequenceTitle: 'Human decision is now required',
      consequenceDetail: 'AI cannot safely continue until a person approves, redirects, or closes this path. The case should remain the anchor for that decision.',
      nextOwner: 'Human director',
      tone: 'warning',
    };
  }
  if (status === 'failed_closed') {
    return {
      eyebrow: 'Recovery lane',
      tempoBadge: 'recover now',
      routePhase: 'This path failed closed. Review the blocked boundary, then reopen AI only when the route is safe again.',
      consequenceTitle: 'Recover before relaunch',
      consequenceDetail: 'The governed path is closed until the failure is reviewed. Fix the route first, then decide whether AI should retry from the same case.',
      nextOwner: 'Recovery review',
      tone: 'danger',
    };
  }
  if (status === 'completed') {
    return {
      eyebrow: 'Outcome ready',
      tempoBadge: 'proof ready',
      routePhase: 'The governed result is ready for follow-through, document review, or proof confirmation from the next lane.',
      consequenceTitle: 'Carry proof forward',
      consequenceDetail: 'The runtime already has a result. Review the linked document, case, or proof lane instead of launching another move blindly.',
      nextOwner: 'Follow-through lane',
      tone: 'success',
    };
  }
  return {
    eyebrow: 'Queued move',
    tempoBadge: 'queued',
    routePhase: 'This action is visible on the board so the Director can decide when to launch or revisit it.',
    consequenceTitle: 'Launch only when the case is ready',
    consequenceDetail: 'Queued moves stay visible so the Director can launch them deliberately from the right case and side-effect posture.',
    nextOwner: 'Director launch decision',
    tone: 'accent',
  };
}

function renderActionConsequenceCard(config = {}) {
  const toneClass = config.tone ? ` tone-${escapeHtml(config.tone)}` : '';
  const featuredClass = config.featured ? ' action-consequence-card-featured' : '';
  const chips = [config.badge, config.secondaryBadge].filter(Boolean).map((badge) => statusBadge(badge)).join('');
  const buttonClassName = config.buttonClassName || (config.featured ? 'action-button' : 'action-button action-button-muted');
  return `
    <article class="command-action-card action-consequence-card${featuredClass}${toneClass}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(config.eyebrow || 'Consequence')}</div>
          <strong>${escapeHtml(config.title || 'Executive consequence')}</strong>
        </div>
        ${chips ? `<div class="hero-chip-row">${chips}</div>` : ''}
      </div>
      <p class="muted">${escapeHtml(config.detail || 'Review the next governed consequence from the right lane.')}</p>
      ${config.traceTitle || config.traceDetail ? `<div class="trace-box compact-trace"><strong>${escapeHtml(config.traceTitle || 'Next consequence')}</strong><p class="muted">${escapeHtml(config.traceDetail || config.detail || '')}</p></div>` : ''}
      ${renderViewJumpButton({
        view: config.view || 'actions',
        label: config.actionLabel || 'Open details',
        className: buttonClassName,
        focusType: config.focusType || '',
        focusId: config.focusId || '',
        caseId: config.caseId || '',
        title: config.title || 'Executive consequence',
        detail: config.detail || config.traceDetail || 'Continue from the right governed lane.',
        actionLabel: config.actionLabel || 'Open details',
      })}
    </article>
  `;
}

function renderActionMissionCard(item, options = {}) {
  const fallbackView = options.fallbackView || 'actions';
  if (!item) {
    const fallbackViewLabel = VIEW_TITLES[fallbackView] || titleCase(fallbackView || 'actions');
    return `
      <article class="command-action-card tone-success command-workforce-card">
        <div class="eyebrow muted">${escapeHtml(options.eyebrow || 'Mission slot')}</div>
        <strong>${escapeHtml(options.fallbackTitle || 'No active action is visible')}</strong>
        <p class="muted">${escapeHtml(options.fallbackDetail || 'This slot will surface the next governed AI mission when it matters.')}</p>
        <div class="trace-box compact-trace"><strong>${escapeHtml(options.fallbackActionLabel || `Open ${fallbackViewLabel}`)}</strong><p class="muted">${escapeHtml(`Use ${fallbackViewLabel} to inspect the broader AI runtime or related case continuity.`)}</p></div>
        ${renderViewJumpButton({ view: fallbackView, label: options.fallbackActionLabel || `Open ${fallbackViewLabel}`, className: 'action-button action-button-muted', title: `${fallbackViewLabel} reopened from AI Actions.`, detail: options.fallbackDetail || `Use ${fallbackViewLabel} to inspect the next AI mission.`, actionLabel: options.fallbackActionLabel || `Open ${fallbackViewLabel}` })}
      </article>
    `;
  }
  const meta = getActionBoardMeta(item);
  const primary = resolveActionPrimaryFocus(item);
  const view = options.viewOverride || primary.view || 'actions';
  const viewLabel = VIEW_TITLES[view] || titleCase(view || 'actions');
  const tone = options.toneOverride || meta.tone || getActionMissionTone(item);
  const summaryLine = item.output_summary || item.next_action || item.waiting_reason || item.latest_error || 'Governed AI runtime item.';
  const traceLine = item.latest_error || item.waiting_reason || `Case ${item.case_id || '-'} | ${item.action_type || 'action'} | ${item.artifacts_total || 0} artifacts`;
  const actionLabel = options.actionLabel || `Open ${viewLabel}`;
  const focusType = primary.entityType || '';
  const focusId = primary.entityId || '';
  const focusClass = focusType && focusId && isFocusedEntity(focusType, focusId) ? ' focused-record' : '';
  const focusAttrs = focusType && focusId ? ` data-focus-key="${escapeHtml(buildFocusKey(focusType, focusId))}"` : '';
  return `
    <article class="command-action-card tone-${escapeHtml(tone)} command-workforce-card${focusClass}"${focusAttrs}>
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(options.eyebrow || meta.eyebrow || 'Mission slot')}</div>
          <strong>${escapeHtml(item.label || titleCase(item.action_type || 'AI action'))}</strong>
        </div>
        <div class="hero-chip-row">${statusBadge(meta.tempoBadge || item.status || 'visible')}${statusBadge(viewLabel)}</div>
      </div>
      <div class="transition-route command-inbox-route">
        <span class="transition-node transition-node-active">${escapeHtml(item.case_id ? `Case ${item.case_id}` : 'AI runtime')}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(item.status || 'planned')}</span>
        <span class="transition-arrow">&rarr;</span>
        <span class="transition-node">${escapeHtml(viewLabel)}</span>
      </div>
      <p class="muted">${escapeHtml(summaryLine)}</p>
      <p class="muted small action-runtime-route-note">${escapeHtml(meta.routePhase || traceLine)}</p>
      <div class="trace-box compact-trace"><strong>${escapeHtml(actionLabel)}</strong><p class="muted">${escapeHtml(traceLine)}</p></div>
      ${renderViewJumpButton({ view, label: actionLabel, className: 'action-button', focusType, focusId, caseId: primary.caseId || item.case_id || '', title: `${item.label || item.action_id || 'AI action'} opened in ${viewLabel}.`, detail: summaryLine, actionLabel })}
    </article>
  `;
}

function renderActions(snapshot) {
  const surface = snapshot.actions || { summary: {}, registry: [], items: [] };
  const summary = surface.summary || {};
  const registry = Array.isArray(surface.registry) ? surface.registry : [];
  const items = Array.isArray(surface.items) ? surface.items : [];
  const currentCase = getScopedActionCase(snapshot);
  const caseLabel = currentCase?.case_id || 'No case selected';
  const nextMoveView = !currentCase ? 'cases' : (summary.waiting_human_total || 0) ? 'cases' : (summary.document_artifact_total || 0) ? 'documents' : 'actions';
  const nextMoveLabel = VIEW_TITLES[nextMoveView] || titleCase(nextMoveView);
  const nextMoveTitle = !currentCase
    ? 'Open a case before launching more AI work'
    : (summary.waiting_human_total || 0)
      ? 'Finish the human handoff for this case'
      : (summary.document_artifact_total || 0)
        ? 'Review the document side effects AI already produced'
        : (summary.running_total || 0)
          ? 'Watch the running actions and keep the case attached'
          : items.length
            ? 'Inspect the latest governed action result'
            : 'Launch the first governed action for this case';
  const nextMoveDetail = !currentCase
    ? 'The AI action runtime is safest when launch, side effects, proof, and follow-up all stay attached to one canonical case.'
    : (summary.waiting_human_total || 0)
      ? 'AI already reached a human boundary. The next move belongs to a real person, but the case should remain the anchor for that follow-through.'
      : (summary.document_artifact_total || 0)
        ? 'AI already created governed artifacts. Review them in the document lane without breaking case continuity.'
        : (summary.running_total || 0)
          ? 'AI is moving right now. Keep the case and action lane close so you can step in only if the runtime hits a new boundary.'
          : items.length
            ? 'The runtime already has visible action history. Inspect the result before deciding whether to launch another governed move.'
            : 'This case is ready for its first governed AI action.';
  const runningAction = items.find((item) => String(item.status || '') === 'running') || null;
  const waitingAction = items.find((item) => String(item.status || '') === 'waiting_human') || null;
  const failedAction = items.find((item) => String(item.status || '') === 'failed_closed') || null;
  const completedAction = items.find((item) => String(item.status || '') === 'completed') || null;
  const featuredConsequenceKey = waitingAction
    ? 'human'
    : failedAction
      ? 'recovery'
      : (completedAction || Number(summary.document_artifact_total || 0))
        ? 'proof'
        : 'launch';
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">AI Action Runtime</div>
            <h2 class="hero-title">Let AI work inside explicit case, authority, side-effect, and proof boundaries.</h2>
            <p class="hero-subtitle">Each action stays attached to one case, one authority boundary, one side-effect policy, and one proof trail.</p>
          </div>
          <div class="hero-chip-row">${statusBadge(currentCase ? 'case scoped' : 'pick case')}${statusBadge(summary.waiting_human_total ? 'human follow-up active' : 'runtime ready')}</div>
        </div>
        <div class="hero-split">
          ${keyValue([
            ['Selected case', caseLabel],
            ['AI actions', String(summary.actions_total || items.length)],
            ['Running', String(summary.running_total || 0)],
            ['Waiting human', String(summary.waiting_human_total || 0)],
            ['Completed', String(summary.completed_total || 0)],
            ['Failed closed', String(summary.failed_closed_total || 0)],
            ['Document artifacts', String(summary.document_artifact_total || 0)],
          ])}
          <div class="hero-note"><strong>Execution contract</strong><p>AI actions only launch inside a canonical case so document drafting, human handoff, and evidence stay in one governed story.</p></div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">What should happen next?</div>
          <h3 class="card-title">${escapeHtml(nextMoveTitle)}</h3>
          <p class="card-subtitle">${escapeHtml(nextMoveDetail)}</p>
        </div>
        ${keyValue([
          ['Current case', caseLabel],
          ['Recommended lane', nextMoveLabel],
          ['Running now', String(summary.running_total || 0)],
          ['Waiting human', String(summary.waiting_human_total || 0)],
          ['Document side effects', String(summary.document_artifact_total || 0)],
        ])}
        <div class="inline-actions">
          ${renderViewJumpButton({ view: nextMoveView, label: `Open ${nextMoveLabel}`, className: 'action-button', caseId: currentCase?.case_id || '', title: `${nextMoveLabel} reopened from AI Actions.`, detail: nextMoveDetail, actionLabel: `Open ${nextMoveLabel}` })}
          ${renderViewJumpButton({ view: 'cases', label: currentCase ? 'Open selected case' : 'Open Cases', className: 'action-button action-button-muted', focusType: currentCase ? 'case' : '', focusId: currentCase?.case_id || '', caseId: currentCase?.case_id || '', title: currentCase ? `Case ${currentCase.case_id} reopened from AI Actions.` : 'Cases reopened from AI Actions.', detail: 'Return to the canonical case to review linked work, proof, and next moves.', actionLabel: currentCase ? 'Open selected case' : 'Open Cases' })}
        </div>
      </article>
    </section>
    <section class="command-workforce-shell action-runtime-board">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Executive action board</div>
          <h3 class="card-title">Which AI mission is moving, waiting, or blocked</h3>
          <p class="card-subtitle">Read this lane like an executive move board: what AI is advancing now, where a real person owns the next move, and which runtime lane needs recovery before AI continues.</p>
        </div>
        <div class="hero-chip-row">${statusBadge((summary.running_total || 0) ? 'ai moving' : 'monitoring')}${statusBadge((summary.failed_closed_total || 0) ? 'recovery visible' : ((summary.waiting_human_total || 0) ? 'human handoff live' : 'board stable'))}</div>
      </div>
      <div class="command-workforce-grid">
        ${renderActionMissionCard(runningAction, {
          eyebrow: 'AI moving now',
          fallbackTitle: 'No action is actively running right now',
          fallbackDetail: 'The workforce board will highlight live governed execution here as soon as AI starts moving inside a case.',
          fallbackView: currentCase ? 'cases' : 'actions',
          fallbackActionLabel: currentCase ? 'Open selected case' : 'Open AI Actions',
          toneOverride: runningAction ? 'accent' : 'success',
          actionLabel: runningAction ? 'Monitor in AI Actions' : undefined,
        })}
        ${renderActionMissionCard(waitingAction, {
          eyebrow: 'Human handoff',
          fallbackTitle: 'No AI action is waiting on a person right now',
          fallbackDetail: 'When AI reaches a real approval or reserved human-only boundary, this slot becomes the next explicit move.',
          fallbackView: 'cases',
          fallbackActionLabel: currentCase ? 'Open selected case' : 'Open Cases',
          toneOverride: waitingAction ? 'warning' : 'success',
          viewOverride: 'cases',
          actionLabel: currentCase ? 'Open selected case' : 'Open Cases',
        })}
        ${renderActionMissionCard(failedAction || completedAction, {
          eyebrow: failedAction ? 'Recovery lane' : 'Latest outcome',
          fallbackTitle: 'No failed or completed action is shaping the board',
          fallbackDetail: 'As soon as an action fails closed or finishes with a meaningful side effect, the board will surface it here.',
          fallbackView: summary.document_artifact_total ? 'documents' : 'actions',
          fallbackActionLabel: summary.document_artifact_total ? 'Open Documents' : 'Open AI Actions',
          toneOverride: failedAction ? 'danger' : completedAction ? 'success' : 'success',
          viewOverride: failedAction ? 'actions' : (summary.document_artifact_total ? 'documents' : undefined),
          actionLabel: failedAction ? 'Recover in AI Actions' : (summary.document_artifact_total ? 'Open Documents' : 'Open AI Actions'),
        })}
      </div>
    </section>
    <section class="action-runtime-section action-consequence-section">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Executive consequences</div>
          <h3 class="card-title">What these AI moves mean right now</h3>
          <p class="card-subtitle">Use this row to read launch posture, human ownership, recovery pressure, and proof follow-through without decoding the full mission log first.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(featuredConsequenceKey === 'human' ? 'human step leads' : featuredConsequenceKey === 'recovery' ? 'recovery leads' : featuredConsequenceKey === 'proof' ? 'proof leads' : 'launch leads')}</div>
      </div>
      <div class="action-consequence-grid">
        ${renderActionConsequenceCard({
          eyebrow: 'Launch window',
          title: currentCase ? 'Launch only the move this case can justify' : 'Select a case before any launch',
          detail: currentCase
            ? (registry.length
                ? 'Only launch the next governed move that matches the current authority boundary and side-effect posture.'
                : 'This case is visible, but no launch-ready move is currently registered from this lane.')
            : 'AI launches stay case-bound so proof, handoff, and recovery never drift into separate stories.',
          badge: currentCase ? `${registry.length} launchable` : 'pick case',
          secondaryBadge: currentCase ? caseLabel : 'case required',
          tone: currentCase ? (registry.length ? 'accent' : 'warning') : 'warning',
          featured: featuredConsequenceKey === 'launch',
          view: currentCase ? 'actions' : 'cases',
          caseId: currentCase?.case_id || '',
          actionLabel: currentCase ? 'Open Action Launch Board' : 'Open Cases',
          traceTitle: currentCase ? 'Launch discipline' : 'Case anchor required',
          traceDetail: currentCase
            ? 'Launch from this lane only when the selected case can justify the AI move and its side effects.'
            : 'Pick the canonical case first, then come back here to launch AI safely.',
        })}
        ${renderActionConsequenceCard({
          eyebrow: 'Human step',
          title: waitingAction ? 'A person now owns the safe next move' : 'No human step is holding AI right now',
          detail: waitingAction
            ? (waitingAction.waiting_reason || waitingAction.next_action || getActionBoardMeta(waitingAction).consequenceDetail)
            : 'The runtime is not currently paused at a human-only boundary.',
          badge: waitingAction ? getActionBoardMeta(waitingAction).tempoBadge : 'clear',
          secondaryBadge: waitingAction ? `Case ${waitingAction.case_id || '-'}` : 'ai can continue',
          tone: waitingAction ? 'warning' : 'success',
          featured: featuredConsequenceKey === 'human',
          view: 'cases',
          focusType: waitingAction ? 'case' : '',
          focusId: waitingAction?.case_id || '',
          caseId: waitingAction?.case_id || currentCase?.case_id || '',
          actionLabel: waitingAction ? (currentCase ? 'Open selected case' : 'Open Cases') : 'Open Cases',
          traceTitle: 'Decision owner',
          traceDetail: waitingAction ? (getActionBoardMeta(waitingAction).nextOwner || 'Human director') : 'AI currently owns the live move until a new governed boundary appears.',
        })}
        ${renderActionConsequenceCard({
          eyebrow: 'Recovery path',
          title: failedAction ? 'Recovery must happen before AI can relaunch' : 'No fail-closed recovery is active',
          detail: failedAction
            ? (failedAction.latest_error || failedAction.next_action || getActionBoardMeta(failedAction).consequenceDetail)
            : 'There is no blocked or fail-closed action demanding recovery right now.',
          badge: failedAction ? getActionBoardMeta(failedAction).tempoBadge : 'clear',
          secondaryBadge: failedAction ? `Case ${failedAction.case_id || '-'}` : 'route open',
          tone: failedAction ? 'danger' : 'success',
          featured: featuredConsequenceKey === 'recovery',
          view: 'actions',
          focusType: failedAction ? 'action' : '',
          focusId: failedAction?.action_id || '',
          caseId: failedAction?.case_id || currentCase?.case_id || '',
          actionLabel: failedAction ? 'Recover in AI Actions' : 'Open AI Actions',
          traceTitle: 'Recovery rule',
          traceDetail: failedAction ? 'Review the blocked boundary first, then decide whether the same case should relaunch AI.' : 'Fail-closed paths will surface here the moment recovery becomes a real executive move.',
        })}
        ${renderActionConsequenceCard({
          eyebrow: 'Proof carry-through',
          title: (completedAction || Number(summary.document_artifact_total || 0)) ? 'A governed result is ready for follow-through' : 'No proof-ready outcome is waiting yet',
          detail: (completedAction || Number(summary.document_artifact_total || 0))
            ? (completedAction?.output_summary || completedAction?.next_action || 'Open the document or case lane to confirm the result, review artifacts, and keep the proof chain intact.')
            : 'Once AI finishes with a meaningful outcome, this slot will point to the proof or document lane that should carry it forward.',
          badge: (completedAction || Number(summary.document_artifact_total || 0)) ? 'proof ready' : 'pending',
          secondaryBadge: Number(summary.document_artifact_total || 0) ? `${summary.document_artifact_total || 0} artifacts` : ((completedAction?.case_id) ? `Case ${completedAction.case_id}` : 'no output'),
          tone: Number(summary.document_artifact_total || 0) ? 'accent' : ((completedAction || Number(summary.document_artifact_total || 0)) ? 'success' : 'default'),
          featured: featuredConsequenceKey === 'proof',
          view: Number(summary.document_artifact_total || 0) ? 'documents' : 'actions',
          caseId: completedAction?.case_id || currentCase?.case_id || '',
          actionLabel: Number(summary.document_artifact_total || 0) ? 'Open Documents' : 'Open AI Actions',
          traceTitle: 'Next proof lane',
          traceDetail: Number(summary.document_artifact_total || 0)
            ? 'The result already created governed side effects. Review them in Documents without breaking case continuity.'
            : ((completedAction || Number(summary.document_artifact_total || 0))
                ? 'Confirm the outcome before launching another move so proof, case, and follow-through stay aligned.'
                : 'Proof-ready results will surface here as soon as the runtime finishes with a governed outcome.'),
        })}
      </div>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Running', summary.running_total || 0, (summary.running_total || 0) ? 'accent' : 'default', 'Governed AI actions actively moving right now.')}
      ${metricCard('Waiting human', summary.waiting_human_total || 0, (summary.waiting_human_total || 0) ? 'warning' : 'success', 'AI actions paused at a real human boundary.')}
      ${metricCard('Completed', summary.completed_total || 0, (summary.completed_total || 0) ? 'success' : 'default', 'Governed AI actions that already finished cleanly.')}
      ${metricCard('Failed closed', summary.failed_closed_total || 0, (summary.failed_closed_total || 0) ? 'danger' : 'success', 'Actions that stopped behind a fail-closed boundary.')}
      ${metricCard('Document artifacts', summary.document_artifact_total || 0, (summary.document_artifact_total || 0) ? 'accent' : 'default', 'Governed document side effects created by AI actions.')}
    </section>
    <section class="split-grid">
      <article class="card stack">
        <div><div class="eyebrow muted">AI workload posture</div><h3 class="card-title">What the workforce is doing from this lane</h3><p class="card-subtitle">AI should feel active here, with human intervention reserved for explicit handoff or fail-closed situations.</p></div>
        ${keyValue([
          ['Running now', String(summary.running_total || 0)],
          ['Waiting human', String(summary.waiting_human_total || 0)],
          ['Completed', String(summary.completed_total || 0)],
          ['Failed closed', String(summary.failed_closed_total || 0)],
        ])}
      </article>
      <article class="card stack">
        <div><div class="eyebrow muted">Keep continuity intact</div><h3 class="card-title">Move through the case, not around it</h3><p class="card-subtitle">When AI drafts a document, triggers a handoff, or fails closed, the safest next move is still the one that preserves the same case story.</p></div>
        <div class="inline-actions">
          ${renderViewJumpButton({ view: 'cases', label: 'Open Cases', className: 'action-button', focusType: currentCase ? 'case' : '', focusId: currentCase?.case_id || '', caseId: currentCase?.case_id || '', title: currentCase ? `Case ${currentCase.case_id} reopened from AI Actions.` : 'Cases reopened from AI Actions.', detail: 'Keep the action, documents, handoffs, and proof trail attached to one governed issue.', actionLabel: 'Open Cases' })}
          ${renderViewJumpButton({ view: 'documents', label: 'Open Documents', className: 'action-button action-button-muted', caseId: currentCase?.case_id || '', title: currentCase?.case_id ? `Case ${currentCase.case_id} reopened in Documents.` : 'Documents reopened from AI Actions.', detail: 'Review governed document drafts or publication follow-through created by the AI action runtime.', actionLabel: 'Open Documents' })}
        </div>
      </article>
    </section>
    <section class="action-runtime-section stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Action launch board</div>
          <h3 class="card-title">What AI can be told to do from this case</h3>
          <p class="card-subtitle">Launch only the governed moves that match the current case, authority boundary, and side-effect posture.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${registry.length} actions available`)}</div>
      </div>
      <div class="card-grid">
        ${registry.map((entry) => renderActionRegistryCard(entry, currentCase)).join('')}
      </div>
    </section>
    <section class="action-runtime-section stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Runtime mission log</div>
          <h3 class="card-title">What the workforce already attempted or produced</h3>
          <p class="card-subtitle">Each action should read like a governed move with a clear pace, route, and next consequence.</p>
        </div>
        <div class="hero-chip-row">${statusBadge(`${summary.actions_total || items.length} visible`)}</div>
      </div>
      <div class="card-grid">
        ${items.length ? items.map((item) => renderActionCard(item)).join('') : renderActionEmptyState(currentCase)}
      </div>
    </section>
  `;
}

function renderDocuments(snapshot) {
  const documentsSurfaceBase = snapshot.documents || { summary: {}, items: [], document_classes: [], human_ask_report: { summary: {}, items: [], narrative: '' } };
  const explicitFilters = getDocumentFilterState();
  const retrievalActive = documentFiltersActive(explicitFilters);
  const documentsSurface = retrievalActive && state.documentSearchResult ? state.documentSearchResult : documentsSurfaceBase;
  const summary = documentsSurface.summary || {};
  const items = Array.isArray(documentsSurface.items) ? documentsSurface.items : [];
  const classes = Array.isArray(documentsSurface.document_classes) ? documentsSurface.document_classes : [];
  const humanAskReport = documentsSurface.human_ask_report || documentsSurfaceBase.human_ask_report || { summary: {}, items: [], narrative: '' };
  const latestLabel = items.length
    ? `${items[0].document_number} | ${shortTime(items[0].updated_at)}`
    : retrievalActive
      ? 'No governed document matched the current runtime search.'
      : 'No governed document has been created yet.';
  const classChips = Object.entries(summary.document_class_counts || {})
    .sort((left, right) => Number(right[1] || 0) - Number(left[1] || 0))
    .slice(0, 5);
  const workQueues = Array.isArray(snapshot.unified_work_inbox?.items)
    ? snapshot.unified_work_inbox.items.filter((item) => item.view === 'documents')
    : [];
  const editingDocument = getDocumentById(state.snapshot, state.documentEditingId);
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Governed Document Center Runtime</div>
            <h2 class="hero-title">Draft, review, publish, supersede, and archive documents inside the governed runtime.</h2>
            <p class="hero-subtitle">This lane turns documents into first-class runtime objects with numbering, active-version logic, case linkage, and reviewable proof instead of leaving them as static files outside the operating story.</p>
          </div>
          <div class="hero-chip-row">
            ${statusBadge(retrievalActive ? 'filtered runtime scope' : (summary.in_review_total ? 'review active' : (summary.published_total ? 'published documents live' : 'document runtime ready')))}
            ${statusBadge(summary.case_linked_total ? 'case linked' : 'standalone lane')}
          </div>
        </div>
        <div class="hero-split">
          ${keyValue([
            ['Latest document', latestLabel],
            ['Documents in scope', String(summary.documents_total || 0)],
            ['Published', String(summary.published_total || 0)],
            ['In review', String(summary.in_review_total || 0)],
            ['Case linked', String(summary.case_linked_total || 0)],
          ])}
          <div class="hero-note">
            <strong>Operator standard</strong>
            <p>Use this lane when the document itself is the governed object that must remain readable across revision work, publication posture, and linked case evidence.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Document reporting</div>
          <h3 class="card-title">Human Ask over document state</h3>
          <p class="card-subtitle">A governed summary of the current document surface so operators can ask for document posture without reconstructing state by hand.</p>
        </div>
        ${keyValue([
          ['Narrative scope', String(humanAskReport.summary?.documents_total || 0)],
          ['Published', String(humanAskReport.summary?.published_total || 0)],
          ['In review', String(humanAskReport.summary?.in_review_total || 0)],
          ['Archived', String(humanAskReport.summary?.archived_total || 0)],
        ])}
        <div class="trace-box"><strong>Human Ask narrative</strong><p class="muted">${escapeHtml(humanAskReport.narrative || 'No governed document report is available yet.')}</p></div>
      </article>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Documents', summary.documents_total || 0, 'accent', retrievalActive ? 'Governed documents visible in the current runtime retrieval scope.' : 'Governed documents currently tracked in the runtime ledger.')}
      ${metricCard('Published', summary.published_total || 0, (summary.published_total || 0) ? 'success' : 'default', 'Documents whose active revision is already published.')}
      ${metricCard('In review', summary.in_review_total || 0, (summary.in_review_total || 0) ? 'warning' : 'success', 'Drafts currently sitting in the formal review lane.')}
      ${metricCard('Approved', summary.approved_total || 0, (summary.approved_total || 0) ? 'accent' : 'default', 'Documents approved but not yet pushed through publish.')}
      ${metricCard('Drafts', summary.draft_total || 0, (summary.draft_total || 0) ? 'accent' : 'success', 'Working revisions that still need review or publication decisions.')}
      ${metricCard('Case linked', summary.case_linked_total || 0, (summary.case_linked_total || 0) ? 'accent' : 'default', 'Documents already tied into a governed business issue or operating story.')}
    </section>
    <section class="split-grid">
      ${renderDocumentRetrievalCard(classes, summary, explicitFilters, retrievalActive)}
      ${renderDocumentWorkQueues(workQueues)}
    </section>
    <section class="split-grid">
      ${renderDocumentEditorCard(classes, editingDocument)}
      ${renderDocumentRuntimeContractCard(classes, classChips)}
    </section>
    <section class="case-grid">
      ${items.length ? items.map((item) => renderDocumentCard(item)).join('') : renderDocumentEmptyState(retrievalActive)}
    </section>
  `;
}

function renderDocumentRetrievalCard(classes, summary, filters, retrievalActive) {
  const effectiveFilters = getEffectiveDocumentFilterState();
  const pills = buildDocumentFilterPills(filters, effectiveFilters);
  const classDistribution = Object.entries(summary.document_class_counts || {})
    .sort((left, right) => Number(right[1] || 0) - Number(left[1] || 0))
    .slice(0, 4);
  const scopedCaseId = getActionContextCaseId() || '';
  return `
    <article class="card stack">
      <div><div class="eyebrow muted">Document retrieval</div><h3 class="card-title">Find the governed document you need</h3><p class="card-subtitle">Search the live runtime by title, status, class, or case without losing lifecycle continuity.</p></div>
      <form id="document-search-form" class="composer-grid">
        <div class="span-2"><label class="permission-note" for="document-search-query">Search query</label><input id="document-search-query" value="${escapeHtml(filters.query || '')}" placeholder="Vendor policy, escalation, retention, finance" /></div>
        <div><label class="permission-note" for="document-search-status">Status</label><select id="document-search-status">${renderSelectOptions([
          ['', 'All statuses'],
          ['draft', 'Draft'],
          ['in_review', 'In review'],
          ['approved', 'Approved'],
          ['published', 'Published'],
          ['archived', 'Archived'],
        ], filters.status || '')}</select></div>
        <div><label class="permission-note" for="document-search-class">Document class</label><select id="document-search-class">${renderSelectOptions([
          ['', 'All classes'],
          ...classes.map((entry) => [entry.document_class || '', entry.label || entry.document_class || 'Document']),
        ], filters.documentClass || '')}</select></div>
        <div><label class="permission-note" for="document-search-case-id">Case id</label><input id="document-search-case-id" value="${escapeHtml(filters.caseId || '')}" placeholder="request:req_001 or CASE-DOC-001" /></div>
        <div class="span-2"><label class="permission-note" for="document-search-active-only"><input id="document-search-active-only" type="checkbox"${filters.activeOnly ? ' checked' : ''} /> Active documents only</label></div>
        <div class="span-2 inline-actions">
          <button class="action-button" type="submit">Apply runtime search</button>
          <button class="action-button action-button-muted" type="button" data-document-filter-clear="true">Clear filters</button>
          ${scopedCaseId && !filters.caseId ? '<button class="action-button action-button-muted" type="button" data-document-filter-current-case="true">Use current case</button>' : ''}
        </div>
      </form>
      <div class="trace-box"><strong>Runtime retrieval</strong><p class="muted">${escapeHtml(retrievalActive ? `Showing ${summary.documents_total || 0} governed documents from the current runtime search.` : 'Showing the live document center surface. Apply a runtime search when you need to narrow the lane by query, status, class, or case.')}</p></div>
      ${pills.length ? `<div class="hero-chip-row">${pills.map((pill) => `<span class="pill">${escapeHtml(pill)}</span>`).join('')}</div>` : '<span class="permission-note">No retrieval filters are active.</span>'}
      ${keyValue([
        ['Visible results', String(summary.documents_total || 0)],
        ['Published', String(summary.published_total || 0)],
        ['In review', String(summary.in_review_total || 0)],
        ['Approved', String(summary.approved_total || 0)],
        ['Case linked', String(summary.case_linked_total || 0)],
      ])}
      ${classDistribution.length ? `<div class="trace-box"><strong>Class distribution</strong>${keyValue(classDistribution.map(([label, total]) => [titleCase(String(label).replaceAll('_', ' ')), String(total || 0)]))}</div>` : ''}
    </article>
  `;
}

function renderDocumentRuntimeContractCard(classes, classChips) {
  return `
    <article class="card stack">
      <div><div class="eyebrow muted">Document runtime contract</div><h3 class="card-title">What this lane guarantees</h3><p class="card-subtitle">This surface is about lifecycle control and readable retrieval, not just file storage.</p></div>
      <div class="hero-chip-row">${(classes.length ? classes : []).map((entry) => `<span class="pill">${escapeHtml(entry.label || entry.document_class || 'Document')} | ${escapeHtml(entry.prefix || '-')}</span>`).join('')}</div>
      ${classChips.length ? keyValue(classChips.map(([label, total]) => [titleCase(String(label).replaceAll('_', ' ')), String(total || 0)])) : '<p class="muted">No class distribution is available yet.</p>'}
      ${keyValue([
        ['Numbering', 'Class prefix plus year plus sequence'],
        ['Active version', 'Published revision stays active until a newer approved revision is published'],
        ['Lifecycle', 'Draft to review to approval to publish to supersede or archive'],
        ['Proof continuity', 'Documents can stay tied to cases, Human Ask, and audit history'],
      ])}
    </article>
  `;
}

function renderDocumentCard(item) {
  const currentRevision = item.current_revision || {};
  const activeRevision = item.active_revision || {};
  const summary = item.summary || {};
  const caseReference = renderCaseReferenceButton(item.case_id, item.case_status, {
    sourceView: 'documents',
    referenceId: item.document_id,
    contextLabel: 'governed document',
    label: item.case_id,
  });
  return `
    <article class="card stack case-card${isFocusedEntity('document', item.document_id) ? ' focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey('document', item.document_id))}">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">${escapeHtml(item.document_number || item.document_id || 'Document')}</div>
          <h3 class="card-title">${escapeHtml(item.title || 'Governed document')}</h3>
          <p class="card-subtitle">${escapeHtml(item.document_class_label || titleCase(item.document_class || 'document'))} | Updated ${shortTime(item.updated_at)}</p>
        </div>
        <div class="hero-chip-row">
          ${statusBadge(item.status || 'draft')}
          ${statusBadge(summary.active_revision_status || 'active revision')}
        </div>
      </div>
      ${keyValue([
        ['Owner', item.owner_id || '-'],
        ['Approver', item.approver_id || '-'],
        ['Retention', item.retention_code || '-'],
        ['Business domain', item.business_domain || '-'],
        ['Current revision', String(item.current_revision_number || 0)],
        ['Active revision', String(item.active_revision_number || 0)],
        ['Published revision', item.published_revision_number == null ? '-' : String(item.published_revision_number)],
      ])}
      <div class="trace-box"><strong>Active-version logic</strong><p class="muted">${escapeHtml(summary.active_version_logic || 'The current revision remains active until lifecycle rules move it forward.')}</p></div>
      <div class="split-grid">
        <article class="mini-card">
          <div class="eyebrow muted">Working revision</div>
          <strong>${escapeHtml(currentRevision.title || item.title || 'Current revision')}</strong>
          <p class="muted">${escapeHtml(formatStatusLabel(currentRevision.status || 'draft'))} | Updated ${escapeHtml(shortTime(currentRevision.updated_at))}</p>
          <span class="permission-note">Revision ${escapeHtml(String(currentRevision.revision_number || item.current_revision_number || 0))} | ${escapeHtml(currentRevision.updated_by || item.owner_id || '-')}</span>
        </article>
        <article class="mini-card">
          <div class="eyebrow muted">Active revision</div>
          <strong>${escapeHtml(activeRevision.title || item.title || 'Active revision')}</strong>
          <p class="muted">${escapeHtml(formatStatusLabel(activeRevision.status || item.status || 'active'))} | Updated ${escapeHtml(shortTime(activeRevision.updated_at || item.updated_at))}</p>
          <span class="permission-note">Revision ${escapeHtml(String(activeRevision.revision_number || item.active_revision_number || 0))} | Published ${escapeHtml(shortTime(activeRevision.published_at || ''))}</span>
        </article>
      </div>
      <div class="hero-chip-row">${(Array.isArray(item.tags) ? item.tags : []).slice(0, 4).map((tag) => `<span class="pill pill-muted">${escapeHtml(tag)}</span>`).join('') || '<span class="pill pill-muted">No tags</span>'}</div>
      <div class="trace-box"><strong>Case continuity</strong><p class="muted">${escapeHtml(item.case_reference ? `Document case reference: ${item.case_reference}.` : 'No originating case reference was written into this document yet.')}</p>${caseReference || '<span class="permission-note">This document is not yet stitched into a canonical dashboard case.</span>'}</div>
      <div class="inline-actions">
        ${renderDocumentActionButtons(item)}
        ${item.case_id ? `<button class="action-button" type="button" ${buildViewJumpAttributes({
          view: 'cases',
          focusType: 'case',
          focusId: item.case_id,
          caseId: item.case_id,
          title: `Case ${item.case_id} opened from document ${item.document_number || item.document_id}.`,
          detail: 'Use Cases to see the linked request, approval, Human Ask, and evidence story around this governed document.',
          actionLabel: 'Open Cases',
        })}>Open Cases</button>` : ''}
        <button class="action-button action-button-muted" type="button" data-view-jump="audit">Open Audit</button>
      </div>
    </article>
  `;
}

function renderDocumentEmptyState() {
  return `
    <article class="card stack case-card case-card-empty">
      <div>
        <div class="eyebrow muted">Document lane empty</div>
        <h3 class="card-title">No governed documents are active yet</h3>
        <p class="card-subtitle">As soon as a governed document is drafted, reviewed, published, or archived inside the runtime, it will appear here as a first-class operating object.</p>
      </div>
      <div class="inline-actions">
        <button class="action-button" type="button" data-document-clear="true">Clear editor</button>
        <button class="action-button action-button-muted" type="button" data-view-jump="cases">Open Cases</button>
        <button class="action-button action-button-muted" type="button" data-view-jump="overview">Open Overview</button>
      </div>
    </article>
  `;
}

function renderDocumentEditorCard(classes, editingDocument) {
  if (!can('documents.create')) {
    return `
      <article class="card stack">
        <div><div class="eyebrow muted">Document editor</div><h3 class="card-title">Read-only lane</h3><p class="card-subtitle">This profile can inspect documents, but document authoring and lifecycle changes remain gated to an operator or owner lane.</p></div>
        <div class="trace-box"><strong>Next governed move</strong><p class="muted">Follow the review or publish queue here, then switch to an authorized runtime lane when the document needs to move.</p></div>
      </article>
    `;
  }
  const currentRevision = editingDocument?.current_revision || {};
  const selectedClass = editingDocument?.document_class || classes[0]?.document_class || 'policy';
  const tagsValue = Array.isArray(editingDocument?.tags) ? editingDocument.tags.join(', ') : '';
  const metadataValue = formatDocumentEditorMetadata(currentRevision.metadata || {});
  const caseId = editingDocument?.case_reference || editingDocument?.case_id || getActionContextCaseId() || '';
  const editingClosedRevision = ['published', 'superseded', 'archived'].includes(String(currentRevision.status || '').trim());
  return `
    <article class="card stack">
      <div><div class="eyebrow muted">Document editor</div><h3 class="card-title">${editingDocument ? 'Continue governed document work' : 'Create governed document'}</h3><p class="card-subtitle">${editingDocument ? (editingClosedRevision ? 'Saving from this editor will create the next working revision because the current revision is already closed.' : 'Update the working draft and keep the same governed document in motion.') : 'Start a governed document with numbering, case linkage, lifecycle metadata, and a runtime-owned revision from the same lane.'}</p></div>
      ${editingDocument ? `<div class="trace-box"><strong>Editing</strong><p class="muted">${escapeHtml(editingDocument.document_number || editingDocument.document_id || 'Document')} | ${escapeHtml(formatStatusLabel(currentRevision.status || editingDocument.status || 'draft'))}</p></div>` : ''}
      <form id="document-form" class="composer-grid">
        <div><label class="permission-note" for="document-title">Title</label><input id="document-title" value="${escapeHtml(editingDocument?.title || '')}" placeholder="Vendor Risk Policy" /></div>
        <div><label class="permission-note" for="document-class">Document class</label><select id="document-class">${classes.map((entry) => `<option value="${escapeHtml(entry.document_class || '')}"${String(entry.document_class || '') === String(selectedClass || '') ? ' selected' : ''}>${escapeHtml(entry.label || entry.document_class || 'Document')}</option>`).join('')}</select></div>
        <div><label class="permission-note" for="document-case-id">Case id</label><input id="document-case-id" value="${escapeHtml(caseId)}" placeholder="request:req_001 or CASE-DOC-001" /></div>
        <div><label class="permission-note" for="document-owner-id">Owner id</label><input id="document-owner-id" value="${escapeHtml(editingDocument?.owner_id || studioExecutiveOwnerId())}" placeholder="EXEC_OWNER" /></div>
        <div><label class="permission-note" for="document-approver-id">Approver id</label><input id="document-approver-id" value="${escapeHtml(editingDocument?.approver_id || 'REVIEW_OWNER')}" placeholder="LEGAL_OWNER" /></div>
        <div><label class="permission-note" for="document-retention-code">Retention code</label><input id="document-retention-code" value="${escapeHtml(editingDocument?.retention_code || '')}" placeholder="RET-POL-7Y" /></div>
        <div><label class="permission-note" for="document-business-domain">Business domain</label><input id="document-business-domain" value="${escapeHtml(editingDocument?.business_domain || '')}" placeholder="legal_operations" /></div>
        <div><label class="permission-note" for="document-tags">Tags</label><input id="document-tags" value="${escapeHtml(tagsValue)}" placeholder="policy, vendor, legal" /></div>
        <div class="span-2"><label class="permission-note" for="document-content">Document content</label><textarea id="document-content" placeholder="Write the governed document body here.">${escapeHtml(currentRevision.content || '')}</textarea></div>
        <div class="span-2"><label class="permission-note" for="document-metadata">Metadata (JSON)</label><textarea id="document-metadata" placeholder='{"region": "th", "criticality": "medium"}'>${escapeHtml(metadataValue)}</textarea></div>
        <div class="span-2"><label class="permission-note" for="document-change-note">Change note</label><textarea id="document-change-note" placeholder="Explain what changed in this revision.">${escapeHtml(currentRevision.change_note || '')}</textarea></div>
        <div class="span-2 inline-actions">
          <button class="action-button" type="submit">${editingDocument ? (editingClosedRevision ? 'Create Next Revision' : 'Save Draft') : 'Create Document'}</button>
          <button class="action-button action-button-muted" type="button" data-document-clear="true">Clear editor</button>
        </div>
      </form>
    </article>
  `;
}

function renderDocumentWorkQueues(items) {
  return `
    <article class="card stack">
      <div><div class="eyebrow muted">Document work lanes</div><h3 class="card-title">Review and publish queues</h3><p class="card-subtitle">These queues tell you whether the document runtime is waiting on authoring, approval, or controlled release.</p></div>
      ${items.length ? items.map((item) => `
        <div class="trace-box">
          <strong>${escapeHtml(item.title || 'Document queue')}</strong>
          <p class="muted">${escapeHtml(item.next_step || 'Continue inside the governed document lane.')}</p>
          ${keyValue([
            ['Disposition', formatStatusLabel(item.disposition || 'monitoring')],
            ['Open items', String(item.total || 0)],
            ['Oldest age (hrs)', String(item.oldest_age_hours || 0)],
            ['Sample refs', (item.sample_references || []).join(', ') || '-'],
          ])}
          <div class="inline-actions">
            <button class="action-button" type="button" ${buildViewJumpAttributes({
              view: 'documents',
              title: `${item.title || 'Document queue'} opened.`,
              detail: item.operator_note || item.next_step || 'Continue in the governed document lane.',
              actionLabel: 'Open Documents',
            })}>Open Documents</button>
          </div>
        </div>`).join('') : '<p class="muted">No document review or publish queues are active right now. Draft, review, and publish work will appear here as soon as the runtime needs attention.</p>'}
    </article>
  `;
}

function renderSelectOptions(options, selectedValue = '') {
  return options.map(([value, label]) => `<option value="${escapeHtml(value || '')}"${String(value || '') === String(selectedValue || '') ? ' selected' : ''}>${escapeHtml(label || value || '')}</option>`).join('');
}

function renderDocumentActionButtons(item) {
  const currentStatus = String(item.current_revision?.status || item.status || 'draft').trim();
  const actions = [];
  if (can('documents.create')) {
    const loadLabel = ['published', 'superseded', 'archived'].includes(currentStatus) ? 'Prepare next revision' : 'Load into editor';
    actions.push(`<button class="action-button" type="button" data-document-action="load" data-document-id="${escapeHtml(item.document_id || '')}">${loadLabel}</button>`);
    if (currentStatus === 'draft') {
      actions.push(`<button class="action-button action-button-muted" type="button" data-document-action="submit-review" data-document-id="${escapeHtml(item.document_id || '')}">Submit review</button>`);
    }
  }
  if (can('documents.review') && currentStatus === 'in_review') {
    actions.push(`<button class="action-button" type="button" data-document-action="approve" data-document-id="${escapeHtml(item.document_id || '')}">Approve</button>`);
  }
  if (can('documents.publish') && currentStatus === 'approved') {
    actions.push(`<button class="action-button" type="button" data-document-action="publish" data-document-id="${escapeHtml(item.document_id || '')}">Publish</button>`);
  }
  if (can('documents.archive') && ['draft', 'in_review', 'approved', 'published'].includes(currentStatus)) {
    actions.push(`<button class="action-button action-button-muted" type="button" data-document-action="archive" data-document-id="${escapeHtml(item.document_id || '')}">Archive</button>`);
  }
  return actions.join('');
}

function getDocumentById(snapshot, documentId = '') {
  const normalizedDocumentId = String(documentId || '').trim();
  if (!normalizedDocumentId) return null;
  const items = Array.isArray(snapshot?.documents?.items) ? snapshot.documents.items : [];
  return items.find((item) => String(item.document_id || '').trim() === normalizedDocumentId) || null;
}

function formatDocumentEditorMetadata(metadata) {
  if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata) || !Object.keys(metadata).length) return '';
  return JSON.stringify(metadata, null, 2);
}

function buildDocumentPayload(documentRef) {
  return {
    title: documentRef.getElementById('document-title')?.value.trim() || '',
    document_class: documentRef.getElementById('document-class')?.value.trim() || 'policy',
    case_id: documentRef.getElementById('document-case-id')?.value.trim() || getActionContextCaseId() || '',
    owner_id: documentRef.getElementById('document-owner-id')?.value.trim() || '',
    approver_id: documentRef.getElementById('document-approver-id')?.value.trim() || '',
    retention_code: documentRef.getElementById('document-retention-code')?.value.trim() || '',
    business_domain: documentRef.getElementById('document-business-domain')?.value.trim() || '',
    tags: parseListField('document-tags'),
    content: documentRef.getElementById('document-content')?.value || '',
    metadata: parseJsonField('document-metadata'),
    change_note: documentRef.getElementById('document-change-note')?.value.trim() || '',
  };
}

function clearDocumentEditor() {
  state.documentEditingId = null;
  setInputValue('document-title', '');
  setSelectValue('document-class', 'policy');
  setInputValue('document-case-id', getActionContextCaseId() || '');
  setInputValue('document-owner-id', studioExecutiveOwnerId());
  setInputValue('document-approver-id', 'REVIEW_OWNER');
  setInputValue('document-retention-code', '');
  setInputValue('document-business-domain', '');
  setInputValue('document-tags', '');
  setInputValue('document-content', '');
  setInputValue('document-metadata', '');
  setInputValue('document-change-note', '');
}

function fillDocumentForm(item) {
  if (!item) return;
  const currentRevision = item.current_revision || {};
  state.documentEditingId = item.document_id || null;
  setInputValue('document-title', item.title || '');
  setSelectValue('document-class', item.document_class || 'policy');
  setInputValue('document-case-id', item.case_reference || item.case_id || '');
  setInputValue('document-owner-id', item.owner_id || studioExecutiveOwnerId());
  setInputValue('document-approver-id', item.approver_id || 'REVIEW_OWNER');
  setInputValue('document-retention-code', item.retention_code || '');
  setInputValue('document-business-domain', item.business_domain || '');
  setInputValue('document-tags', Array.isArray(item.tags) ? item.tags.join(', ') : '');
  setInputValue('document-content', currentRevision.content || '');
  setInputValue('document-metadata', formatDocumentEditorMetadata(currentRevision.metadata || {}));
  setInputValue('document-change-note', currentRevision.change_note || '');
}

function loadDocumentIntoEditor(documentId) {
  const item = getDocumentById(state.snapshot, documentId);
  if (!item) throw new Error('The selected governed document is no longer available in the current snapshot.');
  fillDocumentForm(item);
}

function focusDocumentEditor() {
  window.requestAnimationFrame(() => {
    const anchor = document.getElementById('document-title');
    if (anchor) anchor.focus({ preventScroll: true });
  });
}

function buildViewJumpAttributes({ view = '', controlRoomTool = '', focusType = '', focusId = '', caseId = '', title = '', detail = '', actionLabel = '' } = {}) {
  const resolved = normalizeActionContextTarget({ view, controlRoomTool, title, detail, actionLabel });
  const attrs = [`data-view-jump="${escapeHtml(resolved.view || 'overview')}"`];
  if (resolved.controlRoomTool) attrs.push(`data-view-jump-control-room-tool="${escapeHtml(resolved.controlRoomTool)}"`);
  if (focusType) attrs.push(`data-view-jump-focus-type="${escapeHtml(focusType)}"`);
  if (focusId) attrs.push(`data-view-jump-focus-id="${escapeHtml(focusId)}"`);
  if (caseId) attrs.push(`data-view-jump-case-id="${escapeHtml(caseId)}"`);
  if (resolved.title) attrs.push(`data-view-jump-title="${escapeHtml(resolved.title)}"`);
  if (resolved.detail) attrs.push(`data-view-jump-detail="${escapeHtml(resolved.detail)}"`);
  if (resolved.actionLabel) attrs.push(`data-view-jump-action-label="${escapeHtml(resolved.actionLabel)}"`);
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
  if (view === 'documents') {
    const documentId = (item.linked_document_ids || [])[0] || '';
    return { entityType: documentId ? 'document' : '', entityId: documentId };
  }
  if (view === 'actions') {
    const actionId = (item.linked_action_ids || [])[0] || '';
    return { entityType: actionId ? 'action' : '', entityId: actionId };
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
  const nextMoveView = pendingOverrides.length ? 'overrides' : conflicts.length ? 'conflicts' : requests.length ? 'audit' : 'requests';
  const nextMoveLabel = VIEW_TITLES[nextMoveView] || titleCase(nextMoveView);
  const nextMoveTitle = pendingOverrides.length
    ? 'Resolve the human boundary before adding more demand'
    : conflicts.length
      ? 'Unblock the conflicted request path'
      : requests.length
        ? 'Confirm the latest request finished cleanly'
        : 'Submit the first governed request';
  const nextMoveDetail = pendingOverrides.length
    ? 'The queue already contains requests that need a real human approval or veto before governed execution may continue.'
    : conflicts.length
      ? 'The queue is still alive, but conflicted requests should be cleared before the operator adds pressure to the same runtime corridor.'
      : requests.length
        ? 'No new human boundary is stopping the queue right now. The best move is to confirm the latest governed request outcome and keep intake disciplined.'
        : 'Requests becomes useful the moment one real governed action enters the runtime with role, payload, and boundary context.';
  const composer = can('request.create')
    ? renderRequestComposer(snapshot.roles || [])
    : `<article class="card notice-card stack"><strong>Request composer</strong><p class="permission-note">This profile does not have request.create permission.</p></article>`;
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div class="hero-heading">
          <div>
            <div class="eyebrow muted">Runtime Intake Command</div>
            <h2 class="hero-title">See demand clearly, stop at the right human boundary, and keep governed intake moving.</h2>
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
            <p>Use Requests when new governed work is entering the runtime. The goal is not to inspect plumbing. The goal is to see whether demand can keep flowing, must stop for a human, or is colliding with contention.</p>
          </div>
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">What changes the queue right now?</div>
          <h3 class="card-title">${escapeHtml(nextMoveTitle)}</h3>
          <p class="card-subtitle">${escapeHtml(nextMoveDetail)}</p>
        </div>
        ${keyValue([
          ['Latest request', latestRequestLabel],
          ['Recommended lane', nextMoveLabel],
          ['Pending overrides', String(pendingOverrides.length)],
          ['Conflicts', String(conflicts.length)],
          ['Execution model', 'Governed private runtime'],
        ])}
        <div class="inline-actions">
          ${renderViewJumpButton({ view: nextMoveView, label: `Open ${nextMoveLabel}`, className: 'action-button', title: `${nextMoveLabel} reopened from Requests.`, detail: nextMoveDetail, actionLabel: `Open ${nextMoveLabel}` })}
          ${renderViewJumpButton({ view: 'audit', label: 'Open Audit', className: 'action-button action-button-muted', title: 'Audit reopened from Requests.', detail: 'Use Audit to confirm what happened after a governed request crossed the intake lane.', actionLabel: 'Open Audit' })}
        </div>
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
        <div><div class="eyebrow muted">Before you submit</div><h3 class="card-title">What strong requests include</h3><p class="card-subtitle">Good intake keeps the runtime readable after execution, not just before it.</p></div>
        ${keyValue([
          ['Payload quality', 'Structured JSON with explicit resource context'],
          ['Consistency discipline', 'Idempotency key plus event ordering metadata'],
          ['Role targeting', 'Choose a trusted role or leave it blank for context-aware routing'],
          ['Review posture', pendingOverrides.length ? 'Expect a human boundary when the risk is already visible' : 'No active review bottleneck is visible now'],
        ])}
        <div class="trace-box"><strong>Recommended metadata</strong><p class="muted">Pair each governed request with an idempotency key, event stream, and event sequence whenever the action touches mutable records or recurring workflows.</p></div>
      </article>
      <article class="card stack">
        <div><div class="eyebrow muted">After you submit</div><h3 class="card-title">Move to the right lane instead of guessing</h3><p class="card-subtitle">Requests should tell you where to go next when the runtime changes state.</p></div>
        ${keyValue([
          ['If the request stayed autonomous', 'Open Audit to confirm outcome and policy basis'],
          ['If the request escalated', 'Open Overrides to see who must approve or veto'],
          ['If the request conflicted', 'Open Conflicts to inspect locks before retrying'],
          ['If the role changed', 'Stay in Requests to review activation source and switch reason'],
        ])}
        <div class="inline-actions">
          ${renderViewJumpButton({ view: 'overrides', label: 'Open Overrides', className: 'action-button', title: 'Overrides reopened from Requests.', detail: 'Use Overrides when the queue already crossed a human boundary.', actionLabel: 'Open Overrides' })}
          ${renderViewJumpButton({ view: 'conflicts', label: 'Open Conflicts', className: 'action-button action-button-muted', title: 'Conflicts reopened from Requests.', detail: 'Use Conflicts when contention, locks, or ordering pressure stopped the path.', actionLabel: 'Open Conflicts' })}
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
    renew_soon: 'Renew Soon',
    reconnect_now: 'Reconnect Now',
    idle_lock_soon: 'Idle Lock Soon',
    sign_in_again: 'Sign In Again',
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
    ? `<div class="transition-route"><span class="transition-node">${escapeHtml(previousRole)}</span><span class="transition-arrow">-&gt;</span><span class="transition-node transition-node-active">${escapeHtml(newRole)}</span></div>`
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
    ? `<div class="transition-route"><span class="transition-node">${escapeHtml(role.role_id)}</span><span class="transition-arrow">-&gt;</span><span class="transition-node">${escapeHtml(role.reports_to)}</span><span class="transition-arrow">-&gt;</span><span class="transition-node transition-node-active">${escapeHtml(role.escalation_to || role.reports_to)}</span></div>`
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
  state.documentEditingId = null;
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

function canAccessControlRoom() {
  if (!state.session) return false;
  if (state.session.control_room_access) return true;
  const role = String(state.session.role_name || '').toLowerCase();
  if (['owner', 'founder', 'admin', 'it'].includes(role)) return true;
  return can('ops.manage') && can('health.read') && can('audit.read');
}


function canAccessSetupAssistant() {
  if (!state.session) return false;
  if (typeof state.session.setup_assistant_access === 'boolean') return state.session.setup_assistant_access;
  const role = String(state.session.role_name || '').toLowerCase();
  if (['owner', 'founder', 'admin', 'it'].includes(role)) return true;
  return can('ops.manage');
}

function renderSetupAssistantDenied() {
  return `
    <article class="card notice-card notice-warning stack">
      <div>
        <div class="eyebrow muted">Setup surface restricted</div>
        <h3 class="card-title">Setup Assistant is reserved for owner, admin, and IT sessions</h3>
        <p class="card-subtitle">Normal users stay on the simple command surface while onboarding, diagnostics, and pilot hardening remain inside a privileged setup lane.</p>
      </div>
      <div class="inline-actions">
        <button class="action-button" type="button" data-view-jump="overview">Open Home</button>
        <button class="action-button action-button-muted" type="button" data-view-jump="requests">Open Work Inbox</button>
      </div>
    </article>
  `;
}

function syncCommandRoute() {
  const desiredPath = state.view === 'control_room' ? '/control-room' : '/';
  if ((window.location.pathname || '/') !== desiredPath) {
    window.history.replaceState({}, '', desiredPath);
  }
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
