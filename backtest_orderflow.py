#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UJI ORDER FLOW & MARKET PROFILE
===============================
Pertanyaan: apakah konfirmasi order flow (delta / CVD) dan market profile (POC, zona nilai) dari candle 1 jam
menaikkan hasil sinyal radar (tingkat menang & untung)?

Tahap `data`  : candle 1 jam Binance sejak 2020 untuk koin yang sama dengan uji model pasar → fitur per hari
                (orderflow.py) → backtest_orderflow/fitur.csv.gz (cabang data-orderflow)
Tahap `model` : gabungkan fitur dengan sinyal + hasilnya yang SAMA PERSIS dengan uji model pasar
                (model_pasar/radar.csv.gz & event.csv.gz), lalu bandingkan dengan vs tanpa konfirmasi.

ATURAN YANG DITETAPKAN DI MUKA (ditulis & di-commit sebelum data per jam ditarik)
  1. DASAR = model yang sekarang live (model pasar): 🟢 radar & 🟩 awal Stage 2 saat BTC tren naik dan skor pasar
     tidak kepanasan; 🔻 jual dulu (pantulan Stage 4) saat BTC tidak tren naik. Batas skor tiap tahun uji dipilih
     walk-forward persis seperti di backtest_pasar.py.
  2. Konfirmasi yang diuji = 8 buah di orderflow.KONFIRMASI, arahnya mengikuti teori (beli: harga diterima di atas
     zona nilai / POC, delta positif; jual dulu: cerminannya). Kebalikannya TIDAK boleh dipilih.
  3. Walk-forward: untuk tiap tahun uji (2023 dst.) dan tiap strategi live, konfirmasi dipilih HANYA dari sinyal
     yang sudah selesai sebelum tahun itu (Sharpe portofolio latih). "Tanpa konfirmasi" tetap dipilih kecuali ada
     konfirmasi yang Sharpe latihnya lebih tinggi > 0,10; di antara yang hampir setara dipilih yang sinyalnya terbanyak.
  4. Putusan: konfirmasi dipasang ke radar hanya bila di luar sampel (2023 dst., portofolio maks 5 posisi, median
     100 urutan acak) total untung > DASAR, Sharpe ≥ DASAR + 0,15, dan penurunan maksimum tidak lebih buruk dari
     DASAR − 5 poin. Kalau tidak → dilaporkan apa adanya dan TIDAK dipasang.
  5. Uji tambahan (aturan putusan yang sama): stop loss di batas zona nilai (1% di luar zona, hanya bila jaraknya
     3–12% dari harga masuk dan lebih dekat dari stop loss biasa).
  Tabel "dipasang tetap" (bukan walk-forward), varian TPO / 90 hari, dan uji permutasi hanya untuk penjelasan —
  tidak ikut menentukan putusan.

TAMBAHAN SETELAH HASIL PERTAMA KELUAR (16 Nov 2026) — eksplorasi, tidak ikut menentukan putusan:
  konfirmasi dipakai sebagai URUTAN PRIORITAS saat slot penuh (sinyal terkonfirmasi diambil lebih dulu), bukan saringan.

