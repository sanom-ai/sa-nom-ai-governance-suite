export function buildHumanAskPayload(documentRef) {
  const mode = documentRef.getElementById('human-ask-mode')?.value.trim() || 'report';
  const directoryEntryId = documentRef.getElementById('human-ask-target')?.value.trim() || '';
  const selectedMeetingRoles = Array.from(documentRef.querySelectorAll('input[name="human-ask-meeting-role"]:checked'))
    .map((input) => input.value.trim().toUpperCase())
    .filter(Boolean);
  const meetingRolesRaw = documentRef.getElementById('human-ask-meeting-roles')?.value.trim() || '';
  const prompt = documentRef.getElementById('human-ask-prompt')?.value.trim() || '';
  const parentSessionId = documentRef.getElementById('human-ask-parent')?.value.trim() || '';
  const inheritanceMode = documentRef.getElementById('human-ask-inheritance')?.value.trim() || 'inherit';
  const payload = {
    mode,
    prompt,
    parent_session_id: parentSessionId,
    inheritance_mode: inheritanceMode,
  };
  if (mode === 'meeting') {
    payload.participant_role_ids = [
      ...selectedMeetingRoles,
      ...meetingRolesRaw
        .split(',')
        .map((item) => item.trim().toUpperCase())
        .filter(Boolean),
    ].filter((value, index, list) => list.indexOf(value) === index);
    if (!payload.participant_role_ids.length && directoryEntryId) {
      payload.directory_entry_id = directoryEntryId;
    }
  } else {
    payload.directory_entry_id = directoryEntryId;
  }
  return payload;
}

export async function handleHumanAskAction({
  button,
  apiFetch,
  setMessage,
  setHumanAskView,
  loadDashboard,
  setActionContext,
  windowRef,
}) {
  const action = button.dataset.humanAskAction;
  if (action === 'request-entry-record') {
    const entryId = button.dataset.entryId || '';
    const displayName = button.dataset.entryLabel || 'the selected role';
    const prompt = windowRef.prompt(`Start a report from ${displayName}`, 'Report current posture, key findings, and the next safe action.');
    if (prompt === null) return true;
    const response = await apiFetch('/api/human-ask/sessions', {
      method: 'POST',
      body: JSON.stringify({
        mode: 'report',
        prompt,
        directory_entry_id: entryId,
        inheritance_mode: 'reset',
      }),
    });
    const item = response.item || response;
    const sessionId = item.session_id || item.metadata?.session_id || '';
    setMessage(buildHumanAskOutcomeMessage(item, `Human Ask record created for ${displayName}.`));
    if (typeof setActionContext === 'function') {
      setActionContext({
        entityType: 'human_ask_session',
        entityId: sessionId,
        view: 'human_ask',
        title: sessionId ? `Human Ask record ${sessionId} opened for ${displayName}.` : `Human Ask record opened for ${displayName}.`,
        detail: 'The new governed record stays highlighted in the transcript lane for immediate follow-through.',
        actionLabel: 'Open Human Ask records',
      });
    }
    setHumanAskView();
    await loadDashboard();
    return true;
  }
  if (action === 'studio-record') {
    const requestId = button.dataset.requestId || '';
    const roleLabel = button.dataset.entryLabel || requestId;
    const prompt = windowRef.prompt(`Start a report from ${roleLabel}`, 'Report readiness, structural posture, and the next safe review action.');
    if (prompt === null) return true;
    const response = await apiFetch(`/api/role-private-studio/requests/${encodeURIComponent(requestId)}/human-ask-record`, {
      method: 'POST',
      body: JSON.stringify({ mode: 'report', prompt }),
    });
    const item = response.item || response;
    const sessionId = item.session_id || item.metadata?.session_id || '';
    setMessage(buildHumanAskOutcomeMessage(item, `Human Ask record created from Studio draft ${requestId}.`));
    if (typeof setActionContext === 'function') {
      setActionContext({
        entityType: 'human_ask_session',
        entityId: sessionId,
        view: 'human_ask',
        title: sessionId ? `Human Ask record ${sessionId} opened from Studio draft ${requestId}.` : `Human Ask record opened from Studio draft ${requestId}.`,
        detail: 'The generated record stays highlighted in the Human Ask transcript lane for the next governed review step.',
        actionLabel: 'Open Human Ask records',
      });
    }
    setHumanAskView();
    await loadDashboard();
    return true;
  }
  return false;
}

