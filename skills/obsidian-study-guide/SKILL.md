---
name: obsidian-study-guide
description: Build a thorough, interlinked Obsidian vault from course material (lecture/recitation slides as PDF/PPTX, an existing HTML/MD study guide, Jupyter notebooks). Produces atomic term notes and formula notes (formal + plain-words + why + symbol-by-symbol), full teaching-walkthrough lecture/recitation notes (learn the whole lecture from the note alone) with narrative problem→solution flow and inline wiki-linked terms, MOC indexes, spaced/callout formatting, and rich visuals (Mermaid diagrams, xychart plots, ASCII grids, and animated GIFs — a relevant animated diagram per term note, with faithful hand-authored animations for the key concepts). The vault name is proposed from the source subject and confirmed with the user. Use when the user asks to turn lectures / a course / study material into an Obsidian vault, a "second brain", linked study notes, or wants term/formula notes with diagrams and animations; also use to extend, reformat, add visuals/animations/flow/inline-links to, deepen lecture notes for, rename, or verify an existing such vault.
---

# Obsidian Study Guide Builder

Turn a course's raw material into a polished, deeply interlinked Obsidian vault:
**atomic notes** (one per term, one per formula), **connective lecture notes** that
tell a problem→solution story, full **navigation/MOC** scaffolding, **readable
formatting** (spacing + callouts), and **visuals** (diagrams + plotted curves +
ASCII grids + animated GIFs) everywhere they teach.

Battle-tested playbook — every phase and every "Hard-won rule" encodes a mistake
already made and fixed. Follow phases in order. Re-run `verify.py` after EVERY
mutating pass, not just at the end.

> Reference build A (key-concept GIFs): a 6-lecture + 3-recitation course →
> ~220 term notes, ~104 formula notes, 9 lecture notes, 4 index/Home, 94
> animated GIFs, ~340 files, ~5 MB total, ~2,800 internal links, 0 broken.
>
> Reference build B (full walkthrough + 1:1 GIF coverage + inline links): an
> 8-lecture + 8-recitation LLM/AI-agents course → 623 term notes, 57 formula
> notes, 16 lecture notes (250–450 lines each, full teaching walkthroughs), 4
> index/Home, one animated GIF per term (~13 MB), ~380 inline bold-term links
> added, 0 broken. (Template-path GIFs = ~15–20 shapes re-labelled per term; use
> the LLM-authored path for genuinely bespoke per-concept animations.)

## Working mode

**A FRESH BUILD MUST RUN IN PLAN MODE.** Building a vault from scratch is a large,
many-hour, many-file, token-heavy job — never start writing notes off an assumed
spec. The moment you detect a from-scratch build (no vault exists yet):
1. **Enter plan mode** (EnterPlanMode if the harness offers it; if it doesn't,
   still STOP and do the Phase-0 Q&A before any file is created).
2. **Run the Phase-0 scoping Q&A with the user** — use the AskUserQuestion tool to
   ask the decisions explicitly (sources, coverage, animation level, flashcards
   on/off, depth, …). Do NOT silently apply defaults on a fresh build; the user is
   investing real time/tokens and should choose. See Phase 0 for the exact
   questions and how to batch them.
3. **Write the phased plan** to the plan file (Context → the user's locked
   answers → vault structure → per-phase steps → verification) and get approval.
4. Only THEN exit plan mode and execute. The phases below ARE that plan's
   skeleton. Track progress with a todo list (one item per batch/phase).

(**Incremental add / small tweak** — see below — does NOT require plan mode; for a
one-lecture add or a formatting pass, confirm the few relevant choices inline and
proceed. Plan mode is the gate for the big from-scratch build specifically.)

**Sample-first checkpoint (de-risk a big build).** For a large fresh build
(more than ~3 lectures / ~50 notes), after the plan is approved, build ONE
representative lecture end-to-end first — its formula notes, term notes (with a
`## Visual`), the full lecture walkthrough, and a couple of flashcards if ON —
then STOP and show the user that one lecture as a style sample. Get their sign-off
(or corrections) on depth, tone, visual style, and card format BEFORE mass-
producing the rest. A wrong style caught at note 15 is cheap; caught at note 600
it means re-running everything. Offer to skip the checkpoint if the user says
"just build it all." Skip it outright for small builds and incremental adds.

### Two modes: fresh build vs. incremental add

Decide which you're in BEFORE touching anything:

- **Fresh build** — no vault exists yet. Run all phases in order.
- **Incremental add** — "add lecture N to the existing vault". This is the COMMON
  repeat request. Do NOT rebuild; STUDY the existing vault first, then match it.
  1. **Match the established conventions, don't invent.** Read 2–3 existing
     notes of each kind (term, formula, lecture) + `Home`/indexes. Lock onto the
     exact frontmatter shape, the `f- ` prefix, the lecture-note depth, the
     `## Visual` style (GIF + diagram), the GIF slug rule actually in use, and
     the Prev/Next chain. The vault's own files are the spec — the templates in
     `assets/` are only the fallback.
  2. **Inventory the new source** (Phase 1), then list which concepts are GENUINELY
     NEW vs. ones the vault already has a note for. Build notes ONLY for the new
     ones; for reused concepts, just `[[link]]` and APPEND the new lecture id to
     their `lecture:` frontmatter list (e.g. `lecture: [L6]` → `lecture: [L6, L7]`).
  3. **Extend, don't regenerate, the indexes.** Append a new `## [[Ln - …]]`
     section to `All Terms`/`All Formulas`, add the lecture to `All Lectures` +
     `Home`, bump the counts. Editing in place preserves any hand-written index
     prose; the `build_indexes` script would clobber it (and usually omits the
     new lecture from its `ORDER`/`TITLES` anyway).
  4. **Chain the navigation.** Point the previously-last note's `Next:` at the new
     lecture, and the new note's `Prev:` back at it, so the reading chain stays
     unbroken.
  5. Run `verify.py` and the GIF-fidelity spot-check exactly as in a fresh build.

  Watch for a **slug-convention mismatch**: if the existing per-term GIFs were
  made by a *different* generator than `assets/per_term_generator.py`, re-running
  the bundled generator will emit alt-slug duplicate GIFs for terms that already
  have one (the originals are referenced under the old name). After generating,
  list `Assets/*.gif` not referenced by any `![[…]]` and delete the alt-slug dups
  of *existing* terms — keep only the new terms' GIFs.

## Token economics (governs HOW every phase is run — internalize before Phase 0)

A full build moves a lot of content. The single biggest cost is **source PDFs/
slides as IMAGES** (~1.5k tokens/page → an 80-page deck ≈ 120k+ tokens) — and if
the *main* agent reads them, that bulk sits in its context for the WHOLE session
and is paid for on every subsequent turn. The orchestration principle that keeps
quality identical while slashing cost:

> **The main (orchestrator) agent NEVER bulk-reads source material into its own
> context.** It globs paths, scopes the work, and delegates. All heavy reading
> (PDF images, notebooks, the HTML guide) happens INSIDE disposable sub-agent
> contexts that read → write notes → return only a short structured report. The
> orchestrator holds the inventory/checklist and the verify output, never the
> raw slides.

