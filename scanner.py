#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RADAR KRIPTO — Analisa Teknikal Top 200 CoinMarketCap
=====================================================
Tiap jam (GitHub Actions):
  1. Ambil daftar 200 koin terbesar dari CoinMarketCap (cadangan: CoinGecko)
  2. Ambil candle harian & per jam dari Binance (cadangan: OKX)
  3. Analisa: trend line, MA, Bollinger, candlestick, chart pattern, MACD, RSI,
     Stochastic, Elliott Wave, akumulasi volume  (lihat analisa.py)
  4. Klasifikasi:
       🟢 POTENSI NAIK  = sedang diakumulasi + harga masih di bawah + sinyal naik kuat
       🔴 POTENSI TURUN = sinyal turun kuat (distribusi, pola bearish, momentum melemah)
     lengkap dengan persentase target sesuai aturan pola grafik & batas batal.
  5. Kirim alert + grafik ke Telegram, dan perbarui dashboard web (GitHub Pages).

Cara jalan:
  python scanner.py                      # mode normal
  python scanner.py --mode demo          # uji dengan data simulasi (tanpa internet)
  python scanner.py --mode tes-telegram  # cek sambungan Telegram
  python scanner.py --mode ringkasan     # mode normal + kirim ringkasan harian sekarang juga

BUKAN NASIHAT INVESTASI. Target = proyeksi pola teknikal, bukan jaminan.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests
import yaml

from analisa import BULAN, analisa_koin, fmt_pct, fmt_price
import rekam_jejak as rekam
import pasar as PS
import strategi as ST
from grafik import buat_grafik

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(ROOT, "state.json")
SITE_DIR = os.path.join(ROOT, "site")
OUT_DIR = os.path.join(ROOT, "out")
WIB = timezone(timedelta(hours=7))

# --------------------------------------------------------------------------- #
# Konfigurasi
# --------------------------------------------------------------------------- #
DEFAULT_CONFIG = {
    "sumber_ranking": "coinmarketcap",
    "top_n": 200,
    "ranking_refresh_jam": 6,
    "bursa": ["binance", "okx"],
    "quote": "USDT",
    "min_volume_24j_usd": 300_000,
    "abaikan": [],
    "skor_min": 55,
    "selisih_min": 15,
    "skor_pantau": 40,
    "syarat_akumulasi": True,
    "maks_naik_7h_persen": 20,
    "kirim_alert_turun": False,
    "cooldown_jam": 12,
    "maks_grafik_per_run": 6,
    "maks_grafik_dashboard": 40,
    "profil_volume_hari": 30,
    "ringkasan_harian_jam_wib": 8,
    "url_dashboard": "",
    "filter_pasar": "ketat",
    "filter_meme": "abaikan",
    "wajib_breakout": False,
    "min_rr": 0,
    "filter_stage_naik": [],
    "filter_stage_turun": [],
    "min_checklist": 0,
    "sinyal_stage2": True,
    "stage2_filter_pasar": "ketat",
    "stage2_maks_grafik": 5,
    "stage2_jeda_hari": 10,
    "model_pasar": "auto",
    "sinyal_short": True,
    "short_filter_pasar": "longgar",
    "short_maks_grafik": 5,
    "short_jeda_hari": 10,
    "short_leverage_maks": 2,
    "rencana": dict(ST.DEFAULT_RENCANA),
    "modal_rp": 0,
    "risiko_per_transaksi_persen": 1,
    "maks_posisi_persen": 20,
    "biaya": dict(ST.DEFAULT_BIAYA),
}

STABIL = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDP", "USDE", "USDS", "PYUSD", "USD1", "RLUSD", "BUSD",
          "GUSD", "FRAX", "LUSD", "USDD", "USDX", "EURC", "EURT", "EURI", "AEUR", "XAUT", "PAXG", "USDB",
          "USDY", "USD0", "SUSDE", "BFUSD", "USDTB", "USDG", "USDF", "USDA", "CRVUSD", "GHO", "BUIDL", "USYC",
          "OUSG", "USTB", "SUSDS", "SYRUPUSDC", "USR", "DOLA", "FDIT"}
TURUNAN = {"WBTC", "WETH", "STETH", "WSTETH", "WEETH", "CBBTC", "WBETH", "BNSOL", "METH", "RETH", "LBTC",
           "SOLVBTC", "JITOSOL", "MSOL", "BBSOL", "EZETH", "RSETH", "TBTC", "CMETH", "JUPSOL", "SAVAX",
           "STKAIDA", "CLBTC", "BTC.B", "WBNB", "WTRX", "WHYPE", "KHYPE", "STHYPE", "OSETH", "SFRXETH",
           "LSETH", "WSOL", "BTCB", "RSWETH", "EBTC", "UNIBTC", "PUMPBTC", "FBTC", "XSOLVBTC", "SUPEROETH"}
ALIAS_BINANCE = {"SATS": "1000SATS", "CAT": "1000CAT", "CHEEMS": "1000CHEEMS", "MIOTA": "IOTA"}


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
    cfg["bursa"] = [str(x).lower() for x in (cfg.get("bursa") or ["binance"])]
    return cfg


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
class BlockedError(Exception):
    """Server menolak akses dari lokasi ini (HTTP 403/451)."""


class SourceError(Exception):
    pass


SESSION = requests.Session()
SESSION.headers["User-Agent"] = "radar-kripto/2.0"


def http_get(url: str, params: dict | None = None, headers: dict | None = None, retries: int = 3,
             timeout: int = 25):
    last: Exception | None = None
    for i in range(retries):
        try:
            r = SESSION.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (403, 451):
                raise BlockedError(f"HTTP {r.status_code} dari {url}")
            if r.status_code == 429 or r.status_code >= 500:
                last = RuntimeError(f"HTTP {r.status_code} dari {url}")
                time.sleep(3 * (i + 1))
                continue
            if r.status_code >= 400:
                raise SourceError(f"HTTP {r.status_code} dari {url}: {r.text[:150]}")
            return r.json()
        except (BlockedError, SourceError):
            raise
        except (requests.RequestException, ValueError) as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last if last else RuntimeError(f"Gagal mengambil {url}")


# --------------------------------------------------------------------------- #
# Daftar Top 200
# --------------------------------------------------------------------------- #
def _stabil(sym: str, name: str, price, tags=()) -> bool:
    s = sym.upper()
    if s in STABIL or s in TURUNAN:
        return True
    if any("stablecoin" in str(t) for t in tags) or any("wrapped" in str(t) for t in tags):
        return True
    usd_like = "USD" in s or "usd" in (name or "").lower()
    return bool(usd_like and price is not None and abs(float(price) - 1) < 0.03)


def top_cmc(key: str, n: int) -> list[dict]:
    d = http_get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
                 {"start": 1, "limit": n, "convert": "USD", "sort": "market_cap"},
                 headers={"X-CMC_PRO_API_KEY": key, "Accept": "application/json"})
    st = d.get("status", {})
    if st.get("error_code") not in (0, None):
        raise SourceError(f"CoinMarketCap: {st.get('error_message')}")
    out = []
    for x in d.get("data", []):
        price = (x.get("quote") or {}).get("USD", {}).get("price")
        out.append(dict(symbol=str(x["symbol"]).upper(), name=x.get("name", ""), rank=int(x.get("cmc_rank") or 0),
                        stabil=_stabil(x["symbol"], x.get("name", ""), price, x.get("tags") or []),
                        meme=ST.is_meme(str(x["symbol"]), x.get("tags") or [])))
    return out


def top_coingecko(n: int) -> list[dict]:
    headers = {}
    key = os.environ.get("COINGECKO_API_KEY", "").strip()
    if key:
        headers["x-cg-demo-api-key"] = key
    rows = http_get("https://api.coingecko.com/api/v3/coins/markets",
                    {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 1},
                    headers=headers or None)
    out = []
    for x in rows:
        rk = x.get("market_cap_rank")
        if not rk or rk > n:
            continue
        out.append(dict(symbol=str(x["symbol"]).upper(), name=x.get("name", ""), rank=int(rk),
                        stabil=_stabil(x["symbol"], x.get("name", ""), x.get("current_price")),
                        meme=ST.is_meme(str(x["symbol"]))))
    return sorted(out, key=lambda r: r["rank"])


def ambil_ranking(cfg: dict, state: dict, now: datetime) -> tuple[list[dict], str]:
    n = int(cfg["top_n"])
    cache = state.get("ranking") or {}
    if cache.get("data") and cache.get("n") == n:
        age = (now - datetime.fromisoformat(cache["ts"])).total_seconds() / 3600
        if age < float(cfg["ranking_refresh_jam"]):
            return cache["data"], cache["sumber"]
    key = os.environ.get("CMC_API_KEY", "").strip()
    errors, data, sumber = [], None, ""
    if key and cfg["sumber_ranking"].lower() != "coingecko":
        try:
            data, sumber = top_cmc(key, n), "CoinMarketCap"
        except Exception as e:
            errors.append(f"CoinMarketCap: {e}")
    if not data:
        try:
            data = top_coingecko(n)
            sumber = "CoinGecko" + ("" if not key and cfg["sumber_ranking"].lower() == "coingecko"
                                    else " (cadangan — isi CMC_API_KEY untuk CoinMarketCap)")
        except Exception as e:
            errors.append(f"CoinGecko: {e}")
    if not data:
        if cache.get("data"):
            print("  ! Ranking gagal diperbarui, pakai data lama:", " | ".join(errors))
            return cache["data"], cache["sumber"] + " (data lama)"
        raise SourceError("Gagal mengambil daftar top koin: " + " | ".join(errors))
    if errors:
        print("  !", " | ".join(errors))
    state["ranking"] = {"ts": now.isoformat(timespec="seconds"), "sumber": sumber, "n": n, "data": data}
    return data, sumber


