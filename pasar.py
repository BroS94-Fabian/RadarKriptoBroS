# -*- coding: utf-8 -*-
"""
KONDISI PASAR — "termometer" pasar kripto harian
=================================================
Skor pasar −6 … +6 = jumlah 6 suara (+1 mendukung naik / 0 netral / −1 mendukung turun):

  1. btc_ma50    BTC di atas MA50 yang menanjak (+1) / di bawah MA50 yang menurun (−1)
  2. btc_ma200   BTC di atas MA200 (+1) / di bawah (−1)
  3. lebar50     ≥60% koin di atas MA50-nya (+1) / ≤40% (−1)
  4. lebar_stage (% koin Stage 2) − (% koin Stage 4) ≥ +10 (+1) / ≤ −10 (−1)
  5. momentum    % koin di atas MA50 naik ≥15 poin dalam 10 hari (+1) / turun ≥15 poin (−1)
  6. alt_rs      median kenaikan 30 hari altcoin − BTC ≥ +5 poin (+1) / ≤ −5 poin (−1)

Ambang di atas angka bulat yang ditetapkan di muka (tidak dicocok-cocokkan dengan data).
Skor tinggi BUKAN berarti "waktunya beli": di data 2020–2026 sinyal beli terbaik muncul saat BTC baru
tren naik tetapi pasar luas belum ikut naik (skor rendah–sedang), dan hampir tidak untung saat semua
sudah hijau (skor +5/+6 = pasar kepanasan).

Model pasar (model_pasar/model.json, hasil backtest_pasar.py) = aturan lama + batas skor:
  BELI      : BTC tren naik        DAN skor pasar ≤ batas beli   (batas dipilih walk-forward dari data)
  JUAL DULU : BTC tidak tren naik  DAN skor pasar ≤ batas jual

Semua fungsi hanya memakai candle harian yang sudah tutup → sama persis untuk radar & backtest.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

import strategi as ST
from analisa import sma

AMBANG = dict(lebar_atas=60.0, lebar_bawah=40.0, stage_selisih=10.0, momentum=15.0, alt_rs=5.0)
KOMPONEN = [("btc_ma50", "BTC vs MA50"), ("btc_ma200", "BTC vs MA200"), ("lebar50", "Koin di atas MA50"),
            ("lebar_stage", "Stage 2 vs Stage 4"), ("momentum", "Arah jumlah koin kuat"), ("alt_rs", "Altcoin vs BTC")]
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_pasar", "model.json")
MIN_KOIN = 20   # minimal koin dengan data cukup supaya angka "lebar pasar" berarti


def mode(skor: int) -> dict:
    """Kondisi pasar luas (bukan perintah beli/jual — itu ditentukan model, lihat status())."""
    if skor >= 4:
        return dict(kode="bull", nama="SANGAT KUAT", ikon="🟢🟢")
    if skor >= 2:
        return dict(kode="naik", nama="KUAT", ikon="🟢")
    if skor >= -1:
        return dict(kode="netral", nama="CAMPURAN", ikon="🟡")
    if skor >= -3:
        return dict(kode="turun", nama="LEMAH", ikon="🔴")
    return dict(kode="bear", nama="SANGAT LEMAH", ikon="🔴🔴")


def angka(x: int) -> str:
    """+3 / −5 (dengan tanda minus tipografi)."""
    return f"{int(x):+d}".replace("-", "−")


# --------------------------------------------------------------------------- #
# Fitur per koin (array harian)
# --------------------------------------------------------------------------- #
def fitur_koin(close) -> dict:
    """atas50 / atas200: 1 bila close di atas MA, 0 bila di bawah, NaN bila MA belum ada. r30 dalam persen."""
    c = np.asarray(close, dtype=float)
    ma50, ma200 = sma(c, 50), sma(c, 200)
    with np.errstate(invalid="ignore", divide="ignore"):
        a50 = np.where(np.isfinite(ma50), (c > ma50).astype(float), np.nan)
        a200 = np.where(np.isfinite(ma200), (c > ma200).astype(float), np.nan)
        r30 = np.full(len(c), np.nan)
        if len(c) > 30:
            r30[30:] = (c[30:] / c[:-30] - 1) * 100
    return dict(atas50=a50, atas200=a200, r30=r30)


# --------------------------------------------------------------------------- #
# Skor pasar
# --------------------------------------------------------------------------- #
def suara(f: pd.DataFrame) -> pd.DataFrame:
    """f: kolom rezim, btc_close, btc_ma200, lebar50, s2, s4, d_lebar50, alt_rs
    →  suara per komponen (kolom v_<kode>) + skor."""
    A = AMBANG
    v = pd.DataFrame(index=f.index)
    v["v_btc_ma50"] = np.where(f["rezim"] == "naik", 1, np.where(f["rezim"] == "turun", -1, 0))
    v["v_btc_ma200"] = np.where(f["btc_ma200"].isna(), 0, np.where(f["btc_close"] > f["btc_ma200"], 1, -1))
    v["v_lebar50"] = np.where(f["lebar50"] >= A["lebar_atas"], 1, np.where(f["lebar50"] <= A["lebar_bawah"], -1, 0))
    ss = f["s2"] - f["s4"]
    v["v_lebar_stage"] = np.where(ss >= A["stage_selisih"], 1, np.where(ss <= -A["stage_selisih"], -1, 0))
    v["v_momentum"] = np.where(f["d_lebar50"] >= A["momentum"], 1, np.where(f["d_lebar50"] <= -A["momentum"], -1, 0))
    v["v_alt_rs"] = np.where(f["alt_rs"] >= A["alt_rs"], 1, np.where(f["alt_rs"] <= -A["alt_rs"], -1, 0))
    v = v.astype(int)
    v["skor"] = v[[f"v_{k}" for k, _ in KOMPONEN]].sum(axis=1)
    return v


def harian(btc_close, atas50: pd.DataFrame, r30: pd.DataFrame, stage: pd.DataFrame, btc_kol: str = "BTC") -> pd.DataFrame:
    """Tabel fitur pasar harian untuk backtest.
    btc_close: Series (indeks tanggal). atas50 / r30 / stage: DataFrame tanggal × koin."""
    idx = btc_close.index
    c = btc_close.to_numpy(dtype=float)
    f = pd.DataFrame(index=idx)
    f["btc_close"] = c
    f["rezim"] = ST.rezim_series(c)
    f["btc_ma200"] = sma(c, 200)
    a = atas50.reindex(idx)
    n = a.notna().sum(axis=1)
    f["n_koin"] = n
    f["lebar50"] = (a.sum(axis=1) / n.replace(0, np.nan) * 100).where(n >= MIN_KOIN)
    f["d_lebar50"] = f["lebar50"] - f["lebar50"].shift(10)
    st = stage.reindex(idx)
    ns = (st > 0).sum(axis=1)
    f["s2"] = ((st == 2).sum(axis=1) / ns.replace(0, np.nan) * 100).where(ns >= MIN_KOIN)
    f["s4"] = ((st == 4).sum(axis=1) / ns.replace(0, np.nan) * 100).where(ns >= MIN_KOIN)
    r = r30.reindex(idx)
    alt = r.drop(columns=[btc_kol], errors="ignore")
    f["btc_r30"] = r[btc_kol] if btc_kol in r else np.nan
    f["alt_r30"] = alt.median(axis=1).where(alt.notna().sum(axis=1) >= MIN_KOIN)
    f["alt_rs"] = f["alt_r30"] - f["btc_r30"]
    return pd.concat([f, suara(f)], axis=1)


def sekarang(btc_close, koin: list[dict]) -> dict:
    """Kondisi pasar saat ini untuk radar.
    btc_close: array close harian BTC (candle tutup). koin: list dict(base, close=array harian tutup, stage=int)."""
    c = np.asarray(btc_close, dtype=float)
    a_now, a_10, r30s, st = [], [], [], []
    btc_r30 = float((c[-1] / c[-31] - 1) * 100) if len(c) > 31 else np.nan
    for k in koin:
        fk = fitur_koin(k["close"])
        if len(fk["atas50"]) and np.isfinite(fk["atas50"][-1]):
            a_now.append(fk["atas50"][-1])
        if len(fk["atas50"]) > 10 and np.isfinite(fk["atas50"][-11]):
            a_10.append(fk["atas50"][-11])
        if k.get("base") != "BTC" and len(fk["r30"]) and np.isfinite(fk["r30"][-1]):
            r30s.append(fk["r30"][-1])
        if k.get("stage"):
            st.append(int(k["stage"]))
    lebar = float(np.mean(a_now) * 100) if len(a_now) >= MIN_KOIN else np.nan
    lebar10 = float(np.mean(a_10) * 100) if len(a_10) >= MIN_KOIN else np.nan
    s2 = float(np.mean(np.array(st) == 2) * 100) if len(st) >= MIN_KOIN else np.nan
    s4 = float(np.mean(np.array(st) == 4) * 100) if len(st) >= MIN_KOIN else np.nan
    alt_r30 = float(np.median(r30s)) if len(r30s) >= MIN_KOIN else np.nan
    ma200 = sma(c, 200)
    f = pd.DataFrame([dict(rezim=ST.rezim_series(c)[-1] if len(c) else "netral", btc_close=c[-1] if len(c) else np.nan,
                           btc_ma200=ma200[-1] if len(c) else np.nan, lebar50=lebar, d_lebar50=lebar - lebar10,
                           s2=s2, s4=s4, alt_rs=alt_r30 - btc_r30)])
    v = suara(f).iloc[0]
    skor = int(v["skor"])
    nilai = dict(lebar50=lebar, d_lebar50=lebar - lebar10, s2=s2, s4=s4, alt_r30=alt_r30, btc_r30=btc_r30,
                 alt_rs=alt_r30 - btc_r30, n_koin=len(a_now))
    ket = {
        "btc_ma50": {1: "di atas MA50 yang menanjak", 0: "sideways di sekitar MA50", -1: "di bawah MA50 yang menurun"},
        "btc_ma200": {1: "di atas MA200", 0: "data belum cukup", -1: "di bawah MA200"},
        "lebar50": {x: (f"{lebar:.0f}% koin" if np.isfinite(lebar) else "data kurang") for x in (1, 0, -1)},
        "lebar_stage": {x: (f"Stage 2 {s2:.0f}% · Stage 4 {s4:.0f}%" if np.isfinite(s2) else "data kurang") for x in (1, 0, -1)},
        "momentum": {x: (f"{lebar - lebar10:+.0f} poin / 10 hari" if np.isfinite(lebar - lebar10) else "data kurang")
                     for x in (1, 0, -1)},
        "alt_rs": {x: (f"altcoin {alt_r30:+.0f}% vs BTC {btc_r30:+.0f}% (30 hari)" if np.isfinite(alt_r30 - btc_r30)
                       else "data kurang") for x in (1, 0, -1)},
    }
    ket = {k: {x: t.replace("-", "−") for x, t in d.items()} for k, d in ket.items()}
    komp = [dict(kode=k, nama=nm, suara=int(v[f"v_{k}"]), teks=ket[k][int(v[f"v_{k}"])]) for k, nm in KOMPONEN]
    out = dict(skor=skor, komponen=komp, **mode(skor))
    out["nilai"] = {k: (None if not np.isfinite(x) else round(float(x), 1)) for k, x in nilai.items()}
    return out


# --------------------------------------------------------------------------- #
# Model (hasil backtest_pasar.py)
# --------------------------------------------------------------------------- #
def muat_model(path: str = MODEL_PATH) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            m = json.load(f)
        return m if m.get("strategi") else None
    except Exception:
        return None


def rezim_tutup(kp: dict) -> str:
    """Arah BTC dari candle harian yang sudah tutup (suara komponen btc_ma50)."""
    v = next((k["suara"] for k in kp.get("komponen", []) if k["kode"] == "btc_ma50"), 0)
    return {1: "naik", 0: "netral", -1: "turun"}[int(v)]


def status(model: dict | None, kp: dict | None) -> dict:
    """Menurut model pasar: sisi mana yang boleh jalan sekarang. → {"beli": (boleh, alasan), "jual": (boleh, alasan)}"""
    if not model or not kp:
        return {}
    rz, skor = rezim_tutup(kp), int(kp["skor"])
    b, j = model["beli"], model["jual"]
    if rz != "naik":
        beli = (False, "BTC belum tren naik")
    elif skor > b["skor_maks"]:
        beli = (False, f"pasar sudah kepanasan: skor {angka(skor)}, batas {angka(b['skor_maks'])}")
    else:
        beli = (True, None)
    if rz == "naik":
        jual = (False, "BTC sedang tren naik")
    elif skor > j["skor_maks"]:
        jual = (False, f"pasar belum cukup lemah: skor {angka(skor)}, batas {angka(j['skor_maks'])}")
    else:
        jual = (True, None)
    return dict(beli=beli, jual=jual)


def izin(model: dict | None, strategi: str, kp: dict | None) -> tuple[bool, str | None]:
    """Boleh tidaknya sebuah strategi jalan pada kondisi pasar ini. → (boleh, alasan bila tidak)."""
    a = ((model or {}).get("strategi") or {}).get(strategi)
    if not a or not kp:
        return False, "strategi tidak ada di model pasar"
    if not a.get("aktif"):
        return False, "strategi tidak aktif di model pasar"
    return status(model, kp)["beli" if a["sisi"] == "long" else "jual"]