Three rules that follow from it:
1. **Read-once, co-located with writing.** The agent that WRITES a lecture's
   notes is the one that READS that lecture's source — in the same context, then
   discards it. Don't have the orchestrator read a deck and then paste its
   content into builder prompts (that pays for the slides twice: once in the
   orchestrator, once per builder). Give builders the **file path + page range**,
   not transcribed slide text.
2. **Deterministic work = scripts, never agents.** Embedding GIFs, building/
   extending indexes, fixing collisions, scanning for broken links, frontmatter
   edits across many files — all have copy-paste scripts in `assets/scripts.md`
   and cost ZERO model tokens. Never spawn an LLM agent to do what a script does.
3. **Match model tier to task** (pass `model:` to the Agent/Workflow tool):
   - **Haiku/cheap** — mechanical, well-specified, low-judgement: GIF-embed
     passes that a script can't quite cover, formatting/readability passes, the
     inline bold-link pass, frontmatter `lecture:` appends, index prose tweaks.
   - **Sonnet/mid** — bulk note authoring from clear source: term notes, formula
     notes, `## Visual` diagram passes. The volume work. Quality is fine here.
   - **Opus/top** — only where judgement compounds: the lecture-note teaching
     walkthroughs (Phase 3/5), the arc/narrative design, ambiguous source
     reconciliation, and the orchestrator itself (planning, verifying, deciding).
   When unsure, default a *whole batch* to Sonnet and reserve Opus for lectures.
   A fresh 600-term build done all-Opus vs. tiered is a large cost delta for
   indistinguishable output.

If you find yourself reading a 90-slide PDF into the main context "to plan",
STOP — spawn an Explore/inventory agent instead.

## Phase 0 — Scope the request (a FRESH build ASKS; an incremental add doesn't)

Lock these BEFORE building. **On a fresh from-scratch build, ASK the user — don't
assume.** Use the **AskUserQuestion** tool to put the real choices to them
explicitly (the user is committing significant time/tokens and deserves to drive
the scope). You don't have to ask all of the items below — most have a safe default.
ASK the ones that materially change the build; let the rest ride their defaults
and just state them in the plan. Batch with AskUserQuestion (up to 4 questions at
once), highest-impact first, ~2–3 rounds:
- round 1 (the big levers) = {coverage scope, build cadence (if many lectures),
  animation level, worked examples/problems}
- round 2 (shape & audience) = {audience/reader level, lecture-note depth,
  flashcards on/off, vault name (confirm the derived default)}
- round 3 only if still open = {formula granularity, language, term↔formula
  coupling, navigation, dataview dashboards}
For each question give 2–4 concrete options with the recommended one first and
labelled "(recommended)", so a user who just wants the sensible build can
one-click it. Then echo the locked answers into the plan file before executing.

Don't make the user type things you can compute: **source files** (item 1) you
glob from the directory they pointed at and confirm the found list; the **vault
name** (item 5) you DERIVE a sensible default for — but still CONFIRM it, since
it's the most visible, personal part of the output. Everything else is a real
choice to put to them.

