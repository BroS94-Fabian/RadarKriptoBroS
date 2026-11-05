# -*- coding: utf-8 -*-
"""
MODE JANGKA PENDEK
==================
Dua jenis sinyal di candle 1 jam (yang sudah tutup), dua kelompok lama tahan:
  - "≤3 jam"   : tahan maksimal 3 jam
  - "6–24 jam" : tahan maksimal 6, 12 atau 24 jam (target lebih besar)

Jenis sinyal:
  pantul : harga di DASAR kisaran 3 hari (72 jam), RSI jam sebelumnya oversold lalu
           mulai naik, candle hijau, belum jebol support.
  tembus : harga MENEMBUS atap kisaran 3 hari dengan volume jam itu ≥ X kali rata-rata,
           RSI 55–75 (kuat tapi belum terlalu jenuh), candle hijau.

Rencana jual:
  TP  : persen tetap, atau "pola" (pantul → tengah kisaran; tembus → atap + tinggi kisaran)
  SL  : persen tetap, atau "support" (pantul → bawah support; tembus → kembali masuk kisaran)
  Tutup paksa setelah batas jam.

Logika yang sama dipakai backtest_jp.py dan radar live.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analisa import rsi

DEFAULT_JP = dict(
    aktif=False,          # dinyalakan hanya bila backtest positif
    hanya_sideways=True,  # hanya saat BTC sideways (rezim netral)
    jenis="pantul", jendela=72,
    lebar_min=0.03, lebar_max=0.15, drift_max=0.5, posisi_max=0.2, rsi_max=35,   # pantul
    vol_rel_min=2.0, rsi_min_tembus=55, rsi_max_tembus=75,                         # tembus
    vol24_min=5_000_000,  # USD
    tp="1.5", sl="1.5", tahan_jam=3,
    slippage_persen=0.05,
)


def fitur(h: pd.DataFrame, jendela: int = 72) -> pd.DataFrame:
    """Kolom bantu untuk setiap candle 1 jam (hanya memakai data sampai candle itu)."""
    c, hi, lo = h["close"], h["high"], h["low"]
    F = pd.DataFrame(index=h.index)
    F["close"], F["open"] = c, h["open"]
    F["rng_hi"] = hi.rolling(jendela, min_periods=jendela).max()
    F["rng_lo"] = lo.rolling(jendela, min_periods=jendela).min()
    F["rng_hi_prev"] = hi.shift(1).rolling(jendela, min_periods=jendela).max()
    F["rng_lo_prev"] = lo.shift(1).rolling(jendela, min_periods=jendela).min()
    F["support"] = lo.shift(3).rolling(jendela - 3, min_periods=jendela - 3).min()
    lebar = F["rng_hi"] - F["rng_lo"]
    F["lebar"] = lebar / c
    F["lebar_prev"] = (F["rng_hi_prev"] - F["rng_lo_prev"]) / c
    F["posisi"] = (c - F["rng_lo"]) / lebar.replace(0, np.nan)
    F["drift"] = (c - c.shift(jendela)).abs() / lebar.replace(0, np.nan)
    r = pd.Series(rsi(c.to_numpy()), index=h.index)
    F["rsi"], F["rsi_prev"] = r, r.shift(1)
    q = h["qvol"]
    F["vol24"] = q.rolling(24, min_periods=24).sum()
    F["vol_rel"] = q / q.shift(1).rolling(24, min_periods=24).mean().replace(0, np.nan)
    return F


def mask_masuk(F: pd.DataFrame, P: dict) -> pd.Series:
    hijau = F["close"] > F["open"]
    if P.get("jenis", "pantul") == "tembus":
        m = ((F["close"] > F["rng_hi_prev"]) & hijau & (F["vol_rel"] >= P["vol_rel_min"])
             & (F["rsi"] >= P["rsi_min_tembus"]) & (F["rsi"] <= P["rsi_max_tembus"])
             & (F["lebar_prev"] >= P["lebar_min"]) & (F["lebar_prev"] <= P["lebar_max"])
             & (F["vol24"] >= P["vol24_min"]))
    else:
        m = ((F["lebar"] >= P["lebar_min"]) & (F["lebar"] <= P["lebar_max"])
             & (F["drift"] <= P["drift_max"]) & (F["posisi"] <= P["posisi_max"])
             & (F["rsi_prev"] <= P["rsi_max"]) & (F["rsi"] > F["rsi_prev"])
             & hijau & (F["close"] >= F["support"] * 0.998) & (F["vol24"] >= P["vol24_min"]))
    return m.fillna(False)


def rencana_jp(harga: float, baris, P: dict) -> dict | None:
    """TP & SL untuk satu sinyal. baris = dict berisi rng_lo, rng_hi, rng_hi_prev, rng_lo_prev, support.
    None bila jarak TP terlalu kecil (tidak layak setelah biaya)."""
    tembus = P.get("jenis", "pantul") == "tembus"
    tp_cfg, sl_cfg = str(P["tp"]), str(P["sl"])
    if tp_cfg in ("pola", "tengah"):
        if tembus:
            tp = float(baris["rng_hi_prev"] + (baris["rng_hi_prev"] - baris["rng_lo_prev"]))
        else:
            tp = float(baris["rng_lo"] + 0.5 * (baris["rng_hi"] - baris["rng_lo"]))
    else:
        tp = harga * (1 + float(tp_cfg) / 100)
    if sl_cfg == "support":
        sl = float(baris["rng_hi_prev"]) * 0.99 if tembus else float(baris["support"]) * 0.997
    else:
        sl = harga * (1 - float(sl_cfg) / 100)
    if not (np.isfinite(tp) and np.isfinite(sl)) or tp <= harga * 1.006 or sl >= harga * 0.997:
        return None
    return dict(entry=harga, tp=tp, sl=sl, tp_pct=(tp / harga - 1) * 100, sl_pct=(sl / harga - 1) * 100,
                tahan_jam=int(P["tahan_jam"]))


def simulasi_jp(plan: dict, highs, lows, closes) -> dict:
    """Candle 1 jam setelah sinyal. SL dicek dulu bila keduanya tersentuh di jam yang sama."""
    e, tp, sl = plan["entry"], plan["tp"], plan["sl"]
    for k in range(len(highs)):
        if lows[k] <= sl:
            return dict(hasil="kena SL", pnl=(sl / e - 1) * 100, jam=k + 1)
        if highs[k] >= tp:
            return dict(hasil="kena TP", pnl=(tp / e - 1) * 100, jam=k + 1)
    last = closes[-1] if len(closes) else e
    return dict(hasil="waktu habis", pnl=(last / e - 1) * 100, jam=len(closes))


def bersih_jp(pnl: float, P: dict | None = None, B: dict | None = None) -> float:
    """Bersih setelah biaya beli/jual, pajak jual & slippage dua sisi."""
    P = P or DEFAULT_JP
    B = B or dict(fee_beli_persen=0.1, fee_jual_persen=0.1, pajak_jual_persen=0.21)
    s = float(P.get("slippage_persen", 0.05))
    jual = 1 + pnl / 100
    return pnl - B["fee_beli_persen"] - s - (B["fee_jual_persen"] + B["pajak_jual_persen"] + s) * jual
