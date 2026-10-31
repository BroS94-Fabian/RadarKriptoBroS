# -*- coding: utf-8 -*-
"""Grafik analisa per koin: candle + MA + Bollinger + trend line + pola + target,
ditambah panel Volume, RSI, MACD, Stochastic dan profil volume (zona akumulasi)."""
from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from analisa import BULAN, fmt_big, fmt_pct, fmt_price  # noqa: E402

C = dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9",
         axis="#c3c2b7", up="#0ca30c", down="#d03b3b", ma20="#eb6834", ma50="#2a78d6", ma200="#1baf7a",
         blue="#2a78d6", blue_lt="#86b6ef", orange="#eb6834", red="#e34948", vol="#c3c2b7",
         good="#0ca30c", crit="#d03b3b", band="#898781")


def _style(ax):
    ax.set_facecolor(C["surface"])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(C["axis"])
    ax.tick_params(colors=C["muted"], labelsize=8, length=3)
    ax.grid(axis="y", color=C["grid"], lw=0.6)
    ax.set_axisbelow(True)


def _axis_price(v, _=None):
    s = fmt_price(v)
    return s.rstrip("0").rstrip(",") if "," in s else s


def _chip(ax, x, y, text, color, fg="#ffffff"):
    t = ax.text(x, y, f" {text} ", transform=ax.transAxes, fontsize=9, fontweight="bold", color=fg,
                va="bottom", ha="right",
                bbox=dict(boxstyle="round,pad=0.35", fc=color, ec="none"))
    return t