function formatOperatingModeLabel(mode) {
  return String(mode || 'direct').toLowerCase() === 'indirect' ? 'Indirect' : 'Direct';
}

function formatOperatingResponsibility(target) {
  const mode = String(target?.operating_mode || 'direct').toLowerCase();
  if (mode === 'indirect') {
    const humanOwner = target?.assigned_user_id || 'Assigned human';
    const seat = target?.seat_id ? ` | Seat ${target.seat_id}` : '';
    return `${humanOwner}${seat}`;
  }
  const executiveOwner = target?.executive_owner_id || 'Executive owner';
  const seat = target?.seat_id ? ` | Seat ${target.seat_id}` : '';
  return `${executiveOwner}${seat}`;
}

export function renderHumanAsk(humanAsk, { can, helpers }) {
  const {
    escapeHtml,
    keyValue,
    metricCard,
    shortTime,
    statusBadge,
    titleCase,
    buildFocusKey,
    isFocusedEntity,
    renderCaseReferenceButton,
  } = helpers;
  const summary = humanAsk.summary || {};
  const directory = humanAsk.callable_directory || { summary: {}, entries: [] };
  const sessions = sortHumanAskSessionsForRecordView(humanAsk.sessions || []);
  const canCreate = can('human_ask.create');
  return `
    <section class="overview-hero">
      <article class="card hero-card hero-card-primary">
        <div>
          <div class="eyebrow muted">Governed Record Surface</div>
          <h3 class="card-title">Human Ask</h3>
          <p class="card-subtitle">Start a governed report or meeting record while the Director keeps transcript, scope, and structural posture together.</p>
        </div>
        <div class="hero-metrics">
          ${metricCard('Records', summary.recorded_total || 0, 'accent', 'Governed Human Ask records currently preserved in runtime.')}
          ${metricCard('Callable', summary.callable_total || 0, 'success', 'Published roles and Studio drafts currently callable.')}
          ${metricCard('Waiting human', summary.waiting_human_total || 0, (summary.waiting_human_total || 0) ? 'warning' : 'success', 'Only records that reached a human-only or out-of-scope boundary should pause here.')}
          ${metricCard('Studio callable', summary.studio_callable_total || 0, 'accent', 'Draft hats callable straight from Role Private Studio.')}
        </div>
      </article>
      <article class="card hero-card hero-card-secondary">
        <div>
          <div class="eyebrow muted">Current Surface</div>
          <h3 class="card-title">Report and meeting records</h3>
          <p class="card-subtitle">Use this page to open one-hat report records or multi-hat meeting records from the same surface.</p>
        </div>
        ${keyValue([
          ['Report sessions', String(summary.report_total || 0)],
          ['Meeting sessions', String(summary.meeting_total || 0)],
          ['Recorded sessions', String(summary.recorded_total || 0)],
          ['Follow-up chains', String(summary.follow_up_total || 0)],
        ])}
      </article>
    </section>
    <section class="metrics-grid metrics-grid-luxury">
      ${metricCard('Published callable', summary.published_callable_total || 0, 'success', 'Published hats available to the Director right now.')}
      ${metricCard('Studio callable', summary.studio_callable_total || 0, 'accent', 'Draft hats callable straight from Role Private Studio.')}
      ${metricCard('Recorded sessions', summary.recorded_total || 0, 'accent', 'All report records and meeting records currently preserved.')}
      ${metricCard('Multi-hat', summary.multi_participant_total || 0, 'accent', 'Meeting sessions or other multi-participant flows visible in this runtime window.')}
      ${metricCard('Human boundary', summary.waiting_human_total || 0, (summary.waiting_human_total || 0) ? 'warning' : 'default', 'Records currently waiting on a real human because the request crossed JD scope or human-only boundaries.')}
      ${metricCard('Escalated', summary.escalated_total || 0, (summary.escalated_total || 0) ? 'warning' : 'default', 'Sessions that crossed into governed escalation lanes.')}
      ${metricCard('Blocked', summary.blocked_total || 0, (summary.blocked_total || 0) ? 'danger' : 'default', 'Sessions blocked by callable or structural posture.')}
      ${metricCard('Follow-up chains', summary.follow_up_total || 0, 'default', 'Records that inherited context from an earlier Human Ask session.')}
    </section>
    <section class="split-grid">
      ${renderHumanAskComposer(directory, sessions, canCreate, { escapeHtml, keyValue, shortTime })}
      ${renderHumanAskDirectory(directory.entries || [], canCreate, { can, escapeHtml, keyValue, statusBadge })}
    </section>
    <section class="card stack">
      <div class="hero-heading">
        <div>
          <div class="eyebrow muted">Transcript Baseline</div>
          <h3 class="card-title">Recent Human Ask records</h3>
          <p class="card-subtitle">Each record keeps the prompt, transcript, and boundary trace together for later review.</p>
        </div>
      </div>
      ${sessions.length ? `<div class="stack">${sessions.map((session) => renderHumanAskSessionCard(session, { escapeHtml, keyValue, shortTime, statusBadge, titleCase, buildFocusKey, isFocusedEntity, renderCaseReferenceButton })).join('')}</div>` : `<div class="empty-state-shell"><div class="hero-heading"><div><div class="eyebrow muted">Transcript lane idle</div><strong>No Human Ask records exist yet.</strong><p class="muted">Start a governed report or meeting record from the console above, and the first transcript will appear here with scope, posture, and evidence context attached.</p></div><div class="hero-chip-row"><span class="pill">record lane empty</span><span class="pill">start from console</span></div></div></div>`}
    </section>
  `;
}

