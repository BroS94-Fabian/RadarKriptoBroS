#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UJI "PILIHAN HARIAN" — minimal 1 koin per hari
===============================================
Pertanyaan: kalau radar tidak mengirim sinyal apa pun (filter menahan semua), apakah layak mengirim SATU koin
terbaik per hari yang arahnya mengikuti kondisi pasar? Seberapa bagus hasilnya dibanding koin acak?

Tahap `data`  : candle harian Binance sejak 2020 untuk koin yang sama dengan uji model pasar → tiap koin tiap hari
                jalankan mesin radar harian (sama dengan backtest harian) → catat skor beli, skor jual, kelas, stage,
                perubahan 30 hari, lalu hasil rencana jual standar bila BELI dan bila JUAL DULU hari itu.
                → backtest_pilihan/harian.csv.gz (disimpan di cabang data-pilihan)
Tahap `model` : bandingkan aturan pemilihan, putuskan cara menampilkannya di radar.

ATURAN YANG DITETAPKAN DI MUKA (ditulis & di-commit sebelum tahap model dijalankan pada data ini)
  1. Arah hari itu mengikuti model pasar: BTC tren naik → pilihan BELI; selain itu → pilihan JUAL DULU.
     Meme coin & stablecoin tidak ikut. Rencana jual standar: TP1 +5% (jual 50%, lalu stop loss ke harga masuk),
     TP2 +10%, SL −12%, maks 30 hari; biaya & pajak sama dengan uji lain (jual dulu + funding 0,03%/hari).
     Masuk di harga penutupan candle harian hari pilihan (sama dengan sinyal harian radar).
  2. Enam aturan pemilihan (koin yang sama tidak dipilih lagi selama 10 hari → ambil urutan berikutnya):
       L1 skor beli radar tertinggi (kelas bukan 🔴)      S1 skor jual radar tertinggi (kelas bukan 🟢)
       L2 skor beli tertinggi di antara koin Stage 2     S2 skor jual tertinggi di antara koin Stage 4
       L3 paling kuat vs BTC 30 hari, koin Stage 2       S3 paling lemah vs BTC 30 hari, koin Stage 4
  3. Per arah, aturan dipilih HANYA dari data latih (pilihan sebelum 2023): rata-rata bersih tertinggi dengan
     minimal 60 pilihan. Lalu diuji di luar sampel (2023 dst.).
  4. Putusan per arah: "LAYAK" bila di luar sampel rata-rata bersih > 0 DAN lebih tinggi dari rata-rata semua koin
     (bukan meme) di hari yang sama dengan arah yang sama (= memilih koin secara acak).
       LAYAK       → dikirim sebagai "⚪ Pilihan harian" lengkap dengan rencana masuk/keluar;
       tidak LAYAK → tetap dikirim 1 koin per hari, tetapi sebagai "👀 Koin pantauan" TANPA ajakan masuk.
     Di radar, pilihan hanya dikirim pada hari tanpa sinyal 🟢/🟩/🔻 sama sekali.
  5. Hanya dilaporkan (tidak ikut putusan): pilihan pada hari tanpa sinyal saja, per tahun, dan portofolio
     "sistem sekarang" vs "sistem sekarang + pilihan harian" (maks 5 posisi).

TAMBAHAN SETELAH HASIL KELUAR (24 Nov 2026): jual dulu lolos syarat butir 4 (rata-rata +0,44% semua hari), tetapi
pada hari tanpa sinyal — satu-satunya hari pilihan dikirim — rata-ratanya hanya +0,04% dan bila ikut
diperdagangkan portofolio turun dari +184% ke +119%. Karena itu radar memakai bawaan yang lebih hati-hati:
`pilihan_harian: pantau` (kedua arah dikirim sebagai 👀 pantauan); `rencana` bisa dipilih sendiri di config.yaml.
Laporan menambahkan hasil per arah pada hari tanpa sinyal dan portofolio "sistem + pilihan jual dulu saja".

Hasil: backtest_pilihan/LAPORAN.md, hasil.json, model.json, meta.json
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

