# -*- coding: utf-8 -*-
"""
HARIAN BERJALAN — analisa skala harian yang dihitung ulang TIAP JAM
===================================================================
Radar harian memakai candle harian yang tutup jam 00.00 UTC (07.00 WIB), jadi 🟩 awal Stage 2 dan 🔻 jual dulu
hanya bisa muncul sekali sehari. Di sini candle hariannya "berjalan": dari candle 1 jam dibentuk candle 24 jam yang
berakhir di jam yang baru tutup,

        candle ke-0 = 24 jam terakhir, candle ke-1 = 24 jam sebelumnya, dst. (maks 400 candle)

lalu mesin radar harian dijalankan APA ADANYA pada candle itu (tanpa mengubah satu pun rumus atau ambang).
Tepat jam 00.00 UTC candle berjalan = candle harian biasa, jadi sinyal harian yang sekarang tetap termasuk di dalamnya.

Dipakai SAMA PERSIS oleh backtest (backtest_berjalan.py) dan — bila lolos uji — oleh radar live.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import analisa as A

JENDELA = 400            # jumlah candle 24 jam yang dianalisa (sama dengan radar harian)
MIN_LILIN = 261          # minimal candle supaya dianalisa (sama dengan backtest harian: 260 hari + hari sinyal)
MS_JAM = 3_600_000
H24 = 24 * MS_JAM
JAM_PERLU = JENDELA * 24  # candle 1 jam yang dibutuhkan radar live


def lilin(t, o, h, l, c, v, qv, tb, j: int, n: int = JENDELA) -> pd.DataFrame | None:
    """Candle 24 jam berjalan yang berakhir di penutupan candle 1 jam ke-j (t = waktu buka candle 1 jam, ms, urut naik).
    Candle paling tua boleh tidak penuh (seperti candle harian pertama sebuah koin). None bila datanya belum cukup."""
    t0 = int(t[j]) + MS_JAM
    N = int(min(n, -(-(t0 - int(t[0])) // H24)))
    if N < 2:
        return None
    tepi = t0 - H24 * np.arange(N, -1, -1, dtype=np.int64)
    b = np.searchsorted(t[:j + 1], tepi, side="left")
    ada = b[1:] > b[:-1]                                   # lewati rentang 24 jam yang kosong (bursa mati seharian)
    s = b[:-1][ada]
    if len(s) < 2:
        return None
    a0 = int(s[0])
    idx = s - a0
    seg = slice(a0, j + 1)
    akhir = np.r_[idx[1:], j + 1 - a0] - 1
    return pd.DataFrame(dict(
        time=pd.to_datetime(tepi[:-1][ada], unit="ms", utc=True),
        open=np.asarray(o[seg], dtype=float)[idx], high=np.maximum.reduceat(np.asarray(h[seg], dtype=float), idx),
        low=np.minimum.reduceat(np.asarray(l[seg], dtype=float), idx), close=np.asarray(c[seg], dtype=float)[akhir],
        volume=np.add.reduceat(np.asarray(v[seg], dtype=float), idx), qvol=np.add.reduceat(np.asarray(qv[seg], dtype=float), idx),
        taker_buy_q=np.add.reduceat(np.asarray(tb[seg], dtype=float), idx), closed=True))


def analisa(info: dict, w: pd.DataFrame, cfg: dict):
    """Mesin radar harian pada candle 24 jam berjalan (cara memanggilnya sama dengan backtest harian).
    → (r, sinyal): sinyal = [dict(strategi, sisi, skor, target, batal)]"""
    if w is None or len(w) < MIN_LILIN:
        return None, []
    c = w["close"].to_numpy()
    inf = dict(info, price=float(c[-1]), chg24=float((c[-1] / c[-2] - 1) * 100), qvol24=float(w["qvol"].iat[-1]))
    r = A.analisa_koin(inf, w, None, cfg)
    if not r:
        return None, []
    out = []
    k = r["kelas"]
    if k in ("naik", "turun"):
        out.append(dict(strategi="radar_" + k, sisi="long" if k == "naik" else "short",
                        skor=r["skor_naik"] if k == "naik" else r["skor_turun"],
                        target=r["target"]["harga"] if r.get("target") else None,
                        batal=r["batal"]["harga"] if r.get("batal") else None))
    sik = r.get("siklus") or {}
    if sik.get("baru_stage2"):
        out.append(dict(strategi="awal_stage2", sisi="long", skor=None, target=None, batal=None))
    sf = sik.get("short_fib")
    if sf:
        out.append(dict(strategi="pantul_fib", sisi="short", skor=None, target=sf["target"], batal=sf["batal"]))
    return r, out


def dari_candle(hc: pd.DataFrame):
    """Candle 1 jam format radar (time, open, high, low, close, volume, qvol, taker_buy_q, closed) → candle 24 jam
    berjalan yang berakhir di candle 1 jam terakhir yang sudah tutup. → (w, waktu_tutup) ; (None, None) bila kurang."""
    if hc is None or len(hc) == 0:
        return None, None
    d = hc[hc["closed"]] if "closed" in hc else hc
    if len(d) < 48:
        return None, None
    t = ((d["time"] - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(milliseconds=1)).to_numpy().astype(np.int64)
    kol = [d[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close", "volume", "qvol", "taker_buy_q")]
    w = lilin(t, *kol, j=len(d) - 1)
    return w, pd.Timestamp(int(t[-1]) + MS_JAM, unit="ms", tz="UTC")