# --------------------------------------------------------------------------- #
# Bursa (data candle)
# --------------------------------------------------------------------------- #
class Binance:
    name = "Binance"
    # data-api.binance.vision = mirror data pasar publik, tetap bisa diakses dari server GitHub (AS)
    HOSTS = ["https://data-api.binance.vision", "https://api.binance.com", "https://api-gcp.binance.com"]

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
            except Exception as e:
                err = e
        raise SourceError(f"Binance tidak bisa diakses ({err})")

    def tickers(self, quote: str) -> dict[str, dict]:
        trading: dict[str, str] | None = None
        try:
            info = self._get("/api/v3/exchangeInfo", {"permissions": "SPOT"})
            trading = {s["symbol"]: s["baseAsset"] for s in info.get("symbols", [])
                       if s.get("status") == "TRADING" and s.get("quoteAsset") == quote}
        except SourceError:
            trading = None
        out = {}
        for t in self._get("/api/v3/ticker/24hr"):
            sym = t.get("symbol", "")
            if trading is not None:
                if sym not in trading:
                    continue
                base = trading[sym]
            elif sym.endswith(quote):
                base = sym[: -len(quote)]
            else:
                continue
            if int(t.get("count", 0) or 0) == 0:
                continue
            out[base.upper()] = dict(symbol=sym, base=base.upper(), price=float(t["lastPrice"]),
                                     chg24=float(t["priceChangePercent"]), qvol24=float(t["quoteVolume"]))
        return out

    def candles(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        rows = self._get("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": int(min(limit, 1000))})
        now_ms = int(time.time() * 1000)
        df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v", "ct", "qv", "n", "tbv", "tbqv", "x"])
        return pd.DataFrame({
            "time": pd.to_datetime(df["t"].astype("int64"), unit="ms", utc=True),
            "open": df["o"].astype(float), "high": df["h"].astype(float), "low": df["l"].astype(float),
            "close": df["c"].astype(float), "volume": df["v"].astype(float), "qvol": df["qv"].astype(float),
            "taker_buy_q": df["tbqv"].astype(float), "closed": df["ct"].astype("int64") < now_ms,
        })

    def link(self, r: dict, quote: str) -> str:
        return f"https://www.tradingview.com/chart/?symbol=BINANCE:{r['symbol']}"

    def harga_pada(self, symbol: str, ts_ms: int) -> float | None:
        """Harga pada menit tertentu (open candle 1 menit)."""
        menit = int(ts_ms) // 60000 * 60000
        rows = self._get("/api/v3/klines", {"symbol": symbol, "interval": "1m", "startTime": menit, "limit": 1})
        return float(rows[0][1]) if rows else None


class OKX:
    """Cadangan untuk koin yang tidak ada di Binance. OKX tidak memberi data
    'beli agresif', jadi dipakai perkiraan dari CMF per jam."""
    name = "OKX"
    BASE = "https://www.okx.com"

    def _get(self, path: str, params: dict | None = None):
        d = http_get(self.BASE + path, params)
        if str(d.get("code")) != "0":
            raise SourceError(f"OKX error: {d.get('msg')}")
        return d["data"]

    def tickers(self, quote: str) -> dict[str, dict]:
        out = {}
        for t in self._get("/api/v5/market/tickers", {"instType": "SPOT"}):
            inst = t.get("instId", "")
            if "-" not in inst:
                continue
            base, q = inst.split("-", 1)
            if q != quote:
                continue
            last, open24 = float(t.get("last") or 0), float(t.get("open24h") or 0)
            out[base.upper()] = dict(symbol=inst, base=base.upper(), price=last,
                                     chg24=(last / open24 - 1) * 100 if open24 else 0.0,
                                     qvol24=float(t.get("volCcy24h") or 0))
        return out

    def candles(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        bar = {"1d": "1Dutc", "1h": "1H"}[interval]
        rows: list = []
        after = None
        for _ in range(15):
            if not rows:
                path, params = "/api/v5/market/candles", {"instId": symbol, "bar": bar, "limit": 300}
            else:
                path, params = "/api/v5/market/history-candles", {"instId": symbol, "bar": bar, "limit": 100,
                                                                  "after": after}
            batch = self._get(path, params)
            if not batch:
                break
            rows.extend(batch)
            after = batch[-1][0]
            if len(rows) >= limit:
                break
            time.sleep(0.12)
        rows = rows[:limit][::-1]
        df = pd.DataFrame(rows).iloc[:, :9]
        df.columns = ["t", "o", "h", "l", "c", "v", "vccy", "vq", "confirm"]
        return pd.DataFrame({
            "time": pd.to_datetime(df["t"].astype("int64"), unit="ms", utc=True),
            "open": df["o"].astype(float), "high": df["h"].astype(float), "low": df["l"].astype(float),
            "close": df["c"].astype(float), "volume": df["v"].astype(float), "qvol": df["vq"].astype(float),
            "taker_buy_q": np.nan, "closed": df["confirm"].astype(str) == "1",
        })

    def link(self, r: dict, quote: str) -> str:
        return f"https://www.tradingview.com/chart/?symbol=OKX:{r['base']}{quote}"

    def harga_pada(self, symbol: str, ts_ms: int) -> float | None:
        menit = int(ts_ms) // 60000 * 60000
        rows = self._get("/api/v5/market/history-candles", {"instId": symbol, "bar": "1m", "after": menit + 1,
                                                             "limit": 1})
        return float(rows[0][1]) if rows else None


# --------------------------------------------------------------------------- #
# Data simulasi untuk mode demo
# --------------------------------------------------------------------------- #
class DemoSource:
    name = "DEMO (data simulasi)"
    T = 299
    SPEK = [  # simbol, nama, rank CMC, titik jalur harga (hari, harga), akumulasi (+1/-1/0)
        ("DBOT", "Demo Double Bottom", 12,
         [(0, 100), (200, 100), (240, 70), (255, 85), (275, 71), (299, 72.5)], 1),
        ("IHS", "Demo Inverse H&S", 25,
         [(0, 100), (190, 100), (215, 78), (230, 90), (252, 66), (270, 90), (288, 79), (299, 81)], 1),
        ("FWDG", "Demo Falling Wedge", 40,
         [(0, 130), (210, 130), (222, 100), (232, 110), (246, 86), (256, 93), (270, 78), (280, 82), (293, 73),
          (299, 75)], 1),
        ("CUPH", "Demo Cup and Handle", 55,
         [(0, 80), (150, 80), (175, 100), (195, 85), (210, 77), (220, 75), (232, 77), (247, 85), (265, 99),
          (272, 100), (284, 93), (299, 95)], 1),
        ("HNS", "Demo Head & Shoulders", 8,
         [(0, 70), (190, 70), (215, 92), (230, 80), (252, 104), (270, 80), (286, 91), (296, 79), (299, 77.5)], -1),
        ("RWDG", "Demo Rising Wedge", 30,
         [(0, 70), (210, 70), (222, 100), (232, 90), (246, 114), (256, 107), (270, 122), (280, 118), (292, 127),
          (299, 123)], -1),
        ("BFLG", "Demo Bear Flag", 60,
         [(0, 100), (270, 100), (281, 72), (284, 76), (287, 73), (290, 78), (293, 75), (296, 80), (299, 78)], -1),
        ("TENANG", "Demo Netral", 3, [(0, 50), (100, 55), (200, 48), (299, 52)], 0),
    ]

    def __init__(self):
        rng = np.random.default_rng(11)
        days = self.T + 1
        hours = days * 24
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        idx = pd.date_range(end=now - timedelta(hours=1), periods=hours, freq="h", tz="UTC")
        self.data: dict[str, dict] = {}
        for sym, name, rank, wp, akum in self.SPEK:
            xs, ys = zip(*wp)
            t = np.arange(hours) / 24.0
            base = np.exp(np.interp(t, xs, np.log(ys)))
            e = np.zeros(hours)
            eps = rng.normal(0, 0.0022, hours)
            for i in range(1, hours):
                e[i] = 0.97 * e[i - 1] + eps[i]
            close = base * np.exp(e)
            opn = np.concatenate([[close[0]], close[:-1]])
            high = np.maximum(opn, close) * (1 + np.abs(rng.normal(0, 0.002, hours)))
            low = np.minimum(opn, close) * (1 - np.abs(rng.normal(0, 0.002, hours)))
            vol = rng.lognormal(np.log(300_000), 0.3, hours)
            taker = np.clip(rng.normal(0.5, 0.03, hours), 0.3, 0.7)
            # hari naik / turun (untuk pola volume akumulasi / distribusi)
            day_ret = np.repeat(close.reshape(days, 24)[:, -1] / close.reshape(days, 24)[:, 0] - 1, 24)
            k = 24 * 45
            if akum > 0:
                vol[-k:] *= np.where(day_ret[-k:] > 0, 2.2, 0.6)
                taker[-24 * 30:] = np.clip(rng.normal(0.57, 0.03, 24 * 30), 0.4, 0.75)
            elif akum < 0:
                vol[-k:] *= np.where(day_ret[-k:] < 0, 2.2, 0.6)
                taker[-24 * 30:] = np.clip(rng.normal(0.43, 0.03, 24 * 30), 0.25, 0.6)
            h = pd.DataFrame({"time": idx, "open": opn, "high": high, "low": low, "close": close, "qvol": vol,
                              "taker_buy_q": vol * taker})
            h["volume"] = h["qvol"] / h["close"]
            h["closed"] = True
            d = (h.set_index("time").resample("1D")
                 .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
                       "qvol": "sum", "taker_buy_q": "sum"}).reset_index())
            d["closed"] = d["time"] + timedelta(days=1) <= now
            self.data[sym + "USDT"] = dict(h=h, d=d)

    def ranking(self) -> list[dict]:
        return [dict(symbol=s, name=n, rank=r, stabil=False) for s, n, r, _, _ in self.SPEK]

    def tickers(self, quote: str) -> dict[str, dict]:
        out = {}
        for s, v in self.data.items():
            h = v["h"]
            c = h["close"].to_numpy()
            out[s[:-4]] = dict(symbol=s, base=s[:-4], price=float(c[-1]), chg24=float((c[-1] / c[-25] - 1) * 100),
                               qvol24=float(h["qvol"].tail(24).sum()))
        return out

    def candles(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        return self.data[symbol]["d" if interval == "1d" else "h"].tail(limit).reset_index(drop=True)

    def link(self, r: dict, quote: str) -> str:
        return ""

    def harga_pada(self, symbol: str, ts_ms: int) -> float | None:
        h = self.data[symbol]["h"]
        k = h["time"].searchsorted(pd.Timestamp(ts_ms, unit="ms", tz="UTC"))
        return float(h["open"].iloc[min(k, len(h) - 1)])


# --------------------------------------------------------------------------- #
# Universe: Top 200 yang tersedia di bursa
# --------------------------------------------------------------------------- #
def bangun_universe(rank_list: list[dict], cfg: dict, demo: DemoSource | None):
    quote = cfg["quote"]
    sources: list[tuple[object, dict]] = []
    errors = []
    if demo:
        sources.append((demo, demo.tickers(quote)))
    else:
        for nama in cfg["bursa"]:
            src = Binance() if nama == "binance" else OKX() if nama == "okx" else None
            if src is None:
                continue
            try:
                sources.append((src, src.tickers(quote)))
            except Exception as e:
                errors.append(f"{src.name}: {e}")
                print(f"  ! {src.name} gagal: {e}")
    if not sources:
        raise SourceError("Semua bursa gagal diakses: " + " | ".join(errors))
    seen, uni, tidak_ada = set(), [], []
    for coin in sorted(rank_list, key=lambda x: x["rank"]):
        sym = coin["symbol"]
        if coin.get("stabil") or sym in cfg["abaikan"] or sym in seen:
            continue
        seen.add(sym)
        found = None
        for src, tick in sources:
            key = ALIAS_BINANCE.get(sym, sym) if isinstance(src, Binance) else sym
            if key in tick:
                found = dict(tick[key], name=coin["name"], rank=coin["rank"], bursa=src.name, _src=src,
                             meme=bool(coin.get("meme")) or ST.is_meme(sym))
                break
        if not found:
            tidak_ada.append(sym)
            continue
        if not demo and found["qvol24"] < cfg["min_volume_24j_usd"]:
            continue
        uni.append(found)
    return uni, tidak_ada, [s.name for s, _ in sources]


def scan(uni: list[dict], cfg: dict):
    jam = 24 * int(cfg["profil_volume_hari"]) + 72
    results, failed = [], []

    def work(u):
        src = u["_src"]
        d = src.candles(u["symbol"], "1d", 400)
        h = src.candles(u["symbol"], "1h", jam)
        r = analisa_koin(u, d, h, cfg)
        if r:
            r["_h"] = h
        return r

    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(work, u): u for u in uni}
        for f in as_completed(futs):
            u = futs[f]
            try:
                r = f.result()
                if r:
                    r["link"] = u["_src"].link(r, cfg["quote"])
                    results.append(r)
            except Exception as e:
                failed.append(u["base"])
                if len(failed) <= 5:
                    print(f"  ! gagal analisa {u['base']}: {e}")
    results.sort(key=lambda r: (r["rank"] or 9999))
    return results, failed


