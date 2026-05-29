# Obsidian Study Guide Builder

A [Claude Code](https://claude.com/claude-code) **skill** that turns raw course
material — lecture slides (PDF/PPTX), study guides (HTML/MD), Jupyter notebooks —
into a polished, deeply interlinked [Obsidian](https://obsidian.md) vault you can
actually study from.

It produces:

- **Atomic term notes** — one per concept: formal definition, plain-words
  explanation with an analogy, why it matters, and links to everything related.
- **Atomic formula notes** — one per formula, with a symbol-by-symbol table
  (every letter, sub/superscript, sum, operator), what it computes, and a worked
  numeric example.
- **Full teaching-walkthrough lecture notes** — you can learn the whole lecture
  from the note alone: narrative problem→solution flow, the slides' concrete
  numbers, callouts, and an "arc" that chains each lecture to the next.
- **Navigation & indexes** — a Home MOC, per-kind indexes, optional live
  [Dataview](https://github.com/blacksmithgu/obsidian-dataview) dashboards.
- **Visuals everywhere** — Mermaid diagrams, plotted curves, ASCII grids, GFM
  tables, and **animated GIFs** (three tiers: fast templates, genuinely
  per-concept LLM-authored animations, or hand-authored).
- **Spaced-repetition flashcards** — `Q::A` + cloze cards per note, deck-tagged
  by lecture, ready for the
  [Spaced Repetition plugin](https://github.com/st3v3nmw/obsidian-spaced-repetition)
  or Anki export.

It's **subject-agnostic** — verified across deep learning, plus psychology,
economics, sports, medicine, and law.

## Install

Copy this directory into your Claude Code skills folder:

```sh
cp -r obsidian-study-guide ~/.claude/skills/
```

Then in Claude Code, ask something like *"turn these lecture PDFs into an Obsidian
vault"* and the skill triggers automatically. It runs in **plan mode** for a fresh
build and asks you the scope up front (coverage, animation level, flashcards,
build cadence, …) before producing anything.

Requires Python with `matplotlib` + `numpy` for the animation generators
(everything else is plain markdown — no Obsidian plugins needed for the core
vault; Mermaid and MathJax are built in).

## What's in here

| Path | What it is |
|------|------------|
| `SKILL.md` | The skill itself — the full playbook Claude follows. |
| `assets/templates.md` | Exact note templates (term / formula / lecture / index). |
| `assets/verify.py` | Vault verification (0 broken links, balanced fences, …). |
| `assets/scripts.md` | Copy-paste scripts: index build, GIF embed, collision fix, inline-linking. |
| `assets/per_term_generator.py` | Template GIF generator (concept-shape routing, subject-agnostic). |
| `assets/llm_gif_pipeline.py` | Sandboxed harness for genuinely per-concept LLM-authored GIFs. |
| `assets/example_subject_generator.py` | Worked example of a hand-authored subject generator (CNNs). |
| `assets/animation_generator.py` | Hand-authored GIF generator + style harness. |
| `assets/obsidian-*.json` | `.obsidian/` config (graph colors, hover previews). |
| `assets/README-template.md` | README dropped into a *generated* vault when sharing it. |

## A note on generated content

The notes this skill produces are **derived from your own source material**. The
underlying content belongs to its original author (your instructor / institution)
and may carry that source's license or attribution terms — check before
redistributing a generated vault publicly.

## License

[MIT](LICENSE) — the skill/tool itself. (This does not relicense any vault content
you generate from your own sources.)
