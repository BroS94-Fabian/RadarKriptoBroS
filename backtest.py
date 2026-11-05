#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKTEST RADAR KRIPTO
=====================
Menjalankan mesin analisa yang SAMA dengan radar pada data harian historis
(±2,7 tahun, koin top CoinMarketCap yang ada di Binance), hari demi hari,
lalu mensimulasikan berbagai aturan jual dan menghitung hasil bersih
(setelah biaya beli/jual & pajak jual).

Hasil: backtest/LAPORAN.md, backtest/hasil.json, backtest/sinyal.csv.gz

Keterbatasan (dijelaskan juga di laporan):
  - Data per jam tidak dipakai (profil volume & beli agresif dari candle harian,
    lonjakan volume 1 jam tidak ada).
  - Daftar koin = top 200 SAAT INI (survivorship bias: koin yang dulu besar lalu
    jatuh/hilang tidak ikut diuji → hasil cenderung sedikit terlalu bagus).
  - Masuk di harga penutupan hari sinyal; bila SL & TP tersentuh di candle yang
    sama dianggap SL dulu.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import analisa as A
import scanner as S
import siklus as SK
import strategi as ST

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest")
HARI_MIN = 260      # butuh MA200 + ruang analisa
JENDELA = 400       # jumlah candle yang dianalisa per hari (sama seperti radar)
JEDA = 10           # setelah sinyal, koin & arah yang sama tidak dihitung lagi selama 10 hari
TAHAN = 30          # horizon maksimum simulasi
TAHAN_SIKLUS = 180  # horizon maksimum aturan "ikuti siklus"

# nama: (keterangan, rencana, pakai target/batal pola)
ATURAN = {
    "pola": ("Target & batal pola (tanpa TP1)",
             dict(mode="persen", tp1_persen=5, sl_persen=99, porsi_tp1=0, maks_hari=30), True),
    "pola_sl8": ("Target pola, SL maks −8%", dict(mode="persen", tp1_persen=5, sl_persen=8, porsi_tp1=0, maks_hari=30), True),
    "pola_sl12": ("Target pola, SL maks −12%", dict(mode="persen", tp1_persen=5, sl_persen=12, porsi_tp1=0, maks_hari=30), True),
    "pola_sl15": ("Target pola, SL maks −15%", dict(mode="persen", tp1_persen=5, sl_persen=15, porsi_tp1=0, maks_hari=30), True),
    "pola_tp5": ("50% di +5%, sisa ke target pola, SL batal pola → impas", dict(mode="persen", tp1_persen=5, sl_persen=99, porsi_tp1=0.5, maks_hari=30), True),
    "pola_tp10": ("50% di +10%, sisa ke target pola, SL batal pola → impas", dict(mode="persen", tp1_persen=10, sl_persen=99, porsi_tp1=0.5, maks_hari=30), True),
    "pola_tp5_sl8": ("50% di +5%, sisa ke target pola, SL maks −8% → impas", dict(mode="persen", tp1_persen=5, sl_persen=8, porsi_tp1=0.5, maks_hari=30), True),
    "pola_tp5_sl12": ("50% di +5%, sisa ke target pola, SL maks −12% → impas", dict(mode="persen", tp1_persen=5, sl_persen=12, porsi_tp1=0.5, maks_hari=30), True),
    "pola_tp7_sl12": ("50% di +7%, sisa ke target pola, SL maks −12% → impas", dict(mode="persen", tp1_persen=7, sl_persen=12, porsi_tp1=0.5, maks_hari=30), True),
    "tetap_3_3": ("TP +3% / SL −3% (jual semua)", dict(mode="persen", tp1_persen=3, sl_persen=3, porsi_tp1=1, maks_hari=30), False),
    "tetap_5_5": ("TP +5% / SL −5% (jual semua)", dict(mode="persen", tp1_persen=5, sl_persen=5, porsi_tp1=1, maks_hari=30), False),
    "tetap_8_4": ("TP +8% / SL −4% (jual semua)", dict(mode="persen", tp1_persen=8, sl_persen=4, porsi_tp1=1, maks_hari=30), False),
    "tetap_10_5": ("TP +10% / SL −5% (jual semua)", dict(mode="persen", tp1_persen=10, sl_persen=5, porsi_tp1=1, maks_hari=30), False),
    "atr_2_1": ("TP 2×ATR / SL 1×ATR", dict(mode="atr", tp1_atr=2, sl_atr=1, porsi_tp1=1, maks_hari=30), False),
    "atr_3_15": ("TP 3×ATR / SL 1,5×ATR", dict(mode="atr", tp1_atr=3, sl_atr=1.5, porsi_tp1=1, maks_hari=30), False),
    "sebagian_3_3": ("50% di +3%, sisa ke target pola, SL −3% → impas", dict(mode="persen", tp1_persen=3, sl_persen=3, porsi_tp1=0.5, maks_hari=30), True),
    "sebagian_5_5": ("50% di +5%, sisa ke target pola, SL −5% → impas", dict(mode="persen", tp1_persen=5, sl_persen=5, porsi_tp1=0.5, maks_hari=30), True),
    "sebagian_atr": ("50% di 1,5×ATR, sisa ke target pola, SL 1,5×ATR → impas", dict(mode="atr", tp1_atr=1.5, sl_atr=1.5, porsi_tp1=0.5, maks_hari=30), True),
    "tahan_7": ("Tahan 7 hari (tanpa TP/SL)", dict(mode="persen", tp1_persen=1e6, sl_persen=99.9, porsi_tp1=0, maks_hari=7), False),
    "tahan_14": ("Tahan 14 hari (tanpa TP/SL)", dict(mode="persen", tp1_persen=1e6, sl_persen=99.9, porsi_tp1=0, maks_hari=14), False),
}