function renderHumanAskComposer(directory, sessions, canCreate, helpers) {
  const { escapeHtml, keyValue, shortTime } = helpers;
  const entries = Array.isArray(directory.entries) ? directory.entries : [];
  const meetingEntries = entries.filter((entry) => entry.callable).slice(0, 8);
  const roleOptions = entries.length
    ? entries.map((entry) => `<option value="${escapeHtml(entry.entry_id)}">${escapeHtml(`${entry.display_name} | ${entry.source} | ${entry.callable_status}`)}</option>`).join('')
    : '<option value="">No callable entries</option>';
  const parentOptions = ['<option value="">No parent session</option>', ...sessions.map((session) => `<option value="${escapeHtml(session.session_id)}">${escapeHtml(`${session.summary?.participant || session.session_id} | ${shortTime(session.updated_at)}`)}</option>`)].join('');
  const disabledState = canCreate ? '' : ' disabled';
  const meetingHint = entries.length
    ? entries.slice(0, 6).map((entry) => entry.role_id).join(', ')
    : 'GOV, LEGAL';
  const modeGuidance = keyValue([
    ['Report', 'One hat answers inside one governed record'],
    ['Meeting', 'Several hats respond inside one governed record'],
  ]);
  const footer = canCreate
    ? '<p class="permission-note">Follow-up chains can inherit context from a parent session. Meeting mode also accepts comma-separated role ids.</p>'
    : '<p class="permission-note">This profile can read records but cannot create new ones.</p>';
  const callableCount = entries.filter((entry) => entry.callable).length;
  const consoleChips = [
    `${callableCount} callable hats`,
    `${meetingEntries.length} meeting-ready`,
    `${sessions.length} parent sessions`,
  ];
  return `
    <article class="card stack human-ask-console-card">
      <div class="human-ask-console-hero">
        <div class="human-ask-console-copy">
          <div class="eyebrow muted">Record Console</div>
          <h3 class="card-title">Create a governed report or meeting record</h3>
          <p class="card-subtitle">Create one report lane or one multi-hat record without leaving the Director surface.</p>
        </div>
        <div class="human-ask-console-chip-row">${consoleChips.map((label, index) => `<span class="status-chip human-ask-console-chip${index === 0 ? '' : ' human-ask-console-chip-soft'}">${escapeHtml(label)}</span>`).join('')}</div>
      </div>
      <div class="human-ask-console-grid">
        <div class="trace-box compact-trace human-ask-console-panel">
          <strong>Mode guidance</strong>
          <p class="muted">Use Report for one hat. Use Meeting when several hats should answer inside the same record.</p>
          ${modeGuidance}
        </div>
        <div class="trace-box compact-trace human-ask-console-panel human-ask-console-panel-accent">
          <strong>Meeting quick hint</strong>
          <p class="muted">${escapeHtml(`Use role ids such as ${meetingHint}. The first resolved hat becomes the primary lane for the shared record.`)}</p>
        </div>
      </div>
      <form id="human-ask-form" class="composer-grid human-ask-console-form">
        <div>
          <label class="permission-note" for="human-ask-mode">Mode</label>
          <select id="human-ask-mode"${disabledState}>
            <option value="report">Report</option>
            <option value="meeting">Meeting</option>
          </select>
        </div>
        <div>
          <label class="permission-note" for="human-ask-target">Target</label>
          <select id="human-ask-target"${disabledState}>${roleOptions}</select>
        </div>
        <div>
          <label class="permission-note" for="human-ask-parent">Parent session</label>
          <select id="human-ask-parent"${disabledState}>${parentOptions}</select>
        </div>
        <div>
          <label class="permission-note" for="human-ask-inheritance">Inheritance mode</label>
          <select id="human-ask-inheritance"${disabledState}>
            <option value="inherit">Inherit full context</option>
            <option value="trim">Inherit summary only</option>
            <option value="reset">Reset context</option>
          </select>
        </div>
        <div class="composer-span">
          <label class="permission-note" for="human-ask-meeting-roles">Meeting participant roles</label>
          <input id="human-ask-meeting-roles" type="text" placeholder="${escapeHtml(meetingHint)}"${disabledState}>
        </div>
        <div class="composer-span human-ask-console-picker-shell">
          <div class="trace-box compact-trace human-ask-console-panel human-ask-console-picker">
            <strong>Meeting participant picker</strong>
            ${meetingEntries.length ? `<div class="human-ask-picker-grid">${meetingEntries.map((entry) => `
              <label class="human-ask-picker-card">
                <input type="checkbox" name="human-ask-meeting-role" value="${escapeHtml(entry.role_id)}"${disabledState}>
                <span class="human-ask-picker-copy">
                  <span class="human-ask-picker-role">${escapeHtml(entry.role_id)}</span>
                  <span class="human-ask-picker-name">${escapeHtml(entry.display_name || entry.role_id)}</span>
                </span>
              </label>
            `).join('')}</div>` : '<p class="muted">No callable roles available for meeting selection.</p>'}
          </div>
        </div>
        <div class="composer-span">
          <label class="permission-note" for="human-ask-prompt">Prompt</label>
          <textarea id="human-ask-prompt" rows="5" placeholder="Ask for posture, findings, and the next safe action."${disabledState}></textarea>
        </div>
        <div class="composer-span human-ask-console-action-row inline-actions">
          <button class="action-button" type="submit"${disabledState}>Create Governed Record</button>
        </div>
      </form>
      <div class="human-ask-console-footer">${footer}</div>
    </article>
  `;
}
function renderHumanAskDirectory(entries, canCreate, helpers) {
  const { escapeHtml, keyValue, statusBadge } = helpers;
  if (!entries.length) {
    return `<article class="card stack"><div><div class="eyebrow muted">Callable Directory</div><h3 class="card-title">No callable entries</h3><p class="card-subtitle">Published roles and studio drafts appear here when callable.</p></div></article>`;
  }
  const cards = entries.slice(0, 10).map((entry) => {
    const actions = canCreate && entry.callable
      ? `<button class="action-button action-button-muted" data-human-ask-action="request-entry-record" data-entry-id="${escapeHtml(entry.entry_id)}" data-entry-label="${escapeHtml(entry.display_name)}">Start Report</button>`
      : '';
    return `
      <article class="trace-box stack compact-trace human-ask-directory-card">
        <div class="hero-heading">
          <div>
            <strong>${escapeHtml(entry.display_name)}</strong>
            <p class="muted">${escapeHtml(`${entry.role_id} | ${entry.source}`)}</p>
          </div>
          <div class="status-row">
            ${statusBadge(entry.callable_status || 'available')}
            ${statusBadge(entry.pt_oss_posture || 'unknown')}
          </div>
        </div>
        ${keyValue([
          ['Domain', entry.business_domain || '-'],
          ['Operating mode', formatOperatingModeLabel(entry.operating_mode || 'direct')],
          ['Responsibility', formatOperatingResponsibility(entry)],
          ['Escalation owner', entry.escalation_owner || '-'],
          ['Safety owner', entry.safety_owner || '-'],
          ['Publication', entry.publication_status || '-'],
          ['PT-OSS score', String(entry.pt_oss_readiness_score || 0)],
        ])}
        <p class="muted">${escapeHtml(entry.summary || 'No summary available.')}</p>
        ${entry.notes?.length ? `<div class="trace-box compact-trace"><strong>Notes</strong><p class="muted">${escapeHtml(entry.notes.join(' | '))}</p></div>` : ''}
        ${actions ? `<div class="inline-actions">${actions}</div>` : ''}
      </article>
    `;
  }).join('');
  return `
    <article class="card stack">
      <div>
        <div class="eyebrow muted">Callable Directory</div>
        <h3 class="card-title">Current callable roles and drafts</h3>
        <p class="card-subtitle">Use this list to start a report from any callable role or draft.</p>
      </div>
      <div class="human-ask-directory-grid">${cards}</div>
    </article>
  `;
}

