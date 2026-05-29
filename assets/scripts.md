# Reusable scripts (run from the vault root)

Copy-paste these. They are the exact, tested operations used to build a
reference vault. All are idempotent and link-safe.

---

## 1. `fix_formula_collisions` — retrofit the `f- ` prefix

> ⚠️ **DANGER — read this.** This is a *recovery* tool, NOT a routine pass. A
> bare link `[[ReLU]]` is ambiguous once both `Terms/ReLU.md` and a formula
> exist: a naive "prefix anything that matches a formula name" rule will wrongly
> rewrite TERM links (it would corrupt ~300 links in a mature vault).
>
> **Best practice: never need this.** Have the Phase-3 build agents write
> formula files as `Formulas/f- <Name>.md` and formula links as `[[f- <Name>]]`
> FROM THE START (the templates already do this). Then there is nothing to
> retrofit.
>
> Only run this when: formulas were accidentally created flat AND a list of the
> formula→term collisions is known, so you can scope the rename precisely. It
> renames the files, then rewrites links **only inside `belongs-to:`,
> `## Formulas` transclusions, and `## Used by` lines** (places that are
> unambiguously formula references), and repairs `belongs-to:` self-refs. It
> deliberately does NOT touch bare `[[X]]` links in prose/`Related` — review
> those by hand against the known collision list. After running, ALWAYS run
> `verify.py` and eyeball a diff.

> **The proven conclusion: NO fully-automatic retrofit is safe.** Empirically,
> a formula note's `belongs-to: ["[[ReLU]]"]` and `Used by` correctly point at
> the **term** `ReLU` (not at `f- ReLU`), and `[[Perceptron Loss]]` in prose
> means the term. Any rule that prefixes "names that match a formula" corrupts
> these. The ONLY unambiguous, automatable signal is a **transclusion in a
> term note's `## Formulas` section** — a term embedding `![[X]]` there is
> always embedding the formula. So the safe tool does exactly two things:
> (a) rename files, (b) fix `## Formulas`-section transclusions. Everything else
> is flagged for manual review against the known collision list.

```python
import os, re, glob

# 1. rename flat formula files -> 'f- ' prefixed (idempotent)
for f in glob.glob('Formulas/*.md'):
    b = os.path.basename(f)
    if not b.startswith('f- '):
        os.rename(f, os.path.join('Formulas', 'f- ' + b))
formula_names = {os.path.basename(p)[3:-3] for p in glob.glob('Formulas/f- *.md')}

# 2. SAFE rewrite: ONLY transclusions inside a term note's '## Formulas' section.
#    (A term embedding ![[X]] under '## Formulas' is unambiguously the formula X.)
changed = 0
for path in glob.glob('Terms/*.md'):
    lines = open(path, encoding='utf-8').read().split('\n')
    out, in_formulas = [], False
    for ln in lines:
        if ln.startswith('## '):
            in_formulas = ln.strip().lower() == '## formulas'
        if in_formulas and ln.lstrip().startswith('![[') and '[[f- ' not in ln:
            ln = re.sub(r'!\[\[(?!f- )([^\]]+)\]\]',
                        lambda m: (f'![[f- {m.group(1)}]]'
                                   if m.group(1).split("|")[0].split("#")[0].strip()
                                      in formula_names else m.group(0)), ln)
        out.append(ln)
    new = '\n'.join(out)
    if new != open(path, encoding='utf-8').read():
        open(path, 'w', encoding='utf-8').write(new); changed += 1
print("safe transclusion fixes (0 on a correctly-built vault):", changed)

# 3. Flag everything else for MANUAL review — do not auto-edit these.
flag = []
for path in glob.glob('**/*.md', recursive=True):
    for m in re.finditer(r'(!?)\[\[(?!f- )([^\]]+)\]\]', open(path, encoding='utf-8').read()):
        n = m.group(2).split('|')[0].split('#')[0].strip()
        if n in formula_names:
            flag.append((os.path.basename(path), m.group(0)))
print(f"\n{len(flag)} bare links match a formula name — REVIEW BY HAND against")
print("your known collision list (most are the legit same-named TERM):")
from collections import Counter
for tgt, c in Counter(t for _, t in flag).most_common(15):
    print(f"  {c:3}x  {tgt}")
print("\nNow run verify.py and diff before committing.")
```
```

---

## 2. `embed_gifs` — insert animations into `## Visual` (idempotent)

`MAP` = list of `(note_basename, gif_basename_without_ext, caption)`. Inserts
`**Animated:** …` + `![[gif.gif]]` right after the `## Visual\n` heading, only
if that note's Visual section has no `anim_` yet. Reuse one gif for many notes.

