# PT-OSS Core

This guide explains the PT-OSS core that is already embedded inside SA-NOM.

It should be read as the public-facing explanation of the structural intelligence layer that already exists in the codebase and product flows.

## What PT-OSS Is Inside SA-NOM

PT-OSS is SA-NOM's structural intelligence layer.

In plain language, it is the part of the system that checks whether the organization structure around an AI role is safe enough to trust.

That means PT-OSS is not mainly asking:
- did the model answer correctly
- did the server start
- did the prompt look good

Instead, PT-OSS asks questions such as:
- is this workflow too dependent on one specific human
- will the role become unsafe if that person is absent, overloaded, or bypassed
- is the approval path structurally weak
- is human override real, or only present on paper
- is the power structure too asymmetrical for safe governed use

It does not replace:
- PTAG governance runtime
- governed execution
- Human Ask
- human override
- audit chain
- evidence export

Instead, it adds structural signals that help SA-NOM decide whether a role, workflow, or publication path is structurally safe enough to trust.

If PTAG defines the role and runtime boundaries, PT-OSS helps answer whether the surrounding human and organizational structure is strong enough to support that role safely.

## What PT-OSS Produces

The current PT-OSS foundation in SA-NOM is designed to produce:
- structural risk signal
- dependency posture
- escalation recommendation
- organizational fragility warning
- evidence enrichment

That means PT-OSS is not a side note. It is part of how SA-NOM decides whether a role should move forward, remain guarded, or stop for redesign.

## Embedded Modes

SA-NOM already carries these PT-OSS modes in the packaged foundation:

- `PT_OSS_LITE`
- `PT_OSS_FULL`
- `PT_OSS_FULL_CAL_TH`
- `PT_OSS_FULL_CAL_WE`

These modes make PT-OSS usable across:
- smaller or constrained environments
- standard organizational assessments
- Thai cultural and public-sector contexts
- Western or mixed governance environments

So the modes are not different brands of PT-OSS.
They are different assessment depth and context profiles for different environments.

## Embedded Core Metrics

See [PT_OSS_METRICS.md](PT_OSS_METRICS.md) for the plain-language explainer of what each PT-OSS metric means in product terms.
## Embedded Core Metrics

The current PT-OSS foundation already includes these core metrics:

- `HDI-S` - Human Dependency Index, structural
- `HDI-D` - Human Dependency Index, decision
- `SFS` - Structural Fragility Score
- `KPIR` - Key Person Impact Rating
- `ASP` - Architectural Stability Protocol score
- `HOIS` - Human Override Integrity Score
- `SPAI` - Structural Power Asymmetry Index

Together, these metrics let SA-NOM surface whether a role or workflow is:
- structurally resilient
- overly dependent on specific humans
- fragile under force or change
- too asymmetrical for trusted progression

People do not need to memorize every acronym before understanding the product story.
The practical meaning is that PT-OSS gives SA-NOM a way to judge structural readiness, not only technical readiness.

## Where PT-OSS Already Appears In Product Flows

PT-OSS is already visible in several SA-NOM flows:

- Role Private Studio structural assessment before publication
- publish readiness and structural gate states
- Human Ask structural gating and guarded execution
- dashboard structural posture and readiness cards
- go-live posture and enterprise readiness surfaces

So the main gap is not that PT-OSS is missing.
The main gap is that the public product story has not surfaced it clearly enough.

## What A User Should Understand First

If someone is seeing PT-OSS for the first time, the easiest way to read it is:

1. PT-OSS checks the structure around AI work, not only the AI itself.
2. It looks for fragility, dependency, override weakness, and power imbalance.
3. SA-NOM uses those signals to decide whether a role should proceed, stay guarded, or stop for redesign.
4. That is why PT-OSS matters before publication, runtime trust, and go-live readiness.

## Safe Public Claim

The correct public claim is:

SA-NOM includes PT-OSS as an embedded structural intelligence layer.

PT-OSS is a proprietary framework developed by the creator and integrated into SA-NOM to assess structural dependency, fragility, human-override integrity, and power asymmetry before AI roles and workflows are treated as safely governed.

## What This Does Not Mean

This does not mean:
- every PT-OSS formula is fully exposed as a public academic specification in the repo
- every sector-specific PT-OSS extension is already surfaced equally in the public docs
- the public docs currently explain the whole PT-OSS story as well as the code already supports

That is why `v0.1.8` should be treated as a surfacing milestone.

## A Simple Mental Model

Use this mental model:

- `PTAG` tells SA-NOM what a role is allowed to do
- `Authority Guard` checks whether an action is allowed right now
- `Audit Chain` records what happened
- `PT-OSS` checks whether the surrounding structure is stable enough to trust in the first place

That is why PT-OSS should be read as structural intelligence, not as a duplicate of runtime policy enforcement.

## Recommended Reading Order

1. [Feature Matrix](FEATURE_MATRIX.md)
2. [Product Tour](PRODUCT_TOUR.md)
3. [Guided Evaluation](GUIDED_EVALUATION.md)
4. packaged PT-OSS foundation under `resources/pt_oss/`

## Summary

PT-OSS is already inside SA-NOM as a structural intelligence layer.

The next product step is not to invent it.
The next step is to surface it clearly enough that operators, buyers, and evaluators can see what the system already knows how to do.