function renderHumanAskSessionCard(session, helpers) {
  const { escapeHtml, keyValue, shortTime, statusBadge, titleCase, buildFocusKey, isFocusedEntity, renderCaseReferenceButton } = helpers;
  const decision = session.decision_summary || {};
  const participant = session.participant || {};
  const participants = Array.isArray(session.metadata?.participants) ? session.metadata.participants : [];
  const meetingOverview = session.metadata?.meeting_overview || null;
  const sessionRecord = session.metadata?.session_record || null;
  const directorDisposition = session.metadata?.director_disposition || session.summary?.director_disposition || 'ready_to_proceed';
  const transcript = Array.isArray(session.transcript) ? session.transcript : [];
  const modeLabel = formatHumanAskModeLabel(session.mode || 'report');
  const humanAttention = formatHumanAskHumanAttention(decision, directorDisposition);
  const participantChips = participants.length
    ? `<div class="human-ask-participant-row">${participants.map((item) => `<span class="status-chip status-chip-muted">${escapeHtml(`${item.role_id || '-'} | ${item.display_name || '-'} | ${formatOperatingModeLabel(item.operating_mode || 'direct')}`)}</span>`).join('')}</div>`
    : '';
  const meetingOverviewCard = meetingOverview && session.mode === 'meeting'
    ? renderHumanAskMeetingOverview(meetingOverview, { escapeHtml, keyValue })
    : '';
  const sessionRecordCard = sessionRecord ? renderHumanAskSessionRecord(sessionRecord, decision, { escapeHtml, keyValue, titleCase }) : '';
  const boundaryAlertCard = renderHumanAskBoundaryAlert(session, decision, directorDisposition, { escapeHtml });
  const caseReference = renderCaseReferenceButton
    ? renderCaseReferenceButton(session.case_id, session.case_status, {
        sourceView: 'human_ask',
        referenceId: session.session_id,
        contextLabel: 'Human Ask record',
        label: session.case_id,
      })
    : '';
  return `
    <article class="trace-box stack human-ask-session-card${isFocusedEntity && isFocusedEntity('human_ask_session', session.session_id) ? ' focused-record' : ''}" data-focus-key="${escapeHtml(buildFocusKey ? buildFocusKey('human_ask_session', session.session_id) : `human_ask_session:${session.session_id}`)}">
      <div class="hero-heading">
        <div>
          <strong>${escapeHtml(participant.display_name || session.session_id)}</strong>
          <p class="muted">${escapeHtml(`${modeLabel} | ${shortTime(session.updated_at)}`)}</p>
        </div>
        <div class="status-row">
          ${statusBadge(session.status || 'completed')}
          ${statusBadge(modeLabel.toLowerCase())}
          ${statusBadge(formatOperatingModeLabel(participant.operating_mode || 'direct').toLowerCase())}
          ${humanAttention ? statusBadge(humanAttention) : ''}
          ${statusBadge(decision.structural_posture || 'unknown')}
        </div>
      </div>
      <p class="muted">${escapeHtml(session.prompt || '')}</p>
      ${caseReference ? `<div class="human-ask-case-reference">${caseReference}</div>` : ''}
      ${participantChips}
      <section class="record-posture-grid">
        <article class="trace-box compact-trace record-posture-card">
          <strong>Automation posture</strong>
          <div class="hero-chip-row">
            ${statusBadge(decision.automation_state || 'unknown')}
            ${statusBadge(directorDisposition.replace(/_/g, ' '))}
          </div>
          <p class="muted">The Director keeps automation active unless the record crosses JD scope or a reserved human boundary.</p>
        </article>
        <article class="trace-box compact-trace record-posture-card">
          <strong>Structural posture</strong>
          <div class="hero-chip-row">
            ${statusBadge(decision.structural_posture || 'unknown')}
            ${decision.metadata?.pt_oss_gate ? statusBadge(decision.metadata.pt_oss_gate.replace(/_/g, ' ')) : ''}
          </div>
          <p class="muted">${escapeHtml(decision.metadata?.pt_oss_gate_reason || 'No PT-OSS structural warning was attached to this record.')}</p>
        </article>
      </section>
      ${keyValue([
        ['Role', participant.role_id || '-'],
        ['Operating mode', formatOperatingModeLabel(participant.operating_mode || 'direct')],
        ['Responsibility', formatOperatingResponsibility(participant)],
        ['Participants', participants.length ? participants.map((item) => item.role_id || item.display_name || '-').join(', ') : participant.role_id || '-'],
        ['Scope', titleCase(String(decision.metadata?.scope_status || 'in_scope').replace(/_/g, ' '))],
        ['Human attention', humanAttention || 'Automation may continue'],
        ['Confidence', decision.confidence_percent != null ? `${decision.confidence_percent}%` : '-'],
        ['Risk', decision.risk_percent != null ? `${decision.risk_percent}%` : '-'],
        ['Escalated to', decision.escalated_to || '-'],
      ])}
      ${boundaryAlertCard}
      <div class="trace-box compact-trace">
        <strong>Transcript summary</strong>
        <p class="muted">${escapeHtml(session.transcript_summary || 'No summary available.')}</p>
      </div>
      ${meetingOverviewCard}
      ${sessionRecordCard}
      <div class="stack">
        ${transcript.map((item) => `<div class="timeline-card compact-trace human-ask-transcript-card human-ask-transcript-${escapeHtml(String(item.message_type || 'note'))}"><strong>${escapeHtml(item.speaker_label || item.speaker_id || 'Speaker')}</strong><p class="muted">${escapeHtml(`${titleCase(item.message_type || 'note')} | ${item.timestamp ? shortTime(item.timestamp) : ''}`)}</p><p class="muted">${escapeHtml(item.content || '')}</p></div>`).join('')}
      </div>
    </article>
  `;
}