If the user ALREADY stated a decision in their request (e.g. "full course, max
visuals, one GIF per term, no flashcards"), honor it and DON'T re-ask that item —
only ask the ones still genuinely open. The goal is "confirm the plan together,"
not "interrogate." (Incremental add / small tweak: confirm the few relevant
choices inline, no AskUserQuestion ceremony.)

The decisions to lock (ask the open ones via AskUserQuestion):

1. **Source files** — exact paths. Lecture slides (PDF/PPTX), recitations,
   an existing study guide (HTML/MD), notebooks (.ipynb). If the user gave a
   directory, glob it yourself; don't ask for a list you can discover. Note
   which topics are *only* in slides vs *only* in the guide (the guide often
   skips foundational lectures — those are real gaps to flag).
2. **Coverage scope** — every lecture+recitation, or a subset? Offer: "full
   course", "match the existing guide", or "guide + key missing foundations".
3. **Language** — English notes (cleanest linking, recommended) vs source
   language. Note *titles* in English with `aliases:` even if prose is localized.
4. **Formula granularity** — one note per distinct formula (max atomicity,
   recommended) vs grouped-by-concept vs a single master note.
5. **Vault name & location — DERIVE a default, then ASK to confirm.** This is the
   most visible, personal thing about the output, so always put it to the user —
   but do the work for them: propose a sensible default and let them accept or
   override in one click. Derive the default from the **course/subject name in the
   source parent directory**, placed *next to* the sources — e.g. sources in
   `.../CS/YearC/ai/lectures` → propose `.../CS/YearC/ai/AI Vault`. Ask with
   AskUserQuestion (recommended option = the derived name; other options can be a
   couple of plausible alternatives + "let me type a custom name"). If the parent
   dir is uninformative (`Downloads`, `tmp`), lean harder on the subject from the
   content and still confirm. If the user RENAMES later, just `mv` the folder —
   Obsidian links are path-independent, nothing inside changes; re-run `verify.py`
   at the new path.
6. **Term↔formula coupling** — transclude (`![[f- X]]`, renders inline AND
   stays atomic — recommended) vs link-only.
7. **Animations** — ALWAYS ask this one (AskUserQuestion); it's the biggest
   cost/quality lever. Offer four choices:
   - **Full** — an animation for *every* term. Sub-ask the fidelity: template
     GIFs (fast/cheap, ~15–20 re-labelled shapes) vs **LLM-authored per-term**
     (genuinely bespoke per concept, ~1 cheap call + render each). They compose:
     template baseline, LLM-upgrade the key concepts.
   - **Semi / selective** — animations only for the dynamic/visualizable key
     concepts; static diagrams (Mermaid/ASCII) for the rest. Often the best ROI.
   - **None** — static diagrams only (Mermaid/ASCII/tables). Cheapest; still rich.
   - **After the vault is built** — generate notes + static visuals now, run the
     whole animation pass LATER as a separate step (the user reviews the vault
     first, or wants to defer the GIF cost). Animations are strictly additive to
     `## Visual`, so this is a clean second pass — see Phase 4 (it can run any
     time after notes exist) and the incremental-add mode. Confirm a default
     fidelity now so the later pass needs no re-ask.
   See Phase 4's three animation paths for the mechanics. Whichever the user
   picks, **only animate concepts with a visual logic** — see the note in Phase 4
   on animatable vs. purely-abstract concepts.
8. **Navigation** — full MOC (Home + indexes + tags, recommended) vs minimal.
9. **Lecture-note depth** — **full teaching walkthrough (recommended)** vs thin
   connector. Default to full: a lecture note must let a student learn the whole
   lecture from the note alone (see Phase 5). Thin glossary-style connectors are
   a known failure mode users reject.
10. **Lec 1–2 / probability-recitation depth** if those are PDF-only and not in
    the guide — read fully (recommended) vs lighter.
11. **Flashcards / spaced repetition** — emit review cards in each note (`Q::A`
    + `==cloze==`, deck-tagged) so the vault is exam-ready, vs prose-only. For a
    STUDY vault this is high-value; default ON unless the user wants reading-only.
    See Phase 4b.
12. **Live dashboards (Dataview)** — make the indexes live queries (auto-listing
    terms/formulas, flagging unreviewed) vs static link lists. Default ON for the
    indexes; it degrades gracefully (shows a code block) if Dataview isn't
    installed. See Phase 6.
13. **Audience / reader level** — who reads this, and what do they already know?
    Offer: "me, exam-prep" (concise, exam-relevant, assume the course's
    prerequisites) · "long-term reference" (thorough, self-contained) · "teaching
    / sharing" (most explanatory, define prerequisites too). This shifts every
    note's depth and tone: a prereq-aware exam vault re-teaches less and stays
    tight; a teaching vault explains foundations from scratch. Default
    "long-term reference". (One global setting; don't re-ask per note — bake it
    into the builder prompts.)
14. **Worked examples & practice problems** — the source often has solved
    examples / exercises / past problem sets. Offer: "weave worked examples into
    the relevant notes" (a `> [!example]` per concept, recommended for STEM) ·
    "also create a per-lecture `Problems` note" (linked practice, great for exam
    prep) · "skip — concepts only". If the source folder contains exams/psets,
    flag them and ask whether to fold them in. Worked examples are high-value and
    currently easy to lose — verify their arithmetic yourself (Phase 3 rule).
15. **Build cadence — ASK whenever the job is big** (many lectures/files, say >~3
    lectures or >~50 expected notes). How does the user want it produced?
    - **Full build, end to end** — do the whole course in one go (after the
      sample-first checkpoint). Best when they trust the sample and want to walk
      away. Default for a confident user.
    - **In batches** — do N lectures (e.g. 2–3) at a time, pause, let them review,
      continue. Best for steady oversight without a stop per lecture.
    - **One lecture / file at a time** — build a single lecture (or single source
      file), STOP, wait for "next" before the following one. Most control,
      slowest; good when the user is curating closely or unsure of style.
    Track progress with a todo list either way so a paused build resumes cleanly.
    This is independent of the sample-first checkpoint (which always shows ONE
    lecture first); cadence governs everything AFTER that sign-off.

## Phase 1 — Inventory (delegated; orchestrator keeps only the checklist)

Do NOT read full sources in the main context. Spawn an **inventory sub-agent**
(Sonnet; Explore-type or general) per source or per lecture-cluster. Give it the
path + page range and this contract — it reads, you keep its short return:
- **PDF**: read in ≤20-page chunks (the Read tool errors on big PDFs without a
  page range). Slides are image-heavy — read them as images and transcribe math.
- **PPTX**: convert/extract first (e.g. `libreoffice --headless --convert-to pdf`
  or `python-pptx`); then treat as PDF/text.
- **HTML/MD guide**: read in chunks; it is usually the most accurate, fact-checked
  source for the lectures it covers — prefer it, but verify numeric examples.
- **.ipynb**: read fully (cells + outputs).

Each inventory agent returns ONLY two compact checklists (not the slide text):
- **List A — every distinct term/concept** (granular: "Softmax", "Cross-Entropy",
  "Receptive Field", "Vanishing Gradients", "Bayes Theorem", …).
- **List B — every distinct formula** (model, loss, gradient, update rule,
  init, …), each with LaTeX + which term(s) it belongs to.
Plus each lecture's section/heading structure (drives lecture notes).

KEEP these returned checklists in the orchestrator — they are the completeness
spec for Phase 3 and the final audit. You now know WHAT to build without ever
having held the raw slides. (For a tiny single-lecture add, reading it once in
the main context is fine — the rule bites at scale and on re-reads.)

## Phase 2 — Scaffold

```
Vault/
  .obsidian/app.json          # copy assets/obsidian-app.json
  .obsidian/graph.json        # copy assets/obsidian-graph.json (color groups)
  .obsidian/page-preview.json # copy assets/obsidian-page-preview.json (hover popups)
  README.md                   # only if sharing/publishing — from assets/README-template.md
  Home.md                     # top MOC (generate in Phase 6)
  Indexes/{All Terms,All Formulas,All Lectures}.md   # generate in Phase 6
  Lectures/                   # L1..Ln + R1..Rn  (lectures AND recitations)
  Terms/                      # one note per List A entry
  Formulas/                   # one note per List B entry, "f- " PREFIXED
  Assets/                     # generator script(s) + anim_*.gif (only if animations)
  Assets/_snippets/           # only for the LLM-authored GIF path: <Term>.py bodies
```
Obsidian opens any folder as a vault; MathJax + Mermaid are built-in (no plugins).
`xychart-beta` works in modern Obsidian.

> [!important] Enable hover previews — users WILL ask "why don't I see a popup?"
> The whole point of an interlinked vault is hovering a `[[term]]` to preview it
> without clicking. Obsidian's **Page Preview** core plugin is on by default but
> ships requiring **Cmd/Ctrl+hover**, so plain hover shows nothing and the vault
> feels dead. Ship `.obsidian/page-preview.json` with `previewWithoutModifier:
> true` (+ `sourcePreview: true`) so plain hover works in both edit and reading
> mode — copy `assets/obsidian-page-preview.json`. **Config under `.obsidian/`
> is only read at startup**, so tell the user to reload (Cmd+P → "Reload app
> without saving", or quit/reopen) for it to take effect.

## Phase 3 — Build (batched · parallel · formulas FIRST)

Order: **formulas before terms** (terms transclude them) before **lecture notes**
(they link to both). Batch **by lecture**; run batches as parallel sub-agents.

Thread the Phase-0 answers into EVERY builder prompt: the audience/reader level
(item 13 — sets depth/tone and whether to re-teach prerequisites) and the
worked-examples choice (item 14 — weave `> [!example]` solved problems into notes
and/or build per-lecture `Problems` notes). On a large build, do the **first
lecture's batch, then run the sample-first checkpoint** (see Working mode) before
launching the rest. After sign-off, honor the chosen **build cadence** (item 15):
full = produce all remaining lectures; in-batches = N lectures then pause for
review; one-at-a-time = a single lecture/file then STOP for "next". Keep a todo
list of lectures so a paused build resumes exactly where it left off.

Each sub-agent prompt MUST include, verbatim:
- The exact templates (paste from `assets/templates.md`, don't reference).
- The naming convention restated in full (the `f- ` prefix; ` - ` for `/` `:`).
- A **disjoint scope** (explicit file list or alphabetical range).
- "ADD-only. If a note already exists, another batch owns it — SKIP it and
  just `[[link]]` to it. Never overwrite."
- The **source path + page range** to read (NOT pasted slide text). The builder
  reads its own slice in its own context and discards it — see Token economics.
  EXCEPTION (use judgement — quality first): pass a compact Phase-1 checklist
  entry instead of a path when it is genuinely sufficient. It IS sufficient for
  **formula notes** (the LaTeX is the content) and for **shallow/standard term
  notes**. It is NOT sufficient for subtle terms, anything with a source-specific
  numeric example or quirk, or **lecture walkthroughs** — for those the builder
  MUST read the source slice itself (path + page range), because losing the
  slides' concrete numbers/examples is exactly the quality regression to avoid.
  When in doubt, give the path: a re-read is cheaper than a wrong note.
- The intended model tier for this batch (Sonnet for term/formula volume; Opus
  only for lecture walkthroughs) — set via the Agent/Workflow `model:` param.
- "Report counts + filename list + what you SKIPPED." (A SHORT report — do not
  echo back note bodies; the orchestrator verifies via `verify.py`, not by
  re-reading what the agent wrote.)

Every note (full templates in `assets/templates.md`):
- **Term**: frontmatter → `Formal definition` · `In simple words`
  (`> [!tip] In simple words` callout ending `> **Analogy:** …`) ·
  `Why we need it` · `Formulas` (transclusions, each on its own line) ·
  `Visual` (Phase 4) · `Related` (` · `-joined links) · `Source`.
- **Formula** (`Formulas/f- <Name>.md`): frontmatter w/ `belongs-to` → `$$…$$` →
  **`Symbol-by-symbol` table covering EVERY symbol** (every letter, sub/
  superscript like `[l]`, `∑`+bounds, `∇`, `∂`, `½`, `η`, `⊙`, `∈`, `argmax`,
  `sgn`, the threshold) → `What it computes` → `Why this form` (`> [!tip]`
  intuition; numeric example in `> [!example]`) → `Used by` → `Source`.
- **Lecture/recitation = FULL TEACHING WALKTHROUGH, not a thin connector.**
  A student must be able to learn the ENTIRE lecture from the note alone.
  For EACH subtopic: define the concept, explain the *mechanism / how it works*,
  give the slides' concrete examples and numbers, explain *why it matters* and
  the tradeoffs, and walk any process step by step. Use short paragraphs,
  bullet lists where the slides enumerate, and `> [!example]`/`> [!important]`/
  `> [!warning]` callouts. Add `### subsections` freely. `[[term links]]` are
  for going DEEPER, **never a substitute for explaining the idea in-note**.
  Calibration: a lecture note for an ~80-page slide deck should land around
  **250–450 lines** (one dense compressed paragraph per topic = the rejected
  failure mode). Do NOT inline full math derivations (those live in atomic
  formula notes — transclude `![[f- …]]`), but DO teach what the formula means
  and a worked number. Ends with `## Concepts in this lecture` (every term) +
  `## Navigation` (Prev/Next). The arc box, arc diagram, and bridge sentences
  are added in Phase 5 (scaffold); the *teaching body* is written here.
  Because each note is long, build/rewrite them with parallel sub-agents
  (≈2 notes per agent), each re-reading its own source PDF/notebook in full.

Verify every numeric example's arithmetic YOURSELF. If the source has a quirk
(e.g. a guide using log base-10, Adam without bias-correction, an unusual
`p`=keep-probability convention), document it in a `> [!warning]` — do NOT
silently "fix" the source; the exam follows the source.

After the parallel build, immediately run the **collision fix** (see Hard-won
rules + `assets/scripts.md` → `fix_formula_collisions`) and `verify.py`.

## Phase 4 — Visuals (everywhere they teach)

Add a `## Visual` section to EVERY term note (before `## Related`) and 1–2 per
lecture note. Pick the BEST type per concept — never force one style:

- **Mermaid `graph LR/TD`** — flows, architectures (LeNet/VGG/ResNet w/ skip),
  gate behaviours, taxonomies, computational graphs, pipelines.
- **Mermaid `xychart-beta`** — REAL plotted curves: activation shapes,
  bias-variance U-curve, loss curves, LR-decay schedules, vanish/explode,
  λ-shrinkage. Format: `xychart-beta` / `title "…"` / x-axis / `y-axis "…" 0 -->
  N` / `line [..]` (multiple `line` for comparison), ~6–9 rounded points.
- **ASCII grid art in `text` fences** — spatial things Mermaid cannot do: conv
  sliding window WITH worked numbers, max-pool 2×2→1 (`3 4 / 5 4`), padding
  rings, stride landings, receptive-field trace-back, im2col unroll, XOR grid,
  decision boundary + w arrow, the weather×clothing probability table,
  param-count box (`64·(3·5·5+1)=4864` vs FC). Space-align, no tabs.
- **Tables — prefer a Markdown (GFM) `| col |` table; raw HTML `<table>` only as
  a last resort.** DENSE tabular data (per-layer architecture: layer · out
  C/H/W · memory · params · FLOPs; method-comparison matrix; generations
  timeline) is best as a GFM pipe-table — it renders in Obsidian AND every other
  markdown viewer, and stays portable if the vault is shared/published. Reach for
  raw `<tr>/<th>/<td>` ONLY when you need rowspan/colspan or nested formatting a
  GFM table genuinely can't express. **Portability caveat (matters for a public
  vault):** raw HTML breaks in non-Obsidian renderers AND Obsidian has known bugs
  rendering markdown *inside* HTML blocks — so never put `[[links]]`, `**bold**`,
  or `$math$` inside an HTML block. Whichever you use, keep flows/spatial things
  in Mermaid/ASCII, and keep an ASCII mini-summary above a big table so the note
  still reads as plain text.

A note can carry MORE THAN ONE static visual — a Mermaid flow PLUS an ASCII
worked-example, or an ASCII summary PLUS a full HTML table, is good when each
teaches a different facet. Don't force two where one suffices, but for the
richest notes (architectures, layer budgets) two is the norm, not excess.

Mermaid rules (rendering breaks otherwise): quote labels with `()`/operators;
**NEVER put `$`/LaTeX inside a mermaid block**; `<br/>` for line breaks; close
every fence. Run these via parallel sub-agents in topic clusters (CNN /
backprop / optimization / activations+reg / foundations), ADD-only (`## Visual`
inserted before `## Related`, nothing else touched), with the same
"report counts, link counts unchanged" discipline.

### Animations (high-value; aim for max coverage if asked)

> [!important] Animate only concepts with a VISUAL LOGIC — not every term should move.
> An animation earns its place when the concept is spatial, temporal,
> quantitative, or relational — something with motion or change to show: a
> process unfolding, a window sliding, curves crossing, a balance tipping, a
> distribution sharpening, a network traversed, a value rising over time. This is
> SUBJECT-AGNOSTIC and verified across fields — psychology (conditioning link
> strengthening), economics (supply/demand equilibrium), sports (offside line),
> medicine (action-potential spike), law (burden-of-proof scale tipping) all
> animate well. But a **purely abstract or definitional** concept has no natural
> motion (e.g. *mens rea*, "the ego", a taxonomy label, a named principle) —
> forcing a GIF onto it yields a contrived or empty animation. For those, use a
> STATIC visual (a definition box, a Mermaid taxonomy, a comparison table) and
> skip the GIF. So even in "animate every term" mode, the builder/LLM should
> judge per concept: visual logic → animate; abstract → static only. Don't
> manufacture motion where there is none.

matplotlib(`Agg`)→`PillowWriter` GIFs (dark theme, looping, ~10–80 KB each;
**no ffmpeg needed**). THREE paths, increasing fidelity ↔ increasing cost — pick
by the Phase-0 answer and the subject:

| path | fidelity | cost | when |
|------|----------|------|------|
| template generator | shapes, re-labelled | ~free (deterministic) | fast baseline, on-domain subjects |
| **LLM-authored (per-term)** | **genuinely per-concept** | ~1 cheap call + render / term | **the real "per-term" answer** |
| hand-authored generator | artisan, exact | your time | a few key concepts a script can't nail |

They COMPOSE: run the template generator as a cheap baseline, upgrade the
concepts that matter with the LLM path or a hand-authored override. Bundled:

- **`assets/animation_generator.py`** — hand-authored, one function per dynamic
  concept; reuse one GIF across closely-related notes. Use when only KEY dynamic
  concepts get GIFs. Register functions in named batches with a CLI selector
  (`python3 _generate.py batch3`) so subsets regen cheaply.
- **`assets/per_term_generator.py`** — **per-term 1:1 generator** for "a
  dedicated GIF for every term note" (100% file coverage). It carries ~25 **base
  templates**, each depicting one concept SHAPE — distribution-sharpening,
  loss-curve descent, monotone trend, pipeline, cycle/loop, tree, layer stack,
  graph-walk, vector/cosine/analogy, scatter-cluster, confusion-matrix, vote,
  debate, retrieve, memory, gate, sliding-window, chunking, typewriter.
  `template_for(term)` routes by concept shape; the template pulls per-term
  labels (the note's bold phrases via `note_params()/labels()`) + a name-seeded
  rng for colors/counts. **Honest scope:** distinct FILES, but ~15–20 distinct
  SHAPES re-labelled across terms — NOT N unique animations, and keyword routing
  not comprehension. Describe it to the user as "a relevant animated diagram per
  term," not "a unique animation for every term." For genuinely bespoke
  per-concept fidelity use the LLM-authored path (below); see also the override
  warning further down.
  `--force`, `--only "Name" …`,
  `--batch i n` (shard for parallel runs — 8 background shards do 624 in ~60 s).
  > ⚠️ **Hard-won:** the FIRST version of this had only 5 crude families and a
  > broken pipeline template that rendered a single blank box for hundreds of
  > terms — technically unique files, visually identical garbage, and the user
  > rightly rejected it. The bar is *perceptual* distinctiveness + concept
  > fidelity, NOT just byte-unique md5s. ALWAYS: (1) after generating, check the
  > spread of distinct file SIZES (near-equal tiny sizes ⇒ a degenerate
  > template), not just `md5 | sort -u` — this is a cheap SHELL check, no tokens,
  > do it first and let it gate the visual pass; (2) read back 6–10 GIFs spanning
  > different templates as images and confirm each depicts its concept — but do
  > this in a CHEAP vision sub-agent (Haiku/Sonnet) that returns a one-line
  > pass/fail verdict per GIF, so the ~1.5k-tokens-per-image cost lands in a
  > disposable context, not the orchestrator's. Only pull a GIF into the main
  > context when a verdict flags one as suspect; (3)
  > make label helpers return EXACTLY the requested count (a short
  > `(bolds+words)[:k]` list silently under-fills and throws "list index out of
  > range" mid-batch). Reference scale: 624 terms → 624 GIFs, ~13 MB, ~60 s.
- **`assets/llm_gif_pipeline.py`** — **LLM-authored per-term GIFs: the genuine
  "one bespoke animation per concept" path.** A cheap-model sub-agent reads each
  term note and writes the per-frame DRAWING BODY of a matplotlib animation that
  depicts THAT concept's actual mechanic (a sliding pooling window computing its
  max; a skip-connection pulse adding into F(x); two class distributions
  separating). The harness supplies the fixed scaffold (figure, `FuncAnimation`,
  `PillowWriter`, save) and SANDBOXES the snippet: it execs only the body inside
  `draw(ax, i, n, np, plt, palette, P)` with a restricted builtins set and a
  forbidden-token guard — **no `import`, file, network, or `os` access**, so
  model-written code can't escape matplotlib+numpy. Use this when the user wants
  truly per-term fidelity at scale and accepts ~1 cheap call + a render per term.

  LLM-GIF WORKFLOW (run AFTER notes exist; cheap model; batched):
  1. Pick the terms to upgrade (all, or just the ones a template spot-check
     flagged as generic). For each, a sub-agent reads the note and EITHER writes
     its drawing body to `Vault/Assets/_snippets/<Term>.py` (the BODY only — the
     SNIPPET CONTRACT is in the harness docstring; paste it into the agent prompt
     verbatim) OR, if the concept is purely abstract/definitional with no visual
     logic (see the [!important] note above), SKIPS it and reports it as
     static-only so the orchestrator leaves that note's existing static diagram
     alone. Run agents in parallel, disjoint term lists, ~20 terms each, on a
     cheap model — they each see only their note, not the whole vault.
  2. Render the batch: `python3 Assets/llm_gif_pipeline.py --snippets
     Assets/_snippets --terms Terms --out Assets`. It prints per-term FAIL
     (guard/compile/render) and SUSPECT (tiny file ⇒ likely blank) lines and
     exits nonzero if anything failed.
  3. **Self-repair loop:** for each FAIL/SUSPECT, hand that term's note + the
     harness's error string back to a sub-agent to rewrite just that snippet;
     re-render only those. Repeat until 0 fail / 0 suspect.
  4. Vision spot-check a sample (cheap vision agent, one-line verdict per GIF, as
     for the template path); regenerate any that don't depict their concept.
  5. Embed exactly as any GIF (`embed_per_term` in `scripts.md`).
  > Why a SNIPPET body, not a whole script: it confines the model to "draw frame
  > i of this idea," keeps all file/animation I/O in the trusted harness, and
  > makes every output uniform (same size, theme, fps) and safely sandboxed.
  > Verified end-to-end: distinct faithful GIFs per concept; an `import os`
  > snippet is rejected at the guard stage.

Workflow either way:
1. Copy the chosen generator to `Vault/Assets/_generate.py`. Keep idempotent.
2. Run; spot-check a few GIFs by reading them back as images.
3. Embed `![[anim_*.gif]]` at the TOP of the target note's `## Visual`
   (`**Animated:** caption` + the embed), keeping the static diagram BELOW
   (animation = intuition; static = exact mechanics). Use the embed script in
   `assets/scripts.md` (`embed_gifs`, or `embed_per_term` for the 1:1 case —
   both idempotent, won't double-embed). The slug function MUST match between
   generator and embed script (same `anim_` + alnum-lowercase rule).
For the hand-authored path, only animate genuinely dynamic ideas (descent
paths, sliding filters, gradient flow, curve sweeps, drift) and reuse freely.
For the per-term path, EVERY term note gets its own GIF by design.

> [!warning] Generic templates give a REASONABLE shape; concept-perfect GIFs need a subject generator.
> `per_term_generator.py` routes each term to one of ~25 templates by CONCEPT
> SHAPE (sequence / cycle / hierarchy / comparison / distribution / geometry /
> graph / decision), so it now spreads any subject across many templates instead
> of dumping off-domain terms into one catch-all (verified: a 248-term CNN/DL
> vault routes across 17 templates, none >14%). But shape-routing only gets you a
> *plausible generic* animation — it does NOT know what an "Inception module" or a
> "Residual block" actually looks like. For concepts whose real mechanic no
> generic template depicts, the fidelity bar (perceptual + concept-faithful) still
> requires a **hand-authored subject generator** that overwrites just those slugs:
> one faithful template function per concept (parallel-branches→concat, skip-add
> with a traveling pulse, encoder-decoder with skip arrows, error-vs-depth U-turn,
> channel-squeeze bottleneck). **`assets/example_subject_generator.py` is the
> bundled worked example (CNN architectures)** — copy its structure for a new
> subject. Keep matplotlib
> `Agg`+`PillowWriter`, dark theme, looping; clamp any `f//k`-style stage index
> (`min(maxstage, f//k)`) or the last frames throw IndexError; pre-populate frame 0
> (a template that animates IN from nothing shows a jarring blank first frame).
>
> Decision rule: run the generic generator first (cheap, covers everything), then
> spot-check (cheap shell size-spread + a vision-agent verdict pass), and
> hand-author overrides ONLY for the concepts the verdicts flag as generic/wrong.

**Second animation (`**Animated (2):**`).** A note may carry TWO GIFs when one
shows structure and another shows a different mechanic (e.g. an architecture's
static branch layout + a packet flowing through it; a residual block + the
gradient travelling back the skip). Embed the second right after the first:
`**Animated (2):** <caption>` / blank / `![[anim_<slug>_b.gif]]`. Reserve this for
genuinely dynamic concepts (~1/3 of notes); definitions/taxonomies don't need it.
NOTE: `verify.py` flags `**Animated:**` appearing >1× as a duplicate-embed
PROBLEM, so the second MUST be labelled `**Animated (2):**` (distinct string), not
a repeated `**Animated:**`.

GIF gotchas: matplotlib `RankWarning`/`Polyfit poorly conditioned` is harmless
(high-degree overfit is the intended visual — filter it from logs). Inside a
`FuncAnimation` update closure use `np.random.RandomState(seed)`, not
`rng.RandomState(i)` (the latter throws "list index out of range"). No `$`/raw
LaTeX in plot titles/labels (use `pi`, `sigma`, words) so they render in the GIF.

## Phase 4b — Flashcards (runs after visuals; makes it a STUDY vault, not just a reference)

A dedicated enrichment pass between visuals and narrative. If Phase-0 says ON:
each term note ends with a `## Review` section carrying
spaced-repetition cards in the **Spaced Repetition plugin** (st3v3nmw) syntax, so
the vault is exam-ready and Anki-exportable out of the box. Strictly additive
(insert `## Review` between `## Related` and `## Source`); do it as a cheap-model
batch pass over the finished notes.

Per term note emit 1–3 cards drawn from the note's OWN content (don't invent
facts): a basic `::` card for the definition, optionally a `==cloze==` of the
one-line "simple words" sentence, and a `:::` reversed card for a name↔meaning
pair. Scope every card to a hierarchical deck tag so reviews can be filtered by
lecture. Exact syntax (verified — render-safe in Reading view):

```
## Review
<!-- #flashcards/<course>/<lecture> -->

What does **<Term>** mean?::<one-sentence formal definition>

<Term> is, in one line, ==<the key clause from the simple-words callout>==.

<Term>:::<the 3–5 word gist>   %% reversed: makes both directions %%
```

Rules / gotchas:
- The deck tag (`#flashcards/…`, plural, configurable) is what the plugin scans —
  put ONE per `## Review` block (an HTML-comment `<!-- … -->` keeps it out of the
  rendered prose but still tag-scannable; or a plain `#flashcards/…` line if you
  want it visible). Notes without the tag are simply never scanned — zero risk.
- `::`, `:::`, `?`/`??` (multi-line) render as literal text in Reading view, so
  cards don't disturb the note; only `==…==` shows as a highlight (fine).
- Cloze default delimiter is `==…==`; do NOT also use `==highlight==` decoratively
  elsewhere in the same note or it becomes an accidental card.
- Keep math OUT of the answer side unless wrapped properly — a bare `$` triggers
  the same verify.py `$`-imbalance and the plugin won't render MathJax on the card
  cleanly; prefer words, or reference `[[f- …]]`.
- **Anki path:** this syntax is also consumable by `Obsidian_to_Anki`/Yanki, so
  one format serves both. Mention this to the user; don't build a second format.
- Formula notes generally DON'T need cards (the symbol table is the study object);
  add a single cloze on "what it computes" only if the user wants full coverage.

## Phase 5 — Narrative flow (make it a lecture, not a glossary)

A glossary lists topics; a lecture *threads* them. For every lecture/recitation
note, ADD (strictly additive — never remove/reword/reorder existing content):

1. **Arc box** — `> [!abstract] The arc of this lecture` right after the top
   blockquote: para 1 "Where we left off:" linking the *previous* lecture's
   ending problem; para 2 the through-line naming each section as
   problem→fix→next-problem.
2. **Arc diagram** — a Mermaid chain (~5–7 nodes) of that story + a caption.
3. **Bridge sentences** — between consecutive teaching sections, a one-line
   italic blockquote `> *We just did X; but problem Y → so next, Z.*` specific
   to the adjacent content. Skip before `## Concepts` / `## Navigation` /
   `## Visual`.
**Chain lectures to each other**: lecture N ends on the exact problem lecture
N+1 opens by solving; each note's arc box "Where we left off" links the prior
note and the Prev/Next forms one unbroken chain (including recitations
interleaved in reading order, e.g. L1→R1→L2→R2→…). Frame recurring patterns
explicitly ("Attempt 1 / 2 / 3, each fixing the previous flaw"). Do the richest
lectures yourself to set the reference, then delegate the rest pointing agents
at your reference note.

**Scaffold preservation when rewriting a lecture body.** If you expand a thin
lecture into a full walkthrough (Phase 3 depth) AFTER the scaffold exists, the
sub-agent prompt MUST list the protected elements verbatim and say "strictly
additive to the teaching prose; do NOT remove/reword/reorder": frontmatter,
H1+overview blockquote, the `> [!abstract]` arc box, the arc ```mermaid``` block
+ caption, every italic bridge sentence (kept between the same two sections),
every `![[…]]` transclusion, the `## Concepts` list, and the `## Navigation`
line. Audit afterward that each note still has arc=1, mermaid≥1, nav=1.

## Phase 6 — Readability, indexes, verify

**Readability pass** (often requested separately; strictly additive):
- Split any >2-sentence paragraph into short paragraphs / bullets with blank
  lines. One idea per line. Put each `![[…]]` transclusion on its own line.
- Convert "In simple words"/analogy → `> [!tip]`; key idea → `> [!important]`;
  gotcha → `> [!warning]`; worked numeric example → `> [!example]`. Trailing
  link lists → a `**Related:**` line.
- Callout syntax: every continuation line starts with `> `; a blank `>` is the
  in-callout blank line. A truly empty line *ends* the callout. NOTE: a blank
  line between two `> [!x]` blocks is CORRECT (adjacent separate callouts) — do
  not "fix" those; the real bug is an empty (non-`>`) line *inside* one callout.

**Inline term auto-linking pass (lecture/recitation notes — strictly additive).**
Full teaching bodies flag key concepts in **bold** but the prose itself has no
`[[links]]` — only the `**Related:**` footer does. A reader hovering a bold term
mid-paragraph cannot click through. Fix with `assets/scripts.md` →
`link_bold_terms`: for each lecture note, link the **first** bold span per note
whose exact text (trailing punctuation stripped) matches a Term basename or
alias, as `**[[Canonical Name|readable phrase]]**` (keeps the lowercase prose
readable, points to the right note). HARD RULES learned the hard way:
- ONLY link bold spans that EXACTLY match a known name. A naive "link any word
  that matches a term" rule mis-links generic words (e.g. "recall storage" →
  wrong `[[Recall]]`). Exact-bold-match has ~zero false positives.
- Build the name index from `ls Terms/` + each note's `aliases:` (NOT formulas
  — they're transcluded via `![[f- …]]`; bare formula links collide).
- Protect frontmatter, ``` fences, `inline code`, existing `[[..]]`/`![[..]]`,
  headings, and the `**Related:**`/`## Concepts`/`## Navigation` footer lines.
- One link per term per note (first mention) is correct for navigation — don't
  link every occurrence. Bold phrases with no matching note stay unlinked.
Reference scale: 16 lecture notes → ~380 inline links added, 0 broken.

**Indexes (generate by SCRIPT from real files — never hand-type):** use
`assets/scripts.md` → `build_indexes`. Produces `Home.md` (MOC),
`All Terms` (grouped by lecture frontmatter), `All Formulas` (THE big formula
note: per lecture, each `### [[f- X]]` then `![[f- X]]` so the full symbol table
renders inline), `All Lectures` (course order).

**Live dashboards (Dataview, if Phase-0 says ON).** Static link lists go stale
the moment a note is added; a Dataview block stays current and adds zero
maintenance. Add a couple of query blocks to `Home`/indexes ON TOP of (not
instead of) the static lists — the static list is the portable fallback when
Dataview isn't installed (Obsidian shows the unparsed code block, which is ugly
but harmless). These rely on the YAML `type:` / `lecture:` frontmatter every note
already has. Verified-correct queries to drop in:

````
```dataview
TABLE lecture AS "Lecture", file.link AS "Note"
WHERE type = "term"
SORT lecture ASC, file.name ASC
```
````
A "needs review" dashboard (only meaningful once you add a `reviewed:` field, or
skip): `WHERE type = "term" AND reviewed = null`. Gotchas: field *values* are
case-sensitive (`"term" ≠ "Term"`); use `WHERE !field` or `= null` to find notes
MISSING a field. Keep the static `[[link]]` lists too — they're what survives
export/publish and viewing in any other markdown app.

The readability and inline-bold-link passes are **mechanical → cheap-model
(Haiku/Sonnet) sub-agents**, and the index build/extend is a **script (zero
tokens)** — see Token economics. Don't run these on Opus or do them by hand in
the orchestrator.

**Verify (ALWAYS, after every mutating pass):** `python3 assets/verify.py` from
the vault root. It checks: 0 broken `[[..]]`/`![[..]]`; 0 broken `![[anim_*.gif]]`;
balanced ``` fences; balanced `$`; no `$` in mermaid; every term note has
`## Visual`; no duplicate animation blocks; Term/Formula collision without `f- `;
orphans (warning). Fix until PROBLEMS: 0.

**Verify with the SCRIPT, not by re-reading.** `verify.py` is the source of
truth for structural correctness — do NOT pull dozens of notes back into the
orchestrator to "check" them (that re-pays for content the builders already
wrote). Trust the script; only open a specific note when verify flags it. For
the final quality pass, spot-check **2–3** formula notes' math vs source (a quick
shell `grep`/targeted Read, not a bulk re-read) and open Home + one note of each
kind in Obsidian Reading mode to confirm rendering — that small sample is enough.

