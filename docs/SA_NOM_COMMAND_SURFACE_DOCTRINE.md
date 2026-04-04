# SA-NOM Command Surface Doctrine

This document defines how SA-NOM should feel, what the main operating surface must do, and how the product should evolve if the target is:

> easy enough to use like a high-level management game,
> but serious enough to govern real work in the real world.

This is not a gamification document.
It is a doctrine for reducing cognitive load while increasing operational clarity, momentum, and trust.

## Core Statement

SA-NOM should feel like a high-level management game played on real organizational work.

That means:
- the user should quickly understand the state of the world
- the user should quickly understand what to do next
- the user should feel that AI is actively carrying work forward
- the user should act like a governor or director, not like a clerk
- the system should hide low-level plumbing unless deeper review is actually required

## Founder Doctrine

SA-NOM should keep these truths visible in every major surface:
- one human governs the organization through one command surface
- AI is the primary workforce for routine governed work
- humans remain responsible for boundaries, approvals, escalation, and high-consequence decisions
- advanced runtime, trust, and recovery mechanics stay behind progressive disclosure

## What This Is Not

The command surface doctrine does not mean:
- childish gamification
- pointless badges, scores, or cosmetic rewards
- flattening high-risk work into casual UI
- hiding important consequences
- removing governance depth from the product

The goal is not to make serious work playful.
The goal is to make serious work legible, directed, and manageable.

## The Feeling SA-NOM Should Create

When a normal user opens SA-NOM, the system should feel:
- calm
- directional
- alive
- legible
- high-trust
- low-friction

The user should feel:
- "I understand what is happening."
- "I understand what matters next."
- "The system is already doing work for me."
- "I only need to intervene where human judgment really matters."

## Five-Second Rule

Within five seconds, the Home command surface should answer:
- what posture the system is in right now
- what the next human action is
- what AI is already doing right now
- whether anything important is blocked or escalating
- whether the user is safe to keep moving without opening deeper governance tools

If the surface cannot answer those five questions quickly, it is failing the doctrine.

## The World-State Principle

Good management games always tell the player the state of the world before asking for action.
SA-NOM should do the same.

The command surface should present a readable world-state such as:
- system posture
- active AI workforce posture
- conflicts or locks needing attention
- trust or evidence posture in summary form
- current case and work pressure
- session and operating continuity

This is more important than showing a large number of raw records.

## Everything Is A Move

The command surface should not feel like a passive report.
Every important card, lane, or summary should lead to a meaningful move.

Examples of good moves:
- approve
- review
- resolve now
- open case
- inspect AI action
- escalate to human
- continue rollout
- enter Control Room

Examples of bad non-moves:
- showing a large static list with no prioritization
- showing technical identifiers without action context
- showing deep runtime data that does not change the next decision

## AI Works, Humans Govern

The user should not feel that SA-NOM is asking them to manually push every task.
The system should feel like an active governed workforce.

The command surface should show:
- what AI is currently running
- what AI already completed
- what AI is waiting on from humans
- where a human decision is required
- where AI can continue without more human effort

This keeps the human in a director role instead of a clerical role.

## Progressive Disclosure

Normal users should stay on:
- Home
- Work Inbox
- Cases
- Documents
- AI Actions

Advanced setup, trust, diagnostics, recovery, and governance administration should stay behind:
- Governance
- Control Room

A command surface fails this doctrine when low-level runtime plumbing leaks into normal work by default.

## What Must Stay Off Home By Default

The following belong behind deeper disclosure unless the user has entered an advanced governance path:
- raw evidence pack identifiers
- audit-chain internals
- trusted registry internals
- signature or manifest debugging detail
- low-level provider diagnostic output
- storage and persistence mechanics
- backup mechanics
- configuration scaffolding

Home should show consequence and posture, not plumbing.

## Command Surface Structure

The Home command surface should keep a consistent priority order:

1. posture summary
2. your next actions
3. AI activity
4. quick operational access
5. small supporting links

