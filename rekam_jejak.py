# -*- coding: utf-8 -*-
"""
REKAM JEJAK ALERT
=================
Setiap alert 🟢/🔴 dicatat: waktu, harga saat alert, target & batas batal.
Tiap jam radar memperbarui catatan itu dengan data candle per jam:
  - harga sekarang & persentase perubahan sejak alert
  - harga tertinggi / terendah sejak alert
  - hasil: "kena target", "kena batal", atau "berjalan" (maks. 14 hari, lalu "selesai")
Rekap 7 hari: berapa alert yang bergerak sesuai arah, rata-rata perubahan, dst.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from analisa import _f, _r, fmt_pct

MAKS_HARI = 14     # tiap alert dipantau maksimal 14 hari
SIMPAN_HARI = 30   # catatan disimpan 30 hari


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _entri(r: dict, kelas: str, ts: str, harga: float, **extra) -> dict:
    e = dict(id=f"{r['symbol']}|{kelas}|{ts}", ts=ts, symbol=r["symbol"], base=r["base"],
             bursa=r.get("bursa", ""), rank=r.get("rank"), kelas=kelas, skor=None, pola=None,
             harga=_r(harga), target=None, target_pct=None, batal=None, batal_pct=None,
             harga_now=_r(harga), chg=0.0, maks=_r(harga), min=_r(harga), maks_pct=0.0, min_pct=0.0,
             hasil="berjalan", ts_hasil=None, isi_ulang=False, ts_update=ts)
    e.update(extra)
    return e


def catat(state: dict, r: dict, now: datetime) -> bool:
    """Catat alert baru. Satu koin+arah hanya punya satu catatan yang 'berjalan'."""
    riw = state.setdefault("riwayat", [])
    kelas = r["kelas"]
    if any(e["symbol"] == r["symbol"] and e["kelas"] == kelas and e["hasil"] == "berjalan" for e in riw):
        return False
    P = r["pola_naik" if kelas == "naik" else "pola_turun"]
    t, b = r.get("target"), r.get("batal")
    riw.append(_entri(
        r, kelas, now.isoformat(timespec="seconds"), float(r["price"]),
        skor=r["skor_naik"] if kelas == "naik" else r["skor_turun"], pola=P["nama"] if P else None,
        target=t["harga"] if t else None, target_pct=t["pct"] if t else None,
        batal=b["harga"] if b else None, batal_pct=b["pct"] if b else None))
    return True


def isi_ulang(state: dict, res_map: dict, src_map: dict) -> int:
    """Sekali saja: buat catatan untuk alert yang terkirim sebelum fitur ini ada.
    Harga diambil dari candle 1 menit di bursa pada menit alert dikirim."""
    if state.get("riwayat_isi_ulang"):
        return 0
    riw = state.setdefault("riwayat", [])
    ids = {e["id"] for e in riw}
    n, gagal = 0, 0
    for key, v in sorted(state.get("alerts2", {}).items(), key=lambda kv: kv[1]["ts"]):
        sym, kelas = key.rsplit("|", 1)
        eid = f"{key}|{v['ts']}"
        r, src = res_map.get(sym), src_map.get(sym)
        if eid in ids or r is None or src is None:
            continue
        try:
            harga = src.harga_pada(sym, int(_ts(v["ts"]).timestamp() * 1000))
        except Exception as ex:
            print(f"  ! harga historis {sym} gagal: {ex}")
            harga = None
        if not harga:
            gagal += 1
            continue
        riw.append(_entri(r, kelas, v["ts"], harga, skor=v.get("skor"), isi_ulang=True))
        n += 1
    if gagal == 0:
        state["riwayat_isi_ulang"] = True
    return n


def perbarui(state: dict, res_map: dict, now: datetime) -> None:
    riw = state.setdefault("riwayat", [])
    for e in riw:
        if e["hasil"] != "berjalan":
            continue
        ts = _ts(e["ts"])
        r = res_map.get(e["symbol"])
        if r is None:
            if now - ts >= timedelta(days=MAKS_HARI):
                e["hasil"], e["ts_hasil"] = "selesai", now.isoformat(timespec="seconds")
            continue
        price = float(r["price"])
        h = r.get("_h")
        seg = h[h["time"] >= pd.Timestamp(ts)] if h is not None and len(h) else pd.DataFrame()
        naik = e["kelas"] == "naik"
        hasil = ts_hasil = harga_akhir = None
        for row in seg.itertuples(index=False):
            if naik:
                kena_b = e["batal"] is not None and row.low <= e["batal"]
                kena_t = e["target"] is not None and row.high >= e["target"]
            else:
                kena_b = e["batal"] is not None and row.high >= e["batal"]
                kena_t = e["target"] is not None and row.low <= e["target"]
            if kena_b:  # kalau dalam 1 jam yang sama dua-duanya tersentuh, anggap batal (konservatif)
                hasil, ts_hasil, harga_akhir = "kena batal", row.time, e["batal"]
                break
            if kena_t:
                hasil, ts_hasil, harga_akhir = "kena target", row.time, e["target"]
                break
        hi = [e["maks"], price] + ([float(seg["high"].max())] if len(seg) else [])
        lo = [e["min"], price] + ([float(seg["low"].min())] if len(seg) else [])
        e["maks"], e["min"] = _r(max(hi)), _r(min(lo))
        if hasil:
            e["hasil"] = hasil
            e["ts_hasil"] = pd.Timestamp(ts_hasil).isoformat()
            e["harga_now"] = _r(harga_akhir)
        else:
            e["harga_now"] = _r(price)
            if now - ts >= timedelta(days=MAKS_HARI):
                e["hasil"], e["ts_hasil"] = "selesai", now.isoformat(timespec="seconds")
        base = e["harga"]
        e["chg"] = _f((e["harga_now"] / base - 1) * 100, 2)
        e["maks_pct"] = _f((e["maks"] / base - 1) * 100, 2)
        e["min_pct"] = _f((e["min"] / base - 1) * 100, 2)
        e["ts_update"] = now.isoformat(timespec="seconds")
    batas = now - timedelta(days=SIMPAN_HARI)
    state["riwayat"] = [e for e in riw if _ts(e["ts"]) >= batas]


def rekap(riw: list, now: datetime, hari: int = 7) -> dict:
    out = {"hari": hari}
    for kelas in ("naik", "turun"):
        E = [e for e in riw if e["kelas"] == kelas and now - _ts(e["ts"]) <= timedelta(days=hari)]
        if not E:
            out[kelas] = dict(n=0)
            continue
        sgn = 1 if kelas == "naik" else -1
        chg = np.array([e["chg"] or 0.0 for e in E])
        benar = int(np.sum(sgn * chg > 0))
        best = max(E, key=lambda e: sgn * (e["chg"] or 0))
        worst = min(E, key=lambda e: sgn * (e["chg"] or 0))
        out[kelas] = dict(n=len(E), benar=benar, persen=round(100 * benar / len(E)), rata=_f(chg.mean(), 2),
                          target=sum(e["hasil"] == "kena target" for e in E),
                          batal=sum(e["hasil"] == "kena batal" for e in E),
                          terbaik=dict(base=best["base"], chg=best["chg"]),
                          terburuk=dict(base=worst["base"], chg=worst["chg"]))
    return out


def rekap_teks(rk: dict) -> list[str]:
    lines = []
    for kelas, ikon, kata in (("naik", "🟢", "naik"), ("turun", "🔴", "turun")):
        x = rk.get(kelas, {})
        if not x.get("n"):
            continue
        lines.append(f"{ikon} {x['benar']}/{x['n']} alert bergerak {kata} ({x['persen']}%), rata-rata "
                     f"{fmt_pct(x['rata'])} · kena target {x['target']} · kena batal {x['batal']}")
    return lines
