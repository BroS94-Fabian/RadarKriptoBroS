#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKTEST MODE JANGKA PENDEK
===========================
Candle 1 jam ±2 tahun untuk koin top CMC (bukan meme) di Binance.
Dua kelompok lama tahan:  ≤3 jam  dan  6–24 jam (6, 12, 24 jam).
Dua jenis sinyal: pantul (dasar kisaran) dan tembus (breakout atap kisaran + volume).

Supaya tidak tertipu "kebetulan cocok":
  - Kombinasi terbaik DIPILIH memakai periode 1 (paruh pertama data) saja,
  - lalu DIUJI di periode 2 (paruh kedua) yang tidak dipakai saat memilih.
Bersih = setelah biaya beli/jual 0,1%, pajak jual 0,21%, slippage 0,05% per sisi.

Hasil: backtest_jp/LAPORAN.md, backtest_jp/hasil.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import jangka_pendek as JP
import scanner as S
import strategi as ST

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_jp")
MASUK = ([dict(jenis="pantul", rsi_max=r, posisi_max=p, lebar_min=l)
          for r in (30, 35, 40) for p in (0.2, 0.3) for l in (0.03, 0.05)]
         + [dict(jenis="tembus", vol_rel_min=v, lebar_min=0.02, lebar_max=lm)
            for v in (1.5, 2.5) for lm in (0.10, 0.20)])
KELUAR = {
    3: [(t, s) for t in ("1.0", "1.5", "2.0", "pola") for s in ("1.0", "1.5", "2.0", "support")],
    6: [(t, s) for t in ("1.5", "2.0", "3.0", "pola") for s in ("1.5", "2.0", "3.0", "support")],
    12: [(t, s) for t in ("2.0", "3.0", "4.0", "pola") for s in ("2.0", "3.0", "4.0", "support")],
    24: [(t, s) for t in ("3.0", "4.0", "5.0", "pola") for s in ("2.0", "3.0", "5.0", "support")],
}
KELOMPOK = {"≤3 jam": [3], "6–24 jam": [6, 12, 24]}
REZIM_KODE = {"naik": 0, "netral": 1, "turun": 2}
MIN_N_P1 = 100


def label_masuk(vi):
    v = MASUK[vi]
    if v["jenis"] == "tembus":
        return f"TEMBUS atap kisaran, volume ≥{v['vol_rel_min']}x, lebar kisaran ≤{int(v['lebar_max'] * 100)}%"
    return f"PANTUL dasar kisaran, RSI≤{v['rsi_max']}, posisi≤{int(v['posisi_max'] * 100)}%, lebar≥{int(v['lebar_min'] * 100)}%"


def label_keluar(vi, H, vk):
    t, s = KELUAR[H][vk]
    tembus = MASUK[vi]["jenis"] == "tembus"
    tp = ("TP atap + tinggi kisaran" if tembus else "TP tengah kisaran") if t == "pola" else f"TP +{t}%"
    sl = ("SL masuk lagi ke kisaran" if tembus else "SL bawah support") if s == "support" else f"SL −{s}%"
    return f"{tp} / {sl} / maks {H} jam"


def ambil_jam(bn: S.Binance, symbol: str, hari: int) -> pd.DataFrame:
    rows, end = [], int(time.time() * 1000)
    while len(rows) < hari * 24:
        batch = bn._get("/api/v3/klines", {"symbol": symbol, "interval": "1h", "limit": 1000, "endTime": end})
        if not batch:
            break
        rows = batch + rows
        end = int(batch[0][0]) - 1
        if len(batch) < 1000:
            break
        time.sleep(0.4)
    df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v", "ct", "qv", "n", "tbv", "tbqv", "x"])
    now_ms = int(time.time() * 1000)
    out = pd.DataFrame({"time": pd.to_datetime(df["t"].astype("int64"), unit="ms", utc=True),
                        "open": df["o"].astype(float), "high": df["h"].astype(float), "low": df["l"].astype(float),
                        "close": df["c"].astype(float), "qvol": df["qv"].astype(float),
                        "closed": df["ct"].astype("int64") < now_ms})
    out = out[out["closed"]].drop_duplicates("time").sort_values("time").reset_index(drop=True)
    return out.tail(hari * 24).reset_index(drop=True)


