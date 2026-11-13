#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKTEST SHORT SELLING (cerminan rumus beli)
============================================
Data harian Binance sejak 2020 (ikut bear market 2022 & 2025–26), koin top CMC.

Strategi short yang diuji (semua memakai candle harian yang sudah tutup):
  awal_stage4     : hari pertama Stage 4 terkonfirmasi            (cermin "Awal Stage 2")
  jebol_puncak    : jebol lantai kisaran puncak + volume ≥1,5×      (cermin "Tembus atap dasar")
  pantul_fib      : Stage 4, harga memantul ke zona Fibonacci 0,382–0,618 dari penurunan terakhir
                    lalu candle merah                              (cermin "Pullback Fibonacci")
  acak            : short di hari acak (pembanding)
  radar           : sinyal 🔴 radar dari backtest/sinyal.csv.gz (Okt 2024–Okt 2026)

Aturan tutup posisi (cermin rencana beli):
  rencana   : TP1 −5% (tutup 50%, SL pindah ke harga masuk), TP2 = target pola / −10%, SL +12%, maks 30 hari
  sl8       : sama, SL +8%
  tetap_5_5 : TP −5% / SL +5% (tutup semua)
  ikuti     : tutup saat harga tutup di atas MA50 (≥3 hari) atau SL +12%, maks 180 hari

Biaya (konservatif, bisa diubah di config "biaya_short"): fee buka 0,1% + pajak 0,21% (posisi dibuka dengan menjual)
+ fee tutup 0,1% + funding 0,03%/hari. Pembanding biaya futures murah: 0,05% + 0,05%, tanpa pajak & funding.

Hasil: backtest_short/LAPORAN.md, backtest_short/hasil.json
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

import scanner as S
import siklus as SK
import strategi as ST
from siklus_4tahun import harian

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_short")
HARI_MIN, TAHAN, TAHAN_IKUTI, JEDA = 260, 30, 180, 10
KELUAR = {
    "rencana": ("TP1 −5% (tutup 50%), TP2 target/−10%, SL +12%", dict(ST.DEFAULT_RENCANA)),
    "sl8": ("TP1 −5% (tutup 50%), TP2 target/−10%, SL +8%", dict(ST.DEFAULT_RENCANA, sl_persen=8)),
    "tetap_5_5": ("TP −5% / SL +5% (tutup semua)", dict(ST.DEFAULT_RENCANA, tp1_persen=5, sl_persen=5, porsi_tp1=1)),
    "ikuti": ("Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari)", None),
}
EVENT = {"awal_stage4": "Hari pertama Stage 4 terkonfirmasi",
         "jebol_puncak": "Jebol lantai puncak (Stage 3→4) + volume ≥1,5×",
         "pantul_fib": "Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah",
         "acak": "Short hari acak (pembanding)"}
PASAR = {"BTC tren turun": lambda d: d[d["rezim"] == "turun"],
         "BTC tidak tren naik": lambda d: d[d["rezim"] != "naik"],
         "semua kondisi": lambda d: d}
MEME = {"bukan meme": lambda d: d[~d["meme"]], "termasuk meme": lambda d: d}
BIAYA_KONS = dict(fee_buka=0.1, pajak=0.21, fee_tutup=0.1, funding_harian=0.03)
BIAYA_FUT = dict(fee_buka=0.05, pajak=0.0, fee_tutup=0.05, funding_harian=0.0)


def bersih(pnl, hari, B):
    """pnl = untung short dalam % (harga turun = positif)."""
    return pnl - B["fee_buka"] - B["pajak"] - B["fee_tutup"] * (1 - pnl / 100) - B["funding_harian"] * hari


def ikuti_short(c, h, ma_s, t, n):
    e = c[t]
    sl = e * 1.12
    akhir = min(n - 1, t + TAHAN_IKUTI)
    for k in range(t + 1, akhir + 1):
        if h[k] >= sl:
            return (1 - sl / e) * 100, k - t
        if k - t >= 3 and np.isfinite(ma_s[k]) and c[k] > ma_s[k]:
            return (1 - c[k] / e) * 100, k - t
    return (1 - c[akhir] / e) * 100, akhir - t


