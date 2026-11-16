#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UJI "HARIAN BERJALAN" — sinyal skala harian yang dihitung ulang tiap jam
========================================================================
Pertanyaan: kalau mesin radar harian dijalankan TIAP JAM pada candle 24 jam berjalan (berjalan.py), bukan hanya sekali
sehari saat candle harian tutup (07.00 WIB), apakah hasilnya tidak lebih buruk?

Tahap `data`   : candle 1 jam Binance sejak 2020 → di SETIAP jam bentuk candle 24 jam berjalan, jalankan mesin radar
                 harian apa adanya → catat SEMUA jam saat syarat 🟢 radar / 🟩 awal Stage 2 / 🔻 pantulan Stage 4
                 terpenuhi + simulasi rencana jual harian (TP1 5%, SL 12%, maks 30 hari) pada candle 1 jam.
Tahap `gabung` : satukan hasil semua bagian → backtest_berjalan/sinyal.csv.gz
Tahap `model`  : susun dua sistem dari catatan yang sama lalu bandingkan portofolionya.

ATURAN YANG DITETAPKAN DI MUKA (ditulis & di-commit sebelum data ditarik)
  1. Mesin = berjalan.analisa: rumus & ambang radar harian tidak diubah sama sekali; yang berbeda hanya jam tutup
     candle 24 jam-nya. Meme coin tidak ikut. Biaya & pajak sama dengan uji harian.
  2. Dua sistem dibangun dari catatan yang sama, dengan aturan yang sama persis:
       PEMBANDING ("hanya 07.00 WIB") = mesin dicek hanya saat jam 00.00 UTC — itulah sistem harian sekarang;
       TIAP JAM   = 🟩 awal Stage 2 dan 🔻 jual dulu dicek di setiap jam; 🟢 radar tetap seperti pembanding.
     Gerbang pasar = model pasar yang live (arah BTC harian + skor pasar dari candle harian terakhir yang sudah tutup,
     batas tiap tahun sama dengan uji model pasar). Setelah lolos gerbang, koin & jenis sinyal yang sama tidak
     diulang selama 10 hari (240 jam) — sama dengan jeda alert radar.
  3. MASUK = harga penutupan candle 1 jam berikutnya (jeda 1 jam untuk keterlambatan alert & pasang order manual),
     untuk kedua sistem. Rencana jual harian disimulasikan pada candle 1 jam (SL dulu bila SL & TP di candle yang sama).
  4. Putusan (di luar sampel 2023 dst., portofolio maks 5 posisi, median 100 urutan acak):
     TIAP JAM dipasang ke radar bila total ≥ pembanding, Sharpe ≥ pembanding, dan penurunan maksimum tidak lebih
     buruk dari pembanding − 5 poin. Kalau tidak → dilaporkan apa adanya dan TIDAK dipasang.
  5. Hanya dilaporkan (tidak ikut putusan): versi "semua termasuk 🟢 tiap jam", masuk tanpa jeda, sebaran jam sinyal,
     dan perbandingan dengan angka uji harian yang sudah terbit.

Hasil: backtest_berjalan/LAPORAN.md, hasil.json, model.json, meta.json, kurva.csv (sinyal.csv.gz di cabang data-berjalan)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import backtest as BT
import backtest_pasar as BP
import backtest_perjam as BJ
import backtest_short as BS
import berjalan as BR
import scanner as S
import strategi as ST

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_berjalan")
SINYAL = os.path.join(OUT, "sinyal.csv.gz")
TAHAN = 720               # 30 hari dalam candle 1 jam
JEDA_JAM = 240            # 10 hari
RENCANA = dict(mode="persen", tp1_persen=5.0, sl_persen=12.0, porsi_tp1=0.5, maks_hari=TAHAN)
MASUK = 1                 # 1 = masuk di penutupan candle 1 jam berikutnya
JENIS = {"radar_naik": ("long", "🟢 Radar naik"), "awal_stage2": ("long", "🟩 Awal Stage 2"),
         "pantul_fib": ("short", "🔻 Jual dulu (pantulan Stage 4)")}