```python
import os, re
MAP = [
    ("Gradient Descent", "anim_gradient_descent", "Ball stepping downhill on the cost curve."),
    ("Momentum",         "anim_momentum_vs_sgd",  "SGD zig-zags; momentum glides through the ravine."),
    # ... one row per note; reuse a gif across related notes freely
]
done = skipped = miss = 0
for name, gif, cap in MAP:
    p = f"Terms/{name}.md"
    if not os.path.exists(p): print("MISS NOTE:", name); miss += 1; continue
    s = open(p, encoding='utf-8').read()
    seg = s.split('## Visual')[1].split('## Related')[0] if '## Visual' in s else ""
    if 'anim_' in seg: skipped += 1; continue
    if not os.path.exists(f"Assets/{gif}.gif"): print("MISS GIF:", gif); miss += 1; continue
    m = re.search(r'(## Visual\n)', s)
    if not m: print("NO VISUAL:", name); miss += 1; continue
    block = f"\n**Animated:** {cap}\n\n![[{gif}.gif]]\n"
    s = s[:m.end()] + block + s[m.end():]
    open(p, 'w', encoding='utf-8').write(s); done += 1
print(f"embedded {done} | already-had {skipped} | problems {miss}")
```

---

## 3. `build_indexes` — generate Home + 3 indexes from real files

Reads each note's `lecture:` frontmatter to group by lecture in course order.
`All Formulas` is the "big formula note" (transcludes every formula).

```python
import os, re, glob

ORDER = ['L1','L2','R1','L3','L4','L5A','L5B','L6','R2']   # edit per course
TITLES = {  # edit per course: lecture-id -> exact Lectures/ basename
 'L1':'L1 - Introduction','L2':'L2 - Shallow Regression','R1':'R1 - Probability',
 'L3':'L3 - Shallow Classification','L4':'L4 - MLP and Backpropagation',
 'L5A':'L5A - Training and Optimization I','L5B':'L5B - Training and Optimization II',
 'L6':'L6 - Convolutional Networks','R2':'R2 - Regression Workshop'}

def lec_of(path):
    s = open(path, encoding='utf-8').read()
    m = re.search(r'^lecture:\s*(.+)$', s, re.M)
    if not m: return ['?']
    return [x.strip() for x in m.group(1).strip('[] ').split(',') if x.strip()] or ['?']

def group(folder):
    g = {k: [] for k in ORDER}; g['?'] = []
    for p in glob.glob(f'{folder}/*.md'):
        n = os.path.basename(p)[:-3]
        for L in lec_of(p): (g.get(L, g['?'])).append(n)
    return g

terms = sorted(os.path.basename(p)[:-3] for p in glob.glob('Terms/*.md'))
formulas = sorted(os.path.basename(p)[:-3] for p in glob.glob('Formulas/*.md'))
tg, fg = group('Terms'), group('Formulas')
os.makedirs('Indexes', exist_ok=True)

with open('Indexes/All Terms.md','w',encoding='utf-8') as f:
    f.write(f"---\ntype: index\ntags: [index]\n---\n# All Terms\n\n**{len(terms)} term notes**, grouped by lecture.\n\n")
    for L in ORDER:
        it = sorted(set(tg[L]))
        if it: f.write(f"## [[{TITLES[L]}]]\n\n" + " · ".join(f"[[{t}]]" for t in it) + "\n\n")

with open('Indexes/All Formulas.md','w',encoding='utf-8') as f:
    f.write(f"---\ntype: index\ntags: [index, formula]\n---\n# All Formulas\n\nMaster reference: **{len(formulas)}** notes; every symbol explained.\n\n")
    for L in ORDER:
        it = sorted(set(fg[L]))
        if it:
            f.write(f"## [[{TITLES[L]}]]\n\n")
            for n in it: f.write(f"### [[{n}]]\n![[{n}]]\n\n")

with open('Indexes/All Lectures.md','w',encoding='utf-8') as f:
    f.write("---\ntype: index\ntags: [index]\n---\n# All Lectures & Recitations\n\n")
    for L in ORDER: f.write(f"1. [[{TITLES[L]}]]\n")

with open('Home.md','w',encoding='utf-8') as f:
    f.write("---\ntype: moc\ntags: [moc, home]\n---\n# Course Vault\n\n"
            "Atomic, interlinked notes: **term** (formal+simple+why), **formula** "
            "(every symbol), **lecture/recitation** (narrative flow).\n\n"
            "## Indexes\n- [[All Lectures]]\n- [[All Terms]]\n- [[All Formulas]]\n\n"
            "## Lectures\n" + "".join(f"- [[{TITLES[L]}]]\n" for L in ORDER) +
            "\n## How to use\nStart at a lecture; click any [[term]] to drill in. "
            "Term notes embed their [[f- formula]] inline. Open Reading mode for "
            "math/diagrams/GIFs; open Graph view for the concept web.\n")
print("indexes + Home written")
```

---

## 4. Quick scans (broken targets / orphans / coverage)