# --------------------------------------------------------------------------- #
# Pesan Telegram
# --------------------------------------------------------------------------- #
POSISI = {"bawah": "di bawah zona", "dalam-bawah": "di bawah POC (bagian bawah zona)",
          "dalam-atas": "di atas POC (bagian atas zona)", "atas": "di atas zona", "-": "-"}


def now_wib_str(dt: datetime) -> str:
    w = dt.astimezone(WIB)
    return f"{w.day} {BULAN[w.month - 1]} {w.year} {w:%H:%M} WIB"


def _rr(x):
    return f" · rasio {x:.1f}".replace(".", ",") if x else ""


def caption(r: dict, cfg: dict, dash: str) -> str:
    e = html.escape
    q = cfg["quote"]
    naik = r["kelas"] == "naik"
    skor = r["skor_naik"] if naik else r["skor_turun"]
    rank = f" · #{r['rank']} CMC" if r.get("rank") else ""
    head = [f"{'🟢' if naik else '🔴'} <b>{e(r['base'])}/{q}</b>{rank} · Skor {'naik' if naik else 'turun'} "
            f"<b>{skor}</b>/100",
            f"💰 {fmt_price(r['price'])} | 24j {fmt_pct(r['chg24'])} | 7h {fmt_pct(r['chg7'])}"]
    opsional = []   # (prioritas, indeks sisip, teks) — prioritas besar dibuang lebih dulu bila caption kepanjangan
    sk = r.get("siklus") or {}
    if sk.get("stage"):
        head.append(f"🔄 Siklus: {sk['ikon']} <b>{e(sk['nama'])}</b> — {e(sk['teks'])}"
                    + (f" (MA{sk['ma_n']} {e(sk['ma_arah'])})" if sk.get("ma_arah") else ""))
        if sk.get("saran"):
            opsional.append((3, len(head), f"💡 {e(sk['saran'])}"))
        fb = sk.get("fib")
        if fb:
            opsional.append((2, len(head), f"🧭 Fibonacci 0,382–0,618: {fmt_price(fb['f618'])}–{fmt_price(fb['f382'])} "
                                           f"— harga {e(fb['teks'])}"))
    P = r["pola_naik" if naik else "pola_turun"]
    if P:
        head.append(f"📐 {e(P['nama'])} — {e(P['status_teks'])}")
    t, b = r["target"], r["batal"]
    if t:
        head.append(f"🎯 Potensi {'naik' if naik else 'turun'} <b>{fmt_pct(t['pct'])}</b> → {fmt_price(t['harga'])} "
                    f"({e(t['sumber'])})")
    if b:
        head.append(f"🛑 Batal jika {'<' if naik else '>'} {fmt_price(b['harga'])} ({fmt_pct(b['pct'])}){_rr(r['rr'])}")
    rc = r.get("rencana")
    if rc:
        head.append(f"📋 Rencana: TP1 {fmt_price(rc['tp1'])} ({fmt_pct(rc['tp1_pct'])}, jual "
                    f"{rc['porsi_tp1'] * 100:.0f}%) · TP2 {fmt_price(rc['tp2'])} ({fmt_pct(rc['tp2_pct'])}) · "
                    f"SL {fmt_price(rc['sl'])} ({fmt_pct(rc['sl_pct'])})")
        if rc.get("posisi_rp"):
            head.append(f"💼 Ukuran posisi ±Rp{rc['posisi_rp']:,.0f} (rugi maks ±Rp{rc['risiko_rp']:,.0f} bila kena SL)"
                        .replace(",", "."))
    el = r.get("elliott")
    if el and el["arah"] == r["kelas"]:
        head.append(f"🌊 {e(el['teks'])} → {fmt_price(el['target'])} ({fmt_pct(el['pct'])})")
    z = r["akumulasi"]["zona"]
    if z:
        head.append(f"🧲 Zona akumulasi {fmt_price(z['val'])}–{fmt_price(z['vah'])} · harga "
                    f"{POSISI.get(r['akumulasi']['posisi'], '-')}")
    ind = r["indikator"]
    rsi = f"{ind['rsi']:.0f}" if ind["rsi"] is not None else "-"
    stk = f"{ind['stoch_k']:.0f}" if ind["stoch_k"] is not None else "-"
    head.append(f"📊 RSI {rsi} · Stoch {stk} · MACD {e(ind['macd_status'])}"
                + (" · BB squeeze" if ind["bb_squeeze"] else ""))
    vo = sk.get("volume") or {}
    if vo.get("status") not in (None, "-", "normal"):
        head.append(f"🔊 Volume: {e(vo['teks'])}")
    ck = r.get("checklist")
    if ck:
        head.append(f"☑️ Checklist {ck['cocok']}/6: {e(ck['teks'])}")
    for _, i, teks in sorted(opsional, key=lambda x: -x[1]):
        head.insert(i, teks)
    alasan = r["alasan_naik" if naik else "alasan_turun"]
    links = []
    if r.get("link"):
        links.append(f'<a href="{e(r["link"])}">TradingView</a>')
    if dash:
        links.append(f'<a href="{e(dash)}">Dashboard</a>')
    tail = [" · ".join(links)] if links else []
    buang = [x for p in ("📊", "🧲", "🌊") for x in head if x.startswith(p)]
    buang += [t for _, _, t in sorted(opsional, key=lambda x: -x[0])]
    def susun(k):
        return "\n".join(head + (["✅ Alasan:"] + [f"• {e(a)}" for a in alasan[:k]] if k else []) + tail)
    while True:   # utamakan ≥3 alasan; buang baris tambahan dulu, baru kurangi alasan
        k_min = 0 if not buang else min(3, len(alasan))
        for k in range(min(5, len(alasan)), k_min - 1, -1):
            if len(susun(k)) <= 1020:
                return susun(k)
        if not buang:
            return "\n".join(head[:2] + tail)
        head.remove(buang.pop(0))