SISTEM = {
    "pembanding": ("Hanya 07.00 WIB (sistem sekarang)", dict(radar_naik="fase0", awal_stage2="fase0", pantul_fib="fase0")),
    "tiap_jam": ("🟩 & 🔻 tiap jam", dict(radar_naik="fase0", awal_stage2="semua", pantul_fib="semua")),
    "semua": ("Semua tiap jam (termasuk 🟢)", dict(radar_naik="semua", awal_stage2="semua", pantul_fib="semua")),
}
JAM = pd.Timedelta(hours=1)


# --------------------------------------------------------------------------- #
# Tahap data
# --------------------------------------------------------------------------- #
def proses(job):
    sym, base, meme, a, cfg, sejak_ms = job
    t = a[:, 0].astype(np.int64)
    o, h, l, c, v, qv, tb = (a[:, i] for i in range(1, 8))
    n = len(t)
    Bl, Bs = cfg.get("biaya"), dict(BS.BIAYA_KONS, **(cfg.get("biaya_short") or {}))
    info = dict(symbol=sym, base=base, name=base, rank=100, meme=meme, bursa="Binance")
    out, gagal, dihitung = [], 0, 0
    j0 = int(np.searchsorted(t, t[0] + (BR.MIN_LILIN - 1) * BR.H24 - BR.MS_JAM, side="right"))
    if sejak_ms:
        j0 = max(j0, int(np.searchsorted(t, sejak_ms - BR.MS_JAM, side="left")))
    for j in range(j0, n - TAHAN - 2):
        try:
            _, sig = BR.analisa(info, BR.lilin(t, o, h, l, c, v, qv, tb, j), cfg)
            dihitung += 1
        except Exception:
            gagal += 1
            continue
        for s in sig:
            panjang = s["sisi"] == "long"
            t0 = pd.Timestamp(int(t[j]) + BR.MS_JAM, unit="ms")
            rec = dict(waktu=t0.strftime("%Y-%m-%dT%H:00"), fase=int(t0.hour), symbol=sym, meme=meme, sisi=s["sisi"],
                       strategi=s["strategi"], skor_radar=s.get("skor"))
            for e in (0, 1):
                je = j + e
                plan = ST.rencana(float(c[je]), "naik" if panjang else "turun", s["target"], s["batal"], None, RENCANA)
                x = ST.simulasi(plan, h[je + 1:je + 1 + TAHAN], l[je + 1:je + 1 + TAHAN], c[je + 1:je + 1 + TAHAN])
                net = ST.bersih(x["pnl"], Bl) if panjang else BS.bersih(x["pnl"], x["hari"] / 24, Bs)
                rec[f"n{e}"], rec[f"j{e}"] = round(float(net), 3), int(x["hari"])
            out.append(rec)
    return sym, out, n, dihitung, gagal


def tahap_data(args) -> int:
    t0 = time.time()
    now = datetime.now(timezone.utc)
    cfg = S.load_config()
    koin = BJ.daftar_koin()
    if args.koin:
        koin = koin[:args.koin]
    koin = koin[args.bagian::args.dari]
    bn = S.Binance()
    mulai, sampai = int(pd.Timestamp(args.mulai, tz="UTC").timestamp() * 1000), int(now.timestamp() * 1000)
    sejak_ms = int(pd.Timestamp(args.sejak, tz="UTC").timestamp() * 1000) if args.sejak else 0
    print(f"bagian {args.bagian}/{args.dari}: {len(koin)} koin, candle 1 jam sejak {args.mulai}" + (f", dianalisa sejak {args.sejak}" if args.sejak else ""))
    rows, gagal, n_jam, n_hitung, n_gagal, futs2 = [], [], 0, 0, 0, []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as pp:
        with ThreadPoolExecutor(max_workers=4) as tp:
            futs = {tp.submit(BJ.jam_lengkap, bn, k[0], mulai, sampai): k for k in koin}
            for f in as_completed(futs):
                k = futs[f]
                try:
                    a = f.result()
                    if a is None or len(a) < BR.MIN_LILIN * 24 + TAHAN + 50:
                        gagal.append(k[0])
                    else:
                        futs2.append(pp.submit(proses, (k[0], k[1], k[2], a, cfg, sejak_ms)))
                except Exception as e:
                    gagal.append(k[0])
                    print("  ! gagal", k[0], e)
        print(f"  unduh selesai · {time.time() - t0:.0f} dtk")
        for i, f in enumerate(as_completed(futs2), start=1):
            sym, out, n, nh, ng = f.result()
            rows += out
            n_jam += n
            n_hitung += nh
            n_gagal += ng
            print(f"  {i}/{len(futs2)} {sym}: {n:,} jam · {nh:,} analisa · {len(out)} catatan · {time.time() - t0:.0f} dtk", flush=True)
    os.makedirs(OUT, exist_ok=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, f"bagian_{args.bagian}.csv.gz"), index=False, compression="gzip")
    with open(os.path.join(OUT, f"bagian_{args.bagian}.json"), "w", encoding="utf-8") as f:
        json.dump(dict(koin=len(futs2), gagal=gagal, candle_jam=int(n_jam), analisa=int(n_hitung), analisa_gagal=int(n_gagal),
                       baris=int(len(D)), mulai=args.mulai, durasi_detik=round(time.time() - t0)), f)
    print(f"bagian {args.bagian} selesai: {len(futs2)} koin · {n_hitung:,} analisa · {len(D):,} catatan · gagal {gagal} · {time.time() - t0:.0f} dtk")
    return 0


