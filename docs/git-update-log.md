# Git Update Log

This file records the practical changes behind each numbered Git update so later rollbacks and comparisons are easier.

## Entry Template

## 0.0.0
- Date:
- Branch:
- Scope:
- Summary:
- Verification:

## Entries

## 0.9.5.4
- Date: `2026-04-07`
- Branch: `main`
- Scope: `frontend/src/views/SetupView.vue`
- Summary:
  - Reworked the setup-page start flow into a full-screen staged modal.
  - Added a loading phase with spinner while waiting for backend game state readiness.
  - Added an animated start countdown that displays `3 -> 2 -> 1 -> 0` before entering the game.
  - Removed the incorrect spinner flash that previously reappeared between countdown end and route transition.
  - Added countdown timer cleanup and a longer backend readiness polling window.
- Verification:
  - `cd frontend && npm run build`