def _jam(t: pd.Series) -> np.ndarray:
    return ((t - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(hours=1)).to_numpy()


def proses(job):
    """Hasil per koin: {(vi, H, vk, rezim, periode): [n, jumlah, jumlah², menang, untung, rugi]}."""
    h, rezim, P0, batas = job
    F = JP.fitur(h, P0["jendela"])
    hi, lo, cl = h["high"].to_numpy(), h["low"].to_numpy(), h["close"].to_numpy()
    kol = {k: F[k].to_numpy() for k in ("rng_lo", "rng_hi", "rng_hi_prev", "rng_lo_prev", "support")}
    jam = _jam(h["time"])
    n = len(h)
    agg: dict = {}
    for vi, vm in enumerate(MASUK):
        P = dict(P0, **vm)
        idx = np.where(JP.mask_masuk(F, P).to_numpy())[0]
        for H, exits in KELUAR.items():
            last = -10 ** 9
            for i in idx:
                if i >= n - H or i - last < H:
                    continue
                last = i
                per = 1 if jam[i] < batas else 2
                baris = {k: v[i] for k, v in kol.items()}
                hh, ll, cc = hi[i + 1:i + 1 + H], lo[i + 1:i + 1 + H], cl[i + 1:i + 1 + H]
                for vk, (tp, sl) in enumerate(exits):
                    plan = JP.rencana_jp(float(cl[i]), baris, dict(P, tp=tp, sl=sl, tahan_jam=H))
                    if plan is None:
                        continue
                    x = JP.bersih_jp(JP.simulasi_jp(plan, hh, ll, cc)["pnl"], P)
                    key = (vi, H, vk, int(rezim[i]), per)
                    a = agg.get(key)
                    if a is None:
                        a = agg[key] = [0, 0.0, 0.0, 0, 0.0, 0.0]
                    a[0] += 1
                    a[1] += x
                    a[2] += x * x
                    if x > 0:
                        a[3] += 1
                        a[4] += x
                    else:
                        a[5] -= x
    return agg


def gabung(aggs, filt):
    out = np.zeros(6)
    for key, a in aggs.items():
        if filt(key):
            out += np.array(a, dtype=float)
    return out


def stat(a) -> dict:
    n = int(a[0])
    if n == 0:
        return dict(n=0)
    m = a[1] / n
    var = max(a[2] / n - m * m, 0) * n / max(n - 1, 1)
    sd = var ** 0.5
    return dict(n=n, menang=round(100 * a[3] / n, 1), rata=round(m, 3),
                pf=round(a[4] / a[5], 2) if a[5] > 0 else None,
                t=round(m / (sd / n ** 0.5), 2) if sd > 0 and n > 2 else None, total=round(a[1], 1))


def baris_md(lbl, s):
    if not s.get("n"):
        return f"| {lbl} | 0 | - | - | - | - |"
    return (f"| {lbl} | {s['n']} | {s['menang']}% | {s['rata']:+.2f}% | "
            f"{s['pf'] if s['pf'] is not None else '-'} | {s['t'] if s['t'] is not None else '-'} |")


KEPALA = ["| | Trade | Menang | Rata-rata bersih | Profit factor | t |", "|---|---|---|---|---|---|"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hari", type=int, default=730)
    ap.add_argument("--maks-koin", type=int, default=100)
    args = ap.parse_args()
    t0 = time.time()
    cfg = S.load_config()
    P0 = dict(JP.DEFAULT_JP, **(cfg.get("jangka_pendek") or {}))
    state = S.load_state()
    now = datetime.now(timezone.utc)
    rank_list, src_rank = S.ambil_ranking(cfg, state, now)
    bn = S.Binance()
    tick = bn.tickers(cfg["quote"])
    koin = []
    for c in sorted(rank_list, key=lambda x: x["rank"]):
        b = S.ALIAS_BINANCE.get(c["symbol"], c["symbol"])
        if c.get("stabil") or c["symbol"] in cfg["abaikan"] or b not in tick or c.get("meme") or ST.is_meme(c["symbol"]):
            continue
        koin.append(tick[b]["symbol"])
    koin = koin[:args.maks_koin]
    print(f"{len(koin)} koin, ambil {args.hari} hari candle 1 jam...")

    btc_d = bn.candles("BTCUSDT", "1d", 1000)
    btc_d = btc_d[btc_d["closed"]].reset_index(drop=True)
    rz_hari = dict(zip(btc_d["time"].dt.strftime("%Y-%m-%d"), ST.rezim_series(btc_d["close"].to_numpy())))

    data = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(ambil_jam, bn, k, args.hari): k for k in koin}
        for f in as_completed(futs):
            try:
                d = f.result()
                if len(d) > 24 * 60:
                    data[futs[f]] = d
            except Exception as e:
                print("  ! gagal", futs[f], e)
    syms = sorted(data)
    t_awal = min(_jam(data[s]["time"])[0] for s in syms)
    t_akhir = max(_jam(data[s]["time"])[-1] for s in syms)
    batas = int(t_awal + (t_akhir - t_awal) // 2)
    print(f"Data {len(syms)} koin ({time.time() - t0:.0f} dtk). Simulasi...")

    jobs, rezim_map = [], {}
    for sym in syms:
        h = data[sym]
        kemarin = (h["time"] - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")   # rezim hari sebelumnya (tanpa bocoran)
        rz = np.array([REZIM_KODE.get(rz_hari.get(d, "netral"), 1) for d in kemarin], dtype=np.int8)
        rezim_map[sym] = rz
        jobs.append((h, rz, P0, batas))
    aggs: dict = {}
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for i, agg in enumerate(ex.map(proses, jobs, chunksize=1), start=1):
            for k, a in agg.items():
                b = aggs.get(k)
                if b is None:
                    aggs[k] = list(a)
                else:
                    for j in range(6):
                        b[j] += a[j]
            if i % 20 == 0:
                print(f"  {i}/{len(jobs)} koin · {time.time() - t0:.0f} dtk")

    # Pembanding: beli di jam acak saat sideways, jual setelah H jam
    acak = {}
    for H in KELUAR:
        xs = []
        for sym in syms:
            c = data[sym]["close"].to_numpy()
            r = (c[H:] / c[:-H] - 1) * 100
            ok = rezim_map[sym][:-H] == 1
            xs.extend(r[ok][::6])
        xs = np.array([JP.bersih_jp(x, P0) for x in xs])
        acak[H] = stat(np.array([len(xs), xs.sum(), (xs ** 2).sum(), (xs > 0).sum(), xs[xs > 0].sum(), -xs[xs < 0].sum()]))

    def ringkas(vi, H, vk, rezim_filter):
        sel = lambda per: (lambda k: k[0] == vi and k[1] == H and k[2] == vk and rezim_filter(k[3]) and k[4] == per)  # noqa: E731
        p1, p2 = gabung(aggs, sel(1)), gabung(aggs, sel(2))
        return dict(vi=vi, H=H, vk=vk, masuk=label_masuk(vi), keluar=label_keluar(vi, H, vk), param=dict(
            MASUK[vi], tp=KELUAR[H][vk][0], sl=KELUAR[H][vk][1], tahan_jam=H),
            p1=stat(p1), p2=stat(p2), semua=stat(p1 + p2))

    hasil = dict(meta=dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), koin=len(syms),
                           dari=datetime.fromtimestamp(t_awal * 3600, tz=timezone.utc).strftime("%d %b %Y"),
                           sampai=datetime.fromtimestamp(t_akhir * 3600, tz=timezone.utc).strftime("%d %b %Y"),
                           batas=datetime.fromtimestamp(batas * 3600, tz=timezone.utc).strftime("%d %b %Y"),
                           kombinasi=sum(len(MASUK) * len(v) for v in KELUAR.values()), durasi=round(time.time() - t0)),
                 pembanding_acak={str(H): s for H, s in acak.items()}, kelompok={})
    for kondisi, rf in (("sideways", lambda r: r == 1), ("semua", lambda r: True)):
        for nama, Hs in KELOMPOK.items():
            semua_k = [ringkas(vi, H, vk, rf) for H in Hs for vi in range(len(MASUK)) for vk in range(len(KELUAR[H]))]
            cand = sorted([k for k in semua_k if k["p1"].get("n", 0) >= MIN_N_P1], key=lambda k: -k["p1"]["rata"])
            best = cand[0] if cand else None
            lolos = bool(best and best["p1"]["rata"] > 0 and best["p2"].get("n", 0) >= 50 and best["p2"]["rata"] > 0)
            per_h = {}
            for H in Hs:
                ch = [k for k in cand if k["H"] == H]
                if ch:
                    per_h[str(H)] = ch[0]
            p2_pos = sum(1 for k in cand if k["p2"].get("rata", -1) > 0)
            hasil["kelompok"][f"{nama}|{kondisi}"] = dict(terbaik=best, lolos=lolos, top10=cand[:10], per_jam=per_h,
                                                         diuji=len(cand), p2_positif=p2_pos)

    m = hasil["meta"]
    L = ["# ⚡ Backtest Mode Jangka Pendek", "",
         f"Dibuat {m['dibuat_wib']} · candle 1 jam {m['dari']} s/d {m['sampai']} · {m['koin']} koin (bukan meme) · "
         f"{m['kombinasi']} kombinasi.", "",
         f"Periode 1 (MEMILIH): {m['dari']} – {m['batas']} · Periode 2 (MENGUJI): {m['batas']} – {m['sampai']}.",
         "Bersih = setelah biaya 0,1% beli/jual, pajak jual 0,21%, slippage 0,05% per sisi.", "",
         "## Pembanding: beli di jam acak saat BTC sideways", "", *KEPALA]
    L += [baris_md(f"Tahan {H} jam", s) for H, s in acak.items()]
    for kondisi, judul in (("sideways", "saat BTC sideways"), ("semua", "di semua kondisi BTC")):
        for nama in KELOMPOK:
            g = hasil["kelompok"][f"{nama}|{kondisi}"]
            b = g["terbaik"]
            L += ["", f"## Mode {nama} — {judul}", ""]
            if not b:
                L += ["Tidak ada kombinasi dengan cukup trade."]
                continue
            L += [f"**Terbaik di periode 1:** {b['masuk']} · {b['keluar']}", "", *KEPALA,
                  baris_md("Periode 1 (memilih)", b["p1"]), baris_md("Periode 2 (menguji)", b["p2"]),
                  baris_md("Gabungan", b["semua"]), "",
                  f"**Lolos uji (positif di kedua periode): {'YA ✅' if g['lolos'] else 'TIDAK ❌'}** · "
                  f"dari {g['diuji']} kombinasi yang cukup trade, {g['p2_positif']} positif di periode 2.", "",
                  "Terbaik per lama tahan (dipilih di periode 1):", "",
                  "| Tahan | Sinyal | Jual | P1 rata-rata | P2 trade | P2 menang | P2 rata-rata |", "|---|---|---|---|---|---|---|"]
            for H, k in g["per_jam"].items():
                L.append(f"| {H} jam | {k['masuk']} | {k['keluar']} | {k['p1']['rata']:+.2f}% | {k['p2'].get('n', 0)} | "
                         f"{k['p2'].get('menang', 0)}% | {k['p2'].get('rata', 0):+.2f}% |")
    L += ["", "## Keterbatasan", "",
          "- Masuk di harga penutupan candle 1 jam; bila TP & SL tersentuh di jam yang sama dianggap SL dulu.",
          "- Daftar koin = top CMC saat ini (survivorship bias). Spread & antrian order di bursa Indonesia bisa berbeda.",
          "- Hasil masa lalu tidak menjamin hasil masa depan."]
    md = "\n".join(L) + "\n"
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as f:
        json.dump(hasil, f, ensure_ascii=False, indent=1, default=float)
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as f:
        f.write(md)
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as f:
            f.write(md)
    print(md)
    print(f"Selesai {time.time() - t0:.0f} dtk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
