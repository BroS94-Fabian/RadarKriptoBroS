#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKTEST MODE JANGKA PENDEK (sideways, tahan maks. 3 jam)
=========================================================
Data candle 1 jam ±12 bulan untuk koin top CMC (bukan meme) di Binance.
Menguji 12 variasi syarat masuk × 20 variasi TP/SL = 240 kombinasi.

Supaya tidak tertipu "kebetulan cocok":
  - Kombinasi terbaik DIPILIH memakai periode 1 (6 bulan pertama) saja,
  - lalu DIUJI di periode 2 (6 bulan berikutnya) yang tidak dipakai saat memilih.
Hasil bersih sudah dipotong biaya beli/jual 0,1%, pajak jual 0,21% dan slippage 0,05% per sisi.

Hasil: backtest_jp/LAPORAN.md, backtest_jp/hasil.json
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

import jangka_pendek as JP
import scanner as S
import strategi as ST

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_jp")
VAR_MASUK = [dict(rsi_max=r, posisi_max=p, lebar_min=l) for r in (30, 35, 40) for p in (0.2, 0.3) for l in (0.03, 0.05)]
VAR_KELUAR = [dict(tp=t, sl=s) for t in ("1.0", "1.5", "2.0", "2.5", "tengah") for s in ("1.0", "1.5", "2.0", "support")]
REZIM_KODE = {"naik": 0, "netral": 1, "turun": 2}
HASIL_KODE = {"kena TP": 0, "kena SL": 1, "waktu habis": 2}


def label_masuk(i):
    v = VAR_MASUK[i]
    return f"RSI≤{v['rsi_max']}, posisi≤{int(v['posisi_max'] * 100)}%, lebar≥{int(v['lebar_min'] * 100)}%"


def label_keluar(i):
    v = VAR_KELUAR[i]
    tp = "TP tengah kisaran" if v["tp"] == "tengah" else f"TP +{v['tp']}%"
    sl = "SL bawah support" if v["sl"] == "support" else f"SL −{v['sl']}%"
    return f"{tp} / {sl}"


def ambil_jam(bn: S.Binance, symbol: str, hari: int) -> pd.DataFrame:
    rows, end = [], int(time.time() * 1000)
    while len(rows) < hari * 24:
        batch = bn._get("/api/v3/klines", {"symbol": symbol, "interval": "1h", "limit": 1000, "endTime": end})
        if not batch:
            break
        rows = batch + rows
        end = int(batch[0][0]) - 1
        if len(batch) < 1000:
            break
        time.sleep(0.4)
    df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v", "ct", "qv", "n", "tbv", "tbqv", "x"])
    now_ms = int(time.time() * 1000)
    out = pd.DataFrame({"time": pd.to_datetime(df["t"].astype("int64"), unit="ms", utc=True),
                        "open": df["o"].astype(float), "high": df["h"].astype(float), "low": df["l"].astype(float),
                        "close": df["c"].astype(float), "qvol": df["qv"].astype(float),
                        "closed": df["ct"].astype("int64") < now_ms})
    out = out[out["closed"]].drop_duplicates("time").sort_values("time").reset_index(drop=True)
    return out.tail(hari * 24).reset_index(drop=True)


