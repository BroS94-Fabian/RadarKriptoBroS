#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RADAR WHALE KRIPTO
==================
Memindai semua pasangan USDT di bursa lalu mencari koin yang:
  1. Volume 24 jamnya melonjak dibanding rata-rata 20 hari     -> Lonjakan volume
  2. Volume 1-2 jam terakhir meledak + dominasi beli agresif    -> Jejak whale masuk
  3. OBV & CMF naik saat harga masih datar                      -> Akumulasi diam-diam
  4. Harga menembus zona akumulasi (profil volume) & high 20 hr -> Breakout
Hasilnya dikirim ke Telegram lengkap dengan grafik.

Cara jalan:
  python scanner.py                      # mode normal (dipakai GitHub Actions tiap jam)
  python scanner.py --mode demo          # uji dengan data simulasi (tanpa internet)
  python scanner.py --mode tes-telegram  # cek apakah bot Telegram sudah tersambung

BUKAN NASIHAT INVESTASI. Sinyal volume hanya petunjuk, bukan jaminan harga naik.
"""
from __future__ import annotations

import argparse
import html
import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import requests  # noqa: E402
import yaml  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(ROOT, "state.json")
OUT_DIR = os.path.join(ROOT, "out")
WIB = timezone(timedelta(hours=7))
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

# --------------------------------------------------------------------------- #
# Konfigurasi
# --------------------------------------------------------------------------- #
DEFAULT_CONFIG = {
    "sumber_data": "binance",
    "quote": "USDT",
    "min_volume_24j_usd": 2_000_000,
    "maks_koin_dipindai": 250,
    "pantau_khusus": [],
    "abaikan": ["USDC", "FDUSD", "TUSD", "USDP", "DAI", "BUSD", "EUR", "EURI", "AEUR",
                "USDE", "PYUSD", "USD1", "XUSD", "BFUSD", "RLUSD", "USDS", "PAXG",
                "XAUT", "WBTC", "WBETH", "BNSOL"],
    "ambang": {
        "rvol_harian": 3.0,
        "rvol_jam": 4.0,
        "beli_agresif": 0.58,
        "cmf_akumulasi": 0.05,
        "obv_naik": 0.30,
        "sideways_maks_persen": 12,
        "pump_24j_rawan_persen": 40,
        "skor_min_alert": 45,
    },
    "cooldown_jam": 12,
    "maks_grafik_per_run": 5,
    "profil_volume_hari": 30,
    "ringkasan_harian_jam_wib": 8,
}


def deep_merge(base: dict, extra: dict) -> dict:
    out = deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config() -> dict:
    path = os.path.join(ROOT, "config.yaml")
    user = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            user = yaml.safe_load(f) or {}
    cfg = deep_merge(DEFAULT_CONFIG, user)
    cfg["quote"] = str(cfg["quote"]).upper()
    cfg["abaikan"] = {str(x).upper() for x in (cfg.get("abaikan") or [])}
    cfg["pantau_khusus"] = {str(x).upper() for x in (cfg.get("pantau_khusus") or [])}
    return cfg


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
class BlockedError(Exception):
    """Bursa menolak akses dari lokasi server (HTTP 403/451)."""


class SourceError(Exception):
    pass


SESSION = requests.Session()
SESSION.headers["User-Agent"] = "crypto-whale-radar/1.0"


def http_get(url: str, params: dict | None = None, retries: int = 3, timeout: int = 20):
    last: Exception | None = None
    for i in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
            if r.status_code in (403, 451):
                raise BlockedError(f"HTTP {r.status_code} dari {url}")
            if r.status_code == 429 or r.status_code >= 500:
                last = RuntimeError(f"HTTP {r.status_code} dari {url}")
                time.sleep(2 * (i + 1))
                continue
            if r.status_code >= 400:  # permintaan salah: tidak ada gunanya diulang
                raise SourceError(f"HTTP {r.status_code} dari {url}: {r.text[:150]}")
            return r.json()
        except (BlockedError, SourceError):
            raise
        except (requests.RequestException, ValueError) as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last if last else RuntimeError(f"Gagal mengambil {url}")


# --------------------------------------------------------------------------- #
# Sumber data
# --------------------------------------------------------------------------- #
class Binance:
    name = "Binance"
    workers = 8
    # data-api.binance.vision = mirror publik khusus data pasar, tetap bisa
    # diakses dari server GitHub (AS) yang diblokir oleh api.binance.com.
    HOSTS = ["https://data-api.binance.vision", "https://api.binance.com",
             "https://api-gcp.binance.com", "https://api1.binance.com"]

    def __init__(self):
        self.base: str | None = None

    def _get(self, path: str, params: dict | None = None):
        hosts = [self.base] if self.base else self.HOSTS
        err: Exception | None = None
        for host in hosts:
            try:
                data = http_get(host + path, params)
                self.base = host
                return data
            except Exception as e:  # coba host berikutnya
                err = e
        raise SourceError(f"Binance tidak bisa diakses ({err})")

    def universe(self, quote: str) -> list[dict]:
        trading: dict[str, str] | None = None
        try:
            info = self._get("/api/v3/exchangeInfo", {"permissions": "SPOT"})
            trading = {s["symbol"]: s["baseAsset"] for s in info.get("symbols", [])
                       if s.get("status") == "TRADING" and s.get("quoteAsset") == quote}
        except SourceError:
            trading = None  # tetap lanjut, filter pakai akhiran simbol
        rows = self._get("/api/v3/ticker/24hr")
        out = []
        for t in rows:
            sym = t.get("symbol", "")
            if trading is not None:
                if sym not in trading:
                    continue
                base = trading[sym]
            else:
                if not sym.endswith(quote):
                    continue
                base = sym[: -len(quote)]
            if int(t.get("count", 0) or 0) == 0:
                continue
            out.append(dict(symbol=sym, base=base, price=float(t["lastPrice"]),
                            chg24=float(t["priceChangePercent"]), qvol24=float(t["quoteVolume"])))
        return out

    def candles(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        rows = self._get("/api/v3/klines", {"symbol": symbol, "interval": interval,
                                             "limit": int(min(limit, 1000))})
        now_ms = int(time.time() * 1000)
        df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v", "ct", "qv", "n",
                                         "tbv", "tbqv", "x"])
        return pd.DataFrame({
            "time": pd.to_datetime(df["t"].astype("int64"), unit="ms", utc=True),
            "open": df["o"].astype(float), "high": df["h"].astype(float),
            "low": df["l"].astype(float), "close": df["c"].astype(float),
            "volume": df["v"].astype(float), "qvol": df["qv"].astype(float),
            "taker_buy_q": df["tbqv"].astype(float),
            "closed": df["ct"].astype("int64") < now_ms,
        })

    def chart_link(self, m: dict) -> str:
        return f"https://www.tradingview.com/chart/?symbol=BINANCE:{m['symbol']}"


class OKX:
    """Cadangan jika Binance tidak bisa diakses. OKX tidak memberi data
    'beli agresif' per candle, jadi dipakai pendekatan dari CMF per jam."""
    name = "OKX"
    workers = 4
    BASE = "https://www.okx.com"

    def _get(self, path: str, params: dict | None = None):
        d = http_get(self.BASE + path, params)
        if str(d.get("code")) != "0":
            raise SourceError(f"OKX error: {d.get('msg')}")
        return d["data"]

    def universe(self, quote: str) -> list[dict]:
        out = []
        for t in self._get("/api/v5/market/tickers", {"instType": "SPOT"}):
            inst = t.get("instId", "")
            if "-" not in inst:
                continue
            base, q = inst.split("-", 1)
            if q != quote:
                continue
            last = float(t.get("last") or 0)
            open24 = float(t.get("open24h") or 0)
            out.append(dict(symbol=inst, base=base, price=last,
                            chg24=(last / open24 - 1) * 100 if open24 else 0.0,
                            qvol24=float(t.get("volCcy24h") or 0)))
        return out

    def candles(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        bar = {"1d": "1Dutc", "1h": "1H"}[interval]
        rows: list = []
        after = None
        for _ in range(12):
            if not rows:
                path, params = "/api/v5/market/candles", {"instId": symbol, "bar": bar, "limit": 300}
            else:
                path, params = "/api/v5/market/history-candles", {"instId": symbol, "bar": bar,
                                                                  "limit": 100, "after": after}
            batch = self._get(path, params)
            if not batch:
                break
            rows.extend(batch)
            after = batch[-1][0]
            if len(rows) >= limit:
                break
            time.sleep(0.12)
        rows = rows[:limit][::-1]  # OKX: terbaru dulu -> dibalik
        df = pd.DataFrame(rows).iloc[:, :9]
        df.columns = ["t", "o", "h", "l", "c", "v", "vccy", "vq", "confirm"]
        return pd.DataFrame({
            "time": pd.to_datetime(df["t"].astype("int64"), unit="ms", utc=True),
            "open": df["o"].astype(float), "high": df["h"].astype(float),
            "low": df["l"].astype(float), "close": df["c"].astype(float),
            "volume": df["v"].astype(float), "qvol": df["vq"].astype(float),
            "taker_buy_q": np.nan, "closed": df["confirm"].astype(str) == "1",
        })

    def chart_link(self, m: dict) -> str:
        return f"https://www.tradingview.com/chart/?symbol=OKX:{m['base']}{m['symbol'].split('-')[1]}"


class DemoSource:
    """Data simulasi untuk uji coba: 5 koin dengan pola berbeda."""
    name = "DEMO (data simulasi)"
    workers = 1

    def __init__(self):
        rng = np.random.default_rng(42)
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        hours = 24 * 90
        idx = pd.date_range(end=now - timedelta(hours=1), periods=hours, freq="h", tz="UTC")
        specs = {"WHALEUSDT": (0.85, "whale"), "AKUMUSDT": (2.4, "akum"),
                 "BREAKUSDT": (14.0, "break"), "DUMPUSDT": (0.12, "dump"),
                 "TENANGUSDT": (45.0, "normal")}
        self.data: dict[str, dict] = {}
        for sym, (p0, kind) in specs.items():
            ret = rng.normal(0, 0.006, hours)
            vol = rng.lognormal(np.log(220_000), 0.35, hours)
            taker = np.clip(rng.normal(0.5, 0.03, hours), 0.3, 0.7)
            wick_lo = np.abs(rng.normal(0, 0.003, hours))
            wick_hi = np.abs(rng.normal(0, 0.003, hours))
            if kind == "whale":
                ret[-30:] += 0.003
                vol[-30:] *= np.linspace(2.0, 5.0, 30)
                vol[-2:] *= 3.0
                taker[-30:] = np.clip(rng.normal(0.66, 0.03, 30), 0.5, 0.8)
            elif kind == "akum":
                k = 24 * 21
                taker[-k:] = np.clip(rng.normal(0.56, 0.03, k), 0.4, 0.7)
                wick_lo[-k:] *= 2.5  # ekor bawah panjang = pembeli menyerap
            elif kind == "break":
                ret[-24 * 30:-24] = rng.normal(0, 0.004, 24 * 29)
                ret[-24:] += 0.0065
                vol[-24:] *= 3.8
                taker[-24:] = np.clip(rng.normal(0.63, 0.03, 24), 0.5, 0.8)
            elif kind == "dump":
                ret[-24:] -= 0.008
                vol[-24:] *= 4.2
                taker[-24:] = np.clip(rng.normal(0.38, 0.03, 24), 0.2, 0.5)
            close = p0 * np.exp(np.cumsum(ret))
            if kind == "akum":  # harga naik-turun di kisaran datar, volume besar saat naik
                k = 24 * 21
                t = np.arange(k)
                wave = 0.045 * np.sin(2 * np.pi * t / (24 * 4))
                close[-k:] = close[-k - 1] * np.exp(wave + rng.normal(0, 0.003, k))
                rising = np.gradient(wave) > 0
                vol[-k:] *= np.where(rising, 2.4, 0.8)
            opn = np.concatenate([[close[0]], close[:-1]])
            high = np.maximum(opn, close) * (1 + wick_hi)
            low = np.minimum(opn, close) * (1 - wick_lo)
            h = pd.DataFrame({"time": idx, "open": opn, "high": high, "low": low, "close": close,
                              "qvol": vol, "taker_buy_q": vol * taker})
            h["volume"] = h["qvol"] / h["close"]
            h["closed"] = True
            d = (h.set_index("time")
                 .resample("1D")
                 .agg({"open": "first", "high": "max", "low": "min", "close": "last",
                       "volume": "sum", "qvol": "sum", "taker_buy_q": "sum"})
                 .reset_index())
            d["closed"] = d["time"] + timedelta(days=1) <= now
            self.data[sym] = dict(h=h, d=d, base=sym[:-4], price=float(close[-1]),
                                  chg24=float((close[-1] / close[-25] - 1) * 100),
                                  qvol24=float(vol[-24:].sum()))

    def universe(self, quote: str) -> list[dict]:
        return [dict(symbol=s, base=v["base"], price=v["price"], chg24=v["chg24"],
                     qvol24=v["qvol24"]) for s, v in self.data.items()]

    def candles(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        key = "d" if interval == "1d" else "h"
        return self.data[symbol][key].tail(limit).reset_index(drop=True)

    def chart_link(self, m: dict) -> str:
        return ""


# --------------------------------------------------------------------------- #
# Indikator
# --------------------------------------------------------------------------- #
def cmf(df: pd.DataFrame, n: int) -> float:
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    mfm = (((df["close"] - df["low"]) - (df["high"] - df["close"])) / rng).fillna(0)
    tail = df.tail(n)
    v = tail["volume"].sum()
    return float((mfm.loc[tail.index] * tail["volume"]).sum() / v) if v > 0 else np.nan


def obv_series(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff().fillna(0))
    return (direction * df["volume"]).cumsum()


def volume_profile(h: pd.DataFrame, bins: int = 48) -> dict | None:
    """Sebar volume tiap candle 1 jam ke rentang harganya -> volume per level harga.
    POC = level dengan volume terbesar; Value Area = 70% volume di sekitar POC
    (inilah 'zona akumulasi': harga tempat paling banyak koin berpindah tangan)."""
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


def clip01(x: float) -> float:
    return float(min(1.0, max(0.0, x))) if np.isfinite(x) else 0.0


SIGNAL_LABEL = {
    "WHALE": ("⚡", "Whale masuk (1 jam)"),
    "VOL": ("🐋", "Lonjakan volume harian"),
    "BREAK": ("🚀", "Breakout zona akumulasi"),
    "AKUM": ("🧲", "Akumulasi diam-diam"),
    "JUAL": ("🔻", "Tekanan jual besar"),
}


def analyze(info: dict, d: pd.DataFrame, h: pd.DataFrame, cfg: dict) -> dict | None:
    th = cfg["ambang"]
    dc = d[d["closed"]].reset_index(drop=True)
    hc = h[h["closed"]].reset_index(drop=True)
    if len(dc) < 25 or len(hc) < 72:
        return None  # koin baru listing: belum ada pembanding
    price = info["price"]

    # 1) Volume harian relatif (RVOL)
    avg20 = float(dc["qvol"].tail(20).mean())
    rvol_d = info["qvol24"] / avg20 if avg20 > 0 else np.nan

    # 2) Ledakan volume per jam (2 jam terakhir vs 48 jam sebelumnya)
    base_h = float(hc["qvol"].iloc[-50:-2].mean())
    last2 = hc.tail(2)
    spike_row = last2.loc[last2["qvol"].idxmax()]
    rvol_h = float(spike_row["qvol"]) / base_h if base_h > 0 else np.nan
    chg_spike = (spike_row["close"] / spike_row["open"] - 1) * 100

    # 3) Dominasi beli agresif (taker buy). OKX: didekati dari CMF 24 jam.
    has_taker = bool(hc["taker_buy_q"].notna().all())
    if has_taker:
        q24 = hc["qvol"].tail(24).sum()
        buy24 = float(hc["taker_buy_q"].tail(24).sum() / q24) if q24 > 0 else np.nan
        buy1h = float(spike_row["taker_buy_q"] / spike_row["qvol"]) if spike_row["qvol"] > 0 else np.nan
    else:
        buy24 = 0.5 + cmf(hc, 24) / 2
        buy1h = 0.5 + cmf(hc.tail(2), 2) / 2

    # 4) CMF & OBV harian
    cmf20 = cmf(dc, 20)
    obv = obv_series(dc)
    y = obv.tail(20).to_numpy()
    slope = np.polyfit(np.arange(len(y)), y, 1)[0]
    vavg = dc["volume"].tail(20).mean()
    obv_trend = float(slope / vavg) if vavg > 0 else np.nan
    o20 = obv.tail(20)
    o_rng = float(o20.max() - o20.min())
    obv_high = bool((obv.iloc[-1] - o20.min()) / o_rng >= 0.7) if o_rng > 0 else False

    chg20 = (price / dc["close"].iloc[-21] - 1) * 100
    chg7 = (price / dc["close"].iloc[-7] - 1) * 100
    hi20 = float(dc["high"].tail(20).max())

    # 5) Profil volume -> zona akumulasi
    vp = volume_profile(hc.tail(24 * int(cfg["profil_volume_hari"])))
    if vp:
        pos = "atas" if price > vp["vah"] else ("bawah" if price < vp["val"] else "dalam")
        dist_poc = (price / vp["poc"] - 1) * 100
    else:
        pos, dist_poc = "-", np.nan

    # ---- Sinyal ----
    sig: list[str] = []
    if rvol_h >= th["rvol_jam"] and (not np.isfinite(buy1h) or buy1h >= th["beli_agresif"]) and chg_spike > -1:
        sig.append("WHALE")
    if rvol_d >= th["rvol_harian"] and buy24 >= 0.5:
        sig.append("VOL")
    if vp and price > vp["vah"] and price > hi20 and rvol_d >= 1.5:
        sig.append("BREAK")
    if (obv_trend >= th["obv_naik"] and obv_high and cmf20 >= th["cmf_akumulasi"]
            and abs(chg20) <= th["sideways_maks_persen"]):
        sig.append("AKUM")
    if rvol_d >= 2 and buy24 <= 0.45 and info["chg24"] < 0:
        sig.append("JUAL")

    # ---- Skor 0-100 ----
    s = 25 * clip01((rvol_d - 1) / (th["rvol_harian"] * 1.5 - 1))
    s += 20 * clip01((rvol_h - 1) / (th["rvol_jam"] * 1.5 - 1))
    s += 15 * clip01((buy24 - 0.5) / 0.15)
    s += 15 * clip01(cmf20 / 0.20)
    s += 15 * clip01(obv_trend / 0.8)
    if vp:
        s += 10 if pos == "atas" else (5 if price >= vp["poc"] else 0)
    s += 10 * min(2, len([x for x in sig if x != "JUAL"]))
    warn = []
    if info["chg24"] >= th["pump_24j_rawan_persen"]:
        s -= 15
        warn.append(f"Sudah naik {fmt_pct(info['chg24'])} dalam 24 jam — rawan FOMO/pump & dump")
    if buy24 < 0.45:
        s -= 15
    if "JUAL" in sig:
        warn.append("Volume besar tapi didominasi JUAL — bisa jadi whale keluar (distribusi)")
    score = int(round(max(0.0, min(100.0, s))))

    return dict(symbol=info["symbol"], base=info["base"], price=price, chg24=info["chg24"],
                chg7=chg7, chg20=chg20, qvol24=info["qvol24"], avg20=avg20, rvol_d=rvol_d,
                rvol_h=rvol_h, chg_spike=chg_spike, buy24=buy24, buy1h=buy1h,
                taker_real=has_taker, cmf20=cmf20, obv_trend=obv_trend, vp=vp, pos=pos,
                dist_poc=dist_poc, signals=sig, score=score, warn=warn)


# --------------------------------------------------------------------------- #
# Format angka gaya Indonesia
# --------------------------------------------------------------------------- #
def _id(s: str) -> str:
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_price(p: float) -> str:
    if p is None or not np.isfinite(p):
        return "-"
    if p >= 1000:
        s = f"{p:,.0f}"
    elif p >= 10:
        s = f"{p:,.2f}"
    elif p >= 1:
        s = f"{p:,.3f}"
    else:
        dec = max(4, int(-np.floor(np.log10(p))) + 3) if p > 0 else 4
        s = f"{p:.{min(dec, 10)}f}"
    return "$" + _id(s)


def fmt_axis_price(p: float) -> str:
    """Label sumbu: buang nol di belakang koma agar $1,800 (=1,8) tidak terbaca 1800."""
    s = fmt_price(p)
    if "," in s:
        s = s.rstrip("0").rstrip(",")
    return s


def fmt_big(v: float) -> str:
    if v is None or not np.isfinite(v):
        return "-"
    for div, unit, dec in ((1e9, " M", 2), (1e6, " jt", 1), (1e3, " rb", 0)):
        if abs(v) >= div:
            return "$" + _id(f"{v / div:,.{dec}f}") + unit
    return "$" + _id(f"{v:,.0f}")


def fmt_pct(x: float, plus: bool = True) -> str:
    if x is None or not np.isfinite(x):
        return "-"
    return _id(f"{x:+.1f}%" if plus else f"{x:.0f}%")


def fmt_x(x: float) -> str:
    return "-" if x is None or not np.isfinite(x) else _id(f"{x:.1f}x")


def fmt_dec(x: float) -> str:
    return "-" if x is None or not np.isfinite(x) else _id(f"{x:+.2f}")


def pair_name(m: dict, quote: str) -> str:
    return f"{m['base']}/{quote}"


def now_wib_str(dt: datetime) -> str:
    w = dt.astimezone(WIB)
    return f"{w.day} {BULAN[w.month - 1]} {w.year} {w:%H:%M} WIB"


# --------------------------------------------------------------------------- #
# Pesan Telegram
# --------------------------------------------------------------------------- #
def alert_caption(m: dict, cfg: dict, link: str) -> str:
    e = html.escape
    icons = "".join(SIGNAL_LABEL[s][0] for s in m["signals"])
    labels = ", ".join(SIGNAL_LABEL[s][1] for s in m["signals"])
    beli_lbl = "Beli agresif" if m["taker_real"] else "Tekanan beli (perkiraan)"
    lines = [
        f"{icons} <b>{e(pair_name(m, cfg['quote']))}</b> · Skor <b>{m['score']}</b>/100",
        f"Sinyal: {e(labels)}",
        f"💰 Harga {fmt_price(m['price'])} | 24j {fmt_pct(m['chg24'])} | 7h {fmt_pct(m['chg7'])}",
        f"📊 Vol 24j {fmt_big(m['qvol24'])} = <b>{fmt_x(m['rvol_d'])}</b> rata² 20 hari",
        f"⏱ Vol 1 jam = <b>{fmt_x(m['rvol_h'])}</b> normal ({fmt_pct(m['chg_spike'])}) · "
        f"{beli_lbl} {fmt_pct(m['buy1h'] * 100, plus=False)}",
        f"🧲 Beli 24j {fmt_pct(m['buy24'] * 100, plus=False)} · CMF20 {fmt_dec(m['cmf20'])} · "
        f"OBV {'naik' if m['obv_trend'] > 0.1 else ('turun' if m['obv_trend'] < -0.1 else 'datar')}",
    ]
    vp = m["vp"]
    if vp:
        lines.append(f"📍 Zona akumulasi {cfg['profil_volume_hari']}h: {fmt_price(vp['val'])} – "
                     f"{fmt_price(vp['vah'])} (POC {fmt_price(vp['poc'])})")
        lines.append(f"➡️ Harga di <b>{m['pos'].upper()}</b> zona ({fmt_pct(m['dist_poc'])} dari POC)")
    for w in m["warn"]:
        lines.append(f"⚠️ {e(w)}")
    if link:
        lines.append(f'<a href="{e(link)}">Buka grafik di TradingView</a>')
    text = "\n".join(lines)
    return text[:1020]


def header_text(alerts: list[dict], n_scan: int, source: str, now: datetime) -> str:
    return (f"🛰 <b>Radar Whale</b> · {now_wib_str(now)}\n"
            f"{len(alerts)} koin terdeteksi dari {n_scan} koin yang dipindai ({html.escape(source)}).\n"
            f"<i>Bukan ajakan beli — cek grafik & berita sebelum ambil keputusan.</i>")


def summary_text(results: list[dict], cfg: dict, source: str, now: datetime) -> str:
    e = html.escape
    w = now.astimezone(WIB)
    top = [r for r in results if "JUAL" not in r["signals"]][:10]
    lines = [f"📋 <b>Ringkasan Harian Radar Whale</b> — {w.day} {BULAN[w.month - 1]} {w.year}",
             f"{len(results)} koin dipindai ({e(source)}). Skor tertinggi:"]
    for i, r in enumerate(top, 1):
        icons = "".join(SIGNAL_LABEL[s][0] for s in r["signals"]) or "·"
        lines.append(f"{i}. <b>{e(r['base'])}</b> {r['score']} {icons} {fmt_pct(r['chg24'])} "
                     f"vol {fmt_x(r['rvol_d'])}")
    akum = [r["base"] for r in results if "AKUM" in r["signals"]][:8]
    jual = [r["base"] for r in results if "JUAL" in r["signals"]][:8]
    if akum:
        lines.append(f"🧲 Kandidat akumulasi: {e(', '.join(akum))}")
    if jual:
        lines.append(f"🔻 Tekanan jual besar: {e(', '.join(jual))}")
    lines.append("<i>Ketik nama koin di TradingView untuk cek grafik lengkap.</i>")
    return "\n".join(lines)


class Telegram:
    def __init__(self, token: str | None, chat_ids: str | None):
        self.token = (token or "").strip()
        self.chats = [c.strip() for c in (chat_ids or "").split(",") if c.strip()]
        self.enabled = bool(self.token and self.chats)

    @classmethod
    def from_env(cls) -> "Telegram":
        return cls(os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID"))

    def _post(self, method: str, data: dict, files: dict | None = None) -> None:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        for i in range(3):
            try:
                r = requests.post(url, data=data, files=files, timeout=30)
                if r.status_code == 429:
                    wait = r.json().get("parameters", {}).get("retry_after", 5)
                    time.sleep(int(wait) + 1)
                    continue
                if not r.ok:
                    print(f"  ! Telegram {method} gagal: {r.status_code} {r.text[:200]}")
                return
            except requests.RequestException as ex:
                print(f"  ! Telegram error: {ex}")
                time.sleep(2 * (i + 1))

    def send_text(self, text: str) -> None:
        if not self.enabled:
            print("\n--- [Telegram belum diatur, pesan hanya ditampilkan] ---\n" + text)
            return
        chunks, cur = [], ""
        for line in text.split("\n"):
            if len(cur) + len(line) + 1 > 3900:
                chunks.append(cur)
                cur = ""
            cur += line + "\n"
        chunks.append(cur)
        for chat in self.chats:
            for c in chunks:
                self._post("sendMessage", {"chat_id": chat, "text": c, "parse_mode": "HTML",
                                           "disable_web_page_preview": "true"})

    def send_photo(self, png: bytes, caption: str) -> None:
        if not self.enabled:
            print("\n--- [grafik + caption] ---\n" + caption)
            return
        for chat in self.chats:
            self._post("sendPhoto", {"chat_id": chat, "caption": caption, "parse_mode": "HTML"},
                       files={"photo": ("radar.png", png, "image/png")})


# --------------------------------------------------------------------------- #
# Grafik
# --------------------------------------------------------------------------- #
C = dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9",
         axis="#c3c2b7", up="#0ca30c", down="#d03b3b", blue="#2a78d6", blue_lt="#86b6ef",
         orange="#eb6834", vol="#c3c2b7")


def _style(ax) -> None:
    ax.set_facecolor(C["surface"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(C["axis"])
    ax.tick_params(colors=C["muted"], labelsize=8, length=3)
    ax.grid(axis="y", color=C["grid"], lw=0.6)
    ax.set_axisbelow(True)


def make_chart(m: dict, d: pd.DataFrame, cfg: dict, source: str, now: datetime) -> bytes:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    full = d.reset_index(drop=True)
    obv_full = obv_series(full)
    avg_prev = full["qvol"].shift(1).rolling(20, min_periods=5).mean()
    dd = full.tail(60).reset_index(drop=True)
    obv = obv_full.tail(60).to_numpy()
    avg = avg_prev.tail(60).to_numpy()
    x = np.arange(len(dd))

    fig = plt.figure(figsize=(10, 7.4), dpi=110, facecolor=C["surface"])
    gs = fig.add_gridspec(3, 2, width_ratios=[5, 1.25], height_ratios=[3.3, 1.15, 1.0],
                          hspace=0.22, wspace=0.03)
    ax = fig.add_subplot(gs[0, 0])
    axp = fig.add_subplot(gs[0, 1], sharey=ax)
    axv = fig.add_subplot(gs[1, 0], sharex=ax)
    axo = fig.add_subplot(gs[2, 0], sharex=ax)
    for a in (ax, axp, axv, axo):
        _style(a)

    vp = m["vp"]
    if vp:
        ax.axhspan(vp["val"], vp["vah"], color=C["blue"], alpha=0.09, lw=0, zorder=0)
        ax.axhline(vp["poc"], color=C["blue"], lw=1.3, ls=(0, (5, 3)), zorder=1)

    # Candle: naik = berongga, turun = terisi (bentuk ikut membedakan, bukan warna saja)
    wbody = 0.62
    for i, r in dd.iterrows():
        up = r["close"] >= r["open"]
        col = C["up"] if up else C["down"]
        alpha = 1.0 if r["closed"] else 0.55
        ax.vlines(i, r["low"], r["high"], color=col, lw=1, zorder=2, alpha=alpha)
        lo = min(r["open"], r["close"])
        hgt = max(abs(r["close"] - r["open"]), (r["high"] - r["low"]) * 0.02, 1e-12)
        ax.add_patch(Rectangle((i - wbody / 2, lo), wbody, hgt, facecolor=C["surface"] if up else col,
                               edgecolor=col, lw=1.1, zorder=3, alpha=alpha))
    ax.axhline(m["price"], color=C["ink2"], lw=0.9, ls=":", zorder=1)
    ylo = min(dd["low"].min(), vp["val"] if vp else np.inf)
    yhi = max(dd["high"].max(), vp["vah"] if vp else -np.inf)
    pad = (yhi - ylo) * 0.06
    ax.set_ylim(ylo - pad, yhi + pad)
    ax.set_xlim(-1, len(dd))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt_axis_price(v)))
    plt.setp(ax.get_xticklabels(), visible=False)

    labels = ", ".join(SIGNAL_LABEL[s][1] for s in m["signals"]) or "Tidak ada sinyal"
    ax.set_title(f"{pair_name(m, cfg['quote'])}  ·  Skor {m['score']}/100", loc="left",
                 fontsize=13, fontweight="bold", color=C["ink"], pad=40)
    ax.text(0, 1.085, f"{labels}  ·  Harga {fmt_price(m['price'])} ({fmt_pct(m['chg24'])} 24j)",
            transform=ax.transAxes, fontsize=9, color=C["ink2"], va="bottom")
    handles = [Patch(facecolor=C["blue"], alpha=0.18, label="Zona akumulasi (70% volume)"),
               Line2D([], [], color=C["blue"], lw=1.3, ls=(0, (5, 3)), label="POC — harga volume terbesar"),
               Line2D([], [], color=C["ink2"], lw=0.9, ls=":", label="Harga terakhir")]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=8,
              frameon=False, labelcolor=C["ink2"], borderaxespad=0.2, handlelength=1.8,
              columnspacing=1.4)

    # Profil volume (sumbu kanan)
    if vp:
        cols = []
        for i in range(len(vp["vol"])):
            if i == vp["poc_i"]:
                cols.append(C["blue"])
            elif vp["va"][0] <= i <= vp["va"][1]:
                cols.append(C["blue_lt"])
            else:
                cols.append(C["vol"])
        bh = (vp["edges"][1] - vp["edges"][0]) * 0.86
        axp.barh(vp["centers"], vp["vol"], height=bh, color=cols, lw=0)
        axp.set_xlim(0, vp["vol"].max() * 1.9)
        lx = vp["vol"].max() * 1.06
        near = abs(m["price"] - vp["poc"]) < (yhi - ylo) * 0.07
        poc_txt = f"POC {fmt_price(vp['poc'])}" + ("\n≈ harga sekarang" if near else "")
        axp.text(lx, vp["poc"], poc_txt, fontsize=8, color=C["ink"], va="center")
        if not near:
            axp.text(lx, m["price"], f"Harga {fmt_price(m['price'])}", fontsize=8,
                     color=C["ink2"], va="center")
    axp.set_title(f"Volume per harga\n{cfg['profil_volume_hari']} hari", fontsize=8, color=C["ink2"])
    axp.tick_params(axis="x", bottom=False, labelbottom=False)
    plt.setp(axp.get_yticklabels(), visible=False)
    axp.tick_params(axis="y", left=False)
    axp.spines["left"].set_visible(False)
    axp.spines["bottom"].set_visible(False)
    axp.grid(False)

    # Panel volume harian
    spike = np.nan_to_num(dd["qvol"].to_numpy() > 2 * avg, nan=False).astype(bool)
    axv.bar(x, dd["qvol"], width=0.7, color=np.where(spike, C["orange"], C["vol"]), lw=0)
    axv.plot(x, avg, color=C["ink2"], lw=1.2)
    axv.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt_big(v).replace("$", "")))
    axv.set_title("Volume harian (USDT) — oranye: > 2x rata-rata 20 hari (garis)",
                  loc="left", fontsize=8, color=C["ink2"], pad=4)
    plt.setp(axv.get_xticklabels(), visible=False)

    # Panel OBV
    axo.plot(x, obv, color=C["blue"], lw=1.6)
    axo.tick_params(axis="y", labelleft=False, left=False)
    axo.set_title("OBV (On-Balance Volume) — garis naik = koin sedang dikumpulkan",
                  loc="left", fontsize=8, color=C["ink2"], pad=4)
    step = 10
    ticks = list(range(len(dd) - 1, -1, -step))[::-1]
    axo.set_xticks(ticks)
    axo.set_xticklabels([f"{t.day} {BULAN[t.month - 1]}" for t in dd["time"].iloc[ticks]])

    fig.text(0.99, 0.005, f"Sumber: {source} · {now_wib_str(now)} · bukan nasihat investasi",
             ha="right", fontsize=7, color=C["muted"])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=C["surface"], bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# State (anti-spam)
# --------------------------------------------------------------------------- #
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                s = json.load(f)
                s.setdefault("alerts", {})
                return s
        except (OSError, ValueError):
            pass
    return {"alerts": {}}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def should_alert(m: dict, state: dict, cfg: dict, now: datetime) -> bool:
    prev = state["alerts"].get(m["symbol"])
    if not prev:
        return True
    age_h = (now - datetime.fromisoformat(prev["ts"])).total_seconds() / 3600
    if age_h >= cfg["cooldown_jam"]:
        return True
    new = set(m["signals"]) - set(prev.get("signals", [])) - {"JUAL"}
    return bool(new) or m["score"] >= prev.get("score", 0) + 15


# --------------------------------------------------------------------------- #
# Jalankan
# --------------------------------------------------------------------------- #
def pick_universe(cfg: dict, demo: bool):
    if demo:
        src = DemoSource()
        return src, src.universe(cfg["quote"])
    order = [Binance, OKX] if cfg["sumber_data"].lower() != "okx" else [OKX, Binance]
    errors = []
    for cls in order:
        src = cls()
        try:
            uni = src.universe(cfg["quote"])
            if uni:
                return src, uni
        except Exception as e:
            errors.append(f"{cls.name}: {e}")
            print(f"  ! {cls.name} gagal: {e}")
    raise SourceError(" | ".join(errors) or "Tidak ada data")


def filter_universe(uni: list[dict], cfg: dict, demo: bool) -> list[dict]:
    keep = []
    for u in uni:
        b = u["base"].upper()
        if b in cfg["abaikan"]:
            continue
        if demo or b in cfg["pantau_khusus"] or u["qvol24"] >= cfg["min_volume_24j_usd"]:
            keep.append(u)
    keep.sort(key=lambda u: u["qvol24"], reverse=True)
    top = keep[: int(cfg["maks_koin_dipindai"])]
    extra = [u for u in keep[int(cfg["maks_koin_dipindai"]):] if u["base"].upper() in cfg["pantau_khusus"]]
    return top + extra


def scan(src, uni: list[dict], cfg: dict):
    hours = 24 * int(cfg["profil_volume_hari"]) + 72
    results, frames, failed = [], {}, 0

    def work(u):
        d = src.candles(u["symbol"], "1d", 90)
        h = src.candles(u["symbol"], "1h", hours)
        return u, d, h

    with ThreadPoolExecutor(max_workers=src.workers) as ex:
        futs = [ex.submit(work, u) for u in uni]
        for f in as_completed(futs):
            try:
                u, d, h = f.result()
                m = analyze(u, d, h, cfg)
                if m:
                    results.append(m)
                    frames[m["symbol"]] = d
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"  ! gagal analisa: {e}")
    results.sort(key=lambda r: r["score"], reverse=True)
    return results, frames, failed


def write_step_summary(results: list[dict], cfg: dict, source: str, now: datetime, path: str) -> None:
    lines = [f"## Radar Whale — {now_wib_str(now)}", "",
             f"Sumber: {source} · koin dianalisa: {len(results)}", "",
             "| # | Koin | Skor | Sinyal | Harga | 24j | Vol vs rata² | Vol 1 jam | Beli 24j | Posisi vs zona |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(results[:30], 1):
        sig = " ".join(SIGNAL_LABEL[s][0] + SIGNAL_LABEL[s][1] for s in r["signals"]) or "-"
        lines.append(f"| {i} | {r['base']} | {r['score']} | {sig} | {fmt_price(r['price'])} | "
                     f"{fmt_pct(r['chg24'])} | {fmt_x(r['rvol_d'])} | {fmt_x(r['rvol_h'])} | "
                     f"{fmt_pct(r['buy24'] * 100, plus=False)} | {r['pos']} |")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Radar Whale Kripto")
    ap.add_argument("--mode", default="normal", choices=["normal", "demo", "tes-telegram"])
    args = ap.parse_args()
    cfg = load_config()
    tg = Telegram.from_env()
    now = datetime.now(timezone.utc)
    demo = args.mode == "demo"

    if args.mode == "tes-telegram":
        if not tg.enabled:
            print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diisi di GitHub Secrets.")
            return 1
        tg.send_text(f"✅ <b>Radar Whale tersambung!</b>\n{now_wib_str(now)}\n"
                     "Alert akan dikirim otomatis tiap jam kalau ada koin yang memenuhi syarat.")
        print("Pesan tes terkirim.")
        return 0

    state = load_state()
    t0 = time.time()
    try:
        src, uni = pick_universe(cfg, demo)
    except SourceError as e:
        msg = f"⚠️ <b>Radar Whale gagal mengambil data</b>\n{html.escape(str(e))[:600]}"
        last = state.get("last_error_notice")
        if not last or (now - datetime.fromisoformat(last)).total_seconds() > 6 * 3600:
            tg.send_text(msg)
            state["last_error_notice"] = now.isoformat(timespec="seconds")
            save_state(state)
        print(msg)
        return 1

    uni = filter_universe(uni, cfg, demo)
    print(f"Sumber {src.name}: {len(uni)} koin akan dipindai...")
    results, frames, failed = scan(src, uni, cfg)
    print(f"Selesai {time.time() - t0:.0f} dtk · dianalisa {len(results)} · gagal {failed}")

    th = cfg["ambang"]
    candidates = [r for r in results
                  if any(s != "JUAL" for s in r["signals"]) and r["score"] >= th["skor_min_alert"]]
    alerts = candidates if demo else [r for r in candidates if should_alert(r, state, cfg, now)]

    if demo:
        os.makedirs(OUT_DIR, exist_ok=True)

    if alerts:
        tg.send_text(header_text(alerts, len(results), src.name, now))
        maxg = int(cfg["maks_grafik_per_run"])
        for r in alerts[:maxg]:
            png = make_chart(r, frames[r["symbol"]], cfg, src.name, now)
            if demo:
                with open(os.path.join(OUT_DIR, f"grafik_{r['base']}.png"), "wb") as f:
                    f.write(png)
            tg.send_photo(png, alert_caption(r, cfg, src.chart_link(r)))
        rest = alerts[maxg:]
        if rest:
            tg.send_text("Koin lain yang juga terdeteksi:\n" + "\n".join(
                f"• <b>{html.escape(r['base'])}</b> skor {r['score']} "
                f"{''.join(SIGNAL_LABEL[s][0] for s in r['signals'])} vol {fmt_x(r['rvol_d'])}"
                for r in rest[:20]))
        if not demo:
            for r in alerts:
                state["alerts"][r["symbol"]] = {"ts": now.isoformat(timespec="seconds"),
                                                "score": r["score"], "signals": r["signals"]}
    elif candidates:
        print(f"{len(candidates)} koin masih memenuhi syarat, tapi sudah di-alert "
              f"(masa cooldown {cfg['cooldown_jam']} jam).")
    else:
        print("Tidak ada koin yang memenuhi syarat alert pada putaran ini.")

    # Ringkasan harian (sekali sehari, mulai jam yang diatur)
    w = now.astimezone(WIB)
    today = w.date().isoformat()
    if demo or (w.hour >= int(cfg["ringkasan_harian_jam_wib"]) and state.get("last_summary") != today):
        tg.send_text(summary_text(results, cfg, src.name, now))
        if not demo:
            state["last_summary"] = today

    step = os.environ.get("GITHUB_STEP_SUMMARY") or (os.path.join(OUT_DIR, "ringkasan.md") if demo else None)
    if step:
        write_step_summary(results, cfg, src.name, now, step)

    if not demo:
        cutoff = now - timedelta(days=7)
        state["alerts"] = {k: v for k, v in state["alerts"].items()
                           if datetime.fromisoformat(v["ts"]) >= cutoff}
        state.pop("last_error_notice", None)
        state["sumber_terakhir"] = src.name
        save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
