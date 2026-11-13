# -*- coding: utf-8 -*-
"""
REKAM JEJAK ALERT
=================
Setiap alert 🟢/🔴 dicatat: waktu, harga saat alert, target, batas batal,
rencana jual (TP1/TP2/SL) dan harga BTC saat itu.
Tiap jam radar memperbarui catatan itu dengan data candle per jam:
  - harga sekarang & persentase perubahan sejak alert
  - harga tertinggi / terendah sejak alert
  - hasil target pola: "kena target", "kena batal", "berjalan" (maks. 14 hari → "selesai")
  - hasil RENCANA JUAL: TP1/TP2/SL/impas + untung-rugi bersih (biaya & pajak)
  - perubahan BTC di periode yang sama (pembanding)
Rekap 7 hari: berapa alert yang sesuai arah, rata-rata, dibanding BTC, dst.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import strategi as ST
from analisa import _f, _r, fmt_pct

MAKS_HARI = 14     # hasil target/batal pola dipantau maksimal 14 hari
SIMPAN_HARI = 35   # catatan disimpan 35 hari


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _entri(r: dict, kelas: str, ts: str, harga: float, **extra) -> dict:
    e = dict(id=f"{r['symbol']}|{kelas}|{ts}", ts=ts, symbol=r["symbol"], base=r["base"],
             bursa=r.get("bursa", ""), rank=r.get("rank"), kelas=kelas, skor=None, pola=None,
             harga=_r(harga), target=None, target_pct=None, batal=None, batal_pct=None,
             harga_now=_r(harga), chg=0.0, maks=_r(harga), min=_r(harga), maks_pct=0.0, min_pct=0.0,
             hasil="berjalan", ts_hasil=None, isi_ulang=False, ts_update=ts, meme=bool(r.get("meme")),
             rencana=None, hasil_rencana="berjalan", pnl_rencana=0.0, pnl_rencana_bersih=None,
             btc_harga=None, btc_chg=None)
    e.update(extra)
    return e


def catat(state: dict, r: dict, now: datetime, r_btc: dict | None = None, jenis: str = "radar") -> bool:
    """Catat alert baru. Satu koin+arah+jenis hanya punya satu catatan yang 'berjalan'.
    jenis: "radar" (sinyal skor), "stage2" (sinyal awal Stage 2) atau "short" (pantulan Stage 4)."""
    riw = state.setdefault("riwayat", [])
    kelas = r["kelas"]
    if any(e["symbol"] == r["symbol"] and e["kelas"] == kelas and e.get("jenis", "radar") == jenis
           and e["hasil"] == "berjalan" for e in riw):
        return False
    P = r["pola_naik" if kelas == "naik" else "pola_turun"]
    t, b = r.get("target"), r.get("batal")
    riw.append(_entri(
        r, kelas, now.isoformat(timespec="seconds"), float(r["price"]),
        skor=r["skor_naik"] if kelas == "naik" else r["skor_turun"], pola=P["nama"] if P else None,
        target=t["harga"] if t else None, target_pct=t["pct"] if t else None,
        batal=b["harga"] if b else None, batal_pct=b["pct"] if b else None,
        rencana=_rencana_json(r.get("rencana")), jenis=jenis,
        btc_harga=_r(float(r_btc["price"])) if r_btc else None))
    return True


def _rencana_json(rc):
    if not rc:
        return None
    return {k: (_r(v) if isinstance(v, float) and k in ("entry", "tp1", "tp2", "sl") else
                (_f(v, 2) if isinstance(v, float) else v)) for k, v in rc.items()}


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


def perbarui(state: dict, res_map: dict, now: datetime, cfg: dict | None = None, r_btc: dict | None = None,
             btc_src=None) -> None:
    cfg = cfg or {}
    R, B = ST.cfg_rencana(cfg), ST.cfg_biaya(cfg)
    btc_now = float(r_btc["price"]) if r_btc else None
    riw = state.setdefault("riwayat", [])
    for e in riw:
        for k, v in (("rencana", None), ("hasil_rencana", "berjalan"), ("pnl_rencana", 0.0),
                     ("pnl_rencana_bersih", None), ("btc_harga", None), ("btc_chg", None), ("meme", False)):
            e.setdefault(k, v)
        ts = _ts(e["ts"])
        # Harga BTC saat alert (untuk catatan lama: ambil dari candle 1 menit, sekali)
        if e["btc_harga"] is None and btc_src is not None and not e.get("btc_gagal"):
            try:
                sym_btc = "BTCUSDT" if btc_src.name != "OKX" else "BTC-USDT"
                e["btc_harga"] = _r(btc_src.harga_pada(sym_btc, int(ts.timestamp() * 1000)))
            except Exception as ex:
                print(f"  ! harga BTC historis gagal: {ex}")
                e["btc_gagal"] = True
        pola_selesai = e["hasil"] != "berjalan"
        rencana_selesai = e["hasil_rencana"] not in ("berjalan", None)
        if pola_selesai and rencana_selesai:
            continue
        r = res_map.get(e["symbol"])
        if r is None:
            if now - ts >= timedelta(days=MAKS_HARI) and not pola_selesai:
                e["hasil"], e["ts_hasil"] = "selesai", now.isoformat(timespec="seconds")
            continue
        price = float(r["price"])
        h = r.get("_h")
        seg = h[h["time"] >= pd.Timestamp(ts)] if h is not None and len(h) else pd.DataFrame()
        naik = e["kelas"] == "naik"
        if not pola_selesai:
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
            if btc_now and e["btc_harga"]:
                e["btc_chg"] = _f((btc_now / e["btc_harga"] - 1) * 100, 2)
        # Rencana jual (TP1/TP2/SL) — catatan lama memakai pengaturan saat ini
        if not rencana_selesai:
            if not e["rencana"]:
                e["rencana"] = _rencana_json(ST.rencana(e["harga"], e["kelas"], e["target"], e["batal"], None, R))
                e["rencana_retro"] = True
            hi_a = np.append(seg["high"].to_numpy(dtype=float), price) if len(seg) else np.array([price])
            lo_a = np.append(seg["low"].to_numpy(dtype=float), price) if len(seg) else np.array([price])
            selesai = now - ts >= timedelta(days=int(e["rencana"].get("maks_hari", 30)))
            res = ST.simulasi(e["rencana"], hi_a, lo_a, np.array([price]), selesai=selesai)
            e["hasil_rencana"] = res["hasil"]
            e["pnl_rencana"] = _f(res["pnl"], 2)
            e["pnl_rencana_bersih"] = _f(ST.bersih(res["pnl"], B), 2)
        e["ts_update"] = now.isoformat(timespec="seconds")
    batas = now - timedelta(days=SIMPAN_HARI)
    state["riwayat"] = [e for e in riw if _ts(e["ts"]) >= batas]


def rekap(riw: list, now: datetime, hari: int = 7) -> dict:
    out = {"hari": hari}
    for kelas in ("naik", "turun", "stage2", "short"):
        kls, jenis = {"naik": ("naik", "radar"), "turun": ("turun", "radar"), "stage2": ("naik", "stage2"),
                      "short": ("turun", "short")}[kelas]
        E = [e for e in riw if e["kelas"] == kls and e.get("jenis", "radar") == jenis
             and now - _ts(e["ts"]) <= timedelta(days=hari)]
        if not E:
            out[kelas] = dict(n=0)
            continue
        sgn = -1 if kls == "turun" else 1
        chg = np.array([e["chg"] or 0.0 for e in E])
        benar = int(np.sum(sgn * chg > 0))
        best = max(E, key=lambda e: sgn * (e["chg"] or 0))
        worst = min(E, key=lambda e: sgn * (e["chg"] or 0))
        x = dict(n=len(E), benar=benar, persen=round(100 * benar / len(E)), rata=_f(chg.mean(), 2),
                 target=sum(e["hasil"] == "kena target" for e in E),
                 batal=sum(e["hasil"] == "kena batal" for e in E),
                 terbaik=dict(base=best["base"], chg=best["chg"]),
                 terburuk=dict(base=worst["base"], chg=worst["chg"]))
        rb = [e["pnl_rencana_bersih"] for e in E if e.get("pnl_rencana_bersih") is not None]
        if rb:
            x["rencana"] = dict(n=len(rb), menang=sum(v > 0 for v in rb), rata_bersih=_f(float(np.mean(rb)), 2),
                                tp1=sum(1 for e in E if e.get("hasil_rencana") in ("kena TP1", "kena TP2", "impas setelah TP1")),
                                sl=sum(1 for e in E if e.get("hasil_rencana") == "kena SL"))
        bb = [(e["chg"] or 0, e["btc_chg"]) for e in E if e.get("btc_chg") is not None]
        if bb:
            x["btc"] = dict(n=len(bb), rata_btc=_f(float(np.mean([b for _, b in bb])), 2),
                            lebih_baik=sum(1 for c, b in bb if sgn * (c - b) > 0))
        out[kelas] = x
    return out


def rekap_teks(rk: dict) -> list[str]:
    lines = []
    for kelas, ikon, kata in (("naik", "🟢", "naik"), ("turun", "🔴", "turun"), ("stage2", "🟩", "naik"),
                              ("short", "🔻", "turun")):
        x = rk.get(kelas, {})
        if not x.get("n"):
            continue
        nm = {"stage2": " awal Stage 2", "short": " short"}.get(kelas, "")
        lines.append(f"{ikon} {x['benar']}/{x['n']} alert{nm} bergerak {kata} ({x['persen']}%), rata-rata "
                     f"{fmt_pct(x['rata'])} · kena target {x['target']} · kena batal {x['batal']}")
        if x.get("rencana"):
            rc = x["rencana"]
            lines.append(f"   📋 Rencana jual: {rc['menang']}/{rc['n']} untung, rata-rata bersih "
                         f"{fmt_pct(rc['rata_bersih'])} · sentuh TP1 {rc['tp1']} · kena SL {rc['sl']}")
        if x.get("btc"):
            b = x["btc"]
            lines.append(f"   ₿ BTC periode sama {fmt_pct(b['rata_btc'])} · {b['lebih_baik']}/{b['n']} alert lebih baik dari BTC")
    return lines