import analisa as A
import backtest as BT
import backtest_pasar as BP
import backtest_perjam as BJ
import backtest_short as BS
import scanner as S
import strategi as ST

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_pilihan")
DATA = os.path.join(OUT, "harian.csv.gz")
JEDA = 10
MIN_LATIH = 60
AWAL_UJI = pd.Timestamp("2023-01-01")
ATURAN = {
    # kode: (sisi, nama, syarat calon, kolom urut, kecil dulu?)
    "L1": ("long", "Skor beli radar tertinggi", lambda d: d["kelas"] != "turun", "skor_naik", False),
    "L2": ("long", "Skor beli tertinggi di Stage 2", lambda d: d["stage"] == 2, "skor_naik", False),
    "L3": ("long", "Paling kuat vs BTC 30 hari (Stage 2)", lambda d: d["stage"] == 2, "rs30", False),
    "S1": ("short", "Skor jual radar tertinggi", lambda d: d["kelas"] != "naik", "skor_turun", False),
    "S2": ("short", "Skor jual tertinggi di Stage 4", lambda d: d["stage"] == 4, "skor_turun", False),
    "S3": ("short", "Paling lemah vs BTC 30 hari (Stage 4)", lambda d: d["stage"] == 4, "rs30", True),
}


# --------------------------------------------------------------------------- #
# Tahap data
# --------------------------------------------------------------------------- #
def proses(job):
    sym, base, meme, d, cfg = job
    n = len(d)
    o, h, l, c = (d[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    tgl = d["time"].dt.strftime("%Y-%m-%d").to_numpy()
    Bl, Bs = cfg.get("biaya"), dict(BS.BIAYA_KONS, **(cfg.get("biaya_short") or {}))
    out, gagal = [], 0
    for t in range(BT.HARI_MIN, n - BT.TAHAN):
        w = d.iloc[max(0, t - BT.JENDELA + 1):t + 1]
        info = dict(symbol=sym, base=base, name=base, rank=100, meme=meme, bursa="Binance", price=float(c[t]),
                    chg24=float((c[t] / c[t - 1] - 1) * 100), qvol24=float(d["qvol"].iat[t]))
        try:
            r = A.analisa_koin(info, w, None, cfg)
        except Exception:
            gagal += 1
            continue
        if not r:
            continue
        sk = r.get("siklus") or {}
        rec = dict(tanggal=tgl[t], symbol=sym, meme=meme, kelas=r["kelas"], skor_naik=r["skor_naik"], skor_turun=r["skor_turun"],
                   stage=int(sk.get("stage") or 0), fase=str(sk.get("fase", "0")),
                   r30=round((c[t] / c[t - 30] - 1) * 100, 2) if t >= 30 else None)
        fut = slice(t + 1, t + 1 + BT.TAHAN)
        for arah, kode in (("naik", "L"), ("turun", "S")):
            plan = ST.rencana(float(c[t]), arah, None, None, None, ST.DEFAULT_RENCANA)
            x = ST.simulasi(plan, h[fut], l[fut], c[fut])
            net = ST.bersih(x["pnl"], Bl) if arah == "naik" else BS.bersih(x["pnl"], x["hari"], Bs)
            rec[f"n{kode}"], rec[f"h{kode}"] = round(float(net), 3), int(x["hari"])
        out.append(rec)
    return sym, out, gagal


def tahap_data(args) -> int:
    t0 = time.time()
    now = datetime.now(timezone.utc)
    cfg = S.load_config()
    koin = BJ.daftar_koin()
    if args.koin:
        koin = koin[:args.koin]
        if not any(k[0] == "BTCUSDT" for k in koin):
            koin.insert(0, ("BTCUSDT", "BTC", False))
    bn = S.Binance()
    mulai = pd.Timestamp(args.mulai, tz="UTC")
    print(f"{len(koin)} koin, candle harian sejak {args.mulai}")
    data = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(BP.harian_lengkap, bn, k[0], mulai): k for k in koin}
        for f in as_completed(futs):
            try:
                d = f.result()
                if len(d) >= BT.HARI_MIN + BT.TAHAN + 10:
                    data[futs[f][0]] = d
            except Exception as e:
                print("  ! gagal", futs[f][0], e)
    print(f"  unduh selesai: {len(data)} koin · {time.time() - t0:.0f} dtk")
    jobs = [(k[0], k[1], k[2], data[k[0]], cfg) for k in koin if k[0] in data]
    jobs.sort(key=lambda j: -len(j[3]))
    rows, n_gagal = [], 0
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for i, (sym, out, g) in enumerate(ex.map(proses, jobs, chunksize=1), start=1):
            rows += out
            n_gagal += g
            if i % 10 == 0:
                print(f"  {i}/{len(jobs)} · {len(rows):,} baris · {time.time() - t0:.0f} dtk", flush=True)
    os.makedirs(OUT, exist_ok=True)
    D = pd.DataFrame(rows).sort_values(["tanggal", "symbol"])
    D.to_csv(DATA, index=False, compression="gzip")
    meta = dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), koin=len(jobs),
                gagal=sorted(set(k[0] for k in koin) - set(data)), analisa=int(len(D)), analisa_gagal=int(n_gagal),
                mulai=args.mulai, dari=str(D["tanggal"].min()), sampai=str(D["tanggal"].max()), durasi_detik=round(time.time() - t0))
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------- #
# Tahap model
# --------------------------------------------------------------------------- #
def muat() -> pd.DataFrame:
    X = pd.read_csv(DATA)
    btc = X[X["symbol"] == "BTCUSDT"].set_index("tanggal")["r30"]
    X = X[~X["meme"].astype(bool)].copy()
    X["rs30"] = X["r30"] - X["tanggal"].map(btc)
    ph = pd.read_csv(os.path.join(BP.OUT, "pasar_harian.csv"), index_col="tanggal")
    X = X.merge(ph[["skor", "rezim"]], left_on="tanggal", right_index=True, how="inner")
    X["sisi_hari"] = np.where(X["rezim"] == "naik", "long", "short")
    X["ts"] = pd.to_datetime(X["tanggal"])
    X["bulan"] = X["tanggal"].str[:7]
    return X