This order matters.
The user should see posture and next move before anything else.

## Role Of Control Room

Control Room exists so the command surface can stay simple.
It is not a failure of the doctrine.
It is what allows the doctrine to work.

Control Room should contain:
- setup and onboarding
- AI workforce and role publication posture
- structural risk and alignment
- trust and evidence tools
- documents and records governance
- runtime and recovery tools
- integrations and providers
- access, security, and admin posture

The command surface should point into Control Room only when a deeper advanced action is actually required.

## Continuity Principle

The system must preserve continuity when the user moves across surfaces.

A good command surface should let the user:
- start from Home
- open the relevant case or work item
- inspect the related document or action
- return without losing context
- carry the same case or workflow identity across lanes

The user should feel that they are following one operation, not teleporting between unrelated pages.

## Touch And Tablet Principle

Because SA-NOM is expected to work on tablet and browser-based private environments, the command surface should be:
- touch-friendly
- readable at a glance
- usable without precision clicking
- safe for one-handed navigation in operational contexts

This means:
- large targets
- clear spacing
- visible active states
- no crowded dropdowns
- no essential actions hidden behind awkward hover-only behavior

## Explain Consequence, Not Implementation

When the surface needs to say something important, it should explain the consequence first.

Good language:
- 2 approvals are waiting today
- 1 case is blocked by missing review
- AI can continue without a new human boundary
- trust posture needs attention before publish

Weak language:
- 2 audit hashes missing
- registry delta mismatch
- unsigned bundle reference unresolved

The second kind of message may be valid in Control Room, but not as the main command language for normal users.

## Good Command Surface Signals

Good signals are:
- few
- meaningful
- directional
- actionable
- consequence-aware

A good view usually has 5 to 7 primary signals, not 20.

## Anti-Patterns

Avoid these patterns:
- too many cards with equal visual weight
- dashboards that report everything but guide nothing
- lists that force the user to interpret priority manually
- mixing advanced governance mechanics into everyday work surfaces
- wording that sounds like internal implementation details instead of operational outcomes
- role ambiguity about whether the user is governing or doing clerical cleanup

## Design Checklist For New Features

Before adding a new Home, Inbox, or Case surface element, ask:
1. Does this help the user see the world-state faster?
2. Does this help the user choose the next move faster?
3. Is this really needed on the command surface, or should it live in Control Room?
4. Does this reduce cognitive load, or add it?
5. Does this reinforce the sense that AI is actively working?
6. Does this preserve role continuity across surfaces?
7. Is the language consequence-first rather than implementation-first?

If a proposed feature fails these questions, it should be redesigned or moved.

## Release Acceptance Criteria

A release should be considered aligned with this doctrine only when:
- Home answers posture and next action within five seconds
- the next human move is always visible without hunting
- AI activity feels live and operational, not decorative
- daily users do not need to open Control Room for routine work
- moving across Home, Cases, Documents, and AI Actions preserves context
- tablet and browser use remain clear and touch-safe
- advanced governance depth is available, but not forced on every user

## Practical Translation For Product Work

In product terms, this doctrine means SA-NOM should keep evolving toward:
- one command surface for normal users
- one mission-control layer for advanced operators
- one readable world-state at the top
- one clear next move for the human
- one visible AI workforce posture
- many deep mechanics hidden until they are actually needed

## Short Internal Sentence

Use this sentence when judging UX direction:

"If this makes the user feel more like a governor and less like a clerk, it fits the doctrine."

## Related Documents

- [CONTROL_ROOM_INFORMATION_ARCHITECTURE.md](CONTROL_ROOM_INFORMATION_ARCHITECTURE.md)
- [PRODUCT_TOUR.md](PRODUCT_TOUR.md)
- [FEATURE_MATRIX.md](FEATURE_MATRIX.md)
- [GOVERNED_HITL_OPERATIONS.md](GOVERNED_HITL_OPERATIONS.md)
- [COMMERCIAL_ONE_PAGER.md](COMMERCIAL_ONE_PAGER.md)