# --------------------------------------------------------------------------- #
# Simulasi per koin (jalan paralel)
# --------------------------------------------------------------------------- #
def proses_koin(job):
    sym, base, rank, meme, d, rezim, btc_close, cfg = job
    n = len(d)
    c = d["close"].to_numpy()
    tgl = d["time"].dt.strftime("%Y-%m-%d").to_numpy()
    out, jeda = [], {"naik": -1, "turun": -1}
    for t in range(HARI_MIN, n - TAHAN):
        w = d.iloc[max(0, t - JENDELA + 1):t + 1]
        info = dict(symbol=sym, base=base, name=base, rank=rank, meme=meme, bursa="Binance", price=float(c[t]),
                    chg24=float((c[t] / c[t - 1] - 1) * 100), qvol24=float(d["qvol"].iat[t]))
        try:
            r = A.analisa_koin(info, w, None, cfg)
        except Exception:
            continue
        if not r or r["kelas"] not in ("naik", "turun"):
            continue
        k = r["kelas"]
        if t <= jeda[k]:
            continue
        jeda[k] = t + JEDA
        P = r["pola_naik" if k == "naik" else "pola_turun"]
        fut = d.iloc[t + 1:t + 1 + TAHAN]
        hi, lo, cl = fut["high"].to_numpy(), fut["low"].to_numpy(), fut["close"].to_numpy()
        tgt = r["target"]["harga"] if r["target"] else None
        bt = r["batal"]["harga"] if r["batal"] else None
        atrp = r["indikator"]["atr_pct"]
        b0 = btc_close.get(tgl[t])
        b7 = btc_close.get(tgl[min(t + 7, n - 1)])
        rec = dict(tanggal=tgl[t], symbol=sym, base=base, rank=rank, meme=meme, kelas=k,
                   skor=r["skor_naik"] if k == "naik" else r["skor_turun"],
                   skor_lawan=r["skor_turun"] if k == "naik" else r["skor_naik"],
                   pola=P["nama"] if P else "-", status=P["status"] if P else "-",
                   target_pct=r["target"]["pct"] if r["target"] else None,
                   batal_pct=r["batal"]["pct"] if r["batal"] else None,
                   rsi=r["indikator"]["rsi"], atr_pct=atrp, posisi=r["akumulasi"]["posisi"],
                   rezim=rezim.get(tgl[t], "netral"), candle=r["candle"] or "-",
                   elliott=(r["elliott"]["arah"] if r["elliott"] else "-"),
                   chg7_koin=(c[min(t + 7, n - 1)] / c[t] - 1) * 100,
                   chg7_btc=((b7 / b0 - 1) * 100) if b0 and b7 else None)
        sk, ck = r.get("siklus") or {}, r.get("checklist") or {}
        rec.update(stage=int(sk.get("stage") or 0), fase=str(sk.get("fase", "0")),
                   vol_status=(sk.get("volume") or {}).get("status", "-"),
                   vol_arah=(sk.get("volume") or {}).get("arah") or "-",
                   checklist=ck.get("cocok"), checklist_lawan=ck.get("lawan"))
        for nama, (_, R, pakai_pola) in ATURAN.items():
            plan = ST.rencana(float(c[t]), k, tgt if pakai_pola else None, bt if pakai_pola else None, atrp, R)
            m = R["maks_hari"]
            res = ST.simulasi(plan, hi[:m], lo[:m], cl[:m])
            rec[f"{nama}_bersih"] = round(ST.bersih(res["pnl"], cfg.get("biaya")), 3)
            rec[f"{nama}_hasil"] = res["hasil"]
            rec[f"{nama}_hari"] = res["hari"]
        out.append(rec)
    return out, siklus_murni(sym, meme, d, rezim, cfg)


