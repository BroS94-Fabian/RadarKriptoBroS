# -*- coding: utf-8 -*-
"""
ORDER FLOW & MARKET PROFILE dari candle 1 jam
=============================================
Fitur per hari. Hanya memakai candle 1 jam yang SUDAH TUTUP sampai akhir hari itu (hari = 00.00–24.00 UTC,
sama dengan candle harian radar), jadi angka uji = angka yang bisa dihitung radar saat sinyal muncul.

Order flow (delta = beli agresif − jual agresif, dari "taker buy volume" Binance)
  d1, d3, d7   delta ÷ volume untuk 1 / 3 / 7 hari terakhir (−1…+1). d3 & d7 = arah CVD beberapa hari.
  d_akhir6     delta ÷ volume 6 jam terakhir hari itu
  d_tembus     delta ÷ volume pada jam-jam yang tutup DI ATAS batas atas zona nilai (v_tembus = porsi volumenya)
  d_jebol      delta ÷ volume pada jam-jam yang tutup DI BAWAH batas bawah zona nilai (v_jebol)

Market profile (zona nilai = 70% volume di sekitar POC; rumusnya sama dengan "zona akumulasi" radar)
  poc30, val30, vah30      profil VOLUME 30 hari SEBELUM hari itu (±720 candle 1 jam, 48 tingkat harga)
  tpoc30, tval30, tvah30   profil WAKTU (TPO: berapa jam harga menyentuh tiap tingkat), 30 hari sebelumnya
  poc90, val90, vah90      profil volume 90 hari sebelumnya
  h3, l3                   harga tertinggi / terendah 3 hari terakhir (termasuk hari itu)

KONFIRMASI = daftar konfirmasi yang ditetapkan DI MUKA (sebelum melihat hasil uji), searah teori:
beli dikonfirmasi bila harga diterima di atas zona nilai / POC dan delta positif; jual dulu = cerminannya.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BINS = 48
MS_HARI = 86_400_000
MS_JAM = 3_600_000
MIN_ISI = 0.8          # jendela profil harus terisi minimal 80% candle

KOLOM = ["o", "h", "l", "c", "qv", "n_jam", "d1", "d3", "d7", "d_akhir6", "d_tembus", "v_tembus", "d_jebol", "v_jebol",
         "poc30", "val30", "vah30", "tpoc30", "tval30", "tvah30", "poc90", "val90", "vah90", "h3", "l3"]
_HARGA = ["o", "h", "l", "poc30", "val30", "vah30", "tpoc30", "tval30", "tvah30", "poc90", "val90", "vah90", "h3", "l3"]


def _zona(vol: np.ndarray, edges: np.ndarray) -> tuple[float, float, float]:
    """POC + zona nilai 70% (melebar dari POC ke sisi yang volumenya lebih besar). → (poc, val, vah)"""
    bins = len(vol)
    poc_i = int(vol.argmax())
    target, acc = 0.70 * vol.sum(), vol[poc_i]
    lo_i = hi_i = poc_i
    while acc < target and (lo_i > 0 or hi_i < bins - 1):
        up = vol[hi_i + 1] if hi_i < bins - 1 else -1.0
        dn = vol[lo_i - 1] if lo_i > 0 else -1.0
        if up >= dn:
            hi_i += 1
            acc += up
        else:
            lo_i -= 1
            acc += dn
    return float((edges[poc_i] + edges[poc_i + 1]) / 2), float(edges[lo_i]), float(edges[hi_i + 1])


def profil(low, high, vol, close, bins: int = BINS, tpo: bool = False):
    """Profil volume (dan profil waktu/TPO bila tpo=True) dari sekumpulan candle.
    → (poc, val, vah) atau (poc, val, vah, tpoc, tval, tvah); None bila tidak bisa dihitung.
    Bagian volume identik dengan analisa.volume_profile (zona akumulasi radar)."""
    low, high = np.asarray(low, dtype=float), np.asarray(high, dtype=float)
    if len(low) == 0:
        return None
    lo, hi = float(low.min()), float(high.max())
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return None
    edges = np.linspace(lo, hi, bins + 1)
    L, H, V = low[:, None], high[:, None], np.asarray(vol, dtype=float)[:, None]
    span = H - L
    overlap = np.clip(np.minimum(H, edges[1:][None, :]) - np.maximum(L, edges[:-1][None, :]), 0, None)
    w = np.divide(overlap, span, out=np.zeros_like(overlap), where=span > 0)
    flat = span[:, 0] <= 0
    if flat.any():
        b = np.clip(np.searchsorted(edges, np.asarray(close, dtype=float)[flat], side="right") - 1, 0, bins - 1)
        w[np.where(flat)[0], b] = 1.0
    out = _zona((w * V).sum(axis=0), edges)
    if tpo:
        out += _zona((w > 0).sum(axis=0).astype(float), edges)
    return out


def fitur_harian(t, o, h, l, c, qv, tb, buang_hari_berjalan: bool = True, pakai_90: bool = True) -> pd.DataFrame:
    """Fitur order flow & market profile untuk tiap hari.
    t = waktu buka candle 1 jam (ms, UTC, urut naik, hanya candle yang sudah tutup); qv = volume (quote);
    tb = taker buy volume (quote). Indeks hasil = tanggal 'YYYY-MM-DD'."""
    t = np.asarray(t, dtype=np.int64)
    o, h, l, c, qv, tb = (np.asarray(x, dtype=float) for x in (o, h, l, c, qv, tb))
    if len(t) == 0:
        return pd.DataFrame(columns=KOLOM)
    day = t // MS_HARI
    days, s = np.unique(day, return_index=True)
    e = np.r_[s[1:], len(day)]
    n = len(days)
    delta = 2 * tb - qv
    QV, DL = np.add.reduceat(qv, s), np.add.reduceat(delta, s)
    Hd, Ld = np.maximum.reduceat(h, s), np.minimum.reduceat(l, s)
    idx, full = pd.Index(days), pd.RangeIndex(int(days[0]), int(days[-1]) + 1)
    sQ, sD = pd.Series(QV, index=idx).reindex(full), pd.Series(DL, index=idx).reindex(full)

    def rasio(k):
        q, d = sQ.rolling(k, min_periods=k).sum(), sD.rolling(k, min_periods=k).sum()
        return (d / q.where(q > 0)).reindex(idx).to_numpy()

    F = {k: np.full(n, np.nan) for k in KOLOM}
    F["o"], F["h"], F["l"], F["c"], F["qv"], F["n_jam"] = o[s], Hd, Ld, c[e - 1], QV, (e - s).astype(float)
    F["d1"] = np.divide(DL, QV, out=np.full(n, np.nan), where=QV > 0)
    F["d3"], F["d7"] = rasio(3), rasio(7)
    F["h3"] = pd.Series(Hd, index=idx).reindex(full).rolling(3, min_periods=3).max().reindex(idx).to_numpy()
    F["l3"] = pd.Series(Ld, index=idx).reindex(full).rolling(3, min_periods=3).min().reindex(idx).to_numpy()

    def jendela(k, hari):
        i1 = int(s[k])
        i0 = int(np.searchsorted(day, days[k] - hari, side="left"))
        if i1 - i0 < 24 * hari * MIN_ISI or day[i0] > days[k] - hari + max(1, hari // 10):
            return None
        return slice(i0, i1)

    for k in range(n):
        a, b = int(s[k]), int(e[k])
        w = jendela(k, 30)
        if w is not None:
            p = profil(l[w], h[w], qv[w], c[w], tpo=True)
            if p:
                F["poc30"][k], F["val30"][k], F["vah30"][k], F["tpoc30"][k], F["tval30"][k], F["tvah30"][k] = p
                cj, qj, dj = c[a:b], qv[a:b], delta[a:b]
                tot = qj.sum()
                for nama, m in (("tembus", cj > p[2]), ("jebol", cj < p[1])):
                    q = qj[m].sum()
                    if q > 0:
                        F["d_" + nama][k] = dj[m].sum() / q
                    F["v_" + nama][k] = q / tot if tot > 0 else np.nan
        if pakai_90:
            w = jendela(k, 90)
            if w is not None:
                p = profil(l[w], h[w], qv[w], c[w])
                if p:
                    F["poc90"][k], F["val90"][k], F["vah90"][k] = p
        q6 = qv[max(a, b - 6):b].sum()
        if q6 > 0:
            F["d_akhir6"][k] = delta[max(a, b - 6):b].sum() / q6
    out = pd.DataFrame(F, index=pd.to_datetime(days * MS_HARI, unit="ms").strftime("%Y-%m-%d"))
    out.index.name = "tanggal"
    if buang_hari_berjalan and (t[-1] % MS_HARI) != 23 * MS_JAM:      # hari terakhir belum lengkap
        out = out.iloc[:-1]
    return out


def fitur_dari_candle(hc: pd.DataFrame, pakai_90: bool = False) -> pd.DataFrame:
    """Sama dengan fitur_harian, dari DataFrame candle 1 jam format radar (time, open, high, low, close, qvol,
    taker_buy_q, closed). Dipakai radar live: baris terakhir = hari terakhir yang sudah lengkap."""
    if hc is None or len(hc) == 0:
        return pd.DataFrame(columns=KOLOM)
    d = hc[hc["closed"]] if "closed" in hc else hc
    t = ((d["time"] - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(milliseconds=1)).to_numpy()
    return fitur_harian(t, d["open"], d["high"], d["low"], d["close"], d["qvol"], d["taker_buy_q"], pakai_90=pakai_90)


# --------------------------------------------------------------------------- #
# Simpan / baca (harga disimpan sebagai % terhadap harga tutup supaya berkas kecil)
# --------------------------------------------------------------------------- #
def kemas(F: pd.DataFrame) -> pd.DataFrame:
    out = F.copy()
    for k in _HARGA:
        out[k] = ((F[k] / F["c"] - 1) * 100).round(3 if k in ("h", "l") else 2)   # h & l dipakai simulasi → lebih teliti
    for k in ("d1", "d3", "d7", "d_akhir6", "d_tembus", "v_tembus", "d_jebol", "v_jebol"):
        out[k] = F[k].round(3)
    out["qv"] = F["qv"].round(0).astype("Int64")
    out["n_jam"] = F["n_jam"].round(0).astype("Int64")
    return out


def buka(F: pd.DataFrame) -> pd.DataFrame:
    out = F.copy()
    for k in _HARGA:
        out[k] = F["c"] * (1 + F[k] / 100)
    return out


# --------------------------------------------------------------------------- #
# Konfirmasi (ditetapkan di muka). d = DataFrame berisi kolom fitur; hasil = Series bool.
# Fitur kosong (NaN) → tidak terkonfirmasi.
# --------------------------------------------------------------------------- #
def _l(d, lv="30", tpo=False):
    p = "t" if tpo else ""
    return d[f"{p}poc{lv}"], d[f"{p}val{lv}"], d[f"{p}vah{lv}"]


KONFIRMASI = {
    # kode: (nama, penjelasan beli, penjelasan jual dulu, fungsi beli, fungsi jual)
    "va": ("Tutup di luar zona nilai",
           "harga tutup di atas batas atas zona nilai 30 hari", "harga tutup di bawah batas bawah zona nilai 30 hari",
           lambda d: d["c"] > d["vah30"], lambda d: d["c"] < d["val30"]),
    "poc": ("Tutup melewati POC",
            "harga tutup di atas POC 30 hari", "harga tutup di bawah POC 30 hari",
            lambda d: d["c"] > d["poc30"], lambda d: d["c"] < d["poc30"]),
    "delta1": ("Delta hari sinyal searah",
               "beli agresif > jual agresif di hari sinyal", "jual agresif > beli agresif di hari sinyal",
               lambda d: d["d1"] > 0, lambda d: d["d1"] < 0),
    "delta3": ("Delta 3 hari searah (CVD)",
               "CVD 3 hari naik", "CVD 3 hari turun",
               lambda d: d["d3"] > 0, lambda d: d["d3"] < 0),
    "va_delta1": ("Di luar zona nilai + delta hari sinyal",
                  "tutup di atas zona nilai DAN delta hari sinyal positif", "tutup di bawah zona nilai DAN delta hari sinyal negatif",
                  lambda d: (d["c"] > d["vah30"]) & (d["d1"] > 0), lambda d: (d["c"] < d["val30"]) & (d["d1"] < 0)),
    "poc_delta3": ("Melewati POC + delta 3 hari",
                   "tutup di atas POC DAN CVD 3 hari naik", "tutup di bawah POC DAN CVD 3 hari turun",
                   lambda d: (d["c"] > d["poc30"]) & (d["d3"] > 0), lambda d: (d["c"] < d["poc30"]) & (d["d3"] < 0)),
    "uji_va_delta1": ("Uji zona nilai + delta hari sinyal",
                      "3 hari terakhir menyentuh zona nilai, tutup di atas POC, delta positif",
                      "pantulan 3 hari terakhir menyentuh zona nilai, tutup di bawah POC, delta negatif",
                      lambda d: (d["l3"] <= d["vah30"]) & (d["c"] > d["poc30"]) & (d["d1"] > 0),
                      lambda d: (d["h3"] >= d["val30"]) & (d["c"] < d["poc30"]) & (d["d1"] < 0)),
    "tembus_delta": ("Delta saat harga di luar zona nilai",
                     "tutup di atas zona nilai DAN jam-jam di atasnya didominasi beli agresif",
                     "tutup di bawah zona nilai DAN jam-jam di bawahnya didominasi jual agresif",
                     lambda d: (d["c"] > d["vah30"]) & (d["d_tembus"] > 0), lambda d: (d["c"] < d["val30"]) & (d["d_jebol"] < 0)),
}
KODE = list(KONFIRMASI)


def konfirmasi(d: pd.DataFrame, kode: str, sisi) -> pd.Series:
    """sisi = 'long' / 'short' atau Series berisi sisi tiap baris."""
    _, _, _, fb, fj = KONFIRMASI[kode]
    if isinstance(sisi, str):
        return (fb(d) if sisi == "long" else fj(d)).fillna(False).astype(bool)
    return pd.Series(np.where(sisi == "long", fb(d).fillna(False), fj(d).fillna(False)), index=d.index).astype(bool)


def varian_level(d: pd.DataFrame, jenis: str) -> pd.DataFrame:
    """Ganti level profil utama (volume 30 hari) dengan varian lain: 'tpo30' atau 'vol90' — untuk uji kepekaan."""
    out = d.copy()
    src = dict(tpo30=("tpoc30", "tval30", "tvah30"), vol90=("poc90", "val90", "vah90"))[jenis]
    out["poc30"], out["val30"], out["vah30"] = d[src[0]], d[src[1]], d[src[2]]
    return out
