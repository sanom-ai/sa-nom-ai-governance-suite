# Global Harmony Evaluation Baseline

This guide documents the second `v0.6.1` implementation slice for the Global Harmony Protocol line.

## Purpose

The purpose of this slice is to move beyond loading constitutions into evaluating whether a governed context appears aligned, guarded, or escalated under a selected regional constitution.

## What This Slice Adds

- context normalization for cultural-alignment evaluation
- a baseline evaluator that produces `aligned`, `guarded`, or `escalated`
- matched-principle reporting
- concern reporting with severity
- a result contract that is ready to feed later audit or dashboard surfaces

## Current Context Inputs

The baseline evaluator currently uses fields such as:
- `audience`
- `channel`
- `sensitivity`
- `tone`
- `hierarchy`
- `requires_approval`
- `owner_visible`
- `explanation_visible`

## Current Output Contract

The evaluator currently returns:
- `status`
- `human_review_required`
- `normalized_context`
- `matched_principles`
- `concerns`
- `rationale`

## Why This Matters

This slice starts to encode cultural logic as structured, reviewable evaluation behavior rather than leaving the protocol at the level of templates and intention.

That makes later work on dashboard controls, audit traces, and operator review surfaces much easier because the evaluation result shape already exists.

## Current Limits

This slice still does not provide:
- resonance scoring
- document-center ingestion
- advanced natural-language constitution parsing
- broad regional coverage
- direct runtime enforcement hooks

The current goal is a baseline evaluator that is small, testable, and auditable.