def caption_stage2(r: dict, cfg: dict, dash: str) -> str:
    """Alert 🟩 awal Stage 2 (lolos backtest: BTC tren naik, bukan meme, rencana TP1 5%/TP2 10%/SL 12%)."""
    e = html.escape
    q = cfg["quote"]
    sk, rc, ck = r.get("siklus") or {}, r["stage2"]["rencana"], r.get("checklist")
    dari = {1: "Stage 1 Dasar", 3: "Stage 3 Puncak", 4: "Stage 4 Turun"}.get(sk.get("sebelum"), "stage sebelumnya")
    rank = f" · #{r['rank']} CMC" if r.get("rank") else ""
    L = [f"🟩 <b>AWAL STAGE 2 · {e(r['base'])}/{q}</b>{rank}",
         f"💰 {fmt_price(r['price'])} | 24j {fmt_pct(r['chg24'])} | 7h {fmt_pct(r['chg7'])} | 30h {fmt_pct(r['chg30'])}",
         f"🔄 Hari ini resmi masuk <b>Stage 2 · Naik</b> (dari {dari}). MA{sk.get('ma_n', 200)} {e(sk.get('ma_arah', '-'))}, "
         f"harga {fmt_pct(sk.get('jarak_ma'))} dari MA.",
         f"📋 Rencana: TP1 {fmt_price(rc['tp1'])} ({fmt_pct(rc['tp1_pct'])}, jual {rc['porsi_tp1'] * 100:.0f}%) · "
         f"TP2 {fmt_price(rc['tp2'])} ({fmt_pct(rc['tp2_pct'])}) · SL {fmt_price(rc['sl'])} ({fmt_pct(rc['sl_pct'])}) · "
         f"maks {rc['maks_hari']} hari"]
    if rc.get("posisi_rp"):
        L.append(f"💼 Ukuran posisi ±Rp{rc['posisi_rp']:,.0f} (rugi maks ±Rp{rc['risiko_rp']:,.0f})".replace(",", "."))
    vo = sk.get("volume") or {}
    if vo.get("teks"):
        L.append(f"🔊 {e(vo['teks'])}")
    fb = sk.get("fib")
    if fb:
        L.append(f"🧭 Kalau mau menunggu pullback: zona Fibonacci {fmt_price(fb['f618'])}–{fmt_price(fb['f382'])}")
    if ck:
        L.append(f"☑️ Checklist {ck['cocok']}/6: {e(ck['teks'])}")
    L.append("📈 <i>" + e(r["stage2"].get("uji") or
                          "Backtest Okt 2024–Okt 2026 (BTC tren naik, bukan meme): 260 sinyal, menang 81%, "
                          "rata-rata bersih +1,85%; lebih baik ±1% dari beli acak di minggu yang sama.") + "</i>")
    links = []
    if r.get("link"):
        links.append(f'<a href="{e(r["link"])}">TradingView</a>')
    if dash:
        links.append(f'<a href="{e(dash)}">Dashboard</a>')
    if links:
        L.append(" · ".join(links))
    while len("\n".join(L)) > 1020 and len(L) > 4:
        L.pop(-2 if not links else -3)
    return "\n".join(L)


def caption_short(r: dict, cfg: dict, dash: str) -> str:
    """Alert 🔻 SHORT: Stage 4, harga memantul ke Fibonacci 0,382–0,618 lalu candle merah (lolos backtest)."""
    e = html.escape
    q = cfg["quote"]
    sk, rc, ck = r.get("siklus") or {}, r["short"]["rencana"], r.get("checklist_short")
    sf = sk.get("short_fib") or {}
    lev = cfg.get("short_leverage_maks", 2)
    rank = f" · #{r['rank']} CMC" if r.get("rank") else ""
    L = [f"🔻 <b>JUAL DULU (SHORT) · {e(r['base'])}/{q}</b>{rank}",
         f"💰 {fmt_price(r['price'])} | 24j {fmt_pct(r['chg24'])} | 7h {fmt_pct(r['chg7'])} | 30h {fmt_pct(r['chg30'])}",
         f"🔄 <b>Stage 4 · Turun</b>: harga memantul ke zona Fibonacci {fmt_price(sf.get('f382'))}–{fmt_price(sf.get('f618'))} "
         f"(dari turun {fmt_price(sf.get('swing_high'))} → {fmt_price(sf.get('swing_low'))}) lalu candle merah.",
         f"📋 <b>JUAL di ±{fmt_price(rc['entry'])}</b>, lalu beli kembali di bawah:",
         f"   ✅ Beli kembali {rc['porsi_tp1'] * 100:.0f}% di {fmt_price(rc['tp1'])} ({fmt_pct(rc['tp1_pct'])}), "
         f"lalu batas rugi pindah ke harga jual",
         f"   ✅ Beli kembali sisanya di {fmt_price(rc['tp2'])} ({fmt_pct(rc['tp2_pct'])})",
         f"   🛑 Kalau malah naik ke {fmt_price(rc['sl'])} ({fmt_pct(rc['sl_pct'])}) → beli kembali (cut loss) · "
         f"maks {rc['maks_hari']} hari"]
    if rc.get("posisi_rp"):
        L.append(f"💼 Ukuran posisi ±Rp{rc['posisi_rp']:,.0f} (rugi maks ±Rp{rc['risiko_rp']:,.0f})".replace(",", "."))
    L.append(f"⚠️ Leverage maks {lev}× (SL {fmt_pct(rc['sl_pct'])} × {lev} = rugi ±{abs(rc['sl_pct']) * lev:.0f}% margin). Wajib pasang SL.")
    vo = sk.get("volume") or {}
    if vo.get("teks"):
        L.append(f"🔊 {e(vo['teks'])}")
    if ck:
        L.append(f"☑️ Checklist short {ck['cocok']}/6: {e(ck['teks'])}")
    L.append("📈 <i>" + e(r["short"].get("uji") or
                          "Backtest 2020–2026 (BTC tidak tren naik, bukan meme): 225 sinyal, menang 87%, rata-rata bersih "
                          "+2,65%; di luar crash Okt 2025 ±+1,5%.") + " Biaya, pajak & funding sudah dihitung.</i>")
    links = []
    if r.get("link"):
        links.append(f'<a href="{e(r["link"])}">TradingView</a>')
    if dash:
        links.append(f'<a href="{e(dash)}">Dashboard</a>')
    if links:
        L.append(" · ".join(links))
    while len("\n".join(L)) > 1020 and len(L) > 8:
        L.pop(-2 if links else -1)
    return "\n".join(L)


REZIM_IKON = {"naik": "📈 NAIK", "turun": "📉 TURUN", "netral": "➖ SIDEWAYS"}


def kondisi_pasar(results, r_btc) -> dict | None:
    """Skor pasar −6…+6 dari candle harian tutup (BTC + lebar pasar semua koin yang dianalisa)."""
    if not r_btc:
        return None
    try:
        koin = [dict(base=r["base"], close=r["_g"]["dc"]["close"].to_numpy(dtype=float),
                     stage=(r.get("siklus") or {}).get("stage")) for r in results]
        return PS.sekarang(r_btc["_g"]["dc"]["close"].to_numpy(dtype=float), koin)
    except Exception as e:
        print(f"  ! kondisi pasar gagal dihitung: {e}")
        return None


def teks_kondisi(kp: dict | None) -> str | None:
    if not kp:
        return None
    return f"🌡️ Kondisi pasar: {kp['ikon']} <b>{html.escape(kp['nama'])}</b> (skor {PS.angka(kp['skor'])} dari ±6)"


