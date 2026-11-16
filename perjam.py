# -*- coding: utf-8 -*-
"""
SINYAL PER JAM — mesin analisa yang sama, dibaca pada candle 1 jam
==================================================================
Gerak harga 1 jam ≈ 1/√24 (±1/5) gerak harian. Supaya semua rumus & ambang persen radar harian (pola, stage,
Fibonacci, akumulasi, skor) tetap bermakna, candle 1 jam "diperbesar" dulu:

        harga' = P0 × (harga / P0) ^ √24        (P0 = harga penutupan candle terakhir)

Hasilnya, satu candle 1 jam terlihat oleh mesin seperti satu candle harian. Level yang keluar (target, batal)
dikembalikan ke harga asli dengan rumus kebalikannya. Volume tidak diubah.

Dipakai SAMA PERSIS oleh backtest (backtest_perjam.py) dan — bila lolos uji — oleh radar live:
selalu 400 candle 1 jam terakhir yang sudah tutup.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import analisa as A

K = 24 ** 0.5        # faktor skala 1 jam → harian
JENDELA = 400        # jumlah candle 1 jam yang dianalisa (sama dengan jendela radar harian)
JEDA_JAM = 24        # koin & jenis sinyal yang sama paling banyak sekali per 24 jam
MS_JAM = 3_600_000

# Rencana jual yang diuji (persen dari harga masuk, maks_hari = jumlah candle 1 jam)
RENCANA = {
    "A": ("TP1 +1% · SL −2,5% · maks 30 jam (skala penuh dari rencana harian)", dict(mode="persen", tp1_persen=1.0, sl_persen=2.5, porsi_tp1=0.5, maks_hari=30)),
    "B": ("TP1 +2% · SL −5% · maks 3 hari", dict(mode="persen", tp1_persen=2.0, sl_persen=5.0, porsi_tp1=0.5, maks_hari=72)),
    "C": ("TP1 +3% · SL −7,5% · maks 7 hari", dict(mode="persen", tp1_persen=3.0, sl_persen=7.5, porsi_tp1=0.5, maks_hari=168)),
    "D": ("TP1 +5% · SL −12% · maks 30 hari (rencana harian, masuknya saja per jam)", dict(mode="persen", tp1_persen=5.0, sl_persen=12.0, porsi_tp1=0.5, maks_hari=720)),
}
TAHAN = max(r[1]["maks_hari"] for r in RENCANA.values())


def ubah(x, p0: float, k: float = K) -> np.ndarray:
    return p0 * (np.asarray(x, dtype=float) / p0) ** k


def balik(x, p0: float, k: float = K) -> float | None:
    if x is None:
        return None
    x = float(x)
    return float(p0 * (x / p0) ** (1 / k)) if np.isfinite(x) and x > 0 else None


def jendela(t_ms, o, h, l, c, v, qv, tb, j: int, n: int = JENDELA) -> pd.DataFrame:
    """Candle 1 jam [j-n+1 … j] yang sudah diperbesar, dalam format candle radar."""
    a = max(0, j - n + 1)
    s = slice(a, j + 1)
    p0 = float(c[j])
    return pd.DataFrame(dict(time=pd.to_datetime(np.asarray(t_ms[s], dtype=np.int64), unit="ms", utc=True),
                             open=ubah(o[s], p0), high=ubah(h[s], p0), low=ubah(l[s], p0), close=ubah(c[s], p0),
                             volume=np.asarray(v[s], dtype=float), qvol=np.asarray(qv[s], dtype=float),
                             taker_buy_q=np.asarray(tb[s], dtype=float), closed=True))


def analisa(info: dict, w: pd.DataFrame, cfg: dict):
    """Jalankan mesin radar pada jendela candle 1 jam yang sudah diperbesar.
    → (r, sinyal): r = hasil analisa_koin (dalam harga yang diperbesar; price = harga asli karena P0 = close terakhir),
    sinyal = [dict(strategi, sisi, skor, target, batal)] dengan target/batal dalam HARGA ASLI."""
    p0 = float(w["close"].iat[-1])
    inf = dict(info, price=p0, chg24=float((p0 / w["close"].iat[-2] - 1) * 100) if len(w) > 1 else 0.0,
               qvol24=float(w["qvol"].iat[-1]))
    r = A.analisa_koin(inf, w, None, cfg)
    if not r:
        return None, []
    out = []
    k = r["kelas"]
    if k in ("naik", "turun"):
        out.append(dict(strategi="radar_" + k, sisi="long" if k == "naik" else "short",
                        skor=r["skor_naik"] if k == "naik" else r["skor_turun"],
                        target=balik(r["target"]["harga"], p0) if r.get("target") else None,
                        batal=balik(r["batal"]["harga"], p0) if r.get("batal") else None))
    sik = r.get("siklus") or {}
    if sik.get("baru_stage2"):
        out.append(dict(strategi="awal_stage2", sisi="long", skor=None, target=None, batal=None))
    sf = sik.get("short_fib")
    if sf:
        out.append(dict(strategi="pantul_fib", sisi="short", skor=None, target=balik(sf["target"], p0), batal=balik(sf["batal"], p0)))
    return r, out


def analisa_candle(info: dict, hc: pd.DataFrame, cfg: dict):
    """Untuk radar live: hc = candle 1 jam format radar (time, open, high, low, close, volume, qvol, taker_buy_q, closed).
    Memakai JENDELA candle terakhir yang sudah tutup. → (r, sinyal, waktu_tutup_candle)"""
    d = hc[hc["closed"]].tail(JENDELA) if "closed" in hc else hc.tail(JENDELA)
    if len(d) < JENDELA:
        return None, [], None
    t = ((d["time"] - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(milliseconds=1)).to_numpy()
    kol = [d[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close", "volume", "qvol", "taker_buy_q")]
    w = jendela(t, *kol, j=len(d) - 1)
    r, s = analisa(info, w, cfg)
    return r, s, pd.Timestamp(int(t[-1]) + MS_JAM, unit="ms", tz="UTC")