def ikuti_siklus(c, l, ma_s, t, n):
    """Keluar bila harga tutup di bawah MA50 (setelah ≥3 hari) atau kena SL −12%; maks 180 hari."""
    e = c[t]
    sl = e * 0.88
    akhir = min(n - 1, t + TAHAN_SIKLUS)
    for k in range(t + 1, akhir + 1):
        if l[k] <= sl:
            return (sl / e - 1) * 100, k - t, "kena SL"
        if k - t >= 3 and np.isfinite(ma_s[k]) and c[k] < ma_s[k]:
            return (c[k] / e - 1) * 100, k - t, "tutup < MA50"
    return (c[akhir] / e - 1) * 100, akhir - t, ("batas waktu" if akhir == t + TAHAN_SIKLUS else "data habis")


def siklus_murni(sym, meme, d, rezim, cfg):
    """Strategi berbasis stage saja (tanpa skor radar) + pembanding beli acak per stage."""
    n = len(d)
    o, h, l, c, v = (d[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close", "volume"))
    tgl = d["time"].dt.strftime("%Y-%m-%d").to_numpy()
    F = SK.hitung(o, h, l, c, v)
    st, R, Sb, vr, ma_l, ma_s = F["stage"], F.get("R"), F.get("S"), F.get("vol_rel"), F.get("ma_l"), F.get("ma_s")
    if R is None:
        return []
    Rn = ST.DEFAULT_RENCANA
    out, jeda = [], {}
    for t in range(HARI_MIN, n - TAHAN):
        if st[t] == 0:
            continue
        ev = []
        if t % 5 == 0:
            ev.append(("acak", None, None))
        was1 = bool((st[max(0, t - 10):t + 1] == 1).any())
        if (was1 and st[t] in (1, 2) and np.isfinite(R[t]) and np.isfinite(R[t - 1]) and c[t] > R[t]
                and c[t - 1] <= R[t - 1] and vr[t] >= 1.5 and c[t] > ma_l[t] and R[t] / Sb[t] - 1 <= 0.6):
            ev.append(("tembus_dasar", R[t] + (R[t] - Sb[t]), Sb[t]))
        if st[t] == 2 and st[t - 1] != 2:
            ev.append(("awal_stage2", None, None))
        if st[t] == 2 and c[t] / ma_l[t] - 1 < 0.8 and c[t] > o[t]:
            fb = SK.fibonacci(h, l, t, c[t])
            if fb and fb["posisi"] == "zona":
                ev.append(("pullback_fib", fb["swing_high"],
                           fb["swing_low"] + (fb["swing_high"] - fb["swing_low"]) * 0.214))
        for nama, tgt, bt in ev:
            if nama != "acak":
                if t <= jeda.get(nama, -1):
                    continue
                jeda[nama] = t + JEDA
            plan = ST.rencana(float(c[t]), "naik", tgt, bt, None, Rn)
            r1 = ST.simulasi(plan, h[t + 1:t + 1 + TAHAN], l[t + 1:t + 1 + TAHAN], c[t + 1:t + 1 + TAHAN])
            p2, hari2, hs2 = ikuti_siklus(c, l, ma_s, t, n)
            out.append(dict(tanggal=tgl[t], symbol=sym, meme=meme, rezim=rezim.get(tgl[t], "netral"),
                            stage=int(st[t]), event=nama,
                            rencana_bersih=round(ST.bersih(r1["pnl"], cfg.get("biaya")), 3), rencana_hari=r1["hari"],
                            siklus_bersih=round(ST.bersih(p2, cfg.get("biaya")), 3), siklus_hari=hari2,
                            siklus_hasil=hs2))
    return out


# --------------------------------------------------------------------------- #
# Statistik & laporan
# --------------------------------------------------------------------------- #
def statistik(df: pd.DataFrame, kol: str) -> dict:
    x = df[kol].dropna()
    if len(x) == 0:
        return dict(n=0)
    pos, neg = x[x > 0].sum(), -x[x < 0].sum()
    hari = df[kol.replace("_bersih", "_hari")]
    return dict(n=int(len(x)), menang=round(float((x > 0).mean() * 100), 1), rata=round(float(x.mean()), 2),
                median=round(float(x.median()), 2), total=round(float(x.sum()), 1),
                pf=round(float(pos / neg), 2) if neg > 0 else None, hari=round(float(hari.mean()), 1))


def kelompok(df, kol, by, urut=None):
    rows = []
    for key, g in df.groupby(by, dropna=False):
        st = statistik(g, kol)
        st["grup"] = str(key)
        rows.append(st)
    rows.sort(key=lambda r: (urut.index(r["grup"]) if urut and r["grup"] in urut else 99, -r["n"]))
    return rows


def ember_skor(s):
    return "50–54" if s < 55 else "55–59" if s < 60 else "60–64" if s < 65 else "65+"


def ember_rank(r):
    return "1–50" if r <= 50 else "51–100" if r <= 100 else "101–200"


FILTER = {
    "tanpa filter": lambda d: d,
    "filter pasar BTC": lambda d: d[d["rezim"] != "turun"],
    "tanpa meme": lambda d: d[~d["meme"]],
    "meme butuh skor ≥60": lambda d: d[~d["meme"] | (d["skor"] >= 60)],
    "hanya breakout": lambda d: d[d["status"] == "breakout"],
    "pasar BTC + tanpa meme": lambda d: d[(d["rezim"] != "turun") & ~d["meme"]],
    "pasar BTC + meme ≥60": lambda d: d[(d["rezim"] != "turun") & (~d["meme"] | (d["skor"] >= 60))],
    "pasar BTC naik saja": lambda d: d[d["rezim"] == "naik"],
    "pasar BTC naik + tanpa meme": lambda d: d[(d["rezim"] == "naik") & ~d["meme"]],
    "pasar BTC + tanpa meme + breakout": lambda d: d[(d["rezim"] != "turun") & ~d["meme"] & (d["status"] == "breakout")],
    "skor ≥60": lambda d: d[d["skor"] >= 60],
    "pasar BTC naik + tanpa meme + skor ≥55": lambda d: d[(d["rezim"] == "naik") & ~d["meme"] & (d["skor"] >= 55)],
    "pasar BTC naik + tanpa meme + breakout": lambda d: d[(d["rezim"] == "naik") & ~d["meme"] & (d["status"] == "breakout")],
    "pasar BTC + tanpa meme + skor ≥55": lambda d: d[(d["rezim"] != "turun") & ~d["meme"] & (d["skor"] >= 55)],
}
FILTER_CFG = {
    "tanpa filter": dict(filter_pasar=False, filter_meme=False, wajib_breakout=False),
    "filter pasar BTC": dict(filter_pasar=True, filter_meme=False, wajib_breakout=False),
    "tanpa meme": dict(filter_pasar=False, filter_meme="abaikan", wajib_breakout=False),
    "meme butuh skor ≥60": dict(filter_pasar=False, filter_meme="ketat", wajib_breakout=False),
    "hanya breakout": dict(filter_pasar=False, filter_meme=False, wajib_breakout=True),
    "pasar BTC + tanpa meme": dict(filter_pasar=True, filter_meme="abaikan", wajib_breakout=False),
    "pasar BTC + meme ≥60": dict(filter_pasar=True, filter_meme="ketat", wajib_breakout=False),
    "pasar BTC + tanpa meme + breakout": dict(filter_pasar=True, filter_meme="abaikan", wajib_breakout=True),
}


def tabel_md(rows, judul_grup="Grup"):
    L = [f"| {judul_grup} | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if not r.get("n"):
            continue
        L.append(f"| {r['grup']} | {r['n']} | {r['menang']}% | {r['rata']:+.2f}% | {r['median']:+.2f}% | "
                 f"{r['total']:+.1f}% | {r['pf'] if r['pf'] is not None else '-'} | {r['hari']} |")
    return L


def laporan(df: pd.DataFrame, meta: dict) -> tuple[dict, str]:
    naik, turun = df[df["kelas"] == "naik"], df[df["kelas"] == "turun"]
    hasil = dict(meta=meta, aturan={k: v[0] for k, v in ATURAN.items()})
    hasil["aturan_naik"] = [dict(statistik(naik, f"{k}_bersih"), grup=k) for k in ATURAN]
    hasil["aturan_turun"] = [dict(statistik(turun, f"{k}_bersih"), grup=k) for k in ATURAN]
    cand = [r for r in hasil["aturan_naik"] if r.get("n", 0) >= 30 and not r["grup"].startswith("tahan")]
    terbaik = max(cand, key=lambda r: r["rata"])["grup"] if cand else "pola"
    hasil["terbaik_naik"] = terbaik
    kol = f"{terbaik}_bersih"
    nk = naik.assign(ember_skor=naik["skor"].map(ember_skor), ember_rank=naik["rank"].map(ember_rank),
                     meme_lbl=naik["meme"].map({True: "meme", False: "bukan meme"}))
    hasil["rinci"] = {
        "Kondisi pasar BTC": kelompok(nk, kol, "rezim", ["naik", "netral", "turun"]),
        "Meme coin": kelompok(nk, kol, "meme_lbl"),
        "Status pola": kelompok(nk, kol, "status", ["breakout", "terbentuk", "uji", "-"]),
        "Jenis pola": kelompok(nk, kol, "pola"),
        "Skor naik": kelompok(nk, kol, "ember_skor", ["50–54", "55–59", "60–64", "65+"]),
        "Peringkat CMC": kelompok(nk, kol, "ember_rank", ["1–50", "51–100", "101–200"]),
        "Posisi zona akumulasi": kelompok(nk, kol, "posisi", ["bawah", "dalam-bawah", "dalam-atas", "atas"]),
    }
    filt = []
    for nama, f in FILTER.items():
        sub = f(naik)
        for k in dict.fromkeys((terbaik, "pola", "pola_sl12", "pola_tp5", "pola_tp5_sl12", "pola_tp5_sl8")):
            if k in ATURAN:
                st = statistik(sub, f"{k}_bersih")
                st.update(grup=nama, aturan=k)
                filt.append(st)
    hasil["filter_naik"] = filt
    base_n = max(1, len(naik))
    pilihan = [r for r in filt if r.get("n", 0) >= max(30, 0.1 * base_n)]
    best = max(pilihan, key=lambda r: r["rata"]) if pilihan else None
    hasil["rekomendasi"] = best
    hasil["filter_turun"] = [dict(statistik(turun if nm == "tanpa filter" else turun[turun["rezim"] != "naik"],
                                            f"{terbaik}_bersih"), grup=nm)
                             for nm in ("tanpa filter", "filter pasar BTC")]
    t7 = naik.dropna(subset=["chg7_btc"])
    hasil["pembanding_btc"] = dict(n=int(len(t7)), koin_7h=round(float(t7["chg7_koin"].mean()), 2) if len(t7) else None,
                                   btc_7h=round(float(t7["chg7_btc"].mean()), 2) if len(t7) else None,
                                   lebih_baik=round(float((t7["chg7_koin"] > t7["chg7_btc"]).mean() * 100), 1) if len(t7) else None)

    # ---------- Markdown ----------
    L = ["# 🧪 Laporan Backtest Radar Kripto", "",
         f"Dibuat: {meta['dibuat_wib']} · Periode: {meta['dari']} s/d {meta['sampai']} · "
         f"{meta['koin']} koin top CMC di Binance · {len(df)} sinyal ({len(naik)} naik, {len(turun)} turun)", "",
         "Hasil **bersih** per sinyal (sudah dipotong biaya beli 0,1%, jual 0,1%, pajak jual 0,21%). "
         "Satu sinyal = satu posisi dengan modal sama.", "",
         "## 1. Sinyal 🟢 potensi naik — perbandingan aturan jual", ""]
    L += tabel_md([dict(r, grup=f"{ATURAN[r['grup']][0]}") for r in hasil["aturan_naik"]], "Aturan jual")
    L += ["", f"**Aturan jual terbaik (rata-rata bersih tertinggi): {ATURAN[terbaik][0]}**", "",
          f"## 2. Rincian sinyal naik (aturan: {ATURAN[terbaik][0]})", ""]
    for judul, rows in hasil["rinci"].items():
        L += [f"### {judul}", ""] + tabel_md(rows, judul) + [""]
    L += ["## 3. Pengaruh filter (sinyal naik)", ""]
    for k in dict.fromkeys((terbaik, "pola", "pola_sl12", "pola_tp5", "pola_tp5_sl12", "pola_tp5_sl8")):
        if k not in ATURAN:
            continue
        L += [f"### Aturan: {ATURAN[k][0]}", ""] + tabel_md([r for r in filt if r["aturan"] == k], "Filter") + [""]
    if best:
        L += [f"**Kombinasi terbaik:** {best['grup']} + {ATURAN[best['aturan']][0]} → {best['n']} sinyal, "
              f"menang {best['menang']}%, rata-rata bersih {best['rata']:+.2f}% per sinyal.", ""]
    L += ["## 4. Sinyal 🔴 potensi turun (sebagai posisi short)", ""]
    L += tabel_md([dict(r, grup=f"{ATURAN[r['grup']][0]}") for r in hasil["aturan_turun"]], "Aturan jual")
    L += ["", "Dengan filter pasar BTC (tidak short saat BTC tren naik):", ""] + tabel_md(hasil["filter_turun"], "Filter")
    pb = hasil["pembanding_btc"]
    L += ["", "## 5. Dibanding BTC (tahan 7 hari)", "",
          f"Rata-rata koin sinyal naik dalam 7 hari: {pb['koin_7h']:+.2f}% · BTC di periode yang sama: {pb['btc_7h']:+.2f}% · "
          f"lebih baik dari BTC: {pb['lebih_baik']}% sinyal." if pb["n"] else "Data BTC tidak tersedia.", "",
          "## Keterbatasan", "",
          "- Data per jam tidak dipakai: zona akumulasi & porsi beli agresif dihitung dari candle harian; jejak whale 1 jam tidak ikut.",
          "- Daftar koin = top 200 saat ini (survivorship bias) → hasil cenderung sedikit terlalu bagus.",
          "- Masuk di harga penutupan hari sinyal; bila SL & TP tersentuh di candle yang sama dianggap SL dulu.",
          "- Hasil masa lalu tidak menjamin hasil masa depan."]
    return hasil, "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# Siklus 4 stage
# --------------------------------------------------------------------------- #
def ringkas(x: pd.Series, hari: pd.Series | None = None) -> dict:
    x = x.dropna()
    if len(x) == 0:
        return dict(n=0)
    pos, neg = x[x > 0].sum(), -x[x < 0].sum()
    sd = float(x.std(ddof=1)) if len(x) > 1 else 0.0
    return dict(n=int(len(x)), menang=round(float((x > 0).mean() * 100), 1), rata=round(float(x.mean()), 2),
                median=round(float(x.median()), 2), pf=round(float(pos / neg), 2) if neg > 0 else None,
                t=round(float(x.mean() / (sd / np.sqrt(len(x)))), 2) if sd > 0 else None,
                hari=round(float(hari.loc[x.index].mean()), 1) if hari is not None else None)


def per_periode(df: pd.DataFrame, kol: str, kol_hari: str, mid: str, grup: str, **extra) -> dict:
    r = ringkas(df[kol], df[kol_hari])
    r.update(grup=grup, **extra)
    r["p1"] = ringkas(df.loc[df["tanggal"] < mid, kol])
    r["p2"] = ringkas(df.loc[df["tanggal"] >= mid, kol])
    return r


VAR_STAGE = {
    "tanpa filter stage": lambda d: d,
    "Stage 1 atau 2": lambda d: d[d["stage"].isin([1, 2])],
    "Stage 2 saja": lambda d: d[d["stage"] == 2],
    "Stage 1 saja": lambda d: d[d["stage"] == 1],
    "bukan Stage 4": lambda d: d[d["stage"] != 4],
    "bukan Stage 3/4": lambda d: d[~d["stage"].isin([3, 4])],
    "fase ideal (akhir dasar, 1→2, awal/tengah naik)": lambda d: d[d["fase"].isin(["1-akhir", "1→2", "2-awal", "2"])],
    "checklist ≥4/6": lambda d: d[d["checklist"] >= 4],
    "checklist ≥5/6": lambda d: d[d["checklist"] >= 5],
    "volume tidak berlawanan": lambda d: d[d["vol_arah"] != "turun"],
    "Stage 1/2 + checklist ≥4": lambda d: d[d["stage"].isin([1, 2]) & (d["checklist"] >= 4)],
}
EVENT = {"tembus_dasar": "Tembus atap dasar (Stage 1→2) + volume ≥1,5×",
         "awal_stage2": "Hari pertama Stage 2 terkonfirmasi",
         "pullback_fib": "Pullback Stage 2 ke zona Fibonacci 0,382–0,618 + candle hijau",
         "acak": "Beli hari acak (pembanding)"}
PASAR = {"semua kondisi": lambda d: d, "BTC tidak tren turun": lambda d: d[d["rezim"] != "turun"],
         "BTC tren naik": lambda d: d[d["rezim"] == "naik"]}


def tabel_periode(rows, judul):
    L = [f"| {judul} | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |",
         "|---|---|---|---|---|---|---|---|"]
    f = lambda q: f"{q['rata']:+.2f}% ({q['n']}, menang {q['menang']}%)" if q.get("n") else "-"  # noqa: E731
    for r in rows:
        if not r.get("n"):
            continue
        L.append(f"| {r['grup']} | {r['n']} | {r['menang']}% | {r['rata']:+.2f}% | {r['pf'] if r['pf'] is not None else '-'} | "
                 f"{r['t'] if r['t'] is not None else '-'} | {f(r['p1'])} | {f(r['p2'])} |")
    return L


def laporan_siklus(df: pd.DataFrame, dsik: pd.DataFrame, meta: dict) -> tuple[dict, str]:
    d0, d1 = pd.Timestamp(meta["dari"]), pd.Timestamp(meta["sampai"])
    mid = (d0 + (d1 - d0) / 2).strftime("%Y-%m-%d")
    H = dict(mid=mid, periode1=f"{meta['dari']} – {mid}", periode2=f"{mid} – {meta['sampai']}")
    naik = df[(df["kelas"] == "naik")].copy()
    naik["checklist"] = naik["checklist"].fillna(0)
    dflt = naik[(naik["rezim"] == "naik") & ~naik["meme"]]
    L = ["## 6. Siklus 4 stage (Stage 1 Dasar → 2 Naik → 3 Puncak → 4 Turun)", "",
         f"Periode 1 = {H['periode1']} · Periode 2 = {H['periode2']}. Filter yang baik harus positif di **kedua** periode.", ""]
    H["radar"] = {}
    for kol, judul in (("pola_tp5_sl12_bersih", "Rencana bawaan (50% di +5%, sisa ke target, SL −12%)"),
                       ("pola_sl12_bersih", "Target pola, SL −12%")):
        kh = kol.replace("_bersih", "_hari")
        rows_d = [per_periode(f(dflt), kol, kh, mid, nm) for nm, f in VAR_STAGE.items()]
        rows_a = [per_periode(f(naik), kol, kh, mid, nm) for nm, f in VAR_STAGE.items()]
        H["radar"][kol] = dict(judul=judul, filter_bawaan=rows_d, semua_sinyal=rows_a)
        L += [f"### 6a. Sinyal 🟢 radar + filter stage — {judul}", "",
              "Dengan filter bawaan (BTC tren naik + bukan meme):", ""] + tabel_periode(rows_d, "Filter stage")
        L += ["", "Semua sinyal naik (tanpa filter pasar/meme):", ""] + tabel_periode(rows_a, "Filter stage") + [""]
    kol = "pola_tp5_sl12_bersih"
    H["radar_per_stage"] = [per_periode(g, kol, "pola_tp5_sl12_hari", mid, f"Stage {k}") for k, g in naik.groupby("stage")]
    H["radar_per_fase"] = [per_periode(g, kol, "pola_tp5_sl12_hari", mid, str(k)) for k, g in naik.groupby("fase")]
    turun = df[df["kelas"] == "turun"]
    H["turun_per_stage"] = [per_periode(g, kol, "pola_tp5_sl12_hari", mid, f"Stage {k}") for k, g in turun.groupby("stage")]
    L += ["### 6b. Sinyal 🟢 radar per stage (semua sinyal, rencana bawaan)", ""] + tabel_periode(H["radar_per_stage"], "Stage")
    L += ["", "Per fase:", ""] + tabel_periode(H["radar_per_fase"], "Fase")
    L += ["", "### 6c. Sinyal 🔴 radar (short) per stage", ""] + tabel_periode(H["turun_per_stage"], "Stage") + [""]

    H["murni"] = []
    if len(dsik):
        ds = dsik[~dsik["meme"]]
        acak = ds[ds["event"] == "acak"]
        H["acak_per_stage"] = {k: [per_periode(g, k2, k2.replace("_bersih", "_hari"), mid, f"Stage {st}")
                                   for st, g in acak.groupby("stage")]
                               for k, k2 in (("rencana", "rencana_bersih"), ("siklus", "siklus_bersih"))}
        L += ["### 6d. Beli di hari acak menurut stage (pembanding, bukan meme)", "",
              "Apakah stage saja sudah membedakan hasil? Rencana bawaan:", ""] + tabel_periode(H["acak_per_stage"]["rencana"], "Stage")
        L += ["", "Aturan *ikuti siklus* (jual saat tutup di bawah MA50 atau SL −12%, maks 180 hari):", ""]
        L += tabel_periode(H["acak_per_stage"]["siklus"], "Stage") + [""]
        L += ["### 6e. Strategi siklus murni (tanpa skor radar, bukan meme)", ""]
        for ev, ket in EVENT.items():
            g = ds[ds["event"] == ev]
            for pn, pf in PASAR.items():
                gg = pf(g)
                for k2, ket2 in (("rencana_bersih", "rencana bawaan"), ("siklus_bersih", "ikuti siklus (MA50)")):
                    H["murni"].append(per_periode(gg, k2, k2.replace("_bersih", "_hari"), mid,
                                                  f"{ket} · {pn} · {ket2}", event=ev, pasar=pn, keluar=k2))
        L += tabel_periode(H["murni"], "Strategi · pasar · aturan jual") + [""]
    lolos = [r for r in H["murni"] if r["event"] != "acak" and r.get("n", 0) >= 30
             and (r["p1"].get("n", 0) >= 15 and r["p2"].get("n", 0) >= 15)
             and r["p1"]["rata"] > 0 and r["p2"]["rata"] > 0]
    H["murni_lolos"] = sorted(lolos, key=lambda r: -min(r["p1"]["rata"], r["p2"]["rata"]))
    L += ["**Strategi siklus murni yang positif di kedua periode (≥15 sinyal per periode):** "
          + ("; ".join(f"{r['grup']} → {r['rata']:+.2f}% ({r['n']} sinyal)" for r in H["murni_lolos"][:5])
             if H["murni_lolos"] else "tidak ada."), ""]
    return H, "\n".join(L) + "\n"


def _json_safe(o):
    if isinstance(o, dict):
        return {k: _json_safe(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_json_safe(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


# --------------------------------------------------------------------------- #
# Jalankan
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hari", type=int, default=1000)
    ap.add_argument("--maks-koin", type=int, default=0, help="batasi jumlah koin (untuk uji cepat)")
    args = ap.parse_args()
    t0 = time.time()
    cfg = S.load_config()
    state = S.load_state()
    now = datetime.now(timezone.utc)
    rank_list, src_rank = S.ambil_ranking(cfg, state, now)
    bn = S.Binance()
    tick = bn.tickers(cfg["quote"])
    koin = []
    for c in sorted(rank_list, key=lambda x: x["rank"]):
        b = S.ALIAS_BINANCE.get(c["symbol"], c["symbol"])
        if c.get("stabil") or c["symbol"] in cfg["abaikan"] or b not in tick:
            continue
        koin.append((tick[b]["symbol"], c["symbol"], c["rank"], bool(c.get("meme")) or ST.is_meme(c["symbol"])))
    if args.maks_koin:
        koin = koin[:args.maks_koin]
    if not any(k[0] == "BTCUSDT" for k in koin):
        koin.insert(0, ("BTCUSDT", "BTC", 1, False))
    print(f"Ranking {src_rank}: {len(koin)} koin, ambil {args.hari} candle harian...")

    data = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(bn.candles, k[0], "1d", args.hari): k for k in koin}
        for f in as_completed(futs):
            try:
                d = f.result()
                data[futs[f][0]] = d[d["closed"]].reset_index(drop=True)
            except Exception as e:
                print("  ! gagal", futs[f][0], e)
    btc = data.get("BTCUSDT")
    if btc is None or len(btc) < 100:
        print("Data BTC tidak tersedia")
        return 1
    tg = btc["time"].dt.strftime("%Y-%m-%d").to_numpy()
    rezim = dict(zip(tg, ST.rezim_series(btc["close"].to_numpy())))
    btc_close = dict(zip(tg, btc["close"].to_numpy().astype(float)))
    print(f"Data siap ({time.time() - t0:.0f} dtk). Simulasi...")

    jobs = [(sym, base, rank, meme, data[sym], rezim, btc_close, cfg)
            for sym, base, rank, meme in koin if sym in data and len(data[sym]) > HARI_MIN + TAHAN]
    rows, rows_sik = [], []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for i, (out, out_sik) in enumerate(ex.map(proses_koin, jobs, chunksize=1), start=1):
            rows.extend(out)
            rows_sik.extend(out_sik)
            if i % 20 == 0:
                print(f"  {i}/{len(jobs)} koin · {len(rows)} sinyal · {time.time() - t0:.0f} dtk")
    if not rows:
        print("Tidak ada sinyal.")
        return 1
    df = pd.DataFrame(rows)
    WIB = S.WIB
    meta = dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), ranking=src_rank,
                koin=len(jobs), dari=str(df["tanggal"].min()), sampai=str(df["tanggal"].max()), sinyal=len(df),
                hari_data=args.hari, durasi_detik=round(time.time() - t0))
    hasil, md = laporan(df, meta)
    dsik = pd.DataFrame(rows_sik)
    h_sik, md_sik = laporan_siklus(df, dsik, meta)
    hasil["siklus"] = h_sik
    md = md.replace("## Keterbatasan", md_sik + "\n## Keterbatasan")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as f:
        json.dump(_json_safe(hasil), f, ensure_ascii=False, indent=1, allow_nan=False)
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as f:
        f.write(md)
    with gzip.open(os.path.join(OUT, "sinyal.csv.gz"), "wt", encoding="utf-8") as f:
        df.to_csv(f, index=False)
    with gzip.open(os.path.join(OUT, "siklus.csv.gz"), "wt", encoding="utf-8") as f:
        dsik.to_csv(f, index=False)
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as f:
            f.write(md)
    print(md)
    print(f"Selesai {time.time() - t0:.0f} dtk · zona waktu {WIB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
