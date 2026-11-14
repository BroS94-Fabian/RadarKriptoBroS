#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODEL KONDISI PASAR — uji & pemilihan model yang mengikuti kondisi pasar
========================================================================
Tahap `data`  : candle harian Binance sejak 2020 (koin top CMC) → semua kandidat sinyal + hasilnya:
                  beli  : 🟢 radar, awal Stage 2, tembus atap dasar, pullback Fibonacci Stage 2, beli acak
                  jual  : pantulan Stage 4 ke Fibonacci, awal Stage 4, jebol lantai puncak, 🔴 radar, short acak
                dan tabel kondisi pasar harian (skor pasar −6…+6, lihat pasar.py).
Tahap `model` : 1) pilih, untuk tiap strategi, mulai skor pasar berapa ia boleh jalan — HANYA dari data
                   sebelum tahun uji (walk-forward: uji 2023, 2024, 2025, 2026);
                2) simulasi portofolio (maks N posisi, modal dibagi rata) di tahun-tahun uji:
                   model lama (aturan tetap yang sekarang live) vs model baru (mengikuti skor pasar);
                3) model akhir (dilatih dari semua data) → model_pasar/model.json, dibaca radar.

Hasil: model_pasar/LAPORAN.md, model.json, hasil.json, radar.csv.gz, event.csv.gz, pasar_harian.csv
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

import backtest as BT
import backtest_short as BS
import pasar as P
import scanner as S
import siklus as SK
import strategi as ST

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_pasar")
TAHUN_UJI = [2023, 2024, 2025, 2026]
MIN_N, MIN_BULAN, MIN_T = 40, 12, 2.0
TOLERANSI_T = 0.5     # di antara kandidat yang t-nya hampir sama, pilih yang paling longgar (sinyal terbanyak)
MAKS_POSISI = 5
BENIH = 20            # jumlah urutan acak saat slot penuh (hasil = median)

STRATEGI = {
    # kode: (sisi, nama, sumber)
    "radar_naik": ("long", "🟢 Sinyal radar (skor ≥55)"),
    "awal_stage2": ("long", "🟩 Awal Stage 2"),
    "tembus_dasar": ("long", "Tembus atap dasar + volume"),
    "pullback_fib": ("long", "Pullback Stage 2 ke Fibonacci"),
    "pantul_fib": ("short", "🔻 Pantulan Stage 4 ke Fibonacci"),
    "awal_stage4": ("short", "Awal Stage 4"),
    "jebol_puncak": ("short", "Jebol lantai puncak + volume"),
    "radar_turun": ("short", "🔴 Sinyal radar turun"),
}
# Model lama = aturan tetap yang sekarang live (BTC MA50)
LAMA = {"radar_naik": lambda d: d["rezim"] == "naik", "awal_stage2": lambda d: d["rezim"] == "naik",
        "pantul_fib": lambda d: d["rezim"] != "naik"}


# --------------------------------------------------------------------------- #
# Tahap data
# --------------------------------------------------------------------------- #
def harian_lengkap(bn: S.Binance, sym: str, mulai: pd.Timestamp) -> pd.DataFrame:
    """Candle harian sejak `mulai`, format sama dengan Binance.candles (hanya candle yang sudah tutup)."""
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
    df = df[df["ct"].astype("int64") < int(time.time() * 1000)].drop_duplicates("t")
    return pd.DataFrame({
        "time": pd.to_datetime(df["t"].astype("int64"), unit="ms", utc=True),
        "open": df["o"].astype(float), "high": df["h"].astype(float), "low": df["l"].astype(float),
        "close": df["c"].astype(float), "volume": df["v"].astype(float), "qvol": df["qv"].astype(float),
        "taker_buy_q": df["tbqv"].astype(float), "closed": True,
    }).reset_index(drop=True)


