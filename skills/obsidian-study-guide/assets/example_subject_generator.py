#!/usr/bin/env python3
"""Concept-faithful per-term GIFs for Lecture 7 (CNN Architectures).

Each template actually DEPICTS the mechanic of its concept. Dark theme,
looping, PillowWriter (no ffmpeg). Run:  python3 Assets/_gen_l7.py
Always overwrites its own 28 targets (use to refresh).
"""
import os, warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
warnings.filterwarnings("ignore")

OUT = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({
    "figure.facecolor": "#1e1e1e", "axes.facecolor": "#1e1e1e",
    "savefig.facecolor": "#1e1e1e", "text.color": "#e6e6e6",
    "axes.labelcolor": "#cfcfcf", "xtick.color": "#9a9a9a",
    "ytick.color": "#9a9a9a", "axes.edgecolor": "#555",
    "font.size": 10, "axes.titlecolor": "#e6e6e6", "axes.titlesize": 12,
})
PAL = ["#4fc3f7", "#66bb6a", "#ffa726", "#ef5350", "#ab47bc",
       "#26c6da", "#d4e157", "#ec407a", "#8d6e63", "#7e94ff"]
FPS = 12


def save(fig, anim, slug):
    path = os.path.join(OUT, "anim_" + slug + ".gif")
    anim.save(path, writer=PillowWriter(fps=FPS))
    plt.close(fig)
    print("  made", slug)


def box(ax, x, y, w, h, label, color, alpha=1.0, fs=9):
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02",
                       fc=color, ec="#e6e6e6", lw=1.2, alpha=alpha, zorder=3)
    ax.add_patch(p)
    ax.text(x, y, label, ha="center", va="center", color="#111", fontsize=fs,
            zorder=4, weight="bold")
    return p


def t_curve_timeline(slug, title, vals, labels, hi=None):
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    n = len(vals); frames = n + 6

    def upd(f):
        ax.clear(); ax.set_title(title)
        ax.set_ylim(0, max(vals) * 1.25); ax.set_xlim(-0.6, n - 0.4)
        for i in range(min(f, n)):
            c = PAL[3] if (hi is not None and i == hi) else PAL[0]
            ax.bar(i, vals[i], color=c, ec="#e6e6e6", lw=0.8)
            ax.text(i, vals[i] + max(vals) * 0.02, f"{vals[i]}", ha="center", fontsize=8, color="#e6e6e6")
        ax.set_xticks(range(n)); ax.set_xticklabels(labels, fontsize=7, rotation=30, ha="right")
        ax.set_ylabel("top-5 error %")
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=380), slug)


def t_cost_bars(slug, title, cats, series, snames, ylab=""):
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    n = len(cats); k = len(series); w = 0.8 / k
    mx = max(max(s) for s in series); frames = 22

    def upd(f):
        ax.clear(); ax.set_title(title); ax.set_ylim(0, mx * 1.15)
        g = min(1.0, (f + 1) / 16)
        for j, s in enumerate(series):
            xs = np.arange(n) + (j - (k - 1) / 2) * w
            ax.bar(xs, [v * g for v in s], width=w, color=PAL[j], ec="#333", label=snames[j])
        ax.set_xticks(range(n)); ax.set_xticklabels(cats, fontsize=7, rotation=20)
        ax.legend(fontsize=7, loc="upper right")
        if ylab: ax.set_ylabel(ylab)
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=110), slug)


def t_train_test(slug, title):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(5.6, 3.0))
    x = np.linspace(0, 1, 60)
    deep = 0.18 + 0.5 * np.exp(-4 * x) + 0.10
    shal = 0.10 + 0.5 * np.exp(-5 * x); frames = 60

    def upd(f):
        for a, ttl in ((a1, "training error"), (a2, "test error")):
            a.clear(); a.set_title(ttl, fontsize=9)
            a.set_xlim(0, 1); a.set_ylim(0, 0.8); a.set_xticks([]); a.set_yticks([])
        k = max(2, f)
        a1.plot(x[:k], deep[:k], color=PAL[3], lw=2, label="56-layer")
        a1.plot(x[:k], shal[:k], color=PAL[0], lw=2, label="20-layer")
        a2.plot(x[:k], deep[:k] + 0.04, color=PAL[3], lw=2)
        a2.plot(x[:k], shal[:k] + 0.05, color=PAL[0], lw=2)
        a1.legend(fontsize=7); fig.suptitle(title, fontsize=12)
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=70), slug)


