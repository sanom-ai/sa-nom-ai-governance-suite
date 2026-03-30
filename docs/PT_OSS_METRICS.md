# PT-OSS Metrics

This guide explains the PT-OSS metrics in plain product language so operators, buyers, and evaluators do not have to guess what the acronyms mean.

It is not a full mathematical specification.
It is a practical explainer for how the current PT-OSS layer should be understood inside SA-NOM.

## How To Read These Metrics

The main idea is simple:

- PT-OSS is not scoring model quality alone
- PT-OSS is assessing whether the surrounding human and organizational structure is safe enough to trust
- each metric highlights a different structural risk or readiness signal

A single metric should not usually be read in isolation.
The point is to understand the structural posture created by the group of metrics together.

## HDI-S - Human Dependency Index, Structural

`HDI-S` asks how much the structure depends on specific humans just to keep operating normally.

High structural dependency usually means:
- too much process knowledge lives in a few people
- the workflow becomes unstable when those people are absent
- the role is not yet safely institutionalized

In product terms, a high `HDI-S` should make teams ask:
- is this role too person-dependent to trust at scale
- are handoffs too weak
- is the organization relying on informal human memory instead of explicit governed structure

## HDI-D - Human Dependency Index, Decision

`HDI-D` asks how much important decision-making still depends on a small number of humans.

This matters when a workflow looks stable on paper but still collapses because key decisions cannot move without a specific person.

In product terms, a high `HDI-D` may suggest:
- decision authority is concentrated too narrowly
- escalation paths are brittle
- the governed AI role may appear capable, but actual decisions still bottleneck around one human actor

## SFS - Structural Fragility Score

`SFS` asks how fragile the workflow or operating structure becomes when pressure, disruption, turnover, or exceptions occur.

This is the metric that helps answer whether the structure holds together only in calm conditions.

In product terms, a weak `SFS` often means:
- exceptions break the process too easily
- the workflow cannot absorb disruption cleanly
- the organization is not yet ready to trust the role in real operational pressure

## KPIR - Key Person Impact Rating

`KPIR` asks how much one key person can distort, delay, or destabilize the workflow.

It is closely related to dependency, but the focus here is impact concentration rather than general structural reliance.

In product terms, a high `KPIR` can indicate:
- one individual can override too much
- loss or unavailability of a key person creates outsized disruption
- governance exists, but practical operating power is still concentrated unsafely

## ASP - Architectural Stability Protocol Score

`ASP` asks whether the broader operating architecture is stable enough to support governed execution.

This is less about one person and more about whether the role, process, and structural arrangement fit together in a durable way.

In product terms, `ASP` helps answer:
- does the workflow design support repeatable execution
- are the structural pieces aligned well enough to avoid drift
- is the operating architecture solid enough for scale and continuity

## HOIS - Human Override Integrity Score

`HOIS` asks whether human override is real, trustworthy, and usable when it is needed.

A system can claim to have human oversight while still failing in practice if humans cannot intervene clearly, quickly, or meaningfully.

In product terms, weak `HOIS` may mean:
- override exists only on paper
- escalation reaches humans too late
- human control is ambiguous, inconsistent, or too weak under pressure

This is one of the most important metrics for explaining why SA-NOM is different from automation systems that claim oversight without making it operationally credible.

## SPAI - Structural Power Asymmetry Index

`SPAI` asks whether power in the structure is too asymmetrical for trusted governed use.

This matters when reporting lines, institutional pressure, hierarchy, or approval power are so uneven that formal governance stops being reliable in practice.

In product terms, elevated `SPAI` may suggest:
- people cannot safely challenge decisions
- escalation may be formally available but socially unusable
- the workflow may appear compliant while still being structurally unsafe

This metric is especially important for public-sector, highly hierarchical, or politically sensitive environments.

## What These Metrics Mean Together

When read together, the PT-OSS metrics help SA-NOM answer questions such as:
- is this role structurally resilient enough to trust
- is the workflow too dependent on one person or one decision center
- will human override actually work under pressure
- does the formal governance model match the real organizational power structure

That is why PT-OSS should be understood as structural intelligence, not only a scorecard.

## A Simple Non-Technical Summary

If someone wants the shortest explanation possible:

- `HDI-S` and `HDI-D` ask how dependent the system is on particular humans
- `SFS` asks how fragile the structure is under disruption
- `KPIR` asks how much one key person can affect outcomes
- `ASP` asks whether the operating architecture is stable enough
- `HOIS` asks whether human override is actually trustworthy
- `SPAI` asks whether power asymmetry is too high for safe governed use

## How To Use This In Demos And Buyer Conversations

The best way to explain PT-OSS metrics in a demo is not to start with acronyms.
Start with the practical questions:

- can we trust this role if one person is missing
- can humans still step in when pressure rises
- is the workflow stable under real operating conditions
- is the structure fair and usable enough for governed escalation

Then use the metrics as the evidence vocabulary behind those answers.

## Related Documents

- [PT_OSS_CORE.md](PT_OSS_CORE.md)
- [PRODUCT_TOUR.md](PRODUCT_TOUR.md)
- [FEATURE_MATRIX.md](FEATURE_MATRIX.md)
- packaged PT-OSS foundation under `resources/pt_oss/`