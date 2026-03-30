# Enterprise Function Map

Use this guide when you want to position SA-NOM beyond a single demo lane and explain how governed AI roles can cover an end-to-end organization across manufacturing, finance, accounting, audit, and IT.

## Goal

By the end of this guide you should be able to:
- explain the full manufacturing operating chain from sales planning through delivery
- show where finance and accounting sit inside the governed operating model
- show where internal audit and external-audit response sit in the governed operating model
- explain how IT becomes the enabling and control layer for the whole system
- identify which role packs and scenarios should be built next

## 1. Manufacturing End-To-End

The manufacturing story should be told as one connected operating chain, not as isolated departments.

### 1.1 Sales Planning

Purpose:
- forecast demand
- align customer commitments with production capacity
- flag risk before procurement or production starts

Potential role packs:
- Sales Planning Analyst
- Demand Review Coordinator
- Revenue Risk Escalation Lead

Human Ask examples:
- call the planning role into a meeting to summarize monthly demand signals
- ask for backlog risk by customer or product family
- ask for demand-versus-capacity posture before a planning decision

Human-gated boundaries:
- final commercial commitments
- strategic forecast override
- major customer allocation decisions

### 1.2 Purchasing / Procurement

Purpose:
- review purchase requests
- check supplier risk and lead-time exposure
- prepare escalation when procurement decisions exceed policy

Potential role packs:
- Purchasing Review Analyst
- Supplier Risk Escalation Lead
- Procurement Compliance Coordinator

Human-gated boundaries:
- supplier appointment or removal
- contract signing
- exceptions that change approved procurement policy

### 1.3 Warehouse (Raw Materials / WIP)

Purpose:
- monitor stock posture
- review shortage, overstock, and aging risk
- prepare exception routing for urgent replenishment or blocked materials

Potential role packs:
- Warehouse Posture Analyst
- Inventory Exception Coordinator
- Material Availability Escalation Lead

Human-gated boundaries:
- write-off approval
- inventory adjustments outside policy
- emergency release of blocked materials

### 1.4 Production

Purpose:
- translate planning into governed execution summaries
- monitor schedule adherence, bottlenecks, and stoppage risk
- prepare evidence for why a production issue needs escalation

Potential role packs:
- Production Schedule Review Lead
- Bottleneck Escalation Coordinator
- Shopfloor Exception Analyst

Human-gated boundaries:
- production-release authority
- maintenance override on safety-critical assets
- final approval for emergency deviation from plan

### 1.5 QC

Purpose:
- review in-process inspection results
- summarize defect patterns
- route out-of-spec findings for human action

Potential role packs:
- In-Process QC Review Analyst
- Defect Pattern Escalation Lead
- Quality Hold Coordinator

Human-gated boundaries:
- release of nonconforming product
- override of QC hold
- disposition of high-severity defect cases

### 1.6 QA

Purpose:
- review quality-system posture
- prepare corrective-action summaries
- track policy or procedural exceptions for governed review

Potential role packs:
- QA System Review Lead
- CAPA Escalation Coordinator
- Compliance Deviation Analyst

Human-gated boundaries:
- final CAPA approval
- change-control approval for regulated environments
- release of exception-based quality decisions

### 1.7 Store FG (Finished Goods)

Purpose:
- review finished-goods availability
- summarize allocation or shipment risk
- flag mismatches between release, stock, and delivery commitments

Potential role packs:
- FG Allocation Analyst
- Shipment Risk Escalation Lead
- Release Posture Coordinator

Human-gated boundaries:
- exception-based release of finished goods
- manual reallocation between key customers
- dispatch override under dispute or quality hold

### 1.8 Delivery / Logistics

Purpose:
- review delivery posture and carrier risk
- summarize which orders are on time, at risk, or blocked
- prepare escalation for customer-impacting delays

Potential role packs:
- Delivery Posture Analyst
- Logistics Escalation Coordinator
- Customer Impact Review Lead

Human-gated boundaries:
- customer commitment changes
- penalty acceptance
- crisis-routing decisions during major disruption

### 1.9 New Model / NPI / New Product Introduction

Purpose:
- review readiness for new model launch, trial builds, and change-control gates
- summarize cross-functional blockers before launch
- route unresolved engineering, quality, supply, or cost risks to human owners

Potential role packs:
- New Model Readiness Coordinator
- Trial Build Review Analyst
- Launch Gate Escalation Lead
- Engineering Change Review Coordinator

Key workflow stories:
- NPI readiness review
- APQP / PPAP / control-plan checkpoint summary
- launch blocker escalation
- engineering-change and trial-build exception routing

Human-gated boundaries:
- launch approval
- engineering change authorization
- PPAP sign-off
- acceptance of residual launch risk

## 2. Finance And Accounting Layer

Finance and accounting should be shown as first-class governed lanes, not hidden behind generic operations.

### 2.1 Finance

Purpose:
- review budget posture, spending pressure, and cost variance
- summarize operational financial risk before it becomes a business problem
- route high-impact exceptions to human finance owners

Potential role packs:
- Budget Review Analyst
- Cost Variance Escalation Lead
- Spend Control Coordinator
- Forecast Pressure Review Lead

Key workflow stories:
- budget-versus-actual review
- cost-overrun escalation
- capex or opex exception routing
- margin-risk summary linked to production or delivery issues