def t_inception(slug, title):
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    branches = [("1x1", PAL[0]), ("3x3", PAL[1]), ("5x5", PAL[2]), ("pool", PAL[3])]
    xs = [1.8, 4.0, 6.2, 8.4]; frames = 22

    def upd(f):
        ax.clear(); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off"); ax.set_title(title)
        box(ax, 5, 1.2, 4.6, 0.9, "previous layer", "#cfcfcf", fs=8)
        prog = min(4, f // 3)
        for i, (lbl, c) in enumerate(branches):
            al = 1.0 if i < prog else 0.18
            box(ax, xs[i], 5.0, 1.4, 1.0, lbl, c, alpha=al, fs=9)
            ax.add_patch(FancyArrowPatch((5, 1.7), (xs[i], 4.5), arrowstyle="-|>", color="#888", alpha=al, mutation_scale=10))
            ax.add_patch(FancyArrowPatch((xs[i], 5.5), (5, 8.3), arrowstyle="-|>", color="#888", alpha=al, mutation_scale=10))
        cat_al = 1.0 if f >= 16 else 0.2
        box(ax, 5, 8.9, 4.8, 0.9, "filter concatenation", PAL[5], alpha=cat_al, fs=8)
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=160), slug)


def t_bottleneck(slug, title):
    fig, ax = plt.subplots(figsize=(5.4, 3.2)); frames = 30

    def upd(f):
        ax.clear(); ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off"); ax.set_title(title)
        t = (np.sin(f / 30 * 2 * np.pi) + 1) / 2
        wide_h = 4.2; narrow_h = 1.2
        h_mid = wide_h - (wide_h - narrow_h) * t
        box(ax, 1.6, 3, 1.0, wide_h, "256", PAL[0], fs=9)
        box(ax, 5.0, 3, 1.0, h_mid, "64" if t > .5 else "->", PAL[2], fs=9)
        box(ax, 8.4, 3, 1.0, wide_h, "256", PAL[1], fs=9)
        ax.text(3.3, 0.6, "1x1 reduce", color="#9a9a9a", fontsize=8, ha="center")
        ax.text(6.7, 0.6, "1x1 expand", color="#9a9a9a", fontsize=8, ha="center")
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=80), slug)


def t_residual(slug, title):
    fig, ax = plt.subplots(figsize=(5.0, 3.6)); frames = 36

    def upd(f):
        ax.clear(); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off"); ax.set_title(title)
        box(ax, 5, 1.0, 2.0, 0.8, "x", "#cfcfcf", fs=10)
        box(ax, 5, 3.6, 2.4, 0.9, "conv -> relu", PAL[2], fs=8)
        box(ax, 5, 5.6, 2.4, 0.9, "conv  F(x)", PAL[2], fs=8)
        box(ax, 5, 8.2, 2.4, 0.9, "H=F(x)+x", PAL[1], fs=8)
        ax.add_patch(FancyArrowPatch((5, 1.4), (5, 3.1), arrowstyle="-|>", color="#888", mutation_scale=12))
        ax.add_patch(FancyArrowPatch((5, 4.1), (5, 5.1), arrowstyle="-|>", color="#888", mutation_scale=12))
        ax.add_patch(FancyArrowPatch((5, 6.1), (5, 7.7), arrowstyle="-|>", color="#888", mutation_scale=12))
        ax.plot([6.2, 8.4, 8.4, 6.2], [1.0, 1.0, 8.2, 8.2], color=PAL[0], lw=2)
        ax.text(9.1, 4.6, "identity\nskip", color=PAL[0], fontsize=8, ha="center")
        seg = (f % 36) / 36
        if seg < .33: px, py = 6.2 + (8.4 - 6.2) * (seg / .33), 1.0
        elif seg < .66: px, py = 8.4, 1.0 + (8.2 - 1.0) * ((seg - .33) / .33)
        else: px, py = 8.4 - (8.4 - 6.2) * ((seg - .66) / .34), 8.2
        ax.plot(px, py, "o", color=PAL[3], ms=11)
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=70), slug)


def t_gradient_flow(slug, title):
    fig, ax = plt.subplots(figsize=(5.2, 3.2)); L = 9; x = np.arange(L); frames = L + 4

    def upd(f):
        ax.clear(); ax.set_title(title); ax.set_xlim(-0.5, L - 0.5); ax.set_ylim(0, 1.1)
        ax.set_xlabel("layer (deep -> shallow)"); ax.set_ylabel("gradient magnitude")
        plain = 0.7 ** x; resid = np.ones(L) * 0.9; k = min(L, f + 1)
        ax.plot(x[:k], plain[:k], "o-", color=PAL[3], lw=2, label="plain (vanishes)")
        ax.plot(x[:k], resid[:k], "s-", color=PAL[1], lw=2, label="residual (+1)")
        ax.legend(fontsize=8, loc="center right")
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=220), slug)


