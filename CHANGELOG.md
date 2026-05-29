# Changelog

This plugin uses **commit-SHA versioning** — every push is a new version that
installed users pick up automatically (the `plugin.json` has no pinned `version`).
This file records notable changes by date.

## 2026-05-29 — Initial public release

- Claude Code skill that turns course material (lecture PDFs/PPTX, study guides,
  Jupyter notebooks) into a deeply interlinked Obsidian study vault.
- Atomic **term** and **formula** notes, full teaching-walkthrough **lecture**
  notes, MOC indexes, and optional Dataview dashboards.
- Visuals per concept: Mermaid, plotted curves, ASCII grids, GFM tables.
- Three animation tiers: fast template GIFs, sandboxed **LLM-authored per-concept**
  GIFs, and hand-authored generators (with a worked CNN example).
- Spaced-repetition **flashcards** (`Q::A` + cloze), deck-tagged, Anki-exportable.
- Subject-agnostic (verified across deep learning, psychology, economics, sports,
  medicine, law).
- Plan-mode-gated with up-front scoping, sample-first checkpoint, token-economical
  delegation, and a `verify.py` correctness gate.
- Packaged as an installable Claude Code plugin (self-marketplace).
