#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODEL KONDISI PASAR — uji & pemilihan model yang mengikuti kondisi pasar
========================================================================
Tahap `data`  : candle harian Binance sejak 2020 (koin top CMC) → semua kandidat sinyal + hasilnya:
                  beli  : 🟢 radar, awal Stage 2, tembus atap dasar, pullback Fibonacci Stage 2, beli acak
                  jual  : pantulan Stage 4 ke Fibonacci, awal Stage 4, jebol lantai puncak, 🔴 radar, short acak
                dan tabel kondisi pasar harian (skor pasar −6…+6, lihat pasar.py).
Tahap `model` : Model = aturan lama (beli hanya saat BTC tren naik; jual dulu hanya saat BTC tidak tren naik)
                + BATAS SKOR PASAR per sisi (mis. beli hanya bila skor ≤ +4 = pasar belum kepanasan).
                1) walk-forward: untuk tiap tahun uji (2023 dst.), batas dipilih HANYA dari data tahun-tahun
                   sebelumnya (Sharpe portofolio latih; yang hampir setara → pilih yang paling longgar);
                2) simulasi portofolio (maks 5 posisi, modal dibagi rata) di tahun-tahun uji: model lama vs baru,
                   dengan urutan acak yang sama untuk keduanya;
                3) model akhir (dilatih dari semua data) → model_pasar/model.json. "pakai" = true hanya bila
                   model baru mengalahkan model lama di luar sampel (untung total, Sharpe, penurunan maksimum).
                Percobaan 1 (ambang skor per strategi dengan syarat t ≥ 2) gagal dan tetap dilaporkan apa adanya.

Hasil: model_pasar/LAPORAN.md, model.json, hasil.json, kurva.csv, radar.csv.gz, event.csv.gz, pasar_harian.csv
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
TAHUN_UJI = [2023, 2024, 2025, 2026]   # diperpanjang otomatis sampai tahun terakhir data (lihat tahap_model)
MIN_N, MIN_BULAN, MIN_T = 40, 12, 2.0
TOLERANSI_T = 0.5     # di antara kandidat yang t-nya hampir sama, pilih yang paling longgar (sinyal terbanyak)
MAKS_POSISI = 5
BENIH = 100           # jumlah urutan acak saat slot penuh (hasil = median)

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
    ev = pd.read_csv(os.path.join(OUT, "event.csv.gz"), low_memory=False)
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


def saring(d: pd.DataFrame, sisi: str, batas: int, rs: bool, kol: str = "skor") -> pd.DataFrame:
    m = (d[kol] >= batas) if sisi == "long" else (d[kol] <= batas)
    if rs:
        m &= (d["rs30"] > 0) if sisi == "long" else (d["rs30"] < 0)
    return d[m]