def t_encoder_decoder(slug, title, with_skips=True):
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    enc = [(1.2, 8), (1.2, 6.2), (1.2, 4.4), (1.2, 2.6)]
    dec = [(8.8, 8), (8.8, 6.2), (8.8, 4.4), (8.8, 2.6)]
    sizes = [1.4, 1.1, 0.85, 0.6]; frames = 24

    def upd(f):
        ax.clear(); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off"); ax.set_title(title)
        for i, (x, y) in enumerate(enc): box(ax, x, y, 0.9, sizes[i], "", PAL[0], fs=7)
        box(ax, 5, 1.2, 1.2, 0.7, "bottleneck", PAL[4], fs=7)
        for i, (x, y) in enumerate(dec): box(ax, x, y, 0.9, sizes[i], "", PAL[1], fs=7)
        ax.text(1.2, 9.1, "encoder v", color=PAL[0], fontsize=8, ha="center")
        ax.text(8.8, 9.1, "decoder ^", color=PAL[1], fontsize=8, ha="center")
        if with_skips:
            shown = min(4, f // 4)
            for i in range(shown):
                ax.add_patch(FancyArrowPatch((enc[i][0] + 0.5, enc[i][1]), (dec[i][0] - 0.5, dec[i][1]),
                             arrowstyle="-|>", color=PAL[2], lw=1.6, mutation_scale=10))
            if shown: ax.text(5, 8.7, "copy + concat (skip)", color=PAL[2], fontsize=7, ha="center")
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=160), slug)


def t_stack_filters(slug, title):
    fig, ax = plt.subplots(figsize=(4.4, 3.6)); frames = 24

    def upd(f):
        ax.clear(); ax.set_xlim(0, 7); ax.set_ylim(0, 7); ax.axis("off"); ax.set_title(title)
        for gx in range(8):
            ax.plot([gx, gx], [0, 7], color="#444", lw=0.6); ax.plot([0, 7], [gx, gx], color="#444", lw=0.6)
        rings = [(3, 4, PAL[1]), (2, 5, PAL[2]), (1, 6, PAL[3])]
        for i in range(min(3, f // 5 + 1)):
            lo, hi, c = rings[i]
            ax.add_patch(plt.Rectangle((lo, lo), hi - lo, hi - lo, fill=False, ec=c, lw=2.4))
        ax.text(3.5, 6.4, "stacked 3x3 => 7x7 RF", color="#e6e6e6", fontsize=8, ha="center")
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=180), slug)


def t_vgg_modular(slug, title):
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    stages = [(64, 4.0), (128, 3.0), (256, 2.1), (512, 1.4), (512, 0.9)]
    frames = len(stages) + 4

    def upd(f):
        ax.clear(); ax.set_xlim(0, 11); ax.set_ylim(0, 6); ax.axis("off"); ax.set_title(title)
        shown = min(len(stages), f)
        for i in range(shown):
            ch, h = stages[i]; x = 1.2 + i * 2.0
            box(ax, x, 3, 1.3, h, f"{ch}", PAL[i % len(PAL)], fs=8)
            ax.text(x, 3 - h / 2 - 0.4, "v pool" if i < shown - 1 else "", color="#9a9a9a", fontsize=7, ha="center")
        ax.text(5.5, 5.4, "halve space . double channels", color="#e6e6e6", fontsize=8, ha="center")
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=260), slug)


def t_pipeline(slug, title, stages):
    fig, ax = plt.subplots(figsize=(5.4, 2.6)); n = len(stages); frames = n + 4

    def upd(f):
        ax.clear(); ax.set_xlim(0, 11); ax.set_ylim(0, 4); ax.axis("off"); ax.set_title(title)
        shown = min(n, f); xs = np.linspace(1.3, 9.7, n)
        for i in range(shown):
            box(ax, xs[i], 2, 1.5, 1.1, stages[i], PAL[i % len(PAL)], fs=7)
            if i > 0:
                ax.add_patch(FancyArrowPatch((xs[i - 1] + 0.75, 2), (xs[i] - 0.75, 2), arrowstyle="-|>", color="#888", mutation_scale=10))
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=300), slug)


