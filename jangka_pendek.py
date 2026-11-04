# -*- coding: utf-8 -*-
"""
MODE JANGKA PENDEK (pasar sideways)
===================================
Ide: saat pasar datar, harga koin cenderung bolak-balik di dalam kisaran.
Beli saat harga di DASAR kisaran dan mulai memantul, jual dalam maksimal 3 jam.

Sinyal beli (candle 1 jam yang sudah tutup):
  - Kisaran 3 hari (72 jam): lebar 3–15%, harga tidak sedang tren kuat
  - Harga di 20–30% bawah kisaran
  - RSI(14) jam sebelumnya oversold, lalu mulai naik
  - Candle terakhir hijau dan masih di atas support (tidak jebol)
  - Volume 24 jam cukup besar (spread kecil)
Rencana jual: TP (persen tetap atau tengah kisaran), SL (persen tetap atau di bawah support),
tutup paksa setelah 3 jam.

Logika yang sama dipakai backtest_jp.py dan radar live, supaya hasil uji = perilaku nyata.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analisa import rsi

DEFAULT_JP = dict(
    aktif=False,          # dinyalakan hanya bila backtest positif
    hanya_sideways=True,  # hanya saat BTC sideways (rezim netral)
    jendela=72,           # jam untuk kisaran harga
    lebar_min=0.03, lebar_max=0.15, drift_max=0.5, posisi_max=0.2, rsi_max=35,
    vol24_min=5_000_000,  # USD
    tp="1.5", sl="1.5",   # persen, atau "tengah" (TP) / "support" (SL)
    tahan_jam=3,
    slippage_persen=0.05,
)


def fitur(h: pd.DataFrame, jendela: int = 72) -> pd.DataFrame:
    """Kolom bantu untuk setiap candle 1 jam (hanya memakai data sampai candle itu)."""
    c, hi, lo = h["close"], h["high"], h["low"]
    F = pd.DataFrame(index=h.index)
    F["close"], F["open"] = c, h["open"]
    F["rng_hi"] = hi.rolling(jendela, min_periods=jendela).max()
    F["rng_lo"] = lo.rolling(jendela, min_periods=jendela).min()
    F["support"] = lo.shift(3).rolling(jendela - 3, min_periods=jendela - 3).min()
    lebar = F["rng_hi"] - F["rng_lo"]
    F["lebar"] = lebar / c
    F["posisi"] = (c - F["rng_lo"]) / lebar.replace(0, np.nan)
    F["drift"] = (c - c.shift(jendela)).abs() / lebar.replace(0, np.nan)
    r = pd.Series(rsi(c.to_numpy()), index=h.index)
    F["rsi"], F["rsi_prev"] = r, r.shift(1)
    F["vol24"] = h["qvol"].rolling(24, min_periods=24).sum()
    return F


def mask_masuk(F: pd.DataFrame, P: dict) -> pd.Series:
    return ((F["lebar"] >= P["lebar_min"]) & (F["lebar"] <= P["lebar_max"])
            & (F["drift"] <= P["drift_max"]) & (F["posisi"] <= P["posisi_max"])
            & (F["rsi_prev"] <= P["rsi_max"]) & (F["rsi"] > F["rsi_prev"])
            & (F["close"] > F["open"]) & (F["close"] >= F["support"] * 0.998)
            & (F["vol24"] >= P["vol24_min"])).fillna(False)


def rencana_jp(harga: float, baris, P: dict) -> dict | None:
    """TP & SL untuk satu sinyal. None bila jarak TP terlalu kecil."""
    tp_cfg, sl_cfg = str(P["tp"]), str(P["sl"])
    if tp_cfg == "tengah":
        tp = float(baris["rng_lo"] + 0.5 * (baris["rng_hi"] - baris["rng_lo"]))
    else:
        tp = harga * (1 + float(tp_cfg) / 100)
    if sl_cfg == "support":
        sl = float(baris["support"]) * 0.997
    else:
        sl = harga * (1 - float(sl_cfg) / 100)
    if tp <= harga * 1.006 or sl >= harga * 0.997:   # target terlalu dekat → tidak layak setelah biaya
        return None
    return dict(entry=harga, tp=tp, sl=sl, tp_pct=(tp / harga - 1) * 100, sl_pct=(sl / harga - 1) * 100,
                tahan_jam=int(P["tahan_jam"]))


def simulasi_jp(plan: dict, highs, lows, closes) -> dict:
    """Candle 1 jam setelah sinyal. SL dicek dulu bila keduanya tersentuh di jam yang sama."""
    e = plan["entry"]
    for k, (h, lo) in enumerate(zip(highs, lows), start=1):
        if lo <= plan["sl"]:
            return dict(hasil="kena SL", pnl=(plan["sl"] / e - 1) * 100, jam=k)
        if h >= plan["tp"]:
            return dict(hasil="kena TP", pnl=(plan["tp"] / e - 1) * 100, jam=k)
    last = closes[-1] if len(closes) else e
    return dict(hasil="waktu habis", pnl=(last / e - 1) * 100, jam=len(closes))


def bersih_jp(pnl: float, P: dict | None = None, B: dict | None = None) -> float:
    """Bersih setelah biaya beli/jual, pajak jual & slippage dua sisi."""
    P = P or DEFAULT_JP
    B = B or dict(fee_beli_persen=0.1, fee_jual_persen=0.1, pajak_jual_persen=0.21)
    s = float(P.get("slippage_persen", 0.05))
    jual = 1 + pnl / 100
    return pnl - B["fee_beli_persen"] - s - (B["fee_jual_persen"] + B["pajak_jual_persen"] + s) * jual
