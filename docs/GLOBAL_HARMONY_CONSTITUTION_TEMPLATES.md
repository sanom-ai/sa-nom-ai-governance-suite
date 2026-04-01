# Global Harmony Constitution Templates

This guide documents the first public template set for the `v0.6.1` Global Harmony Protocol implementation line.

## Purpose

These templates are not final country packs.
They are starter governed constitution inputs that demonstrate how a future alignment layer can load regional posture without changing SA-NOM's core runtime structure.

## Included Starter Templates

- `resources/alignment/thailand_harmony_constitution.json`
- `resources/alignment/eu_transparency_constitution.json`
- `resources/alignment/usa_accountability_constitution.json`

## Template Shape

Each template currently defines:
- `region_id`
- `display_name`
- `geography_scope`
- `default_locale`
- `constitutional_version`
- `values`
- `communication_posture`
- `regulatory_sources`
- `safe_claim`
- `notes`
- `principles`

Each `principles` entry currently defines:
- `principle_id`
- `title`
- `category`
- `description`
- `weight`
- `keywords`

## Current Scope

This first slice is intentionally narrow.
It provides:
- baseline loading
- public starter constitutions
- validation for required fields and at least one principle
- a registry snapshot for later dashboard or operator use

It does not yet provide:
- dynamic dashboard switching
- resonance scoring
- document-center ingestion
- advanced parsing from natural-language constitutions
- broad regional coverage

## Why This Matters

The first implementation slice proves that the Global Harmony Protocol can start as governed structured input rather than as a vague promise.

That keeps the path to `v0.6.1` disciplined: structure first, then richer parsing and control surfaces later.