Hasil: backtest_orderflow/LAPORAN.md, hasil.json, model.json, meta.json, kurva.csv
"""
from __future__ import annotations

import argparse
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
import orderflow as OF
import scanner as S
import strategi as ST

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_orderflow")
FITUR = os.path.join(OUT, "fitur.csv.gz")
LIVE = BP.LIVE
NAMA_S = {s: v[1] for s, v in BP.STRATEGI.items()}
MIN_LATIH = 30            # minimal sinyal latih (strategi itu, setelah konfirmasi) supaya sebuah konfirmasi boleh dinilai
TOLERANSI = 0.10          # konfirmasi harus menaikkan Sharpe latih lebih dari ini agar dipilih
SELISIH_PAKAI = 0.15      # syarat Sharpe uji untuk dipasang
N_PERM = 2000
SL_PENYANGGA, SL_MIN, SL_MAKS = 0.01, 0.03, 0.12


# --------------------------------------------------------------------------- #
# Tahap data
# --------------------------------------------------------------------------- #
def jam_lengkap(bn: S.Binance, sym: str, mulai_ms: int, sampai_ms: int) -> np.ndarray | None:
    """Candle 1 jam yang sudah tutup → array kolom: t, o, h, l, c, qvol, taker_buy_q."""
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
        bag.append(np.array([(x[0], x[1], x[2], x[3], x[4], x[7], x[10], x[6]) for x in r], dtype=np.float64))
        if len(r) < 1000:
            break
        t = int(r[-1][0]) + OF.MS_JAM
    if not bag:
        return None
    a = np.concatenate(bag)
    a = a[a[:, 7] < sampai_ms]
    _, i = np.unique(a[:, 0], return_index=True)
    return a[i][:, :7]


def kerja(job):
    sym, a = job
    F = OF.fitur_harian(a[:, 0].astype(np.int64), a[:, 1], a[:, 2], a[:, 3], a[:, 4], a[:, 5], a[:, 6])
    F = OF.kemas(F).reset_index()
    F.insert(1, "symbol", sym)
    return sym, F, int(len(a))


def daftar_simbol() -> list[str]:
    dr = pd.read_csv(os.path.join(BP.OUT, "radar.csv.gz"), usecols=["symbol"])
    ev = pd.read_csv(os.path.join(BP.OUT, "event.csv.gz"), usecols=["symbol"])
    return sorted(set(dr["symbol"]) | set(ev["symbol"]))


def tahap_data(args) -> int:
    t0 = time.time()
    now = datetime.now(timezone.utc)
    sim = daftar_simbol()[:args.koin] if args.koin else daftar_simbol()
    bn = S.Binance()
    mulai, sampai = int(pd.Timestamp(args.mulai, tz="UTC").timestamp() * 1000), int(now.timestamp() * 1000)
    print(f"{len(sim)} koin, candle 1 jam sejak {args.mulai}...")
    bag, gagal, n_jam, futs2 = [], [], 0, []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as pp:
        with ThreadPoolExecutor(max_workers=6) as tp:
            futs = {tp.submit(jam_lengkap, bn, s, mulai, sampai): s for s in sim}
            for i, f in enumerate(as_completed(futs), start=1):
                s = futs[f]
                try:
                    a = f.result()
                    if a is None or len(a) < 24 * 60:
                        gagal.append(s)
                    else:
                        futs2.append(pp.submit(kerja, (s, a)))
                except Exception as e:
                    gagal.append(s)
                    print("  ! gagal", s, e)
                if i % 20 == 0:
                    print(f"  unduh {i}/{len(sim)} · {time.time() - t0:.0f} dtk")
        for i, f in enumerate(as_completed(futs2), start=1):
            s, F, nj = f.result()
            bag.append(F)
            n_jam += nj
            if i % 20 == 0:
                print(f"  fitur {i}/{len(futs2)} · {time.time() - t0:.0f} dtk")
    if not bag:
        print("Tidak ada data")
        return 1
    D = pd.concat(bag, ignore_index=True).sort_values(["symbol", "tanggal"])
    os.makedirs(OUT, exist_ok=True)
    D.to_csv(FITUR, index=False, compression="gzip")
    meta = dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), koin=len(bag), gagal=gagal,
                mulai=args.mulai, candle_jam=int(n_jam), baris=int(len(D)), dari=str(D["tanggal"].min()), sampai=str(D["tanggal"].max()),
                kosong={k: round(float(D[k].isna().mean() * 100), 1) for k in ("d1", "d3", "poc30", "tpoc30", "poc90")},
                durasi_detik=round(time.time() - t0))
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"Data selesai: {len(bag)} koin · {n_jam:,} candle 1 jam · {len(D):,} baris · gagal {gagal} · {time.time() - t0:.0f} dtk")
    print(D[D["symbol"] == "BTCUSDT"].tail(3).to_string(index=False))
    return 0


# --------------------------------------------------------------------------- #
# Tahap model
# --------------------------------------------------------------------------- #
def muat(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """→ (U: semua kandidat sinyal bukan-meme + fitur + kolom k_<kode>, ph, F: fitur harga asli)."""
    T, ph = BP.muat_sinyal(cfg)
    U = T[~T["meme"]].copy()
    F = OF.buka(pd.read_csv(FITUR))
    assert not F.duplicated(["tanggal", "symbol"]).any(), "fitur ganda"
    n0 = len(U)
    U = U.merge(F, on=["tanggal", "symbol"], how="left")
    assert len(U) == n0
    for k in OF.KODE:
        U["k_" + k] = OF.konfirmasi(U, k, U["sisi"])
    U["ada_fitur"] = U["poc30"].notna() & U["d3"].notna()
    return U, ph, F


def p_permutasi(d: pd.DataFrame, kol: str, n_perm: int = N_PERM, seed: int = 0, menang: bool = False) -> float | None:
    """Uji permutasi dua sisi untuk selisih rata-rata (terkonfirmasi − tidak); label diacak DI DALAM bulan yang sama,
    supaya konfirmasi yang cuma kebetulan muncul di bulan-bulan bagus tidak dianggap berguna.
    menang=True → yang diuji selisih TINGKAT MENANG (bukan rata-rata untung)."""
    x, k = d["net"].to_numpy(dtype=float), d[kol].to_numpy(dtype=bool)
    if menang:
        x = (x > 0).astype(float)
    if k.sum() < 10 or (~k).sum() < 10:
        return None
    obs = x[k].mean() - x[~k].mean()
    blok = [np.where(d["bulan"].to_numpy() == b)[0] for b in d["bulan"].unique()]
    rng, lebih = np.random.default_rng(seed), 0
    for _ in range(n_perm):
        kp = k.copy()
        for ix in blok:
            if len(ix) > 1:
                kp[ix] = k[rng.permutation(ix)]
        lebih += abs(x[kp].mean() - x[~kp].mean()) >= abs(obs) - 1e-12
    return float((lebih + 1) / (n_perm + 1))


def banding(d: pd.DataFrame, kol: str, perm: bool = True) -> dict:
    ya, tdk = BP.ringkas(d[d[kol]]), BP.ringkas(d[~d[kol]])
    out = dict(ya=ya, tidak=tdk)
    if ya.get("n") and tdk.get("n"):
        out["selisih_rata"] = round(ya["rata"] - tdk["rata"], 2)
        out["selisih_menang"] = round(ya["menang"] - tdk["menang"], 1)
        if perm:
            out["p"] = p_permutasi(d, kol)
            out["p_menang"] = p_permutasi(d, kol, menang=True)
    return out


def susun(pool: pd.DataFrame, sisi: str, pil: dict) -> pd.DataFrame:
    bag = []
    for s in LIVE[sisi]:
        d = pool[pool["strategi"] == s]
        if pil.get(s):
            d = d[d["k_" + pil[s]]]
        bag.append(d)
    return pd.concat(bag)


def pilih_konf(pool: pd.DataFrame, sisi: str, awal, akhir) -> dict:
    """pool = sinyal latih sisi ini yang lolos gerbang pasar. Pilih konfirmasi per strategi (berurutan)."""
    pil, rinci = {s: None for s in LIVE[sisi]}, {}
    for s in LIVE[sisi]:
        kand = []
        for k in [None] + OF.KODE:
            g = susun(pool, sisi, dict(pil, **{s: k}))
            n_s = int((g["strategi"] == s).sum())
            if len(g) < MIN_LATIH or (k is not None and n_s < MIN_LATIH):
                continue
            v = BP.nilai_latih(g, awal, akhir)
            kand.append(dict(konf=k, n=n_s, sharpe=round(v["sharpe"], 2), total=round(v["total"], 1)))
        dasar = next((x for x in kand if x["konf"] is None), None)
        if dasar and len(kand) > 1:
            s_maks = max(x["sharpe"] for x in kand)
            if dasar["sharpe"] < s_maks - TOLERANSI:
                dekat = [x for x in kand if x["konf"] is not None and x["sharpe"] >= s_maks - TOLERANSI]
                pil[s] = max(dekat, key=lambda x: (x["n"], x["sharpe"]))["konf"]
        rinci[s] = kand
    return dict(pilihan=pil, kandidat=rinci)


def walk(U: pd.DataFrame, akhir_data: pd.Timestamp, tahun_uji: list[int]):
    per, bag_d, bag_b = {}, [], []
    awal_latih = U["ts"].min()
    for th in tahun_uji:
        mulai = pd.Timestamp(f"{th}-01-01")
        latih = U[U["keluar"] < mulai]
        uji = U[(U["ts"] >= mulai) & (U["ts"] <= min(pd.Timestamp(f"{th}-12-31"), akhir_data))]
        sel = BP.pilih_v2(latih, awal_latih, mulai)           # gerbang pasar: sama dengan model pasar
        dasar = BP.lolos_v2(uji, sel, False)
        info, baru = {}, []
        for sisi in ("long", "short"):
            pool = BP.gerbang(latih[latih["strategi"].isin(LIVE[sisi])], sisi, sel[sisi]["batas"])
            pk = pilih_konf(pool, sisi, awal_latih, mulai)
            du = dasar[dasar["sisi"] == sisi]
            bu = susun(du, sisi, pk["pilihan"])
            baru.append(bu)
            info[sisi] = dict(batas=int(sel[sisi]["batas"]), pilihan=pk["pilihan"], kandidat=pk["kandidat"],
                              uji_dasar={s: BP.ringkas(du[du["strategi"] == s]) for s in LIVE[sisi]},
                              uji_baru={s: BP.ringkas(bu[bu["strategi"] == s]) for s in LIVE[sisi]})
        per[str(th)] = info
        bag_d.append(dasar)
        bag_b.append(pd.concat(baru))
    return pd.concat(bag_d), pd.concat(bag_b), per


# ---------- uji tambahan: stop loss di batas zona nilai ----------
def simulasi_ulang(G: pd.DataFrame, F: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Ulangi simulasi rencana jual tiap sinyal dari candle harian (hasil agregasi candle 1 jam):
    net_ulang = rencana biasa (harus ≈ net tersimpan), net_sl = sama tetapi stop loss di batas zona nilai bila memenuhi syarat."""
    Bs = dict(BS.BIAYA_KONS, **(cfg.get("biaya_short") or {}))
    dr = pd.read_csv(os.path.join(BP.OUT, "radar.csv.gz"), usecols=["tanggal", "symbol", "kelas", "target_pct", "batal_pct"])
    tb = {(r.tanggal, r.symbol): (r.target_pct, r.batal_pct) for r in dr[dr["kelas"] == "naik"].itertuples()}
    per = {s: g.reset_index(drop=True) for s, g in F[F["symbol"].isin(G["symbol"].unique())].groupby("symbol")}
    pos = {s: dict(zip(g["tanggal"], range(len(g)))) for s, g in per.items()}
    arr = {s: tuple(g[k].to_numpy(dtype=float) for k in ("h", "l", "c", "val30", "vah30")) for s, g in per.items()}
    rows = []
    for r in G.itertuples():
        t = pos.get(r.symbol, {}).get(r.tanggal)
        if t is None:
            rows.append((np.nan, np.nan, np.nan, np.nan, False))
            continue
        h, l, c, val, vah = arr[r.symbol]
        e, arah = float(c[t]), ("naik" if r.sisi == "long" else "turun")
        tgt = bt = None
        if r.strategi == "radar_naik":
            tp, bp = tb.get((r.tanggal, r.symbol), (np.nan, np.nan))
            tgt = e * (1 + tp / 100) if np.isfinite(tp) else None
            bt = e * (1 + bp / 100) if np.isfinite(bp) else None
        elif r.strategi == "pantul_fib" and t >= 90:
            a = t - 59
            il = a + int(np.argmin(l[a:t + 1]))
            b = max(0, il - 90)
            ih = b + int(np.argmax(h[b:il + 1]))
            lo, hi = float(l[il]), float(h[ih])
            tgt, bt = lo, lo + (hi - lo) * 0.786
        plan = ST.rencana(e, arah, tgt, bt, None, ST.DEFAULT_RENCANA)
        jalur = (h[t + 1:t + 1 + BT.TAHAN], l[t + 1:t + 1 + BT.TAHAN], c[t + 1:t + 1 + BT.TAHAN])

        def net(p):
            x = ST.simulasi(p, *jalur)
            return (ST.bersih(x["pnl"], cfg.get("biaya")) if r.sisi == "long" else BS.bersih(x["pnl"], x["hari"], Bs)), x["hari"]
        n0, h0 = net(plan)
        if r.sisi == "long":
            sl = val[t] * (1 - SL_PENYANGGA) if np.isfinite(val[t]) else np.nan
            ok = np.isfinite(sl) and SL_MIN <= 1 - sl / e <= SL_MAKS and sl > plan["sl"]
        else:
            sl = vah[t] * (1 + SL_PENYANGGA) if np.isfinite(vah[t]) else np.nan
            ok = np.isfinite(sl) and SL_MIN <= sl / e - 1 <= SL_MAKS and sl < plan["sl"]
        n1, h1 = net(dict(plan, sl=float(sl))) if ok else (n0, h0)
        rows.append((n0, h0, n1, h1, bool(ok)))
    return pd.DataFrame(rows, columns=["net_ulang", "hari_ulang", "net_sl", "hari_sl", "sl_dipakai"], index=G.index)