function renderHumanAskBoundaryAlert(session, decision, directorDisposition, helpers) {
  const { escapeHtml } = helpers;
  const scopeStatus = decision?.metadata?.scope_status || 'in_scope';
  const ptOssGateReason = decision?.metadata?.pt_oss_gate_reason || '';
  if (scopeStatus === 'out_of_scope' || directorDisposition === 'hold_for_clearance') {
    return `<div class="trace-box compact-trace notice-card notice-danger boundary-alert-card"><strong>AI paused: outside JD scope</strong><p class="muted">${escapeHtml(ptOssGateReason || 'This record moved beyond the loaded job definition or allowed scope, so the AI Director core stopped automation and is waiting for a real human decision.')}</p></div>`;
  }
  if (scopeStatus === 'human_only_boundary' || session.status === 'waiting_human' || directorDisposition === 'guarded_follow_up') {
    return `<div class="trace-box compact-trace notice-card notice-warning boundary-alert-card"><strong>AI paused: human boundary reached</strong><p class="muted">${escapeHtml(ptOssGateReason || 'This record reached a reserved human-only action or sensitive decision boundary. Automation stopped at the correct boundary and is waiting for human judgment.')}</p></div>`;
  }
  if (session.status === 'blocked') {
    return `<div class="trace-box compact-trace notice-card notice-warning boundary-alert-card"><strong>AI paused: callable lane blocked</strong><p class="muted">${escapeHtml(ptOssGateReason || 'The target hat could not proceed because callable or structural posture blocked the record before execution continued.')}</p></div>`;
  }
  return '';
}