## Hard-won rules (do not relearn these the hard way)

- **`f- ` prefix on ALL formula filenames, decided UP FRONT.** Terms and
  formulas WILL collide ("Bayes Theorem", "Normal Equation", "Numerical
  Gradient" exist as both). `Terms/Bayes Theorem.md` + `Formulas/f- Bayes
  Theorem.md` keeps `[[Bayes Theorem]]` vs `[[f- Bayes Theorem]]` unambiguous.
  Retrofitting = renaming files AND rewriting every link (script provided), and
  the rename also corrupts `belongs-to:` self-refs — re-point them to the term.
- **No `/` or `:` in filenames** — use ` - ` (`L2 Loss - Squared Error`). The
  `/` may stay only in the H1 title.
- **Additive edits stay additive.** Formatting / flow / visual / animation
  passes must NOT remove, reword, or reorder content. Verify line counts only
  grew and link counts are unchanged; diff if unsure.
- **Parallel batch agents**: disjoint scope; ADD-only + skip-if-exists +
  link-to-other-batches; identical pasted templates; restate naming convention
  every time. Always run a link-reconciliation + collision pass after.
- **Sub-agent reports describe intent, not outcome.** Always run `verify.py`
  yourself afterward. "Trust but verify."
- **Build links/indexes from `ls`, never from memory.** `[[Name]]` must match a
  file basename exactly. Script the indexes.
- **`![[Note]]` transclusion name-collision**: with the `f- ` prefix this is
  avoided; without it, Obsidian shows an ambiguity picker.
- The "broken target" scan will list literal template words like `Term` /
  `Formula` if a lecture says "links to [[Term]]/[[Formula]]" in prose —
  de-link those (make them code) ; and forward-links to not-yet-created lectures
  are expected mid-build (resolve by end).
- **`verify.py` only strips ```triple-fenced``` blocks, not `inline code`, and
  counts EVERY `$`.** Consequences seen in real builds: (a) a literal protocol
  token like `'[[rating]]'` or `'Rating: [[5]]'` inside a judge-prompt quote
  scans as a broken `[[link]]` even wrapped in backticks — rephrase it (e.g.
  "the double-bracket rating token"), don't rely on `` ` ``. (b) Currency `$18`
  / `$VAR` placeholders make the `$` count odd → "unbalanced $ MathJax" even
  with no real math. `\$` does NOT help (still a `$` to the regex). If a note
  has no real inline math, eliminate bare `$` entirely (write `18 USD`, drop the
  `$` from `$DOC_STRING`). These bite the long teaching-walkthrough notes most.
  (c) **`verify.py` matches link targets against file BASENAMES, not `aliases:`.**
  Obsidian resolves `[[Softmax]]` to `Terms/Softmax Function.md` via its alias, but
  verify.py reports it as a broken link. Two fixes, prefer the first: (1) link with
  an explicit display alias — `[[Softmax Function|Softmax]]` — which is unambiguous,
  matches the file, AND keeps the prose word; (2) check the vault's own convention
  (`grep -ro "\[\[Softmax[^]]*\]\]"`) and match what existing notes already do. A
  lone `[[Alias]]` is the single most common "broken link" in a verified vault.
- **Inline auto-linking is exact-bold-match only.** Never run a "link any
  occurrence of any term name" pass over prose — it corrupts generic words.
  See the inline-term pass in Phase 6.
- Animation generator: `matplotlib.use("Agg")` + `PillowWriter`; idempotent;
  batch CLI selectors; `np.random.RandomState(seed)` not `rng.RandomState(i)`;
  filter harmless `RankWarning` from logs; no `$` in labels.
- **Per-term GIF label quality.** `note_params()` must extract bolds ONLY from
  `## Formal definition` and `## Why we need it` — NOT the whole note. The
  `> [!tip] In simple words` callout has a `> **Analogy:**` bold line that leaks
  garbage into labels (e.g. Softmax gets label "Analogy"). Also skip
  `> [!…]` callout opener lines. When bolds are empty (plain-prose notes), fall
  back to the term's own name words + semantic pads ("input","output","token"…),
  NOT generic "item/step/node". The `words()` function should camelCase-split
  compound terms for extra richness.
- **`template_for()` routes by CONCEPT SHAPE, not subject keywords.** Layer 1
  keys off shape words any field uses (sequence/cycle/hierarchy/comparison/
  distribution/geometry/graph/decision); layer 2 adds optional domain keywords
  (LLM/agents, ML/DL); layer 3 is a SHAPE-BALANCED hash fallback so unmatched
  terms spread across ~10 diverse templates, never one catch-all. This is what
  makes the generator subject-agnostic — to support a new field, ADD a few
  `kw(...)` lines mapping its vocabulary to the nearest shape, don't rewrite. The
  old failure (a ~10-keyword router dumping 50%+ of terms into one `t_pipeline`
  catch-all) is fixed. Sanity target: no single template should own >15–20% of
  terms; if one does, the field needs more shape keywords or a subject generator.
- **Frame-0 blank issue.** Templates that animate IN from nothing (typewriter,
  bars-grow, tree-build) show a blank/empty first frame — jarring when the GIF
  pauses on load. Fix: start with a pre-populated state at frame 0 (show first
  token, draw bars at 40% height, draw full tree statically then animate a
  traversal dot). Affects: t_typewriter, t_bars_compare, t_tree, t_chunking.
- Vault stays small even with ~250 GIFs (~5 MB) — coverage is cheap; the
  constraint is *pedagogical value*, not size.

## Bundled assets
- `assets/templates.md` — exact term / formula / lecture / index templates.
- `assets/obsidian-app.json`, `assets/obsidian-graph.json` — `.obsidian` config
  (graph color groups: Terms / Formulas / Lectures / Indexes).
- `assets/obsidian-page-preview.json` — `.obsidian` config enabling hover
  previews WITHOUT a modifier key (so plain hover over a `[[link]]` shows the
  popup). Copy to `Vault/.obsidian/page-preview.json`; user must reload Obsidian.
- `assets/README-template.md` — vault-root README for a SHARED/published vault:
  how to open, recommended plugins (Spaced Repetition + Dataview), and a
  content-ownership/license note. Fill in `<Course Name>` and drop at vault root.
- `assets/animation_generator.py` — hand-authored GIF generator + style harness
  + 5 exemplar functions (point/contour/sliding-grid/curve-drawin/pipeline).
  Use for KEY dynamic concepts with GIF reuse.
- `assets/per_term_generator.py` — **per-term 1:1 GIF generator**: ~25
  concept-faithful base templates + `template_for()` **concept-SHAPE routing**
  (subject-agnostic: shape words → optional domain keywords → shape-balanced
  fallback) + semantic per-term parameterisation (`note_params()`/`labels()`) +
  `--batch i n` sharding. For a new field, add a few shape-keyword lines; for
  concepts no generic template depicts, write a subject generator (next asset).
- `assets/example_subject_generator.py` — **worked example** of a hand-authored
  subject-specific generator (CNN architectures): ~12 faithful template functions
  (parallel-branch inception, residual skip-add, encoder-decoder, degradation
  U-turn, …) that overwrite specific slugs after the generic pass. Copy its
  structure when the generic templates don't capture a subject's real mechanics.
- `assets/llm_gif_pipeline.py` — **LLM-authored per-term GIF harness** (the true
  per-term path): safely execs a model-written per-frame drawing body inside a
  sandboxed `draw(ax,i,n,np,plt,palette,P)` (matplotlib+numpy only; forbidden-
  token + restricted-builtins guard), renders `anim_<slug>.gif`, flags failures/
  blanks for a self-repair loop. CLI batches a dir of `<Term>.py` snippet
  sidecars. See the LLM-GIF WORKFLOW in Phase 4.
- `assets/scripts.md` — copy-paste Python for: `fix_formula_collisions`,
  `embed_gifs`, `build_indexes`, `embed_per_term` (1:1 GIF embed),
  `link_bold_terms` (inline term auto-linking), plus broken-target/orphan scans.
- `assets/verify.py` — the full vault verification script (exit 1 on problems).

## Publishing the generated vault (when sharing/open-sourcing)

If the user intends to SHARE or publish the vault (not just use it privately),
optimize for portability and set expectations:
- **Ship a minimal `.obsidian/`** (`app.json`, `graph.json`, `page-preview.json`)
  plus a vault-root `README.md` from `assets/README-template.md` that RECOMMENDS
  Spaced Repetition + Dataview. Do NOT hand-write a `.obsidian/community-plugins.json`
  listing those IDs — that file names *installed* plugins, and referencing ones
  that aren't actually in `.obsidian/plugins/` makes Obsidian error on load. The
  README recommendation is the honest path. Shipping `.obsidian/` with a template
  vault is otherwise normal — it pre-configures graph colors and hover previews.
- **Favor portable syntax** so the vault degrades gracefully outside Obsidian:
  GFM tables over raw HTML; Mermaid/ASCII over HTML; YAML frontmatter `properties`
  for all metadata; `[[wikilinks]]` for STRUCTURE and tags only for STATUS
  (`#flashcards/…`, `#exam-1`) — over-tagging-instead-of-linking is the community
  anti-pattern. Wikilinks/embeds/`==highlights==`/callouts are Obsidian-specific;
  that's fine (the deliverable IS an Obsidian vault) but note it in the README.
- **Content ownership / licensing.** The notes are DERIVED from the user's own
  course material — do NOT assert copyright over that content. If open-sourcing
  the *generator/skill*, a permissive tool license (MIT/Apache) is typical;
  comparable vault tools use AGPLv3+. Add a one-line README note that generated
  output belongs to the source material's owner and may carry the source's
  license/attribution requirements (e.g. lecture slides are usually the
  instructor's). When in doubt, ask the user before publishing course-derived
  notes publicly.
- **Distribution shape:** this skill emits a vault directly (the pragmatic shape).
  A bundled template `.obsidian/` + a short README in the vault root is enough for
  someone to clone-and-open. A full Obsidian *community plugin* would maximize
  discoverability but is a much larger lift — out of scope for the skill itself.
