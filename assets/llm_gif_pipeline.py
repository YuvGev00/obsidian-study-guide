#!/usr/bin/env python3
"""LLM-authored per-term GIF harness — genuinely one bespoke animation per term.

The MODEL writes only the per-frame DRAWING BODY for a concept (a short snippet
that, given `ax`, `i` (frame), `n` (total frames), `np`, `plt`, and the supplied
`palette`, draws frame i of an animation that depicts THAT concept's mechanic).
This harness supplies the fixed, safe scaffold: it builds the figure, runs
FuncAnimation, saves anim_<slug>.gif, and sandboxes execution so a snippet can
only touch matplotlib + numpy (no imports, files, network, os).

Workflow (driven by the skill, not this file):
  1. A cheap-model sub-agent reads a term note and writes a snippet (see
     SNIPPET CONTRACT below). It writes the snippet to Assets/_snippets/<Term>.py
     and the orchestrator batch-renders them with this harness.
  2. This harness execs the snippet body inside draw(ax, i, n, np, plt, palette,
     P) in a restricted namespace, renders the GIF, returns a status dict.
  3. Caller validates (ok? non-trivial size?), spot-checks via a vision agent,
     and asks the model to regenerate any failures.

CLI (batch a directory of snippet sidecars):
  python3 llm_gif_pipeline.py --snippets Assets/_snippets --terms Terms --out Assets
  # each Assets/_snippets/<Term>.py contains ONLY the body of draw(...).

SNIPPET CONTRACT (what the model writes — the BODY only, no def line):
  - Available names: ax, i, n, np, plt, palette (list of hex colors), P (dict
    with P['title'] term name, P['labels'] list of the note's key phrases).
  - Draw frame i (0..n-1) of the animation on ax. (The harness calls ax.clear()
    before each frame for you.)
  - Use i/n for progress. Keep it concept-faithful: show the actual mechanic
    (a sliding window moving, bars sharpening, a skip-connection adding, a tree
    growing, two distributions separating, ...) NOT a generic shape.
  - NO imports, NO file/network/os access, NO `while True`. ~5-40 lines.
"""
import os, sys, argparse, ast, warnings, builtins
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

warnings.filterwarnings("ignore")

PALETTE = ["#4fc3f7", "#66bb6a", "#ffa726", "#ef5350", "#ab47bc",
           "#26c6da", "#d4e157", "#ec407a", "#8d6e63", "#7e94ff"]
FPS = 12
plt.rcParams.update({
    "figure.facecolor": "#1e1e1e", "axes.facecolor": "#1e1e1e",
    "savefig.facecolor": "#1e1e1e", "text.color": "#e6e6e6",
    "axes.labelcolor": "#cfcfcf", "xtick.color": "#9a9a9a",
    "ytick.color": "#9a9a9a", "axes.edgecolor": "#555",
    "font.size": 10, "axes.titlecolor": "#e6e6e6", "axes.titlesize": 12,
})

_FORBIDDEN = ("import", "__", "open(", "exec(", "eval(", "compile(",
              "globals(", "locals(", "getattr(", "setattr(", "os.", "sys.",
              "subprocess", "socket", "while true", "while 1", "input(",
              "path(", "shutil", "requests", "urllib")


def slug(name):
    return "anim_" + "".join(c if c.isalnum() else "_" for c in name).strip("_").lower()


def _static_ok(body):
    low = body.lower()
    for tok in _FORBIDDEN:
        if tok in low:
            return False, f"forbidden token: {tok!r}"
    try:
        ast.parse(body)
    except SyntaxError as e:
        return False, f"syntax error: {e}"
    return True, ""


def _safe_globals():
    allowed = {k: getattr(builtins, k) for k in (
        "range", "len", "min", "max", "abs", "round", "int", "float", "str",
        "list", "tuple", "dict", "set", "enumerate", "zip", "sorted", "sum",
        "map", "filter", "bool", "True", "False", "None") if hasattr(builtins, k)}
    return {"__builtins__": allowed, "np": np, "plt": plt}


def render_snippet(body, term, labels=None, out_dir=".", frames=36, fps=FPS):
    ok, why = _static_ok(body)
    if not ok:
        return {"term": term, "ok": False, "stage": "guard", "error": why}

    P = {"title": term, "labels": labels or []}
    ns = _safe_globals()
    src = ("def draw(ax, i, n, np, plt, palette, P):\n" +
           "\n".join("    " + ln for ln in body.splitlines()))
    try:
        code = compile(src, f"<snippet:{term}>", "exec")
        exec(code, ns)
        draw = ns["draw"]
    except Exception as e:
        return {"term": term, "ok": False, "stage": "compile", "error": repr(e)}

    fig, ax = plt.subplots(figsize=(5.0, 3.2))

    def upd(i):
        ax.clear()
        draw(ax, i, frames, np, plt, PALETTE, P)

    path = os.path.join(out_dir, slug(term) + ".gif")
    try:
        anim = FuncAnimation(fig, upd, frames=frames, interval=1000 // fps)
        anim.save(path, writer=PillowWriter(fps=fps))
    except Exception as e:
        plt.close(fig)
        return {"term": term, "ok": False, "stage": "render", "error": repr(e)}
    plt.close(fig)

    size = os.path.getsize(path)
    return {"term": term, "ok": True, "stage": "done", "path": path,
            "bytes": size, "suspect_blank": size < 6000}


def _labels_from_note(term, terms_dir):
    import re  # harness-side only, never exposed to the snippet namespace
    p = os.path.join(terms_dir, term + ".md")
    if not os.path.exists(p):
        return []
    s = open(p, encoding="utf-8").read()
    out = []
    for sec in ("## Formal definition", "## Why we need it"):
        st = s.find(sec)
        if st == -1:
            continue
        end = s.find("\n## ", st + 5)
        chunk = s[st:end if end != -1 else st + 1500]
        for b in re.findall(r"\*\*([A-Za-z][^*\n]{2,34})\*\*", chunk):
            b = b.strip(" .:,;")
            if 2 < len(b) < 32 and b not in out:
                out.append(b)
    return out[:6]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snippets", required=True, help="dir of <Term>.py drawing-body files")
    ap.add_argument("--terms", default="Terms")
    ap.add_argument("--out", default="Assets")
    ap.add_argument("--frames", type=int, default=36)
    args = ap.parse_args()

    made = fail = suspect = 0
    for fn in sorted(os.listdir(args.snippets)):
        if not fn.endswith(".py"):
            continue
        term = fn[:-3]
        body = open(os.path.join(args.snippets, fn), encoding="utf-8").read()
        labels = _labels_from_note(term, args.terms)
        r = render_snippet(body, term, labels, out_dir=args.out, frames=args.frames)
        if r["ok"]:
            made += 1
            if r.get("suspect_blank"):
                suspect += 1
                print(f"  SUSPECT (tiny) {term}: {r['bytes']}B")
        else:
            fail += 1
            print(f"  FAIL {term} [{r['stage']}]: {r['error']}")
    print(f"\nrendered {made} | failed {fail} | suspect-blank {suspect}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
