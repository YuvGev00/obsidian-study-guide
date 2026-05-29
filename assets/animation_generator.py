#!/usr/bin/env python3
"""
STARTER animated-GIF generator for an Obsidian study vault.

Copy this to <Vault>/Assets/_generate.py, then ADD one function per dynamic
concept following the exemplars below. Run:
    python3 _generate.py            # all
    python3 _generate.py batch2     # only a named batch (see __main__)

Design:
  - matplotlib 'Agg' + PillowWriter  -> writes .gif, NO ffmpeg needed
  - dark theme to match Obsidian dark mode
  - small, looping, ~20-60 KB each (cheap to embed dozens)
  - idempotent & re-runnable; batch selectors so you regen subsets

Only animate genuinely DYNAMIC ideas (descent paths, sliding filters, gradient
flow, curve sweeps, dropout). Static facts stay as static diagrams.

Embed in a note's '## Visual' (animation first, static diagram kept below):
    **Animated:** <caption>

    ![[anim_<name>.gif]]
Reuse one GIF across closely-related notes instead of duplicating files.
"""
import os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

OUT = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({
    "figure.facecolor": "#1e1e1e", "axes.facecolor": "#1e1e1e",
    "savefig.facecolor": "#1e1e1e", "text.color": "#e0e0e0",
    "axes.labelcolor": "#e0e0e0", "xtick.color": "#b0b0b0",
    "ytick.color": "#b0b0b0", "axes.edgecolor": "#666666",
    "font.size": 11, "axes.titlecolor": "#e0e0e0",
})
FPS = 12
PALETTE = dict(blue="#4fc3f7", green="#66bb6a", orange="#ff7043",
               red="#ef5350", yellow="#ffca28", grey="#9e9e9e")

def save(anim, name, fps=FPS):
    p = os.path.join(OUT, name + ".gif")
    anim.save(p, writer=PillowWriter(fps=fps)); plt.close('all')
    print("  ->", name + ".gif")

# ---- EXEMPLAR 1: a moving point on a curve (use for GD / loss curves / sigmoid)
def ex_gradient_descent():
    fig, ax = plt.subplots(figsize=(5, 3.2))
    xs = np.linspace(-3, 3, 200)
    ax.plot(xs, xs**2, color=PALETTE["blue"], lw=2)
    pt, = ax.plot([], [], 'o', color=PALETTE["orange"], ms=12)
    ax.set_title("Gradient Descent: step downhill"); ax.set_xlabel("w"); ax.set_ylabel("cost")
    x = [2.7]
    def upd(i):
        pt.set_data([x[0]], [x[0]**2]); x[0] -= 0.15 * (2*x[0]); return pt,
    save(FuncAnimation(fig, upd, frames=40, blit=True), "anim_gradient_descent")

# ---- EXEMPLAR 2: a 2-D contour trajectory (use for SGD/momentum/Adam paths)
def ex_momentum():
    fig, ax = plt.subplots(figsize=(5, 3.4))
    X, Y = np.meshgrid(np.linspace(-4,4,80), np.linspace(-2,2,60)); Z = 0.1*X**2 + 2*Y**2
    ax.contour(X, Y, Z, 12, colors="#555", linewidths=.6)
    s, = ax.plot([], [], 'o-', color=PALETTE["red"], ms=6, lw=1, label="SGD")
    m, = ax.plot([], [], 'o-', color=PALETTE["green"], ms=6, lw=1, label="Momentum")
    ax.legend(fontsize=8, facecolor="#1e1e1e", edgecolor="#555", labelcolor="#e0e0e0")
    ax.set_title("SGD zig-zags; Momentum glides")
    st = dict(sx=-3.6, sy=1.6, mx=-3.6, my=-1.6, vx=0, vy=0); SX=[];SY=[];MX=[];MY=[]
    def upd(i):
        st['sx'] -= .18*.2*st['sx']; st['sy'] -= .18*4*st['sy']
        gx, gy = .2*st['mx'], 4*st['my']
        st['vx'] = .85*st['vx'] - .18*gx; st['vy'] = .85*st['vy'] - .18*gy
        st['mx'] += st['vx']; st['my'] += st['vy']
        SX.append(st['sx']);SY.append(st['sy']);MX.append(st['mx']);MY.append(st['my'])
        s.set_data(SX,SY); m.set_data(MX,MY); return s,m
    save(FuncAnimation(fig, upd, frames=45, blit=True), "anim_momentum_vs_sgd")