```python
import os, re, glob
notes = {os.path.basename(p)[:-3] for p in
         glob.glob('Terms/*.md')+glob.glob('Formulas/*.md')+
         glob.glob('Lectures/*.md')+glob.glob('Indexes/*.md')} | {'Home'}
gifs = set(os.listdir('Assets')) if os.path.isdir('Assets') else set()
brk = set(); badgif = set(); linked = set()
for p in glob.glob('**/*.md', recursive=True):
    s = re.sub(r'```.*?```', '', open(p, encoding='utf-8').read(), flags=re.S)
    for m in re.finditer(r'!?\[\[([^\]]+)\]\]', s):
        t = m.group(1).split('|')[0].split('#')[0].strip(); linked.add(t)
        if t.endswith('.gif'):
            if t not in gifs: badgif.add(t)
        elif t not in notes: brk.add(t)
orphans = [os.path.basename(p)[:-3] for p in glob.glob('Terms/*.md')+glob.glob('Formulas/*.md')
           if os.path.basename(p)[:-3] not in linked]
no_visual = [os.path.basename(p) for p in glob.glob('Terms/*.md')
             if '## Visual' not in open(p, encoding='utf-8').read()]
print("broken links :", sorted(brk) or "NONE")
print("broken gifs  :", sorted(badgif) or "NONE")
print("orphans      :", len(orphans), orphans[:10])
print("no ## Visual :", len(no_visual), no_visual[:10])
```

Note: literal `Term`/`Formula` (template prose) and forward-links to
not-yet-created lecture notes are expected mid-build; resolve by the end.

---

## 5. `embed_per_term` — embed the 1:1 per-term GIF (idempotent)

For the per-term generator (`assets/per_term_generator.py`): every
`Terms/<Name>.md` gets its own `Assets/anim_<slug>.gif`. The slug rule MUST be
byte-identical to the generator's. Animation goes at the TOP of `## Visual`,
static diagram stays below. Won't double-embed.

```python
import os, re, glob
def slug(name): return "anim_"+"".join(c if c.isalnum() else "_" for c in name).strip("_").lower()
done=skip=miss=0
for p in glob.glob('Terms/*.md'):
    name=os.path.splitext(os.path.basename(p))[0]
    gif=slug(name)+".gif"
    if not os.path.exists(os.path.join("Assets",gif)): miss+=1; print("MISS GIF",name); continue
    s=open(p,encoding='utf-8').read()
    seg = s.split('## Visual')[1].split('## Related')[0] if '## Visual' in s else ""
    if 'anim_' in seg: skip+=1; continue
    m=re.search(r'(## Visual\n)', s)
    if not m: miss+=1; print("NO VISUAL HDR",name); continue
    block=f"\n**Animated:** {name} — concept-specific animation (intuition); exact mechanics in the static diagram below.\n\n![[{gif}]]\n"
    s=s[:m.end()]+block+s[m.end():]
    open(p,'w',encoding='utf-8').write(s); done+=1
print(f"embedded {done} | already-had {skip} | problems {miss}")
```

---

## 6. `link_bold_terms` — inline-link bold key-terms in lecture notes

Strictly additive. Links the FIRST bold span per note whose exact text (trailing
`.:,;)` and leading `(` stripped) matches a Term basename or alias, as
`**[[Canonical|readable phrase]]**`. Exact-bold-match ONLY (no generic-word
corruption). Protects frontmatter, fences, inline code, existing links,
headings, and the footer link lines. Formulas excluded (transcluded, collide).

```python
import os, re, glob
names={}
for p in glob.glob('Terms/*.md'):
    b=os.path.basename(p)[:-3]; names[b.lower()]=b
    s=open(p,encoding='utf-8').read()
    m=re.search(r'^aliases:\s*\[(.*?)\]', s, re.M)
    if m:
        for a in m.group(1).split(','):
            a=a.strip().strip('"\'')
            if a and len(a)>2: names.setdefault(a.lower(), b)
tot=0
for path in sorted(glob.glob('Lectures/*.md')):
    raw=open(path,encoding='utf-8').read(); fm=''
    if raw.startswith('---'):
        e=raw.index('\n---',3)+4; fm,raw=raw[:e],raw[e:]
    tok=[]
    def stash(m): tok.append(m.group(0)); return f'\x00{len(tok)-1}\x00'
    raw=re.sub(r'```.*?```',stash,raw,flags=re.S)
    raw=re.sub(r'`[^`\n]*`',stash,raw)
    raw=re.sub(r'!?\[\[[^\]]+\]\]',stash,raw)
    used=set(); cnt=[0]
    def repl(m):
        inner=m.group(1)
        core=inner.rstrip(' .:,;)').lstrip('(')
        canon=names.get(core.lower())
        if canon and canon not in used:
            used.add(canon); cnt[0]+=1
            lead=inner[:len(inner)-len(inner.lstrip('('))]
            trail=inner[len(inner.rstrip(' .:,;)')):]
            link=f'[[{canon}]]' if core==canon else f'[[{canon}|{core}]]'
            return f'**{lead}{link}{trail}**'
        return m.group(0)
    raw=re.sub(r'\*\*([A-Za-z][^*\n]{1,48})\*\*', repl, raw)
    raw=re.sub(r'\x00(\d+)\x00', lambda m: tok[int(m.group(1))], raw)
    open(path,'w',encoding='utf-8').write(fm+raw); tot+=cnt[0]
    print(f"{os.path.basename(path)[:34]:34} +{cnt[0]}")
print("total inline links:", tot)
```
Run `verify.py` after — must stay PROBLEMS 0.

