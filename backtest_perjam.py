#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UJI SINYAL PER JAM
==================
Pertanyaan: kalau sinyal dihitung dari candle 1 jam (bukan candle harian), apakah hasilnya layak dipakai?

Tahap `data`   : candle 1 jam Binance sejak 2020 → di SETIAP jam jalankan mesin radar yang sama (perjam.py) pada
                 400 candle 1 jam terakhir → sinyal 🟢 radar, 🟩 awal Stage 2, 🔻 jual dulu (pantulan Stage 4) →
                 simulasi 4 rencana jual × 2 cara masuk. Berat (±5 juta analisa) → dibagi beberapa bagian (--bagian).
Tahap `gabung` : satukan hasil semua bagian → backtest_perjam/sinyal.csv.gz
Tahap `model`  : pilih rencana & gerbang secara walk-forward, uji portofolio di luar sampel, bandingkan dengan
                 sistem harian yang sekarang live.

ATURAN YANG DITETAPKAN DI MUKA (ditulis & di-commit sebelum data ditarik)
  1. Mesin = perjam.analisa: rumus radar harian apa adanya, candle 1 jam diperbesar √24× supaya ambang persennya
     sepadan. Koin & jenis sinyal yang sama paling banyak sekali per 24 jam. Meme coin tidak ikut.
  2. Yang dinilai hanya versi per jam dari tiga sinyal yang sekarang live: 🟢 radar naik, 🟩 awal Stage 2 (beli) dan
     🔻 pantulan Stage 4 (jual dulu). Biaya & pajak sama dengan uji harian (jual dulu + funding 0,03%/hari).
  3. MASUK = harga penutupan candle 1 jam BERIKUTNYA (jeda 1 jam): radar jalan di menit ke-7, jadwal GitHub sering
     terlambat, dan order dipasang manual. "Tanpa jeda" hanya dilaporkan sebagai pembanding.
  4. Gerbang pasar = model pasar yang sekarang live (arah BTC harian + skor pasar, batas tiap tahun sama dengan uji
     model pasar), memakai candle harian terakhir yang sudah tutup. Pilihan tambahan: arah BTC per jam (MA50 jam).
  5. Walk-forward: untuk tiap tahun uji (2023 dst.) dan tiap sisi, rencana jual (A/B/C/D) dan gerbang (dengan / tanpa
     arah BTC per jam) dipilih HANYA dari sinyal yang sudah selesai sebelum tahun itu: Sharpe portofolio latih
     tertinggi; yang selisihnya ≤ 0,10 dianggap setara → ambil yang total latihnya terbesar. Sisi itu baru aktif di
     tahun uji bila total & Sharpe latih pilihan itu positif.
  6. Putusan (di luar sampel, portofolio maks 5 posisi, median 100 urutan acak), pembanding = sistem harian sekarang:
       GANTI  (per jam menggantikan harian) bila per jam saja: total > harian, Sharpe ≥ harian + 0,15,
              maks turun tidak lebih buruk dari harian − 5 poin;
       TAMBAH (per jam berjalan di samping harian) bila gabungan memenuhi tiga syarat itu DAN per jam saja untung;
       selain itu TIDAK dipasang, dan hasilnya dilaporkan apa adanya.

