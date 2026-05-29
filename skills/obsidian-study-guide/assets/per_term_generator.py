#!/usr/bin/env python3
"""
Per-term GIF generator: one animated diagram per term note (1:1 file coverage).

Each term gets ONE GIF whose ANIMATION SHAPE comes from a base template chosen
by `template_for(term)` (routing by concept shape — see that function), and whose
LABELS/colors are parameterised from the term itself (name + the note's bold
key-phrases via note_params()/labels() + a name-seeded rng).

Honest scope: this gives a *relevant, varied* GIF per term, NOT a unique
animation per term. Terms routed to the same template share one motif
(re-labelled); a typical vault yields ~15-20 distinct shapes across all terms.
Routing is keyword-based, not comprehension — for concepts whose true mechanic no
template captures, hand-author a subject generator that overwrites those slugs
(see example_subject_generator.py). Verify perceptual quality after a run: check
the spread of file SIZES (near-equal tiny ones = a degenerate template) and read
back a sample as images, ideally via a cheap vision sub-agent.

  python3 _generate.py                 # all missing (idempotent)
  python3 _generate.py --force
  python3 _generate.py --only "Softmax" "HNSW"
  python3 _generate.py --batch 0 8     # shard i of n (for parallel runs)

matplotlib Agg + PillowWriter -> .gif, no ffmpeg. Dark theme, looping.
"""
import os, sys, re, glob, hashlib, warnings, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

warnings.filterwarnings("ignore")
OUT = os.path.dirname(os.path.abspath(__file__))
TERMS = os.path.join(os.path.dirname(OUT), "Terms")
plt.rcParams.update({
    "figure.facecolor": "#1e1e1e", "axes.facecolor": "#1e1e1e",
    "savefig.facecolor": "#1e1e1e", "text.color": "#e6e6e6",
    "axes.labelcolor": "#cfcfcf", "xtick.color": "#9a9a9a",
    "ytick.color": "#9a9a9a", "axes.edgecolor": "#555",
    "font.size": 10, "axes.titlecolor": "#e6e6e6", "axes.titlesize": 11,
})
PAL = ["#4fc3f7", "#66bb6a", "#ffa726", "#ef5350", "#ab47bc",
       "#26c6da", "#d4e157", "#ec407a", "#8d6e63", "#7e94ff"]
FPS = 12


def slug(name):
    return "anim_" + "".join(c if c.isalnum() else "_" for c in name).strip("_").lower()


def seed_of(name):
    return int(hashlib.md5(name.encode()).hexdigest(), 16) % (2 ** 31)


def wrap(s, n=30):
    return "\n".join(textwrap.wrap(str(s), n)) or str(s)


def save(anim, name, fps=FPS):
    anim.save(os.path.join(OUT, slug(name) + ".gif"), writer=PillowWriter(fps=fps))
    plt.close("all")


def note_params(term):
    """Pull bold key-phrases + tag from the note for label parameterisation."""
    p = os.path.join(TERMS, term + ".md")
    bolds, tag = [], ""
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        m = re.search(r"^tags:\s*\[(.*?)\]", s, re.M)
        if m:
            parts = [x.strip() for x in m.group(1).split(",") if x.strip() != "term"]
            tag = parts[0] if parts else ""
        # Only pull from Formal definition and Why we need it sections
        # (avoids Analogy callout, tip header words, and related links)
        body = ""
        for section in ("## Formal definition", "## Why we need it"):
            start = s.find(section)
            if start != -1:
                end = s.find("\n## ", start + 5)
                chunk = s[start:end if end != -1 else start + 2000]
                # Strip callout lines (> [!...) and link-only lines
                for line in chunk.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("> [!") or stripped.startswith("> **Analogy"):
                        continue
                    body += line + "\n"
        for b in re.findall(r"\*\*([A-Za-z][^*\n]{2,34})\*\*", body):
            b = b.rstrip(" .:,;").strip()
            if 2 < len(b) < 32 and b.lower() not in (x.lower() for x in bolds):
                bolds.append(b)
    return {"bolds": bolds, "tag": tag}


_PAD = ["input", "output", "score", "token", "embed", "query", "key", "value",
        "chunk", "doc", "layer", "gate", "route", "rank", "vec", "pool"]


def words(term, n=3):
    """Split term into constituent words; use semantic pads if too short."""
    w = [x for x in re.split(r"[ \-/@()]+", term) if len(x) > 1]
    # also add camelCase splits
    extra = []
    for part in w:
        subs = re.findall(r"[A-Z][a-z]+|[a-z]+|[A-Z]+(?=[A-Z]|$)", part)
        extra += [s.lower() for s in subs if len(s) > 1]
    combined = w + extra
    # deduplicate preserving order
    seen = set(); out = []
    for x in combined:
        if x.lower() not in seen:
            seen.add(x.lower()); out.append(x)
    out += _PAD
    while len(out) < n:
        out += _PAD
    return out[:n]


def labels(P, term, n):
    """Always return exactly n non-empty labels (bold phrases, then term words, then pad)."""
    out = list(P["bolds"]) + words(term, max(n, 4))
    out += _PAD
    # deduplicate
    seen = set(); deduped = []
    for x in out:
        if x.lower() not in seen:
            seen.add(x.lower()); deduped.append(x)
    while len(deduped) < n:
        deduped += _PAD
    return deduped[:n]


# =====================================================================
#  CONCEPT-FAITHFUL BASE TEMPLATES. Each reads term-specific labels so
#  no two outputs look the same; the template depicts the real mechanic.
# =====================================================================

