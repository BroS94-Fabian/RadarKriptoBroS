#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIKLUS 4 TAHUN KRIPTO
=====================
Data harian Binance:
  - BTC sejak Agustus 2017 (2 siklus halving lengkap sebagai pembanding: puncak 2017 & 2021)
  - ETH dan ±150 koin top CoinMarketCap sejak akhir 2019 (6 tahun terakhir + ruang hitung MA200)

Yang dihitung:
  1. Stage Weinstein BTC: harian (MA200 ≈ 30 minggu, sama dengan radar) dan mingguan (MA 30 minggu klasik)
  2. Puncak & dasar tiap siklus halving (2016, 2020, 2024) dan posisi siklus sekarang
  3. Peta stage seluruh pasar dari waktu ke waktu (% koin di Stage 1/2/3/4)
  4. Peluang naik/turun dari hari ini sampai TUJUAN (default 31 Jan 2027) berdasarkan sejarah:
     semua hari, hari dengan stage/kondisi serupa, posisi siklus yang sama, dan musiman Nov→Jan
Hasil: siklus4/LAPORAN.md, siklus4/hasil.json, siklus4/grafik.png

Ini statistik masa lalu, bukan ramalan. Sampel siklus hanya 2–3, jadi ketidakpastiannya besar.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import scanner as S  # noqa: E402
import siklus as SK  # noqa: E402
import strategi as ST  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "siklus4")
HALVING = [pd.Timestamp(x, tz="UTC") for x in ("2016-07-09", "2020-05-11", "2024-04-20")]
HALVING_BERIKUT = pd.Timestamp("2028-04-15", tz="UTC")   # perkiraan (±210.000 blok setelah 2024)
WARNA = {0: "#d9d8d2", 1: "#2a78d6", 2: "#0a9a0a", 3: "#d99a00", 4: "#d03b3b"}
NAMA = {1: "Stage 1 Dasar", 2: "Stage 2 Naik", 3: "Stage 3 Puncak", 4: "Stage 4 Turun"}


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def harian(bn: S.Binance, sym: str, mulai: pd.Timestamp) -> pd.DataFrame:
    rows, t = [], int(mulai.timestamp() * 1000)
    for _ in range(20):
        r = bn._get("/api/v3/klines", {"symbol": sym, "interval": "1d", "startTime": t, "limit": 1000})
        if not r:
            break
        rows += r
        if len(r) < 1000:
            break
        t = int(r[-1][0]) + 86_400_000
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v", "ct", "qv", "n", "tbv", "tbqv", "x"])
    now_ms = int(time.time() * 1000)
    df = df[df["ct"].astype("int64") < now_ms]
    out = pd.DataFrame({"open": df["o"].astype(float).to_numpy(), "high": df["h"].astype(float).to_numpy(),
                        "low": df["l"].astype(float).to_numpy(), "close": df["c"].astype(float).to_numpy(),
                        "volume": df["v"].astype(float).to_numpy()},
                       index=pd.to_datetime(df["t"].astype("int64"), unit="ms", utc=True).dt.normalize().to_numpy())
    return out[~out.index.duplicated()]


def stage_harian(d: pd.DataFrame) -> pd.Series:
    F = SK.hitung(*(d[k].to_numpy() for k in ("open", "high", "low", "close", "volume")))
    return pd.Series(F["stage"], index=d.index), F


def stage_mingguan(close: pd.Series) -> pd.DataFrame:
    """Weinstein klasik: candle mingguan & MA 30 minggu (kemiringan 4 minggu)."""
    w = close.resample("W-SUN").last().dropna()
    ma = w.rolling(30).mean()
    sl = ma / ma.shift(4) - 1
    hi, lo = w.rolling(104, min_periods=52).max(), w.rolling(104, min_periods=52).min()
    pos = (w - lo) / (hi - lo)
    atas = w > ma
    st = np.where(atas & (sl > 0.02), 2, np.where(~atas & (sl < -0.02), 4, np.where(pos < 0.5, 1, 3)))
    st = np.where(ma.notna() & sl.notna() & pos.notna(), st, 0)
    return pd.DataFrame(dict(close=w, ma30=ma, slope=sl, stage=st))


