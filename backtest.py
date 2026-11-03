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
import strategi as ST

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest")
HARI_MIN = 260      # butuh MA200 + ruang analisa
JENDELA = 400       # jumlah candle yang dianalisa per hari (sama seperti radar)
JEDA = 10           # setelah sinyal, koin & arah yang sama tidak dihitung lagi selama 10 hari
TAHAN = 30          # horizon maksimum simulasi

# nama: (keterangan, rencana, pakai target/batal pola)
ATURAN = {
    "pola": ("Target & batal pola (tanpa TP1)",
             dict(mode="persen", tp1_persen=5, sl_persen=99, porsi_tp1=0, maks_hari=30), True),
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
        for nama, (_, R, pakai_pola) in ATURAN.items():
            plan = ST.rencana(float(c[t]), k, tgt if pakai_pola else None, bt if pakai_pola else None, atrp, R)
            m = R["maks_hari"]
            res = ST.simulasi(plan, hi[:m], lo[:m], cl[:m])
            rec[f"{nama}_bersih"] = round(ST.bersih(res["pnl"], cfg.get("biaya")), 3)
            rec[f"{nama}_hasil"] = res["hasil"]
            rec[f"{nama}_hari"] = res["hari"]
        out.append(rec)
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
        for k in dict.fromkeys((terbaik, "pola", "sebagian_5_5", "sebagian_atr")):
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
    for k in dict.fromkeys((terbaik, "pola", "sebagian_5_5", "sebagian_atr")):
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
    rows = []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for i, out in enumerate(ex.map(proses_koin, jobs, chunksize=1), start=1):
            rows.extend(out)
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
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as f:
        json.dump(_json_safe(hasil), f, ensure_ascii=False, indent=1, allow_nan=False)
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as f:
        f.write(md)
    with gzip.open(os.path.join(OUT, "sinyal.csv.gz"), "wt", encoding="utf-8") as f:
        df.to_csv(f, index=False)
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as f:
            f.write(md)
    print(md)
    print(f"Selesai {time.time() - t0:.0f} dtk · zona waktu {WIB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
