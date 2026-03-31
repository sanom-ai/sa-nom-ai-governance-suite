# Security Follow-Up Visibility

This guide defines how SA-NOM should keep accepted or deferred security work visible after merge.

## Why This Guide Exists

A security exception workflow is only trustworthy if follow-up does not disappear after the PR closes.

After `v0.1.13` introduced a clearer security exception workflow, the next step is to explain how maintainers should keep deferred risk visible through issues, milestones, and review notes.

## Core Position

Security follow-up in SA-NOM should be:
- visible
- attributable
- easy to revisit
- proportional to the severity of the deferred finding
- lightweight enough for a small, fast-moving repository

The goal is not process for its own sake. The goal is to prevent accepted risk from becoming forgotten risk.

## When This Workflow Applies

Use this workflow when:
- a security-related finding is accepted temporarily
- a dependency finding cannot be fixed in the current PR
- a follow-up fix is intentionally deferred to a later milestone
- a maintainer wants a paper trail for why a finding did not block merge

## Minimum Visibility Expectations

A deferred security item should remain visible through at least one of these paths:
- a linked issue
- a milestone note
- explicit language in the merged PR summary
- a security follow-up section in the relevant planning docs

The exact mechanism can stay lightweight, but the deferred work should be easy to rediscover.

## What A Good Follow-Up Item Should Include

A follow-up item should capture:
- what the unresolved finding is
- why it was deferred
- what current mitigation or context made temporary acceptance reasonable
- who owns the next review or fix
- which milestone or review point should revisit it
- whether the issue is trust-critical or lower-impact

## Recommended Workflow

1. identify the finding and decide that it will not be fixed in the current PR
2. record the reason for deferral in the PR or review note
3. create or link a follow-up issue when the deferred work should stay visible beyond the PR itself
4. note the intended revisit point, such as the next milestone or maintenance cycle
5. reference the follow-up from the accepted-exception note when practical

This keeps the trail connected instead of fragmented.

## When A Linked Issue Is Especially Important

A linked issue is strongly preferred when:
- the finding affects a trust-sensitive runtime path
- the deferred risk may outlive the current milestone
- the fix requires additional design or dependency work
- the finding is likely to be asked about again in review or diligence conversations

## Maintainer Review Expectations

Maintainers should ask:
- if this finding is accepted temporarily, where will we see it again?
- who is expected to revisit it?
- is the revisit point concrete enough to be meaningful?
- does the PR language make the current risk understandable to future reviewers?

If those questions do not have good answers, the follow-up visibility is probably too weak.

## Relationship To Existing Docs

This guide should be read with:
- [docs/SECURITY_EXCEPTION_WORKFLOW.md](SECURITY_EXCEPTION_WORKFLOW.md)
- [docs/DEPENDENCY_REVIEW_WORKFLOW.md](DEPENDENCY_REVIEW_WORKFLOW.md)
- [docs/SECURITY_AUTOMATION_BASELINE.md](SECURITY_AUTOMATION_BASELINE.md)
- [SECURITY.md](../SECURITY.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

The exception workflow explains how temporary acceptance works.
This guide explains how that acceptance stays visible after merge.

## Practical Summary

The right public message is:

SA-NOM does not only document accepted security exceptions. It also expects deferred risk to stay visible through an explicit follow-up path.

