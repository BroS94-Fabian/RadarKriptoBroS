# -*- coding: utf-8 -*-
"""
MESIN ANALISA TEKNIKAL — Radar Kripto
=====================================
Semua dihitung dari candle HARIAN yang sudah tutup (+ data per jam untuk volume):

  1. Trend line      : garis support/resistance dari titik pivot (zigzag)
  2. Moving Average  : MA20, MA50, MA200, golden/death cross
  3. Bollinger Bands : %B, squeeze (volatilitas menyempit)
  4. Candlestick     : hammer, engulfing, morning/evening star, dst.
  5. Chart pattern   : 18 pola sesuai gambar + target "measured move"
  6. MACD (12,26,9)  : cross naik/turun
  7. RSI (14)        : overbought/oversold + divergensi
  8. Stochastic      : (14,3,3) cross di area oversold/overbought
  9. Elliott Wave    : perkiraan posisi gelombang otomatis (eksperimental)
 10. Akumulasi volume: OBV, CMF, beli agresif, profil volume (zona akumulasi)

Pola bearish dideteksi dengan "membalik" grafik (harga dikali -1), sehingga
satu aturan dipakai untuk dua arah: Double Bottom <-> Double Top, dst.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


# =========================================================================== #
# Format angka gaya Indonesia
# =========================================================================== #
def _id(s: str) -> str:
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_price(p) -> str:
    if p is None or not np.isfinite(p):
        return "-"
    neg = p < 0
    p = abs(p)
    if p >= 1000:
        s = f"{p:,.0f}"
    elif p >= 10:
        s = f"{p:,.2f}"
    elif p >= 1:
        s = f"{p:,.3f}"
    else:
        dec = max(4, int(-np.floor(np.log10(p))) + 3) if p > 0 else 4
        s = f"{p:.{min(dec, 10)}f}"
    return ("-" if neg else "") + "$" + _id(s)


def fmt_big(v) -> str:
    if v is None or not np.isfinite(v):
        return "-"
    for div, unit, dec in ((1e9, " M", 2), (1e6, " jt", 1), (1e3, " rb", 0)):
        if abs(v) >= div:
            return "$" + _id(f"{v / div:,.{dec}f}") + unit
    return "$" + _id(f"{v:,.0f}")


def fmt_pct(x, plus: bool = True) -> str:
    if x is None or not np.isfinite(x):
        return "-"
    s = _id(f"{x:+.1f}%" if plus else f"{x:.0f}%")
    return s.replace("-", "−")


def fmt_x(x) -> str:
    return "-" if x is None or not np.isfinite(x) else _id(f"{x:.1f}x")


def fmt_dec(x) -> str:
    return "-" if x is None or not np.isfinite(x) else _id(f"{x:+.2f}").replace("-", "−")


def _f(x, nd=4):
    """Angka aman untuk JSON (NaN -> None)."""
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, nd) if np.isfinite(x) else None


def _r(p):
    """Bulatkan harga dengan 6 angka penting."""
    if p is None or not np.isfinite(p) or p == 0:
        return _f(p)
    return float(f"{p:.6g}")


# =========================================================================== #
# 1. Indikator dasar
# =========================================================================== #
def sma(x, n):
    return pd.Series(x, dtype=float).rolling(n, min_periods=n).mean().to_numpy()


def ema(x, n):
    return pd.Series(x, dtype=float).ewm(span=n, adjust=False).mean().to_numpy()


def rsi(close, n=14):
    s = pd.Series(close, dtype=float)
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    out = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    out = out.mask((dn == 0) & up.notna(), 100.0)
    return out.to_numpy()


def macd(close, f=12, s=26, sig=9):
    m = ema(close, f) - ema(close, s)
    sg = ema(m, sig)
    return m, sg, m - sg


def stochastic(high, low, close, n=14, k=3, d=3):
    hh = pd.Series(high, dtype=float).rolling(n).max()
    ll = pd.Series(low, dtype=float).rolling(n).min()
    raw = 100 * (pd.Series(close, dtype=float) - ll) / (hh - ll).replace(0, np.nan)
    K = raw.rolling(k).mean()
    D = K.rolling(d).mean()
    return K.to_numpy(), D.to_numpy()


def bollinger(close, n=20, k=2.0):
    s = pd.Series(close, dtype=float)
    mid = s.rolling(n).mean()
    sd = s.rolling(n).std(ddof=0)
    up, lo = mid + k * sd, mid - k * sd
    pctb = (s - lo) / (up - lo).replace(0, np.nan)
    bw = (up - lo) / mid
    return mid.to_numpy(), up.to_numpy(), lo.to_numpy(), pctb.to_numpy(), bw.to_numpy()


def atr(high, low, close, n=14):
    h, l, c = (pd.Series(a, dtype=float) for a in (high, low, close))
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()


def obv(close, vol):
    direction = np.sign(np.diff(close, prepend=close[0]))
    return np.cumsum(direction * vol)


def cmf(high, low, close, vol, n=20):
    rng = np.where(high - low > 0, high - low, np.nan)
    mfm = np.nan_to_num(((close - low) - (high - close)) / rng)
    v = vol[-n:].sum()
    return float((mfm[-n:] * vol[-n:]).sum() / v) if v > 0 else np.nan


def _ok(*xs) -> bool:
    return all(x is not None and np.isfinite(x) for x in xs)


def _cross_up(a, b, j, k=3) -> bool:
    for i in range(j, max(j - k, 0), -1):
        if _ok(a[i], b[i], a[i - 1], b[i - 1]) and a[i] > b[i] and a[i - 1] <= b[i - 1]:
            return True
    return False


def _cross_down(a, b, j, k=3) -> bool:
    for i in range(j, max(j - k, 0), -1):
        if _ok(a[i], b[i], a[i - 1], b[i - 1]) and a[i] < b[i] and a[i - 1] >= b[i - 1]:
            return True
    return False


# =========================================================================== #
# Pivot (ZigZag) & garis
# =========================================================================== #
def zigzag(high, low, thr):
    """Titik balik harga: pergerakan >= thr (mis. 0,06 = 6%) dianggap ayunan baru.
    Titik terakhir bersifat sementara (tent=True) karena ayunannya belum selesai."""
    n = len(high)
    piv: list[dict] = []
    if n < 3:
        return piv
    up = None
    hi, lo, hi_i, lo_i = high[0], low[0], 0, 0
    cand, cand_i = 0.0, 0
    for i in range(1, n):
        if up is None:
            if high[i] > hi:
                hi, hi_i = high[i], i
            if low[i] < lo:
                lo, lo_i = low[i], i
            if lo > 0 and hi >= lo * (1 + thr):
                if hi_i > lo_i:
                    piv.append({"i": lo_i, "p": float(lo), "t": "L"})
                    up, cand, cand_i = True, hi, hi_i
                else:
                    piv.append({"i": hi_i, "p": float(hi), "t": "H"})
                    up, cand, cand_i = False, lo, lo_i
            continue
        if up:
            if high[i] >= cand:
                cand, cand_i = high[i], i
            elif low[i] <= cand * (1 - thr):
                piv.append({"i": cand_i, "p": float(cand), "t": "H"})
                up, cand, cand_i = False, low[i], i
        else:
            if low[i] <= cand:
                cand, cand_i = low[i], i
            elif high[i] >= cand * (1 + thr):
                piv.append({"i": cand_i, "p": float(cand), "t": "L"})
                up, cand, cand_i = True, high[i], i
    for p in piv:
        p["tent"] = False
    if up is not None:
        piv.append({"i": cand_i, "p": float(cand), "t": "H" if up else "L", "tent": True})
    return piv


class Garis:
    def __init__(self, i1, p1, i2, p2):
        self.i1, self.p1, self.i2, self.p2 = float(i1), float(p1), float(i2), float(p2)
        self.m = (self.p2 - self.p1) / (self.i2 - self.i1) if self.i2 != self.i1 else 0.0

    def at(self, i):
        return self.p1 + self.m * (i - self.i1)


def _fit(points):
    xs = np.array([p["i"] for p in points], float)
    ys = np.array([p["p"] for p in points], float)
    if len(points) == 2:
        m = (ys[1] - ys[0]) / (xs[1] - xs[0])
        b = ys[0] - m * xs[0]
    else:
        m, b = np.polyfit(xs, ys, 1)
    res = float(np.max(np.abs(ys - (m * xs + b))))
    return float(m), float(b), res


class Ctx:
    """Data satu koin untuk pendeteksi pola (bisa dibalik untuk pola bearish)."""

    def __init__(self, o, h, l, c, v, price, piv, atrp, flipped=False):
        self.o, self.h, self.l, self.c, self.v = o, h, l, c, v
        self.price, self.piv, self.atrp, self.flipped = price, piv, atrp, flipped
        self.n = len(c)
        self.j = self.n - 1
        self.ref = float(np.nanmean(np.abs(c[-60:])))
        self.tol = float(np.clip(0.8 * atrp, 0.02, 0.06))

    def flip(self) -> "Ctx":
        fp = [{"i": p["i"], "p": -p["p"], "t": "L" if p["t"] == "H" else "H", "tent": p["tent"]}
              for p in self.piv]
        return Ctx(-self.o, -self.l, -self.h, -self.c, self.v, -self.price, fp, self.atrp, not self.flipped)


# =========================================================================== #
# 5. Chart pattern (sesuai gambar) — ditulis untuk arah NAIK, arah TURUN = dibalik
# =========================================================================== #
NAMA_FLIP = {
    "Double Bottom": "Double Top", "Triple Bottom": "Triple Top",
    "Inverse Head and Shoulders": "Head and Shoulders",
    "Falling Wedge": "Rising Wedge", "Ascending Triangle": "Descending Triangle",
    "Bull Flag (Downward Flag)": "Bear Flag (Upward Flag)",
    "Bullish Pennant": "Bearish Pennant",
}
LEVEL_FLIP = {"neckline": "neckline", "resistance": "support", "garis atas": "garis bawah",
              "garis atas bendera": "garis bawah bendera"}
LABEL_FLIP = {"Dasar 1": "Puncak 1", "Dasar 2": "Puncak 2", "Dasar 3": "Puncak 3",
              "Bahu kiri": "Bahu kiri", "Kepala": "Kepala", "Bahu kanan": "Bahu kanan"}
UJI_FLIP = {"sedang menguji dasar ke-2": "sedang menguji puncak ke-2",
            "sedang menguji dasar ke-3": "sedang menguji puncak ke-3",
            "sedang membentuk bahu kanan": "sedang membentuk bahu kanan"}

# Panduan arti tiap pola (ditampilkan di dashboard)
ARTI_POLA = {
    "Double Bottom": "Harga 2x gagal turun di level yang sama → pembeli bertahan. Target = neckline + tinggi pola.",
    "Triple Bottom": "Harga 3x gagal turun di level yang sama → support sangat kuat. Target = neckline + tinggi pola.",
    "Inverse Head and Shoulders": "Bahu–kepala–bahu terbalik di dasar tren turun → pembalikan naik. Target = neckline + (neckline − kepala).",
    "Falling Wedge": "Harga turun dalam baji yang menyempit → tekanan jual habis. Target = awal baji.",
    "Ascending Triangle": "Atap datar + dasar makin tinggi → pembeli makin agresif. Target = atap + tinggi segitiga.",
    "Symmetrical Triangle": "Segitiga menyempit → arah ikut breakout. Target = titik breakout ± tinggi segitiga.",
    "Bull Flag (Downward Flag)": "Naik tajam lalu konsolidasi turun → lanjut naik. Target = breakout + panjang tiang.",
    "Bullish Pennant": "Naik tajam lalu segitiga kecil → lanjut naik. Target = breakout + panjang tiang.",
    "Cup and Handle": "Dasar membulat (cangkir) + koreksi kecil (gagang) → lanjut naik. Target = bibir + kedalaman cangkir.",
    "Double Top": "Harga 2x gagal naik di level yang sama → penjual bertahan. Target = neckline − tinggi pola.",
    "Triple Top": "Harga 3x gagal naik di level yang sama → resistance sangat kuat. Target = neckline − tinggi pola.",
    "Head and Shoulders": "Bahu–kepala–bahu di puncak tren naik → pembalikan turun. Target = neckline − (kepala − neckline).",
    "Rising Wedge": "Harga naik dalam baji yang menyempit → tenaga beli habis. Target = awal baji.",
    "Descending Triangle": "Lantai datar + atap makin rendah → penjual makin agresif. Target = lantai − tinggi segitiga.",
    "Bear Flag (Upward Flag)": "Turun tajam lalu konsolidasi naik → lanjut turun. Target = breakdown − panjang tiang.",
    "Bearish Pennant": "Turun tajam lalu segitiga kecil → lanjut turun. Target = breakdown − panjang tiang.",
}


def _since_break(K: Ctx, level_at, start) -> int:
    """Berapa candle tutup berturut-turut (dari yang terakhir) sudah di atas level."""
    cnt = 0
    for i in range(K.j, max(int(start), 0) - 1, -1):
        if K.c[i] > level_at(i) + 0.003 * K.ref:
            cnt += 1
        else:
            break
    return cnt


def _pola(K: Ctx, nama, level, level_nama, target, batal, kekuatan, mulai, garis, titik,
          status=None, uji_teks="sedang menguji dasar ke-2"):
    if status is None:
        status = "breakout" if K.price > level + 0.005 * K.ref else "terbentuk"
    if status == "breakout":
        kekuatan += 0.2
        vavg = np.nanmean(K.v[max(0, K.j - 20):K.j])
        if vavg > 0 and K.v[K.j] > 1.5 * vavg:
            kekuatan += 0.1  # breakout dengan volume besar
    return dict(nama=nama, arah="naik", status=status, level=float(level), level_nama=level_nama,
                target=float(target), batal=float(batal), kekuatan=float(min(1.0, kekuatan)),
                mulai=int(mulai), garis=garis, titik=titik, uji_teks=uji_teks)


def _sah(K: Ctx, P) -> bool:
    return P["target"] > K.price > P["batal"] and P["target"] > P["level"]


def _balik(P):
    Q = dict(P)
    Q["nama"] = NAMA_FLIP.get(P["nama"], P["nama"])
    Q["arah"] = "turun"
    for k in ("level", "target", "batal"):
        Q[k] = -P[k]
    Q["level_nama"] = LEVEL_FLIP.get(P["level_nama"], P["level_nama"])
    Q["uji_teks"] = UJI_FLIP.get(P["uji_teks"], P["uji_teks"])
    Q["garis"] = [dict(g, p1=-g["p1"], p2=-g["p2"]) for g in P["garis"]]
    Q["titik"] = [dict(t, p=-t["p"], label=LABEL_FLIP.get(t["label"], t["label"])) for t in P["titik"]]
    return Q


def _prior_drop(S, idx, level, height) -> bool:
    """Ada tren turun sebelum pola (puncak sebelumnya jauh di atas)."""
    return idx >= 1 and S[idx - 1]["p"] > level + 0.3 * height


def det_bottoms(K: Ctx):
    """Double Bottom & Triple Bottom (dibalik: Double/Triple Top)."""
    S, out = K.piv, []
    ref, tol, j = K.ref, K.tol, K.j
    for e in (len(S) - 1, len(S) - 2):
        if e < 2 or S[e]["t"] != "L" or S[e]["i"] < j - 45:
            continue
        found = False
        if e >= 4 and [S[e - k]["t"] for k in range(5)] == ["L", "H", "L", "H", "L"]:
            Ls, Hs = [S[e - 4], S[e - 2], S[e]], [S[e - 3], S[e - 1]]
            lp = [x["p"] for x in Ls]
            neck, low = max(x["p"] for x in Hs), min(lp)
            height = neck - low
            if (max(lp) - low <= 1.2 * tol * ref and height >= max(0.05, 1.5 * tol) * ref
                    and abs(Hs[0]["p"] - Hs[1]["p"]) <= tol * ref  # neckline datar, bukan segitiga
                    and Ls[2]["i"] - Ls[0]["i"] >= 15 and Ls[0]["i"] >= j - 160):
                P = _bottom(K, "Triple Bottom", Ls, neck, low, height, _prior_drop(S, e - 4, neck, height))
                if P:
                    out.append(P)
                    found = True
        if found:
            continue
        L1, Hn, L2 = S[e - 2], S[e - 1], S[e]
        if Hn["t"] != "H" or L1["t"] != "L":
            continue
        low = min(L1["p"], L2["p"])
        height = Hn["p"] - low
        if (abs(L1["p"] - L2["p"]) <= tol * ref and height >= max(0.05, 1.5 * tol) * ref
                and 7 <= L2["i"] - L1["i"] <= 120):
            P = _bottom(K, "Double Bottom", [L1, L2], Hn["p"], low, height, _prior_drop(S, e - 2, Hn["p"], height))
            if P:
                out.append(P)
    return out


def _bottom(K: Ctx, nama, Ls, neck, low, height, prior):
    ref, tol, j = K.ref, K.tol, K.j
    last = Ls[-1]
    status = None
    if last["tent"]:
        if K.price <= last["p"] + 0.25 * height:
            status = "uji"
        batal = min(x["p"] for x in Ls[:-1]) - tol * ref
    else:
        if _since_break(K, lambda i: neck, last["i"]) > 7:
            return None
        batal = low - 0.5 * tol * ref
    k = 0.55 + (0.1 if prior else 0) + (0.05 if nama.startswith("Triple") else 0)
    labels = ["Dasar 1", "Dasar 2", "Dasar 3"]
    titik = [dict(i=int(x["i"]), p=float(x["p"]), label=labels[n]) for n, x in enumerate(Ls)]
    garis = [dict(i1=int(Ls[0]["i"]), p1=float(neck), i2=int(j), p2=float(neck), label="Neckline")]
    uji = "sedang menguji dasar ke-3" if nama.startswith("Triple") else "sedang menguji dasar ke-2"
    P = _pola(K, nama, neck, "neckline", neck + height, batal, k, Ls[0]["i"], garis, titik, status, uji)
    return P if _sah(K, P) else None


def det_ihs(K: Ctx):
    """Inverse Head and Shoulders (dibalik: Head and Shoulders)."""
    S, out = K.piv, []
    ref, tol, j = K.ref, K.tol, K.j
    for e in (len(S) - 1, len(S) - 2):
        if e < 4:
            continue
        LS, H1, HD, H2, RS = S[e - 4], S[e - 3], S[e - 2], S[e - 1], S[e]
        if [x["t"] for x in (LS, H1, HD, H2, RS)] != ["L", "H", "L", "H", "L"]:
            continue
        if RS["i"] < j - 40 or LS["i"] < j - 180:
            continue
        if not HD["p"] < min(LS["p"], RS["p"]) - 0.8 * tol * ref:
            continue
        if abs(LS["p"] - RS["p"]) > 2.5 * tol * ref:
            continue
        a, b = HD["i"] - LS["i"], RS["i"] - HD["i"]
        if a < 3 or b < 3 or not 0.33 <= a / b <= 3.0:
            continue
        nl = Garis(H1["i"], H1["p"], H2["i"], H2["p"])
        if nl.at(RS["i"]) < RS["p"] + 0.5 * tol * ref or nl.at(LS["i"]) < LS["p"] + 0.5 * tol * ref:
            continue
        height = nl.at(HD["i"]) - HD["p"]
        level = nl.at(j)
        status = None
        if RS["tent"]:
            if K.price <= RS["p"] + 0.35 * (nl.at(RS["i"]) - RS["p"]):
                status = "uji"
            batal = HD["p"] - 0.3 * tol * ref
        else:
            if _since_break(K, nl.at, RS["i"]) > 7:
                continue
            batal = RS["p"] - 0.5 * tol * ref
        k = 0.65 + (0.1 if _prior_drop(S, e - 4, level, height) else 0)
        titik = [dict(i=int(LS["i"]), p=float(LS["p"]), label="Bahu kiri"),
                 dict(i=int(HD["i"]), p=float(HD["p"]), label="Kepala"),
                 dict(i=int(RS["i"]), p=float(RS["p"]), label="Bahu kanan")]
        garis = [dict(i1=int(LS["i"]), p1=float(nl.at(LS["i"])), i2=int(j), p2=float(level), label="Neckline")]
        P = _pola(K, "Inverse Head and Shoulders", level, "neckline", level + height, batal, k, LS["i"],
                  garis, titik, status, "sedang membentuk bahu kanan")
        if _sah(K, P):
            out.append(P)
    return out


def det_triangles(K: Ctx, simetris=True):
    """Ascending Triangle, Falling Wedge, Symmetrical Triangle
    (dibalik: Descending Triangle, Rising Wedge)."""
    S = [p for p in K.piv if not p["tent"]]
    out = []
    ref, tol, j = K.ref, K.tol, K.j
    for k in (6, 5, 4):
        if len(S) < k:
            continue
        P = S[-k:]
        start, last = P[0]["i"], P[-1]["i"]
        if last < j - 30 or start < j - 160 or last - start < 12:
            continue
        Hs = [p for p in P if p["t"] == "H"]
        Ls = [p for p in P if p["t"] == "L"]
        if len(Hs) < 2 or len(Ls) < 2:
            continue
        mu, bu, ru = _fit(Hs)
        ml, bl, rl = _fit(Ls)
        if ru > 0.6 * tol * ref or rl > 0.6 * tol * ref:
            continue
        U = lambda i, mu=mu, bu=bu: mu * i + bu  # noqa: E731
        Lo = lambda i, ml=ml, bl=bl: ml * i + bl  # noqa: E731
        ws, we = U(start) - Lo(start), U(j) - Lo(j)
        if ws < 2 * tol * ref or we <= 0:
            continue
        margin = 0.5 * tol * ref
        if any(K.c[i] > U(i) + margin or K.c[i] < Lo(i) - margin for i in range(start, last + 1)):
            continue
        du, dl = U(last) - U(start), Lo(last) - Lo(start)
        flat = tol * ref
        conv = we < 0.8 * ws
        nama = None
        if abs(du) <= flat and dl >= 1.5 * flat and conv:
            nama = "Ascending Triangle"
        elif du < -flat and dl < -flat and mu < ml and conv:
            nama = "Falling Wedge"
        elif simetris and du <= -0.8 * flat and dl >= 0.8 * flat and conv:
            nama = "Symmetrical Triangle"
        if not nama:
            continue
        garis = [dict(i1=int(start), p1=float(U(start)), i2=int(j), p2=float(U(j)), label=""),
                 dict(i1=int(start), p1=float(Lo(start)), i2=int(j), p2=float(Lo(j)), label="")]
        titik: list = []
        if nama == "Symmetrical Triangle":
            if K.price > U(j) + 0.005 * ref:
                arah = 1
            elif K.price < Lo(j) - 0.005 * ref:
                arah = -1
            else:
                prev = K.c[max(0, start - 30)]
                arah = 1 if K.c[start] >= prev else -1
            if arah == 1:
                if _since_break(K, U, last) > 7:
                    continue
                Pp = _pola(K, nama, U(j), "garis atas", U(j) + ws, Lo(j) - margin, 0.5, start, garis, titik)
                if _sah(K, Pp):
                    out.append(Pp)
            else:
                cnt = 0
                for i in range(j, last - 1, -1):
                    if K.c[i] < Lo(i) - 0.003 * ref:
                        cnt += 1
                    else:
                        break
                if cnt > 7:
                    continue
                lvl = Lo(j)
                st = "breakout" if K.price < lvl - 0.005 * ref else "terbentuk"
                Pp = dict(nama=nama, arah="turun", status=st, level=float(lvl), level_nama="garis bawah",
                          target=float(lvl - ws), batal=float(U(j) + margin),
                          kekuatan=0.5 + (0.2 if st == "breakout" else 0), mulai=int(start),
                          garis=garis, titik=titik, uji_teks="")
                if Pp["target"] < K.price < Pp["batal"]:
                    out.append(Pp)
            break
        if K.price < Lo(j) - margin:
            continue  # sudah jebol ke arah berlawanan
        if _since_break(K, U, last) > 7:
            continue
        if nama == "Ascending Triangle":
            Pp = _pola(K, nama, U(j), "resistance", U(j) + ws, Lo(j) - margin, 0.6, start, garis, titik)
        else:
            Pp = _pola(K, nama, U(j), "garis atas", max(U(start), U(j) + ws), Lo(j) - margin, 0.6, start,
                       garis, titik)
        if _sah(K, Pp):
            out.append(Pp)
            break
    return out


def det_flags(K: Ctx):
    """Bull Flag (gambar: 'Downward Flag') & Bullish Pennant
    (dibalik: Bear Flag 'Upward Flag' & Bearish Pennant)."""
    out = []
    ref, tol, j, atrp = K.ref, K.tol, K.j, K.atrp
    if K.n < 40:
        return out
    a, b_ = j - 22, j - 4
    t = a + int(np.argmax(K.h[a:b_ + 1]))
    b0 = max(0, t - 15)
    if t - b0 < 2:
        return out
    b = b0 + int(np.argmin(K.l[b0:t]))
    pole = K.h[t] - K.l[b]
    if t - b < 2 or pole < max(0.12, 3.5 * atrp) * ref or pole / (t - b) < 0.012 * ref:
        return out
    m = j - t
    if m < 4 or m > 20:
        return out
    cons_l = K.l[t + 1:j + 1]
    retr = K.h[t] - cons_l.min()
    if not 0.08 * pole <= retr <= 0.5 * pole:
        return out
    xh, xl = np.arange(t, j + 1), np.arange(t + 1, j + 1)
    mu = np.polyfit(xh, K.h[t:j + 1], 1)[0]
    ml = np.polyfit(xl, cons_l, 1)[0]
    bu = float(np.max(K.h[t:j + 1] - mu * xh))   # garis atas menyentuh puncak tertinggi
    bl = float(np.min(cons_l - ml * xl))         # garis bawah menyentuh dasar terendah
    U = lambda i: mu * i + bu  # noqa: E731
    Lo = lambda i: ml * i + bl  # noqa: E731
    ws, we = U(t + 1) - Lo(t + 1), U(j) - Lo(j)
    if ws <= 0 or we <= 0:
        return out
    flat = 0.004 * ref  # kemiringan "datar" per candle
    if we < 0.75 * ws and mu < 0 < ml:
        nama = "Bullish Pennant"
    elif mu <= flat and ml <= flat and abs(we - ws) <= 0.6 * ws:
        nama = "Bull Flag (Downward Flag)"
    else:
        return out
    k = 0.6
    vp, vc = np.nanmean(K.v[b:t + 1]), np.nanmean(K.v[t + 1:j + 1])
    if vc > 0 and vp > 1.2 * vc:
        k += 0.1  # volume tiang besar, konsolidasi sepi = khas bendera
    garis = [dict(i1=int(b), p1=float(K.l[b]), i2=int(t), p2=float(K.h[t]), label="Tiang"),
             dict(i1=int(t), p1=float(U(t)), i2=int(j), p2=float(U(j)), label=""),
             dict(i1=int(t + 1), p1=float(Lo(t + 1)), i2=int(j), p2=float(Lo(j)), label="")]
    P = _pola(K, nama, U(j), "garis atas bendera", U(j) + pole, cons_l.min() - 0.3 * tol * ref, k, b,
              garis, [])
    if _sah(K, P):
        out.append(P)
    return out


def det_cup(K: Ctx):
    """Cup and Handle (hanya arah naik, sesuai gambar)."""
    out = []
    ref, tol, j = K.ref, K.tol, K.j
    if K.n < 60:
        return out
    a = max(0, j - 30)
    r2 = a + int(np.argmax(K.h[a:j - 2]))
    if r2 > j - 3:
        return out
    w0, w1 = max(0, r2 - 150), r2 - 30  # cangkir minimal 30 candle
    if w1 - w0 < 5:
        return out
    r1 = w0 + int(np.argmax(K.h[w0:w1]))
    rim = max(K.h[r1], K.h[r2])
    if abs(K.h[r1] - K.h[r2]) > max(0.05, 2 * tol) * rim:
        return out
    bi = r1 + int(np.argmin(K.l[r1:r2 + 1]))
    depth = min(K.h[r1], K.h[r2]) - K.l[bi]
    if not 0.12 * rim <= depth <= 0.6 * rim:
        return out
    pos = (bi - r1) / (r2 - r1)
    if not 0.25 <= pos <= 0.75:
        return out
    inner_l = K.l[r1 + 1:r2]
    if np.mean(inner_l <= K.l[bi] + depth / 3) < 0.4:
        return out  # dasar berbentuk V, bukan U
    if np.any(K.h[r1 + 1:r2] > rim + tol * ref):
        return out
    hl = float(K.l[r2 + 1:j + 1].min())
    pull = K.h[r2] - hl
    if not 0.03 * rim <= pull <= 0.5 * depth or hl < K.l[bi] + depth / 2:
        return out
    level = float(K.h[r2])
    if _since_break(K, lambda i: level, r2) > 7:
        return out
    garis = [dict(i1=int(r1), p1=float(K.h[r1]), i2=int(j), p2=level, label="Bibir cangkir")]
    titik = [dict(i=int(bi), p=float(K.l[bi]), label="Dasar cangkir"),
             dict(i=int(j - int(np.argmin(K.l[r2 + 1:j + 1][::-1]))), p=hl, label="Gagang")]
    P = _pola(K, "Cup and Handle", level, "bibir cangkir", level + depth, hl - 0.3 * tol * ref, 0.6, r1,
              garis, titik)
    if _sah(K, P):
        out.append(P)
    return out


def semua_pola(K: Ctx):
    hasil = det_bottoms(K) + det_ihs(K) + det_triangles(K, True) + det_flags(K) + det_cup(K)
    F = K.flip()
    hasil += [_balik(P) for P in det_bottoms(F) + det_ihs(F) + det_triangles(F, False) + det_flags(F)]
    return hasil


def status_teks(P) -> str:
    lv = f"{P['level_nama']} {fmt_price(P['level'])}"
    naik = P["arah"] == "naik"
    if P["status"] == "breakout":
        return ("sudah tembus " if naik else "sudah jebol ") + lv
    if P["status"] == "uji":
        return P.get("uji_teks") or "sedang terbentuk"
    return ("menunggu tembus " if naik else "menunggu jebol ") + lv


# =========================================================================== #
# 9. Elliott Wave (perkiraan otomatis)
# =========================================================================== #
TEKS_ELL = {  # (versi tren naik, versi tren turun)
    "g2": ("Akhir gelombang 2 → potensi gelombang 3 naik",
           "Akhir gelombang 2 (pantulan) → potensi gelombang 3 turun"),
    "g3": ("Gelombang 3 naik sedang berjalan", "Gelombang 3 turun sedang berjalan"),
    "abc": ("Koreksi A-B-C kemungkinan selesai → potensi naik lagi",
            "Pantulan A-B-C kemungkinan selesai → potensi turun lagi"),
    "imp": ("Impuls 5 gelombang naik kemungkinan selesai → potensi koreksi A-B-C",
            "Impuls 5 gelombang turun kemungkinan selesai → potensi pantulan naik"),
    "g5": ("Gelombang 5 naik (fase akhir tren, waspada)", "Gelombang 5 turun (fase akhir tren)"),
}


def _impuls(pts, ref, lengkap=True) -> bool:
    e = 0.005 * ref
    if lengkap:
        p0, p1, p2, p3, p4, p5 = pts
        w5 = p5 - p4
    else:
        p0, p1, p2, p3, p4 = pts
        p5, w5 = None, None
    w1, w3 = p1 - p0, p3 - p2
    ok = w1 > 0 and w3 > 0 and p2 > p0 + e and p4 > p1 + e and p3 > p1
    if lengkap:
        ok = ok and w5 > 0 and p5 > p3 - e and not (w3 < w1 and w3 < w5)
    return ok


def _ell_scan(S, price, ref):
    res = []
    n = len(S)

    def ty(k):
        return "".join(p["t"] for p in S[-k:]) if n >= k else ""

    def pts(a, b=None):
        return [p["p"] for p in S[a:b]]

    def tt(seg, labels):
        return [dict(i=int(p["i"]), p=float(p["p"]), label=lb) for p, lb in zip(seg, labels)]

    # Impuls 5 gelombang selesai, harga mulai berbalik
    if ty(7) == "LHLHLHL" and S[-1]["tent"]:
        q = pts(-7, -1)
        if _impuls(q, ref):
            tgt = q[5] - 0.382 * (q[5] - q[0])
            if price > tgt:
                res.append(("imp", -1, tgt, 5, tt(S[-7:-1], "012345")))
    if ty(6) == "LHLHLH" and S[-1]["tent"]:
        q = pts(-6)
        w1 = q[1] - q[0]
        if _impuls(q, ref) and price >= q[4] + 0.9 * w1:
            tgt = q[5] - 0.382 * (q[5] - q[0])
            res.append(("imp", -1, tgt, 3, tt(S[-6:], "012345")))
        elif _impuls(q[:5], ref, lengkap=False):
            tgt = q[4] + w1
            if price < tgt:
                res.append(("g5", 1, tgt, 2, tt(S[-6:-1], "01234")))
    # Akhir gelombang 2 / awal gelombang 3
    if ty(3) == "LHL" and S[-1]["tent"]:
        p0, p1, p2 = pts(-3)
        w1 = p1 - p0
        if w1 > 0 and p2 > p0 and 0.382 <= (p1 - p2) / w1 <= 0.786 and price <= p2 + 0.3 * (p1 - p2):
            res.append(("g2", 1, p2 + 1.618 * w1, 6, tt(S[-3:], "012")))
    if ty(4) == "LHLH" and S[-1]["tent"]:
        p0, p1, p2 = pts(-4, -1)
        w1 = p1 - p0
        tgt = p2 + 1.618 * w1
        if (w1 > 0 and p2 > p0 and 0.382 <= (p1 - p2) / w1 <= 0.786
                and price <= p1 + 0.618 * w1 and price < tgt):
            res.append(("g3", 1, tgt, 5, tt(S[-4:-1], "012")))
    # Koreksi A-B-C selesai
    for off, bobot in ((0, 5), (1, 4)):
        k = 5 + off
        if n < k:
            continue
        seg = S[-k:len(S) - off] if off else S[-k:]
        if "".join(p["t"] for p in seg) != "LHLHL":
            continue
        if off == 0 and not seg[-1]["tent"]:
            continue
        if off == 1 and not (S[-1]["tent"] and S[-1]["t"] == "H"):
            continue
        xp, x0, A, B, C = [p["p"] for p in seg]
        lenA, lenC = x0 - A, B - C
        if lenA > 0 and A < B < x0 and C < A and 0.618 <= lenC / lenA <= 1.618 and C > xp:
            if (off == 0 and price <= C + 0.3 * (B - C)) or (off == 1 and price <= B):
                res.append(("abc", 1, x0, bobot, tt(seg[2:], "ABC")))
    return res


def elliott(h, l, price, atrp):
    thr = float(np.clip(3.0 * atrp, 0.07, 0.25))
    piv = zigzag(h, l, thr)
    if len(piv) < 3:
        return None
    ref = abs(price)
    cands = []
    for kode, arah, tgt, bobot, titik in _ell_scan(piv, price, ref):
        cands.append((bobot, kode, 1 if arah > 0 else -1, tgt, titik, 0))
    fp = [{"i": p["i"], "p": -p["p"], "t": "L" if p["t"] == "H" else "H", "tent": p["tent"]} for p in piv]
    for kode, arah, tgt, bobot, titik in _ell_scan(fp, -price, ref):
        titik = [dict(t, p=-t["p"]) for t in titik]
        cands.append((bobot, kode, -1 if arah > 0 else 1, -tgt, titik, 1))
    if not cands:
        return None
    bobot, kode, arah, tgt, titik, ori = max(cands, key=lambda x: x[0])
    return dict(kode=kode, teks=TEKS_ELL[kode][ori], arah="naik" if arah > 0 else "turun",
                target=float(tgt), pct=float((tgt / price - 1) * 100), bobot=bobot, titik=titik)


# =========================================================================== #
# 4. Candlestick
# =========================================================================== #
def pola_candle(o, h, l, c, j):
    if j < 8:
        return None

    def part(i):
        body = abs(c[i] - o[i])
        rng = max(h[i] - l[i], 1e-12)
        return body, rng, h[i] - max(o[i], c[i]), min(o[i], c[i]) - l[i]

    hijau = lambda i: c[i] > o[i]  # noqa: E731
    merah = lambda i: c[i] < o[i]  # noqa: E731
    turun = c[j - 1] < c[j - 6]
    naik = c[j - 1] > c[j - 6]
    turun3 = c[j - 3] < c[j - 8]
    naik3 = c[j - 3] > c[j - 8]
    b0, r0, _, _ = part(j - 2)
    b1, r1, _, _ = part(j - 1)
    b2, r2, u2, lo2 = part(j)
    # Pola 3 candle
    if turun3 and merah(j - 2) and b0 >= 0.5 * r0 and b1 <= 0.35 * b0 and hijau(j) and c[j] > (o[j - 2] + c[j - 2]) / 2:
        return dict(nama="Morning Star", arah="naik", bobot=8)
    if naik3 and hijau(j - 2) and b0 >= 0.5 * r0 and b1 <= 0.35 * b0 and merah(j) and c[j] < (o[j - 2] + c[j - 2]) / 2:
        return dict(nama="Evening Star", arah="turun", bobot=8)
    tiga = [j - 2, j - 1, j]
    if all(hijau(i) and part(i)[0] >= 0.5 * part(i)[1] and part(i)[2] <= 0.3 * part(i)[0] for i in tiga) \
            and c[j - 2] < c[j - 1] < c[j] and o[j - 1] <= c[j - 2] and o[j] <= c[j - 1] and not naik3:
        return dict(nama="Three White Soldiers", arah="naik", bobot=8)
    if all(merah(i) and part(i)[0] >= 0.5 * part(i)[1] and part(i)[3] <= 0.3 * part(i)[0] for i in tiga) \
            and c[j - 2] > c[j - 1] > c[j] and o[j - 1] >= c[j - 2] and o[j] >= c[j - 1] and not turun3:
        return dict(nama="Three Black Crows", arah="turun", bobot=8)
    # Pola 2 candle
    if turun and merah(j - 1) and hijau(j) and o[j] <= c[j - 1] * 1.002 and c[j] >= o[j - 1] and b2 > b1:
        return dict(nama="Bullish Engulfing", arah="naik", bobot=7)
    if naik and hijau(j - 1) and merah(j) and o[j] >= c[j - 1] * 0.998 and c[j] <= o[j - 1] and b2 > b1:
        return dict(nama="Bearish Engulfing", arah="turun", bobot=7)
    if turun and merah(j - 1) and b1 >= 0.5 * r1 and hijau(j) and o[j] <= c[j - 1] * 1.001 \
            and (o[j - 1] + c[j - 1]) / 2 < c[j] < o[j - 1]:
        return dict(nama="Piercing Line", arah="naik", bobot=6)
    if naik and hijau(j - 1) and b1 >= 0.5 * r1 and merah(j) and o[j] >= c[j - 1] * 0.999 \
            and o[j - 1] < c[j] < (o[j - 1] + c[j - 1]) / 2:
        return dict(nama="Dark Cloud Cover", arah="turun", bobot=6)
    # Pola 1 candle
    bb = max(b2, 0.05 * r2)
    if lo2 >= 2 * bb and u2 <= 0.15 * r2 and lo2 >= 0.55 * r2:
        if turun:
            return dict(nama="Hammer", arah="naik", bobot=5)
        if naik:
            return dict(nama="Hanging Man", arah="turun", bobot=4)
    if u2 >= 2 * bb and lo2 <= 0.15 * r2 and u2 >= 0.55 * r2:
        if turun:
            return dict(nama="Inverted Hammer", arah="naik", bobot=4)
        if naik:
            return dict(nama="Shooting Star", arah="turun", bobot=5)
    if b2 <= 0.08 * r2:
        return dict(nama="Doji (ragu-ragu)", arah="netral", bobot=0)
    return None


# =========================================================================== #
# 1. Trend line
# =========================================================================== #
def garis_tren(piv, c, price, j):
    S = [p for p in piv if not p["tent"] and p["i"] >= j - 150]
    Hs = [p for p in S if p["t"] == "H"][-2:]
    Ls = [p for p in S if p["t"] == "L"][-2:]
    res = Garis(Hs[0]["i"], Hs[0]["p"], Hs[1]["i"], Hs[1]["p"]) if len(Hs) == 2 else None
    sup = Garis(Ls[0]["i"], Ls[0]["p"], Ls[1]["i"], Ls[1]["p"]) if len(Ls) == 2 else None
    tren = "Sideways"
    if res and sup:
        hh, hl = Hs[1]["p"] > Hs[0]["p"], Ls[1]["p"] > Ls[0]["p"]
        if hh and hl:
            tren = "Naik (higher high & higher low)"
        elif not hh and not hl:
            tren = "Turun (lower high & lower low)"
    sup_now = sup.at(j) if sup and sup.at(j) > 0 else None
    res_now = res.at(j) if res and res.at(j) > 0 else None
    sinyal = []
    if sup_now and sup.m >= 0 and 0 <= price - sup_now <= 0.04 * price:
        sinyal.append(("naik", 5, f"Dekat garis support tren ({fmt_price(sup_now)})"))
    if res_now and res.m < 0 and price > res_now * 1.01 and any(c[i] <= res.at(i) for i in range(max(0, j - 5), j + 1)):
        sinyal.append(("naik", 5, "Tembus garis tren turun (trend line breakout)"))
    if sup_now and price < sup_now * 0.99 and any(c[i] >= sup.at(i) for i in range(max(0, j - 5), j + 1)):
        sinyal.append(("turun", 5, "Jebol garis support tren"))
    if res_now and res.m <= 0 and 0 <= res_now - price <= 0.04 * price:
        sinyal.append(("turun", 5, f"Tertahan garis resistance tren turun ({fmt_price(res_now)})"))
    return dict(tren=tren, sup=sup, res=res, sup_now=sup_now, res_now=res_now, sinyal=sinyal)


def divergensi(piv, r, j):
    Ls = [p for p in piv if p["t"] == "L" and p["i"] >= j - 60][-2:]
    Hs = [p for p in piv if p["t"] == "H" and p["i"] >= j - 60][-2:]
    bull = (len(Ls) == 2 and Ls[1]["i"] >= j - 10 and Ls[1]["p"] < Ls[0]["p"]
            and _ok(r[Ls[0]["i"]], r[Ls[1]["i"]]) and r[Ls[1]["i"]] > r[Ls[0]["i"]] + 2 and r[Ls[0]["i"]] < 45)
    bear = (len(Hs) == 2 and Hs[1]["i"] >= j - 10 and Hs[1]["p"] > Hs[0]["p"]
            and _ok(r[Hs[0]["i"]], r[Hs[1]["i"]]) and r[Hs[1]["i"]] < r[Hs[0]["i"]] - 2 and r[Hs[0]["i"]] > 55)
    return bool(bull), bool(bear)


# =========================================================================== #
# 10. Volume, akumulasi & profil volume
# =========================================================================== #
def volume_profile(h: pd.DataFrame, bins: int = 48):
    """Volume per level harga. POC = level volume terbesar; Value Area = 70% volume
    di sekitar POC = ZONA AKUMULASI (harga tempat paling banyak koin berpindah tangan)."""
    if h.empty:
        return None
    lo, hi = float(h["low"].min()), float(h["high"].max())
    if not np.isfinite(lo) or hi <= lo:
        return None
    edges = np.linspace(lo, hi, bins + 1)
    L = h["low"].to_numpy()[:, None]
    H = h["high"].to_numpy()[:, None]
    V = h["qvol"].to_numpy()[:, None]
    span = H - L
    overlap = np.clip(np.minimum(H, edges[1:][None, :]) - np.maximum(L, edges[:-1][None, :]), 0, None)
    w = np.divide(overlap, span, out=np.zeros_like(overlap), where=span > 0)
    flat = span[:, 0] <= 0
    if flat.any():
        b = np.clip(np.searchsorted(edges, h["close"].to_numpy()[flat], side="right") - 1, 0, bins - 1)
        w[np.where(flat)[0], b] = 1.0
    vol = (w * V).sum(axis=0)
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
    centers = (edges[:-1] + edges[1:]) / 2
    return dict(edges=edges, centers=centers, vol=vol, poc_i=poc_i, va=(lo_i, hi_i),
                poc=float(centers[poc_i]), val=float(edges[lo_i]), vah=float(edges[hi_i + 1]))


def metrik_volume(info, dc: pd.DataFrame, h: pd.DataFrame, hari_profil: int):
    hc = h[h["closed"]].reset_index(drop=True) if h is not None and len(h) else pd.DataFrame()
    out = dict(rvol_d=np.nan, rvol_h=np.nan, buy24=np.nan, buy1h=np.nan, taker_real=False, vp=None)
    avg20 = float(dc["qvol"].tail(20).mean())
    out["rvol_d"] = info["qvol24"] / avg20 if avg20 > 0 else np.nan
    if len(hc) >= 72:
        base_h = float(hc["qvol"].iloc[-50:-2].mean())
        last2 = hc.tail(2)
        row = last2.loc[last2["qvol"].idxmax()]
        out["rvol_h"] = float(row["qvol"]) / base_h if base_h > 0 else np.nan
        out["chg_spike"] = float((row["close"] / row["open"] - 1) * 100)
        if hc["taker_buy_q"].notna().all():
            q24 = hc["qvol"].tail(24).sum()
            out["buy24"] = float(hc["taker_buy_q"].tail(24).sum() / q24) if q24 > 0 else np.nan
            out["buy1h"] = float(row["taker_buy_q"] / row["qvol"]) if row["qvol"] > 0 else np.nan
            out["taker_real"] = True
        else:
            t24 = hc.tail(24)
            out["buy24"] = 0.5 + cmf(t24["high"].to_numpy(), t24["low"].to_numpy(), t24["close"].to_numpy(),
                                     t24["volume"].to_numpy(), 24) / 2
            t2 = hc.tail(2)
            out["buy1h"] = 0.5 + cmf(t2["high"].to_numpy(), t2["low"].to_numpy(), t2["close"].to_numpy(),
                                     t2["volume"].to_numpy(), 2) / 2
        out["vp"] = volume_profile(hc.tail(24 * hari_profil))
    return out


# =========================================================================== #
# Penilaian & klasifikasi
# =========================================================================== #
class Skor:
    BATAS = {"vol": 20, "lokasi": 15, "pola": 25, "momentum": 20, "candle": 8, "tren": 10, "squeeze": 5,
             "elliott": 6}

    def __init__(self):
        self.kat: dict[str, float] = {}
        self.alasan: list[tuple[float, str]] = []

    def add(self, kat, pts, teks):
        cur = self.kat.get(kat, 0)
        add = min(pts, self.BATAS[kat] - cur)
        if add <= 0:
            return
        self.kat[kat] = cur + add
        self.alasan.append((pts, teks))

    @property
    def total(self) -> int:
        return int(round(min(100, sum(self.kat.values()))))

    def daftar(self, n=8):
        return [t for _, t in sorted(self.alasan, key=lambda x: -x[0])[:n]]


def _target_level(price, arah, kandidat, minimal=0.03):
    """Level terdekat di atas (naik) / di bawah (turun) yang jaraknya >= minimal."""
    if arah == "naik":
        c = [(p, n) for p, n in kandidat if p is not None and np.isfinite(p) and p >= price * (1 + minimal)]
        return min(c, key=lambda x: x[0]) if c else None
    c = [(p, n) for p, n in kandidat if p is not None and np.isfinite(p) and 0 < p <= price * (1 - minimal)]
    return max(c, key=lambda x: x[0]) if c else None


def analisa_koin(info: dict, d: pd.DataFrame, h: pd.DataFrame, cfg: dict) -> dict | None:
    dc = d[d["closed"]].reset_index(drop=True)
    if len(dc) < 60:
        return None  # koin terlalu baru
    o, hh, ll, c, v = (dc[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close", "volume"))
    price = float(info["price"])
    j = len(c) - 1
    A = atr(hh, ll, c)
    atrp = float(A[j] / c[j]) if _ok(A[j]) and c[j] > 0 else 0.04
    ma20, ma50, ma200 = sma(c, 20), sma(c, 50), sma(c, 200)
    r = rsi(c)
    m_line, m_sig, m_hist = macd(c)
    sk, sd = stochastic(hh, ll, c)
    bb_mid, bb_up, bb_lo, pctb, bw = bollinger(c)

    piv = zigzag(hh, ll, float(np.clip(1.6 * atrp, 0.04, 0.14)))
    K = Ctx(o, hh, ll, c, v, price, piv, atrp)
    pola = semua_pola(K)
    for P in pola:
        P["target_pct"] = (P["target"] / price - 1) * 100
        P["batal_pct"] = (P["batal"] / price - 1) * 100
    pola_naik = max((P for P in pola if P["arah"] == "naik"), key=lambda P: P["kekuatan"], default=None)
    pola_turun = max((P for P in pola if P["arah"] == "turun"), key=lambda P: P["kekuatan"], default=None)

    ell = elliott(hh, ll, price, atrp)
    tl = garis_tren(piv, c, price, j)
    cdl = pola_candle(o, hh, ll, c, j)
    div_bull, div_bear = divergensi(piv, r, j)
    vm = metrik_volume(info, dc, h, int(cfg.get("profil_volume_hari", 30)))
    vp = vm["vp"]

    cmf20 = cmf(hh, ll, c, v, 20)
    ob = obv(c, v)
    y = ob[-20:]
    vavg = float(np.mean(v[-20:]))
    obv_trend = float(np.polyfit(np.arange(len(y)), y, 1)[0] / vavg) if vavg > 0 else np.nan
    chg7 = (price / c[-7] - 1) * 100 if len(c) >= 7 else np.nan
    chg20 = (price / c[-21] - 1) * 100 if len(c) >= 21 else np.nan
    chg30 = (price / c[-31] - 1) * 100 if len(c) >= 31 else np.nan

    B, S = Skor(), Skor()  # B = potensi naik, S = potensi turun

    # --- Akumulasi / distribusi volume ---
    buy24, buy1h, rvol_d, rvol_h = vm["buy24"], vm["buy1h"], vm["rvol_d"], vm["rvol_h"]
    if _ok(obv_trend) and obv_trend >= 0.3:
        B.add("vol", 7, "OBV naik → koin sedang dikumpulkan")
    if _ok(obv_trend) and obv_trend <= -0.3:
        S.add("vol", 7, "OBV turun → koin sedang dilepas (distribusi)")
    if _ok(cmf20) and cmf20 >= 0.05:
        B.add("vol", 6, f"CMF {fmt_dec(cmf20)} → uang masuk")
    if _ok(cmf20) and cmf20 <= -0.05:
        S.add("vol", 6, f"CMF {fmt_dec(cmf20)} → uang keluar")
    if _ok(buy24) and buy24 >= 0.55:
        B.add("vol", 4, f"Beli agresif 24 jam {fmt_pct(buy24 * 100, False)}")
    if _ok(buy24) and buy24 <= 0.45:
        S.add("vol", 4, f"Jual agresif 24 jam {fmt_pct((1 - buy24) * 100, False)}")
    if _ok(obv_trend, chg20) and obv_trend >= 0.2 and chg20 <= 3:
        B.add("vol", 5, "OBV naik saat harga datar/turun → akumulasi diam-diam")
    if _ok(obv_trend, chg20) and obv_trend <= -0.2 and chg20 >= -3:
        S.add("vol", 5, "OBV turun saat harga datar/naik → distribusi diam-diam")
    if _ok(rvol_h, buy1h) and rvol_h >= 4 and buy1h >= 0.58:
        B.add("vol", 4, f"Lonjakan volume 1 jam {fmt_x(rvol_h)}, dominan beli (jejak whale)")
    if _ok(rvol_h, buy1h) and rvol_h >= 4 and buy1h <= 0.42:
        S.add("vol", 4, f"Lonjakan volume 1 jam {fmt_x(rvol_h)}, dominan jual")
    if _ok(rvol_d, buy24) and rvol_d >= 2 and buy24 >= 0.52:
        B.add("vol", 3, f"Volume 24 jam {fmt_x(rvol_d)} rata-rata")
    if _ok(rvol_d, buy24) and rvol_d >= 2 and buy24 <= 0.48:
        S.add("vol", 3, f"Volume jual 24 jam {fmt_x(rvol_d)} rata-rata")

    # --- Lokasi harga ---
    posisi = "-"
    if vp:
        posisi = "bawah" if price < vp["val"] else ("atas" if price > vp["vah"] else
                                                   ("dalam-bawah" if price <= vp["poc"] else "dalam-atas"))
        if price <= vp["poc"] * 1.01:
            B.add("lokasi", 8, f"Harga di bawah/dekat POC zona akumulasi ({fmt_price(vp['poc'])})")
        elif price <= vp["vah"]:
            B.add("lokasi", 4, "Harga masih di dalam zona akumulasi")
        if price > vp["vah"] * 1.02:
            S.add("lokasi", 6, "Harga sudah di atas zona akumulasi (rawan ambil untung)")
    if _ok(pctb[j]) and pctb[j] <= 0.2:
        B.add("lokasi", 4, "Dekat Bollinger Band bawah")
    if _ok(pctb[j]) and pctb[j] >= 0.9:
        S.add("lokasi", 4, "Dekat Bollinger Band atas")
    if _ok(ma200[j]) and 0 <= price / ma200[j] - 1 <= 0.04:
        B.add("lokasi", 4, "Bertahan tepat di atas MA200")
    elif _ok(ma50[j]) and 0 <= price / ma50[j] - 1 <= 0.03:
        B.add("lokasi", 3, "Bertahan tepat di atas MA50")
    if _ok(ma50[j]) and price / ma50[j] - 1 >= 0.25:
        S.add("lokasi", 4, f"Terlalu jauh di atas MA50 ({fmt_pct((price / ma50[j] - 1) * 100)})")
    if _ok(r[j]) and r[j] <= 40:
        B.add("lokasi", 3, f"RSI rendah ({r[j]:.0f})")
    if _ok(r[j]) and r[j] >= 65:
        S.add("lokasi", 3, f"RSI tinggi ({r[j]:.0f})")
    for arah, pts, teks in tl["sinyal"]:
        (B if arah == "naik" else S).add("lokasi" if "Dekat" in teks or "Tertahan" in teks else "tren", pts, teks)

    # --- Chart pattern ---
    if pola_naik:
        B.add("pola", round(25 * pola_naik["kekuatan"]), f"Pola {pola_naik['nama']} ({status_teks(pola_naik)})")
    if pola_turun:
        S.add("pola", round(25 * pola_turun["kekuatan"]), f"Pola {pola_turun['nama']} ({status_teks(pola_turun)})")

    # --- Momentum: MACD, RSI, Stochastic ---
    if _cross_up(m_line, m_sig, j):
        B.add("momentum", 9 if m_line[j] < 0 else 7,
              "MACD cross naik" + (" di bawah nol (awal pembalikan)" if m_line[j] < 0 else ""))
    if _cross_down(m_line, m_sig, j):
        S.add("momentum", 9 if m_line[j] > 0 else 7,
              "MACD cross turun" + (" di atas nol (awal pembalikan)" if m_line[j] > 0 else ""))
    if _ok(m_hist[j], m_hist[j - 3]) and m_hist[j] < 0 and m_hist[j] > m_hist[j - 1] > m_hist[j - 2] > m_hist[j - 3]:
        B.add("momentum", 3, "Histogram MACD menguat (tekanan jual melemah)")
    if _ok(m_hist[j], m_hist[j - 3]) and m_hist[j] > 0 and m_hist[j] < m_hist[j - 1] < m_hist[j - 2] < m_hist[j - 3]:
        S.add("momentum", 3, "Histogram MACD melemah (tekanan beli memudar)")
    if _cross_up(sk, sd, j) and np.nanmin(sk[j - 3:j + 1]) < 25:
        B.add("momentum", 6, f"Stochastic cross naik dari oversold ({sk[j]:.0f})")
    if _cross_down(sk, sd, j) and np.nanmax(sk[j - 3:j + 1]) > 75:
        S.add("momentum", 6, f"Stochastic cross turun dari overbought ({sk[j]:.0f})")
    if _ok(r[j]) and r[j] < 30:
        B.add("momentum", 5, f"RSI oversold ({r[j]:.0f})")
    if _ok(r[j]) and r[j] > 70:
        S.add("momentum", 5, f"RSI overbought ({r[j]:.0f})")
    if div_bull:
        B.add("momentum", 8, "Divergensi naik RSI (harga lower low, RSI higher low)")
    if div_bear:
        S.add("momentum", 8, "Divergensi turun RSI (harga higher high, RSI lower high)")

    # --- Candlestick ---
    if cdl and cdl["arah"] == "naik":
        B.add("candle", cdl["bobot"], f"Candle {cdl['nama']}")
    if cdl and cdl["arah"] == "turun":
        S.add("candle", cdl["bobot"], f"Candle {cdl['nama']}")

    # --- Tren & Moving Average ---
    if _cross_up(ma50, ma200, j, 15):
        B.add("tren", 5, "Golden cross (MA50 memotong ke atas MA200)")
    if _cross_down(ma50, ma200, j, 15):
        S.add("tren", 5, "Death cross (MA50 memotong ke bawah MA200)")
    if _ok(ma200[j]):
        if price > ma200[j]:
            B.add("tren", 2, "Di atas MA200 (tren besar naik)")
        else:
            S.add("tren", 3, "Di bawah MA200 (tren besar turun)")
    if _ok(ma20[j], ma50[j], ma200[j]):
        if ma20[j] > ma50[j] > ma200[j]:
            B.add("tren", 3, "MA20 > MA50 > MA200")
        elif ma20[j] < ma50[j] < ma200[j]:
            S.add("tren", 3, "MA20 < MA50 < MA200")
    if _cross_up(c, ma20, j):
        B.add("tren", 2, "Harga kembali di atas MA20")
    if _cross_down(c, ma20, j):
        S.add("tren", 2, "Harga turun ke bawah MA20")

    # --- Bollinger squeeze ---
    squeeze = False
    if _ok(bw[j]) and j >= 60:
        lo_bw = np.nanmin(bw[max(0, j - 120):j + 1])
        squeeze = bool(bw[j] <= 1.1 * lo_bw)
    if squeeze:
        teks = "Bollinger menyempit (squeeze) → siap bergerak besar"
        if B.kat.get("vol", 0) >= S.kat.get("vol", 0):
            B.add("squeeze", 5, teks)
        else:
            S.add("squeeze", 5, teks)

    # --- Elliott ---
    if ell:
        (B if ell["arah"] == "naik" else S).add("elliott", ell["bobot"], f"Elliott: {ell['teks']}")

    # --- Klasifikasi ---
    skor_min = cfg.get("skor_min", 55)
    selisih = cfg.get("selisih_min", 15)
    lok_bawah = (vp is None or price <= vp["vah"] * 1.03) and (not _ok(chg7) or chg7 < cfg.get("maks_naik_7h_persen", 20))
    akum_ok = B.kat.get("vol", 0) >= 6 or not cfg.get("syarat_akumulasi", True)
    kelas = "netral"
    pantau = cfg.get("skor_pantau", 40)
    if B.total >= skor_min and B.total - S.total >= selisih and lok_bawah and akum_ok:
        kelas = "naik"
    elif S.total >= skor_min and S.total - B.total >= selisih:
        kelas = "turun"
    elif B.total >= pantau and B.total - S.total >= 10 and lok_bawah:
        kelas = "pantau-naik"   # hampir memenuhi syarat (hanya di dashboard)
    elif S.total >= pantau and S.total - B.total >= 10:
        kelas = "pantau-turun"

    # --- Target & batas batal ---
    hi30, lo20 = float(np.max(hh[-30:])), float(np.min(ll[-20:]))
    res_kand = [(tl["res_now"], "garis resistance tren"), (bb_up[j], "Bollinger atas"), (hi30, "high 30 hari"),
                (ma50[j], "MA50"), (ma200[j], "MA200")]
    sup_kand = [(tl["sup_now"], "garis support tren"), (bb_lo[j], "Bollinger bawah"), (lo20, "low 20 hari"),
                (ma50[j], "MA50"), (ma200[j], "MA200")]
    if vp:
        res_kand.append((vp["vah"], "batas atas zona akumulasi"))
        sup_kand.append((vp["val"], "batas bawah zona akumulasi"))
    target = batal = None
    arah_k = kelas.replace("pantau-", "") if kelas != "netral" else ("naik" if B.total >= S.total else "turun")
    Pk = pola_naik if arah_k == "naik" else pola_turun
    if Pk:
        target = dict(harga=Pk["target"], sumber=f"target pola {Pk['nama']}")
        batal = dict(harga=Pk["batal"], sumber=f"batal pola {Pk['nama']}")
    elif ell and ell["arah"] == arah_k and abs(ell["pct"]) >= 3:
        target = dict(harga=ell["target"], sumber="target Elliott Wave")
    if target is None:
        t = _target_level(price, arah_k, res_kand if arah_k == "naik" else sup_kand)
        if t:
            target = dict(harga=t[0], sumber=t[1])
    if batal is None:
        b = _target_level(price, "turun" if arah_k == "naik" else "naik",
                          sup_kand if arah_k == "naik" else res_kand, 0.02)
        if b:
            batal = dict(harga=b[0] * (0.99 if arah_k == "naik" else 1.01), sumber=b[1])
    for x in (target, batal):
        if x:
            x["pct"] = (x["harga"] / price - 1) * 100
    rr = abs(target["pct"] / batal["pct"]) if target and batal and batal["pct"] else None

    def _pola_json(P):
        if not P:
            return None
        return dict(nama=P["nama"], arah=P["arah"], status=P["status"], status_teks=status_teks(P),
                    level=_r(P["level"]), target=_r(P["target"]), target_pct=_f(P["target_pct"], 1),
                    batal=_r(P["batal"]), batal_pct=_f(P["batal_pct"], 1), arti=ARTI_POLA.get(P["nama"], ""))

    hasil = dict(
        symbol=info["symbol"], base=info["base"], nama=info.get("name", info["base"]), rank=info.get("rank"),
        bursa=info.get("bursa", ""), price=_r(price), chg24=_f(info.get("chg24"), 2), chg7=_f(chg7, 2),
        chg30=_f(chg30, 2), qvol24=_f(info.get("qvol24"), 0), kelas=kelas, arah_utama=arah_k,
        skor_naik=B.total, skor_turun=S.total, alasan_naik=B.daftar(), alasan_turun=S.daftar(),
        pola_naik=_pola_json(pola_naik), pola_turun=_pola_json(pola_turun),
        target=dict(harga=_r(target["harga"]), pct=_f(target["pct"], 1), sumber=target["sumber"]) if target else None,
        batal=dict(harga=_r(batal["harga"]), pct=_f(batal["pct"], 1), sumber=batal["sumber"]) if batal else None,
        rr=_f(rr, 2),
        elliott=dict(teks=ell["teks"], arah=ell["arah"], target=_r(ell["target"]), pct=_f(ell["pct"], 1)) if ell else None,
        candle=cdl["nama"] if cdl else None,
        indikator=dict(
            rsi=_f(r[j], 1), stoch_k=_f(sk[j], 1), stoch_d=_f(sd[j], 1), macd=_f(m_line[j], 8),
            macd_sinyal=_f(m_sig[j], 8), macd_hist=_f(m_hist[j], 8),
            macd_status=("cross naik" if _cross_up(m_line, m_sig, j) else "cross turun" if _cross_down(m_line, m_sig, j)
                         else ("di atas sinyal" if _ok(m_hist[j]) and m_hist[j] > 0 else "di bawah sinyal")),
            bb_pctb=_f(pctb[j], 2), bb_squeeze=squeeze, ma20=_r(ma20[j]), ma50=_r(ma50[j]), ma200=_r(ma200[j]),
            tren=tl["tren"], support=_r(tl["sup_now"]), resistance=_r(tl["res_now"]), atr_pct=_f(atrp * 100, 2),
            div_rsi="naik" if div_bull else ("turun" if div_bear else None),
        ),
        akumulasi=dict(obv_trend=_f(obv_trend, 2), cmf=_f(cmf20, 3), beli24=_f(buy24, 3), rvol_d=_f(rvol_d, 2),
                       rvol_h=_f(rvol_h, 2), posisi=posisi,
                       zona=dict(val=_r(vp["val"]), poc=_r(vp["poc"]), vah=_r(vp["vah"])) if vp else None),
    )
    hasil["_g"] = dict(dc=dc, ma20=ma20, ma50=ma50, ma200=ma200, bb_up=bb_up, bb_lo=bb_lo, bb_mid=bb_mid,
                       rsi=r, macd=m_line, macd_sig=m_sig, macd_hist=m_hist, sk=sk, sd=sd, tl=tl, vp=vp,
                       pola=pola_naik if arah_k == "naik" else pola_turun, ell=ell, target=target, batal=batal,
                       obv=ob)
    return hasil