def pilih(X: pd.DataFrame, kode: str) -> pd.DataFrame:
    """Satu pilihan per hari (hari dengan arah yang sesuai), dengan jeda 10 hari per koin."""
    sisi, _, syarat, kol, naik = ATURAN[kode]
    d = X[(X["sisi_hari"] == sisi) & syarat(X) & X[kol].notna()]
    d = d.sort_values(["tanggal", kol, "symbol"], ascending=[True, naik, True])
    terakhir, ambil = {}, []
    for tgl, g in d.groupby("tanggal", sort=True):
        t = pd.Timestamp(tgl)
        for i, sy in zip(g.index, g["symbol"]):
            if sy in terakhir and (t - terakhir[sy]).days < JEDA:
                continue
            terakhir[sy] = t
            ambil.append(i)
            break
    P = X.loc[ambil].copy()
    k = "L" if sisi == "long" else "S"
    P["net"], P["hari"], P["sisi"], P["strategi"] = P[f"n{k}"], P[f"h{k}"], sisi, "pilihan_" + kode
    P["keluar"] = P["ts"] + pd.to_timedelta(P["hari"].clip(lower=1), unit="D")
    return P


def acak(X: pd.DataFrame) -> pd.DataFrame:
    """Rata-rata semua koin (bukan meme) per hari, sesuai arah hari itu = hasil yang diharapkan dari koin acak."""
    a = X.assign(net=np.where(X["sisi_hari"] == "long", X["nL"], X["nS"]), menang=lambda d: (np.where(d["sisi_hari"] == "long", d["nL"], d["nS"]) > 0))
    return a.groupby("tanggal").agg(net_acak=("net", "mean"), menang_acak=("menang", "mean"), sisi=("sisi_hari", "first"))


def ringkas(P: pd.DataFrame, A_: pd.DataFrame | None = None) -> dict:
    if not len(P):
        return dict(n=0)
    r = BP.ringkas(P)
    if A_ is not None:
        a = A_.reindex(P["tanggal"])
        r["acak_rata"] = round(float(a["net_acak"].mean()), 2)
        r["acak_menang"] = round(float(a["menang_acak"].mean() * 100), 1)
        r["lebih_acak"] = round(r["rata"] - r["acak_rata"], 2)
    return r