def teks_komponen(kp: dict) -> list[str]:
    ik = {1: "🟢", 0: "⚪", -1: "🔴"}
    return [f"   {ik[k['suara']]} {html.escape(k['nama'])}: {html.escape(k['teks'])}" for k in kp["komponen"]]


def teks_model(model: dict | None, kp: dict | None, pakai: bool) -> list[str]:
    """Baris 'apa yang boleh jalan sekarang' menurut model pasar."""
    if not (pakai and model and kp):
        return []
    st = PS.status(model, kp)
    f = lambda x: "✅ aktif" if x[0] else f"⏸ ditahan ({x[1]})"  # noqa: E731
    return [f"🟢 Beli: {f(st['beli'])}", f"🔻 Jual dulu: {f(st['jual'])}"]


def uji_teks(model: dict | None, strategi: str) -> str | None:
    """Kalimat hasil uji strategi pada kondisi pasar yang diizinkan model (dari model.json)."""
    a = ((model or {}).get("strategi") or {}).get(strategi) or {}
    if not a.get("aktif") or not a.get("n"):
        return None
    g = model["beli" if a["sisi"] == "long" else "jual"]
    angka = f"{a['n']} sinyal, menang {a['menang']:.0f}%, rata-rata bersih {a['rata']:+.2f}%".replace(".", ",")
    return f"Uji {model['data'][:4]}–{model['data'][-10:-6]} saat {g['teks']}: {angka}."


def peta_siklus(results) -> dict:
    """Jumlah koin per stage + koin yang baru tembus dasar / baru jebol puncak."""
    n = {k: 0 for k in (1, 2, 3, 4)}
    for r in results:
        st = (r.get("siklus") or {}).get("stage")
        if st in n:
            n[st] += 1
    urut = sorted(results, key=lambda r: r.get("rank") or 9999)
    fase = lambda f: [r["base"] for r in urut if (r.get("siklus") or {}).get("fase") == f]  # noqa: E731
    tot = sum(n.values()) or 1
    return dict(jumlah={str(k): v for k, v in n.items()}, persen_naik=round(n[2] / tot * 100),
                persen_turun=round(n[4] / tot * 100), tembus_dasar=fase("1→2"), siap_tembus=fase("1-akhir"),
                jebol_puncak=fase("3→4"))


def teks_peta(ps: dict) -> str:
    j = ps["jumlah"]
    return (f"🔄 Peta siklus: 🟦 Dasar {j['1']} · 🟩 Naik {j['2']} · 🟨 Puncak {j['3']} · 🟥 Turun {j['4']}")


def teks_btc_stage(r_btc) -> str | None:
    sk = (r_btc or {}).get("siklus") or {}
    if not sk.get("stage"):
        return None
    return f"BTC: {sk['ikon']} <b>{html.escape(sk['nama'])}</b> — {html.escape(sk['teks'])}"


def header_text(naik, turun, n_scan, src_rank, src_bursa, now, dash, rz=None, tertahan=0, ps=None, btc_st=None,
                kp=None, model_baris=None) -> str:
    lines = [f"📡 <b>Radar Kripto</b> · {now_wib_str(now)}",
             f"Top {n_scan} koin ({html.escape(src_rank)}) · data {html.escape(src_bursa)}"]
    if kp:
        lines.append(teks_kondisi(kp))
        if model_baris:
            lines.append(html.escape(" · ".join(model_baris)))
    if rz:
        lines.append(f"Pasar BTC: <b>{REZIM_IKON.get(rz['rezim'], rz['rezim'])}</b> ({html.escape(rz['teks'])})")
    if btc_st:
        lines.append(btc_st)
    if ps:
        lines.append(teks_peta(ps))
    lines.append(f"🟢 Potensi naik: <b>{len(naik)}</b> · 🔴 Potensi turun: <b>{len(turun)}</b>"
                 + (f" · ⏸ ditahan filter: {tertahan}" if tertahan else ""))
    if dash:
        lines.append(f'📊 <a href="{html.escape(dash)}">Buka dashboard lengkap</a>')
    lines.append("<i>Target = proyeksi pola grafik, bukan jaminan. Bukan ajakan beli/jual.</i>")
    return "\n".join(lines)


def baris_ringkas(r: dict) -> str:
    t = r["target"]
    P = r["pola_naik" if r["kelas"] == "naik" else "pola_turun"]
    pola = f" {html.escape(P['nama'])}" if P else ""
    skor = r["skor_naik"] if r["kelas"] == "naik" else r["skor_turun"]
    sk = r.get("siklus") or {}
    st = f" · {sk['ikon']}S{sk['stage']}" if sk.get("stage") else ""
    return (f"• <b>{html.escape(r['base'])}</b> (#{r['rank']}) skor {skor}{st}{pola}"
            + (f" → {fmt_pct(t['pct'])}" if t else ""))


def summary_text(results, now, src_rank, dash, rk=None, rz=None, ps=None, btc_st=None, stage2=None,
                 shorts=None, kand_short=None, kp=None, model_baris=None) -> str:
    w = now.astimezone(WIB)
    naik = sorted([r for r in results if r["kelas"] == "naik"], key=lambda r: -r["skor_naik"])
    turun = sorted([r for r in results if r["kelas"] == "turun"], key=lambda r: -r["skor_turun"])
    lines = [f"📋 <b>Ringkasan Harian Radar Kripto</b> — {w.day} {BULAN[w.month - 1]} {w.year}",
             f"{len(results)} koin top ({html.escape(src_rank)}) dianalisa."]
    if kp:
        lines.append(teks_kondisi(kp))
        lines += teks_komponen(kp)
        lines += [html.escape(x) for x in (model_baris or [])]
    if rz:
        lines.append(f"Pasar BTC: <b>{REZIM_IKON.get(rz['rezim'], rz['rezim'])}</b> ({html.escape(rz['teks'])})")
    if btc_st:
        lines.append(btc_st)
    if ps:
        lines.append(teks_peta(ps) + f" (naik {ps['persen_naik']}% · turun {ps['persen_turun']}%)")
        for label, key in (("🟦→🟩 Baru tembus dari dasar", "tembus_dasar"), ("🟦 Akhir dasar, siap tembus", "siap_tembus"),
                           ("🟨→🟥 Baru jebol dari puncak", "jebol_puncak")):
            xs = ps.get(key) or []
            if xs:
                lines.append(f"{label} ({len(xs)}): " + html.escape(", ".join(xs[:12])) + ("…" if len(xs) > 12 else ""))
    lines.append(f"\n🟢 <b>Potensi naik ({len(naik)})</b>")
    lines += [baris_ringkas(r) for r in naik[:10]] or ["• (belum ada)"]
    lines.append(f"\n🔴 <b>Potensi turun ({len(turun)})</b>")
    lines += [baris_ringkas(r) for r in turun[:10]] or ["• (belum ada)"]
    if stage2 is not None:
        lolos = [r for r in stage2 if not r["stage2"]["ditahan"]]
        lines.append(f"\n🟩 <b>Awal Stage 2 hari ini ({len(lolos)})</b>")
        lines += [f"• <b>{html.escape(r['base'])}</b> (#{r['rank']}) {fmt_price(r['price'])}" for r in lolos[:10]] or [
            "• (belum ada" + (f"; {len(stage2)} koin ditahan filter pasar)" if stage2 else ")")]
    if shorts is not None:
        lolos = [r for r in shorts if not r["short"]["ditahan"]]
        lines.append(f"\n🔻 <b>Sinyal short hari ini ({len(lolos)})</b>")
        lines += [f"• <b>{html.escape(r['base'])}</b> (#{r['rank']}) {fmt_price(r['price'])} · TP1 "
                  f"{fmt_price(r['short']['rencana']['tp1'])} · SL {fmt_price(r['short']['rencana']['sl'])}"
                  for r in lolos[:10]] or [
            "• (belum ada" + (f"; {len(shorts)} koin ditahan filter pasar)" if shorts else ")")]
        if kand_short:
            lines.append(f"⏳ Kandidat short, tunggu candle harian merah ({len(kand_short)}): "
                         + html.escape(", ".join(r["base"] for r in kand_short[:15])) + ("…" if len(kand_short) > 15 else ""))
    rt = rekam.rekap_teks(rk or {})
    if rt:
        lines.append(f"\n📈 <b>Rekam jejak {rk['hari']} hari</b>")
        lines += [html.escape(x) for x in rt]
    if dash:
        lines.append(f'\n📊 <a href="{html.escape(dash)}">Dashboard lengkap</a>')
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

    def send_photo(self, png: bytes, cap: str) -> None:
        if not self.enabled:
            print("\n--- [grafik + caption] ---\n" + cap)
            return
        for chat in self.chats:
            self._post("sendPhoto", {"chat_id": chat, "caption": cap, "parse_mode": "HTML"},
                       files={"photo": ("radar.png", png, "image/png")})


# --------------------------------------------------------------------------- #
# State (anti alert dobel)
# --------------------------------------------------------------------------- #
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                s = json.load(f)
            s.setdefault("alerts2", {})
            return s
        except (OSError, ValueError):
            pass
    return {"alerts2": {}}


