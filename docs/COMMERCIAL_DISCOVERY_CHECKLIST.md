# Commercial Discovery Checklist

Use this checklist for the first real commercial conversation after a prospect has seen the repo, one-pager, or product demo.

The goal is not to pitch every feature.
The goal is to qualify whether SA-NOM should stay on the community path, move into a guided evaluation, enter a paid pilot, or become a commercial rollout conversation.

## Best Use Cases For This Checklist

Use this during:
- the first discovery call
- a pricing or rollout follow-up
- an internal qualification review before preparing a quote
- a government or regulated-environment screening conversation
- a post-demo conversation when the prospect asks about next steps

## Before The Call

Have these ready:
- [ONE_PAGER.md](ONE_PAGER.md)
- [ONE_PAGER_TH.md](ONE_PAGER_TH.md)
- [FEATURE_MATRIX.md](FEATURE_MATRIX.md)
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
- [PRODUCT_TOUR.md](PRODUCT_TOUR.md)
- [DISCOVERY_DEMO.md](DISCOVERY_DEMO.md)
- [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- [LIVE_CUSTOMER_WALKTHROUGH_TH.md](LIVE_CUSTOMER_WALKTHROUGH_TH.md)
- [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md)

## 1. Qualification Snapshot

Confirm the basics first:
- What organization is this and what team is driving the evaluation?
- Are they trying to govern existing AI usage, deploy AI into real roles, or both?
- Is this a small self-managed evaluation or a real production-track initiative?
- Do they need a private deployment, air-gapped path, or hosted evaluation only?
- Is there already an internal executive sponsor or only a technical evaluator?
- Are they evaluating a single team workflow or a cross-functional program?

A strong fit usually sounds like this:
- they want AI to participate in real work, not just chat
- they care about authority boundaries, escalation, auditability, or compliance
- they expect private infrastructure, internal review, or procurement involvement
- they can point to a real workflow owner and a real business problem

## 2. Workflow And Business Pain

Identify the first valuable workflow:
- Which workflow needs AI first?
- What happens today without SA-NOM?
- What risk appears when that workflow is done with general chat tools or loose automation?
- Where do approvals, escalation, or reporting break down today?
- What would a successful first deployment change in 30 to 90 days?
- What is the operational or regulatory cost of leaving the workflow unchanged?

Good early targets often include:
- governed internal request handling
- policy-aware review flows
- meeting or human-escalation workflows
- operator dashboards for evidence and deployment posture
- regulated approval paths that need clear accountability

## 3. Technical Fit

Check the environment before discussing price:
- Private server, hybrid, or air-gapped?
- Expected operator count?
- Need SSO or SCIM?
- Need custom integrations beyond webhook delivery?
- Need Kubernetes or Helm deployment support?
- Need local-model usage through Ollama, or hosted evaluation through OpenAI / Claude?
- Need data residency or sovereign-hosting constraints?
- Is the first lane a demo, a pilot, or a production-track environment?

Signals that the commercial path is likely:
- enterprise identity requirements
- regulated deployment hardening
- custom provider or integration requirements
- rollout across multiple teams or environments
- expectation of direct vendor participation during rollout

## 4. Governance And Compliance Fit

Ask these directly:
- Is the environment regulated?
- Do they need evidence export or audit traceability for internal review?
- Are there Thai banking, government, or sovereign constraints?
- Do legal, IT, compliance, or audit teams need to review the runtime before go-live?
- Do they need a formal go-live gate, operator enablement, or policy tailoring?
- Are there retention, legal-hold, or evidence-handling requirements?

Escalate faster toward commercial scope when the answer is yes to:
- audit trail requirements
- deployment review requirements
- evidence retention requirements
- public-sector or sovereign constraints
- air-gapped delivery expectations
- internal review by legal, compliance, or security before launch

## 5. Commercial Fit

Qualify how the engagement should start:
- Are they best served by community self-management, a guided evaluation, a paid pilot, or a full commercial rollout?
- Is budget already known?
- Is procurement direct, partner-led, or government-led?
- Is the customer trying to buy software only, or software plus rollout support?
- Do they need on-site enablement, architecture review, or internal stakeholder workshops?
- Do they expect enterprise-only features or a quote-specific rollout package?

A simple decision rule:
- community only: small internal evaluation, no special support, no regulated rollout pressure
- guided evaluation: real interest, but still proving fit and deployment shape
- paid pilot: real business workflow, real sponsor, real rollout pressure, but still scoping production
- commercial rollout: production scope, procurement path, compliance requirements, or enterprise features/support needed

## 6. ROI Framing And Economic Narrative

Do not overpromise ROI.
Instead, build a simple business case around one workflow and one operating problem.

Collect these baseline signals:
- how many requests, cases, or reviews happen per week or month
- how many people currently touch the workflow
- average turnaround time today
- how much rework happens because ownership or escalation is unclear
- how often evidence collection becomes manual work
- what internal review or compliance delay is currently slowing progress

A practical ROI framing usually comes from one or more of these:
- reduced coordination time because work is routed through explicit roles
- reduced review and escalation overhead because authority boundaries are built in
- faster audit or evidence preparation because runtime actions are already traceable
- lower deployment friction because readiness and provider checks are explicit before go-live
- lower risk of unmanaged AI usage in sensitive or regulated workflows

### Example ROI Framing

Use language like this, not guaranteed promises:
- If a team currently spends 8 to 12 staff-hours per week coordinating one governed workflow, and SA-NOM reduces that coordination load while improving evidence posture, the economic case may be clearer than the license cost alone.
- If audit preparation currently creates repeated manual evidence-gathering work, SA-NOM may reduce the cost of each review cycle even before a broader rollout.
- If leadership requires a private AI lane from day one, the value is not only time saved. It is also the ability to move forward at all without failing internal review.

### ROI Questions To Ask

- What is the cost of the current manual process each month?
- What is the cost of delay if this workflow cannot move forward safely with AI?
- Which part is more painful today: time, risk, evidence, or rollout coordination?
- If the first deployment worked, what measurable improvement would matter most to leadership in 60 to 90 days?

## 7. Pilot Program Fit And Structure

Recommend a paid pilot when:
- the prospect has a real workflow and sponsor
- they need proof in their own environment before committing to rollout
- they want more than a self-managed evaluation but are not ready for full production scope
- procurement needs a structured first phase with a defined success window

A good pilot usually has:
- one executive sponsor
- one workflow owner
- one first workflow
- one target deployment posture
- one provider recommendation, preferably Ollama if private-first is required
- a defined 30-, 60-, or 90-day decision point

### Suggested Pilot Scope

A strong first pilot often includes:
- one governed workflow
- one provider lane
- one runtime environment
- one operator group
- one readiness and evidence review cycle

### Suggested Pilot Success Criteria

Use measurable outcomes such as:
- runtime deployed in the intended environment
- provider lane validated and documented
- role boundaries reviewed and accepted by stakeholders
- evidence export demonstrated successfully
- smoke-test and go-live readiness paths passing
- business workflow completed with acceptable human escalation behavior

### Pilot Anti-Patterns

Avoid pilots that sound like this:
- "let's test everything"
- no sponsor, only curiosity
- no workflow, only general AI interest
- private or regulated requirements with no willingness to scope rollout properly
- expectation of enterprise support on a community-only path

## 8. Provider Strategy

Keep the product story consistent:
- Ollama is the default private demo lane
- OpenAI and Claude are optional hosted evaluation lanes

Ask:
- Does the prospect need model traffic to stay inside their environment from day one?
- Are they comfortable starting with a hosted evaluation lane and moving private later?
- Do they need a private-first story for leadership, legal, or security review?
- Will the first successful outcome depend on local-model validation or just a fast hosted proof?

If they need a private-first story, keep the demo and discovery recommendation centered on Ollama.

## 9. Suggested 30-Minute Call Flow

1. Confirm the organization, team, and trigger for the call.
2. Identify the first workflow they want AI to support.
3. Clarify deployment shape and provider expectations.
4. Surface governance, audit, and compliance requirements.
5. Frame the likely economic case in simple workflow terms.
6. Decide whether the next step is community, guided evaluation, pilot, or commercial rollout.
7. Record the follow-up owner, timeline, and next meeting.

## 10. Red Flags To Capture Early

Do not ignore these:
- no owner or sponsor for the initiative
- no clear workflow beyond "we want AI"
- expectation of enterprise support on a community-only path
- procurement pressure without technical fit
- requirement for private or air-gapped deployment without willingness to scope rollout properly
- expectation that governance can be skipped during production rollout
- desire for a pilot without success criteria or decision owner

These do not always mean no.
They usually mean the next step should be structured more carefully.

## 11. Recommended Next-Step Output

By the end of the call, record:
- recommended path: community / guided evaluation / paid pilot / commercial rollout
- target tier if known
- deployment posture
- provider lane recommendation
- first workflow candidate
- draft ROI narrative
- pilot recommendation if applicable
- main blockers
- internal owner
- next meeting date

Then transfer the result into [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md).

## 12. Fast Follow-Up Message

A good follow-up should include:
- one-sentence summary of the problem they want SA-NOM to solve
- recommended next step
- deployment and provider recommendation
- draft ROI framing in plain business language
- pilot recommendation or rollout recommendation
- any prerequisites before the next demo or quote
- contact point: `sanomaiarch@gmail.com`