def kerja(job):
    sym, base, rank, meme, d, rezim, btc_close, cfg = job
    radar, ev_long = BT.proses_koin(job)
    d2 = d.set_index(d["time"].dt.normalize())[["open", "high", "low", "close", "volume"]]
    ev_short = BS.proses((sym, meme, d2, rezim))
    o, h, l, c, v = (d[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close", "volume"))
    F = SK.hitung(o, h, l, c, v)
    fk = P.fitur_koin(c)
    idx = d["time"].dt.normalize()
    fitur = pd.DataFrame(dict(atas50=fk["atas50"], r30=fk["r30"], stage=F["stage"], close=c), index=idx)
    return sym, radar, ev_long, ev_short, fitur


def tahap_data(args) -> int:
    t0 = time.time()
    now = datetime.now(timezone.utc)
    cfg, state = S.load_config(), S.load_state()
    bn = S.Binance()
    rank_list, src = S.ambil_ranking(cfg, state, now)
    tick = bn.tickers(cfg["quote"])
    koin = []
    for c in sorted(rank_list, key=lambda x: x["rank"]):
        b = S.ALIAS_BINANCE.get(c["symbol"], c["symbol"])
        if c.get("stabil") or c["symbol"] in cfg["abaikan"] or b not in tick:
            continue
        koin.append((tick[b]["symbol"], c["symbol"], c["rank"], bool(c.get("meme")) or ST.is_meme(c["symbol"])))
    koin = koin[:args.koin]
    if not any(k[0] == "BTCUSDT" for k in koin):
        koin.insert(0, ("BTCUSDT", "BTC", 1, False))
    mulai = pd.Timestamp(args.mulai, tz="UTC")
    print(f"Ranking {src}: {len(koin)} koin, data harian sejak {args.mulai}...")
    data = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(harian_lengkap, bn, k[0], mulai): k for k in koin}
        for f in as_completed(futs):
            try:
                d = f.result()
                if len(d) >= 60:
                    data[futs[f][0]] = d
            except Exception as e:
                print("  ! gagal", futs[f][0], e)
    btc = data.get("BTCUSDT")
    if btc is None or len(btc) < 400:
        print("Data BTC tidak tersedia")
        return 1
    tg = btc["time"].dt.strftime("%Y-%m-%d").to_numpy()
    rezim = dict(zip(tg, ST.rezim_series(btc["close"].to_numpy())))
    btc_close = dict(zip(tg, btc["close"].to_numpy().astype(float)))
    print(f"Data {len(data)} koin siap ({time.time() - t0:.0f} dtk). Simulasi...")

    jobs = [(sym, base, rank, meme, data[sym], rezim, btc_close, cfg) for sym, base, rank, meme in koin if sym in data]
    jobs.sort(key=lambda j: -len(j[4]))
    info = {sym: (base, rank, meme) for sym, base, rank, meme in koin}
    radar, ev_long, ev_short, fitur = [], [], [], {}
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for i, (sym, a, b, c, f) in enumerate(ex.map(kerja, jobs, chunksize=1), start=1):
            radar.extend(a)
            ev_long.extend(b)
            ev_short.extend(c)
            fitur[sym] = f
            if i % 20 == 0:
                print(f"  {i}/{len(jobs)} koin · radar {len(radar)} · event {len(ev_long) + len(ev_short)} · {time.time() - t0:.0f} dtk")

    # Kondisi pasar harian
    atas50 = pd.DataFrame({s: f["atas50"] for s, f in fitur.items()})
    r30 = pd.DataFrame({s: f["r30"] for s, f in fitur.items()})
    stage = pd.DataFrame({s: f["stage"] for s, f in fitur.items()}).fillna(0)
    btc_s = pd.Series(btc["close"].to_numpy(dtype=float), index=btc["time"].dt.normalize())
    ph = P.harian(btc_s, atas50, r30, stage, btc_kol="BTCUSDT")
    ph.index = ph.index.strftime("%Y-%m-%d")
    ph.index.name = "tanggal"

    # rs30 koin (kenaikan 30 hari koin − BTC) untuk tiap sinyal
    rs = r30.sub(r30["BTCUSDT"], axis=0)
    rs.index = rs.index.strftime("%Y-%m-%d")
    rs_long = rs.stack().rename("rs30").reset_index()
    rs_long.columns = ["tanggal", "symbol", "rs30"]

    dr = pd.DataFrame(radar)
    el = pd.DataFrame(ev_long).assign(sisi="long")
    es = pd.DataFrame(ev_short).assign(sisi="short")
    ev = pd.concat([el, es], ignore_index=True)
    ev["base"] = ev["symbol"].map(lambda s: info[s][0])
    ev["rank"] = ev["symbol"].map(lambda s: info[s][1])
    dr = dr.merge(rs_long, on=["tanggal", "symbol"], how="left")
    ev = ev.merge(rs_long, on=["tanggal", "symbol"], how="left")
    os.makedirs(OUT, exist_ok=True)
    dr.to_csv(os.path.join(OUT, "radar.csv.gz"), index=False, compression="gzip")
    ev.to_csv(os.path.join(OUT, "event.csv.gz"), index=False, compression="gzip")
    ph.round(3).to_csv(os.path.join(OUT, "pasar_harian.csv"))
    meta = dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), ranking=src, koin=len(jobs),
                mulai=args.mulai, radar=len(dr), event=len(ev), durasi_detik=round(time.time() - t0))
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"Data selesai: radar {len(dr)} · event {len(ev)} · hari {len(ph)} · {time.time() - t0:.0f} dtk")
    return 0