# --------------------------------------------------------------------------- #
# Statistik
# --------------------------------------------------------------------------- #
def maju(close: pd.Series, h: int) -> pd.Series:
    """Perubahan harga h hari ke depan (persen), dari setiap hari."""
    return (close.shift(-h) / close - 1) * 100


def ringkas(x: pd.Series) -> dict:
    x = x.dropna()
    if len(x) == 0:
        return dict(n=0)
    bulan = x.index.to_period("M").nunique()
    return dict(n=int(len(x)), bulan=int(bulan), naik=round(float((x > 0).mean() * 100), 1),
                median=round(float(x.median()), 1), p25=round(float(x.quantile(0.25)), 1),
                p75=round(float(x.quantile(0.75)), 1), rata=round(float(x.mean()), 1),
                naik_10=round(float((x >= 10).mean() * 100), 1), turun_10=round(float((x <= -10).mean() * 100), 1))


def siklus_halving(btc: pd.DataFrame) -> list[dict]:
    out = []
    batas = HALVING + [HALVING_BERIKUT]
    for i, hv in enumerate(HALVING):
        seg = btc[(btc.index >= hv) & (btc.index < batas[i + 1])]
        if seg.empty:
            continue
        # puncak siklus = harga tertinggi dalam ±2,5 tahun setelah halving (puncak historis: 526–549 hari)
        win = seg[seg.index < hv + pd.Timedelta(days=900)]
        ip = win["high"].idxmax()
        pk = float(win.loc[ip, "high"])
        sesudah = seg[seg.index > ip]
        ib = sesudah["low"].idxmin() if len(sesudah) else None
        out.append(dict(halving=hv.strftime("%Y-%m-%d"), puncak_tgl=ip.strftime("%Y-%m-%d"), puncak=pk,
                        hari_halving_ke_puncak=int((ip - hv).days),
                        dasar_tgl=ib.strftime("%Y-%m-%d") if ib is not None else None,
                        dasar=float(sesudah.loc[ib, "low"]) if ib is not None else None,
                        hari_puncak_ke_dasar=int((ib - ip).days) if ib is not None else None,
                        turun_pct=round((float(sesudah.loc[ib, "low"]) / pk - 1) * 100, 1) if ib is not None else None,
                        data_mulai=seg.index[0].strftime("%Y-%m-%d")))
    return out


def fmt(x, nd=1):
    return "-" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{nd}f}%".replace(".", ",")


def rp(x):
    return f"${x:,.0f}".replace(",", ".")


# --------------------------------------------------------------------------- #
# Grafik
# --------------------------------------------------------------------------- #
def blok_stage(ax, st: pd.Series, alpha=0.18):
    if st.empty:
        return
    v = st.to_numpy()
    idx = st.index
    a = 0
    for i in range(1, len(v) + 1):
        if i == len(v) or v[i] != v[a]:
            if v[a]:
                ax.axvspan(idx[a], idx[min(i, len(v) - 1)], color=WARNA[int(v[a])], alpha=alpha, lw=0, zorder=0)
            a = i