def buat_grafik(r: dict, quote: str, sumber: str, waktu: str) -> bytes:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    g = r["_g"]
    dc = g["dc"]
    n = len(dc)
    P, ell, vp, tl = g["pola"], g["ell"], g["vp"], g["tl"]
    s0 = max(0, n - 120)
    if P:
        s0 = max(0, n - 200, min(s0, P["mulai"] - 6))
    idx = np.arange(s0, n)
    seg = dc.iloc[s0:n]
    price = float(r["price"])
    right = n + max(14, int(0.16 * (n - s0)))  # ruang label di kanan

    fig = plt.figure(figsize=(10, 12.2), dpi=105, facecolor=C["surface"])
    gs = fig.add_gridspec(5, 2, width_ratios=[5, 1.1], height_ratios=[4.2, 1.0, 1.0, 1.0, 1.0],
                          hspace=0.28, wspace=0.03, top=0.95, bottom=0.045)
    ax = fig.add_subplot(gs[0, 0])
    axp = fig.add_subplot(gs[0, 1], sharey=ax)
    axv = fig.add_subplot(gs[1, 0], sharex=ax)
    axr = fig.add_subplot(gs[2, 0], sharex=ax)
    axm = fig.add_subplot(gs[3, 0], sharex=ax)
    axs = fig.add_subplot(gs[4, 0], sharex=ax)
    for a in (ax, axp, axv, axr, axm, axs):
        _style(a)

    # ---- Harga ----
    ax.fill_between(idx, g["bb_lo"][s0:n], g["bb_up"][s0:n], color=C["band"], alpha=0.09, lw=0, zorder=0)
    if vp:
        ax.axhspan(vp["val"], vp["vah"], color=C["blue"], alpha=0.06, lw=0, zorder=0)
    ma_labels = []
    for key, lw, lab in (("ma20", 1.1, "MA20"), ("ma50", 1.3, "MA50"), ("ma200", 1.7, "MA200")):
        y = g[key][s0:n]
        if np.isfinite(y).any():
            ax.plot(idx, y, color=C[key], lw=lw, zorder=2)
            ma_labels.append([float(y[np.isfinite(y)][-1]), lab, key])
    wbody = 0.62
    for i, row in zip(idx, seg.itertuples(index=False)):
        up = row.close >= row.open
        col = C["up"] if up else C["down"]
        ax.vlines(i, row.low, row.high, color=col, lw=0.9, zorder=3)
        lo = min(row.open, row.close)
        hgt = max(abs(row.close - row.open), (row.high - row.low) * 0.02, 1e-12)
        ax.add_patch(Rectangle((i - wbody / 2, lo), wbody, hgt, facecolor=C["surface"] if up else col,
                               edgecolor=col, lw=1.0, zorder=4))
    # Trend line (support / resistance)
    for gl, lab in ((tl.get("sup"), "support"), (tl.get("res"), "resistance")):
        if gl is None:
            continue
        a = max(int(gl.i1), s0)
        xs = np.array([a, n - 1])
        ys = np.array([gl.at(a), gl.at(n - 1)])
        if np.all(ys > 0) and abs(ys[1] / price - 1) <= 0.2 and gl.i2 - gl.i1 >= 8:
            ax.plot(xs, ys, color=C["muted"], lw=1.0, ls=(0, (4, 3)), zorder=5)
    # Pola
    if P:
        for gr in P["garis"]:
            i1 = max(gr["i1"], s0)
            if gr["i2"] == gr["i1"]:
                continue
            m = (gr["p2"] - gr["p1"]) / (gr["i2"] - gr["i1"])
            y1 = gr["p1"] + m * (i1 - gr["i1"])
            ax.plot([i1, gr["i2"]], [y1, gr["p2"]], color=C["ink"], lw=1.8, zorder=6, solid_capstyle="round")
            if gr.get("label"):
                ax.text(i1, y1, gr["label"], fontsize=7.5, color=C["ink"], va="bottom", ha="left", zorder=8,
                        bbox=dict(boxstyle="round,pad=0.15", fc=C["surface"], ec="none", alpha=0.85))
        for t in P["titik"]:
            if t["i"] < s0:
                continue
            below = (t["p"] <= np.nanmedian(seg["close"]))
            ax.annotate(t["label"], (t["i"], t["p"]), xytext=(0, -14 if below else 10), textcoords="offset points",
                        ha="center", fontsize=7.5, color=C["ink"], zorder=8,
                        bbox=dict(boxstyle="round,pad=0.15", fc=C["surface"], ec=C["axis"], lw=0.6))
    # Elliott
    if ell:
        dekat = {t["i"] for t in (P["titik"] if P else [])}
        closes = dc["close"].to_numpy()
        for t in ell.get("titik", []):
            if t["i"] < s0:
                continue
            bawah = t["p"] <= closes[t["i"]]
            geser = 12 if any(abs(t["i"] - k) <= 6 for k in dekat) else 0
            dy = (-26 if bawah else 18) if geser else (-13 if bawah else 6)
            ax.annotate(f"({t['label']})", (t["i"], t["p"]), xytext=(geser, dy),
                        textcoords="offset points", ha="left" if geser else "center",
                        fontsize=7.5, fontweight="bold", color=C["ink2"], zorder=8)
    # Target & batal
    tgt, bt = g["target"], g["batal"]
    ys_extra = []
    if tgt:
        col = C["good"] if tgt["harga"] > price else C["crit"]
        ax.plot([n - 8, right], [tgt["harga"], tgt["harga"]], color=col, lw=1.4, ls=(0, (6, 3)), zorder=6)
        ax.text(right, tgt["harga"], f"Target {fmt_pct(tgt['pct'])}\n{fmt_price(tgt['harga'])}", fontsize=7.5,
                color=C["ink"], ha="right", va="bottom" if tgt["harga"] > price else "top", zorder=9,
                bbox=dict(boxstyle="round,pad=0.2", fc=C["surface"], ec="none", alpha=0.9))
        ys_extra.append(tgt["harga"])
    if bt:
        col = C["crit"] if bt["harga"] < price else C["good"]
        ax.plot([n - 8, right], [bt["harga"], bt["harga"]], color=col, lw=1.2, ls=(0, (1, 2)), zorder=6)
        ax.text(right, bt["harga"], f"Batal {fmt_pct(bt['pct'])}\n{fmt_price(bt['harga'])}", fontsize=7.5,
                color=C["ink"], ha="right", va="top" if bt["harga"] < price else "bottom", zorder=9,
                bbox=dict(boxstyle="round,pad=0.2", fc=C["surface"], ec="none", alpha=0.9))
        ys_extra.append(bt["harga"])
    ax.axhline(price, color=C["ink2"], lw=0.8, ls=":", zorder=1)
    ylo = min(float(seg["low"].min()), *ys_extra) if ys_extra else float(seg["low"].min())
    yhi = max(float(seg["high"].max()), *ys_extra) if ys_extra else float(seg["high"].max())
    pad = (yhi - ylo) * 0.07
    ax.set_ylim(ylo - pad, yhi + pad)
    # label MA di kanan, dijarakkan agar tidak bertumpuk
    gap = 0.04 * (yhi - ylo + 2 * pad)
    ma_labels.sort(key=lambda x: x[0])
    for k in range(1, len(ma_labels)):
        if ma_labels[k][0] - ma_labels[k - 1][0] < gap:
            ma_labels[k][0] = ma_labels[k - 1][0] + gap
    for yv, lab, key in ma_labels:
        ax.text(n + 0.6, yv, lab, color=C["ink2"], fontsize=7, va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc=C["surface"], ec=C[key], lw=0.8))
    ax.set_xlim(s0 - 1, right + 1)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(_axis_price))
    plt.setp(ax.get_xticklabels(), visible=False)

    # Judul
    kelas = r["kelas"]
    chip_txt, chip_col, chip_fg = {"naik": ("POTENSI NAIK", C["good"], "#ffffff"),
                                   "turun": ("POTENSI TURUN", C["crit"], "#ffffff")}.get(
        kelas, ("NETRAL", C["axis"], C["ink"]))
    rank = f"  ·  #{r['rank']} CoinMarketCap" if r.get("rank") else ""
    ax.set_title(f"{r['base']}/{quote}{rank}", loc="left", fontsize=13, fontweight="bold", color=C["ink"], pad=34)
    sub = f"Harga {fmt_price(price)} ({fmt_pct(r['chg24'])} 24j)  ·  Skor naik {r['skor_naik']} / turun {r['skor_turun']}"
    ax.text(0, 1.035, sub, transform=ax.transAxes, fontsize=9, color=C["ink2"], va="bottom")
    _chip(ax, 1.0, 1.035, chip_txt, chip_col, chip_fg)
    if P:
        ax.text(0.01, 0.97, f"{P['nama']}", transform=ax.transAxes, fontsize=9, fontweight="bold",
                color=C["ink"], va="top", zorder=9,
                bbox=dict(boxstyle="round,pad=0.3", fc=C["surface"], ec=C["axis"], lw=0.8))
    leg = "MA20 / MA50 / MA200 · area abu = Bollinger Bands · area biru = zona akumulasi · garis putus abu = trend line"
    ax.text(0, -0.025, leg, transform=ax.transAxes, fontsize=7, color=C["muted"], va="top")

    # Profil volume
    if vp:
        cols = [C["blue"] if i == vp["poc_i"] else (C["blue_lt"] if vp["va"][0] <= i <= vp["va"][1] else C["vol"])
                for i in range(len(vp["vol"]))]
        bh = (vp["edges"][1] - vp["edges"][0]) * 0.86
        axp.barh(vp["centers"], vp["vol"], height=bh, color=cols, lw=0)
        axp.set_xlim(0, vp["vol"].max() * 1.9)
        axp.text(vp["vol"][vp["poc_i"]] * 1.05, vp["poc"], f"POC\n{fmt_price(vp['poc'])}", fontsize=7.5,
                 color=C["ink"], va="center")
    axp.set_title("Volume per harga\n(zona akumulasi)", fontsize=8, color=C["ink2"])
    axp.tick_params(axis="x", bottom=False, labelbottom=False)
    axp.tick_params(axis="y", left=False)
    plt.setp(axp.get_yticklabels(), visible=False)
    for s in ("left", "bottom"):
        axp.spines[s].set_visible(False)
    axp.grid(False)

    # Volume
    qv = seg["qvol"].to_numpy()
    avg = dc["qvol"].shift(1).rolling(20, min_periods=5).mean().to_numpy()[s0:n]
    spike = np.nan_to_num(qv > 2 * avg, nan=False).astype(bool)
    axv.bar(idx, qv, width=0.7, color=np.where(spike, C["orange"], C["vol"]), lw=0)
    axv.plot(idx, avg, color=C["ink2"], lw=1.1)
    axv.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt_big(v).replace("$", "")))
    axv.set_title("Volume harian — oranye: > 2x rata-rata 20 hari", loc="left", fontsize=8, color=C["ink2"], pad=3)

    # RSI
    rs = g["rsi"][s0:n]
    axr.axhspan(70, 100, color=C["crit"], alpha=0.05, lw=0)
    axr.axhspan(0, 30, color=C["good"], alpha=0.05, lw=0)
    for lv in (30, 70):
        axr.axhline(lv, color=C["axis"], lw=0.8, ls="--")
    axr.plot(idx, rs, color=C["blue"], lw=1.4)
    axr.set_ylim(0, 100)
    axr.set_yticks([30, 70])
    last_rsi = rs[np.isfinite(rs)][-1] if np.isfinite(rs).any() else np.nan
    axr.set_title(f"RSI 14 = {last_rsi:.0f}  (>70 overbought · <30 oversold)", loc="left", fontsize=8,
                  color=C["ink2"], pad=3)

    # MACD
    hist = g["macd_hist"][s0:n]
    axm.bar(idx, hist, width=0.7, color=np.where(hist >= 0, C["blue_lt"], "#f1a9a9"), lw=0)
    axm.plot(idx, g["macd"][s0:n], color=C["ink"], lw=1.1)
    axm.plot(idx, g["macd_sig"][s0:n], color=C["orange"], lw=1.1, ls=(0, (4, 2)))
    axm.axhline(0, color=C["axis"], lw=0.8)
    axm.tick_params(axis="y", labelleft=False, left=False)
    axm.set_title("MACD 12,26,9 — garis hitam: MACD · putus oranye: sinyal · batang: histogram", loc="left",
                  fontsize=8, color=C["ink2"], pad=3)

    # Stochastic
    for lv in (20, 80):
        axs.axhline(lv, color=C["axis"], lw=0.8, ls="--")
    axs.plot(idx, g["sk"][s0:n], color=C["blue"], lw=1.3)
    axs.plot(idx, g["sd"][s0:n], color=C["orange"], lw=1.1, ls=(0, (4, 2)))
    axs.set_ylim(0, 100)
    axs.set_yticks([20, 80])
    axs.set_title("Stochastic 14,3,3 — biru: %K · putus oranye: %D (>80 overbought · <20 oversold)",
                  loc="left", fontsize=8, color=C["ink2"], pad=3)
    for a in (axv, axr, axm):
        plt.setp(a.get_xticklabels(), visible=False)
    step = 15 if len(idx) > 100 else 10
    ticks = list(range(n - 1, s0 - 1, -step))[::-1]
    axs.set_xticks(ticks)
    axs.set_xticklabels([f"{t.day} {BULAN[t.month - 1]}" for t in dc["time"].iloc[ticks]])

    fig.text(0.99, 0.012, f"Sumber: {sumber} · {waktu} · target = proyeksi pola, bukan jaminan",
             ha="right", fontsize=7, color=C["muted"])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=C["surface"], bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return buf.getvalue()
