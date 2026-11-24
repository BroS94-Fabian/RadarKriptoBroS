# -*- coding: utf-8 -*-
"""
👀 KOIN PANTAUAN HARIAN — supaya radar tidak diam
================================================
Bila dalam 24 jam terakhir tidak ada sinyal 🟢/🟩/🔻/🔴 yang terkirim, radar mengirim SATU koin per hari:
koin yang paling menonjol sesuai arah pasar (BTC tren naik → kandidat beli; selain itu → kandidat jual dulu).
Aturan pemilihannya diambil dari backtest_pilihan/model.json (uji "Pilihan Harian"), dengan logika yang sama
persis dengan backtest_pilihan.ATURAN.

Hasil uji (24 Nov 2026): memilih koin seperti ini setiap hari TIDAK lebih baik dari menunggu sinyal — pada hari
tanpa sinyal rata-ratanya ±0% per transaksi, dan bila ikut diperdagangkan hasil portofolio turun. Karena itu
bawaannya dikirim sebagai PANTAUAN (tanpa ajakan masuk). Pengaturan `pilihan_harian` di config.yaml:
  pantau  (bawaan) koin dikirim sebagai pantauan + syarat yang membuatnya jadi sinyal sungguhan
  rencana          sama, ditambah rencana masuk/keluar (TP1/TP2/SL) — tetap bukan sinyal yang lolos filter
  false            tidak dikirim
"""
from __future__ import annotations

import json
import os

import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_pilihan", "model.json")
JEDA_HARI = 10

ATURAN = {
    # kode: (sisi, nama, syarat calon, kunci urut, kecil dulu?)  — sama dengan backtest_pilihan.ATURAN
    "L1": ("long", "skor beli radar tertinggi", lambda f: f["kelas"] != "turun", "skor_naik", False),
    "L2": ("long", "skor beli tertinggi di Stage 2", lambda f: f["stage"] == 2, "skor_naik", False),
    "L3": ("long", "paling kuat vs BTC 30 hari (Stage 2)", lambda f: f["stage"] == 2, "rs30", False),
    "S1": ("short", "skor jual radar tertinggi", lambda f: f["kelas"] != "naik", "skor_turun", False),
    "S2": ("short", "skor jual tertinggi di Stage 4", lambda f: f["stage"] == 4, "skor_turun", False),
    "S3": ("short", "paling lemah vs BTC 30 hari (Stage 4)", lambda f: f["stage"] == 4, "rs30", True),
}
BAWAAN = {"long": "L1", "short": "S2"}


def muat_model(path: str = MODEL_PATH) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def r30(close) -> float | None:
    c = np.asarray(close, dtype=float)
    return float((c[-1] / c[-31] - 1) * 100) if len(c) > 30 and c[-31] > 0 else None


def fitur(r: dict, btc_r30: float | None) -> dict:
    """Fitur satu koin dari hasil analisa radar (kelas sebelum filter, skor, stage, kekuatan vs BTC 30 hari)."""
    dc = r["_g"]["dc"] if r.get("_g") else None
    x = r30(dc["close"].to_numpy()) if dc is not None else None
    return dict(kelas=r.get("kelas_asli", r["kelas"]), skor_naik=r.get("skor_naik"), skor_turun=r.get("skor_turun"),
                stage=int(((r.get("siklus") or {}).get("stage")) or 0),
                rs30=(x - btc_r30) if x is not None and btc_r30 is not None else None)


def urutkan(calon: list[tuple[str, dict]], kode: str) -> list[str]:
    """calon = [(symbol, fitur)] → daftar symbol sesuai aturan (terbaik dulu). Seri → urut nama simbol."""
    _, _, syarat, kunci, kecil = ATURAN[kode]
    ok = [(s, f) for s, f in calon if f.get(kunci) is not None and syarat(f)]
    ok.sort(key=lambda sf: sf[0])
    ok.sort(key=lambda sf: sf[1][kunci], reverse=not kecil)
    return [s for s, _ in ok]


def pilih(calon: list[tuple[str, dict]], kode: str, terakhir: dict, hari_ini: str) -> str | None:
    """Koin pertama sesuai aturan yang tidak dipilih dalam 10 hari terakhir. terakhir = {symbol: 'YYYY-MM-DD'}."""
    from datetime import date
    h = date.fromisoformat(hari_ini)
    for s in urutkan(calon, kode):
        t = terakhir.get(s)
        if t and (h - date.fromisoformat(t)).days < JEDA_HARI:
            continue
        return s
    return None


def zona_pantul(dc) -> dict | None:
    """Untuk koin Stage 4: zona Fibonacci 0,382–0,618 dari penurunan terakhir (cara yang sama dengan sinyal 🔻).
    Sinyal 🔻 muncul bila harga memantul ke zona ini lalu candle harian merah."""
    if dc is None or len(dc) < 91:
        return None
    h, l, c = (dc[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    j = len(c) - 1
    a = j - 59
    il = a + int(np.argmin(l[a:j + 1]))
    b = max(0, il - 90)
    ih = b + int(np.argmax(h[b:il + 1]))
    lo, hi = float(l[il]), float(h[ih])
    if not (lo > 0 and hi / lo - 1 >= 0.15 and ih < il):
        return None
    return dict(f382=lo + (hi - lo) * 0.382, f618=lo + (hi - lo) * 0.618, swing_low=lo, swing_high=hi,
                harga=float(c[j]), posisi=("bawah" if c[j] < lo + (hi - lo) * 0.382 else
                                           "zona" if c[j] <= lo + (hi - lo) * 0.618 else "atas"))