def t_softmax_sharpen(slug, title, labels):
    fig, ax = plt.subplots(figsize=(5.0, 3.0)); n = len(labels)
    base = np.linspace(1.0, 0.2, n); frames = 30

    def upd(f):
        ax.clear(); ax.set_title(title); ax.set_ylim(0, 1.0)
        T = 2.0 - 1.8 * (f / frames)
        p = np.exp(base / T); p = p / p.sum()
        colors = [PAL[3] if i == 0 else PAL[0] for i in range(n)]
        ax.bar(range(n), p, color=colors, ec="#333")
        ax.set_xticks(range(n)); ax.set_xticklabels(labels, fontsize=7, rotation=20); ax.set_ylabel("prob")
    save(fig, FuncAnimation(fig, upd, frames=frames, interval=90), slug)


def build():
    t_softmax_sharpen("feature_hierarchy_in_cnns", "Feature Hierarchy in CNNs", ["edges", "textures", "parts", "objects"])
    t_pipeline("imagenet", "ImageNet", ["14M imgs", "20k classes", "MTurk labels", "1000-class"])
    t_curve_timeline("ilsvrc", "ILSVRC top-5 error", [28, 26, 16, 12, 7, 7, 4],
                     ["'10", "'11", "AlexN", "ZFNet", "VGG", "GoogLe", "ResNet"], hi=6)
    t_softmax_sharpen("top_5_error", "Top-5 Error", ["true", "guess2", "guess3", "guess4", "guess5"])
    t_cost_bars("alexnet_layer_analysis", "AlexNet: cost per layer", ["conv1", "conv2", "conv3", "fc6", "fc7"],
                [[800, 550, 250, 16, 16], [35, 307, 664, 37749, 16777]], ["memory KB", "params K"])
    t_cost_bars("memory_params_flops_tradeoff", "Where cost lives", ["early conv", "deep conv", "FC"],
                [[800, 250, 16], [35, 600, 37000], [106, 145, 38]], ["memory", "params", "FLOPs"])
    t_pipeline("zfnet", "ZFNet = bigger AlexNet", ["7x7 s2", "512/1024/512", "tuned", "11.7%"])
    t_vgg_modular("vgg_modular_design", "VGG Modular Design")
    t_stack_filters("stacked_3x3_vs_one_7x7", "Stacked 3x3 vs one 7x7")
    t_pipeline("googlenet", "GoogLeNet", ["stem", "inception xN", "GAP", "linear->1000"])
    t_inception("inception_module", "Inception Module")
    t_inception("naive_inception_module", "Naive Inception (no bottleneck)")
    t_bottleneck("bottleneck_layer", "1x1 Bottleneck Layer")
    t_pipeline("auxiliary_classifier", "Auxiliary Classifier", ["mid layer", "avgpool", "FC", "extra grad"])
    t_train_test("degradation_problem", "Degradation Problem")
    t_residual("residual_block", "Residual Block")
    t_gradient_flow("identity_mapping", "Identity Mapping (additive)")
    t_gradient_flow("resnet_gradient_flow", "ResNet Gradient Flow")
    t_cost_bars("spatial_batch_normalization", "Spatial BatchNorm (per channel)", ["chan1", "chan2", "chan3"],
                [[0.9, 0.6, 0.8], [0.3, 0.3, 0.3]], ["raw", "normalized"])
    t_vgg_modular("wide_resnet", "Wide ResNet (fewer, wider)")
    t_inception("resnext", "ResNeXt (parallel paths)")
    t_pipeline("cardinality", "Cardinality", ["path 1", "path 2", "...", "path 32"])
    t_encoder_decoder("densenet", "DenseNet (dense connections)", with_skips=True)
    t_curve_timeline("network_generations", "Network Generations", [16, 7, 4, 3],
                     ["AlexN'12", "VGG'14", "ResNet'15", "next'16"], hi=2)
    t_cost_bars("architecture_complexity_comparison", "Accuracy vs cost", ["AlexNet", "VGG", "GoogLeNet", "ResNet"],
                [[57, 71, 69, 76], [1, 14, 2, 4]], ["accuracy", "GFLOPs"])
    t_encoder_decoder("encoder_decoder_architecture", "Encoder-Decoder", with_skips=False)
    t_encoder_decoder("u_net", "U-Net (skip connections)", with_skips=True)
    t_pipeline("cnn_design_principles", "CNN Design Principles", ["small filters", "1x1 bottleneck", "down space", "skips"])


if __name__ == "__main__":
    print("generating L7 concept-faithful GIFs...")
    build()
    print("done.")
