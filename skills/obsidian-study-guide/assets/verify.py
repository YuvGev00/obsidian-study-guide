#!/usr/bin/env python3
"""
Vault verification — run from the vault root after building / every edit pass.
    python3 verify.py
Exits 0 if clean, 1 if any problem. Checks:
  - broken [[wikilinks]] and ![[transclusions]] (0 expected)
  - broken ![[anim_*.gif]] embeds (0 expected)
  - orphan term/formula notes (never linked)        [warning only]
  - unbalanced ``` fences
  - unbalanced $ MathJax (outside code)
  - $ / LaTeX inside any mermaid block (breaks rendering)
  - every term note has a '## Visual' section
  - notes with >1 '**Animated:**' block (duplicate embed)
  - Term/Formula filename collisions NOT using the 'f- ' prefix
"""
import os, re, glob, sys

ROOT = "."
def md(*parts): return glob.glob(os.path.join(ROOT, *parts))

note_files = md('Terms','*.md')+md('Formulas','*.md')+md('Lectures','*.md')+md('Indexes','*.md')
notes = {os.path.basename(p)[:-3] for p in note_files}
if os.path.exists(os.path.join(ROOT,'Home.md')): notes.add('Home')
gifs = {f for f in os.listdir(os.path.join(ROOT,'Assets'))} if os.path.isdir(os.path.join(ROOT,'Assets')) else set()

problems, warnings = [], []
broken_links, broken_gifs = set(), set()
all_link_targets = set()

for p in glob.glob(os.path.join(ROOT,'**','*.md'), recursive=True):
    raw = open(p, encoding='utf-8').read()
    nocode = re.sub(r'```.*?```', '', raw, flags=re.S)
    for m in re.finditer(r'!?\[\[([^\]]+)\]\]', nocode):
        t = m.group(1).split('|')[0].split('#')[0].strip()
        if t.endswith('.gif'):
            if t not in gifs: broken_gifs.add((os.path.basename(p), t))
        else:
            all_link_targets.add(t)
            if t not in notes: broken_links.add((os.path.basename(p), t))
    if raw.count('```') % 2:
        problems.append(f"unbalanced ``` fences: {p}")
    if nocode.replace('$$','').count('$') % 2:
        problems.append(f"unbalanced $ MathJax: {p}")
    for blk in re.findall(r'```mermaid\n(.*?)```', raw, re.S):
        if '$' in blk:
            problems.append(f"$ inside mermaid: {p}")

# coverage / dup checks on Terms
for p in md('Terms','*.md'):
    raw = open(p, encoding='utf-8').read()
    if '## Visual' not in raw:
        warnings.append(f"term note missing ## Visual: {os.path.basename(p)}")
    if raw.count('**Animated:**') > 1:
        problems.append(f"duplicate animation block: {os.path.basename(p)}")

# orphans
linked = {t for t in all_link_targets}
for p in md('Terms','*.md')+md('Formulas','*.md'):
    n = os.path.basename(p)[:-3]
    if n not in linked:
        warnings.append(f"orphan note (never linked): {n}")

# collision check (Term vs Formula sharing a base name w/o f- prefix)
term_names = {os.path.basename(p)[:-3] for p in md('Terms','*.md')}
formula_names = {os.path.basename(p)[:-3] for p in md('Formulas','*.md')}
bad_collide = [n for n in term_names & formula_names]  # any exact dup is a problem
if bad_collide:
    problems.append(f"Term/Formula filename collision (use 'f- ' prefix): {bad_collide}")

if broken_links: problems.append(f"broken wikilinks: {sorted(broken_links)[:10]}{' ...' if len(broken_links)>10 else ''}")
if broken_gifs:  problems.append(f"broken gif embeds: {sorted(broken_gifs)}")

print(f"Notes: {len(note_files)} | GIFs: {len([g for g in gifs if g.endswith('.gif')])} | link targets scanned: {len(all_link_targets)}")
print(f"PROBLEMS: {len(problems)}")
for x in problems: print("  ✗", x)
print(f"WARNINGS: {len(warnings)}")
for x in warnings[:20]: print("  ·", x)
if len(warnings) > 20: print(f"  · ... (+{len(warnings)-20} more)")

sys.exit(1 if problems else 0)