def pilih(latih: pd.DataFrame, sisi: str, kol: str = "skor", maks: int = 6) -> dict:
    """Pilih batas skor pasar (dan filter kekuatan relatif) terbaik dari data latih."""
    kand = []
    grid = range(-maks, maks) if sisi == "long" else range(maks, -maks, -1)
    for rs in (False, True):
        for k in grid:
            sub = saring(latih, sisi, k, rs, kol)
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
    """Simulasi portofolio: maks `maks` posisi, tiap posisi = modal saat itu / maks, untung-rugi dicatat saat tutup.
    Tiap hari: tutup dulu posisi yang jatuh tempo, lalu buka sinyal hari itu selama slot masih ada (satu koin satu posisi)."""
    hari = pd.date_range(awal, akhir, freq="D")
    n = len(hari)
    eq = np.ones(n)
    if len(T) == 0:
        return dict(kurva=pd.Series(eq, index=hari), transaksi=0, menang=None, rata=None, terisi=0.0)
    # urutan prioritas acak tapi "berpasangan": sinyal yang sama mendapat angka yang sama di model mana pun
    kunci = [k for k in ("tanggal", "symbol", "strategi") if k in T.columns] or ["symbol"]
    u = pd.util.hash_pandas_object(T[kunci].assign(_b=benih), index=False).to_numpy(dtype=np.uint64) / np.float64(2 ** 64)
    d0 = np.datetime64(pd.Timestamp(awal).to_datetime64(), "D")
    ti = (T["ts"].to_numpy().astype("datetime64[D]") - d0).astype(np.int64)
    ki = (T["keluar"].to_numpy().astype("datetime64[D]") - d0).astype(np.int64)
    net, sym = T["net"].to_numpy(dtype=float), T["symbol"].to_numpy()
    urut = np.lexsort((u, ti))
    ti, ki, net, sym = ti[urut], ki[urut], net[urut], sym[urut]
    m, p = len(ti), int(np.searchsorted(ti, 0, side="left"))
    modal, buka, hasil, terisi = 1.0, [], [], 0
    for i in range(n):
        if buka:
            sisa = []
            for pos in buka:
                if pos[0] <= i:
                    modal += pos[1] * pos[2] / 100
                    hasil.append(pos[2])
                else:
                    sisa.append(pos)
            buka = sisa
        while p < m and ti[p] == i:
            if len(buka) < maks and not any(q[3] == sym[p] for q in buka):
                buka.append((ki[p], modal / maks, net[p], sym[p]))
            p += 1
        terisi += len(buka) > 0
        eq[i] = modal
    for pos in buka:   # posisi yang masih terbuka di akhir periode ditutup di hasil simulasinya
        modal += pos[1] * pos[2] / 100
        hasil.append(pos[2])
    eq[-1] = modal
    h = np.array(hasil) if hasil else np.array([np.nan])
    return dict(kurva=pd.Series(eq, index=hari), transaksi=len(hasil), menang=float(np.nanmean(h > 0) * 100) if hasil else None,
                rata=float(np.nanmean(h)) if hasil else None, terisi=terisi / n * 100)


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
                _kurva=runs[0]["kurva"], _total=[m["total"] for m in ms], _sharpe=[m["sharpe"] for m in ms],
                _maxdd=[m["maxdd"] for m in ms])


