# -*- coding: utf-8 -*-
"""
SIKLUS 4 STAGE (Stan Weinstein · "Super Trader Analysis Check List")
====================================================================
  Stage 1  DASAR   (basing / akumulasi) : turun sudah berhenti, harga mendatar di sekitar MA panjang
                                          yang mulai datar. Volume mengering, lalu muncul lonjakan.
  Stage 2  NAIK    (markup)             : harga di atas MA panjang yang menanjak, MA50 > MA200.
                                          Titik beli terbaik = awal Stage 2 (tembus atap dasar + volume)
                                          atau saat pullback ke zona Fibonacci 0,382–0,618.
  Stage 3  PUNCAK  (distribusi)         : kenaikan berhenti, harga bolak-balik, MA mendatar. Ambil untung.
  Stage 4  TURUN   (markdown)           : harga di bawah MA panjang yang menurun. Hindari beli.

MA panjang = MA200 harian (±30 minggu, padanan MA 30 minggu Weinstein; koin <230 hari: MA100).
Stage baru dianggap berganti setelah bertahan 3 hari (supaya tidak berkedip-kedip).

Checklist (urutan "Super Trader Analysis"):
  Price analysis : Cycle → Trend → Support & Resistance → Pattern → Candlestick
  Volume analysis: volume tinggi searah harga = konfirmasi (conforming);
                   volume rendah / tidak searah / lonjakan mendadak = anomali (bell ringing).

Semua angka hanya memakai data sampai candle itu → dipakai sama persis oleh radar & backtest.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analisa import atr, sma

NAMA = {0: "Belum diketahui", 1: "Stage 1 · Dasar", 2: "Stage 2 · Naik", 3: "Stage 3 · Puncak", 4: "Stage 4 · Turun"}
ARTI = {0: "data belum cukup", 1: "akumulasi / pembentukan dasar", 2: "tren naik (markup)",
        3: "distribusi / pembentukan puncak", 4: "tren turun (markdown)"}
IKON = {0: "⚪", 1: "🟦", 2: "🟩", 3: "🟨", 4: "🟥"}

MA_L, MA_S = 200, 50      # MA panjang (±30 minggu) & menengah
SLOPE_L, SLOPE_S = 20, 10  # jarak hari untuk mengukur kemiringan MA
BASIS = 60                 # panjang kisaran dasar / puncak (hari)
TAHUN = 365
KONFIRM = 3                # hari bertahan sebelum stage dianggap berganti


def _geser(x: np.ndarray, k: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if 0 < k < len(x):
        out[k:] = x[:-k]
    return out


def _rmax(x, n, mp=None):
    return pd.Series(x, dtype=float).rolling(n, min_periods=mp or n).max().to_numpy()


def _rmin(x, n, mp=None):
    return pd.Series(x, dtype=float).rolling(n, min_periods=mp or n).min().to_numpy()


def _rmean(x, n, mp=None):
    return pd.Series(x, dtype=float).rolling(n, min_periods=mp or n).mean().to_numpy()


def hitung(o, h, l, c, v) -> dict:
    """Stage untuk SETIAP candle harian (array). Dipakai radar (ambil indeks terakhir) & backtest."""
    o, h, l, c, v = (np.asarray(a, dtype=float) for a in (o, h, l, c, v))
    n = len(c)
    ma_n = MA_L if n >= MA_L + SLOPE_L + 10 else (100 if n >= 100 + SLOPE_L + 10 else 0)
    F = dict(n=n, ma_n=ma_n, stage=np.zeros(n, dtype=int), prev=np.zeros(n, dtype=int), umur=np.zeros(n, dtype=int))
    if not ma_n:
        return F
    with np.errstate(invalid="ignore", divide="ignore"):
        ma_l, ma_s = sma(c, ma_n), sma(c, MA_S)
        slope_l = ma_l / _geser(ma_l, SLOPE_L) - 1
        slope_prev = _geser(ma_l, SLOPE_L) / _geser(ma_l, 4 * SLOPE_L) - 1
        slope_s = ma_s / _geser(ma_s, SLOPE_S) - 1
        atrp = atr(h, l, c) / c
        thr = np.clip(0.35 * atrp, 0.015, 0.04)     # batas "mendatar" untuk MA panjang (per 20 hari)
        thr_s = np.clip(0.5 * atrp, 0.01, 0.05)     # batas "mendatar" untuk MA50 (per 10 hari)
        hi1, lo1 = _rmax(h, TAHUN, 150), _rmin(l, TAHUN, 150)
        pos = (c - lo1) / np.where(hi1 > lo1, hi1 - lo1, np.nan)
        # low/high baru: 20 hari terakhir menembus low/high 70 hari sebelumnya minimal 3%
        low_baru = _rmin(l, 20) < _geser(_rmin(l, 70), 20) * 0.97
        high_baru = _rmax(h, 20) > _geser(_rmax(h, 70), 20) * 1.03
        R = _rmax(_geser(h, 3), BASIS)                         # atap kisaran 60 hari (tanpa 3 hari terakhir)
        S = _rmin(_geser(l, 3), BASIS)                         # lantai kisaran
        vol_rel = v / _rmean(_geser(v, 1), 50)

        above = c > ma_l
        naik_l, turun_l = slope_l > thr, slope_l < -thr
        c2 = above & naik_l & (ma_s > ma_l)
        c4 = ~above & turun_l & (ma_s < ma_l)
        dasar_dari4 = c4 & (c >= ma_s * 0.97) & (slope_s >= -thr_s) & ~low_baru     # turun berhenti → mulai Stage 1
        puncak_dari2 = c2 & (c <= ma_s * 1.03) & (slope_s <= thr_s) & ~high_baru     # naik berhenti → mulai Stage 3
        awal2 = above & high_baru & (slope_s > 0) & (slope_l >= -thr)       # tembus dasar, MA panjang belum menanjak
        awal4 = ~above & low_baru & (slope_s < 0) & (slope_l <= thr)        # jebol puncak, MA panjang belum menurun
        konteks = (0.5 - pos) * 2 - 0.5 * np.sign(np.nan_to_num(slope_prev))  # >0: datang dari bawah (dasar)

    raw = np.where(konteks > 0, 1, 3)
    raw = np.where(awal4, 4, raw)
    raw = np.where(awal2, 2, raw)
    raw = np.where(dasar_dari4, 1, raw)
    raw = np.where(puncak_dari2, 3, raw)
    raw = np.where(c4 & ~dasar_dari4, 4, raw)
    raw = np.where(c2 & ~puncak_dari2, 2, raw)
    valid = np.isfinite(ma_l) & np.isfinite(slope_l) & np.isfinite(ma_s) & np.isfinite(slope_s) & np.isfinite(pos)
    raw = np.where(valid, raw, 0)

    st, prv, umur = F["stage"], F["prev"], F["umur"]
    cur = p = age = 0
    for t in range(n):
        r = raw[t]
        if r == 0:
            cur = p = age = 0
        elif cur == 0:
            cur, age = r, 1
        elif r != cur and t >= KONFIRM - 1 and all(raw[t - k] == r for k in range(KONFIRM)):
            p, cur, age = cur, r, KONFIRM
        else:
            age += 1
        st[t], prv[t], umur[t] = cur, p, age
    F.update(raw=raw, ma_l=ma_l, ma_s=ma_s, slope_l=slope_l, slope_s=slope_s, thr=thr, pos=pos, R=R, S=S,
             vol_rel=vol_rel, hi1=hi1, lo1=lo1)
    return F


def fase(F: dict, j: int, c: float) -> tuple[str, str]:
    """Kode & teks fase di dalam stage (awal/akhir/transisi)."""
    stg, prv, age = int(F["stage"][j]), int(F["prev"][j]), int(F["umur"][j])
    if stg == 0:
        return "0", "data belum cukup"
    ma, R, S = F["ma_l"][j], F["R"][j], F["S"][j]
    ext = c / ma - 1 if np.isfinite(ma) and ma > 0 else 0.0
    if stg == 1:
        if c >= ma * 0.97 or (np.isfinite(R) and c >= R * 0.93):
            return "1-akhir", "akhir dasar: mendekati atap kisaran, siap tembus"
        return "1", "sedang membentuk dasar"
    if stg == 2:
        if prv == 1 and age <= 20:
            return "1→2", "baru tembus dari dasar (awal tren naik)"
        if ext >= 0.8:
            return "2-jenuh", f"sudah {ext * 100:.0f}% di atas MA{F['ma_n']}, rawan koreksi"
        if age <= 40 or ext <= 0.25:
            return "2-awal", "awal tren naik"
        return "2", "tren naik berjalan"
    if stg == 3:
        if np.isfinite(S) and c <= S * 1.03:
            return "3-akhir", "di lantai kisaran puncak, rawan jebol"
        return "3", "kenaikan tertahan, harga bolak-balik (distribusi)"
    if prv == 3 and age <= 20:
        return "3→4", "baru jebol dari puncak (awal tren turun)"
    if age <= 40:
        return "4-awal", "awal tren turun"
    return "4", "tren turun berjalan"


SARAN = {
    "1": "Pantau. Akumulasi bertahap boleh, beli utama saat tembus atap dasar dengan volume besar.",
    "1-akhir": "Siapkan beli: tunggu tembus atap kisaran dengan volume ≥1,5× rata-rata.",
    "1→2": "Titik beli ideal (awal Stage 2). Pasang stop di bawah lantai dasar.",
    "2-awal": "Tren naik sehat. Beli/tambah saat pullback ke zona Fibonacci.",
    "2": "Tahan posisi. Beli baru hanya saat pullback ke zona Fibonacci.",
    "2-jenuh": "Jangan kejar harga. Tunggu pullback, mulai amankan untung.",
    "3": "Ambil untung bertahap. Jangan beli baru.",
    "3-akhir": "Waspada jebol ke Stage 4. Kurangi/keluar posisi.",
    "3→4": "Keluar / hindari. Tren turun baru dimulai.",
    "4-awal": "Hindari beli. Tunggu dasar baru terbentuk.",
    "4": "Hindari beli. Tunggu dasar baru terbentuk.",
    "0": "",
}


def analisa_volume(o, h, l, c, v, j: int) -> dict:
    """Volume tinggi searah harga = konfirmasi; volume tipis / berlawanan / lonjakan mendadak = anomali."""
    if j < 60:
        return dict(status="-", arah=None, teks="data volume belum cukup")
    w = slice(j - 9, j + 1)
    up = c[w] > c[j - 10:j]
    upv, dnv = float(v[w][up].sum()), float(v[w][~up].sum())
    base = float(np.mean(v[j - 59:j - 9]))
    vr10 = float(np.mean(v[w])) / base if base > 0 else 1.0
    base5 = float(np.mean(v[j - 59:j - 4]))
    k = int(np.argmax(v[j - 4:j + 1])) + j - 4
    spike = float(v[k]) / base5 if base5 > 0 else 1.0
    chg10 = c[j] / c[j - 10] - 1
    if spike >= 3 and abs(c[k] / c[k - 1] - 1) <= 0.06:
        hijau = c[k] >= o[k]
        return dict(status="bell", arah="naik" if hijau else "turun", vr10=vr10, spike=spike,
                    teks=f"Lonjakan volume {spike:.1f}× tanpa gerak harga besar → bell ringing "
                         f"({'ada yang menampung' if hijau else 'ada yang melepas'})")
    if chg10 >= 0.03:
        if upv >= 1.2 * dnv and vr10 >= 0.9:
            return dict(status="konfirmasi", arah="naik", vr10=vr10, spike=spike,
                        teks=f"Naik {chg10 * 100:.0f}% dengan volume besar → kenaikan didukung (conforming)")
        if vr10 < 0.75 or dnv > upv:
            return dict(status="anomali", arah="turun", vr10=vr10, spike=spike,
                        teks=f"Naik {chg10 * 100:.0f}% tapi volume tipis/dominan jual → lonceng peringatan")
    elif chg10 <= -0.03:
        if dnv >= 1.2 * upv and vr10 >= 0.9:
            return dict(status="konfirmasi", arah="turun", vr10=vr10, spike=spike,
                        teks=f"Turun {abs(chg10) * 100:.0f}% dengan volume besar → tekanan jual nyata")
        if vr10 < 0.75:
            return dict(status="anomali", arah="naik", vr10=vr10, spike=spike,
                        teks=f"Turun {abs(chg10) * 100:.0f}% dengan volume tipis → tekanan jual melemah")
    elif vr10 < 0.7:
        return dict(status="sepi", arah=None, vr10=vr10, spike=spike,
                    teks="Harga datar & volume mengering → fase tenang, tunggu pemicu")
    return dict(status="normal", arah=None, vr10=vr10, spike=spike, teks="Volume normal, belum ada sinyal khusus")


def fibonacci(h, l, j: int, price: float) -> dict | None:
    """Retracement dari swing low ke swing high terakhir (zona beli pullback 0,382–0,618)."""
    if j < 90:
        return None
    a = j - 59
    ih = a + int(np.argmax(h[a:j + 1]))
    b = max(0, ih - 90)
    il = b + int(np.argmin(l[b:ih + 1]))
    hi, lo = float(h[ih]), float(l[il])
    if lo <= 0 or hi / lo - 1 < 0.15 or il >= ih:
        return None
    lv = {k: hi - (hi - lo) * k for k in (0.382, 0.5, 0.618)}
    if price > lv[0.382]:
        posisi, teks = "atas", "di atas zona (tunggu pullback)"
    elif price >= lv[0.618]:
        posisi, teks = "zona", "di dalam zona pullback"
    else:
        posisi, teks = "bawah", "di bawah 0,618 (koreksi dalam)"
    return dict(swing_high=hi, swing_low=lo, f382=lv[0.382], f500=lv[0.5], f618=lv[0.618], posisi=posisi, teks=teks)


def short_fib(o, h, l, c, F: dict, j: int, wajib_merah: bool = True) -> dict | None:
    """Sinyal SHORT (lolos backtest): koin di Stage 4, harga memantul naik ke zona Fibonacci 0,382–0,618
    dari penurunan terakhir, lalu candle merah. Target = low terakhir, batal = level 0,786."""
    st = F["stage"]
    if j < 90 or st[j] != 4 or "ma_l" not in F:
        return None
    ma = F["ma_l"][j]
    if not (np.isfinite(ma) and c[j] / ma - 1 > -0.45 and (c[j] < o[j] or not wajib_merah)):
        return None
    a = j - 59
    il = a + int(np.argmin(l[a:j + 1]))
    b = max(0, il - 90)
    ih = b + int(np.argmax(h[b:il + 1]))
    lo, hi = float(l[il]), float(h[ih])
    if not (lo > 0 and hi / lo - 1 >= 0.15 and ih < il < j):
        return None
    f382, f618 = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
    if not (f382 <= c[j] <= f618 and (h[j] >= f382 or not wajib_merah)):
        return None
    return dict(swing_high=hi, swing_low=lo, f382=f382, f500=lo + (hi - lo) * 0.5, f618=f618,
                f786=lo + (hi - lo) * 0.786, target=lo, batal=lo + (hi - lo) * 0.786)


def analisa(o, h, l, c, v, price: float) -> dict:
    """Ringkasan siklus untuk candle terakhir (dipakai analisa_koin)."""
    o, h, l, c, v = (np.asarray(a, dtype=float) for a in (o, h, l, c, v))
    F = hitung(o, h, l, c, v)
    j = len(c) - 1
    stg = int(F["stage"][j])
    kode, teks = fase(F, j, float(c[j]))
    out = dict(stage=stg, nama=NAMA[stg], arti=ARTI[stg], ikon=IKON[stg], fase=kode, teks=teks,
               saran=SARAN.get(kode, ""), umur=int(F["umur"][j]), sebelum=int(F["prev"][j]), ma_n=F["ma_n"],
               baru_stage2=bool(stg == 2 and j >= 1 and F["stage"][j - 1] != 2))
    if stg:
        sl = F["slope_l"][j]
        thr = F["thr"][j]
        out.update(ma=float(F["ma_l"][j]), ma_slope=float(sl * 100), jarak_ma=float((price / F["ma_l"][j] - 1) * 100),
                   ma_arah="menanjak" if sl > thr else ("menurun" if sl < -thr else "mendatar"),
                   pos_1th=float(F["pos"][j]), atap=float(F["R"][j]) if np.isfinite(F["R"][j]) else None,
                   lantai=float(F["S"][j]) if np.isfinite(F["S"][j]) else None)
    out["volume"] = analisa_volume(o, h, l, c, v, j)
    out["fib"] = fibonacci(h, l, j, price) if stg == 2 else None
    out["short_fib"] = short_fib(o, h, l, c, F, j)
    # kandidat: sudah di zona Fibonacci, tinggal menunggu candle harian merah
    out["short_kandidat"] = None if out["short_fib"] else short_fib(o, h, l, c, F, j, wajib_merah=False)
    out["_F"] = F
    return out


def cocok_arah(sik: dict, arah: str) -> int:
    """+1 siklus mendukung arah, 0 netral, −1 berlawanan."""
    f = sik.get("fase", "0")
    if arah == "naik":
        if f in ("1-akhir", "1→2", "2-awal", "2"):
            return 1
        if f in ("1", "2-jenuh", "0"):
            return 0
        return -1
    if f in ("3-akhir", "3→4", "4-awal", "4"):
        return 1
    if f in ("3", "0"):
        return 0
    return -1


def checklist(sik: dict, arah: str, tren: str, rr, pola_searah, pola_lawan, candle_arah) -> dict:
    """Super Trader Analysis Check List: Cycle → Trend → S&R → Pattern → Candlestick → Volume."""
    def st(x):
        return "✅" if x > 0 else ("❌" if x < 0 else "⚠️")
    t = tren.lower()
    tr = 1 if t.startswith(arah) else (-1 if t.startswith("naik" if arah == "turun" else "turun") else 0)
    sr = 0 if rr is None else (1 if rr >= 1.5 else (0 if rr >= 1 else -1))
    po = 1 if pola_searah else (-1 if pola_lawan else 0)
    ca = 0 if not candle_arah else (1 if candle_arah == arah else -1)
    va = sik["volume"].get("arah")
    vo = 0 if not va else (1 if va == arah else -1)
    butir = [("Siklus", cocok_arah(sik, arah)), ("Tren", tr), ("S&R", sr), ("Pola", po), ("Candle", ca), ("Volume", vo)]
    return dict(arah=arah, cocok=sum(1 for _, x in butir if x > 0), lawan=sum(1 for _, x in butir if x < 0),
                butir=[dict(nama=nm, nilai=x, ikon=st(x)) for nm, x in butir],
                teks=" ".join(f"{nm}{st(x)}" for nm, x in butir))