# ---- EXEMPLAR 3: a sliding window over a grid (use for conv / pooling / stride)
def ex_convolution():
    img = np.random.RandomState(0).rand(7,7)
    fig,(a1,a2)=plt.subplots(1,2,figsize=(6,3.2))
    a1.imshow(img,cmap="viridis"); a1.set_title("Input (filter slides)")
    out=np.zeros((5,5)); im2=a2.imshow(out,cmap="magma",vmin=0,vmax=4)
    a2.set_title("Activation map (fills in)")
    for a in (a1,a2): a.set_xticks([]); a.set_yticks([])
    rect=plt.Rectangle((-.5,-.5),3,3,fill=False,edgecolor=PALETTE["orange"],lw=2.5); a1.add_patch(rect)
    pos=[(i,j) for i in range(5) for j in range(5)]
    def upd(k):
        i,j=pos[k]; rect.set_xy((j-.5,i-.5))
        out[i,j]=img[i:i+3,j:j+3].mean()*9; im2.set_data(out); return rect,im2
    save(FuncAnimation(fig,upd,frames=25,blit=False),"anim_convolution",fps=6)

# ---- EXEMPLAR 4: progressive curve draw-in (use for activations / loss shapes)
def ex_activations():
    x=np.linspace(-5,5,200)
    fig,ax=plt.subplots(figsize=(5,3.2)); ax.set_xlim(-5,5); ax.set_ylim(-1.2,3)
    ax.set_title("Activation functions")
    data={"Sigmoid":1/(1+np.exp(-x)),"Tanh":np.tanh(x),"ReLU":np.maximum(0,x)}
    cols=[PALETTE["blue"],PALETTE["green"],PALETTE["orange"]]
    L=[ax.plot([],[],color=c,lw=2,label=n)[0] for (n,_),c in zip(data.items(),cols)]
    ax.legend(fontsize=8,facecolor="#1e1e1e",edgecolor="#555",labelcolor="#e0e0e0")
    vals=list(data.values())
    def upd(i):
        n=int(len(x)*(i+1)/40)
        for l,v in zip(L,vals): l.set_data(x[:n],v[:n])
        return L
    save(FuncAnimation(fig,upd,frames=40,blit=True),"anim_activations")

# ---- EXEMPLAR 5: a building-up flow/architecture (use for pipelines, networks)
def ex_pipeline():
    fig,ax=plt.subplots(figsize=(6,2.4))
    steps=["Collect (x,t)","Model + loss","Minimize cost","Generalize"]
    def upd(k):
        ax.clear(); ax.axis("off"); ax.set_xlim(0,12); ax.set_ylim(0,2)
        ax.set_title("Supervised pipeline")
        for idx,s in enumerate(steps[:k+1]):
            ax.add_patch(plt.Rectangle((idx*3+.2,.4),2.5,1.2,
                         color=plt.cm.viridis(idx/4),ec="#222"))
            ax.text(idx*3+1.45,1,s,ha="center",va="center",fontsize=8,color="#111")
            if idx>0: ax.annotate("",(idx*3+.2,1),(idx*3-3+2.7,1),
                                   arrowprops=dict(arrowstyle="->",color="#888"))
        return []
    save(FuncAnimation(fig,upd,frames=4,blit=False),"anim_pipeline",fps=1)

if __name__ == "__main__":
    import sys
    ALL = [ex_gradient_descent, ex_momentum, ex_convolution,
           ex_activations, ex_pipeline]
    # Add more functions above and register them in named batches here, e.g.:
    #   BATCH2 = [ex_new_a, ex_new_b]; sel = {"batch2": BATCH2}.get(arg, ALL)
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    sel = ALL  # extend with batch dict as the vault grows
    print(f"Generating {len(sel)} animations...")
    for fn in sel:
        try: fn()
        except Exception as e: print("  !! FAILED", fn.__name__, e)
    print("Done.")