def grafik(btc, st_btc, ma200, ma200w, cyc, idx_alt, breadth, tujuan, path):
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#52514e",
                         "xtick.color": "#52514e", "ytick.color": "#52514e"})
    fig, axs = plt.subplots(3, 1, figsize=(13, 11), sharex=True, gridspec_kw=dict(height_ratios=[3.2, 1.6, 1.6]))
    fig.patch.set_facecolor("#fcfcfb")
    ax = axs[0]
    blok_stage(ax, st_btc)
    ax.plot(btc.index, btc["close"], color="#0b0b0b", lw=1.1, label="BTC (harga harian)")
    ax.plot(ma200.index, ma200, color="#1baf7a", lw=1.2, label="MA200 harian (±30 minggu)")
    ax.plot(ma200w.index, ma200w, color="#7a5af5", lw=1.2, ls="--", label="MA 200 minggu (lantai siklus)")
    ax.set_yscale("log")
    ax.set_ylim(top=float(btc["high"].max()) * 1.9)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"${y:,.0f}".replace(",", ".")))
    for hv in HALVING:
        if hv >= btc.index[0] - pd.Timedelta(days=400):
            ax.axvline(hv, color="#52514e", ls=":", lw=1)
            ax.text(hv, 0.98, f"Halving\n{hv.strftime('%b %Y')}", transform=ax.get_xaxis_transform(), ha="center",
                    va="top", fontsize=8, color="#52514e", bbox=dict(boxstyle="round,pad=0.2", fc="#fcfcfb", ec="none"))
    for c in cyc:
        p = pd.Timestamp(c["puncak_tgl"], tz="UTC")
        if p >= btc.index[0]:
            ax.annotate(f"Puncak {rp(c['puncak'])}\n{p.strftime('%d %b %Y')}", (p, c["puncak"]), xytext=(0, 14),
                        textcoords="offset points", ha="center", fontsize=8, color="#0a7d0a", fontweight="bold",
                        arrowprops=dict(arrowstyle="-", color="#0a7d0a", lw=0.8))
        if c["dasar_tgl"] and (btc.index[-1] - pd.Timestamp(c["dasar_tgl"], tz="UTC")).days > 30:
            b = pd.Timestamp(c["dasar_tgl"], tz="UTC")
            sudah = c.get("dasar_final", True)
            ax.annotate(f"{'Dasar' if sudah else 'Terendah sejauh ini'} {rp(c['dasar'])}\n{b.strftime('%d %b %Y')} "
                        f"({fmt(c['turun_pct'], 0)})", (b, c["dasar"]), xytext=(0, -30), textcoords="offset points",
                        ha="center", fontsize=8, color="#c23232", fontweight="bold",
                        arrowprops=dict(arrowstyle="-", color="#c23232", lw=0.8))
    now = btc.index[-1]
    ax.scatter([now], [btc["close"].iloc[-1]], s=40, color="#c23232", zorder=5)
    ax.annotate(f"Sekarang {rp(btc['close'].iloc[-1])}", (now, btc["close"].iloc[-1]), xytext=(8, 10),
                textcoords="offset points", fontsize=8.5, fontweight="bold")
    ax.axvspan(now, tujuan, color="#76746e", alpha=0.08, lw=0)
    ax.text(now + (tujuan - now) / 2, 0.02, "s/d\n31 Jan\n2027", transform=ax.get_xaxis_transform(), ha="center",
            fontsize=7, color="#76746e")
    ax.set_title("Bitcoin & siklus 4 tahun — latar warna = stage harian "
                 "(biru Dasar · hijau Naik · kuning Puncak · merah Turun)", loc="left", fontsize=11, fontweight="bold")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.grid(alpha=0.25)

    ax2 = axs[1]
    if idx_alt is not None and len(idx_alt):
        ax2.plot(idx_alt.index, idx_alt, color="#eb6834", lw=1.2)
        ax2.set_yscale("log")
        ax2.set_title(f"Indeks altcoin (rata-rata harian {idx_alt.attrs.get('n', 0)} koin yang sudah ada sejak 2020, "
                      "Nov 2020 = 100)", loc="left", fontsize=9)
    ax2.grid(alpha=0.25)

    ax3 = axs[2]
    if breadth is not None and len(breadth):
        b = breadth[["s1", "s2", "s3", "s4"]]
        ax3.stackplot(b.index, *(b[c] for c in b.columns), colors=[WARNA[1], WARNA[2], WARNA[3], WARNA[4]], alpha=0.75,
                      labels=["Dasar", "Naik", "Puncak", "Turun"])
        ax3.set_ylim(0, 100)
        ax3.set_title("Peta siklus pasar: % koin di tiap stage (top CMC di Binance)", loc="left", fontsize=9)
        ax3.legend(loc="upper left", ncol=4, fontsize=8, frameon=False)
    ax3.xaxis.set_major_locator(mdates.YearLocator())
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax3.set_xlim(btc.index[0], tujuan + pd.Timedelta(days=20))
    fig.tight_layout()
    fig.savefig(path, dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Jalankan
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tujuan", default="2027-01-31")
    ap.add_argument("--koin", type=int, default=150)
    args = ap.parse_args()
    t0 = time.time()
    now = datetime.now(timezone.utc)
    cfg, state = S.load_config(), S.load_state()
    bn = S.Binance()

    btc = harian(bn, "BTCUSDT", pd.Timestamp("2017-08-01", tz="UTC"))
    print(f"BTC: {len(btc)} hari ({btc.index[0].date()} – {btc.index[-1].date()})")
    hari_ini = btc.index[-1]
    tujuan = pd.Timestamp(args.tujuan, tz="UTC")
    H = int((tujuan - hari_ini).days)

    rank_list, src = S.ambil_ranking(cfg, state, now)
    tick = bn.tickers(cfg["quote"])
    koin = []
    for c in sorted(rank_list, key=lambda x: x["rank"]):
        b = S.ALIAS_BINANCE.get(c["symbol"], c["symbol"])
        if c.get("stabil") or c["symbol"] == "BTC" or b not in tick:
            continue
        koin.append((tick[b]["symbol"], c["symbol"], c["rank"], bool(c.get("meme")) or ST.is_meme(c["symbol"])))
    koin = koin[:args.koin]
    data = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(harian, bn, k[0], pd.Timestamp("2019-11-01", tz="UTC")): k for k in koin}
        for f in as_completed(futs):
            try:
                d = f.result()
                if len(d) >= 60:
                    data[futs[f][1]] = d
            except Exception as e:
                print("  ! gagal", futs[f][1], e)
    print(f"Koin lain: {len(data)} dari {len(koin)} ({time.time() - t0:.0f} dtk)")

    # ---------- BTC: stage & siklus ----------
    st_btc, F = stage_harian(btc)
    ma200 = pd.Series(F["ma_l"], index=btc.index)
    wk = stage_mingguan(btc["close"])
    ma200w = btc["close"].resample("W-SUN").last().rolling(200).mean().reindex(btc.index, method="ffill")
    j = len(btc) - 1
    kode, teks = SK.fase(F, j, float(btc["close"].iloc[-1]))
    cyc = siklus_halving(btc)
    if cyc:
        cyc[-1]["dasar_final"] = False
    c_now = cyc[-1]
    harga = float(btc["close"].iloc[-1])
    ath = float(btc["high"].max())
    dd_now = (harga / ath - 1) * 100
    hari_sejak_halving = int((hari_ini - HALVING[-1]).days)
    hari_sejak_puncak = int((hari_ini - pd.Timestamp(c_now["puncak_tgl"], tz="UTC")).days)
    sekarang = dict(tanggal=hari_ini.strftime("%Y-%m-%d"), harga=harga, ath=ath, turun_dari_ath=round(dd_now, 1),
                    stage_harian=int(st_btc.iloc[-1]), fase=kode, fase_teks=teks,
                    stage_mingguan=int(wk["stage"].iloc[-1]), ma30w=float(wk["ma30"].iloc[-1]),
                    ma30w_slope=round(float(wk["slope"].iloc[-1]) * 100, 2),
                    ma200=float(ma200.iloc[-1]), ma200w=float(ma200w.iloc[-1]) if np.isfinite(ma200w.iloc[-1]) else None,
                    hari_sejak_halving=hari_sejak_halving, hari_sejak_puncak=hari_sejak_puncak,
                    hari_ke_halving_berikut=int((HALVING_BERIKUT - hari_ini).days), horizon_hari=H,
                    tujuan=tujuan.strftime("%Y-%m-%d"))
    print("Sekarang:", sekarang)

    # Posisi yang sama di siklus sebelumnya
    analog = []
    for c in cyc[:-1]:
        for dasar_hitung, ref in (("halving", pd.Timestamp(c["halving"], tz="UTC") + pd.Timedelta(days=hari_sejak_halving)),
                                  ("puncak", pd.Timestamp(c["puncak_tgl"], tz="UTC") + pd.Timedelta(days=hari_sejak_puncak))):
            if ref not in btc.index or ref + pd.Timedelta(days=H) not in btc.index:
                continue
            p0, p1 = float(btc.loc[ref, "close"]), float(btc.loc[ref + pd.Timedelta(days=H), "close"])
            seg = btc.loc[ref:ref + pd.Timedelta(days=H)]
            pk = pd.Timestamp(c["puncak_tgl"], tz="UTC")
            analog.append(dict(siklus=c["halving"][:4], acuan=dasar_hitung, dari=ref.strftime("%Y-%m-%d"),
                               sampai=(ref + pd.Timedelta(days=H)).strftime("%Y-%m-%d"), harga_dari=p0, harga_sampai=p1,
                               hasil=round((p1 / p0 - 1) * 100, 1),
                               terendah=round((float(seg["low"].min()) / p0 - 1) * 100, 1),
                               tertinggi=round((float(seg["high"].max()) / p0 - 1) * 100, 1),
                               turun_dari_puncak=round((p0 / c["puncak"] - 1) * 100, 1),
                               dasar_sudah_lewat=bool(c["dasar_tgl"] and pd.Timestamp(c["dasar_tgl"], tz="UTC") <= ref),
                               stage=int(st_btc.get(ref, 0)), puncak=pk.strftime("%Y-%m-%d")))

    # ---------- Indeks altcoin & peta stage ----------
    awal6 = pd.Timestamp("2020-11-05", tz="UTC")
    lama = {k: d for k, d in data.items() if d.index[0] <= awal6 and k != "ETH"}
    idx_alt = None
    if lama:
        ret = pd.DataFrame({k: np.log(d["close"]).diff().clip(-0.5, 0.5) for k, d in lama.items()})
        ret = ret[ret.index >= awal6]
        idx_alt = 100 * np.exp(ret.mean(axis=1).fillna(0).cumsum())
        idx_alt.attrs["n"] = len(lama)
    stg = {}
    for k, d in data.items():
        if len(d) >= 230:
            stg[k] = stage_harian(d)[0]
    breadth = None
    if stg:
        B = pd.DataFrame(stg)
        B = B[B.index >= pd.Timestamp("2020-06-01", tz="UTC")]
        valid = (B > 0).sum(axis=1)
        breadth = pd.DataFrame({f"s{s}": (B == s).sum(axis=1) / valid.replace(0, np.nan) * 100 for s in (1, 2, 3, 4)})
        breadth["n"] = valid
        breadth = breadth[breadth["n"] >= 20]
    eth = data.get("ETH")

    # ---------- Peluang naik/turun sampai tujuan ----------
    fb = maju(btc["close"], H)
    fa = maju(idx_alt, H) if idx_alt is not None else None
    fe = maju(eth["close"], H) if eth is not None else None
    dd = (btc["close"] / btc["high"].cummax() - 1) * 100
    pkd = pd.Series(np.nan, index=btc.index)   # hari sejak puncak siklus terakhir (setelah puncak tercapai)
    for c in cyc:
        p = pd.Timestamp(c["puncak_tgl"], tz="UTC")
        nxt = [pd.Timestamp(x["puncak_tgl"], tz="UTC") for x in cyc if pd.Timestamp(x["puncak_tgl"], tz="UTC") > p]
        m = (btc.index >= p) & (btc.index < (nxt[0] if nxt else btc.index[-1] + pd.Timedelta(days=1)))
        pkd[m] = (btc.index[m] - p).days
    hsh = pd.Series(np.nan, index=btc.index)
    for hv in HALVING:
        m = btc.index >= hv
        hsh[m] = (btc.index[m] - hv).days
    s_now = sekarang["stage_harian"]
    w_stage = wk["stage"].reindex(btc.index, method="ffill")
    bawah_ma = (btc["close"] < ma200) & (ma200 < ma200.shift(20))
    KOND = {
        "Semua hari sejak 2017": pd.Series(True, index=btc.index),
        f"Stage harian BTC sama (Stage {s_now})": st_btc == s_now,
        f"Stage mingguan BTC sama (Stage {sekarang['stage_mingguan']})": w_stage == sekarang["stage_mingguan"],
        f"Turun {abs(dd_now) - 10:.0f}–{abs(dd_now) + 10:.0f}% dari ATH": (dd >= dd_now - 10) & (dd <= dd_now + 10),
        "Harga di bawah MA200 yang menurun": bawah_ma,
        f"Fase siklus sama: {hari_sejak_puncak - 75}–{hari_sejak_puncak + 75} hari setelah puncak siklus":
            (pkd >= hari_sejak_puncak - 75) & (pkd <= hari_sejak_puncak + 75),
        f"Fase siklus sama: {hari_sejak_halving - 75}–{hari_sejak_halving + 75} hari setelah halving":
            (hsh >= hari_sejak_halving - 75) & (hsh <= hari_sejak_halving + 75),
    }
    peluang = []
    for nm, m in KOND.items():
        m = m.fillna(False).astype(bool)
        row = dict(kondisi=nm, btc=ringkas(fb[m]))
        if fa is not None:
            row["alt"] = ringkas(fa[fa.index.isin(btc.index[m])])
        if fe is not None:
            row["eth"] = ringkas(fe[fe.index.isin(btc.index[m])])
        peluang.append(row)
    musim = []
    for th in range(2017, hari_ini.year + 1):
        a = pd.Timestamp(f"{th}-{hari_ini.month:02d}-{hari_ini.day:02d}", tz="UTC")
        b = a + pd.Timedelta(days=H)
        if a in btc.index and b in btc.index:
            x = dict(tahun=f"{a.strftime('%d %b %Y')} → {b.strftime('%d %b %Y')}",
                     btc=round((btc.loc[b, "close"] / btc.loc[a, "close"] - 1) * 100, 1))
            if idx_alt is not None and a in idx_alt.index and b in idx_alt.index:
                x["alt"] = round((idx_alt.loc[b] / idx_alt.loc[a] - 1) * 100, 1)
            musim.append(x)

    pasar_now = None
    if breadth is not None and len(breadth):
        r = breadth.iloc[-1]
        pasar_now = dict(dasar=round(float(r["s1"]), 1), naik=round(float(r["s2"]), 1), puncak=round(float(r["s3"]), 1),
                         turun=round(float(r["s4"]), 1), n=int(r["n"]))
        # sejarah: % koin di Stage 2 per bulan
        bln = breadth.resample("ME").last()
        pasar_now["riwayat_bulanan"] = [dict(bulan=i.strftime("%Y-%m"), naik=round(float(v["s2"]), 1),
                                             turun=round(float(v["s4"]), 1), dasar=round(float(v["s1"]), 1))
                                        for i, v in bln.iterrows()]
    if idx_alt is not None:
        sekarang["alt_dari_puncak"] = round(float(idx_alt.iloc[-1] / idx_alt.max() - 1) * 100, 1)
        sekarang["alt_puncak_tgl"] = idx_alt.idxmax().strftime("%Y-%m-%d")
        ia = idx_alt[idx_alt.index >= HALVING[-1]]
        sekarang["alt_dari_puncak_siklus"] = round(float(ia.iloc[-1] / ia.max() - 1) * 100, 1)
        sekarang["alt_puncak_siklus_tgl"] = ia.idxmax().strftime("%Y-%m-%d")
        sekarang["alt_dari_terendah_siklus"] = round(float(ia.iloc[-1] / ia[ia.index > ia.idxmax()].min() - 1) * 100, 1)
        sekarang["alt_terendah_siklus_tgl"] = ia[ia.index > ia.idxmax()].idxmin().strftime("%Y-%m-%d")
    lo_c = pd.Timestamp(c_now["dasar_tgl"], tz="UTC") if c_now["dasar_tgl"] else None
    if lo_c is not None:
        sekarang["naik_dari_terendah"] = round((harga / c_now["dasar"] - 1) * 100, 1)
        sekarang["hari_sejak_terendah"] = int((hari_ini - lo_c).days)
    bulanan_btc = [dict(bulan=i.strftime("%Y-%m"), close=round(float(v), 0))
                   for i, v in btc["close"].resample("ME").last().items() if i >= pd.Timestamp("2025-01-01", tz="UTC")]
    st_bulanan = [dict(bulan=i.strftime("%Y-%m"), stage=int(v)) for i, v in st_btc.resample("ME").last().items()]

    hasil = dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), sekarang=sekarang,
                 siklus=cyc, analog=analog, peluang=peluang, musiman=musim, pasar=pasar_now,
                 stage_btc_bulanan=st_bulanan, btc_bulanan=bulanan_btc, koin=len(data), koin_indeks=len(lama))

    # ---------- Laporan ----------
    os.makedirs(OUT, exist_ok=True)
    grafik(btc, st_btc, ma200, ma200w, cyc, idx_alt, breadth, tujuan, os.path.join(OUT, "grafik.png"))
    L = ["# 🔄 Siklus 4 Tahun Kripto", "",
         f"Dibuat {hasil['dibuat_wib']} · BTC sejak {btc.index[0].date()} · {len(data)} koin lain sejak akhir 2019 · "
         f"horizon {H} hari (s/d {sekarang['tujuan']})", "",
         "![grafik](grafik.png)", "",
         "## Posisi sekarang", "",
         f"- Harga BTC {rp(harga)} · ATH {rp(ath)} · **{fmt(dd_now)} dari ATH**",
         f"- Stage harian (MA200): **{NAMA.get(sekarang['stage_harian'], '-')}** — {teks}",
         f"- Stage mingguan (MA 30 minggu, Weinstein klasik): **{NAMA.get(sekarang['stage_mingguan'], '-')}** "
         f"(MA30 minggu {rp(sekarang['ma30w'])}, kemiringan 4 minggu {fmt(sekarang['ma30w_slope'], 2)})",
         f"- MA200 harian {rp(sekarang['ma200'])} · MA 200 minggu {rp(sekarang['ma200w']) if sekarang['ma200w'] else '-'}",
         f"- {hari_sejak_halving} hari setelah halving April 2024 · {hari_sejak_puncak} hari setelah puncak siklus "
         f"({c_now['puncak_tgl']}, {rp(c_now['puncak'])}) · ±{sekarang['hari_ke_halving_berikut']} hari ke halving berikutnya",
         ]
    if pasar_now:
        L.append(f"- Peta pasar ({pasar_now['n']} koin): Dasar {pasar_now['dasar']}% · Naik {pasar_now['naik']}% · "
                 f"Puncak {pasar_now['puncak']}% · Turun {pasar_now['turun']}%")
    if "naik_dari_terendah" in sekarang:
        L.append(f"- Terendah siklus ini {rp(c_now['dasar'])} ({c_now['dasar_tgl']}, {sekarang['hari_sejak_terendah']} hari lalu) · "
                 f"sekarang {fmt(sekarang['naik_dari_terendah'])} dari titik itu")
    if "alt_dari_puncak" in sekarang:
        L.append(f"- Indeks altcoin {fmt(sekarang['alt_dari_puncak_siklus'])} dari puncak siklus ini "
                 f"({sekarang['alt_puncak_siklus_tgl']}), {fmt(sekarang['alt_dari_terendah_siklus'])} dari terendahnya "
                 f"({sekarang['alt_terendah_siklus_tgl']}) · {fmt(sekarang['alt_dari_puncak'])} dari puncak 2021")
    L += ["", "## Siklus halving", "",
          "| Halving | Puncak | Hari halving→puncak | Dasar | Hari puncak→dasar | Turun |", "|---|---|---|---|---|---|"]
    for c in cyc:
        L.append(f"| {c['halving']} | {c['puncak_tgl']} · {rp(c['puncak'])} | {c['hari_halving_ke_puncak']} | "
                 f"{(c['dasar_tgl'] or '-')} · {rp(c['dasar']) if c['dasar'] else '-'}"
                 f"{'' if c.get('dasar_final', True) else ' (terendah sejauh ini)'} | {c['hari_puncak_ke_dasar'] or '-'} | "
                 f"{fmt(c['turun_pct'])} |")
    L += ["", f"Catatan: data Binance baru mulai {cyc[0]['data_mulai']}, jadi siklus 2016 dihitung dari tanggal itu.", "",
          f"## Posisi yang sama di siklus sebelumnya (horizon {H} hari)", "",
          "| Siklus | Disejajarkan dari | Periode | Turun dari puncak saat itu | Dasar sudah lewat? | Hasil | Terendah | Tertinggi |",
          "|---|---|---|---|---|---|---|---|"]
    for a in analog:
        L.append(f"| {a['siklus']} | {a['acuan']} | {a['dari']} → {a['sampai']} | {fmt(a['turun_dari_puncak'])} | "
                 f"{'ya' if a['dasar_sudah_lewat'] else 'belum'} | **{fmt(a['hasil'])}** | {fmt(a['terendah'])} | {fmt(a['tertinggi'])} |")
    L += ["", f"## Peluang dari sejarah: perubahan {H} hari ke depan", "",
          "Setiap hari dalam sejarah dengan kondisi serupa dihitung hasilnya H hari kemudian. "
          "Hari-hari berurutan saling tumpang tindih, jadi sampel sebenarnya ±jumlah bulan.", "",
          "| Kondisi | Aset | Hari (bulan) | Peluang naik | Median | Kisaran tengah (25–75%) | Naik ≥10% | Turun ≥10% |",
          "|---|---|---|---|---|---|---|---|"]
    for p in peluang:
        for aset, key in (("BTC", "btc"), ("Altcoin", "alt"), ("ETH", "eth")):
            x = p.get(key) or {}
            if x.get("n"):
                L.append(f"| {p['kondisi']} | {aset} | {x['n']} ({x['bulan']}) | **{x['naik']}%** | {fmt(x['median'])} | "
                         f"{fmt(x['p25'])} s/d {fmt(x['p75'])} | {x['naik_10']}% | {x['turun_10']}% |")
    L += ["", f"## Musiman: tanggal yang sama tiap tahun (+{H} hari)", "", "| Periode | BTC | Altcoin |", "|---|---|---|"]
    for m in musim:
        L.append(f"| {m['tahun']} | {fmt(m['btc'])} | {fmt(m.get('alt'))} |")
    L += ["", "## Keterbatasan", "",
          "- Hanya 2–3 siklus halving yang tercatat; pola bisa berubah (ETF, suku bunga, regulasi).",
          "- Indeks altcoin & peta pasar memakai koin top saat ini (survivorship bias: koin yang mati tidak ikut).",
          "- Peluang = frekuensi masa lalu, bukan ramalan. Bukan ajakan beli/jual."]
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as f:
        json.dump(hasil, f, ensure_ascii=False, indent=1, default=lambda o: None if o != o else str(o))
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"Selesai {time.time() - t0:.0f} dtk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
