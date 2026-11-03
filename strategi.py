# -*- coding: utf-8 -*-
"""
STRATEGI: filter sinyal, rencana jual (TP1/TP2/SL), simulasi keluar posisi & biaya.
Dipakai bersama oleh radar (live) dan backtest, supaya aturannya persis sama.

Rencana jual (contoh mode persen, TP1 3%, SL 3%, porsi 50%):
  - Beli di harga sinyal.
  - SL awal  = yang lebih dekat antara batas batal pola dan −3%.
  - TP1 +3%  : jual 50%, lalu SL dipindah ke harga beli (impas).
  - TP2      : target pola (kalau tidak ada: 2× jarak TP1) → jual sisanya.
  - Tidak kena apa pun dalam maks_hari → jual di harga penutupan terakhir.
Sinyal turun = posisi short (cerminannya).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Meme coin populer (cadangan bila label "memes" CoinMarketCap tidak tersedia)
MEME = {"DOGE", "SHIB", "PEPE", "BONK", "WIF", "FLOKI", "PENGU", "TRUMP", "BRETT", "POPCAT", "MOG", "NEIRO",
        "TURBO", "MEW", "SPX", "FARTCOIN", "BOME", "PNUT", "GOAT", "MOODENG", "ACT", "DOGS", "CAT", "BABYDOGE",
        "1000SATS", "SATS", "ORDI", "MEME", "PEOPLE", "WEN", "MYRO", "COQ", "LADYS", "AIDOGE", "BABY", "CHEEMS",
        "1000CHEEMS", "1000CAT", "BAN", "CHILLGUY", "MELANIA", "TOSHI", "MOCHI", "SUNDOG", "BRISE", "ELON",
        "KISHU", "LEASH", "BONE", "SAMO", "DEGEN", "HIPPO", "PUMP", "USELESS", "VINE", "GIGA", "AI16Z", "ZEREBRO",
        "BOOK", "HMSTR", "NOT", "MANEKI", "SLERF", "PONKE", "MICHI", "SIGMA", "RETARDIO", "LOFI", "BUTTHOLE"}

DEFAULT_RENCANA = dict(mode="persen", tp1_persen=3.0, sl_persen=3.0, tp1_atr=1.5, sl_atr=1.5, porsi_tp1=0.5,
                       maks_hari=30)
DEFAULT_BIAYA = dict(fee_beli_persen=0.1, fee_jual_persen=0.1, pajak_jual_persen=0.21)


def is_meme(symbol: str, tags=()) -> bool:
    return symbol.upper() in MEME or any("meme" in str(t).lower() for t in (tags or ()))


def rezim_pasar(close, price=None, ma_n: int = 50, slope_n: int = 5) -> dict:
    """Kondisi pasar dari BTC: naik = harga di atas MA50 dan MA50 menanjak; turun = kebalikannya."""
    c = np.asarray(close, dtype=float)
    if len(c) < ma_n + slope_n:
        return dict(rezim="netral", harga=None, ma=None, teks="data BTC belum cukup")
    ma = pd.Series(c).rolling(ma_n).mean().to_numpy()
    p = float(price if price is not None else c[-1])
    now, prev = float(ma[-1]), float(ma[-1 - slope_n])
    if p > now and now > prev:
        rz, teks = "naik", f"BTC di atas MA{ma_n} & MA{ma_n} menanjak"
    elif p < now and now < prev:
        rz, teks = "turun", f"BTC di bawah MA{ma_n} & MA{ma_n} menurun"
    else:
        rz, teks = "netral", f"BTC sideways di sekitar MA{ma_n}"
    return dict(rezim=rz, harga=p, ma=now, teks=teks)


def rezim_series(close, ma_n: int = 50, slope_n: int = 5) -> np.ndarray:
    """Rezim untuk setiap hari (dipakai backtest)."""
    c = np.asarray(close, dtype=float)
    ma = pd.Series(c).rolling(ma_n).mean().to_numpy()
    prev = np.roll(ma, slope_n)
    prev[:slope_n] = np.nan
    out = np.full(len(c), "netral", dtype=object)
    ok = np.isfinite(ma) & np.isfinite(prev)
    out[ok & (c > ma) & (ma > prev)] = "naik"
    out[ok & (c < ma) & (ma < prev)] = "turun"
    return out


def cfg_rencana(cfg: dict) -> dict:
    return dict(DEFAULT_RENCANA, **(cfg.get("rencana") or {}))


def cfg_biaya(cfg: dict) -> dict:
    return dict(DEFAULT_BIAYA, **(cfg.get("biaya") or {}))


def rencana(price: float, arah: str, target=None, batal=None, atr_pct=None, R: dict | None = None) -> dict:
    """Rencana jual untuk satu sinyal. atr_pct dalam persen (mis. 4.2)."""
    R = dict(DEFAULT_RENCANA, **(R or {}))
    s = 1 if arah == "naik" else -1
    if R["mode"] == "atr" and atr_pct:
        tp1_d, sl_d = R["tp1_atr"] * atr_pct / 100, R["sl_atr"] * atr_pct / 100
    else:
        tp1_d, sl_d = R["tp1_persen"] / 100, R["sl_persen"] / 100
    tp1 = price * (1 + s * tp1_d)
    sl = price * (1 - s * sl_d)
    if batal is not None and np.isfinite(batal):
        sl = max(sl, batal) if s > 0 else min(sl, batal)          # pakai yang lebih dekat
        if (s > 0 and sl >= price) or (s < 0 and sl <= price):
            sl = price * (1 - s * sl_d)
    tp2 = price * (1 + s * 2 * tp1_d)
    if target is not None and np.isfinite(target) and s * (target - tp1) > 0:
        tp2 = float(target)
    pct = lambda x: (x / price - 1) * 100  # noqa: E731
    rr = abs(pct(tp2)) / abs(pct(sl)) if pct(sl) else None
    return dict(arah=arah, entry=float(price), tp1=float(tp1), tp1_pct=pct(tp1), tp2=float(tp2), tp2_pct=pct(tp2),
                sl=float(sl), sl_pct=pct(sl), porsi_tp1=float(R["porsi_tp1"]), maks_hari=int(R["maks_hari"]), rr=rr)


def simulasi(plan: dict, highs, lows, closes, selesai: bool = True) -> dict:
    """Jalankan rencana pada urutan candle setelah sinyal.
    Bila SL dan TP tersentuh di candle yang sama, dianggap SL dulu (konservatif).
    selesai=False → posisi yang belum kena apa pun dianggap masih berjalan (untuk live)."""
    e, s = plan["entry"], (1 if plan["arah"] == "naik" else -1)
    tp1, tp2, sl, porsi = plan["tp1"], plan["tp2"], plan["sl"], plan["porsi_tp1"]
    sisa, hasil_pct, tp1_kena = 1.0, 0.0, False
    ret = lambda x: s * (x / e - 1) * 100  # noqa: E731
    n = 0
    for n, (h, lo) in enumerate(zip(highs, lows), start=1):
        fav, adv = (h, lo) if s > 0 else (lo, h)
        if s * (adv - sl) <= 0:
            hasil_pct += sisa * ret(sl)
            return dict(hasil="impas setelah TP1" if tp1_kena else "kena SL", pnl=hasil_pct, hari=n, tp1=tp1_kena)
        if not tp1_kena and porsi > 0 and s * (fav - tp1) >= 0:
            hasil_pct += porsi * ret(tp1)
            sisa -= porsi
            tp1_kena = True
            sl = e  # stop loss pindah ke harga beli
            if sisa <= 1e-9:
                return dict(hasil="kena TP1", pnl=hasil_pct, hari=n, tp1=True)
        if s * (fav - tp2) >= 0:
            hasil_pct += sisa * ret(tp2)
            return dict(hasil="kena TP2", pnl=hasil_pct, hari=n, tp1=tp1_kena)
    last = closes[-1] if len(closes) else e
    hasil_pct += sisa * ret(last)
    return dict(hasil=("batas waktu" if selesai else "berjalan"), pnl=hasil_pct, hari=n, tp1=tp1_kena)


def bersih(pnl_pct: float, B: dict | None = None) -> float:
    """Persentase bersih setelah biaya beli, biaya jual & pajak jual (dari nilai jual)."""
    B = dict(DEFAULT_BIAYA, **(B or {}))
    jual = 1 + pnl_pct / 100
    return pnl_pct - B["fee_beli_persen"] - (B["fee_jual_persen"] + B["pajak_jual_persen"]) * jual


def filter_sinyal(r: dict, cfg: dict, rezim: str) -> tuple[str, str | None]:
    """Terapkan filter tambahan. Sinyal yang tertahan diturunkan jadi 'pantau'."""
    k = r["kelas"]
    if k not in ("naik", "turun"):
        return k, None
    turun_ke = "pantau-" + k
    fp = cfg.get("filter_pasar", True)
    if fp:
        ketat = str(fp).lower() == "ketat"   # ketat = sinyal naik hanya saat BTC tren naik
        if k == "naik" and (rezim == "turun" or (ketat and rezim != "naik")):
            return turun_ke, "ditahan: pasar BTC sedang " + ("tren turun" if rezim == "turun" else "sideways")
        if k == "turun" and (rezim == "naik" or (ketat and rezim != "turun")):
            return turun_ke, "ditahan: pasar BTC sedang " + ("tren naik" if rezim == "naik" else "sideways")
    fm = str(cfg.get("filter_meme", "ketat")).lower()
    if k == "naik" and r.get("meme"):
        if fm == "abaikan":
            return turun_ke, "ditahan: meme coin"
        if fm == "ketat" and r["skor_naik"] < cfg.get("skor_min", 50) + 10:
            return turun_ke, f"ditahan: meme coin butuh skor ≥ {cfg.get('skor_min', 50) + 10}"
    if cfg.get("wajib_breakout", False):
        P = r.get("pola_naik" if k == "naik" else "pola_turun")
        if not P or P.get("status") != "breakout":
            return turun_ke, "ditahan: pola belum breakout"
    min_rr = float(cfg.get("min_rr", 0) or 0)
    rc = r.get("rencana")
    if min_rr and rc and (rc.get("rr") or 0) < min_rr:
        return turun_ke, f"ditahan: rasio potensi/risiko < {min_rr:g}"
    return k, None