def t_softmax(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    k = 4 + rng.randint(4)
    logits = rng.uniform(0.5, 3.5, k)
    lbls = labels(P, term, k)
    bars = ax.bar(range(k), np.ones(k) / k, color=[PAL[i % len(PAL)] for i in range(k)])
    ax.set_xticks(range(k)); ax.set_xticklabels([wrap(l, 9) for l in lbls], fontsize=7)
    ax.set_ylim(0, 1); ax.set_ylabel("probability"); ax.set_title(wrap(term, 34))

    def upd(i):
        T = 2.2 - 2.0 * i / 34
        p = np.exp(logits / max(T, .15)); p /= p.sum()
        for b, h in zip(bars, p): b.set_height(h)
        ax.set_xlabel(f"temperature = {max(T,.15):.2f}")
        return bars
    save(FuncAnimation(fig, upd, frames=36, blit=False), term)


def t_curve_descent(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    a = 0.5 + rng.rand(); sh = (rng.rand() - .5) * 1.5
    xs = np.linspace(-3, 3, 200)
    ax.plot(xs, a * (xs - sh) ** 2 + 0.4, color=PAL[seed_of(term) % len(PAL)], lw=2)
    pt, = ax.plot([], [], "o", color="#ff7043", ms=13)
    tr, = ax.plot([], [], "-", color="#ff7043", lw=1, alpha=.5)
    ax.set_title(wrap(term, 34)); ax.set_xlabel("parameter"); ax.set_ylabel("loss")
    x = [(-1) ** rng.randint(2) * (2.3 + rng.rand())]; X = []; Y = []

    def upd(i):
        X.append(x[0]); Y.append(a * (x[0] - sh) ** 2 + 0.4)
        pt.set_data([x[0]], [Y[-1]]); tr.set_data(X, Y)
        x[0] -= (0.10 + 0.05 * rng.rand()) * (2 * a * (x[0] - sh))
        return pt, tr
    save(FuncAnimation(fig, upd, frames=42, blit=True), term)


def t_trend(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    x = np.linspace(0, 1, 60); kind = rng.randint(4)
    if kind == 0: y = 1 - (1 - x) ** (2 + rng.randint(4))
    elif kind == 1: y = 1 / (1 + np.exp(-(x - .5) * (7 + rng.rand() * 8)))
    elif kind == 2: y = x ** (.35 + rng.rand())
    else: y = 1 - np.exp(-x * (2 + rng.rand() * 4))
    c = PAL[seed_of(term) % len(PAL)]
    ln, = ax.plot([], [], color=c, lw=2.6)
    fillpt, = ax.plot([], [], "o", color=c, ms=8)
    ax.set_xlim(0, 1); ax.set_ylim(-.04, 1.05)
    ax.set_title(wrap(term, 34))
    ax.set_xlabel((P["bolds"][0][:22] if P["bolds"] else "k / steps"))
    ax.set_ylabel("score")

    def upd(i):
        n = int(len(x) * (i + 1) / 40)
        ln.set_data(x[:n], y[:n])
        if n: fillpt.set_data([x[n - 1]], [y[n - 1]])
        return ln, fillpt
    save(FuncAnimation(fig, upd, frames=40, blit=True), term)


def t_pipeline(term, rng, P):
    tw = [x for x in re.split(r"[ \-/]+", term) if len(x) > 1]
    src = labels(P, term, 5)
    stages = [wrap(s, 12) for s in src][:5]
    n = len(stages)
    fig, ax = plt.subplots(figsize=(2.0 + 1.7 * n, 2.4))

    def upd(k):
        ax.clear(); ax.axis("off")
        ax.set_xlim(0, n * 2.0 + .4); ax.set_ylim(0, 2)
        ax.set_title(wrap(term, 40))
        for i, s in enumerate(stages[:k + 1]):
            ax.add_patch(FancyBboxPatch((i * 2.0 + .15, .45), 1.65, 1.1,
                         boxstyle="round,pad=0.04",
                         fc=PAL[i % len(PAL)], ec="#111"))
            ax.text(i * 2.0 + .975, 1.0, s, ha="center", va="center",
                    fontsize=7.5, color="#111", weight="bold")
            if i:
                ax.annotate("", (i * 2.0 + .15, 1.0), (i * 2.0 - .35, 1.0),
                            arrowprops=dict(arrowstyle="-|>", color="#bbb", lw=2))
        return []
    save(FuncAnimation(fig, upd, frames=n, blit=False), term, fps=1)


def t_loop(term, rng, P):
    src = P["bolds"][:4]
    nodes = [wrap(s, 11) for s in (src if len(src) >= 3 else
             ["Think", "Act", "Observe", "Decide"])][:4]
    m = len(nodes)
    fig, ax = plt.subplots(figsize=(3.6, 3.4))
    ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.6)
    ax.axis("off"); ax.set_title(wrap(term, 30))
    ang = np.linspace(90, 450, m, endpoint=False) * np.pi / 180
    pos = np.c_[np.cos(ang), np.sin(ang)]
    for i in range(m):
        j = (i + 1) % m
        ax.annotate("", pos[j] * .82, pos[i] * .82,
                    arrowprops=dict(arrowstyle="-|>", color="#777",
                                    connectionstyle="arc3,rad=0.25", lw=1.6))
    for i, (x, y) in enumerate(pos):
        ax.add_patch(Circle((x, y), .34, fc=PAL[i % len(PAL)], ec="#111"))
        ax.text(x, y, nodes[i], ha="center", va="center", fontsize=7.5,
                color="#111", weight="bold")
    tok, = ax.plot([], [], "o", color="#fff", ms=12)

    def upd(f):
        seg = (f // 8) % m; t = (f % 8) / 8
        a, b = pos[seg], pos[(seg + 1) % m]
        tok.set_data([a[0] * (1 - t) + b[0] * t], [a[1] * (1 - t) + b[1] * t])
        return tok,
    save(FuncAnimation(fig, upd, frames=8 * m * 2, blit=True), term)


def t_vectors(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.4, 3.4))
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(wrap(term, 34))
    k = 5 + rng.randint(4)
    base = (rng.rand(k, 2) - .5) * 1.9
    targ = base + (rng.rand(k, 2) - .5) * .55
    lbl = labels(P, term, k)
    cols = [PAL[i % len(PAL)] for i in range(k)]
    sc = ax.scatter(*base.T, c=cols, s=120, zorder=3)
    txt = [ax.text(*base[i], wrap(lbl[i], 8), fontsize=6, color="#ddd") for i in range(k)]
    arr = FancyArrowPatch((0, 0), (0, 0), color="#fff", lw=2,
                          arrowstyle="-|>", mutation_scale=14)
    ax.add_patch(arr)

    def upd(i):
        t = i / 29; pp = base * (1 - t) + targ * t
        sc.set_offsets(pp)
        for j in range(k): txt[j].set_position(pp[j])
        arr.set_positions(tuple(pp[0]), tuple(pp[1]))
        return sc,
    save(FuncAnimation(fig, upd, frames=30, blit=False), term)


def t_cosine(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.0, 3.4))
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(wrap(term, 30))
    a = np.array([1, 0.15]); a = a / np.linalg.norm(a)
    A = FancyArrowPatch((0, 0), tuple(a), color=PAL[0], lw=3,
                        arrowstyle="-|>", mutation_scale=18)
    B = FancyArrowPatch((0, 0), (1, 0), color=PAL[2], lw=3,
                        arrowstyle="-|>", mutation_scale=18)
    ax.add_patch(A); ax.add_patch(B)
    cap = ax.text(0, -1.05, "", ha="center", fontsize=9, color="#ddd")
    th0 = rng.uniform(.3, 2.6)

    def upd(i):
        th = th0 * (1 - i / 33) + .05
        b = np.array([np.cos(th), np.sin(th)])
        B.set_positions((0, 0), tuple(b))
        cap.set_text(f"cos = {np.dot(a, b):.2f}")
        return A, B
    save(FuncAnimation(fig, upd, frames=34, blit=False), term)


def t_analogy(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    ax.set_xlim(-.3, 3.3); ax.set_ylim(-.3, 2.3)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(wrap(term, 32))
    wlab = (P["bolds"] + words(term, 4) + ["king", "man", "woman", "queen"])
    A, Bv, C, D = [(.4, .5), (.4, 1.6), (2.0, .5), (2.0, 1.6)]
    for (x, y), nm, c in zip([A, Bv, C, D], wlab, PAL):
        ax.add_patch(Circle((x, y), .12, color=c))
        ax.text(x, y + .2, wrap(nm, 10), ha="center", fontsize=7, color="#ddd")
    seq = [(A, Bv, "#4fc3f7"), (Bv, D, "#66bb6a"), (C, D, "#ffa726")]

    def upd(i):
        k = i // 12
        if i % 12 == 0:
            for (p, q, c) in seq[:k]:
                ax.annotate("", q, p, arrowprops=dict(arrowstyle="-|>",
                            color=c, lw=2))
        return []
    save(FuncAnimation(fig, upd, frames=38, blit=False), term, fps=6)


def t_graphwalk(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.4, 3.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title(wrap(term, 32))
    k = 12 + rng.randint(8)
    pts = rng.rand(k, 2)
    for i in range(k):
        d = np.argsort(((pts - pts[i]) ** 2).sum(1))[1:4]
        for j in d:
            ax.plot(*zip(pts[i], pts[j]), color="#3a3a3a", lw=.7, zorder=1)
    ax.scatter(*pts.T, c="#555", s=40, zorder=2)
    tgt = k - 1
    ax.scatter(*pts[tgt], c="#ef5350", s=160, marker="*", zorder=4)
    path = [0]
    for _ in range(8):
        cur = path[-1]
        nb = np.argsort(((pts - pts[cur]) ** 2).sum(1))
        nxt = next((n for n in nb if n not in path and
                    ((pts[n] - pts[tgt]) ** 2).sum() <
                    ((pts[cur] - pts[tgt]) ** 2).sum()), None)
        if nxt is None: break
        path.append(nxt)
        if nxt == tgt: break
    dot, = ax.plot([], [], "o", color="#4fc3f7", ms=14, zorder=5)
    ln, = ax.plot([], [], "-", color="#4fc3f7", lw=2, zorder=3)

    def upd(i):
        s = min(i // 4, len(path) - 1)
        pp = pts[path[:s + 1]]
        ln.set_data(*pp.T); dot.set_data([pts[path[s]][0]], [pts[path[s]][1]])
        return dot, ln
    save(FuncAnimation(fig, upd, frames=4 * len(path) + 6, blit=True), term)


def t_chunking(term, rng, P):
    fig, ax = plt.subplots(figsize=(5.0, 2.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis("off")
    ax.set_title(wrap(term, 38))
    ax.add_patch(FancyBboxPatch((0, 1.9), 10, .8, boxstyle="round,pad=0.02",
                 fc="#333", ec="#666"))
    ax.text(5, 2.3, "document", ha="center", fontsize=8, color="#bbb")
    nC = 5; w = 2.6; step = (10 - w) / (nC - 1)
    # Draw first chunk immediately so frame 0 is not blank
    r0 = FancyBboxPatch((0, .3), w, 1.0, boxstyle="round,pad=0.02",
                        fc=PAL[0], ec="#111", alpha=.85)
    ax.add_patch(r0)
    ax.text(w / 2, .8, "chunk 1", ha="center", fontsize=7, color="#111", weight="bold")
    rects = [r0]

    def upd(i):
        k = i // 6 + 1  # chunk 2 onward
        if i % 6 == 0 and k < nC:
            r = FancyBboxPatch((k * step, .3), w, 1.0,
                               boxstyle="round,pad=0.02",
                               fc=PAL[k % len(PAL)], ec="#111", alpha=.85)
            ax.add_patch(r); rects.append(r)
            ax.text(k * step + w / 2, .8, f"chunk {k+1}", ha="center",
                    fontsize=7, color="#111", weight="bold")
        return rects
    save(FuncAnimation(fig, upd, frames=6 * (nC - 1) + 4, blit=False), term, fps=6)


def t_slidewin(term, rng, P):
    toks = labels(P, term, 8)
    fig, ax = plt.subplots(figsize=(5.2, 2.0))
    ax.set_xlim(-.2, 8.2); ax.set_ylim(0, 2); ax.axis("off")
    ax.set_title(wrap(term, 40))
    for i, tk in enumerate(toks):
        ax.add_patch(FancyBboxPatch((i + .05, .5), .9, .9,
                     boxstyle="round,pad=0.03", fc="#333", ec="#666"))
        ax.text(i + .5, .95, wrap(str(tk), 6), ha="center", va="center",
                fontsize=7, color="#ccc")
    box = FancyBboxPatch((-.05, .42), 2.1, 1.06, boxstyle="round,pad=0.03",
                         fill=False, ec="#ffa726", lw=2.5)
    ax.add_patch(box)

    def upd(i):
        box.set_x((i % (len(toks) - 1)) - .05)
        return box,
    save(FuncAnimation(fig, upd, frames=(len(toks) - 1) * 4, blit=True), term, fps=5)


def t_matrix(term, rng, P):
    fig, ax = plt.subplots(figsize=(3.6, 3.4))
    ax.set_xlim(0, 2); ax.set_ylim(0, 2); ax.axis("off")
    ax.set_title(wrap(term, 30))
    cells = [(0, 1, "TP", "#66bb6a"), (1, 1, "FP", "#ef5350"),
             (0, 0, "FN", "#ffa726"), (1, 0, "TN", "#4fc3f7")]
    order = list(range(4)); rng.shuffle(order)

    def upd(i):
        k = i // 7
        if i % 7 == 0 and k < 4:
            x, y, lab, c = cells[order[k]]
            ax.add_patch(FancyBboxPatch((x + .05, y + .05), .9, .9,
                         boxstyle="round,pad=0.02", fc=c, ec="#111"))
            ax.text(x + .5, y + .5, lab, ha="center", va="center",
                    fontsize=13, color="#111", weight="bold")
        return []
    save(FuncAnimation(fig, upd, frames=7 * 4 + 4, blit=False), term, fps=6)


def t_vote(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    k = 4
    cand = [wrap(c, 10) for c in (P["bolds"] + words(term, k) + list("ABCD"))][:k]
    win = rng.randint(k)

    def upd(i):
        ax.clear(); ax.axis("off"); ax.set_xlim(0, 6); ax.set_ylim(0, 5)
        ax.set_title(wrap(term, 34))
        for j in range(k):
            on = i > j * 5
            ax.add_patch(FancyBboxPatch((.3, 4 - j * 1.05), 2.0, .85,
                         boxstyle="round,pad=0.03",
                         fc=PAL[j % len(PAL)] if on else "#333", ec="#111"))
            if on:
                ax.text(1.3, 4.42 - j * 1.05, cand[j], ha="center",
                        va="center", fontsize=7, color="#111")
        if i > k * 5 + 2:
            ax.add_patch(FancyBboxPatch((3.6, 1.8), 2.0, 1.2,
                         boxstyle="round,pad=0.04", fc="#ffca28", ec="#111"))
            ax.text(4.6, 2.4, "WINNER\n" + cand[win], ha="center",
                    va="center", fontsize=8, color="#111", weight="bold")
            ax.annotate("", (3.6, 2.4), (2.4, 2.4),
                        arrowprops=dict(arrowstyle="-|>", color="#bbb", lw=2))
        return []
    save(FuncAnimation(fig, upd, frames=k * 5 + 12, blit=False), term, fps=6)


def t_debate(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    ax.set_xlim(0, 6); ax.set_ylim(0, 5); ax.axis("off")
    ax.set_title(wrap(term, 34))
    for x, lab, c in [(0.9, "Agent A", "#4fc3f7"), (5.1, "Agent B", "#ef5350")]:
        ax.add_patch(Circle((x, 4), .42, fc=c, ec="#111"))
        ax.text(x, 4, lab, ha="center", va="center", fontsize=7,
                color="#111", weight="bold")
    ax.add_patch(FancyBboxPatch((2.1, .3), 1.8, .9, boxstyle="round,pad=0.04",
                 fc="#ffca28", ec="#111"))
    ax.text(3.0, .75, "Judge", ha="center", va="center", fontsize=8,
            color="#111", weight="bold")
    msg, = ax.plot([], [], "o", color="#fff", ms=11)

    def upd(i):
        r = (i // 10) % 2; t = (i % 10) / 10
        a, b = ((0.9, 4), (5.1, 4)) if r == 0 else ((5.1, 4), (0.9, 4))
        if i < 40:
            msg.set_data([a[0] * (1 - t) + b[0] * t], [4])
        else:
            msg.set_data([3.0], [4 - (i - 40) / 10 * 2.7])
        return msg,
    save(FuncAnimation(fig, upd, frames=56, blit=True), term)


def t_toolcall(term, rng, P):
    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    ax.set_xlim(0, 6); ax.set_ylim(0, 3); ax.axis("off")
    ax.set_title(wrap(term, 38))
    for x, lab, c in [(0.3, "LLM", "#4fc3f7"), (2.3, "Tool\nschema", "#ab47bc"),
                      (4.3, "Execute", "#66bb6a")]:
        ax.add_patch(FancyBboxPatch((x, 1.0), 1.4, 1.0,
                     boxstyle="round,pad=0.04", fc=c, ec="#111"))
        ax.text(x + .7, 1.5, lab, ha="center", va="center", fontsize=8,
                color="#111", weight="bold")
    tok, = ax.plot([], [], "o", color="#fff", ms=12)
    xs = [1.0, 2.3, 3.7, 5.0]

    def upd(i):
        f = i % 48
        if f < 32:
            seg = f // 11; t = (f % 11) / 11
            a, b = xs[seg], xs[seg + 1]
            tok.set_data([a * (1 - t) + b * t], [1.5])
        else:
            t = (f - 32) / 16
            tok.set_data([5.0 * (1 - t) + 1.0 * t], [0.5])
        return tok,
    save(FuncAnimation(fig, upd, frames=48, blit=True), term)


def t_memory(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    ax.set_xlim(0, 6); ax.set_ylim(0, 4); ax.axis("off")
    ax.set_title(wrap(term, 34))
    ax.add_patch(FancyBboxPatch((2.1, .4), 1.8, 3.0, boxstyle="round,pad=0.05",
                 fc="#2c2c2c", ec="#888"))
    ax.text(3.0, 3.6, "memory", ha="center", fontsize=8, color="#bbb")
    items = labels(P, term, 5)

    def upd(i):
        k = i // 9
        if i % 9 == 0 and k < len(items):
            y = .7 + k * .55
            ax.add_patch(FancyBboxPatch((2.25, y), 1.5, .42,
                         boxstyle="round,pad=0.02",
                         fc=PAL[k % len(PAL)], ec="#111"))
            ax.text(3.0, y + .21, wrap(items[k], 12), ha="center",
                    va="center", fontsize=6.5, color="#111")
        return []
    save(FuncAnimation(fig, upd, frames=9 * len(items) + 4, blit=False), term, fps=6)


def t_tree(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)]
    coord = {0: (4, 4.3), 1: (2, 2.7), 2: (6, 2.7),
             3: (1, 1.1), 4: (3, 1.1), 5: (6, 1.1)}
    lbl = labels(P, term, 6)
    # Draw full tree statically; animate a traversal dot on top
    ax.axis("off"); ax.set_xlim(0, 8); ax.set_ylim(0, 5)
    ax.set_title(wrap(term, 34))
    for (a, b) in edges:
        ax.plot(*zip(coord[a], coord[b]), color="#555", lw=1.4)
    for nidx in range(6):
        x, y = coord[nidx]
        ax.add_patch(Circle((x, y), .42, fc=PAL[nidx % len(PAL)], ec="#111"))
        ax.text(x, y, wrap(lbl[nidx], 8), ha="center", va="center",
                fontsize=6.5, color="#111", weight="bold")
    path = [0, 1, 3, 1, 4, 1, 0, 2, 5]
    dot, = ax.plot([coord[0][0]], [coord[0][1]], "o", color="#fff", ms=13, zorder=5)

    def upd(i):
        n = path[i % len(path)]
        dot.set_data([coord[n][0]], [coord[n][1]])
        return dot,
    save(FuncAnimation(fig, upd, frames=len(path) * 4, blit=True), term, fps=4)


def t_layers(term, rng, P):
    src = labels(P, term, 5)
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.set_xlim(0, 5); ax.set_ylim(0, 5.2); ax.axis("off")
    ax.set_title(wrap(term, 34))

    def upd(i):
        k = i // 8
        if i % 8 == 0 and k < len(src):
            ax.add_patch(FancyBboxPatch((.6, .4 + k * .92), 3.8, .8,
                         boxstyle="round,pad=0.03",
                         fc=PAL[k % len(PAL)], ec="#111"))
            ax.text(2.5, .8 + k * .92, wrap(src[k], 22), ha="center",
                    va="center", fontsize=7.5, color="#111", weight="bold")
        return []
    save(FuncAnimation(fig, upd, frames=8 * len(src) + 4, blit=False), term, fps=6)


def t_retrieval(term, rng, P):
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    ax.set_xlim(0, 7); ax.set_ylim(0, 5); ax.axis("off")
    ax.set_title(wrap(term, 36))
    # query box label: first bold phrase or term words
    tw = [x for x in re.split(r"[ \-/]+", term) if len(x) > 1]
    q_label = wrap((P["bolds"][0] if P["bolds"] else tw[0])[:14], 10)
    ax.add_patch(FancyBboxPatch((.2, 2.0), 1.2, 1.0, boxstyle="round,pad=0.04",
                 fc="#4fc3f7", ec="#111"))
    ax.text(.8, 2.5, q_label, ha="center", va="center", fontsize=7, color="#111",
            weight="bold")
    docs = [(3.2, 3.7), (3.2, 2.5), (3.2, 1.3)]
    doc_labels = labels(P, term, 3)
    for (x, y), dlbl in zip(docs, doc_labels):
        ax.add_patch(FancyBboxPatch((x, y - .35), 1.1, .7,
                     boxstyle="round,pad=0.02", fc="#2a2a3a", ec="#666"))
        ax.text(x + .55, y, wrap(str(dlbl)[:14], 10), ha="center", va="center",
                fontsize=6, color="#aaa")
    ax.add_patch(FancyBboxPatch((5.4, 2.0), 1.3, 1.0,
                 boxstyle="round,pad=0.04", fc="#66bb6a", ec="#111"))
    ax.text(6.05, 2.5, "LLM", ha="center", va="center", fontsize=8, color="#111",
            weight="bold")
    sel, = ax.plot([], [], "o", color="#ffca28", ms=13)

    def upd(i):
        f = i % 40
        if f < 24:
            d = f // 8; t = (f % 8) / 8
            sel.set_data([0.8 * (1 - t) + 3.75 * t], [2.5 * (1 - t) + docs[d][1] * t])
        else:
            t = (f - 24) / 16
            sel.set_data([3.75 * (1 - t) + 6.05 * t], [2.5])
        return sel,
    save(FuncAnimation(fig, upd, frames=40, blit=True), term)


def t_router(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    ax.set_xlim(0, 6); ax.set_ylim(0, 5); ax.axis("off")
    ax.set_title(wrap(term, 34))
    ax.add_patch(FancyBboxPatch((.3, 2.0), 1.3, 1.0, boxstyle="round,pad=0.04",
                 fc="#ab47bc", ec="#111"))
    ax.text(.95, 2.5, "router", ha="center", va="center", fontsize=8, color="#111")
    br = labels(P, term, 3)
    ys = [4.0, 2.5, 1.0]
    for y, b in zip(ys, br):
        ax.add_patch(FancyBboxPatch((4.0, y - .4), 1.6, .8,
                     boxstyle="round,pad=0.03", fc="#333", ec="#666"))
        ax.text(4.8, y, wrap(b, 12), ha="center", va="center",
                fontsize=7, color="#ccc")
    tok, = ax.plot([], [], "o", color="#fff", ms=12)

    def upd(i):
        pick = seed_of(term) % 3; f = i % 26
        t = min(f / 22, 1)
        tx = 1.6 * (1 - t) + 4.0 * t
        ty = 2.5 * (1 - t) + ys[pick] * t
        tok.set_data([tx], [ty]); return tok,
    save(FuncAnimation(fig, upd, frames=26, blit=True), term)


def t_bars_compare(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    k = 4
    g1 = rng.uniform(.3, .9, k); g2 = np.clip(g1 + rng.uniform(-.2, .35, k), .05, 1.15)
    lbl = labels(P, term, k)
    x = np.arange(k)
    # Start at 40% so frame 0 is not blank; animate to full height then pulse
    b1 = ax.bar(x - .2, g1 * .4, .38, color="#4fc3f7", label="A")
    b2 = ax.bar(x + .2, g2 * .4, .38, color="#ffa726", label="B")
    ax.set_xticks(x); ax.set_xticklabels([wrap(l, 9) for l in lbl], fontsize=7)
    ax.set_ylim(0, 1.2); ax.set_title(wrap(term, 34))
    ax.legend(fontsize=7, facecolor="#1e1e1e", edgecolor="#555", labelcolor="#ddd")

    def upd(i):
        t = min(.4 + i / 28 * .6, 1)
        for b, h in zip(b1, g1 * t): b.set_height(h)
        for b, h in zip(b2, g2 * t): b.set_height(h)
        return list(b1) + list(b2)
    save(FuncAnimation(fig, upd, frames=32, blit=False), term)


def t_scatter_cluster(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.4, 3.4))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(wrap(term, 32))
    ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4)
    nc = 3; n = 60
    cen = (rng.rand(nc, 2) - .5) * 2
    lab = rng.randint(nc, size=n)
    start = (rng.rand(n, 2) - .5) * 2.4
    end = cen[lab] + (rng.rand(n, 2) - .5) * .5
    cols = np.array(PAL)[lab % len(PAL)]
    sc = ax.scatter(*start.T, c=cols, s=28)

    def upd(i):
        t = min(i / 30, 1)
        sc.set_offsets(start * (1 - t) + end * t)
        return sc,
    save(FuncAnimation(fig, upd, frames=34, blit=False), term)


def t_dist_drift(term, rng, P):
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    x = np.linspace(-4, 4, 200)
    col = PAL[seed_of(term) % len(PAL)]
    ln, = ax.plot([], [], color=col, lw=2.5)
    ax.set_xlim(-4, 4); ax.set_ylim(0, .55); ax.set_title(wrap(term, 34))
    ax.set_xlabel("value"); ax.set_ylabel("density")

    def upd(i):
        mu = -1.5 + 3 * i / 33; sg = .7 + .5 * abs(np.sin(i / 6))
        y = np.exp(-((x - mu) ** 2) / (2 * sg ** 2)) / (sg * 2.5)
        ln.set_data(x, y)
        for c in list(ax.collections): c.remove()
        ax.fill_between(x, 0, y, color=col, alpha=.25)
        return ln,
    save(FuncAnimation(fig, upd, frames=34, blit=False), term)


def t_typewriter(term, rng, P):
    seq = (P["bolds"][:1] or [term]) + words(term, 6)
    toks = (" ".join(seq)).split()[:9] or ["the", "next", "token"]
    fig, ax = plt.subplots(figsize=(5.2, 2.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title(wrap(term, 38))
    # Show first token immediately so frame 0 is not blank
    txt = ax.text(.04, .5, toks[0], fontsize=12, color="#9be7a0",
                  family="monospace", va="center")

    def upd(i):
        k = max(1, min(i // 3 + 1, len(toks)))
        txt.set_text(" ".join(toks[:k]))
        return txt,
    save(FuncAnimation(fig, upd, frames=3 * len(toks) + 6, blit=False), term, fps=5)


def t_gate(term, rng, P):
    fig, ax = plt.subplots(figsize=(5.0, 2.6))
    ax.set_xlim(0, 6); ax.set_ylim(0, 3); ax.axis("off")
    ax.set_title(wrap(term, 38))
    ax.add_patch(FancyBboxPatch((2.4, .8), .5, 1.4, fc="#ef5350", ec="#111"))
    ax.text(2.65, 2.4, "gate", ha="center", fontsize=8, color="#bbb")
    dot, = ax.plot([], [], "o", ms=13)
    blocked = seed_of(term) % 3 == 0

    def upd(i):
        t = (i % 40) / 38
        if blocked:
            dot.set_data([min(0.3 + t * 6, 2.3)], [1.5]); dot.set_color("#ef5350")
        else:
            dot.set_data([0.3 + t * 5.4], [1.5]); dot.set_color("#66bb6a")
        return dot,
    save(FuncAnimation(fig, upd, frames=40, blit=True), term)


def template_for(term):
    """Route a term to a faithful animation template by CONCEPT SHAPE.

    Subject-agnostic by design: the primary layer keys off shape words that any
    discipline uses (sequence/cycle/hierarchy/comparison/distribution/geometry/
    graph/decision). A second layer adds domain-specific keywords (LLM/agents,
    ML/DL, …) for sharper matches. Anything unmatched falls through to a
    SHAPE-BALANCED hash so no single template dominates.

    To tune for a NEW subject: add a few `kw(...)` lines mapping that field's
    vocabulary to the closest shape template, OR (better, for concepts no generic
    template depicts) hand-author a subject generator that overwrites those slugs
    — see assets/_gen_l7.py for a worked CNN example, and the Phase-4 warning.
    """
    t = term.lower()
    kw = lambda *xs: any(x in t for x in xs)

    # ============ LAYER 1 — generic CONCEPT-SHAPE words (subject-agnostic) ======
    # distribution sharpening / probability over options
    if kw("softmax", "logit", "probabilit", "distribution over", "normaliz"):
        return t_softmax
    # sampling / spread / drift of a distribution
    if kw("sampling", "temperature", "variance", "spread", "drift", "noise",
           "stochast", "perturb", "jitter"): return t_dist_drift
    # optimization landscape / minimizing an objective
    if kw("loss", "cost function", "objective", "gradient", "descent", "minim",
           "optimiz", "convex", "fine-tun", "energy", "error surface"):
        return t_curve_descent
    # monotone curve vs a quantity: metrics, scaling, growth/decay, tradeoff-vs-x
    if kw("accuracy", "metric", "score", "scaling", "growth", "decay", "rate",
           "saturat", "diminish", "convergence", "learning curve", "vs depth",
           "vs size", "throughput", "latency", "cost", "pric", "budget",
           "pass@", "f1 vs", "complexity"): return t_trend
    # side-by-side comparison of discrete options
    if kw("compare", "comparison", "versus", " vs ", "ablation", "tradeoff",
           "trade-off", "benchmark", "leaderboard", "baseline", "before and after",
           "a/b", "which is better"): return t_bars_compare
    # 2D confusion/contingency table
    if kw("confusion", "contingency", "true positive", "false positive",
           "true negative", "false negative", "precision", "recall",
           "sensitivity", "specificity", "matrix of"): return t_matrix
    # cycle / iterate-until-converged / feedback
    if kw("loop", "cycle", "iterat", "feedback", "recurren", "repeat until",
           "epoch", "round-trip", "closed loop", "step-act"): return t_loop
    # sequence emitted left-to-right (process, generation, autoregression)
    if kw("sequence", "autoregress", "generat", "step by step", "left to right",
           "unroll", "timeline", "read out", "emit", "decode"): return t_typewriter
    # multi-stage linear pipeline / workflow
    if kw("pipeline", "workflow", "phases", "stage", "ingestion", "end-to-end",
           "process flow", "assembly line"): return t_pipeline
    # a window sliding over a sequence (conv window, attention window, context)
    if kw("sliding", "window", "context window", "stride", "convol", "receptive",
           "n-gram", "scan over", "local window"): return t_slidewin
    # splitting a long thing into overlapping pieces
    if kw("chunk", "overlap", "segment", "tile", "split into", "partition"):
        return t_chunking
    # tree / recursive decomposition / branching search
    if kw("tree", "hierarchy of", "recurs", "decompos", "subgoal", "branch",
           "beam search", "breadth-first", "depth-first", "divide", "taxonomy",
           "parse tree", "decision tree"): return t_tree
    # stacked layers / levels (no branching)
    if kw("layer", "stack", "level", "tier", "hierarch", "depth", "topology",
           "deep network", "block of"): return t_layers
    # graph traversal / nodes-and-edges walk
    if kw("graph", "node", "edge", "traversal", "walk", "shortest path",
           "network of", "adjacency", "digraph", "neighbor", "hop"):
        return t_graphwalk
    # routing / dispatch by a condition
    if kw("rout", "dispatch", "switch", "conditional", "gate to", "selector",
           "branch to", "send to"): return t_router
    # vectors in space / embeddings
    if kw("vector", "embedding", "coordinate", "point in space", "dimension",
           "feature space", "latent space"): return t_vectors
    # angle / similarity between two vectors
    if kw("cosine", "angle between", "dot product", "similarity", "orthogonal",
           "alignment of"): return t_cosine
    # a + b - c style analogy / arithmetic on vectors
    if kw("analogy", "arithmetic", "offset", "a is to b", "king minus",
           "parallelogram"): return t_analogy
    # clusters / classification regions of points
    if kw("cluster", "classif", "knn", "k-means", "region", "decision boundary",
           "scatter", "group of points", "separab"): return t_scatter_cluster
    # voting / aggregating many opinions into one
    if kw("vot", "majority", "plurality", "ensembl", "aggregat", "consensus",
           "self-consistency", "combine", "pool of", "best-of"): return t_vote
    # two parties arguing, a judge deciding
    if kw("debate", "argue", "adversar", "critic vs", "pro and con",
           "proposer", "affirmative", "judge between"): return t_debate
    # storing/recalling from a memory store
    if kw("memory", "store", "recall", "cache", "buffer", "archive",
           "retain", "write-back", "key-value store"): return t_memory
    # retrieval: query -> fetch docs -> use
    if kw("retriev", "search index", "lookup", "query", "fetch", "rag",
           "knn search", "vector database", "semantic search"): return t_retrieval
    # calling a function/tool with arguments
    if kw("function call", "tool call", "tool use", "api call", "invoke",
           "dispatcher", "parameter mapping", "schema fill"): return t_toolcall
    # a guard / filter / accept-or-reject decision
    if kw("gate", "filter", "guard", "threshold", "accept or reject", "block",
           "validate", "firewall", "defense", "injection", "safety check",
           "hallucin", "grounding", "faithful"): return t_gate

    # ============ LAYER 2 — domain keywords (sharper, optional refinements) =====
    # LLM / agents vocabulary (the syllabus this generator was first tuned on)
    if kw("hnsw", "ann", "approximate nearest", "skip list", "langgraph",
           "stategraph", "cypher", "neo4j", "multi-hop"): return t_graphwalk
    if kw("react", "agentic", "agent", "autonomous", "supervisor",
           "orchestrat", "think-act"): return t_loop
    if kw("mcp", "model context protocol", "tool discovery", "tool repositor"):
        return t_router
    if kw("memgpt", "fifo", "conversation history", "checkpointer"):
        return t_memory
    if kw("reflexion", "reflect", "planner", "monte-carlo"): return t_tree
    if kw("mixture of expert", "context engineering", "compaction"):
        return t_layers
    if kw("mixture of agents", "camel", "coder framework"): return t_debate
    if kw("prompt", "instruction", "few-shot", "zero-shot", "chain-of-thought",
           "cot", "co-star"): return t_typewriter
    if kw("token", "tokeniz", "bpe", "wordpiece", "sentencepiece", "subword",
           "attention", "positional"): return t_slidewin
    if kw("cross-entropy", "likelihood", "backprop"): return t_curve_descent
    if kw("polysem", "contextualized", "word2vec", "one-hot"): return t_vectors

    # ============ LAYER 3 — shape-balanced fallback ============================
    # Spread the unmatched across a DIVERSE set of shapes (not all one template),
    # keyed by a stable hash so re-runs are deterministic.
    fallback_pool = [t_pipeline, t_layers, t_trend, t_loop, t_bars_compare,
                     t_tree, t_dist_drift, t_scatter_cluster, t_graphwalk,
                     t_typewriter]
    return fallback_pool[seed_of(term) % len(fallback_pool)]


def main():
    a = sys.argv[1:]
    force = "--force" in a
    only = a[a.index("--only") + 1:] if "--only" in a else None
    shard = None
    if "--batch" in a:
        i = a.index("--batch"); shard = (int(a[i + 1]), int(a[i + 2]))
    terms = (only if only else
             sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(TERMS, "*.md"))))
    if shard:
        idx, n = shard
        terms = [t for j, t in enumerate(terms) if j % n == idx]
    made = skip = fail = 0
    for term in terms:
        g = os.path.join(OUT, slug(term) + ".gif")
        if os.path.exists(g) and not force:
            skip += 1; continue
        rng = np.random.RandomState(seed_of(term))
        try:
            template_for(term)(term, rng, note_params(term))
            made += 1
            if made % 25 == 0: print(f"  ... {made} done")
        except Exception as e:
            print(f"  !! FAIL {term}: {e}"); fail += 1
    print(f"GIFs made {made} | skipped {skip} | failed {fail} | scanned {len(terms)}")


if __name__ == "__main__":
    main()