def tahap_gabung(args) -> int:
    now = datetime.now(timezone.utc)
    berkas = sorted(glob.glob(os.path.join(OUT, "bagian_*.csv.gz")))
    if not berkas:
        print("tidak ada berkas bagian_*.csv.gz")
        return 1
    D = pd.concat([pd.read_csv(b) for b in berkas if os.path.getsize(b) > 50], ignore_index=True).sort_values(["waktu", "symbol", "strategi"])
    D.to_csv(SINYAL, index=False, compression="gzip")
    ms = [json.load(open(b, encoding="utf-8")) for b in sorted(glob.glob(os.path.join(OUT, "bagian_*.json")))]
    meta = dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), bagian=len(berkas),
                koin=sum(m["koin"] for m in ms), gagal=sum((m["gagal"] for m in ms), []), candle_jam=sum(m["candle_jam"] for m in ms),
                analisa=sum(m["analisa"] for m in ms), analisa_gagal=sum(m["analisa_gagal"] for m in ms), baris=int(len(D)),
                mulai=ms[0]["mulai"] if ms else None, dari=str(D["waktu"].min()), sampai=str(D["waktu"].max()),
                jam_mesin=round(sum(m["durasi_detik"] for m in ms) / 3600, 1),
                per_strategi={k: int(v) for k, v in D["strategi"].value_counts().items()})
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for b in berkas + glob.glob(os.path.join(OUT, "bagian_*.json")):
        os.remove(b)
    print(json.dumps(meta, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------- #
# Tahap model
# --------------------------------------------------------------------------- #
def muat() -> tuple[pd.DataFrame, pd.DataFrame]:
    """→ (X: catatan bukan-meme + gerbang pasar, R: catatan mentah untuk cek kecocokan)."""
    R = pd.read_csv(SINYAL)
    X = R[~R["meme"].astype(bool)].copy()
    X["tw"] = pd.to_datetime(X["waktu"])
    ph = pd.read_csv(os.path.join(BP.OUT, "pasar_harian.csv"), index_col="tanggal")
    X["tgl_gerbang"] = (X["tw"].dt.floor("D") - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")   # candle harian terakhir yang sudah tutup
    X = X.merge(ph[["skor", "rezim"]], left_on="tgl_gerbang", right_index=True, how="left").dropna(subset=["skor"])
    X["skor"] = X["skor"].astype(int)
    X["tanggal"], X["bulan"] = X["waktu"], X["waktu"].str[:7]
    return X.sort_values(["tw", "symbol", "strategi"]).reset_index(drop=True), R


def jeda(d: pd.DataFrame) -> pd.DataFrame:
    """Koin & jenis yang sama: ambil yang pertama, lalu lewati 240 jam berikutnya. d harus urut waktu."""
    pakai, akhir = [], {}
    batas = np.timedelta64(JEDA_JAM, "h")
    for i, (sy, tw) in enumerate(zip(d["symbol"].to_numpy(), d["tw"].to_numpy())):
        if sy in akhir and tw - akhir[sy] < batas:
            continue
        akhir[sy] = tw
        pakai.append(i)
    return d.iloc[pakai]


def susun(X: pd.DataFrame, mode: dict, batas, masuk: int = MASUK) -> pd.DataFrame:
    """Bangun satu sistem: per jenis sinyal pilih jam cek (fase0 / semua) → gerbang pasar → jeda 10 hari → kolom portofolio.
    batas = fungsi (tahun, sisi) → batas skor pasar."""
    bag = []
    for s, md in mode.items():
        sisi = JENIS[s][0]
        d = X[X["strategi"] == s]
        if md == "fase0":
            d = d[d["fase"] == 0]
        cap = np.array([batas(y, sisi) for y in d["tw"].dt.year.to_numpy()])
        d = jeda(d[(BP.rezim_ok(d, sisi) & (d["skor"].to_numpy() <= cap)).to_numpy()])
        bag.append(d)
    T = pd.concat(bag)
    T = T.assign(net=T[f"n{masuk}"], jam=T[f"j{masuk}"])
    T["buka"] = T["tw"] + masuk * JAM
    T["tutup"] = T["buka"] + pd.to_timedelta(T["jam"].clip(lower=1), unit="h")
    return T


def lolos(baru: dict, dasar: dict) -> bool:
    return bool(baru["total"] >= dasar["total"] and baru["total"] > 0 and baru["sharpe"] >= dasar["sharpe"]
                and baru["maxdd"] >= dasar["maxdd"] - 5)


def tahap_model(args) -> int:
    cfg = S.load_config()
    if not os.path.exists(SINYAL):
        print("backtest_berjalan/sinyal.csv.gz belum ada — jalankan tahap data & gabung dulu")
        return 1
    X, R = muat()
    T, _ = BP.muat_sinyal(cfg)
    U = T[~T["meme"]].copy()
    meta = json.load(open(os.path.join(OUT, "meta.json"), encoding="utf-8")) if os.path.exists(os.path.join(OUT, "meta.json")) else {}
    mp = json.load(open(os.path.join(BP.OUT, "model.json"), encoding="utf-8"))
    now = datetime.now(timezone.utc)
    akhir_h = U["ts"].max()
    akhir_data = min(akhir_h, X["tw"].max().floor("D"))
    tahun_uji = list(range(2023, int(akhir_data.year) + 1))
    oos_awal, oos_akhir = pd.Timestamp(f"{tahun_uji[0]}-01-01"), akhir_data + pd.Timedelta(days=31)
    bersih_ = lambda r: {k: v for k, v in r.items() if not k.startswith("_")}  # noqa: E731
    H = dict(versi=1, dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), data=meta,
             dari=str(X["waktu"].min()), sampai=str(X["waktu"].max()), masuk=MASUK, jeda_jam=JEDA_JAM,
             sistem={k: v[0] for k, v in SISTEM.items()})

    # gerbang pasar per tahun = uji model pasar (walk-forward); sinyal harian terbit untuk pembanding luar
    caps, bag_h = {}, []
    for th in tahun_uji:
        mulai = pd.Timestamp(f"{th}-01-01")
        sel = BP.pilih_v2(U[U["keluar"] < mulai], U["ts"].min(), mulai)
        caps[th] = dict(long=int(sel["long"]["batas"]), short=int(sel["short"]["batas"]))
        bag_h.append(BP.lolos_v2(U[(U["ts"] >= mulai) & (U["ts"] <= min(pd.Timestamp(f"{th}-12-31"), akhir_h))], sel, False))
    Td = pd.concat(bag_h)
    H["batas"] = {str(k): v for k, v in caps.items()}
    batas_uji = lambda y, sisi: caps[int(min(max(y, tahun_uji[0]), tahun_uji[-1]))][sisi]  # noqa: E731
    akhir_caps = dict(long=int(mp["beli"]["skor_maks"]), short=int(mp["jual"]["skor_maks"]))

    # ---------- 1) cek kecocokan: tepat jam 00.00 UTC mesin berjalan harus = mesin harian ----------
    dr = pd.read_csv(os.path.join(BP.OUT, "radar.csv.gz"), usecols=["tanggal", "symbol", "kelas", "skor"])
    dr["waktu"] = (pd.to_datetime(dr["tanggal"]) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%dT00:00")
    dr["strategi"] = "radar_" + dr["kelas"]
    r0 = R[(R["fase"] == 0) & R["strategi"].str.startswith("radar")]
    dr = dr[(dr["waktu"] >= R["waktu"].min()) & (dr["waktu"] <= R["waktu"].max()) & dr["symbol"].isin(R["symbol"].unique())]
    g = dr.merge(r0[["waktu", "symbol", "strategi", "skor_radar"]], on=["waktu", "symbol", "strategi"], how="left")
    ev = pd.read_csv(os.path.join(BP.OUT, "event.csv.gz"), usecols=["tanggal", "symbol", "event"])
    ev = ev[ev["event"].isin(["awal_stage2", "pantul_fib"])].rename(columns={"event": "strategi"})
    ev["waktu"] = (pd.to_datetime(ev["tanggal"]) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%dT00:00")
    ev = ev[(ev["waktu"] >= R["waktu"].min()) & (ev["waktu"] <= R["waktu"].max()) & ev["symbol"].isin(R["symbol"].unique())]
    e0 = R[(R["fase"] == 0) & R["strategi"].isin(["awal_stage2", "pantul_fib"])][["waktu", "symbol", "strategi"]].assign(ada=True)
    ge = ev.merge(e0, on=["waktu", "symbol", "strategi"], how="left")
    H["cek"] = dict(radar=dict(n=int(len(g)), ketemu=int(g["skor_radar"].notna().sum()), skor_sama=int((g["skor_radar"] == g["skor"]).sum())),
                    event={s: dict(n=int((ge["strategi"] == s).sum()), ketemu=int(ge.loc[ge["strategi"] == s, "ada"].eq(True).sum()))
                           for s in ("awal_stage2", "pantul_fib")})

    # ---------- 2) sistem & portofolio di luar sampel ----------
    Xo = X[X["tw"] >= oos_awal - pd.Timedelta(days=20)]          # sedikit sebelum 2023 supaya jeda 10 hari terbawa
    kol = ["tanggal", "symbol", "strategi", "net", "buka", "tutup"]
    Ts = {k: susun(Xo, v[1], batas_uji) for k, v in SISTEM.items()}
    res = {k: BJ.uji_w(Ts[k][kol], oos_awal, oos_akhir) for k in SISTEM}
    kurva = {SISTEM[k][0]: res[k].pop("_kurva") for k in SISTEM}
    terbit = BJ.uji_w(BJ.harian_w(Td)[kol], oos_awal, oos_akhir)
    terbit.pop("_kurva")
    tanpa_jeda = {k: BJ.uji_w(susun(Xo, SISTEM[k][1], batas_uji, 0)[kol], oos_awal, oos_akhir) for k in ("pembanding", "tiap_jam")}
    for v in tanpa_jeda.values():
        v.pop("_kurva")
    pasang = lambda a, b: dict(benih=BP.BENIH, total_lebih_baik=int((np.array(a["_total"]) > np.array(b["_total"])).sum()),  # noqa: E731
                               sharpe_lebih_baik=int((np.array(a["_sharpe"]) > np.array(b["_sharpe"])).sum()),
                               maxdd_lebih_baik=int((np.array(a["_maxdd"]) > np.array(b["_maxdd"])).sum()),
                               selisih_total_median=round(float(np.median(np.array(a["_total"]) - np.array(b["_total"]))), 1))
    uji_mask = lambda d: d[(d["buka"] >= oos_awal) & (d["buka"] < oos_akhir + pd.Timedelta(days=1))]  # noqa: E731
    H["oos"] = dict(dari=str(oos_awal.date()), sampai=str(akhir_data.date()),
                    portofolio={k: bersih_(res[k]) for k in SISTEM}, terbit=bersih_(terbit),
                    tanpa_jeda={k: bersih_(v) for k, v in tanpa_jeda.items()},
                    berpasangan=dict(tiap_jam=pasang(res["tiap_jam"], res["pembanding"]), semua=pasang(res["semua"], res["pembanding"])),
                    per_jenis={k: {s: BP.ringkas(uji_mask(Ts[k])[lambda d: d["strategi"] == s]) for s in JENIS} for k in SISTEM})
    pakai = lolos(res["tiap_jam"], res["pembanding"])

    # ---------- 3) penjelasan: seluruh data (batas model akhir), sebaran jam, seberapa lebih cepat ----------
    batas_akhir = lambda y, sisi: akhir_caps[sisi]  # noqa: E731
    Fa = {k: susun(X, v[1], batas_akhir) for k, v in SISTEM.items()}
    H["semua_data"] = {k: {s: BP.ringkas(Fa[k][Fa[k]["strategi"] == s]) for s in JENIS} for k in SISTEM}
    tj = Fa["tiap_jam"]
    tj = tj[tj["strategi"].isin(["awal_stage2", "pantul_fib"])]
    wib = ((tj["fase"] + 7) % 24).value_counts().reindex(range(24), fill_value=0)
    H["sebaran_wib"] = {str(k): int(v) for k, v in wib.items()}
    H["di_0700"] = round(float((tj["fase"] == 0).mean() * 100), 1) if len(tj) else None
    # seberapa lebih cepat: untuk tiap sinyal pembanding (07.00 WIB), adakah sinyal "tiap jam" koin & jenis sama dalam 24 jam sebelumnya?
    lebih = {}
    for s in ("awal_stage2", "pantul_fib"):
        a = Fa["pembanding"][Fa["pembanding"]["strategi"] == s]
        b = Fa["tiap_jam"][Fa["tiap_jam"]["strategi"] == s]
        peta = {sy: q["tw"].to_numpy() for sy, q in b.groupby("symbol")}
        maju = []
        for sy, tw in zip(a["symbol"].to_numpy(), a["tw"].to_numpy()):
            w = peta.get(sy)
            if w is None:
                continue
            i = int(np.searchsorted(w, tw, side="right")) - 1
            if i >= 0 and tw - w[i] <= np.timedelta64(10 * 24, "h"):
                maju.append(float((tw - w[i]) / np.timedelta64(1, "h")))
        lebih[s] = dict(n=int(len(a)), tertangkap=int(len(maju)), lebih_awal=int(sum(1 for x in maju if x > 0)),
                        median_jam=round(float(np.median([x for x in maju if x > 0])), 1) if any(x > 0 for x in maju) else None)
    H["lebih_cepat"] = lebih
    H["jumlah"] = {k: {s: int((Fa[k]["strategi"] == s).sum()) for s in JENIS} for k in SISTEM}

    H["putusan"] = dict(pakai=bool(pakai), alasan=f"di luar sampel {H['oos']['dari']} s/d {H['oos']['sampai']}: tiap jam {BJ.f_p(res['tiap_jam'])} — "
                                                  f"hanya 07.00 WIB {BJ.f_p(res['pembanding'])}")
    model = dict(versi=1, dibuat=H["dibuat"], dibuat_wib=H["dibuat_wib"], pakai=bool(pakai), putusan=H["putusan"]["alasan"],
                 jenis=["awal_stage2", "pantul_fib"], jeda_jam=JEDA_JAM,
                 uji={s: H["oos"]["per_jenis"]["tiap_jam"][s] for s in ("awal_stage2", "pantul_fib")})
    H["model"] = model

    # ---------- laporan ----------
    def f_r(r):
        return f"{r['rata']:+.2f}% · menang {r['menang']}% ({r['n']})" if r and r.get("n") else "-"
    ck = H["cek"]
    judul = "✅ 🟩 dan 🔻 DIHITUNG TIAP JAM (dipasang ke radar)" if pakai else "❌ Tidak dipasang — dihitung tiap jam tidak lebih baik dari sekali sehari"
    L = ["# 🕐 Uji \"Harian Berjalan\" — sinyal harian yang dihitung ulang tiap jam", "",
         f"Dibuat {H['dibuat_wib']} · {meta.get('koin', '?')} koin · {meta.get('analisa', 0):,} analisa (tiap koin × tiap jam, ±{meta.get('jam_mesin', '?')} jam mesin) · "
         f"catatan {H['dari']} s/d {H['sampai']} UTC · meme coin tidak ikut", "",
         "## Putusan", "", f"**{judul}.**", "",
         f"- 🟩 & 🔻 dicek tiap jam: {BJ.f_p(res['tiap_jam'])}", f"- Hanya dicek 07.00 WIB (sistem sekarang): {BJ.f_p(res['pembanding'])}",
         "- Syarat (ditetapkan di muka): total ≥ pembanding, Sharpe ≥ pembanding, maks turun tidak lebih buruk dari pembanding − 5 poin.", "",
         "## Yang diuji", "",
         "Mesin radar harian dijalankan apa adanya di setiap jam pada candle 24 jam berjalan (24 jam terakhir = satu candle, dst.). "
         "Tepat jam 07.00 WIB candle berjalan sama dengan candle harian biasa, jadi sistem sekarang adalah bagian darinya. "
         "Kedua sistem memakai aturan yang sama: gerbang model pasar, jeda 10 hari per koin & jenis sinyal, masuk di penutupan candle "
         "1 jam berikutnya, rencana jual TP1 5% / SL 12% / maks 30 hari yang disimulasikan pada candle 1 jam, biaya & pajak dipotong.", "",
         f"Cek mesin: dari {ck['radar']['n']} sinyal radar uji harian, {ck['radar']['ketemu']} ditemukan mesin berjalan tepat di jam 00.00 UTC "
         f"({ck['radar']['skor_sama']} dengan skor yang sama persis). Sinyal stage uji harian yang juga muncul di mesin berjalan jam 00.00 UTC: "
         f"🟩 {ck['event']['awal_stage2']['ketemu']} dari {ck['event']['awal_stage2']['n']}, 🔻 {ck['event']['pantul_fib']['ketemu']} dari {ck['event']['pantul_fib']['n']} "
         "(uji harian menghitung stage dari seluruh riwayat; mesin berjalan & radar live dari 400 candle terakhir).", "",
         f"## Uji portofolio di luar sampel ({H['oos']['dari']} s/d {H['oos']['sampai']})", "",
         f"Maks {BP.MAKS_POSISI} posisi, modal dibagi rata, median dari {BP.BENIH} urutan acak (dalam kurung = terendah…tertinggi).", "",
         "| Sistem | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |", "|---|---|---|---|---|---|---|---|"]

    def baris(nm, r):
        if not r.get("transaksi"):
            return f"| {nm} | tidak ada transaksi | | | | | | |"
        pt = " · ".join(f"{y}: {v:+.0f}%" for y, v in r["per_tahun"].items())
        return (f"| {nm} | **{r['total']:+.1f}%** ({r['total_min']:+.0f}…{r['total_maks']:+.0f}) | {pt} | {r['maxdd']:.1f}% | {r['sharpe']} | "
                f"{r['transaksi']} dari {r['kandidat']} | {r['menang']}% | {r['rata']:+.2f}% |")
    L += [baris(SISTEM[k][0], H["oos"]["portofolio"][k]) for k in SISTEM]
    L += [baris("(acuan) angka uji harian yang sudah terbit — candle harian, tanpa jeda masuk", H["oos"]["terbit"]),
          baris("(pembanding) hanya 07.00 WIB, masuk tanpa jeda 1 jam", H["oos"]["tanpa_jeda"]["pembanding"]),
          baris("(pembanding) 🟩 & 🔻 tiap jam, masuk tanpa jeda 1 jam", H["oos"]["tanpa_jeda"]["tiap_jam"])]
    b1, b2 = H["oos"]["berpasangan"]["tiap_jam"], H["oos"]["berpasangan"]["semua"]
    L += ["", f"Berpasangan ({b1['benih']} urutan acak yang sama): '🟩 & 🔻 tiap jam' lebih tinggi totalnya dari 'hanya 07.00 WIB' di {b1['total_lebih_baik']} urutan, "
              f"Sharpe lebih tinggi di {b1['sharpe_lebih_baik']}, penurunan maksimum lebih kecil di {b1['maxdd_lebih_baik']}; selisih total (median) {b1['selisih_total_median']:+.1f} poin. "
              f"'Semua tiap jam': total lebih tinggi di {b2['total_lebih_baik']}, Sharpe di {b2['sharpe_lebih_baik']}.", "",
          "### Hasil per jenis sinyal", "",
          "Isi sel: rata-rata bersih per transaksi · tingkat menang (jumlah sinyal).", "",
          "| Jenis | Di luar sampel: hanya 07.00 WIB | Di luar sampel: tiap jam | Seluruh data 2020–2026: hanya 07.00 WIB | Seluruh data: tiap jam |", "|---|---|---|---|---|"]
    for s, (_, nm) in JENIS.items():
        md = "semua" if s == "radar_naik" else "tiap_jam"
        L.append(f"| {nm} | {f_r(H['oos']['per_jenis']['pembanding'][s])} | {f_r(H['oos']['per_jenis'][md][s])} | "
                 f"{f_r(H['semua_data']['pembanding'][s])} | {f_r(H['semua_data'][md][s])} |")
    L += ["", "(Untuk 🟢 radar kolom 'tiap jam' berasal dari sistem 'semua tiap jam'; di sistem yang diputuskan 🟢 tetap seperti sekarang.)", "",
          "### Kapan sinyal 🟩 & 🔻 muncul bila dicek tiap jam (seluruh data)", "",
          f"Tepat jam 07.00 WIB: {H['di_0700']}% — sisanya tersebar di jam lain.", "",
          "| Jam WIB | " + " | ".join(f"{k:02d}" for k in range(24)) + " |", "|---|" + "---|" * 24,
          "| Sinyal | " + " | ".join(str(H["sebaran_wib"][str(k)]) for k in range(24)) + " |", "",
          "| Jenis | Sinyal 07.00 WIB | Sudah tertangkap versi tiap jam (≤10 hari sebelumnya) | Lebih awal | Median lebih awal |", "|---|---|---|---|---|"]
    for s in ("awal_stage2", "pantul_fib"):
        x = H["lebih_cepat"][s]
        L.append(f"| {JENIS[s][1]} | {x['n']} | {x['tertangkap']} | {x['lebih_awal']} | {x['median_jam'] if x['median_jam'] is not None else '-'} jam |")
    L += ["", "## Catatan jujur", "",
          "- 'Hanya 07.00 WIB' di sini dihitung ulang dengan cara yang sama dengan versi tiap jam (simulasi pada candle 1 jam, masuk dengan "
          "jeda 1 jam, jeda 10 hari setelah gerbang, stage dari 400 candle terakhir seperti radar live), jadi angkanya tidak sama persis "
          "dengan angka uji harian yang sudah terbit — baris '(acuan)' di tabel menunjukkan selisihnya.",
          "- Versi tiap jam melihat lebih banyak kesempatan (24 kali sehari), jadi sinyalnya sedikit lebih banyak dan bisa lebih awal "
          "maupun lebih lambat daripada versi 07.00 WIB.",
          "- Daftar koin = koin top CMC saat ini (yang sudah mati tidak ikut); untung-rugi dicatat saat posisi ditutup.",
          "- Aturan uji ditulis sebelum data ditarik. Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual."]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as f:
        json.dump(BT._json_safe(H), f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "model.json"), "w", encoding="utf-8") as f:
        json.dump(BT._json_safe(model), f, ensure_ascii=False, indent=1)
    kv = pd.DataFrame(kurva)
    kv.index.name = "tanggal"
    kv.round(4).to_csv(os.path.join(OUT, "kurva.csv"))
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tahap", choices=["data", "gabung", "model", "semua"], nargs="?", default="semua")
    ap.add_argument("--mulai", default="2020-01-01")
    ap.add_argument("--koin", type=int, default=0, help="batasi jumlah koin (0 = semua)")
    ap.add_argument("--sejak", default="", help="hanya analisa jam sejak tanggal ini (uji cepat); kosong = semua")
    ap.add_argument("--bagian", type=int, default=0)
    ap.add_argument("--dari", type=int, default=1)
    args = ap.parse_args()
    if args.tahap in ("data", "semua"):
        rc = tahap_data(args)
        if rc:
            return rc
    if args.tahap in ("gabung", "semua"):
        rc = tahap_gabung(args)
        if rc:
            return rc
    if args.tahap in ("model", "semua"):
        return tahap_model(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