function renderHumanAskMeetingOverview(item, helpers) {
  const { escapeHtml, keyValue } = helpers;
  const guardedRoles = Array.isArray(item.guarded_roles) && item.guarded_roles.length ? item.guarded_roles.join(', ') : '-';
  const blockedRoles = Array.isArray(item.blocked_roles) && item.blocked_roles.length ? item.blocked_roles.join(', ') : '-';
  return `
    <div class="trace-box compact-trace human-ask-meeting-overview">
      <strong>Meeting overview</strong>
      ${keyValue([
        ['Ready lanes', item.ready_total != null ? `${item.ready_total}` : '0'],
        ['Guarded lanes', item.guarded_total != null ? `${item.guarded_total}` : '0'],
        ['Blocked lanes', item.blocked_total != null ? `${item.blocked_total}` : '0'],
        ['Human gates', item.human_gate_total != null ? `${item.human_gate_total}` : '0'],
        ['Guarded roles', guardedRoles],
        ['Blocked roles', blockedRoles],
      ])}
    </div>
  `;
}

function renderHumanAskSessionRecord(record, decision, helpers) {
  const { escapeHtml, keyValue, titleCase } = helpers;
  const participantValue = Array.isArray(record.participants) ? record.participants.join(', ') : record.participant || '-';
  return `
    <div class="trace-box compact-trace human-ask-session-record">
      <strong>${escapeHtml(record.title || 'Session record')}</strong>
      ${keyValue([
        ['Record type', titleCase(String(record.record_type || 'record').replace(/_/g, ' '))],
        ['Participants', participantValue],
        ['Scope', titleCase(String(decision?.metadata?.scope_status || 'in_scope').replace(/_/g, ' '))],
        ['Automation', titleCase(String(decision?.automation_state || 'unknown').replace(/_/g, ' '))],
      ])}
      <p class="muted">${escapeHtml(record.summary || 'No record summary available.')}</p>
    </div>
  `;
}