def proses(job):
    ci, h, rezim, P0 = job
    F = JP.fitur(h, P0["jendela"])
    hi, lo, cl = h["high"].to_numpy(), h["low"].to_numpy(), h["close"].to_numpy()
    rl, rh, sp = F["rng_lo"].to_numpy(), F["rng_hi"].to_numpy(), F["support"].to_numpy()
    jam = ((h["time"] - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(hours=1)).to_numpy()
    n, H = len(h), int(P0["tahan_jam"])
    out = []
    for vi, vm in enumerate(VAR_MASUK):
        P = dict(P0, **vm)
        idx = np.where(JP.mask_masuk(F, P).to_numpy())[0]
        last = -10
        for i in idx:
            if i >= n - H or i - last < H:
                continue
            last = i
            baris = {"rng_lo": rl[i], "rng_hi": rh[i], "support": sp[i]}
            for vk, vx in enumerate(VAR_KELUAR):
                plan = JP.rencana_jp(float(cl[i]), baris, dict(P, **vx))
                if plan is None:
                    continue
                res = JP.simulasi_jp(plan, hi[i + 1:i + 1 + H], lo[i + 1:i + 1 + H], cl[i + 1:i + 1 + H])
                out.append((vi, vk, ci, int(jam[i]), rezim[i], JP.bersih_jp(res["pnl"], P),
                            HASIL_KODE[res["hasil"]]))
    return out


def stat(x: np.ndarray) -> dict:
    if len(x) == 0:
        return dict(n=0)
    pos, neg = x[x > 0].sum(), -x[x < 0].sum()
    t = float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std() > 0 else None
    return dict(n=int(len(x)), menang=round(float((x > 0).mean() * 100), 1), rata=round(float(x.mean()), 3),
                median=round(float(np.median(x)), 3), total=round(float(x.sum()), 1),
                pf=round(float(pos / neg), 2) if neg > 0 else None, t=round(t, 2) if t is not None else None)


def tabel(rows, kolom="Kombinasi"):
    L = [f"| {kolom} | Trade | Menang | Rata-rata bersih | Median | Profit factor | t |", "|---|---|---|---|---|---|---|"]
    for lbl, s in rows:
        if not s.get("n"):
            L.append(f"| {lbl} | 0 | - | - | - | - | - |")
            continue
        L.append(f"| {lbl} | {s['n']} | {s['menang']}% | {s['rata']:+.2f}% | {s['median']:+.2f}% | "
                 f"{s['pf'] if s['pf'] is not None else '-'} | {s['t'] if s['t'] is not None else '-'} |")
    return L


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hari", type=int, default=365)
    ap.add_argument("--maks-koin", type=int, default=100)
    args = ap.parse_args()
    t0 = time.time()
    cfg = S.load_config()
    P0 = dict(JP.DEFAULT_JP, **(cfg.get("jangka_pendek") or {}))
    state = S.load_state()
    now = datetime.now(timezone.utc)
    rank_list, src_rank = S.ambil_ranking(cfg, state, now)
    bn = S.Binance()
    tick = bn.tickers(cfg["quote"])
    koin = []
    for c in sorted(rank_list, key=lambda x: x["rank"]):
        b = S.ALIAS_BINANCE.get(c["symbol"], c["symbol"])
        if c.get("stabil") or c["symbol"] in cfg["abaikan"] or b not in tick or c.get("meme") or ST.is_meme(c["symbol"]):
            continue
        koin.append((tick[b]["symbol"], c["symbol"], c["rank"]))
    koin = koin[:args.maks_koin]
    print(f"{len(koin)} koin, ambil {args.hari} hari candle 1 jam...")

    btc_d = bn.candles("BTCUSDT", "1d", 1000)
    btc_d = btc_d[btc_d["closed"]].reset_index(drop=True)
    rz_hari = dict(zip(btc_d["time"].dt.strftime("%Y-%m-%d"), ST.rezim_series(btc_d["close"].to_numpy())))

    data = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(ambil_jam, bn, k[0], args.hari): k for k in koin}
        for f in as_completed(futs):
            try:
                d = f.result()
                if len(d) > 24 * 30:
                    data[futs[f][0]] = d
            except Exception as e:
                print("  ! gagal", futs[f][0], e)
    print(f"Data {len(data)} koin siap ({time.time() - t0:.0f} dtk). Simulasi {len(VAR_MASUK) * len(VAR_KELUAR)} kombinasi...")

    syms = sorted(data)
    jobs = []
    for ci, sym in enumerate(syms):
        h = data[sym]
        kemarin = (h["time"] - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")   # rezim hari sebelumnya (tanpa bocoran)
        rezim = np.array([REZIM_KODE.get(rz_hari.get(d, "netral"), 1) for d in kemarin], dtype=np.int8)
        jobs.append((ci, h, rezim, P0))
    rows = []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for out in ex.map(proses, jobs, chunksize=2):
            rows.extend(out)
    if not rows:
        print("Tidak ada trade.")
        return 1
    df = pd.DataFrame(rows, columns=["vi", "vk", "ci", "jam", "rezim", "bersih", "hasil"])
    t_awal, t_akhir = df["jam"].min(), df["jam"].max()
    batas = t_awal + (t_akhir - t_awal) // 2
    df["periode"] = np.where(df["jam"] < batas, 1, 2)
    jam_ts = lambda j: datetime.fromtimestamp(int(j) * 3600, tz=timezone.utc).strftime("%d %b %Y")  # noqa: E731

    # Pembanding: beli di sembarang jam saat sideways, jual 3 jam kemudian
    acak = []
    for sym in syms:
        h = data[sym]
        kemarin = (h["time"] - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
        rz = np.array([rz_hari.get(d, "netral") for d in kemarin])
        c = h["close"].to_numpy()
        r3 = (c[3:] / c[:-3] - 1) * 100
        acak.extend(r3[rz[:-3] == "netral"][::6])
    acak = np.array([JP.bersih_jp(x, P0) for x in acak])

    side = df[df["rezim"] == 1]
    grp = {k: g["bersih"].to_numpy() for k, g in side.groupby(["vi", "vk", "periode"])}
    kombinasi = []
    for vi in range(len(VAR_MASUK)):
        for vk in range(len(VAR_KELUAR)):
            p1, p2 = grp.get((vi, vk, 1), np.array([])), grp.get((vi, vk, 2), np.array([]))
            kombinasi.append(dict(vi=vi, vk=vk, masuk=label_masuk(vi), keluar=label_keluar(vk),
                                  p1=stat(p1), p2=stat(p2), semua=stat(np.concatenate([p1, p2]))))
    cand = [k for k in kombinasi if k["p1"].get("n", 0) >= 150]
    cand.sort(key=lambda k: -k["p1"]["rata"])
    best = cand[0] if cand else None
    top = cand[:10]
    lolos = bool(best and best["p2"].get("n", 0) >= 50 and best["p2"]["rata"] > 0 and best["p1"]["rata"] > 0)

    hasil = dict(meta=dict(dibuat=now.isoformat(timespec="seconds"), dibuat_wib=S.now_wib_str(now), koin=len(syms),
                           dari=jam_ts(t_awal), sampai=jam_ts(t_akhir), batas_periode=jam_ts(batas),
                           trade_sideways=int(len(side)), durasi=round(time.time() - t0)),
                 pembanding_acak=stat(acak), terbaik=best, top10=top, lolos=lolos)
    if best:
        sub = df[(df["vi"] == best["vi"]) & (df["vk"] == best["vk"])]
        hasil["terbaik_semua_rezim"] = {nm: stat(sub[sub["rezim"] == kd]["bersih"].to_numpy())
                                        for nm, kd in REZIM_KODE.items()}
        hb = sub[sub["rezim"] == 1]["hasil"].value_counts().to_dict()
        hasil["terbaik_hasil"] = {nm: int(hb.get(kd, 0)) for nm, kd in HASIL_KODE.items()}
        hasil["terbaik_per_bulan"] = {
            str(m): stat(g["bersih"].to_numpy())
            for m, g in sub[sub["rezim"] == 1].groupby(pd.to_datetime(sub[sub["rezim"] == 1]["jam"] * 3600, unit="s").dt.to_period("M"))}
        per_koin = sub[sub["rezim"] == 1].groupby("ci")["bersih"].sum().sort_values()
        hasil["terbaik_koin"] = dict(untung=int((per_koin > 0).sum()), rugi=int((per_koin <= 0).sum()))

    m = hasil["meta"]
    L = ["# ⚡ Backtest Mode Jangka Pendek (sideways, tahan maks. 3 jam)", "",
         f"Dibuat {m['dibuat_wib']} · data candle 1 jam {m['dari']} s/d {m['sampai']} · {m['koin']} koin (bukan meme) · "
         f"{len(VAR_MASUK) * len(VAR_KELUAR)} kombinasi diuji.", "",
         f"Periode 1 (untuk MEMILIH): {m['dari']} – {m['batas_periode']} · Periode 2 (untuk MENGUJI): {m['batas_periode']} – {m['sampai']}.",
         "Hanya trade saat BTC sideways. Bersih = setelah biaya 0,1% beli/jual, pajak jual 0,21%, slippage 0,05%/sisi.", "",
         "## Pembanding", "", *tabel([("Beli di jam acak saat sideways, jual 3 jam kemudian", hasil["pembanding_acak"])], "Cara"), ""]
    if best:
        L += ["## Kombinasi terbaik (dipilih di periode 1)", "",
              f"**Syarat masuk:** {best['masuk']} · **Jual:** {best['keluar']} · tutup paksa 3 jam", "",
              *tabel([("Periode 1 (memilih)", best["p1"]), ("Periode 2 (menguji)", best["p2"]),
                      ("Gabungan", best["semua"])], "Periode"), "",
              f"**Lolos uji (positif di kedua periode): {'YA ✅' if lolos else 'TIDAK ❌'}**", "",
              "### Hasil trade (sideways)", "",
              " · ".join(f"{k}: {v}" for k, v in hasil["terbaik_hasil"].items()), "",
              f"Per koin (total): {hasil['terbaik_koin']['untung']} koin untung, {hasil['terbaik_koin']['rugi']} koin rugi.", "",
              "### Kombinasi yang sama di kondisi BTC lain", "",
              *tabel([(f"BTC {k}", v) for k, v in hasil["terbaik_semua_rezim"].items()], "Kondisi"), "",
              "### Per bulan (sideways)", "",
              *tabel(list(hasil["terbaik_per_bulan"].items()), "Bulan"), "",
              "## 10 kombinasi terbaik di periode 1 — dan hasilnya di periode 2", "",
              "| Syarat masuk | Jual | P1 trade | P1 rata-rata | P2 trade | P2 rata-rata | P2 menang |",
              "|---|---|---|---|---|---|---|"]
        for k in top:
            L.append(f"| {k['masuk']} | {k['keluar']} | {k['p1']['n']} | {k['p1']['rata']:+.2f}% | "
                     f"{k['p2'].get('n', 0)} | {k['p2'].get('rata', 0):+.2f}% | {k['p2'].get('menang', 0)}% |")
    L += ["", "## Keterbatasan", "",
          "- Masuk di harga penutupan candle 1 jam; bila TP & SL tersentuh di jam yang sama dianggap SL dulu.",
          "- Daftar koin = top CMC saat ini (survivorship bias). Spread & antrian order di bursa Indonesia bisa berbeda.",
          "- Hasil masa lalu tidak menjamin hasil masa depan."]
    md = "\n".join(L) + "\n"
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "hasil.json"), "w", encoding="utf-8") as f:
        json.dump(hasil, f, ensure_ascii=False, indent=1, default=float)
    with open(os.path.join(OUT, "LAPORAN.md"), "w", encoding="utf-8") as f:
        f.write(md)
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as f:
            f.write(md)
    print(md)
    print(f"Selesai {time.time() - t0:.0f} dtk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