def save_state(state: dict) -> None:
    state.pop("alerts", None)  # format lama
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def perlu_alert(r: dict, state: dict, cfg: dict, now: datetime) -> bool:
    key = f"{r['symbol']}|{r['kelas']}"
    prev = state["alerts2"].get(key)
    if not prev:
        return True
    age = (now - datetime.fromisoformat(prev["ts"])).total_seconds() / 3600
    if age >= cfg["cooldown_jam"]:
        return True
    skor = r["skor_naik"] if r["kelas"] == "naik" else r["skor_turun"]
    P = r["pola_naik" if r["kelas"] == "naik" else "pola_turun"]
    breakout_baru = P is not None and P["status"] == "breakout" and prev.get("status") != "breakout"
    return skor >= prev.get("skor", 0) + 10 or breakout_baru


# --------------------------------------------------------------------------- #
# Dashboard (GitHub Pages)
# --------------------------------------------------------------------------- #
def url_dashboard(cfg: dict) -> str:
    if cfg.get("url_dashboard"):
        return str(cfg["url_dashboard"])
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner.lower()}.github.io/{name}/"
    return ""


def tulis_dashboard(results, charts: dict[str, bytes], meta: dict) -> None:
    if os.path.isdir(SITE_DIR):
        shutil.rmtree(SITE_DIR)
    os.makedirs(os.path.join(SITE_DIR, "charts"))
    tpl = os.path.join(ROOT, "dashboard.html")
    if os.path.exists(tpl):
        shutil.copy(tpl, os.path.join(SITE_DIR, "index.html"))
    koin = []
    for r in results:
        x = {k: v for k, v in r.items() if not k.startswith("_")}
        png = charts.get(r["symbol"])
        if png:
            fn = f"charts/{r['base']}.png"
            with open(os.path.join(SITE_DIR, fn), "wb") as f:
                f.write(png)
            x["chart"] = fn
        else:
            x["chart"] = None
        koin.append(x)
    data = dict(meta, koin=koin)
    bt = os.path.join(ROOT, "backtest", "hasil.json")
    if os.path.exists(bt):
        shutil.copy(bt, os.path.join(SITE_DIR, "backtest.json"))
        data["ada_backtest"] = True
    mpj = os.path.join(ROOT, "model_pasar", "hasil.json")
    if os.path.exists(mpj):
        shutil.copy(mpj, os.path.join(SITE_DIR, "model_pasar.json"))
        data["ada_model_pasar"] = True
    s4 = os.path.join(ROOT, "siklus4")
    if os.path.exists(os.path.join(s4, "hasil.json")):
        os.makedirs(os.path.join(SITE_DIR, "siklus4"), exist_ok=True)
        for fn in ("hasil.json", "grafik.png", "perbandingan.png"):
            if os.path.exists(os.path.join(s4, fn)):
                shutil.copy(os.path.join(s4, fn), os.path.join(SITE_DIR, "siklus4", fn))
        data["ada_siklus4"] = True
    with open(os.path.join(SITE_DIR, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    with open(os.path.join(SITE_DIR, ".nojekyll"), "w") as f:
        f.write("")


def write_step_summary(results, meta, path) -> None:
    def tabel(rows, kelas):
        out = ["| # CMC | Koin | Skor | Stage | Pola | Target | Batal | RSI | Zona |", "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            P = r["pola_naik" if kelas == "naik" else "pola_turun"]
            skor = r["skor_naik"] if kelas == "naik" else r["skor_turun"]
            t, b = r["target"], r["batal"]
            sk = r.get("siklus") or {}
            out.append(f"| {r['rank']} | {r['base']} | {skor} | {sk.get('fase', '-')} | {P['nama'] if P else '-'} | "
                       f"{fmt_pct(t['pct']) if t else '-'} | {fmt_pct(b['pct']) if b else '-'} | "
                       f"{r['indikator']['rsi'] if r['indikator']['rsi'] is not None else '-'} | "
                       f"{r['akumulasi']['posisi']} |")
        return out
    naik = sorted([r for r in results if r["kelas"] == "naik"], key=lambda r: -r["skor_naik"])
    turun = sorted([r for r in results if r["kelas"] == "turun"], key=lambda r: -r["skor_turun"])
    lines = [f"## Radar Kripto — {meta['updated_wib']}", "",
             f"Pasar BTC: {meta.get('pasar', {}).get('rezim', '-')} ({meta.get('pasar', {}).get('teks', '')}) · "
             f"ditahan filter: {meta.get('tertahan', 0)}", "",
             teks_peta(meta["siklus"]) if meta.get("siklus") else "", "",
             f"Ranking: {meta['sumber_ranking']} · Data: {meta['sumber_harga']} · Dianalisa: {len(results)}", ""]
    if meta.get("dashboard"):
        lines += [f"Dashboard: {meta['dashboard']}", ""]
    lines += [f"### 🟢 Potensi naik ({len(naik)})", ""] + tabel(naik, "naik")
    lines += ["", f"### 🔴 Potensi turun ({len(turun)})", ""] + tabel(turun, "turun")
    riw = meta.get("riwayat") or []
    if riw:
        lines += ["", "### 📈 Rekam jejak alert", ""] + [f"- {x}" for x in rekam.rekap_teks(meta.get("rekap7", {}))]
        lines += ["", "| Waktu alert (UTC) | Koin | Arah | Harga alert | Sekarang | Perubahan | Tertinggi | Terendah | Hasil |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for e in riw[:40]:
            lines.append(f"| {e['ts'][:16].replace('T', ' ')} | {e['base']} | {e['kelas']} | {fmt_price(e['harga'])} | "
                         f"{fmt_price(e['harga_now'])} | {fmt_pct(e['chg'])} | {fmt_pct(e['maks_pct'])} | "
                         f"{fmt_pct(e['min_pct'])} | {e['hasil']} |")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# --------------------------------------------------------------------------- #
# Jalankan
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Radar Kripto")
    ap.add_argument("--mode", default="normal", choices=["normal", "demo", "tes-telegram", "ringkasan"])
    args = ap.parse_args()
    cfg = load_config()
    tg = Telegram.from_env()
    now = datetime.now(timezone.utc)
    demo = args.mode == "demo"
    dash = url_dashboard(cfg)

    if args.mode == "tes-telegram":
        if not tg.enabled:
            print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diisi di GitHub Secrets.")
            return 1
        tg.send_text(f"✅ <b>Radar Kripto tersambung!</b>\n{now_wib_str(now)}")
        print("Pesan tes terkirim.")
        return 0

    state = load_state()
    t0 = time.time()
    try:
        if demo:
            dsrc = DemoSource()
            rank_list, src_rank = dsrc.ranking(), "DEMO"
        else:
            dsrc = None
            rank_list, src_rank = ambil_ranking(cfg, state, now)
        uni, tidak_ada, bursa = bangun_universe(rank_list, cfg, dsrc)
    except SourceError as e:
        msg = f"⚠️ <b>Radar Kripto gagal mengambil data</b>\n{html.escape(str(e))[:600]}"
        last = state.get("last_error_notice")
        if not last or (now - datetime.fromisoformat(last)).total_seconds() > 6 * 3600:
            tg.send_text(msg)
            state["last_error_notice"] = now.isoformat(timespec="seconds")
            save_state(state)
        print(msg)
        return 1

    src_harga = " + ".join(bursa)
    print(f"Ranking: {src_rank} · {len(uni)} koin akan dianalisa (tidak ada di bursa: {len(tidak_ada)})")
    results, failed = scan(uni, cfg)
    print(f"Selesai {time.time() - t0:.0f} dtk · dianalisa {len(results)} · gagal {len(failed)}")

    # Rekam jejak: lengkapi alert lama (sekali) lalu perbarui hasil semua alert yang berjalan
    res_map = {r["symbol"]: r for r in results}
    if not demo:
        n_isi = rekam.isi_ulang(state, res_map, {u["symbol"]: u["_src"] for u in uni})
        if n_isi:
            print(f"Rekam jejak: {n_isi} alert lama dilengkapi harga historis")
    # Kondisi pasar dari BTC, rencana jual & filter sinyal
    r_btc = res_map.get("BTCUSDT") or res_map.get("BTC-USDT")
    rz = (ST.rezim_pasar(r_btc["_g"]["dc"]["close"].to_numpy(), price=r_btc["price"]) if r_btc
          else dict(rezim="netral", harga=None, ma=None, teks="data BTC tidak tersedia"))
    R = ST.cfg_rencana(cfg)
    # Model kondisi pasar: skor pasar harian menentukan strategi mana yang boleh jalan (lihat pasar.py)
    kp = kondisi_pasar(results, r_btc)
    model = PS.muat_model()
    mp = str(cfg.get("model_pasar", "auto")).lower()
    pakai_model = bool(kp and model and model.get("versi") == 2
                       and (mp == "true" or (mp == "auto" and model.get("pakai"))))
    tertahan = 0
    for r in results:
        arah = r["arah_utama"]
        t, b = r.get("target"), r.get("batal")
        r["rencana"] = ST.rencana(float(r["price"]), arah, t["harga"] if t else None, b["harga"] if b else None,
                                  r["indikator"].get("atr_pct"), R)
        k, alasan = ST.filter_sinyal(r, cfg, rz["rezim"])
        if pakai_model and not alasan and k == "naik":      # aturan lama lolos → cek batas skor pasar dari model
            ok, why = PS.izin(model, "radar_naik", kp)
            if not ok:
                k, alasan = "pantau-naik", "ditahan: " + why
        if alasan:
            r["kelas"], r["ditahan"] = k, alasan
            tertahan += 1
    print(f"Pasar BTC: {rz['rezim']} ({rz['teks']}) · {tertahan} sinyal ditahan filter")
    model_baris = teks_model(model, kp, pakai_model)
    if kp:
        print(f"Kondisi pasar: skor {PS.angka(kp['skor'])} ({kp['nama']}) · model pasar {'AKTIF' if pakai_model else 'tidak dipakai'}"
              + "".join(" · " + x for x in model_baris))
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::notice title=Kondisi pasar::skor {PS.angka(kp['skor'])} ({kp['nama']}) · "
                  + " · ".join(f"{k['nama']} {k['suara']:+d}" for k in kp["komponen"])
                  + f" · model {'aktif' if pakai_model else 'tidak dipakai'}" + "".join(" · " + x for x in model_baris))
    ps = peta_siklus(results)
    btc_st = teks_btc_stage(r_btc)
    # Sinyal 🟩 awal Stage 2 (hari pertama Stage 2 terkonfirmasi pada candle harian terakhir)
    stage2 = []
    if cfg.get("sinyal_stage2", True):
        for r in results:
            sk = r.get("siklus") or {}
            if not sk.get("baru_stage2") or r.get("meme"):
                continue
            plan = ST.rencana(float(r["price"]), "naik", None, None, r["indikator"].get("atr_pct"), R)
            plan.update(ST.ukuran_posisi(plan, cfg))
            fp = str(cfg.get("stage2_filter_pasar", "ketat")).lower()
            ditahan = None
            if fp == "ketat" and rz["rezim"] != "naik":
                ditahan = "ditahan: pasar BTC tidak sedang tren naik"
            elif fp in ("true", "longgar") and rz["rezim"] == "turun":
                ditahan = "ditahan: pasar BTC sedang tren turun"
            if pakai_model and not ditahan:
                ok, why = PS.izin(model, "awal_stage2", kp)
                ditahan = None if ok else "ditahan: " + why
            tgl = str(r["_g"]["dc"]["time"].iloc[-1])[:10]
            r["stage2"] = dict(rencana=plan, ditahan=ditahan, tanggal=tgl,
                               uji=uji_teks(model, "awal_stage2") if pakai_model else None)
            stage2.append(r)
        stage2.sort(key=lambda r: r.get("rank") or 9999)
        print(f"Awal Stage 2: {len(stage2)} koin ({sum(1 for r in stage2 if not r['stage2']['ditahan'])} lolos filter pasar)")
    # Sinyal 🔻 SHORT: Stage 4, memantul ke Fibonacci 0,382–0,618 lalu candle merah (candle harian terakhir)
    shorts = []
    if cfg.get("sinyal_short", True):
        for r in results:
            sf = (r.get("siklus") or {}).get("short_fib")
            if not sf or r.get("meme"):
                continue
            plan = ST.rencana(float(r["price"]), "turun", sf["target"], sf["batal"], r["indikator"].get("atr_pct"), R)
            plan.update(ST.ukuran_posisi(plan, cfg))
            fp = str(cfg.get("short_filter_pasar", "longgar")).lower()
            ditahan = None
            if fp == "ketat" and rz["rezim"] != "turun":
                ditahan = "ditahan: pasar BTC tidak sedang tren turun"
            elif fp in ("true", "longgar") and rz["rezim"] == "naik":
                ditahan = "ditahan: pasar BTC sedang tren naik"
            if pakai_model and not ditahan:
                ok, why = PS.izin(model, "pantul_fib", kp)
                ditahan = None if ok else "ditahan: " + why
            tgl = str(r["_g"]["dc"]["time"].iloc[-1])[:10]
            r["short"] = dict(rencana=plan, ditahan=ditahan, tanggal=tgl,
                              uji=uji_teks(model, "pantul_fib") if pakai_model else None)
            shorts.append(r)
        shorts.sort(key=lambda r: r.get("rank") or 9999)
        print(f"Sinyal short: {len(shorts)} koin ({sum(1 for r in shorts if not r['short']['ditahan'])} lolos filter pasar)")
    kand_short = sorted([r for r in results if (r.get("siklus") or {}).get("short_kandidat") and not r.get("meme")],
                        key=lambda r: r.get("rank") or 9999)
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::notice title=Short::sinyal {', '.join(r['base'] for r in shorts) or '-'} · kandidat (tunggu candle merah): "
              f"{', '.join(r['base'] for r in kand_short[:25]) or '-'}")
    if not demo:
        state["short_kandidat"] = dict(ts=now.isoformat(timespec="seconds"),
                                       sinyal=[r["base"] for r in shorts], kandidat=[r["base"] for r in kand_short])
    print(teks_peta(ps))
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::notice title=Siklus 4 stage::{teks_peta(ps)} · BTC {((r_btc or {}).get('siklus') or {}).get('nama', '-')}"
              f" · tembus dasar: {', '.join(ps['tembus_dasar'][:15]) or '-'} · siap tembus: {', '.join(ps['siap_tembus'][:15]) or '-'}")
    if not demo:
        bs = (r_btc or {}).get("siklus") or {}
        state["siklus"] = dict(ps, btc=dict(stage=bs.get("stage"), fase=bs.get("fase"), teks=bs.get("teks")),
                               ts=now.isoformat(timespec="seconds"))
    if not demo:
        # Koin di rekam jejak yang tidak ikut dianalisa (mis. keluar dari top 200) tetap dipantau
        srcs = {u["_src"].name: u["_src"] for u in uni}
        for e in state.get("riwayat", []):
            sym = e["symbol"]
            if sym in res_map or (e.get("hasil") != "berjalan" and e.get("hasil_rencana") not in ("berjalan", None)):
                continue
            src = srcs.get(e.get("bursa")) or (Binance() if e.get("bursa") == "Binance" else OKX())
            try:
                hh = src.candles(sym, "1h", 24 * 35)
                res_map[sym] = dict(symbol=sym, base=e["base"], bursa=e.get("bursa"), rank=e.get("rank"),
                                    price=float(hh["close"].iloc[-1]), _h=hh)
            except Exception as ex:
                print(f"  ! pantau {sym} gagal: {ex}")
    state["pasar"] = dict(rz, ts=now.isoformat(timespec="seconds"))
    if kp and not demo:
        state["kondisi_pasar"] = dict(skor=kp["skor"], kode=kp["kode"], nama=kp["nama"], model_aktif=pakai_model,
                                      komponen={k["kode"]: k["suara"] for k in kp["komponen"]}, nilai=kp["nilai"],
                                      ts=now.isoformat(timespec="seconds"))
    for r in results:
        if r.get("rencana"):
            r["rencana"].update(ST.ukuran_posisi(r["rencana"], cfg))
    btc_src = next((u["_src"] for u in uni if u["symbol"] in ("BTCUSDT", "BTC-USDT")), None)
    rekam.perbarui(state, res_map, now, cfg, r_btc, btc_src)

    naik = sorted([r for r in results if r["kelas"] == "naik"], key=lambda r: -r["skor_naik"])
    turun = sorted([r for r in results if r["kelas"] == "turun"], key=lambda r: -r["skor_turun"])
    kandidat = naik + (turun if cfg["kirim_alert_turun"] else [])
    st2 = state.setdefault("stage2", {})
    jeda2 = timedelta(days=int(cfg.get("stage2_jeda_hari", 10)))
    alert2 = [r for r in stage2 if not r["stage2"]["ditahan"] and (demo or not (
        r["symbol"] in st2 and (st2[r["symbol"]].get("tanggal") == r["stage2"]["tanggal"]
                                or now - datetime.fromisoformat(st2[r["symbol"]]["ts"]) < jeda2)))]
    stS = state.setdefault("short", {})
    jedaS = timedelta(days=int(cfg.get("short_jeda_hari", 10)))
    alertS = [r for r in shorts if not r["short"]["ditahan"] and (demo or not (
        r["symbol"] in stS and (stS[r["symbol"]].get("tanggal") == r["short"]["tanggal"]
                                or now - datetime.fromisoformat(stS[r["symbol"]]["ts"]) < jedaS)))]
    alerts = kandidat if demo else [r for r in kandidat if perlu_alert(r, state, cfg, now)]

    # Grafik: semua koin naik/turun (untuk dashboard), dibatasi jumlahnya
    waktu = now_wib_str(now)
    charts: dict[str, bytes] = {}
    pantau = sorted([r for r in results if r["kelas"].startswith("pantau")],
                    key=lambda r: -max(r["skor_naik"], r["skor_turun"]))
    ekstra = [x for x in stage2 + shorts if x not in naik and x not in turun]
    for r in (naik + turun + list({id(x): x for x in ekstra}.values()) + pantau)[: int(cfg["maks_grafik_dashboard"])]:
        try:
            rg = r
            if r["kelas"] not in ("naik", "turun"):
                rg = dict(r, _chip="short") if r.get("short") else (dict(r, _chip="stage2") if r.get("stage2") else r)
            charts[r["symbol"]] = buat_grafik(rg, cfg["quote"], src_harga, waktu)
        except Exception as e:
            print(f"  ! grafik {r['base']} gagal: {e}")

    if alerts:
        tg.send_text(header_text(naik, turun, len(results), src_rank, src_harga, now, dash, rz, tertahan, ps, btc_st, kp,
                                 model_baris))
        maxg = int(cfg["maks_grafik_per_run"])
        for r in alerts[:maxg]:
            png = charts.get(r["symbol"]) or buat_grafik(r, cfg["quote"], src_harga, waktu)
            tg.send_photo(png, caption(r, cfg, dash))
        rest = alerts[maxg:]
        if rest:
            tg.send_text("Koin lain yang juga terdeteksi:\n" + "\n".join(baris_ringkas(r) for r in rest[:25]))
        for r in alerts:
            rekam.catat(state, r, now, r_btc)
        if not demo:
            for r in alerts:
                P = r["pola_naik" if r["kelas"] == "naik" else "pola_turun"]
                state["alerts2"][f"{r['symbol']}|{r['kelas']}"] = {
                    "ts": now.isoformat(timespec="seconds"),
                    "skor": r["skor_naik"] if r["kelas"] == "naik" else r["skor_turun"],
                    "status": P["status"] if P else None}
    elif kandidat:
        print(f"{len(kandidat)} koin masih memenuhi syarat, tapi sudah di-alert (cooldown {cfg['cooldown_jam']} jam).")
    else:
        print("Tidak ada koin yang memenuhi syarat pada putaran ini.")

    if alert2:
        tg.send_text(f"🟩 <b>Sinyal Awal Stage 2</b> · {now_wib_str(now)}\n"
                     f"{len(alert2)} koin hari ini resmi masuk tren naik (Stage 1 → 2) saat BTC "
                     f"{REZIM_IKON.get(rz['rezim'], rz['rezim'])}.\n"
                     + (f"{teks_kondisi(kp)}\n" if kp else "")
                     + (f"{btc_st}\n" if btc_st else "") + teks_peta(ps) +
                     "\n<i>Sinyal ini lolos uji historis, tapi bukan jaminan. Bukan ajakan beli/jual.</i>")
        m2 = int(cfg.get("stage2_maks_grafik", 5))
        for r in alert2[:m2]:
            png = charts.get(r["symbol"]) or buat_grafik(dict(r, _chip="stage2"), cfg["quote"], src_harga, waktu)
            tg.send_photo(png, caption_stage2(r, cfg, dash))
        if alert2[m2:]:
            tg.send_text("Koin lain yang juga baru masuk Stage 2:\n" + "\n".join(
                f"• <b>{html.escape(r['base'])}</b> (#{r['rank']}) {fmt_price(r['price'])} · TP1 "
                f"{fmt_price(r['stage2']['rencana']['tp1'])} · SL {fmt_price(r['stage2']['rencana']['sl'])}"
                for r in alert2[m2:m2 + 25]))
        for r in alert2:
            rc = r["stage2"]["rencana"]
            rek = dict(r, kelas="naik", pola_naik=None, rencana=rc,
                       target=dict(harga=rc["tp2"], pct=rc["tp2_pct"]), batal=dict(harga=rc["sl"], pct=rc["sl_pct"]))
            rekam.catat(state, rek, now, r_btc, jenis="stage2")
            if not demo:
                st2[r["symbol"]] = dict(tanggal=r["stage2"]["tanggal"], ts=now.isoformat(timespec="seconds"))
    st2_batas = now - timedelta(days=40)
    state["stage2"] = {k: v for k, v in st2.items() if datetime.fromisoformat(v["ts"]) >= st2_batas}

    if alertS:
        tg.send_text(f"🔻 <b>Sinyal SHORT</b> · {now_wib_str(now)}\n"
                     f"{len(alertS)} koin di Stage 4 (tren turun) baru memantul ke zona Fibonacci lalu melemah lagi. "
                     f"BTC {REZIM_IKON.get(rz['rezim'], rz['rezim'])}.\n"
                     + (f"{teks_kondisi(kp)}\n" if kp else "")
                     + (f"{btc_st}\n" if btc_st else "") +
                     "Jual dulu, beli kembali lebih murah. Punya koinnya → jual di spot. Tidak punya → buka posisi "
                     "short di futures (leverage rendah). Selalu pasang batas rugi.\n"
                     "<i>Lolos uji historis, tapi bukan jaminan. Bukan ajakan beli/jual.</i>")
        mS = int(cfg.get("short_maks_grafik", 5))
        for r in alertS[:mS]:
            png = charts.get(r["symbol"]) or buat_grafik(dict(r, _chip="short"), cfg["quote"], src_harga, waktu)
            tg.send_photo(png, caption_short(r, cfg, dash))
        if alertS[mS:]:
            tg.send_text("Koin lain dengan sinyal short:\n" + "\n".join(
                f"• <b>{html.escape(r['base'])}</b> (#{r['rank']}) {fmt_price(r['price'])} · TP1 "
                f"{fmt_price(r['short']['rencana']['tp1'])} · TP2 {fmt_price(r['short']['rencana']['tp2'])} · "
                f"SL {fmt_price(r['short']['rencana']['sl'])}" for r in alertS[mS:mS + 25]))
        for r in alertS:
            rc = r["short"]["rencana"]
            rek = dict(r, kelas="turun", pola_turun=None, rencana=rc,
                       target=dict(harga=rc["tp2"], pct=rc["tp2_pct"]), batal=dict(harga=rc["sl"], pct=rc["sl_pct"]))
            rekam.catat(state, rek, now, r_btc, jenis="short")
            if not demo:
                stS[r["symbol"]] = dict(tanggal=r["short"]["tanggal"], ts=now.isoformat(timespec="seconds"))
    state["short"] = {k: v for k, v in stS.items() if datetime.fromisoformat(v["ts"]) >= st2_batas}

    riw = sorted(state.get("riwayat", []), key=lambda e: e["ts"], reverse=True)
    rk = rekam.rekap(riw, now)
    if os.environ.get("GITHUB_ACTIONS"):
        for x in rekam.rekap_teks(rk):
            print(f"::notice title=Rekam jejak {rk['hari']} hari::{x}")

    w = now.astimezone(WIB)
    today = w.date().isoformat()
    if demo or args.mode == "ringkasan" or (w.hour >= int(cfg["ringkasan_harian_jam_wib"])
                                            and state.get("last_summary") != today):
        tg.send_text(summary_text(results, now, src_rank, dash, rk, rz, ps, btc_st,
                                  stage2 if cfg.get("sinyal_stage2", True) else None,
                                  shorts if cfg.get("sinyal_short", True) else None, kand_short, kp, model_baris))
        if not demo:
            state["last_summary"] = today

    meta = dict(updated=now.isoformat(timespec="seconds"), updated_wib=waktu, sumber_ranking=src_rank,
                sumber_harga=src_harga, jumlah=len(results), top_n=int(cfg["top_n"]),
                tidak_tersedia=tidak_ada, dashboard=dash, demo=demo,
                ambang=dict(skor_min=cfg["skor_min"], selisih_min=cfg["selisih_min"]),
                pasar=rz, tertahan=tertahan, siklus=ps, stage2_aktif=bool(cfg.get("sinyal_stage2", True)),
                short_aktif=bool(cfg.get("sinyal_short", True)), short_leverage=cfg.get("short_leverage_maks", 2),
                btc_siklus=(r_btc or {}).get("siklus"), kondisi_pasar=kp,
                model_pasar=dict(aktif=pakai_model, baris=model_baris, pengaturan=mp,
                                 putusan=model.get("putusan"), dibuat=model.get("dibuat_wib"),
                                 beli=model.get("beli"), jual=model.get("jual")) if model else None,
                filter=dict(pasar=cfg["filter_pasar"], meme=cfg["filter_meme"], breakout=cfg["wajib_breakout"],
                            min_rr=cfg["min_rr"], stage_naik=cfg["filter_stage_naik"],
                            stage_turun=cfg["filter_stage_turun"], min_checklist=cfg["min_checklist"]), rencana_cfg=R,
                riwayat=riw, rekap7=rk)
    tulis_dashboard(results, charts, meta)
    if demo:
        os.makedirs(OUT_DIR, exist_ok=True)
        for sym, png in charts.items():
            with open(os.path.join(OUT_DIR, f"grafik_{sym[:-4] if sym.endswith('USDT') else sym}.png"), "wb") as f:
                f.write(png)
    step = os.environ.get("GITHUB_STEP_SUMMARY") or (os.path.join(OUT_DIR, "ringkasan.md") if demo else None)
    if step:
        write_step_summary(results, meta, step)

    if not demo:
        cutoff = now - timedelta(days=7)
        state["alerts2"] = {k: v for k, v in state["alerts2"].items() if datetime.fromisoformat(v["ts"]) >= cutoff}
        state.pop("last_error_notice", None)
        save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