function sortHumanAskSessionsForRecordView(sessions) {
  return [...sessions].sort((left, right) => {
    const leftNeedsHuman = humanAskNeedsHumanAttention(left) ? 1 : 0;
    const rightNeedsHuman = humanAskNeedsHumanAttention(right) ? 1 : 0;
    if (leftNeedsHuman !== rightNeedsHuman) {
      return rightNeedsHuman - leftNeedsHuman;
    }
    return (Date.parse(right.updated_at || '') || 0) - (Date.parse(left.updated_at || '') || 0);
  });
}

function humanAskNeedsHumanAttention(session) {
  const decision = session.decision_summary || {};
  const scopeStatus = decision.metadata?.scope_status || 'in_scope';
  return Boolean(
    session.status === 'waiting_human'
      || decision.escalated
      || scopeStatus === 'human_only_boundary'
      || scopeStatus === 'out_of_scope',
  );
}

export function buildHumanAskOutcomeMessage(session, fallback = 'Human Ask record created.') {
  if (!session || typeof session !== 'object') return fallback;
  const decision = session.decision_summary || {};
  const scopeStatus = decision.metadata?.scope_status || 'in_scope';
  if (scopeStatus === 'out_of_scope') {
    return 'Human Ask record created, but AI paused because the request is outside the loaded JD scope.';
  }
  if (scopeStatus === 'human_only_boundary' || session.status === 'waiting_human') {
    return 'Human Ask record created, but AI paused at a reserved human decision boundary.';
  }
  if (session.status === 'blocked') {
    return 'Human Ask record created, but AI could not continue because the callable or structural lane is blocked.';
  }
  return fallback;
}

function formatHumanAskHumanAttention(decision, directorDisposition) {
  const scopeStatus = decision?.metadata?.scope_status || 'in_scope';
  if (scopeStatus === 'out_of_scope' || directorDisposition === 'hold_for_clearance') {
    return 'Human decision needed';
  }
  if (scopeStatus === 'human_only_boundary' || directorDisposition === 'guarded_follow_up') {
    return 'Human boundary';
  }
  return '';
}

function formatHumanAskModeLabel(mode) {
  if (mode === 'meeting') return 'Meeting';
  return 'Report';
}