# --------------------------------------------------------------------------- #
# Tahap model
# --------------------------------------------------------------------------- #
def muat_sinyal(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Satu tabel semua kandidat sinyal: tanggal, symbol, meme, sisi, strategi, net (% bersih), hari, rs30, skor pasar."""
    ph = pd.read_csv(os.path.join(OUT, "pasar_harian.csv"), index_col="tanggal")
    dr = pd.read_csv(os.path.join(OUT, "radar.csv.gz"))
    ev = pd.read_csv(os.path.join(OUT, "event.csv.gz"))
    Bs = dict(BS.BIAYA_KONS, **(cfg.get("biaya_short") or {}))
    Bsp = ST.cfg_biaya(cfg)
    a = Bsp["fee_beli_persen"] + Bsp["fee_jual_persen"] + Bsp["pajak_jual_persen"]
    b = (Bsp["fee_jual_persen"] + Bsp["pajak_jual_persen"]) / 100
    kol = ["tanggal", "symbol", "base", "meme", "sisi", "strategi", "net", "hari", "rs30", "skor_radar"]
    bag = []
    # radar: rencana bawaan (50% di +5%, sisa ke target pola, SL 12%)
    rn = dr[dr["kelas"] == "naik"].assign(sisi="long", strategi="radar_naik")
    rn = rn.assign(net=rn["pola_tp5_sl12_bersih"], hari=rn["pola_tp5_sl12_hari"], skor_radar=rn["skor"])
    rt = dr[dr["kelas"] == "turun"].assign(sisi="short", strategi="radar_turun")
    pnl = (rt["pola_tp5_sl12_bersih"] + a) / (1 - b)          # balik ke untung kotor, lalu biaya short
    rt = rt.assign(net=BS.bersih(pnl, rt["pola_tp5_sl12_hari"], Bs), hari=rt["pola_tp5_sl12_hari"], skor_radar=rt["skor"])
    bag += [rn[kol], rt[kol]]
    el = ev[ev["sisi"] == "long"].copy()
    el["strategi"] = el["event"].replace({"acak": "acak_long"})
    el = el.assign(net=el["rencana_bersih"], hari=el["rencana_hari"], skor_radar=np.nan)
    es = ev[ev["sisi"] == "short"].copy()
    es["strategi"] = es["event"].replace({"acak": "acak_short"})
    es = es.assign(net=BS.bersih(es["rencana_pnl"], es["rencana_hari"], Bs), hari=es["rencana_hari"], skor_radar=np.nan)
    bag += [el[kol], es[kol]]
    T = pd.concat(bag, ignore_index=True)
    T = T.merge(ph[["skor", "rezim"] + [f"v_{k}" for k, _ in P.KOMPONEN]], left_on="tanggal", right_index=True, how="left")
    T = T.dropna(subset=["skor", "net"])
    T["skor"] = T["skor"].astype(int)
    T["ts"] = pd.to_datetime(T["tanggal"])
    T["keluar"] = T["ts"] + pd.to_timedelta(T["hari"].clip(lower=1), unit="D")
    T["bulan"] = T["tanggal"].str[:7]
    T["meme"] = T["meme"].astype(bool)
    return T, ph


def t_kluster(x: pd.Series, kl: pd.Series) -> float | None:
    """t-statistik rata-rata dengan galat baku ber-kluster (sinyal di bulan yang sama dianggap saling terkait)."""
    n = len(x)
    if n < 2:
        return None
    m = x.mean()
    s = (x - m).groupby(kl).sum()
    G = len(s)
    if G < 2:
        return None
    var = float((s ** 2).sum()) / n ** 2 * G / (G - 1)
    return float(m / np.sqrt(var)) if var > 0 else None


def ringkas(d: pd.DataFrame) -> dict:
    if len(d) == 0:
        return dict(n=0)
    x = d["net"]
    t = t_kluster(x, d["bulan"])
    return dict(n=int(len(x)), bulan=int(d["bulan"].nunique()), menang=round(float((x > 0).mean() * 100), 1),
                rata=round(float(x.mean()), 2), median=round(float(x.median()), 2),
                t=round(t, 2) if t is not None else None)


def saring(d: pd.DataFrame, sisi: str, batas: int, rs: bool) -> pd.DataFrame:
    m = (d["skor"] >= batas) if sisi == "long" else (d["skor"] <= batas)
    if rs:
        m &= (d["rs30"] > 0) if sisi == "long" else (d["rs30"] < 0)
    return d[m]


def pilih(latih: pd.DataFrame, sisi: str) -> dict:
    """Pilih batas skor pasar (dan filter kekuatan relatif) terbaik dari data latih."""
    kand = []
    grid = range(-6, 6) if sisi == "long" else range(6, -6, -1)
    for rs in (False, True):
        for k in grid:
            sub = saring(latih, sisi, k, rs)
            r = ringkas(sub)
            if r["n"] >= MIN_N and r["bulan"] >= MIN_BULAN and r["rata"] > 0 and r["t"] is not None:
                kand.append(dict(r, skor_batas=int(k), rs=rs))
    if not kand:
        return dict(aktif=False, alasan="sinyal latih kurang / rata-rata tidak positif")
    t_maks = max(k["t"] for k in kand)
    dekat = [k for k in kand if k["t"] >= t_maks - TOLERANSI_T]
    best = max(dekat, key=lambda k: (k["n"], not k["rs"]))
    best["aktif"] = bool(best["t"] >= MIN_T)
    if not best["aktif"]:
        best["alasan"] = f"t {best['t']} < {MIN_T}"
    return best


def portofolio(T: pd.DataFrame, awal: pd.Timestamp, akhir: pd.Timestamp, maks: int = MAKS_POSISI, benih: int = 0) -> dict:
    """Simulasi portofolio: maks `maks` posisi, tiap posisi = modal saat itu / maks, untung-rugi dicatat saat tutup."""
    hari = pd.date_range(awal, akhir, freq="D")
    eq = np.ones(len(hari))
    if len(T) == 0:
        return dict(kurva=pd.Series(eq, index=hari), transaksi=0, menang=None, rata=None, terisi=0.0)
    rng = np.random.default_rng(benih)
    T = T.assign(_u=rng.random(len(T))).sort_values(["ts", "_u"])
    per_hari = {k: g for k, g in T.groupby("ts")}
    modal, buka, hasil, terisi = 1.0, [], [], 0
    for i, d in enumerate(hari):
        sisa = []
        for pos in buka:
            if pos[0] <= d:
                modal += pos[1] * pos[2] / 100
                hasil.append(pos[2])
            else:
                sisa.append(pos)
        buka = sisa
        g = per_hari.get(d)
        if g is not None and len(buka) < maks:
            pegang = {p[3] for p in buka}
            for row in g.itertuples():
                if len(buka) >= maks:
                    break
                if row.symbol in pegang:
                    continue
                buka.append((row.keluar, modal / maks, row.net, row.symbol))
                pegang.add(row.symbol)
        terisi += len(buka) > 0
        eq[i] = modal
    for pos in buka:   # posisi yang masih terbuka di akhir periode ditutup di hasil simulasinya
        modal += pos[1] * pos[2] / 100
        hasil.append(pos[2])
    eq[-1] = modal
    h = np.array(hasil) if hasil else np.array([np.nan])
    return dict(kurva=pd.Series(eq, index=hari), transaksi=len(hasil), menang=float(np.nanmean(h > 0) * 100) if hasil else None,
                rata=float(np.nanmean(h)) if hasil else None, terisi=terisi / len(hari) * 100)


def metrik(kurva: pd.Series) -> dict:
    tot = float(kurva.iloc[-1] / kurva.iloc[0] - 1) * 100
    th = (kurva.index[-1] - kurva.index[0]).days / 365.25
    cagr = ((kurva.iloc[-1] / kurva.iloc[0]) ** (1 / th) - 1) * 100 if th > 0 and kurva.iloc[-1] > 0 else np.nan
    dd = float((kurva / kurva.cummax() - 1).min()) * 100
    bl = kurva.resample("ME").last().pct_change().dropna()
    sharpe = float(bl.mean() / bl.std() * np.sqrt(12)) if len(bl) > 2 and bl.std() > 0 else np.nan
    per_th = {str(y): round(float(g.iloc[-1] / g.iloc[0] - 1) * 100, 1) for y, g in kurva.groupby(kurva.index.year)}
    return dict(total=round(tot, 1), cagr=round(float(cagr), 1), maxdd=round(dd, 1), sharpe=round(sharpe, 2),
                per_tahun=per_th, bulan_rugi=round(float((bl < 0).mean() * 100), 0) if len(bl) else None)


def uji_portofolio(T: pd.DataFrame, awal, akhir, maks=MAKS_POSISI) -> dict:
    runs = [portofolio(T, awal, akhir, maks, b) for b in range(BENIH)]
    ms = [metrik(r["kurva"]) for r in runs]
    def med(k):
        x = [m[k] for m in ms if np.isfinite(m[k])]
        return round(float(np.median(x)), 2) if x else 0.0
    tahun = sorted({y for m in ms for y in m["per_tahun"]})
    return dict(total=med("total"), total_min=round(min(m["total"] for m in ms), 1), total_maks=round(max(m["total"] for m in ms), 1),
                cagr=med("cagr"), maxdd=med("maxdd"), sharpe=med("sharpe"),
                per_tahun={y: round(float(np.median([m["per_tahun"].get(y, 0) for m in ms])), 1) for y in tahun},
                transaksi=int(np.median([r["transaksi"] for r in runs])),
                menang=round(float(np.median([r["menang"] for r in runs])), 1) if len(T) else None,
                rata=round(float(np.median([r["rata"] for r in runs])), 2) if len(T) else None,
                terisi=round(float(np.median([r["terisi"] for r in runs])), 0), kandidat=int(len(T)),
                _kurva=runs[0]["kurva"])


def lolos_lama(d: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([d[(d["strategi"] == s) & f(d)] for s, f in LAMA.items()]) if len(d) else d


def lolos_baru(d: pd.DataFrame, aturan: dict) -> pd.DataFrame:
    bag = []
    for s, a in aturan.items():
        if a.get("aktif"):
            bag.append(saring(d[d["strategi"] == s], STRATEGI[s][0], a["skor_batas"], a["rs"]))
    return pd.concat(bag) if bag else d.iloc[0:0]


def f_r(r: dict) -> str:
    if not r or not r.get("n"):
        return "-"
    return f"{r['rata']:+.2f}% ({r['n']}, menang {r['menang']}%)"


def tahap_model(args) -> int:
    cfg = S.load_config()
    T, ph = muat_sinyal(cfg)
    meta = json.load(open(os.path.join(OUT, "meta.json"), encoding="utf-8"))
    now = datetime.now(timezone.utc)
    U = T[~T["meme"]].copy()                       # sama seperti live: meme coin tidak ikut
    akhir_data = U["ts"].max()
    H = dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), data=meta,
             dari=str(U["tanggal"].min()), sampai=str(U["tanggal"].max()), maks_posisi=MAKS_POSISI,
             syarat=dict(min_n=MIN_N, min_bulan=MIN_BULAN, min_t=MIN_T))

    # 1) Gambaran: hasil tiap strategi per kondisi pasar (seluruh data, deskriptif)
    ember = [("bear (≤−4)", -6, -4), ("turun (−3…−2)", -3, -2), ("netral (−1…+1)", -1, 1), ("naik (+2…+3)", 2, 3),
             ("bull (≥+4)", 4, 6)]
    H["per_mode"] = {}
    for s in list(STRATEGI) + ["acak_long", "acak_short"]:
        d = U[U["strategi"] == s]
        H["per_mode"][s] = {nm: ringkas(d[(d["skor"] >= lo) & (d["skor"] <= hi)]) for nm, lo, hi in ember}
        H["per_mode"][s]["semua"] = ringkas(d)
    hari_mode = {nm: int(((ph["skor"] >= lo) & (ph["skor"] <= hi)).sum()) for nm, lo, hi in ember}
    H["hari_per_mode"] = hari_mode

    # 2) Walk-forward: aturan dipilih dari data sebelum tahun uji
    H["walk"] = {}
    bag_baru, bag_lama = [], []
    for th in TAHUN_UJI:
        mulai = pd.Timestamp(f"{th}-01-01")
        selesai = min(pd.Timestamp(f"{th}-12-31"), akhir_data)
        if mulai > akhir_data:
            continue
        latih = U[U["keluar"] < mulai]              # hanya sinyal yang sudah selesai sebelum tahun uji
        uji = U[(U["ts"] >= mulai) & (U["ts"] <= selesai)]
        aturan = {s: pilih(latih[latih["strategi"] == s], STRATEGI[s][0]) for s in STRATEGI}
        for s, a in aturan.items():
            if a.get("aktif"):
                a["uji"] = ringkas(saring(uji[uji["strategi"] == s], STRATEGI[s][0], a["skor_batas"], a["rs"]))
        H["walk"][str(th)] = aturan
        bag_baru.append(lolos_baru(uji, aturan))
        bag_lama.append(lolos_lama(uji))
    oos_awal = pd.Timestamp(f"{TAHUN_UJI[0]}-01-01")
    oos_akhir = akhir_data + pd.Timedelta(days=31)
    Tb, Tl = pd.concat(bag_baru), pd.concat(bag_lama)
    Usem = U[(U["ts"] >= oos_awal) & U["strategi"].isin(list(LAMA))]
    susunan = {
        "Model LAMA (aturan tetap BTC MA50)": Tl,
        "Model BARU (mengikuti skor pasar)": Tb,
        "LAMA — hanya beli": Tl[Tl["sisi"] == "long"],
        "BARU — hanya beli": Tb[Tb["sisi"] == "long"],
        "LAMA — hanya jual dulu (short)": Tl[Tl["sisi"] == "short"],
        "BARU — hanya jual dulu (short)": Tb[Tb["sisi"] == "short"],
        "Tanpa filter pasar (3 strategi live, semua kondisi)": Usem,
    }
    H["oos"] = dict(dari=str(oos_awal.date()), sampai=str(akhir_data.date()), portofolio={}, per_sinyal={})
    kurva = {}
    for nm, d in susunan.items():
        r = uji_portofolio(d, oos_awal, oos_akhir)
        kurva[nm] = r.pop("_kurva")
        H["oos"]["portofolio"][nm] = r
        H["oos"]["per_sinyal"][nm] = ringkas(d)
    H["oos"]["portofolio_10"] = {nm: {k: v for k, v in uji_portofolio(susunan[nm], oos_awal, oos_akhir, 10).items() if k != "_kurva"}
                                 for nm in list(susunan)[:2]}
    b = ph["btc_close"]
    b.index = pd.to_datetime(b.index)
    bb = b[(b.index >= oos_awal) & (b.index <= oos_akhir)]
    H["oos"]["btc"] = dict(metrik(bb / bb.iloc[0]))
    # per strategi di luar sampel
    H["oos"]["per_strategi"] = {}
    for s in STRATEGI:
        H["oos"]["per_strategi"][s] = dict(baru=ringkas(Tb[Tb["strategi"] == s]), lama=ringkas(Tl[Tl["strategi"] == s]),
                                           semua=ringkas(U[(U["ts"] >= oos_awal) & (U["strategi"] == s)]))

    # 3) Model akhir: dilatih dari semua data
    akhir_latih = U[U["keluar"] <= akhir_data + pd.Timedelta(days=31)]
    final = {}
    for s, (sisi, nama) in STRATEGI.items():
        a = pilih(akhir_latih[akhir_latih["strategi"] == s], sisi)
        a.update(sisi=sisi, nama=nama)
        final[s] = a
    pl, pb = H["oos"]["portofolio"]["Model LAMA (aturan tetap BTC MA50)"], H["oos"]["portofolio"]["Model BARU (mengikuti skor pasar)"]
    lolos = bool(pb["total"] > pl["total"] and pb["total"] > 0 and pb["sharpe"] >= pl["sharpe"] and pb["maxdd"] >= pl["maxdd"] - 5)
    H["putusan"] = dict(pakai=lolos, alasan=(
        f"di luar sampel {H['oos']['dari']}–{H['oos']['sampai']}: BARU {pb['total']:+.1f}% (maks turun {pb['maxdd']:.1f}%, "
        f"Sharpe {pb['sharpe']}) vs LAMA {pl['total']:+.1f}% (maks turun {pl['maxdd']:.1f}%, Sharpe {pl['sharpe']})"))
    skr = ph.iloc[-1]
    H["sekarang"] = dict(tanggal=str(ph.index[-1])[:10], skor=int(skr["skor"]), **P.mode(int(skr["skor"])),
                         komponen={k: int(skr[f"v_{k}"]) for k, _ in P.KOMPONEN},
                         lebar50=float(skr["lebar50"]), s2=float(skr["s2"]), s4=float(skr["s4"]))
    model = dict(dibuat=H["dibuat"], dibuat_wib=H["dibuat_wib"], data=f"{H['dari']} s/d {H['sampai']}", pakai=lolos,
                 putusan=H["putusan"]["alasan"], ambang=P.AMBANG, strategi=final,
                 oos=dict(dari=H["oos"]["dari"], sampai=H["oos"]["sampai"], baru=pb, lama=pl))
    H["model"] = final

    # ---------- laporan ----------
    L = ["# 🌡️ Model Kondisi Pasar", "",
         f"Dibuat {H['dibuat_wib']} · {meta['koin']} koin · sinyal {H['dari']} s/d {H['sampai']} · meme coin tidak ikut", "",
         "## Putusan", "",
         f"**{'✅ Model BARU dipakai' if lolos else '❌ Model BARU tidak dipakai (radar tetap memakai aturan lama)'}** — {H['putusan']['alasan']}.", "",
         f"## Uji portofolio di luar sampel ({H['oos']['dari']} s/d {H['oos']['sampai']})", "",
         f"Maks {MAKS_POSISI} posisi sekaligus, tiap posisi = modal ÷ {MAKS_POSISI}, tanpa leverage. Aturan model baru untuk tiap tahun "
         "dipilih hanya dari data tahun-tahun sebelumnya. Saat slot penuh, sinyal dipilih acak (median dari "
         f"{BENIH} urutan).", "",
         "| Susunan | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi | Hari ada posisi |",
         "|---|---|---|---|---|---|---|---|---|"]
    for nm, r in H["oos"]["portofolio"].items():
        pt = " · ".join(f"{y}: {v:+.0f}%" for y, v in r["per_tahun"].items())
        if not r["kandidat"]:
            L.append(f"| {nm} | tidak ada sinyal | - | - | - | 0 | - | - | 0% |")
            continue
        L.append(f"| {nm} | **{r['total']:+.1f}%** ({r['total_min']:+.0f}…{r['total_maks']:+.0f}) | {pt} | {r['maxdd']:.1f}% | {r['sharpe']} | "
                 f"{r['transaksi']} dari {r['kandidat']} | {r['menang']}% | {r['rata']:+.2f}% | {r['terisi']:.0f}% |")
    bt = H["oos"]["btc"]
    L.append(f"| Pembanding: beli & tahan BTC | {bt['total']:+.1f}% | " + " · ".join(f"{y}: {v:+.0f}%" for y, v in bt["per_tahun"].items())
             + f" | {bt['maxdd']:.1f}% | {bt['sharpe']} | - | - | - | 100% |")
    L += ["", "Dengan maks 10 posisi: " + " · ".join(
        f"{nm.split(' (')[0]} {r['total']:+.1f}% (maks turun {r['maxdd']:.1f}%)" for nm, r in H["oos"]["portofolio_10"].items()), "",
          "### Per sinyal di luar sampel (tanpa batas slot)", "",
          "| Strategi | Model baru | Model lama | Semua sinyal (tanpa filter) |", "|---|---|---|---|"]
    for s, (sisi, nama) in STRATEGI.items():
        x = H["oos"]["per_strategi"][s]
        L.append(f"| {nama} ({'beli' if sisi == 'long' else 'jual dulu'}) | {f_r(x['baru'])} | {f_r(x['lama'])} | {f_r(x['semua'])} |")
    L += ["", "## Aturan yang terpilih tiap tahun uji (walk-forward)", "",
          "| Tahun uji | Strategi | Aturan dari data sebelumnya | Hasil latih | Hasil di tahun uji |", "|---|---|---|---|---|"]
    for th, aturan in H["walk"].items():
        for s, a in aturan.items():
            sisi, nama = STRATEGI[s]
            if a.get("aktif"):
                syarat = f"skor pasar {'≥' if sisi == 'long' else '≤'} {a['skor_batas']:+d}" + (" + koin lebih kuat dari BTC" if a["rs"] and sisi == "long" else " + koin lebih lemah dari BTC" if a["rs"] else "")
                L.append(f"| {th} | {nama} | {syarat} | {f_r(a)} · t {a['t']} | {f_r(a.get('uji'))} |")
            else:
                L.append(f"| {th} | {nama} | ✖ tidak aktif ({a.get('alasan', '-')}) | {f_r(a) if a.get('n') else '-'} | - |")
    L += ["", "## Model akhir (dilatih dari semua data, dipakai radar bila putusan ✅)", "",
          "| Strategi | Sisi | Aturan | Sinyal | Menang | Rata-rata | t (kluster bulan) |", "|---|---|---|---|---|---|---|"]
    for s, a in final.items():
        sisi = a["sisi"]
        if a.get("aktif"):
            syarat = f"skor pasar {'≥' if sisi == 'long' else '≤'} {a['skor_batas']:+d}" + (" + koin lebih kuat dari BTC" if a["rs"] and sisi == "long" else " + koin lebih lemah dari BTC" if a["rs"] else "")
            L.append(f"| {a['nama']} | {'beli' if sisi == 'long' else 'jual dulu'} | {syarat} | {a['n']} | {a['menang']}% | {a['rata']:+.2f}% | {a['t']} |")
        else:
            L.append(f"| {a['nama']} | {'beli' if sisi == 'long' else 'jual dulu'} | ✖ tidak aktif ({a.get('alasan', '-')}) | {a.get('n', '-')} | - | - | {a.get('t', '-')} |")
    L += ["", "## Hasil tiap strategi menurut kondisi pasar (seluruh data, deskriptif)", "",
          "Jumlah hari per kondisi: " + " · ".join(f"{k} {v}" for k, v in hari_mode.items()), "",
          "| Strategi | " + " | ".join(nm for nm, _, _ in ember) + " | Semua |", "|---|" + "---|" * (len(ember) + 1)]
    nama_s = dict({s: v[1] for s, v in STRATEGI.items()}, acak_long="Pembanding: beli acak", acak_short="Pembanding: short acak")
    for s, x in H["per_mode"].items():
        L.append(f"| {nama_s[s]} | " + " | ".join(f_r(x[nm]) for nm, _, _ in ember) + f" | {f_r(x['semua'])} |")
    k = H["sekarang"]
    L += ["", "## Kondisi pasar pada akhir data", "",
          f"{k['tanggal']}: skor **{k['skor']:+d}** ({k['ikon']} {k['nama']}) · koin di atas MA50 {k['lebar50']:.0f}% · "
          f"Stage 2 {k['s2']:.0f}% · Stage 4 {k['s4']:.0f}%", "",
          "## Catatan", "",
          "- Skor pasar memakai ambang bulat yang ditetapkan di muka; yang dipilih dari data hanya batas skor tiap strategi.",
          "- Model lama disetel memakai data 2024–2026 (beli) dan 2020–2026 (short), jadi di uji ini model lama diuntungkan.",
          "- Daftar koin = top CMC saat ini (koin yang sudah mati tidak ikut): hasil beli cenderung terlalu bagus, hasil short terlalu jelek.",
          "- Untung-rugi dicatat saat posisi ditutup; penurunan sementara di tengah posisi tidak terlihat di 'maks turun'.",
          "- Biaya: beli/jual 0,1% + pajak jual 0,21%; short 0,1% + 0,1% + pajak 0,21% + funding 0,03%/hari.",
          "- Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual."]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as f:
        json.dump(BT._json_safe(H), f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "model.json"), "w", encoding="utf-8") as f:
        json.dump(BT._json_safe(model), f, ensure_ascii=False, indent=1)
    kv = pd.DataFrame({nm: k_ for nm, k_ in kurva.items()})
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
    ap.add_argument("tahap", choices=["data", "model", "semua"], nargs="?", default="semua")
    ap.add_argument("--mulai", default="2020-01-01")
    ap.add_argument("--koin", type=int, default=150)
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