def lolos(baru: dict, dasar: dict) -> bool:
    return bool(baru["total"] > dasar["total"] and baru["total"] > 0 and baru["sharpe"] >= dasar["sharpe"] + SELISIH_PAKAI
                and baru["maxdd"] >= dasar["maxdd"] - 5)


def f_p(r: dict) -> str:
    return f"{r['total']:+.1f}% · maks turun {r['maxdd']:.1f}% · Sharpe {r['sharpe']} · menang {r['menang']}% · {r['transaksi']} transaksi"


def tahap_model(args) -> int:
    cfg = S.load_config()
    if not os.path.exists(FITUR):
        print("backtest_orderflow/fitur.csv.gz belum ada — jalankan tahap data dulu")
        return 1
    U, ph, F = muat(cfg)
    meta = json.load(open(os.path.join(OUT, "meta.json"), encoding="utf-8")) if os.path.exists(os.path.join(OUT, "meta.json")) else {}
    mp = json.load(open(os.path.join(BP.OUT, "model.json"), encoding="utf-8"))
    hp = json.load(open(os.path.join(BP.OUT, "hasil.json"), encoding="utf-8"))
    now = datetime.now(timezone.utc)
    akhir_data = U["ts"].max()
    tahun_uji = list(range(2023, int(akhir_data.year) + 1))
    oos_awal, oos_akhir = pd.Timestamp(f"{tahun_uji[0]}-01-01"), akhir_data + pd.Timedelta(days=31)
    bersih_ = lambda r: {k: v for k, v in r.items() if not k.startswith("_")}  # noqa: E731
    H = dict(versi=1, dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), data=meta,
             dari=str(U["tanggal"].min()), sampai=str(U["tanggal"].max()),
             konfirmasi={k: dict(nama=v[0], beli=v[1], jual=v[2]) for k, v in OF.KONFIRMASI.items()})

    # gerbang model pasar akhir (untuk tabel deskriptif seluruh data)
    batas = dict(long=int(mp["beli"]["skor_maks"]), short=int(mp["jual"]["skor_maks"]))
    G = pd.concat([BP.gerbang(U[U["strategi"].isin(LIVE[s])], s, batas[s]) for s in ("long", "short")])
    A_ = pd.concat([BP.gerbang(U[U["strategi"] == ("acak_long" if s == "long" else "acak_short")], s, batas[s]) for s in ("long", "short")])
    H["cakupan"] = dict(sinyal=int(len(G)), ada_fitur=int(G["ada_fitur"].sum()), persen=round(float(G["ada_fitur"].mean() * 100), 1))

    # 1) deskriptif: dengan vs tanpa konfirmasi (seluruh data, sinyal live yang lolos gerbang pasar)
    H["per_konfirmasi"] = {}
    for sisi in ("long", "short"):
        for s in LIVE[sisi]:
            d = G[G["strategi"] == s]
            H["per_konfirmasi"][s] = dict(semua=BP.ringkas(d))
            for k in OF.KODE:
                x = banding(d, "k_" + k)
                x["awal"] = banding(d[d["ts"] < oos_awal], "k_" + k, perm=False)
                x["akhir"] = banding(d[d["ts"] >= oos_awal], "k_" + k, perm=False)
                H["per_konfirmasi"][s][k] = x
        nm = "acak_long" if sisi == "long" else "acak_short"
        d = A_[A_["strategi"] == nm]
        H["per_konfirmasi"][nm] = dict(semua=BP.ringkas(d), **{k: banding(d, "k_" + k, perm=False) for k in OF.KODE})
    n_uji = sum(1 for s in sum(LIVE.values(), []) for k in OF.KODE if H["per_konfirmasi"][s][k].get("p") is not None)
    H["bonferroni"] = dict(jumlah_uji=n_uji, ambang=round(0.05 / max(1, n_uji), 4))

    # 2) walk-forward + portofolio di luar sampel
    Td, Tb, H["walk"] = walk(U, akhir_data, tahun_uji)
    DS, BR = "DASAR (model pasar sekarang)", "DASAR + konfirmasi order flow / market profile (walk-forward)"
    rd, rb = BP.uji_portofolio(Td, oos_awal, oos_akhir), BP.uji_portofolio(Tb, oos_awal, oos_akhir)
    kurva = {DS: rd.pop("_kurva"), BR: rb.pop("_kurva")}
    pasang = lambda a, b: dict(benih=BP.BENIH, total_lebih_baik=int((np.array(a["_total"]) > np.array(b["_total"])).sum()),  # noqa: E731
                               sharpe_lebih_baik=int((np.array(a["_sharpe"]) > np.array(b["_sharpe"])).sum()),
                               maxdd_lebih_baik=int((np.array(a["_maxdd"]) > np.array(b["_maxdd"])).sum()),
                               selisih_total_median=round(float(np.median(np.array(a["_total"]) - np.array(b["_total"]))), 1))
    H["oos"] = dict(dari=str(oos_awal.date()), sampai=str(akhir_data.date()), portofolio={DS: bersih_(rd), BR: bersih_(rb)},
                    per_sinyal={DS: BP.ringkas(Td), BR: BP.ringkas(Tb)}, berpasangan=pasang(rb, rd))
    acuan = hp["oos"]["portofolio"].get("Model BARU (aturan lama + batas skor pasar)") or {}
    H["oos"]["cek_dasar"] = dict(model_pasar=dict(total=acuan.get("total"), sharpe=acuan.get("sharpe")),
                                 di_sini=dict(total=rd["total"], sharpe=rd["sharpe"]),
                                 cocok=bool(acuan and abs(acuan["total"] - rd["total"]) < 0.11 and abs(acuan["sharpe"] - rd["sharpe"]) < 0.011))
    ada_pilihan = any(v for th in H["walk"].values() for sisi in th.values() for v in sisi["pilihan"].values())
    pakai = bool(ada_pilihan and lolos(rb, rd))

    # 3) kepekaan: satu konfirmasi dipasang tetap pada satu strategi sepanjang masa uji (BUKAN walk-forward)
    H["tetap"] = {}
    for sisi in ("long", "short"):
        for s in LIVE[sisi]:
            H["tetap"][s] = {}
            for k in OF.KODE:
                d = Td[(Td["strategi"] != s) | Td["k_" + k]]
                H["tetap"][s][k] = dict(bersih_(BP.uji_portofolio(d, oos_awal, oos_akhir)), sinyal=BP.ringkas(d[d["strategi"] == s]))
    # varian level (TPO 30 hari, volume 90 hari) untuk konfirmasi berbasis level
    H["varian"] = {}
    for jenis, nama in (("tpo30", "profil waktu (TPO) 30 hari"), ("vol90", "profil volume 90 hari")):
        V = OF.varian_level(Td, jenis)
        H["varian"][jenis] = dict(nama=nama, hasil={})
        for k in ("va", "poc"):
            kk = OF.konfirmasi(V, k, V["sisi"])
            for s in sum(LIVE.values(), []):
                d = Td[(Td["strategi"] != s) | kk]
                H["varian"][jenis]["hasil"][f"{s}|{k}"] = dict(bersih_(BP.uji_portofolio(d, oos_awal, oos_akhir)),
                                                              sinyal=BP.ringkas(d[d["strategi"] == s]))

    # 3b) EKSPLORASI (dirancang setelah hasil pertama keluar): konfirmasi sebagai urutan prioritas saat slot penuh
    H["prioritas"] = {}
    for k in OF.KODE:
        r = BP.uji_portofolio(Td, oos_awal, oos_akhir, pri="k_" + k)
        H["prioritas"][k] = dict(bersih_(r), total_lebih_baik=int((np.array(r["_total"]) > np.array(rd["_total"])).sum()))

    # 4) uji tambahan: stop loss di batas zona nilai
    R = simulasi_ulang(G, F, cfg)
    Gs = G.join(R)
    ok = Gs["net_ulang"].notna()
    selisih = (Gs.loc[ok, "net_ulang"] - Gs.loc[ok, "net"]).abs()
    H["sl"] = dict(cek=dict(n=int(ok.sum()), dari=int(len(Gs)), selisih_rata=round(float(selisih.mean()), 3),
                            sama=round(float((selisih < 0.05).mean() * 100), 1)), per_strategi={})
    for s in sum(LIVE.values(), []):
        d = Gs[(Gs["strategi"] == s) & ok]
        u = d[d["sl_dipakai"]]
        H["sl"]["per_strategi"][s] = dict(
            n=int(len(d)), sl_berubah=int(len(u)),
            biasa=BP.ringkas(d.assign(net=d["net_ulang"])), zona=BP.ringkas(d.assign(net=d["net_sl"])),
            biasa_yang_berubah=BP.ringkas(u.assign(net=u["net_ulang"])), zona_yang_berubah=BP.ringkas(u.assign(net=u["net_sl"])))
    Rd = simulasi_ulang(Td, F, cfg)
    Ts = Td.join(Rd)
    Ts = Ts[Ts["net_ulang"].notna()]
    T0 = Ts.assign(net=Ts["net_ulang"], hari=Ts["hari_ulang"])
    T1 = Ts.assign(net=Ts["net_sl"], hari=Ts["hari_sl"])
    for X in (T0, T1):
        X["keluar"] = X["ts"] + pd.to_timedelta(X["hari"].clip(lower=1), unit="D")
    s0, s1 = BP.uji_portofolio(T0, oos_awal, oos_akhir), BP.uji_portofolio(T1, oos_awal, oos_akhir)
    kurva["Stop loss di batas zona nilai"] = s1.pop("_kurva")
    s0.pop("_kurva")
    H["sl"]["portofolio"] = dict(biasa=bersih_(s0), zona=bersih_(s1), berpasangan=pasang(s1, s0))
    pakai_sl = lolos(s1, s0)
    H["sl"]["pakai"] = pakai_sl

    # 5) model akhir (dilatih dari semua data) — hanya dipakai radar bila putusan = pakai
    awal_latih = U["ts"].min()
    final = {}
    for sisi in ("long", "short"):
        pool = BP.gerbang(U[U["strategi"].isin(LIVE[sisi]) & (U["keluar"] <= oos_akhir)], sisi, batas[sisi])
        final[sisi] = pilih_konf(pool, sisi, awal_latih, oos_akhir)
    H["putusan"] = dict(pakai=pakai, pakai_sl=pakai_sl, ada_pilihan=bool(ada_pilihan),
                        alasan=f"di luar sampel {H['oos']['dari']} s/d {H['oos']['sampai']}: dengan konfirmasi {f_p(rb)} — DASAR {f_p(rd)}")
    model = dict(versi=1, dibuat=H["dibuat"], dibuat_wib=H["dibuat_wib"], pakai=pakai, pakai_sl=pakai_sl, putusan=H["putusan"]["alasan"],
                 konfirmasi={s: (k if pakai else None) for sisi in final for s, k in final[sisi]["pilihan"].items()})
    H["model"] = dict(konfirmasi=model["konfirmasi"], pilihan_akhir={sisi: final[sisi] for sisi in final})

    # ---------- laporan ----------
    def f_r(r):
        return f"{r['rata']:+.2f}% · menang {r['menang']}% ({r['n']})" if r and r.get("n") else "-"

    def f_k(k):
        return OF.KONFIRMASI[k][0] if k else "tanpa konfirmasi"
    bp_ = H["oos"]["berpasangan"]
    cd = H["oos"]["cek_dasar"]
    if pakai:
        judul = "✅ Konfirmasi order flow / market profile DIPASANG ke radar"
    elif not ada_pilihan:
        judul = "❌ Tidak dipasang — tidak ada satu pun konfirmasi yang terpilih dari data latih"
    else:
        judul = "❌ Tidak dipasang — di luar sampel tidak memenuhi syarat"
    PK = H["per_konfirmasi"]
    jawab = []
    for s in sum(LIVE.values(), []):
        sm = [PK[s][k]["selisih_menang"] for k in OF.KODE if "selisih_menang" in PK[s][k]]
        sr = [PK[s][k]["selisih_rata"] for k in OF.KODE if "selisih_rata" in PK[s][k]]
        sisa = [PK[s][k]["ya"].get("n", 0) / max(1, PK[s]["semua"]["n"]) * 100 for k in OF.KODE]
        jawab.append(f"- {NAMA_S[s]} (tanpa konfirmasi: menang {PK[s]['semua']['menang']}%, rata-rata {PK[s]['semua']['rata']:+.2f}%): "
                     f"sinyal yang terkonfirmasi menangnya {min(sm):+.1f}…{max(sm):+.1f} poin dibanding yang tidak, rata-rata untungnya "
                     f"{min(sr):+.2f}…{max(sr):+.2f} poin; sinyal yang tersisa tinggal {min(sisa):.0f}–{max(sisa):.0f}%.")
    ps = [PK[s][k]["p"] for s in sum(LIVE.values(), []) for k in OF.KODE if PK[s][k].get("p") is not None]
    tt = [r["total"] for x in H["tetap"].values() for r in x.values()]
    ts_ = [r["sharpe"] for x in H["tetap"].values() for r in x.values()]
    pr = list(H["prioritas"].values())
    pm_ = [PK[s][k]["p_menang"] for s in sum(LIVE.values(), []) for k in OF.KODE if PK[s][k].get("p_menang") is not None]
    jawab += [f"- Dari {H['bonferroni']['jumlah_uji']} perbandingan, p terkecil {min(pm_):.3f} untuk tingkat menang dan {min(ps):.3f} untuk rata-rata untung "
              f"(batas layak disebut nyata: {H['bonferroni']['ambang']}) → "
              f"{'ada' if min(ps + pm_) < H['bonferroni']['ambang'] else 'tidak ada satu pun'} selisih yang bisa dibedakan dari kebetulan.",
              f"- Dipakai sebagai saringan tetap (24 susunan, melihat ke belakang): total {min(tt):+.1f}…{max(tt):+.1f}%, Sharpe {min(ts_)}…{max(ts_)} — "
              f"DASAR {rd['total']:+.1f}%, Sharpe {rd['sharpe']}. Sinyal yang tersaring tidak cukup lebih bagus untuk menutup berkurangnya transaksi.",
              f"- Dipakai sebagai urutan prioritas saat slot penuh (eksplorasi): total {min(x['total'] for x in pr):+.1f}…{max(x['total'] for x in pr):+.1f}%, "
              f"menang {min(x['menang'] for x in pr)}…{max(x['menang'] for x in pr)}% — DASAR {rd['total']:+.1f}%, menang {rd['menang']}%."]
    L = ["# 📊 Uji Order Flow & Market Profile", "",
         f"Dibuat {H['dibuat_wib']} · {meta.get('koin', '?')} koin · {meta.get('candle_jam', 0):,} candle 1 jam "
         f"({meta.get('dari', '?')} s/d {meta.get('sampai', '?')}) · sinyal {H['dari']} s/d {H['sampai']} · meme coin tidak ikut", "",
         "## Putusan", "", f"**{judul}.**", "",
         f"- Dengan konfirmasi (dipilih walk-forward): {f_p(rb)}", f"- DASAR (model pasar sekarang): {f_p(rd)}",
         f"- Syarat pasang (ditetapkan di muka): total > DASAR, Sharpe ≥ DASAR + {SELISIH_PAKAI}, maks turun tidak lebih buruk dari DASAR − 5 poin.",
         f"- Stop loss di batas zona nilai: **{'✅ dipakai' if pakai_sl else '❌ tidak dipakai'}** — {f_p(s1)} vs stop loss biasa {f_p(s0)}.", "",
         "## Jawaban singkat: apakah tingkat menang naik?", ""] + jawab + ["",
         "## Yang diuji", "",
         "Sinyal dan hasilnya sama persis dengan uji model pasar (🟢 radar, 🟩 awal Stage 2, 🔻 jual dulu pantulan Stage 4; "
         "rencana jual TP1 5% / SL 12% / maks 30 hari; biaya & pajak sudah dipotong). Bedanya: tiap sinyal diberi fitur dari "
         "candle 1 jam sampai penutupan hari sinyal — delta (beli agresif − jual agresif), arah CVD 3 hari, POC dan zona nilai "
         "(70% volume) 30 hari sebelumnya.", "",
         f"Sinyal live yang lolos gerbang pasar: {H['cakupan']['sinyal']} · punya fitur lengkap: {H['cakupan']['persen']}%. "
         f"Cek data: portofolio DASAR di sini {cd['di_sini']['total']:+.1f}% / Sharpe {cd['di_sini']['sharpe']} — "
         f"di laporan model pasar {cd['model_pasar']['total']}% / {cd['model_pasar']['sharpe']} → {'cocok' if cd['cocok'] else 'TIDAK cocok'}.", "",
         "| Kode | Konfirmasi | Untuk beli | Untuk jual dulu |", "|---|---|---|---|"]
    L += [f"| {k} | {v[0]} | {v[1]} | {v[2]} |" for k, v in OF.KONFIRMASI.items()]

    L += ["", "## Dengan vs tanpa konfirmasi (seluruh data 2020–2026, sinyal live yang lolos gerbang pasar)", "",
          "Isi sel: rata-rata bersih per transaksi · tingkat menang (jumlah sinyal). p = peluang selisih sebesar itu muncul kebetulan "
          f"(uji permutasi di dalam bulan yang sama; 'p menang' untuk selisih tingkat menang, 'p rata-rata' untuk selisih untung). "
          f"Ada {H['bonferroni']['jumlah_uji']} perbandingan, jadi baru layak disebut nyata bila p < {H['bonferroni']['ambang']}."]
    for s in sum(LIVE.values(), []):
        x = H["per_konfirmasi"][s]
        L += ["", f"### {NAMA_S[s]} — semua: {f_r(x['semua'])}", "",
              "| Konfirmasi | Terkonfirmasi | Tidak | Selisih menang | p menang | Selisih rata-rata | p rata-rata | Selisih rata-rata 2020–22 | 2023–26 |", "|---|---|---|---|---|---|---|---|---|"]
        for k in OF.KODE:
            y = x[k]
            sr = f"{y['selisih_rata']:+.2f}" if "selisih_rata" in y else "-"
            sm = f"{y['selisih_menang']:+.1f}" if "selisih_menang" in y else "-"
            p = f"{y['p']:.3f}" if y.get("p") is not None else "-"
            pm = f"{y['p_menang']:.3f}" if y.get("p_menang") is not None else "-"
            sa = f"{y['awal']['selisih_rata']:+.2f}" if "selisih_rata" in y["awal"] else "-"
            sb = f"{y['akhir']['selisih_rata']:+.2f}" if "selisih_rata" in y["akhir"] else "-"
            L.append(f"| {OF.KONFIRMASI[k][0]} | {f_r(y['ya'])} | {f_r(y['tidak'])} | {sm} | {pm} | {sr} | {p} | {sa} | {sb} |")
    L += ["", "Pembanding — beli / short di hari ACAK pada kondisi pasar yang sama (apakah konfirmasi itu memang menandai hari yang lebih baik?):", "",
          "| Konfirmasi | Beli acak: terkonfirmasi | tidak | Short acak: terkonfirmasi | tidak |", "|---|---|---|---|---|"]
    for k in OF.KODE:
        a, b = H["per_konfirmasi"]["acak_long"][k], H["per_konfirmasi"]["acak_short"][k]
        L.append(f"| {OF.KONFIRMASI[k][0]} | {f_r(a['ya'])} | {f_r(a['tidak'])} | {f_r(b['ya'])} | {f_r(b['tidak'])} |")

    L += ["", f"## Uji portofolio di luar sampel ({H['oos']['dari']} s/d {H['oos']['sampai']})", "",
          f"Maks {BP.MAKS_POSISI} posisi, modal dibagi rata, median dari {BP.BENIH} urutan acak (dalam kurung = terendah…tertinggi).", "",
          "| Susunan | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |", "|---|---|---|---|---|---|---|---|"]
    for nm, r in H["oos"]["portofolio"].items():
        pt = " · ".join(f"{y}: {v:+.0f}%" for y, v in r["per_tahun"].items())
        L.append(f"| {nm} | **{r['total']:+.1f}%** ({r['total_min']:+.0f}…{r['total_maks']:+.0f}) | {pt} | {r['maxdd']:.1f}% | {r['sharpe']} | "
                 f"{r['transaksi']} dari {r['kandidat']} | {r['menang']}% | {r['rata']:+.2f}% |")
    L += ["", f"Perbandingan berpasangan ({bp_['benih']} urutan acak yang sama): dengan konfirmasi lebih tinggi totalnya di "
              f"{bp_['total_lebih_baik']}, Sharpe lebih tinggi di {bp_['sharpe_lebih_baik']}, penurunan maksimum lebih kecil di "
              f"{bp_['maxdd_lebih_baik']}; selisih total (median) {bp_['selisih_total_median']:+.1f} poin.", "",
          "### Konfirmasi yang terpilih tiap tahun uji (hanya dari data sebelum tahun itu)", "",
          "| Tahun uji | Strategi | Terpilih | Sharpe latih: tanpa → terbaik | Hasil uji DASAR | Hasil uji dengan pilihan |", "|---|---|---|---|---|---|"]
    for th, info in H["walk"].items():
        for sisi in ("long", "short"):
            x = info[sisi]
            for s in LIVE[sisi]:
                kd = x["kandidat"].get(s) or []
                ds = next((c["sharpe"] for c in kd if c["konf"] is None), None)
                tb_ = max((c for c in kd if c["konf"] is not None), key=lambda c: c["sharpe"], default=None)
                ket = f"{ds} → {tb_['sharpe']} ({OF.KONFIRMASI[tb_['konf']][0]}, {tb_['n']} sinyal)" if tb_ and ds is not None else "data latih kurang"
                L.append(f"| {th} | {NAMA_S[s]} | {f_k(x['pilihan'][s])} | {ket} | {f_r(x['uji_dasar'][s])} | {f_r(x['uji_baru'][s])} |")

    L += ["", "### Bila satu konfirmasi dipasang tetap sepanjang 2023–2026 (BUKAN walk-forward — melihat ke belakang, hanya untuk penjelasan)", "",
          f"Tiap baris: konfirmasi itu dipasang pada SATU strategi, sisanya seperti DASAR. DASAR: {f_p(rd)}.", "",
          "| Strategi | Konfirmasi | Total | Maks turun | Sharpe | Sinyal strategi itu (rata-rata · menang · jumlah) |", "|---|---|---|---|---|---|"]
    for s, x in H["tetap"].items():
        for k, r in x.items():
            L.append(f"| {NAMA_S[s]} | {OF.KONFIRMASI[k][0]} | {r['total']:+.1f}% | {r['maxdd']:.1f}% | {r['sharpe']} | {f_r(r['sinyal'])} |")
    L += ["", "Varian level (konfirmasi berbasis level dihitung dari profil lain):", "",
          "| Profil | Strategi | Konfirmasi | Total | Maks turun | Sharpe | Sinyal strategi itu |", "|---|---|---|---|---|---|---|"]
    for jenis, v in H["varian"].items():
        for key, r in v["hasil"].items():
            s, k = key.split("|")
            L.append(f"| {v['nama']} | {NAMA_S[s]} | {OF.KONFIRMASI[k][0]} | {r['total']:+.1f}% | {r['maxdd']:.1f}% | {r['sharpe']} | {f_r(r['sinyal'])} |")

    L += ["", "### Eksplorasi: konfirmasi sebagai urutan prioritas saat slot penuh (dirancang SETELAH hasil di atas keluar)", "",
          "Semua sinyal DASAR tetap boleh diambil; bedanya, saat slot penuh sinyal yang terkonfirmasi didahulukan. Tidak ikut menentukan putusan.", "",
          "| Didahulukan bila | Total | Maks turun | Sharpe | Menang | Rata-rata/transaksi | Lebih tinggi dari DASAR di … dari 100 urutan |", "|---|---|---|---|---|---|---|",
          f"| (DASAR: urutan acak) | {rd['total']:+.1f}% | {rd['maxdd']:.1f}% | {rd['sharpe']} | {rd['menang']}% | {rd['rata']:+.2f}% | - |"]
    for k, r in H["prioritas"].items():
        L.append(f"| {OF.KONFIRMASI[k][0]} | {r['total']:+.1f}% | {r['maxdd']:.1f}% | {r['sharpe']} | {r['menang']}% | {r['rata']:+.2f}% | {r['total_lebih_baik']} |")
    sl = H["sl"]
    L += ["", "## Uji tambahan: stop loss di batas zona nilai", "",
          f"Beli: stop loss 1% di bawah batas bawah zona nilai; jual dulu: 1% di atas batas atas. Hanya dipakai bila jaraknya "
          f"{SL_MIN * 100:.0f}–{SL_MAKS * 100:.0f}% dari harga masuk dan lebih dekat daripada stop loss biasa. "
          f"Cek simulasi ulang: {sl['cek']['sama']}% sinyal hasilnya sama dengan data tersimpan (selisih rata-rata {sl['cek']['selisih_rata']} poin).", "",
          "| Strategi | Sinyal | Stop loss berubah | Semua sinyal: SL biasa | Semua sinyal: SL zona nilai | Yang berubah saja: SL biasa | SL zona nilai |",
          "|---|---|---|---|---|---|---|"]
    for s, x in sl["per_strategi"].items():
        L.append(f"| {NAMA_S[s]} | {x['n']} | {x['sl_berubah']} | {f_r(x['biasa'])} | {f_r(x['zona'])} | {f_r(x['biasa_yang_berubah'])} | {f_r(x['zona_yang_berubah'])} |")
    sp = sl["portofolio"]
    L += ["", f"Portofolio di luar sampel — SL biasa: {f_p(sp['biasa'])}", "", f"Portofolio di luar sampel — SL zona nilai: {f_p(sp['zona'])}", "",
          f"Berpasangan: SL zona nilai lebih tinggi totalnya di {sp['berpasangan']['total_lebih_baik']} dari {sp['berpasangan']['benih']} urutan, "
          f"Sharpe lebih tinggi di {sp['berpasangan']['sharpe_lebih_baik']}, penurunan maksimum lebih kecil di {sp['berpasangan']['maxdd_lebih_baik']}.", "",
          "## Catatan jujur", "",
          "- Ini bukan order flow penuh. Data gratis hanya memberi volume beli/jual agresif per candle 1 jam; order book, footprint per "
          "harga, absorption dan iceberg tidak ada datanya, jadi tidak diuji.",
          "- Zona nilai memakai rumus yang sama dengan zona akumulasi radar (48 tingkat harga, 70% volume di sekitar POC), dari 30 hari "
          "sebelum hari sinyal.",
          "- Radar 🟢 sudah memakai porsi beli agresif 24 jam dan posisi harga terhadap zona akumulasi di dalam skornya, jadi untuk "
          "sinyal 🟢 sebagian informasi ini sudah terpakai.",
          "- Daftar konfirmasi, cara memilih dan syarat pasang ditulis sebelum data per jam ditarik. Tabel 'dipasang tetap' melihat ke "
          "belakang dan tidak dipakai untuk memutuskan. Uji 'urutan prioritas' ditambahkan setelah hasil pertama keluar (eksplorasi).",
          "- Daftar koin = koin top CMC saat ini (yang sudah mati tidak ikut); untung-rugi dicatat saat posisi ditutup.",
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
    ap.add_argument("tahap", choices=["data", "model", "semua"], nargs="?", default="semua")
    ap.add_argument("--mulai", default="2020-01-01")
    ap.add_argument("--koin", type=int, default=0, help="batasi jumlah koin (0 = semua)")
    args = ap.parse_args()
    if args.tahap in ("data", "semua"):
        rc = tahap_data(args)
        if rc:
            return rc
    if args.tahap in ("model", "semua"):
        return tahap_model(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