def proses(job):
    sym, meme, d, rezim = job
    n = len(d)
    o, h, l, c, v = (d[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close", "volume"))
    tgl = d.index.strftime("%Y-%m-%d").to_numpy()
    F = SK.hitung(o, h, l, c, v)
    st = F["stage"]
    if "R" not in F:
        return []
    R, Sb, vr, ma_l, ma_s = F["R"], F["S"], F["vol_rel"], F["ma_l"], F["ma_s"]
    out, jeda = [], {}
    for t in range(HARI_MIN, n - TAHAN):
        if st[t] == 0:
            continue
        ev = []
        if t % 5 == 0:
            ev.append(("acak", None, None))
        if st[t] == 4 and st[t - 1] != 4:
            ev.append(("awal_stage4", None, None))
        was3 = bool((st[max(0, t - 10):t + 1] == 3).any())
        if (was3 and st[t] in (3, 4) and np.isfinite(Sb[t]) and np.isfinite(Sb[t - 1]) and c[t] < Sb[t]
                and c[t - 1] >= Sb[t - 1] and vr[t] >= 1.5 and c[t] < ma_l[t] and R[t] / Sb[t] - 1 <= 0.6):
            ev.append(("jebol_puncak", Sb[t] - (R[t] - Sb[t]), R[t]))
        if st[t] == 4 and c[t] / ma_l[t] - 1 > -0.45 and c[t] < o[t] and t >= 90:
            a = t - 59
            il = a + int(np.argmin(l[a:t + 1]))
            b = max(0, il - 90)
            ih = b + int(np.argmax(h[b:il + 1]))
            lo, hi = float(l[il]), float(h[ih])
            if lo > 0 and hi / lo - 1 >= 0.15 and ih < il < t:
                f382, f618 = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
                if f382 <= c[t] <= f618 and h[t] >= f382:
                    ev.append(("pantul_fib", lo, lo + (hi - lo) * 0.786))
        for nama, tgt, bt in ev:
            if nama != "acak":
                if t <= jeda.get(nama, -1):
                    continue
                jeda[nama] = t + JEDA
            rec = dict(tanggal=tgl[t], symbol=sym, meme=meme, rezim=rezim.get(tgl[t], "netral"), stage=int(st[t]),
                       event=nama)
            for k, (_, Rn) in KELUAR.items():
                if Rn is None:
                    p, hr = ikuti_short(c, h, ma_s, t, n)
                else:
                    plan = ST.rencana(float(c[t]), "turun", tgt, bt, None, Rn)
                    res = ST.simulasi(plan, h[t + 1:t + 1 + TAHAN], l[t + 1:t + 1 + TAHAN], c[t + 1:t + 1 + TAHAN])
                    p, hr = res["pnl"], res["hari"]
                rec[f"{k}_pnl"], rec[f"{k}_hari"] = round(float(p), 3), int(hr)
            out.append(rec)
    return out


def ringkas(x: pd.Series) -> dict:
    x = x.dropna()
    if len(x) == 0:
        return dict(n=0)
    sd = float(x.std(ddof=1)) if len(x) > 1 else 0.0
    pos, neg = x[x > 0].sum(), -x[x < 0].sum()
    return dict(n=int(len(x)), menang=round(float((x > 0).mean() * 100), 1), rata=round(float(x.mean()), 2),
                median=round(float(x.median()), 2), pf=round(float(pos / neg), 2) if neg > 0 else None,
                t=round(float(x.mean() / (sd / np.sqrt(len(x)))), 2) if sd > 0 else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mulai", default="2020-01-01")
    ap.add_argument("--koin", type=int, default=150)
    args = ap.parse_args()
    t0 = time.time()
    now = datetime.now(timezone.utc)
    cfg, state = S.load_config(), S.load_state()
    B_cfg = dict(BIAYA_KONS, **(cfg.get("biaya_short") or {}))
    bn = S.Binance()
    rank_list, src = S.ambil_ranking(cfg, state, now)
    tick = bn.tickers(cfg["quote"])
    koin = [("BTCUSDT", "BTC", False)]
    for c in sorted(rank_list, key=lambda x: x["rank"]):
        b = S.ALIAS_BINANCE.get(c["symbol"], c["symbol"])
        if c.get("stabil") or c["symbol"] in cfg["abaikan"] or c["symbol"] == "BTC" or b not in tick:
            continue
        koin.append((tick[b]["symbol"], c["symbol"], bool(c.get("meme")) or ST.is_meme(c["symbol"])))
    koin = koin[:args.koin + 1]
    mulai = pd.Timestamp(args.mulai, tz="UTC")
    data = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(harian, bn, k[0], mulai): k for k in koin}
        for f in as_completed(futs):
            try:
                d = f.result()
                if len(d) > HARI_MIN + TAHAN:
                    data[futs[f][1]] = (futs[f][2], d)
            except Exception as e:
                print("  ! gagal", futs[f][1], e)
    btc = data["BTC"][1]
    rezim = dict(zip(btc.index.strftime("%Y-%m-%d"), ST.rezim_series(btc["close"].to_numpy())))
    print(f"Data {len(data)} koin ({time.time() - t0:.0f} dtk)")
    jobs = [(sym, meme, d, rezim) for sym, (meme, d) in data.items()]
    rows = []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for out in ex.map(proses, jobs, chunksize=2):
            rows.extend(out)
    df = pd.DataFrame(rows)
    print(f"{len(df)} baris ({time.time() - t0:.0f} dtk)")
    for k in KELUAR:
        df[f"{k}_kons"] = bersih(df[f"{k}_pnl"], df[f"{k}_hari"], B_cfg)
        df[f"{k}_fut"] = bersih(df[f"{k}_pnl"], df[f"{k}_hari"], BIAYA_FUT)
    d0, d1 = df["tanggal"].min(), df["tanggal"].max()
    mid = (pd.Timestamp(d0) + (pd.Timestamp(d1) - pd.Timestamp(d0)) / 2).strftime("%Y-%m-%d")
    df["minggu"] = pd.to_datetime(df["tanggal"]).dt.to_period("W").astype(str)
    acak = df[df["event"] == "acak"]

    hasil = dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), dari=d0, sampai=d1, mid=mid,
                 koin=len(data), biaya=B_cfg, biaya_futures=BIAYA_FUT, baris=[])
    for ev in EVENT:
        g0 = df[df["event"] == ev]
        for mn, mf in MEME.items():
            for pn, pf in PASAR.items():
                g = pf(mf(g0))
                base = pf(mf(acak)).groupby("minggu")
                for k, (ket, _) in KELUAR.items():
                    kol = f"{k}_kons"
                    r = ringkas(g[kol])
                    if not r["n"]:
                        continue
                    ex_ = (g[kol] - g["minggu"].map(base[kol].mean())).dropna()
                    r.update(event=ev, meme=mn, pasar=pn, keluar=k, ket=ket,
                             p1=ringkas(g.loc[g["tanggal"] < mid, kol]), p2=ringkas(g.loc[g["tanggal"] >= mid, kol]),
                             futures=ringkas(g[f"{k}_fut"]), lebih_acak=ringkas(ex_),
                             hari=round(float(g[f"{k}_hari"].mean()), 1))
                    hasil["baris"].append(r)
    lolos = [r for r in hasil["baris"] if r["event"] != "acak" and r["n"] >= 30
             and r["p1"].get("n", 0) >= 15 and r["p2"].get("n", 0) >= 15
             and r["p1"]["rata"] > 0 and r["p2"]["rata"] > 0 and (r["lebih_acak"].get("rata") or -1) > 0]
    hasil["lolos"] = sorted(lolos, key=lambda r: -min(r["p1"]["rata"], r["p2"]["rata"]))

    # Rincian per tahun untuk strategi terbaik (cek apakah untungnya merata, bukan dari 1–2 bulan saja)
    hasil["rinci"] = []
    pilih = hasil["lolos"][:1] + [r for r in hasil["lolos"] if r["keluar"] == "rencana"][:2]
    for b in {(r["event"], r["pasar"], r["meme"], r["keluar"]): r for r in pilih}.values():
        g = PASAR[b["pasar"]](MEME[b["meme"]](df[df["event"] == b["event"]]))
        kol = f"{b['keluar']}_kons"
        th = [dict(ringkas(gg[kol]), tahun=t) for t, gg in g.groupby(g["tanggal"].str[:4])]
        bln = g.groupby(g["tanggal"].str[:7])[kol].agg(["count", "sum"])
        hasil["rinci"].append(dict(judul=f"{EVENT[b['event']]} · {b['pasar']} · {b['meme']} · {b['ket']}", per_tahun=th,
                                   bulan_aktif=int(len(bln)), maks_sinyal_sebulan=int(bln["count"].max()),
                                   porsi_3_bulan_teratas=round(float(bln["sum"].nlargest(3).sum() / bln["sum"].sum() * 100), 1)
                                   if bln["sum"].sum() > 0 else None))
    df[df["event"] != "acak"].to_csv(os.path.join(OUT, "sinyal.csv.gz"), index=False, compression="gzip")

    # Sinyal 🔴 radar (dari backtest utama): balik ke pnl mentah lalu hitung biaya short
    radar = []
    p = os.path.join(os.path.dirname(OUT), "backtest", "sinyal.csv.gz")
    if os.path.exists(p):
        sg = pd.read_csv(p)
        sg = sg[sg["kelas"] == "turun"].copy()
        Bsp = ST.DEFAULT_BIAYA
        a, b = Bsp["fee_beli_persen"] + Bsp["fee_jual_persen"] + Bsp["pajak_jual_persen"], \
            (Bsp["fee_jual_persen"] + Bsp["pajak_jual_persen"]) / 100
        mid_r = (pd.Timestamp(sg["tanggal"].min()) + (pd.Timestamp(sg["tanggal"].max()) - pd.Timestamp(sg["tanggal"].min())) / 2).strftime("%Y-%m-%d")
        for k in ("pola_tp5_sl12", "pola_sl12", "tetap_5_5", "pola_tp5"):
            if f"{k}_bersih" not in sg:
                continue
            pnl = (sg[f"{k}_bersih"] + a) / (1 - b)
            sg[f"{k}_kons"] = bersih(pnl, sg[f"{k}_hari"], B_cfg)
            for mn, mf in MEME.items():
                for pn, pf in PASAR.items():
                    g = pf(mf(sg))
                    r = ringkas(g[f"{k}_kons"])
                    if r["n"]:
                        r.update(aturan=k, meme=mn, pasar=pn, p1=ringkas(g.loc[g["tanggal"] < mid_r, f"{k}_kons"]),
                                 p2=ringkas(g.loc[g["tanggal"] >= mid_r, f"{k}_kons"]))
                        radar.append(r)
    hasil["radar"] = radar

    # Laporan
    f = lambda q: f"{q['rata']:+.2f}% ({q['n']}, menang {q['menang']}%)" if q.get("n") else "-"  # noqa: E731
    L = ["# 🔴 Backtest Short Selling", "",
         f"Dibuat {hasil['dibuat_wib']} · {len(data)} koin · {d0} s/d {d1} · periode 1 < {mid} ≤ periode 2", "",
         f"Biaya konservatif: fee buka {B_cfg['fee_buka']}% + pajak {B_cfg['pajak']}% + fee tutup {B_cfg['fee_tutup']}% "
         f"+ funding {B_cfg['funding_harian']}%/hari. Kolom 'Futures murah' = 0,05% + 0,05% tanpa pajak & funding.", "",
         "Syarat lolos: ≥30 sinyal, ≥15 per periode, rata-rata positif di KEDUA periode, dan lebih baik dari short acak di minggu yang sama.",
         "", "## Strategi yang lolos", ""]
    if hasil["lolos"]:
        for r in hasil["lolos"][:12]:
            L.append(f"- **{EVENT[r['event']]} · {r['pasar']} · {r['meme']} · {r['ket']}** → {r['n']} sinyal, menang {r['menang']}%, "
                     f"rata-rata {r['rata']:+.2f}% (P1 {f(r['p1'])} · P2 {f(r['p2'])}) · lebih baik dari acak {r['lebih_acak']['rata']:+.2f}% "
                     f"(t {r['lebih_acak'].get('t')})")
    else:
        L.append("Tidak ada.")
    for k in hasil["rinci"]:
        L += ["", f"### Per tahun — {k['judul']}", "", "| Tahun | Sinyal | Menang | Rata-rata |", "|---|---|---|---|"]
        L += [f"| {r['tahun']} | {r['n']} | {r['menang']}% | {r['rata']:+.2f}% |" for r in k["per_tahun"]]
        L += ["", f"Aktif di {k['bulan_aktif']} bulan · maks {k['maks_sinyal_sebulan']} sinyal sebulan · "
                  f"3 bulan terbaik menyumbang {k['porsi_3_bulan_teratas']}% total untung"]
    L += ["", "## Semua kombinasi", "",
          "| Strategi | Pasar | Meme | Aturan | Sinyal | Menang | Rata-rata | PF | Periode 1 | Periode 2 | vs acak | Futures murah |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in hasil["baris"]:
        L.append(f"| {EVENT[r['event']]} | {r['pasar']} | {r['meme']} | {r['ket']} | {r['n']} | {r['menang']}% | {r['rata']:+.2f}% | "
                 f"{r['pf'] if r['pf'] is not None else '-'} | {f(r['p1'])} | {f(r['p2'])} | "
                 f"{(r['lebih_acak'].get('rata') or 0):+.2f}% | {r['futures'].get('rata', 0):+.2f}% |")
    L += ["", "## Sinyal 🔴 radar sebagai short (Okt 2024–Okt 2026, biaya konservatif)", "",
          "| Aturan | Pasar | Meme | Sinyal | Menang | Rata-rata | Periode 1 | Periode 2 |", "|---|---|---|---|---|---|---|---|"]
    for r in radar:
        L.append(f"| {r['aturan']} | {r['pasar']} | {r['meme']} | {r['n']} | {r['menang']}% | {r['rata']:+.2f}% | {f(r['p1'])} | {f(r['p2'])} |")
    L += ["", "## Catatan", "",
          "- Koin = top CMC saat ini. Koin yang sudah mati tidak ikut, padahal itu short terbaik → hasil short cenderung terlalu jelek, bukan terlalu bagus.",
          "- Funding futures bisa menguntungkan short (saat pasar optimis) atau membebani (saat pasar takut). Di sini dianggap selalu biaya.",
          "- Short memakai leverage berisiko likuidasi. Hasil di atas tanpa leverage (1×)."]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as fh:
        json.dump(hasil, fh, ensure_ascii=False, indent=1, default=str)
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as fh:
            fh.write("\n".join(L[:40]) + "\n")
    print("\n".join(L[:30]))
    print(f"Selesai {time.time() - t0:.0f} dtk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
