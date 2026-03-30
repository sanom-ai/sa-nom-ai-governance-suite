# Commercial Discovery Checklist

Use this checklist for the first real commercial conversation after a prospect has seen the repo, one-pager, or product demo.

The goal is not to pitch every feature.
The goal is to qualify whether SA-NOM should stay on the community path, move into a guided evaluation, or become a commercial rollout conversation.

## Best Use Cases For This Checklist

Use this during:
- the first discovery call
- a pricing or rollout follow-up
- an internal qualification review before preparing a quote
- a government or regulated-environment screening conversation

## Before The Call

Have these ready:
- [ONE_PAGER.md](ONE_PAGER.md)
- [ONE_PAGER_TH.md](ONE_PAGER_TH.md)
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
- [PRODUCT_TOUR.md](PRODUCT_TOUR.md)
- [DISCOVERY_DEMO.md](DISCOVERY_DEMO.md)
- [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md)

## 1. Qualification Snapshot

Confirm the basics first:
- What organization is this and what team is driving the evaluation?
- Are they trying to govern existing AI usage, deploy AI into real roles, or both?
- Is this a small self-managed evaluation or a real production-track initiative?
- Do they need a private deployment, air-gapped path, or hosted evaluation only?
- Is there already an internal executive sponsor or only a technical evaluator?

A strong fit usually sounds like this:
- they want AI to participate in real work, not just chat
- they care about authority boundaries, escalation, auditability, or compliance
- they expect private infrastructure, internal review, or procurement involvement

## 2. Workflow And Business Pain

Identify the first valuable workflow:
- Which workflow needs AI first?
- What happens today without SA-NOM?
- What risk appears when that workflow is done with general chat tools or loose automation?
- Where do approvals, escalation, or reporting break down today?
- What would a successful first deployment change in 30 to 90 days?

Good early targets often include:
- governed internal request handling
- policy-aware review flows
- meeting or human-escalation workflows
- operator dashboards for evidence and deployment posture

## 3. Technical Fit

Check the environment before discussing price:
- Private server, hybrid, or air-gapped?
- Expected operator count?
- Need SSO or SCIM?
- Need custom integrations beyond webhook delivery?
- Need Kubernetes or Helm deployment support?
- Need local-model usage through Ollama, or hosted evaluation through OpenAI / Claude?
- Need data residency or sovereign-hosting constraints?

Signals that the commercial path is likely:
- enterprise identity requirements
- regulated deployment hardening
- custom provider or integration requirements
- rollout across multiple teams or environments

## 4. Governance And Compliance Fit

Ask these directly:
- Is the environment regulated?
- Do they need evidence export or audit traceability for internal review?
- Are there Thai banking, government, or sovereign constraints?
- Do legal, IT, compliance, or audit teams need to review the runtime before go-live?
- Do they need a formal go-live gate, operator enablement, or policy tailoring?

Escalate faster toward commercial scope when the answer is yes to:
- audit trail requirements
- deployment review requirements
- evidence retention requirements
- public-sector or sovereign constraints
- air-gapped delivery expectations

## 5. Commercial Fit

Qualify how the engagement should start:
- Are they best served by community self-management, a guided evaluation, a paid pilot, or a full commercial rollout?
- Is budget already known?
- Is procurement direct, partner-led, or government-led?
- Is the customer trying to buy software only, or software plus rollout support?
- Do they need on-site enablement, architecture review, or internal stakeholder workshops?

A simple decision rule:
- community only: small internal evaluation, no special support, no regulated rollout pressure
- guided evaluation: real interest, but still proving fit and deployment shape
- paid pilot: real business workflow, real sponsor, real rollout pressure, but still scoping production
- commercial rollout: production scope, procurement path, compliance requirements, or enterprise features/support needed

## 6. Provider Strategy

Keep the product story consistent:
- Ollama is the default private demo lane
- OpenAI and Claude are optional hosted evaluation lanes

Ask:
- Does the prospect need model traffic to stay inside their environment from day one?
- Are they comfortable starting with a hosted evaluation lane and moving private later?
- Do they need a private-first story for leadership, legal, or security review?

If they need a private-first story, keep the demo and discovery recommendation centered on Ollama.

## 7. Suggested 30-Minute Call Flow

1. Confirm the organization, team, and trigger for the call.
2. Identify the first workflow they want AI to support.
3. Clarify deployment shape and provider expectations.
4. Surface governance, audit, and compliance requirements.
5. Decide whether the next step is community, guided evaluation, pilot, or commercial rollout.
6. Record the follow-up owner, timeline, and next meeting.

## 8. Red Flags To Capture Early

Do not ignore these:
- no owner or sponsor for the initiative
- no clear workflow beyond "we want AI"
- expectation of enterprise support on a community-only path
- procurement pressure without technical fit
- requirement for private or air-gapped deployment without willingness to scope rollout properly
- expectation that governance can be skipped during production rollout

These do not always mean no.
They usually mean the next step should be structured more carefully.

## 9. Recommended Next-Step Output

By the end of the call, record:
- recommended path: community / guided evaluation / paid pilot / commercial rollout
- target tier if known
- deployment posture
- provider lane recommendation
- main blockers
- internal owner
- next meeting date

Then transfer the result into [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md).

## Fast Follow-Up Message

A good follow-up should include:
- one-sentence summary of the problem they want SA-NOM to solve
- recommended next step
- deployment and provider recommendation
- any prerequisites before the next demo or quote
- contact point: `sanomaiarch@gmail.com`