Hasil: backtest_perjam/LAPORAN.md, hasil.json, model.json, meta.json, kurva.csv (sinyal.csv.gz di cabang data-perjam)
"""
from __future__ import annotations

import argparse
import glob
import heapq
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import backtest as BT
import backtest_pasar as BP
import backtest_short as BS
import perjam as PJ
import scanner as S
import strategi as ST

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_perjam")
SINYAL = os.path.join(OUT, "sinyal.csv.gz")
LIVE = BP.LIVE
NAMA_S = {"radar_naik": "🟢 Radar naik", "awal_stage2": "🟩 Awal Stage 2", "pantul_fib": "🔻 Jual dulu (pantulan Stage 4)",
          "radar_turun": "🔴 Radar turun", "acak_long": "beli acak", "acak_short": "short acak"}
ACAK = 97                 # pembanding: masuk di setiap candle ke-97
MASUK = 1                 # 1 = masuk di penutupan candle berikutnya (jeda 1 jam); 0 = tanpa jeda
MIN_LATIH = 30
BENIH_LATIH = 25
TOLERANSI = 0.10
SELISIH_PAKAI = 0.15
JAM = pd.Timedelta(hours=1)


# --------------------------------------------------------------------------- #
# Tahap data
# --------------------------------------------------------------------------- #
def jam_lengkap(bn: S.Binance, sym: str, mulai_ms: int, sampai_ms: int) -> np.ndarray | None:
    """Candle 1 jam yang sudah tutup → kolom: t, o, h, l, c, volume, qvol, taker_buy_q."""
    bag, t = [], int(mulai_ms)
    while t < sampai_ms:
        r = None
        for coba in range(6):
            try:
                r = bn._get("/api/v3/klines", {"symbol": sym, "interval": "1h", "startTime": t, "limit": 1000})
                break
            except Exception:
                if coba == 5:
                    raise
                time.sleep(10 * (coba + 1))
        if not r:
            break
        bag.append(np.array([(x[0], x[1], x[2], x[3], x[4], x[5], x[7], x[10], x[6]) for x in r], dtype=np.float64))
        if len(r) < 1000:
            break
        t = int(r[-1][0]) + PJ.MS_JAM
    if not bag:
        return None
    a = np.concatenate(bag)
    a = a[a[:, 8] < sampai_ms]
    _, i = np.unique(a[:, 0], return_index=True)
    return a[i][:, :8]


def proses(job):
    """Satu koin: di tiap jam jalankan mesin, catat sinyal baru, simulasikan semua rencana."""
    sym, base, meme, a, bt, br, cfg = job
    t = a[:, 0].astype(np.int64)
    o, h, l, c, v, qv, tb = (a[:, i] for i in range(1, 8))
    n = len(t)
    Bl, Bs = cfg.get("biaya"), dict(BS.BIAYA_KONS, **(cfg.get("biaya_short") or {}))
    info = dict(symbol=sym, base=base, name=base, rank=100, meme=meme, bursa="Binance")
    jeda, out, gagal = {}, [], 0
    for j in range(PJ.JENDELA - 1, n - PJ.TAHAN - 2):
        try:
            _, sig = PJ.analisa(info, PJ.jendela(t, o, h, l, c, v, qv, tb, j), cfg)
        except Exception:
            gagal += 1
            continue
        ev = list(sig)
        if j % ACAK == 0:
            ev += [dict(strategi="acak_long", sisi="long", skor=None, target=None, batal=None),
                   dict(strategi="acak_short", sisi="short", skor=None, target=None, batal=None)]
        for s in ev:
            nm = s["strategi"]
            if not nm.startswith("acak"):
                if j <= jeda.get(nm, -1):
                    continue
                jeda[nm] = j + PJ.JEDA_JAM
            panjang = s["sisi"] == "long"
            ib = int(np.searchsorted(bt, t[j]))
            rec = dict(waktu=pd.Timestamp(int(t[j]) + PJ.MS_JAM, unit="ms").strftime("%Y-%m-%dT%H:00"), symbol=sym, meme=meme,
                       sisi=s["sisi"], strategi=nm, skor_radar=s.get("skor"),
                       rezim_jam=str(br[ib]) if ib < len(bt) and bt[ib] == t[j] else "netral")
            for e in (0, 1):
                je = j + e
                for kode, (_, R) in PJ.RENCANA.items():
                    plan = ST.rencana(float(c[je]), "naik" if panjang else "turun", s["target"], s["batal"], None, R)
                    m = R["maks_hari"]
                    x = ST.simulasi(plan, h[je + 1:je + 1 + m], l[je + 1:je + 1 + m], c[je + 1:je + 1 + m])
                    net = ST.bersih(x["pnl"], Bl) if panjang else BS.bersih(x["pnl"], x["hari"] / 24, Bs)
                    rec[f"n{kode}{e}"], rec[f"j{kode}{e}"] = round(float(net), 3), int(x["hari"])
            out.append(rec)
    return sym, out, n, gagal


def daftar_koin() -> list[tuple[str, str, bool]]:
    """(symbol, base, meme) — koin yang sama dengan uji model pasar."""
    ev = pd.read_csv(os.path.join(BP.OUT, "event.csv.gz"), usecols=["symbol", "meme"])
    dr = pd.read_csv(os.path.join(BP.OUT, "radar.csv.gz"), usecols=["symbol", "meme"])
    m = pd.concat([ev, dr]).groupby("symbol")["meme"].max()
    return [(s, s[:-4] if s.endswith("USDT") else s, bool(x)) for s, x in sorted(m.items())]


def tahap_data(args) -> int:
    t0 = time.time()
    now = datetime.now(timezone.utc)
    cfg = S.load_config()
    koin = daftar_koin()
    if args.koin:
        koin = koin[:args.koin]
    koin = koin[args.bagian::args.dari]
    bn = S.Binance()
    mulai, sampai = int(pd.Timestamp(args.mulai, tz="UTC").timestamp() * 1000), int(now.timestamp() * 1000)
    btc = jam_lengkap(bn, "BTCUSDT", mulai, sampai)
    bt, br = btc[:, 0].astype(np.int64), ST.rezim_series(btc[:, 4])
    print(f"bagian {args.bagian}/{args.dari}: {len(koin)} koin, candle 1 jam sejak {args.mulai} · BTC {len(bt):,} candle")
    rows, gagal, n_jam, n_gagal, futs2 = [], [], 0, 0, []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as pp:
        with ThreadPoolExecutor(max_workers=4) as tp:
            futs = {tp.submit(jam_lengkap, bn, k[0], mulai, sampai): k for k in koin}
            for f in as_completed(futs):
                k = futs[f]
                try:
                    a = f.result()
                    if a is None or len(a) < PJ.JENDELA + PJ.TAHAN + 50:
                        gagal.append(k[0])
                    else:
                        futs2.append(pp.submit(proses, (k[0], k[1], k[2], a, bt, br, cfg)))
                except Exception as e:
                    gagal.append(k[0])
                    print("  ! gagal", k[0], e)
        print(f"  unduh selesai · {time.time() - t0:.0f} dtk")
        for i, f in enumerate(as_completed(futs2), start=1):
            sym, out, n, ng = f.result()
            rows += out
            n_jam += n
            n_gagal += ng
            print(f"  {i}/{len(futs2)} {sym}: {n:,} jam · {len(out)} sinyal · {time.time() - t0:.0f} dtk", flush=True)
    os.makedirs(OUT, exist_ok=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, f"bagian_{args.bagian}.csv.gz"), index=False, compression="gzip")
    with open(os.path.join(OUT, f"bagian_{args.bagian}.json"), "w", encoding="utf-8") as f:
        json.dump(dict(koin=len(futs2), gagal=gagal, candle_jam=int(n_jam), analisa_gagal=int(n_gagal), baris=int(len(D)),
                       mulai=args.mulai, durasi_detik=round(time.time() - t0)), f)
    print(f"bagian {args.bagian} selesai: {len(futs2)} koin · {n_jam:,} jam · {len(D):,} baris · gagal {gagal} · {time.time() - t0:.0f} dtk")
    return 0


def tahap_gabung(args) -> int:
    now = datetime.now(timezone.utc)
    berkas = sorted(glob.glob(os.path.join(OUT, "bagian_*.csv.gz")))
    if not berkas:
        print("tidak ada berkas bagian_*.csv.gz")
        return 1
    D = pd.concat([pd.read_csv(b) for b in berkas if os.path.getsize(b) > 50], ignore_index=True).sort_values(["waktu", "symbol", "strategi"])
    D.to_csv(SINYAL, index=False, compression="gzip")
    ms = [json.load(open(b, encoding="utf-8")) for b in sorted(glob.glob(os.path.join(OUT, "bagian_*.json")))]
    meta = dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), bagian=len(berkas),
                koin=sum(m["koin"] for m in ms), gagal=sum((m["gagal"] for m in ms), []), candle_jam=sum(m["candle_jam"] for m in ms),
                analisa_gagal=sum(m["analisa_gagal"] for m in ms), baris=int(len(D)), mulai=ms[0]["mulai"] if ms else None,
                dari=str(D["waktu"].min()), sampai=str(D["waktu"].max()), jam_mesin=round(sum(m["durasi_detik"] for m in ms) / 3600, 1),
                per_strategi={k: int(v) for k, v in D["strategi"].value_counts().items()})
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for b in berkas + glob.glob(os.path.join(OUT, "bagian_*.json")):
        os.remove(b)
    print(json.dumps(meta, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------- #
# Simulasi portofolio berbasis waktu (jam) — untuk sinyal harian hasilnya identik dengan backtest_pasar.portofolio
# --------------------------------------------------------------------------- #
def portofolio_w(T: pd.DataFrame, awal: pd.Timestamp, akhir: pd.Timestamp, maks: int = BP.MAKS_POSISI, benih: int = 0) -> dict:
    """T: kolom buka, tutup (waktu), net, symbol, tanggal (kunci), strategi. Posisi yang jatuh tempo ditutup dulu,
    lalu sinyal pada waktu itu dibuka selama slot masih ada (satu koin satu posisi)."""
    hari = pd.date_range(awal, akhir, freq="D")
    n = len(hari)
    if len(T) == 0:
        return dict(kurva=pd.Series(np.ones(n), index=hari), transaksi=0, menang=None, rata=None)
    u = pd.util.hash_pandas_object(T[["tanggal", "symbol", "strategi"]].assign(_b=benih), index=False).to_numpy(dtype=np.uint64) / np.float64(2 ** 64)
    tb = T["buka"].to_numpy().astype("datetime64[s]").astype(np.int64)
    tk = T["tutup"].to_numpy().astype("datetime64[s]").astype(np.int64)
    net, sym = T["net"].to_numpy(dtype=float), T["symbol"].to_numpy()
    a0 = int(pd.Timestamp(awal).to_datetime64().astype("datetime64[s]").astype(np.int64))
    a1 = a0 + n * 86400
    urut = np.lexsort((u, tb))
    modal, heap, pegang, hasil, wkt, nilai, seq = 1.0, [], set(), [], [], [], 0
    for i in urut:
        if tb[i] < a0 or tb[i] >= a1:
            continue
        while heap and heap[0][0] <= tb[i]:
            k, _, uk, nt, sy = heapq.heappop(heap)
            modal += uk * nt / 100
            hasil.append(nt)
            pegang.discard(sy)
            wkt.append(k)
            nilai.append(modal)
        if len(heap) < maks and sym[i] not in pegang:
            seq += 1
            heapq.heappush(heap, (int(tk[i]), seq, modal / maks, float(net[i]), sym[i]))
            pegang.add(sym[i])
    while heap:
        k, _, uk, nt, sy = heapq.heappop(heap)
        modal += uk * nt / 100
        hasil.append(nt)
        wkt.append(k)
        nilai.append(modal)
    wkt, nilai = np.array(wkt, dtype=np.int64), np.array([1.0] + nilai)
    eq = nilai[np.searchsorted(wkt, a0 + (np.arange(n) + 1) * 86400, side="left")]   # modal setelah semua penutupan s/d akhir hari itu
    eq[-1] = modal
    h = np.array(hasil) if hasil else np.array([np.nan])
    return dict(kurva=pd.Series(eq, index=hari), transaksi=len(hasil), menang=float(np.nanmean(h > 0) * 100) if hasil else None,
                rata=float(np.nanmean(h)) if hasil else None)


def uji_w(T: pd.DataFrame, awal, akhir, maks: int = BP.MAKS_POSISI, benih: int = BP.BENIH) -> dict:
    runs = [portofolio_w(T, awal, akhir, maks, b) for b in range(benih)]
    ms = [BP.metrik(r["kurva"]) for r in runs]

    def med(k, nd=1):
        x = [m[k] for m in ms if np.isfinite(m[k])]
        return round(float(np.median(x)), nd) if x else 0.0
    tahun = sorted({y for m in ms for y in m["per_tahun"]})
    return dict(total=med("total"), total_min=round(min(m["total"] for m in ms), 1), total_maks=round(max(m["total"] for m in ms), 1),
                maxdd=med("maxdd"), sharpe=med("sharpe", 2),
                per_tahun={y: round(float(np.median([m["per_tahun"].get(y, 0) for m in ms])), 1) for y in tahun},
                transaksi=int(np.median([r["transaksi"] for r in runs])),
                menang=round(float(np.median([r["menang"] for r in runs])), 1) if len(T) and runs[0]["menang"] is not None else None,
                rata=round(float(np.median([r["rata"] for r in runs])), 2) if len(T) and runs[0]["rata"] is not None else None,
                kandidat=int(len(T)), _kurva=runs[0]["kurva"], _total=[m["total"] for m in ms], _sharpe=[m["sharpe"] for m in ms],
                _maxdd=[m["maxdd"] for m in ms])


# --------------------------------------------------------------------------- #
# Tahap model
# --------------------------------------------------------------------------- #
def muat_jam() -> pd.DataFrame:
    X = pd.read_csv(SINYAL)
    X = X[~X["meme"].astype(bool)].copy()
    X["tw"] = pd.to_datetime(X["waktu"])
    ph = pd.read_csv(os.path.join(BP.OUT, "pasar_harian.csv"), index_col="tanggal")
    X["tgl_gerbang"] = (X["tw"].dt.floor("D") - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")   # candle harian terakhir yang sudah tutup
    X = X.merge(ph[["skor", "rezim"]], left_on="tgl_gerbang", right_index=True, how="left").dropna(subset=["skor"])
    X["skor"] = X["skor"].astype(int)
    X["tanggal"], X["bulan"] = X["waktu"], X["waktu"].str[:7]
    return X


def bentuk(d: pd.DataFrame, rencana: str, masuk: int = MASUK) -> pd.DataFrame:
    """Isi kolom net/jam/buka/tutup untuk satu rencana & cara masuk."""
    out = d.assign(net=d[f"n{rencana}{masuk}"], jam=d[f"j{rencana}{masuk}"])
    out["buka"] = out["tw"] + masuk * JAM
    out["tutup"] = out["buka"] + pd.to_timedelta(out["jam"].clip(lower=1), unit="h")
    return out


def gerbang_jam(d: pd.DataFrame, sisi: str, batas: int, pakai_jam: bool) -> pd.DataFrame:
    m = BP.rezim_ok(d, sisi) & (d["skor"] <= batas)
    if pakai_jam:
        m &= (d["rezim_jam"] == "naik") if sisi == "long" else (d["rezim_jam"] != "naik")
    return d[m]


def nilai_latih_w(T: pd.DataFrame, awal, akhir) -> dict:
    ms = [BP.metrik(portofolio_w(T, awal, akhir, BP.MAKS_POSISI, b)["kurva"]) for b in range(BENIH_LATIH)]
    sh = [m["sharpe"] for m in ms if np.isfinite(m["sharpe"])]
    return dict(sharpe=float(np.median(sh)) if sh else -9.0, total=float(np.median([m["total"] for m in ms])))


def pilih_jam(latih: pd.DataFrame, sisi: str, batas: int, awal, akhir) -> dict:
    """Pilih (rencana, gerbang BTC per jam) untuk satu sisi dari data latih."""
    pool = latih[latih["strategi"].isin(LIVE[sisi])]
    kand = []
    for pj in (False, True):
        g = gerbang_jam(pool, sisi, batas, pj)
        if len(g) < MIN_LATIH:
            continue
        for kode in PJ.RENCANA:
            f = bentuk(g, kode)
            f = f[f["tutup"] < akhir]
            if len(f) < MIN_LATIH:
                continue
            v = nilai_latih_w(f, awal, akhir)
            kand.append(dict(rencana=kode, btc_jam=pj, n=int(len(f)), sharpe=round(v["sharpe"], 2), total=round(v["total"], 1)))
    if not kand:
        return dict(aktif=False, alasan="sinyal latih kurang", kandidat=[])
    s_maks = max(k["sharpe"] for k in kand)
    best = dict(max((k for k in kand if k["sharpe"] >= s_maks - TOLERANSI), key=lambda k: (k["total"], k["sharpe"])))
    best["aktif"] = bool(best["total"] > 0 and best["sharpe"] > 0)
    if not best["aktif"]:
        best["alasan"] = "hasil latih terbaik pun tidak untung"
    best["kandidat"] = kand
    return best


def harian_w(Td: pd.DataFrame, geser: bool = True) -> pd.DataFrame:
    """Sinyal harian → format waktu. geser=True: masuk di penutupan candle harian (tanggal + 1 hari, 00.00 UTC)."""
    out = Td.copy()
    out["buka"] = out["ts"] + (pd.Timedelta(days=1) if geser else pd.Timedelta(0))
    out["tutup"] = out["buka"] + pd.to_timedelta(out["hari"].clip(lower=1), unit="D")
    return out


def lolos(baru: dict, dasar: dict) -> bool:
    return bool(baru["total"] > dasar["total"] and baru["total"] > 0 and baru["sharpe"] >= dasar["sharpe"] + SELISIH_PAKAI
                and baru["maxdd"] >= dasar["maxdd"] - 5)


def f_p(r: dict) -> str:
    if not r.get("transaksi"):
        return "tidak ada transaksi"
    return f"{r['total']:+.1f}% · maks turun {r['maxdd']:.1f}% · Sharpe {r['sharpe']} · menang {r['menang']}% · {r['transaksi']} transaksi"


def tahap_model(args) -> int:
    cfg = S.load_config()
    if not os.path.exists(SINYAL):
        print("backtest_perjam/sinyal.csv.gz belum ada — jalankan tahap data & gabung dulu")
        return 1
    X = muat_jam()
    T, _ = BP.muat_sinyal(cfg)
    U = T[~T["meme"]].copy()
    meta = json.load(open(os.path.join(OUT, "meta.json"), encoding="utf-8")) if os.path.exists(os.path.join(OUT, "meta.json")) else {}
    mp = json.load(open(os.path.join(BP.OUT, "model.json"), encoding="utf-8"))
    now = datetime.now(timezone.utc)
    akhir_h = U["ts"].max()
    akhir_data = min(akhir_h, X["tw"].max().floor("D"))
    tahun_uji = list(range(2023, int(akhir_data.year) + 1))
    oos_awal, oos_akhir = pd.Timestamp(f"{tahun_uji[0]}-01-01"), akhir_data + pd.Timedelta(days=31)
    bersih_ = lambda r: {k: v for k, v in r.items() if not k.startswith("_")}  # noqa: E731
    H = dict(versi=1, dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), data=meta,
             dari=str(X["waktu"].min()), sampai=str(X["waktu"].max()), masuk=MASUK,
             rencana={k: v[0] for k, v in PJ.RENCANA.items()})
    batas_akhir = dict(long=int(mp["beli"]["skor_maks"]), short=int(mp["jual"]["skor_maks"]))

    # ---------- 1) deskriptif: seluruh data, gerbang model pasar akhir ----------
    H["per_strategi"], H["jumlah"] = {}, {}
    hari_data = max(1, (X["tw"].max() - X["tw"].min()).days)
    for sisi in ("long", "short"):
        for s in LIVE[sisi] + ["acak_long" if sisi == "long" else "acak_short"]:
            d = X[X["strategi"] == s]
            g = gerbang_jam(d, sisi, batas_akhir[sisi], False)
            gj = gerbang_jam(d, sisi, batas_akhir[sisi], True)
            H["jumlah"][s] = dict(semua=int(len(d)), lolos=int(len(g)), per_hari_semua=round(len(d) / hari_data, 2), per_hari_lolos=round(len(g) / hari_data, 2))
            H["per_strategi"][s] = {}
            for kode in PJ.RENCANA:
                f1, f0 = bentuk(g, kode, 1), bentuk(g, kode, 0)
                x = dict(jeda=BP.ringkas(f1), tanpa_jeda=BP.ringkas(f0), btc_jam=BP.ringkas(bentuk(gj, kode, 1)),
                         tanpa_gerbang=BP.ringkas(bentuk(d, kode, 1)), jam_rata=round(float(f1["jam"].mean()), 1) if len(f1) else None,
                         per_tahun={str(y): BP.ringkas(q) for y, q in f1.groupby(f1["tw"].dt.year)})
                H["per_strategi"][s][kode] = x

    # ---------- 2) walk-forward ----------
    awal_latih = min(U["ts"].min(), X["tw"].min().floor("D"))
    bag_h, bag_j, H["walk"] = [], [], {}
    for th in tahun_uji:
        mulai = pd.Timestamp(f"{th}-01-01")
        selesai = min(pd.Timestamp(f"{th}-12-31 23:59"), akhir_data + pd.Timedelta(hours=23))
        sel = BP.pilih_v2(U[U["keluar"] < mulai], U["ts"].min(), mulai)            # gerbang pasar tahun itu (= uji model pasar)
        bag_h.append(BP.lolos_v2(U[(U["ts"] >= mulai) & (U["ts"] <= min(pd.Timestamp(f"{th}-12-31"), akhir_h))], sel, False))
        info = {}
        for sisi in ("long", "short"):
            b = int(sel[sisi]["batas"])
            pk = pilih_jam(X[X["tw"] < mulai], sisi, b, awal_latih, mulai)
            info[sisi] = dict(batas=b, **pk)
            uji = X[(X["tw"] >= mulai) & (X["tw"] <= selesai) & X["strategi"].isin(LIVE[sisi])]
            if pk.get("aktif"):
                f = bentuk(gerbang_jam(uji, sisi, b, pk["btc_jam"]), pk["rencana"])
                bag_j.append(f)
                info[sisi]["uji"] = {s: BP.ringkas(f[f["strategi"] == s]) for s in LIVE[sisi]}
        H["walk"][str(th)] = info
    Td = pd.concat(bag_h)
    Tj = pd.concat(bag_j) if bag_j else bentuk(X.iloc[0:0], "A")
    Dw = harian_w(Td)
    kol = ["tanggal", "symbol", "strategi", "net", "buka", "tutup"]
    Gw = pd.concat([Dw[kol].assign(sumber="harian"), Tj[kol].assign(sumber="per jam")], ignore_index=True)

    # cek simulator: untuk sinyal harian harus sama dengan simulator model pasar
    cek_a, cek_b = BP.uji_portofolio(Td, oos_awal, oos_akhir), uji_w(harian_w(Td, geser=False), oos_awal, oos_akhir)
    H["cek_simulator"] = dict(model_pasar=dict(total=cek_a["total"], sharpe=cek_a["sharpe"], maxdd=cek_a["maxdd"]),
                              di_sini=dict(total=cek_b["total"], sharpe=cek_b["sharpe"], maxdd=cek_b["maxdd"]),
                              cocok=bool(cek_a["total"] == cek_b["total"] and cek_a["sharpe"] == cek_b["sharpe"] and cek_a["maxdd"] == cek_b["maxdd"]))

    NH, NJ, NG = "Harian (sistem sekarang)", "Per jam saja", "Harian + per jam (5 slot bersama)"
    rh, rj, rg = uji_w(Dw, oos_awal, oos_akhir), uji_w(Tj[kol], oos_awal, oos_akhir), uji_w(Gw, oos_awal, oos_akhir)
    kurva = {NH: rh.pop("_kurva"), NJ: rj.pop("_kurva"), NG: rg.pop("_kurva")}
    pasang = lambda a, b: dict(benih=BP.BENIH, total_lebih_baik=int((np.array(a["_total"]) > np.array(b["_total"])).sum()),  # noqa: E731
                               sharpe_lebih_baik=int((np.array(a["_sharpe"]) > np.array(b["_sharpe"])).sum()),
                               maxdd_lebih_baik=int((np.array(a["_maxdd"]) > np.array(b["_maxdd"])).sum()))
    H["oos"] = dict(dari=str(oos_awal.date()), sampai=str(akhir_data.date()), portofolio={NH: bersih_(rh), NJ: bersih_(rj), NG: bersih_(rg)},
                    per_sinyal={NH: BP.ringkas(Td), NJ: BP.ringkas(Tj) if len(Tj) else dict(n=0)},
                    berpasangan=dict(per_jam_vs_harian=pasang(rj, rh), gabungan_vs_harian=pasang(rg, rh)))
    # pembanding: tanpa jeda 1 jam (ideal), rencana & gerbang yang sama
    bag0 = []
    for th, info in H["walk"].items():
        mulai = pd.Timestamp(f"{th}-01-01")
        selesai = min(pd.Timestamp(f"{th}-12-31 23:59"), akhir_data + pd.Timedelta(hours=23))
        for sisi in ("long", "short"):
            pk = info[sisi]
            if pk.get("aktif"):
                uji = X[(X["tw"] >= mulai) & (X["tw"] <= selesai) & X["strategi"].isin(LIVE[sisi])]
                bag0.append(bentuk(gerbang_jam(uji, sisi, pk["batas"], pk["btc_jam"]), pk["rencana"], 0))
    Tj0 = pd.concat(bag0) if bag0 else Tj
    r0 = uji_w(Tj0[kol], oos_awal, oos_akhir)
    r0.pop("_kurva")
    H["oos"]["tanpa_jeda"] = bersih_(r0)
    # kepekaan: satu rencana dipasang tetap sepanjang masa uji (gerbang model pasar per tahun, tanpa BTC per jam)
    H["tetap"] = {}
    for kode in PJ.RENCANA:
        bagk = []
        for th, info in H["walk"].items():
            mulai = pd.Timestamp(f"{th}-01-01")
            selesai = min(pd.Timestamp(f"{th}-12-31 23:59"), akhir_data + pd.Timedelta(hours=23))
            for sisi in ("long", "short"):
                uji = X[(X["tw"] >= mulai) & (X["tw"] <= selesai) & X["strategi"].isin(LIVE[sisi])]
                bagk.append(bentuk(gerbang_jam(uji, sisi, info[sisi]["batas"], False), kode))
        fk = pd.concat(bagk)
        H["tetap"][kode] = dict(bersih_(uji_w(fk[kol], oos_awal, oos_akhir)), per_sinyal=BP.ringkas(fk),
                                beli=BP.ringkas(fk[fk["sisi"] == "long"]), jual=BP.ringkas(fk[fk["sisi"] == "short"]))

    aktif = any(info[s].get("aktif") for info in H["walk"].values() for s in ("long", "short"))
    ganti = bool(aktif and lolos(rj, rh))
    tambah = bool(aktif and not ganti and lolos(rg, rh) and rj["total"] > 0)
    putusan = "ganti" if ganti else ("tambah" if tambah else "tidak")
    # model akhir (dilatih dari semua data) — hanya dipakai radar bila putusan ≠ tidak
    final = {sisi: pilih_jam(X[X["tw"] < oos_akhir], sisi, batas_akhir[sisi], awal_latih, oos_akhir) for sisi in ("long", "short")}
    for v in final.values():
        v.pop("kandidat", None)
    H["putusan"] = dict(pakai=putusan, aktif=bool(aktif),
                        alasan=f"di luar sampel {H['oos']['dari']} s/d {H['oos']['sampai']}: per jam saja {f_p(rj)} — gabungan {f_p(rg)} — harian {f_p(rh)}")
    model = dict(versi=1, dibuat=H["dibuat"], dibuat_wib=H["dibuat_wib"], pakai=putusan, putusan=H["putusan"]["alasan"], masuk=MASUK,
                 beli=final["long"], jual=final["short"], rencana=H["rencana"])
    H["model"] = model

    # ---------- laporan ----------
    def f_r(r):
        return f"{r['rata']:+.2f}% · menang {r['menang']}% ({r['n']})" if r and r.get("n") else "-"
    judul = {"ganti": "✅ Sinyal per jam MENGGANTIKAN sinyal harian", "tambah": "✅ Sinyal per jam DITAMBAHKAN di samping sinyal harian",
             "tidak": "❌ Sinyal per jam TIDAK dipasang — tidak lebih baik dari sistem harian"}[putusan]
    cs = H["cek_simulator"]
    L = ["# ⏱ Uji Sinyal Per Jam", "",
         f"Dibuat {H['dibuat_wib']} · {meta.get('koin', '?')} koin · {meta.get('candle_jam', 0):,} candle 1 jam dianalisa satu per satu "
         f"(±{meta.get('jam_mesin', '?')} jam mesin) · sinyal {H['dari']} s/d {H['sampai']} UTC · meme coin tidak ikut", "",
         "## Putusan", "", f"**{judul}.**", "",
         f"- Harian (sistem sekarang): {f_p(rh)}", f"- Per jam saja: {f_p(rj)}", f"- Harian + per jam (5 slot bersama): {f_p(rg)}",
         f"- Per jam saja bila bisa masuk TANPA jeda 1 jam (tidak realistis, hanya pembanding): {f_p(r0)}",
         f"- Syarat (ditetapkan di muka): total > harian, Sharpe ≥ harian + {SELISIH_PAKAI}, maks turun tidak lebih buruk dari harian − 5 poin.", "",
         "## Yang diuji", "",
         "Mesin radar yang sama dijalankan di setiap jam pada 400 candle 1 jam terakhir. Karena gerak 1 jam ±1/5 gerak harian, candle "
         "diperbesar √24× dulu supaya semua ambang persen (pola, stage, Fibonacci, skor) sepadan; target & batal dikembalikan ke harga asli. "
         "Sinyal: 🟢 radar naik, 🟩 awal Stage 2, 🔻 jual dulu (pantulan Stage 4) — koin & jenis yang sama paling banyak sekali per 24 jam. "
         "Masuk di penutupan candle 1 jam berikutnya (jeda 1 jam untuk keterlambatan jadwal & pasang order manual). "
         "Gerbang pasar sama dengan sistem harian (arah BTC harian + skor pasar). Biaya & pajak sudah dipotong.", "",
         f"Cek simulator: portofolio sinyal harian di sini {cs['di_sini']['total']:+.1f}% / Sharpe {cs['di_sini']['sharpe']} / maks turun {cs['di_sini']['maxdd']}% — "
         f"simulator model pasar {cs['model_pasar']['total']:+.1f}% / {cs['model_pasar']['sharpe']} / {cs['model_pasar']['maxdd']}% → {'cocok' if cs['cocok'] else 'TIDAK cocok'}.", "",
         "| Rencana | Isi |", "|---|---|"] + [f"| {k} | {v} |" for k, v in H["rencana"].items()]
    L += ["", "## Berapa banyak sinyal per jam?", "",
          "| Sinyal | Semua (2020–2026) | Per hari | Lolos gerbang pasar | Per hari |", "|---|---|---|---|---|"]
    for s in sum(LIVE.values(), []):
        j = H["jumlah"][s]
        L.append(f"| {NAMA_S[s]} | {j['semua']:,} | {j['per_hari_semua']} | {j['lolos']:,} | {j['per_hari_lolos']} |")
    L += ["", "## Hasil per sinyal (seluruh data, lolos gerbang pasar, masuk dengan jeda 1 jam)", "",
          "Isi sel: rata-rata bersih per transaksi · tingkat menang (jumlah sinyal)."]
    for sisi in ("long", "short"):
        for s in LIVE[sisi] + ["acak_long" if sisi == "long" else "acak_short"]:
            L += ["", f"### {NAMA_S[s]}", "",
                  "| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |", "|---|---|---|---|---|---|---|---|"]
            for kode in PJ.RENCANA:
                x = H["per_strategi"][s][kode]
                pt = " · ".join(f"{y}: {v['rata']:+.1f}" for y, v in x["per_tahun"].items() if v.get("n"))
                L.append(f"| {kode} | {f_r(x['jeda'])} | {x['jeda'].get('t', '-') if x['jeda'].get('n') else '-'} | {f_r(x['tanpa_jeda'])} | {f_r(x['btc_jam'])} | "
                         f"{f_r(x['tanpa_gerbang'])} | {x['jam_rata']} jam | {pt} |")
    L += ["", f"## Uji portofolio di luar sampel ({H['oos']['dari']} s/d {H['oos']['sampai']})", "",
          f"Maks {BP.MAKS_POSISI} posisi, modal dibagi rata, median dari {BP.BENIH} urutan acak (dalam kurung = terendah…tertinggi).", "",
          "| Susunan | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |", "|---|---|---|---|---|---|---|---|"]
    for nm, r in H["oos"]["portofolio"].items():
        if not r.get("transaksi"):
            L.append(f"| {nm} | tidak ada transaksi | | | | | | |")
            continue
        pt = " · ".join(f"{y}: {v:+.0f}%" for y, v in r["per_tahun"].items())
        L.append(f"| {nm} | **{r['total']:+.1f}%** ({r['total_min']:+.0f}…{r['total_maks']:+.0f}) | {pt} | {r['maxdd']:.1f}% | {r['sharpe']} | "
                 f"{r['transaksi']} dari {r['kandidat']} | {r['menang']}% | {r['rata']:+.2f}% |")
    bp1, bp2 = H["oos"]["berpasangan"]["per_jam_vs_harian"], H["oos"]["berpasangan"]["gabungan_vs_harian"]
    L += ["", f"Berpasangan ({bp1['benih']} urutan acak): per jam saja lebih tinggi dari harian di {bp1['total_lebih_baik']} urutan (Sharpe {bp1['sharpe_lebih_baik']}, "
              f"penurunan lebih kecil {bp1['maxdd_lebih_baik']}); gabungan lebih tinggi dari harian di {bp2['total_lebih_baik']} (Sharpe {bp2['sharpe_lebih_baik']}, "
              f"penurunan lebih kecil {bp2['maxdd_lebih_baik']}).", "",
          "### Pilihan tiap tahun uji (hanya dari data sebelum tahun itu)", "",
          "| Tahun uji | Sisi | Batas skor pasar | Rencana | + BTC per jam | Latih: Sharpe · total (sinyal) | Hasil uji |", "|---|---|---|---|---|---|---|"]
    for th, info in H["walk"].items():
        for sisi, nm in (("long", "Beli"), ("short", "Jual dulu")):
            x = info[sisi]
            if not x.get("rencana"):
                L.append(f"| {th} | {nm} | ≤ {x['batas']:+d} | - | - | {x.get('alasan', '-')} | - |")
                continue
            uji = " · ".join(f"{NAMA_S[s].split(' ')[0]} {f_r(v)}" for s, v in (x.get("uji") or {}).items()) or f"tidak aktif ({x.get('alasan', '')})"
            L.append(f"| {th} | {nm} | ≤ {x['batas']:+d} | {x['rencana']} | {'ya' if x['btc_jam'] else 'tidak'} | {x['sharpe']} · {x['total']:+.0f}% ({x['n']}) | {uji} |")
    L += ["", "### Bila satu rencana dipasang tetap sepanjang 2023–2026 (melihat ke belakang, hanya untuk penjelasan)", "",
          "| Rencana | Total | Maks turun | Sharpe | Menang | Semua sinyal | Beli | Jual dulu |", "|---|---|---|---|---|---|---|---|"]
    for kode, r in H["tetap"].items():
        L.append(f"| {kode} | {r['total']:+.1f}% | {r['maxdd']:.1f}% | {r['sharpe']} | {r['menang']}% | {f_r(r['per_sinyal'])} | {f_r(r['beli'])} | {f_r(r['jual'])} |")
    L += ["", "## Catatan jujur", "",
          "- Biaya & pajak ±0,41% per transaksi sama besarnya di candle 1 jam maupun harian, padahal gerak yang dikejar di candle 1 jam "
          "jauh lebih kecil — itu sebabnya rencana A (skala penuh) paling berat menanggung biaya.",
          "- Jeda 1 jam adalah perkiraan: alert bisa datang 10–30 menit setelah candle tutup, lalu order dipasang manual.",
          "- 'Diperbesar √24×' adalah cara menyamakan skala, bukan satu-satunya cara membaca candle 1 jam.",
          "- Daftar koin = koin top CMC saat ini (yang sudah mati tidak ikut); untung-rugi dicatat saat posisi ditutup.",
          "- Aturan uji ditulis sebelum data ditarik. Tabel 'dipasang tetap' melihat ke belakang dan tidak dipakai untuk memutuskan.",
          "- Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual."]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as f:
        json.dump(BT._json_safe(H), f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "model.json"), "w", encoding="utf-8") as f:
        json.dump(BT._json_safe(model), f, ensure_ascii=False, indent=1)
    kv = pd.DataFrame(kurva)
    kv.index.name = "tanggal"
    kv.round(4).to_csv(os.path.join(OUT, "kurva.csv"))
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tahap", choices=["data", "gabung", "model", "semua"], nargs="?", default="semua")
    ap.add_argument("--mulai", default="2020-01-01")
    ap.add_argument("--koin", type=int, default=0, help="batasi jumlah koin (0 = semua)")
    ap.add_argument("--bagian", type=int, default=0)
    ap.add_argument("--dari", type=int, default=1)
    args = ap.parse_args()
    if args.tahap in ("data", "semua"):
        rc = tahap_data(args)
        if rc:
            return rc
    if args.tahap in ("gabung", "semua"):
        rc = tahap_gabung(args)
        if rc:
            return rc
    if args.tahap in ("model", "semua"):
        return tahap_model(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