Human-gated boundaries:
- budget approval
- fund release
- acceptance of material variance without remediation
- commercial or pricing decisions that bind the business

### 2.2 Accounting

Purpose:
- review accounting-close readiness, inventory valuation posture, and transaction exceptions
- summarize what is missing, mismatched, or blocked before close or audit review
- route sensitive accounting judgments to human owners

Potential role packs:
- Close Readiness Coordinator
- Inventory Valuation Review Analyst
- GR/IR Exception Lead
- Revenue Recognition Escalation Coordinator

Key workflow stories:
- month-end close readiness
- inventory valuation exception review
- GR/IR mismatch analysis
- accrual and revenue-recognition escalation

Human-gated boundaries:
- final journal approval
- revenue-recognition judgment
- statutory filing sign-off
- external-financial-reporting approval

## 3. Audit Layer

Audit should be positioned as a cross-functional control lane, not a separate afterthought.

### 3.1 Internal Audit

Purpose:
- review governed evidence across purchasing, warehouse, production, quality, delivery, finance, and accounting
- identify policy deviation, repeated overrides, and weak control points
- prepare management-facing audit summaries

Potential role packs:
- Internal Audit Review Lead
- Control Testing Analyst
- Evidence Pack Coordinator

Key workflow stories:
- sample-based review of exceptions
- repeated override analysis
- control-gap reporting for management review
- cross-functional control review spanning operations and finance

Human-gated boundaries:
- final audit opinion
- audit rating sign-off
- management-action closeout approval

### 3.2 External Audit Response

Purpose:
- prepare structured evidence for outside auditors
- coordinate requests without letting AI invent commitments
- keep the response trail complete and reviewable

Potential role packs:
- External Audit Response Coordinator
- Auditor Evidence Pack Analyst
- Regulatory Query Escalation Lead

Key workflow stories:
- auditor request intake
- evidence-pack assembly
- response-note preparation
- escalation when the request crosses legal, finance, accounting, or compliance boundaries

Human-gated boundaries:
- official external response approval
- legal or regulatory representation
- commitments made to outside auditors or regulators

## 4. IT Layer

IT should be framed as the enabling and control backbone for every domain above.

### 4.1 IT Operations

Purpose:
- review system posture, service incidents, and runtime health
- coordinate readiness for governed AI lanes
- summarize what is blocking safe operation

Potential role packs:
- IT Operations Review Lead
- Service Health Escalation Coordinator
- Runtime Change Review Analyst

### 4.2 Security And Access

Purpose:
- monitor access posture, secrets handling, and high-risk changes
- prepare escalation when security or governance boundaries are crossed

Potential role packs:
- Access Governance Analyst
- Security Exception Escalation Lead
- Privileged Change Review Coordinator

### 4.3 Change / Release / Recovery

Purpose:
- review change requests
- summarize release readiness and rollback posture
- prepare human-facing recovery notes during incidents

Potential role packs:
- Change Control Review Lead
- Release Readiness Analyst
- Incident Recovery Coordinator

Human-gated boundaries across IT:
- production change approval
- emergency override on privileged operations
- acceptance of residual security risk

## 5. How These Layers Connect In SA-NOM

SA-NOM should present these functions as one governed operating model:
- manufacturing roles run the day-to-day chain
- finance and accounting roles explain cost, budget, close, and transaction posture
- audit roles review the evidence and the exceptions
- IT roles keep the runtime, access, and change posture safe

That lets SA-NOM tell a bigger story than "AI assistant per team".
It becomes a governed operating fabric where:
- humans call roles into reporting or meetings through Human Ask
- governed roles stay inside bounded authority
- escalations and alerts move sensitive decisions back to humans
- evidence remains available for internal and external review

## 6. Recommended Build Order

A practical sequence after the current legal and HR lanes:
1. Purchasing / supplier-risk role pack
2. Warehouse / inventory-exception role pack
3. New model / NPI readiness pack
4. Finance budget and cost-variance pack
5. Accounting close-readiness or GR/IR exception pack
6. Production schedule or bottleneck role pack
7. QC / QA quality-hold scenario
8. Internal audit evidence-review scenario
9. External audit response coordinator pack
10. IT operations and change-control pack

## 7. Good Demo Story For This Expansion

A strong enterprise-level talk track is:
- planning creates demand pressure
- procurement and warehouse surface supply risk
- production and quality surface execution risk
- finance and accounting surface cost, variance, and close pressure
- delivery surfaces customer impact
- audit reviews the evidence trail afterward
- IT keeps the whole governed runtime safe and explainable

This is stronger than showing isolated packs because it explains how SA-NOM can govern work across the operating chain, not only inside one department.

## Next Steps

- For the current legal pack: [LEGAL_REVIEW_ROLE_PACK.md](LEGAL_REVIEW_ROLE_PACK.md)
- For the current HR pack: [HR_POLICY_ROLE_PACK.md](HR_POLICY_ROLE_PACK.md)
- For the current legal scenario: [LEGAL_REVIEW_SCENARIO.md](LEGAL_REVIEW_SCENARIO.md)
- For the current HR scenario: [HR_POLICY_SCENARIO.md](HR_POLICY_SCENARIO.md)
- For milestone planning: [ROADMAP_v0.1.6.md](ROADMAP_v0.1.6.md)
- For issue-ready follow-up work: [ISSUE_DRAFTS_v0.1.6.md](ISSUE_DRAFTS_v0.1.6.md)