def lolos_lama(d: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([d[(d["strategi"] == s) & f(d)] for s, f in LAMA.items()]) if len(d) else d


def lolos_baru(d: pd.DataFrame, aturan: dict, kol: str = "skor") -> pd.DataFrame:
    bag = []
    for s, a in aturan.items():
        if a.get("aktif"):
            bag.append(saring(d[d["strategi"] == s], STRATEGI[s][0], a["skor_batas"], a["rs"], kol))
    return pd.concat(bag) if bag else d.iloc[0:0]


def walk_forward(U: pd.DataFrame, akhir_data: pd.Timestamp, kol: str = "skor", maks: int = 6):
    """PERCOBAAN 1 (gagal): tiap strategi boleh jalan mulai skor tertentu, syarat t ≥ 2."""
    per_tahun, bag = {}, []
    for th in TAHUN_UJI:
        mulai = pd.Timestamp(f"{th}-01-01")
        selesai = min(pd.Timestamp(f"{th}-12-31"), akhir_data)
        if mulai > akhir_data:
            continue
        latih = U[U["keluar"] < mulai]
        uji = U[(U["ts"] >= mulai) & (U["ts"] <= selesai)]
        aturan = {s: pilih(latih[latih["strategi"] == s], STRATEGI[s][0], kol, maks) for s in STRATEGI}
        for s, a in aturan.items():
            if a.get("aktif"):
                a["uji"] = ringkas(saring(uji[uji["strategi"] == s], STRATEGI[s][0], a["skor_batas"], a["rs"], kol))
        per_tahun[str(th)] = aturan
        bag.append(lolos_baru(uji, aturan, kol))
    return pd.concat(bag), per_tahun


# --------------------------------------------------------------------------- #
# Model versi 2: aturan lama (arah BTC) + batas "pasar kepanasan / belum cukup lemah" yang dipilih dari data
# --------------------------------------------------------------------------- #
LIVE = {"long": ["radar_naik", "awal_stage2"], "short": ["pantul_fib"]}
PENDATANG = {"long": ["tembus_dasar", "pullback_fib"], "short": ["awal_stage4", "jebol_puncak", "radar_turun"]}
BATAS = {"long": [6, 5, 4, 3, 2, 1], "short": [6, 1, -1, -2, -3]}   # skor pasar maksimum (6 = tanpa batas = aturan lama)
MIN_LATIH = 30          # minimal sinyal latih supaya sebuah batas boleh dinilai
BENIH_LATIH = 25        # urutan acak untuk menilai tiap batas di data latih
TOLERANSI_SHARPE = 0.10  # batas yang Sharpe latihnya ≤0,1 di bawah yang terbaik dianggap setara → pilih yang paling longgar
TAMBAH_SHARPE = 0.05    # strategi pendatang masuk bila menaikkan Sharpe portofolio latih minimal segini
SELISIH_B = 0.15        # versi "dengan pendatang" dipilih hanya bila Sharpe uji lebih tinggi minimal segini


def rezim_ok(d: pd.DataFrame, sisi: str) -> pd.Series:
    return (d["rezim"] == "naik") if sisi == "long" else (d["rezim"] != "naik")


def gerbang(d: pd.DataFrame, sisi: str, batas: int) -> pd.DataFrame:
    """Beli: BTC tren naik & skor pasar ≤ batas. Jual dulu: BTC tidak tren naik & skor pasar ≤ batas."""
    return d[rezim_ok(d, sisi) & (d["skor"] <= batas)]


def nilai_latih(T: pd.DataFrame, awal, akhir) -> dict:
    ms = [metrik(portofolio(T, awal, akhir, MAKS_POSISI, b)["kurva"]) for b in range(BENIH_LATIH)]
    sh = [m["sharpe"] for m in ms if np.isfinite(m["sharpe"])]
    return dict(sharpe=float(np.median(sh)) if sh else -9.0, total=float(np.median([m["total"] for m in ms])))


def pilih_v2(latih: pd.DataFrame, awal, akhir) -> dict:
    """Dari data latih: batas skor terbaik per sisi (Sharpe portofolio latih), lalu strategi pendatang yang menambah Sharpe."""
    out = {}
    for sisi in ("long", "short"):
        pool = latih[latih["strategi"].isin(LIVE[sisi])]
        kand = []
        for b in BATAS[sisi]:
            g = gerbang(pool, sisi, b)
            if len(g) < MIN_LATIH:
                continue
            v = nilai_latih(g, awal, akhir)
            kand.append(dict(batas=b, n=int(len(g)), rata=round(float(g["net"].mean()), 2), sharpe=round(v["sharpe"], 2),
                             total=round(v["total"], 1)))
        if kand:
            # di antara batas yang Sharpe-nya hampir sama dengan yang terbaik, pilih yang paling longgar (lebih stabil)
            s_maks = max(k["sharpe"] for k in kand)
            best = max((k for k in kand if k["sharpe"] >= s_maks - TOLERANSI_SHARPE), key=lambda k: k["batas"])
        else:
            best = dict(batas=6, n=int(len(gerbang(pool, sisi, 6))), rata=None, sharpe=None, total=None)
        strategi, base, s_base, tambahan = list(LIVE[sisi]), gerbang(pool, sisi, best["batas"]), best["sharpe"], {}
        for s in PENDATANG[sisi]:
            g = gerbang(latih[latih["strategi"] == s], sisi, best["batas"])
            info = dict(n=int(len(g)), rata=round(float(g["net"].mean()), 2) if len(g) else None, masuk=False)
            if s_base is not None and len(g) >= MIN_LATIH and g["net"].mean() > 0:
                v = nilai_latih(pd.concat([base, g]), awal, akhir)
                info["sharpe_gabung"] = round(v["sharpe"], 2)
                if v["sharpe"] >= s_base + TAMBAH_SHARPE:
                    strategi.append(s)
                    base, s_base, info["masuk"] = pd.concat([base, g]), v["sharpe"], True
            tambahan[s] = info
        out[sisi] = dict(batas=int(best["batas"]), sharpe=best["sharpe"], n=best["n"], rata=best["rata"], kandidat=kand,
                         strategi=strategi, pendatang=tambahan)
    return out


def lolos_v2(d: pd.DataFrame, sel: dict, pendatang: bool) -> pd.DataFrame:
    bag = []
    for sisi in ("long", "short"):
        ss = sel[sisi]["strategi"] if pendatang else LIVE[sisi]
        bag.append(gerbang(d[d["strategi"].isin(ss)], sisi, sel[sisi]["batas"]))
    return pd.concat(bag)


def walk_v2(U: pd.DataFrame, akhir_data: pd.Timestamp):
    per, bag_a, bag_b = {}, [], []
    awal_latih = U["ts"].min()
    for th in TAHUN_UJI:
        mulai = pd.Timestamp(f"{th}-01-01")
        if mulai > akhir_data:
            continue
        latih = U[U["keluar"] < mulai]              # hanya sinyal yang sudah selesai sebelum tahun uji
        uji = U[(U["ts"] >= mulai) & (U["ts"] <= min(pd.Timestamp(f"{th}-12-31"), akhir_data))]
        sel = pilih_v2(latih, awal_latih, mulai)
        a, b = lolos_v2(uji, sel, False), lolos_v2(uji, sel, True)
        for sisi in ("long", "short"):
            sel[sisi]["uji"] = ringkas(a[a["sisi"] == sisi])
            sel[sisi]["uji_lama"] = ringkas(gerbang(uji[uji["strategi"].isin(LIVE[sisi])], sisi, 6))
        per[str(th)] = sel
        bag_a.append(a)
        bag_b.append(b)
    return pd.concat(bag_a), pd.concat(bag_b), per


def f_r(r: dict) -> str:
    if not r or not r.get("n"):
        return "-"
    return f"{r['rata']:+.2f}% ({r['n']}, menang {r['menang']}%)"


def teks_gerbang(sisi: str, batas: int) -> str:
    if sisi == "long":
        return "BTC tren naik" + (f" & skor pasar ≤ {batas:+d}" if batas < 6 else " (tanpa batas skor)")
    return "BTC tidak tren naik" + (f" & skor pasar ≤ {batas:+d}" if batas < 6 else " (tanpa batas skor)")


def tahap_model(args) -> int:
    cfg = S.load_config()
    T, ph = muat_sinyal(cfg)
    meta = json.load(open(os.path.join(OUT, "meta.json"), encoding="utf-8"))
    now = datetime.now(timezone.utc)
    U = T[~T["meme"]].copy()                       # sama seperti live: meme coin tidak ikut
    U["mode"] = U["skor"].map(lambda x: P.mode(int(x))["kode"])
    akhir_data = U["ts"].max()
    TAHUN_UJI[:] = list(range(2023, int(akhir_data.year) + 1))
    H = dict(versi=2, dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), data=meta,
             dari=str(U["tanggal"].min()), sampai=str(U["tanggal"].max()), maks_posisi=MAKS_POSISI)
    MODE = ["bear", "turun", "netral", "naik", "bull"]
    NAMA_MODE = {"bear": "sangat lemah (≤−4)", "turun": "lemah (−3…−2)", "netral": "campuran (−1…+1)",
                 "naik": "kuat (+2…+3)", "bull": "sangat kuat (≥+4)"}

    # 1) Gambaran: hasil per kondisi pasar (seluruh data, deskriptif)
    H["per_mode"] = {}
    for s in list(STRATEGI) + ["acak_long", "acak_short"]:
        d = U[U["strategi"] == s]
        H["per_mode"][s] = {NAMA_MODE[m]: ringkas(d[d["mode"] == m]) for m in MODE}
        H["per_mode"][s]["semua"] = ringkas(d)
    phm = ph["skor"].map(lambda x: P.mode(int(x))["kode"])
    H["hari_per_mode"] = {NAMA_MODE[m]: int((phm == m).sum()) for m in MODE}
    H["inti"] = {}
    for sisi, nm in (("long", "beli"), ("short", "jual")):
        g = U[U["strategi"].isin(LIVE[sisi]) & rezim_ok(U, sisi)]
        a = U[(U["strategi"] == ("acak_long" if sisi == "long" else "acak_short")) & rezim_ok(U, sisi)]
        H["inti"][nm] = dict(sinyal={NAMA_MODE[m]: ringkas(g[g["mode"] == m]) for m in MODE},
                             acak={NAMA_MODE[m]: ringkas(a[a["mode"] == m]) for m in MODE},
                             hari={NAMA_MODE[m]: int(((phm == m) & ((ph["rezim"] == "naik") if sisi == "long" else (ph["rezim"] != "naik"))).sum())
                                   for m in MODE})

    # 2) Walk-forward
    oos_awal = pd.Timestamp(f"{TAHUN_UJI[0]}-01-01")
    oos_akhir = akhir_data + pd.Timedelta(days=31)
    Ta, Tb, H["walk"] = walk_v2(U, akhir_data)
    T1, H["walk_percobaan1"] = walk_forward(U, akhir_data)
    O = U[U["ts"] >= oos_awal]
    Tl = lolos_lama(O)
    A, B, LM = "Model BARU (aturan lama + batas skor pasar)", "Model BARU + strategi pendatang", "Model LAMA (aturan tetap BTC MA50)"
    susunan = {
        LM: Tl, A: Ta, B: Tb,
        "LAMA — hanya beli": Tl[Tl["sisi"] == "long"], "BARU — hanya beli": Ta[Ta["sisi"] == "long"],
        "LAMA — hanya jual dulu (short)": Tl[Tl["sisi"] == "short"], "BARU — hanya jual dulu (short)": Ta[Ta["sisi"] == "short"],
        "Percobaan 1 (ambang skor per strategi, syarat t ≥ 2) — gagal": T1,
        "Tanpa filter pasar (3 strategi live, semua kondisi)": O[O["strategi"].isin(list(LAMA))],
    }
    H["oos"] = dict(dari=str(oos_awal.date()), sampai=str(akhir_data.date()), portofolio={}, per_sinyal={})
    kurva = {}
    per_benih = {}
    for nm, d in susunan.items():
        r = uji_portofolio(d, oos_awal, oos_akhir)
        kurva[nm] = r.pop("_kurva")
        per_benih[nm] = dict(total=r.pop("_total"), sharpe=r.pop("_sharpe"), maxdd=r.pop("_maxdd"))
        H["oos"]["portofolio"][nm] = r
        H["oos"]["per_sinyal"][nm] = ringkas(d)
    bersih_ = lambda r: {k: v for k, v in r.items() if not k.startswith("_")}  # noqa: E731
    H["oos"]["portofolio_10"] = {nm: bersih_(uji_portofolio(susunan[nm], oos_awal, oos_akhir, 10)) for nm in (LM, A, B)}
    H["oos"]["portofolio_3"] = {nm: bersih_(uji_portofolio(susunan[nm], oos_awal, oos_akhir, 3)) for nm in (LM, A)}
    # perbandingan berpasangan: urutan acak yang sama untuk kedua model
    tb, tl_ = np.array(per_benih[A]["total"]), np.array(per_benih[LM]["total"])
    sb, sl_ = np.array(per_benih[A]["sharpe"]), np.array(per_benih[LM]["sharpe"])
    db, dl_ = np.array(per_benih[A]["maxdd"]), np.array(per_benih[LM]["maxdd"])
    H["oos"]["berpasangan"] = dict(benih=BENIH, total_lebih_baik=int((tb > tl_).sum()), sharpe_lebih_baik=int((sb > sl_).sum()),
                                   maxdd_lebih_baik=int((db > dl_).sum()), selisih_total_median=round(float(np.median(tb - tl_)), 1))
    # kepekaan: batas beli tetap (bukan walk-forward) — apakah hasil bergantung pada satu angka batas?
    H["oos"]["kepekaan"] = {}
    for b in BATAS["long"]:
        d = pd.concat([gerbang(O[O["strategi"].isin(LIVE["long"])], "long", b), Tl[Tl["sisi"] == "short"]])
        H["oos"]["kepekaan"][str(b)] = bersih_(uji_portofolio(d, oos_awal, oos_akhir))
    bc = ph["btc_close"].copy()
    bc.index = pd.to_datetime(bc.index)
    bb = bc[(bc.index >= oos_awal) & (bc.index <= oos_akhir)]
    H["oos"]["btc"] = dict(metrik(bb / bb.iloc[0]))
    H["oos"]["per_strategi"] = {}
    for s in STRATEGI:
        H["oos"]["per_strategi"][s] = dict(baru=ringkas(Ta[Ta["strategi"] == s]), baru_b=ringkas(Tb[Tb["strategi"] == s]),
                                           lama=ringkas(Tl[Tl["strategi"] == s]), semua=ringkas(O[O["strategi"] == s]))

    # 3) Putusan
    P_ = H["oos"]["portofolio"]
    pl, pa, pb = P_[LM], P_[A], P_[B]
    pakai_b = bool(pb["sharpe"] >= pa["sharpe"] + SELISIH_B and pb["total"] > pa["total"])
    pk, nama_k = (pb, B) if pakai_b else (pa, A)
    lolos = bool(pk["total"] > pl["total"] and pk["total"] > 0 and pk["sharpe"] >= pl["sharpe"] and pk["maxdd"] >= pl["maxdd"] - 5)
    H["putusan"] = dict(pakai=lolos, versi=nama_k, pendatang=pakai_b, alasan=(
        f"di luar sampel {H['oos']['dari']} s/d {H['oos']['sampai']}: BARU {pk['total']:+.1f}% (maks turun {pk['maxdd']:.1f}%, "
        f"Sharpe {pk['sharpe']}) vs LAMA {pl['total']:+.1f}% (maks turun {pl['maxdd']:.1f}%, Sharpe {pl['sharpe']})"))

    # 4) Model akhir: dilatih dari semua data
    sel = pilih_v2(U[U["keluar"] <= oos_akhir], U["ts"].min(), oos_akhir)
    final = {}
    for s, (sisi, nama) in STRATEGI.items():
        aktif = s in (sel[sisi]["strategi"] if pakai_b else LIVE[sisi])
        g = gerbang(U[U["strategi"] == s], sisi, sel[sisi]["batas"])
        final[s] = dict(aktif=bool(aktif), sisi=sisi, nama=nama, live=s in LIVE[sisi], **ringkas(g))
    skr = ph.iloc[-1]
    H["sekarang"] = dict(tanggal=str(ph.index[-1])[:10], skor=int(skr["skor"]), rezim=str(skr["rezim"]), **P.mode(int(skr["skor"])),
                         komponen={k: int(skr[f"v_{k}"]) for k, _ in P.KOMPONEN},
                         lebar50=float(skr["lebar50"]), s2=float(skr["s2"]), s4=float(skr["s4"]))
    ekor = ph.tail(730)
    H["riwayat_skor"] = [dict(t=str(i)[:10], s=int(r["skor"]), b=round(float(r["btc_close"]), 0)) for i, r in ekor.iterrows()]
    model = dict(versi=2, dibuat=H["dibuat"], dibuat_wib=H["dibuat_wib"], data=f"{H['dari']} s/d {H['sampai']}", pakai=lolos,
                 putusan=H["putusan"]["alasan"], ambang=P.AMBANG,
                 beli=dict(rezim="naik", skor_maks=sel["long"]["batas"], teks=teks_gerbang("long", sel["long"]["batas"])),
                 jual=dict(rezim_bukan="naik", skor_maks=sel["short"]["batas"], teks=teks_gerbang("short", sel["short"]["batas"])),
                 strategi=final, oos=dict(dari=H["oos"]["dari"], sampai=H["oos"]["sampai"], baru=pk, lama=pl))
    H["model"] = dict(beli=model["beli"], jual=model["jual"], strategi=final, pilihan=sel)

    # ---------- laporan ----------
    def baris_p(nm, r):
        if not r["kandidat"]:
            return f"| {nm} | tidak ada sinyal | - | - | - | 0 | - | - | 0% |"
        pt = " · ".join(f"{y}: {v:+.0f}%" for y, v in r["per_tahun"].items())
        return (f"| {nm} | **{r['total']:+.1f}%** ({r['total_min']:+.0f}…{r['total_maks']:+.0f}) | {pt} | {r['maxdd']:.1f}% | {r['sharpe']} | "
                f"{r['transaksi']} dari {r['kandidat']} | {r['menang']}% | {r['rata']:+.2f}% | {r['terisi']:.0f}% |")
    L = ["# 🌡️ Model Kondisi Pasar", "",
         f"Dibuat {H['dibuat_wib']} · {meta['koin']} koin · sinyal {H['dari']} s/d {H['sampai']} · meme coin tidak ikut", "",
         "## Putusan", "",
         f"**{'✅ Model BARU dipakai radar' if lolos else '❌ Model BARU tidak dipakai (radar tetap memakai aturan lama)'}** — {H['putusan']['alasan']}.", "",
         f"Model baru = aturan lama (beli hanya saat BTC tren naik, jual dulu hanya saat BTC tidak tren naik) **ditambah batas skor pasar** "
         f"yang dipilih dari data: beli → {model['beli']['teks']}; jual dulu → {model['jual']['teks']}.", "",
         f"## Uji portofolio di luar sampel ({H['oos']['dari']} s/d {H['oos']['sampai']})", "",
         f"Maks {MAKS_POSISI} posisi sekaligus, tiap posisi = modal ÷ {MAKS_POSISI}, tanpa leverage. Batas skor untuk tiap tahun uji "
         "dipilih hanya dari data tahun-tahun sebelumnya (walk-forward). Saat slot penuh, sinyal dipilih acak (median dari "
         f"{BENIH} urutan; dalam kurung = terendah…tertinggi).", "",
         "| Susunan | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi | Hari ada posisi |",
         "|---|---|---|---|---|---|---|---|---|"]
    L += [baris_p(nm, r) for nm, r in P_.items()]
    bt = H["oos"]["btc"]
    L.append(f"| Pembanding: beli & tahan BTC | {bt['total']:+.1f}% | " + " · ".join(f"{y}: {v:+.0f}%" for y, v in bt["per_tahun"].items())
             + f" | {bt['maxdd']:.1f}% | {bt['sharpe']} | - | - | - | 100% |")
    bp = H["oos"]["berpasangan"]
    L += ["", f"Perbandingan berpasangan (urutan acak yang sama untuk kedua model, {bp['benih']} urutan): model baru lebih tinggi total "
              f"untungnya di **{bp['total_lebih_baik']} dari {bp['benih']}**, Sharpe lebih tinggi di {bp['sharpe_lebih_baik']}, "
              f"penurunan maksimum lebih kecil di {bp['maxdd_lebih_baik']}; selisih total (median) {bp['selisih_total_median']:+.1f} poin.", "",
          "Dengan maks 3 posisi: " + " · ".join(
        f"{nm.split(' (')[0]} {r['total']:+.1f}% (maks turun {r['maxdd']:.1f}%, Sharpe {r['sharpe']})" for nm, r in H["oos"]["portofolio_3"].items()), "",
          "Dengan maks 10 posisi: " + " · ".join(
        f"{nm.split(' (')[0]} {r['total']:+.1f}% (maks turun {r['maxdd']:.1f}%, Sharpe {r['sharpe']})" for nm, r in H["oos"]["portofolio_10"].items()), "",
          "### Aturan yang terpilih tiap tahun uji", "",
          "| Tahun uji | Sisi | Batas terpilih dari data sebelumnya | Sharpe latih tiap batas | Hasil di tahun uji (model baru) | Bila tanpa batas (aturan lama) | Pendatang yang masuk |",
          "|---|---|---|---|---|---|---|"]
    for th, sl in H["walk"].items():
        for sisi in ("long", "short"):
            x = sl[sisi]
            kd = " · ".join(f"≤{k['batas']:+d}: {k['sharpe']}" if k["batas"] < 6 else f"tanpa: {k['sharpe']}" for k in x["kandidat"]) or "data latih kurang"
            pd_ = ", ".join(STRATEGI[s][1] for s, v in x["pendatang"].items() if v.get("masuk")) or "-"
            L.append(f"| {th} | {'beli' if sisi == 'long' else 'jual dulu'} | {teks_gerbang(sisi, x['batas'])} | {kd} | {f_r(x['uji'])} | "
                     f"{f_r(x['uji_lama'])} | {pd_} |")
    L += ["", "### Uji kepekaan: batas beli dipasang tetap sepanjang 2023–2026 (BUKAN walk-forward)", "",
          "Untuk melihat apakah hasil bergantung pada satu angka batas saja. Sisi jual dulu memakai aturan lama.", "",
          "| Beli hanya bila skor pasar | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |", "|---|---|---|---|---|---|---|---|"]
    for b, r in H["oos"]["kepekaan"].items():
        pt = " · ".join(f"{y}: {v:+.0f}%" for y, v in r["per_tahun"].items())
        L.append(f"| {'tanpa batas (= model lama)' if b == '6' else '≤ ' + format(int(b), '+d')} | {r['total']:+.1f}% | {pt} | {r['maxdd']:.1f}% | {r['sharpe']} | "
                 f"{r['transaksi']} | {r['menang']}% | {r['rata']:+.2f}% |")
    L += ["", "## Kenapa: hasil sinyal menurut kondisi pasar (seluruh data 2020–2026)", "",
          "Sinyal beli live (🟢 radar + 🟩 awal Stage 2) **saat BTC tren naik**, dan sinyal 🔻 jual dulu **saat BTC tidak tren naik**:", "",
          "| | " + " | ".join(NAMA_MODE[m] for m in MODE) + " |", "|---|" + "---|" * len(MODE)]
    for nm, judul in (("beli", "Sinyal beli"), ("jual", "Sinyal jual dulu")):
        x = H["inti"][nm]
        L.append(f"| {judul} | " + " | ".join(f_r(x["sinyal"][NAMA_MODE[m]]) for m in MODE) + " |")
        L.append(f"| ↳ pembanding: {'beli' if nm == 'beli' else 'short'} acak | " + " | ".join(f_r(x["acak"][NAMA_MODE[m]]) for m in MODE) + " |")
        L.append("| ↳ jumlah hari | " + " | ".join(str(x["hari"][NAMA_MODE[m]]) for m in MODE) + " |")
    L += ["", "## Model akhir (dilatih dari semua data)", "",
          f"- **Beli** boleh jalan saat: {model['beli']['teks']}", f"- **Jual dulu** boleh jalan saat: {model['jual']['teks']}", "",
          "| Strategi | Sisi | Status | Sinyal di kondisi yang diizinkan | Menang | Rata-rata bersih |", "|---|---|---|---|---|---|"]
    for s, a in final.items():
        status = "✅ aktif" if a["aktif"] else ("✖ tidak aktif" if not a["live"] else "✖")
        L.append(f"| {a['nama']} | {'beli' if a['sisi'] == 'long' else 'jual dulu'} | {status} | {a.get('n', 0)} | "
                 f"{str(a['menang']) + '%' if a.get('n') else '-'} | {format(a['rata'], '+.2f') + '%' if a.get('n') else '-'} |")
    L += ["", "## Hasil tiap strategi menurut kondisi pasar (semua arah BTC, deskriptif)", "",
          "Jumlah hari per kondisi: " + " · ".join(f"{k} {v}" for k, v in H["hari_per_mode"].items()), "",
          "| Strategi | " + " | ".join(NAMA_MODE[m] for m in MODE) + " | Semua |", "|---|" + "---|" * (len(MODE) + 1)]
    nama_s = dict({s: v[1] for s, v in STRATEGI.items()}, acak_long="Pembanding: beli acak", acak_short="Pembanding: short acak")
    for s, x in H["per_mode"].items():
        L.append(f"| {nama_s[s]} | " + " | ".join(f_r(x[NAMA_MODE[m]]) for m in MODE) + f" | {f_r(x['semua'])} |")
    k = H["sekarang"]
    L += ["", "## Kondisi pasar pada akhir data", "",
          f"{k['tanggal']}: skor **{k['skor']:+d}** ({k['ikon']} {k['nama']}) · BTC {k['rezim']} · koin di atas MA50 {k['lebar50']:.0f}% · "
          f"Stage 2 {k['s2']:.0f}% · Stage 4 {k['s4']:.0f}%", "",
          "## Catatan jujur", "",
          "- **Percobaan 1 gagal.** Rancangan pertama (tiap strategi boleh jalan mulai skor tertentu, dengan syarat statistik ketat) "
          "hampir tidak pernah bertransaksi dan rugi; hasilnya tetap dicantumkan di tabel. Model versi 2 dirancang SETELAH melihat hasil itu, "
          "jadi angka ujinya tidak sebersih uji buta. Pegangannya: batas dipilih walk-forward, hasilnya mirip untuk batas +2, +3 dan +4, "
          "dan polanya sama di data 2020–2022 yang tidak dipakai sebagai tahun uji.",
          "- Skor pasar memakai ambang bulat yang ditetapkan di muka; yang dipilih dari data hanya batas skor per sisi.",
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
