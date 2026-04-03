# ROADMAP v0.7.7 - Productization Hardening

Status: In progress  
Line: v0.7.7-command-surface

## Goal
Make SA-NOM operable as a serious pilot product by separating the simple command surface for normal users from advanced governance tooling, then hardening first-run, diagnostics, backup/restore, and admin flows.

## Slices

### 1. Command Surface Foundation
- simple Home dashboard for normal users
- top navigation with Home, Work Inbox, Cases, Documents, AI Actions
- Your Next Actions section from assignment queue and approvals
- AI activity feed
- department quick access using master data and search continuity
- progressive disclosure

### 2. Control Room + Role Gate
- dedicated Control Room surface
- admin / IT / founder only
- advanced governance posture and technical tooling
- hide low-level runtime plumbing from the main Home surface

### 3. First-Run / Doctor / Onboarding
- first-run assistant
- setup continuity
- diagnostics / doctor UX
- polished onboarding

### 4. Backup/Restore + Admin Settings
- admin settings surface
- backup / restore UX
- pilot hardening

## Slice 1 Definition of Done
- Home becomes the default command surface
- normal users understand posture + next move within 5 seconds
- Control Room is hidden unless the session has advanced governance access
- Work Inbox, Cases, Documents, and AI Actions remain reachable without exposing technical internals