def tahap_model(args) -> int:
    cfg = S.load_config()
    if not os.path.exists(DATA):
        print("backtest_pilihan/harian.csv.gz belum ada — jalankan tahap data dulu")
        return 1
    X = muat()
    A_ = acak(X)
    meta = json.load(open(os.path.join(OUT, "meta.json"), encoding="utf-8")) if os.path.exists(os.path.join(OUT, "meta.json")) else {}
    now = datetime.now(timezone.utc)
    bersih_ = lambda r: {k: v for k, v in r.items() if not k.startswith("_")}  # noqa: E731
    H = dict(versi=1, dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), data=meta,
             dari=str(X["tanggal"].min()), sampai=str(X["tanggal"].max()), awal_uji=str(AWAL_UJI.date()),
             aturan={k: dict(sisi=v[0], nama=v[1]) for k, v in ATURAN.items()})
    Pk = {k: pilih(X, k) for k in ATURAN}
    latih = lambda P: P[P["keluar"] < AWAL_UJI]  # noqa: E731
    uji = lambda P: P[P["ts"] >= AWAL_UJI]  # noqa: E731
    H["per_aturan"] = {k: dict(latih=ringkas(latih(P), A_), uji=ringkas(uji(P), A_), semua=ringkas(P, A_),
                               per_tahun={str(y): ringkas(g, A_) for y, g in P.groupby(P["ts"].dt.year)}) for k, P in Pk.items()}
    # pilih aturan per arah dari data latih
    H["pilihan"], putusan = {}, {}
    for sisi in ("long", "short"):
        kand = [k for k, v in ATURAN.items() if v[0] == sisi and H["per_aturan"][k]["latih"].get("n", 0) >= MIN_LATIH]
        if not kand:
            H["pilihan"][sisi] = dict(aturan=None, alasan="data latih kurang")
            putusan[sisi] = False
            continue
        k = max(kand, key=lambda q: H["per_aturan"][q]["latih"]["rata"])
        u = H["per_aturan"][k]["uji"]
        ok = bool(u.get("n") and u["rata"] > 0 and u["rata"] > u["acak_rata"])
        H["pilihan"][sisi] = dict(aturan=k, nama=ATURAN[k][1], latih=H["per_aturan"][k]["latih"], uji=u, layak=ok)
        putusan[sisi] = ok

    # sistem live (walk-forward, sama dengan uji model pasar) & hari tanpa sinyal
    T, _ = BP.muat_sinyal(cfg)
    U = T[~T["meme"]].copy()
    akhir = min(U["ts"].max(), X["ts"].max())
    bag = []
    for th in range(AWAL_UJI.year, int(akhir.year) + 1):
        mulai = pd.Timestamp(f"{th}-01-01")
        sel = BP.pilih_v2(U[U["keluar"] < mulai], U["ts"].min(), mulai)
        bag.append(BP.lolos_v2(U[(U["ts"] >= mulai) & (U["ts"] <= min(pd.Timestamp(f"{th}-12-31"), akhir))], sel, False))
    Td = pd.concat(bag)
    hari_sinyal = set(Td["tanggal"])
    hari_uji = pd.date_range(AWAL_UJI, akhir, freq="D").strftime("%Y-%m-%d")
    kosong = [t for t in hari_uji if t not in hari_sinyal]
    H["hari"] = dict(uji=len(hari_uji), ada_sinyal=len(hari_uji) - len(kosong), tanpa_sinyal=len(kosong),
                     tanpa_sinyal_per_tahun={str(y): int(sum(1 for t in kosong if t.startswith(str(y)))) for y in range(AWAL_UJI.year, akhir.year + 1)})
    set_kosong = set(kosong)
    for s in ("long", "short"):
        if H["pilihan"][s].get("aturan"):
            Pu = uji(Pk[H["pilihan"][s]["aturan"]])
            H["pilihan"][s]["uji_hari_kosong"] = ringkas(Pu[Pu["tanggal"].isin(set_kosong)], A_)
    gab = pd.concat([Pk[H["pilihan"][s]["aturan"]] for s in ("long", "short") if H["pilihan"][s].get("aturan")])
    gab_u = uji(gab)
    gab_k = gab_u[gab_u["tanggal"].isin(set(kosong))]
    H["gabungan"] = dict(semua_hari=ringkas(gab_u, A_), hari_tanpa_sinyal=ringkas(gab_k, A_),
                         per_tahun={str(y): ringkas(g, A_) for y, g in gab_k.groupby(gab_k["ts"].dt.year)},
                         per_sisi={s: ringkas(gab_k[gab_k["sisi"] == s], A_) for s in ("long", "short")})
    a0, a1 = AWAL_UJI, akhir + pd.Timedelta(days=31)
    kol = ["tanggal", "symbol", "strategi", "net", "hari", "ts", "keluar"]
    r_live = BP.uji_portofolio(Td[kol], a0, a1)
    r_plus = BP.uji_portofolio(pd.concat([Td[kol], gab_k[kol]]), a0, a1)
    r_saja = BP.uji_portofolio(gab_k[kol], a0, a1)
    gab_j = gab_k[gab_k["sisi"] == "short"]
    r_jual = BP.uji_portofolio(pd.concat([Td[kol], gab_j[kol]]), a0, a1)
    for r in (r_live, r_plus, r_saja, r_jual):
        r.pop("_kurva")
    H["portofolio"] = {"Sistem sekarang": bersih_(r_live), "Sistem sekarang + pilihan harian": bersih_(r_plus),
                       "Sistem sekarang + pilihan jual dulu saja": bersih_(r_jual),
                       "Pilihan harian saja (hari tanpa sinyal)": bersih_(r_saja)}
    H["putusan"] = putusan
    model = dict(versi=1, dibuat=H["dibuat"], dibuat_wib=H["dibuat_wib"], jeda_hari=JEDA,
                 bawaan_radar="pantau",
                 beli=dict(aturan=H["pilihan"]["long"].get("aturan"), layak=putusan["long"], uji=H["pilihan"]["long"].get("uji"),
                           uji_hari_kosong=H["pilihan"]["long"].get("uji_hari_kosong")),
                 jual=dict(aturan=H["pilihan"]["short"].get("aturan"), layak=putusan["short"], uji=H["pilihan"]["short"].get("uji"),
                           uji_hari_kosong=H["pilihan"]["short"].get("uji_hari_kosong")))
    H["model"] = model

    # ---------- laporan ----------
    def f_r(r, acak_=True):
        if not r or not r.get("n"):
            return "-"
        s = f"{r['rata']:+.2f}% · menang {r['menang']}% ({r['n']})"
        return s + (f" · acak {r['acak_rata']:+.2f}% / {r['acak_menang']}%" if acak_ and "acak_rata" in r else "")

    def f_p(r):
        return f"{r['total']:+.1f}% · maks turun {r['maxdd']:.1f}% · Sharpe {r['sharpe']} · menang {r['menang']}% · {r['transaksi']} transaksi" if r.get("transaksi") else "tidak ada transaksi"
    L = ["# 📌 Uji \"Pilihan Harian\" — minimal 1 koin per hari", "",
         f"Dibuat {H['dibuat_wib']} · {meta.get('koin', '?')} koin · {meta.get('analisa', 0):,} analisa harian · {H['dari']} s/d {H['sampai']} · "
         f"latih sebelum {H['awal_uji']}, uji {H['awal_uji']} dst. · meme coin tidak ikut", "", "## Putusan", ""]
    for sisi, nm in (("long", "Beli (saat BTC tren naik)"), ("short", "Jual dulu (saat BTC tidak tren naik)")):
        p = H["pilihan"][sisi]
        if not p.get("aturan"):
            L.append(f"- **{nm}: tidak ada aturan** ({p.get('alasan')})")
            continue
        L.append(f"- **{nm}: {'✅ LAYAK → ⚪ Pilihan harian dengan rencana' if p['layak'] else '❌ tidak layak → 👀 Koin pantauan tanpa ajakan masuk'}** — "
                 f"aturan {p['aturan']} ({p['nama']}); di luar sampel {f_r(p['uji'])}")
    L += ["", "Syarat LAYAK (ditetapkan di muka): rata-rata bersih di luar sampel > 0 dan lebih tinggi dari koin acak di hari yang sama.", "",
          "### Cara dipasang di radar (diputuskan setelah hasil keluar)", "",
          "Pilihan hanya dikirim pada hari tanpa sinyal. Pada hari-hari itu hasilnya:"]
    for sisi, nm in (("long", "Beli"), ("short", "Jual dulu")):
        p = H["pilihan"][sisi]
        if p.get("aturan"):
            L.append(f"- {nm} ({p['aturan']}): {f_r(p.get('uji_hari_kosong'))}")
    L += ["", "Bila ikut diperdagangkan, portofolio justru turun (lihat tabel portofolio). Karena itu radar memakai bawaan "
          "**`pilihan_harian: pantau`**: satu koin per hari dikirim sebagai 👀 pantauan beserta syarat yang membuatnya jadi sinyal "
          "sungguhan, tanpa ajakan masuk. `rencana` (dengan TP/SL) bisa dipilih sendiri di config.yaml.", "",
          "## Semua aturan", "", "Isi sel: rata-rata bersih per pilihan · tingkat menang (jumlah) · pembanding koin acak di hari yang sama.", "",
          "| Aturan | Arah | Latih (s/d 2022) | Uji (2023 dst.) |", "|---|---|---|---|"]
    for k, v in ATURAN.items():
        x = H["per_aturan"][k]
        L.append(f"| {k} {v[1]} | {'beli' if v[0] == 'long' else 'jual dulu'} | {f_r(x['latih'])} | {f_r(x['uji'])} |")
    L += ["", "### Per tahun (aturan terpilih)", "", "| Tahun | " + " | ".join(f"{H['pilihan'][s].get('aturan') or '-'}" for s in ("long", "short")) + " |", "|---|---|---|"]
    tahun = sorted(set().union(*[set(H["per_aturan"][H["pilihan"][s]["aturan"]]["per_tahun"]) for s in ("long", "short") if H["pilihan"][s].get("aturan")]))
    for y in tahun:
        L.append(f"| {y} | " + " | ".join(f_r(H["per_aturan"][H["pilihan"][s]["aturan"]]["per_tahun"].get(y)) if H["pilihan"][s].get("aturan") else "-" for s in ("long", "short")) + " |")
    g = H["gabungan"]
    L += ["", f"## Seberapa sering radar diam? ({H['awal_uji']} dst.)", "",
          f"Dari {H['hari']['uji']} hari, {H['hari']['ada_sinyal']} hari ada sinyal 🟢/🟩/🔻 dan **{H['hari']['tanpa_sinyal']} hari tanpa sinyal sama sekali** "
          f"(per tahun: " + ", ".join(f"{y}: {n}" for y, n in H["hari"]["tanpa_sinyal_per_tahun"].items()) + ").", "",
          f"Pilihan harian pada hari tanpa sinyal: {f_r(g['hari_tanpa_sinyal'])}", "",
          f"- Beli: {f_r(g['per_sisi']['long'])}", f"- Jual dulu: {f_r(g['per_sisi']['short'])}", "",
          "| Tahun | Pilihan pada hari tanpa sinyal |", "|---|---|"] + [f"| {y} | {f_r(r)} |" for y, r in g["per_tahun"].items()]
    L += ["", "## Portofolio di luar sampel (maks 5 posisi, median 100 urutan acak)", "",
          "| Susunan | Hasil |", "|---|---|"] + [f"| {nm} | {f_p(r)} |" for nm, r in H["portofolio"].items()]
    L += ["", "## Catatan jujur", "",
          "- Pilihan harian dibuat supaya radar tidak diam; ia BUKAN sinyal yang lolos semua filter. Hari tanpa sinyal biasanya hari "
          "ketika pasar sedang tidak mendukung.",
          "- Data koin = koin top CMC saat ini (yang sudah mati tidak ikut) — hasil beli cenderung terlalu bagus, hasil jual dulu terlalu jelek.",
          "- Aturan & syarat ditulis sebelum tahap model dijalankan. Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual."]
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as f:
        json.dump(BT._json_safe(H), f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "model.json"), "w", encoding="utf-8") as f:
        json.dump(BT._json_safe(model), f, ensure_ascii=False, indent=1)
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tahap", choices=["data", "model", "semua"], nargs="?", default="semua")
    ap.add_argument("--mulai", default="2020-01-01")
    ap.add_argument("--koin", type=int, default=0)
    args = ap.parse_args()
    if args.tahap in ("data", "semua"):
        rc = tahap_data(args)
        if rc:
            return rc
    if args.tahap in ("model", "semua"):
        return tahap_model(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
