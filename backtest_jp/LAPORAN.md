# ⚡ Backtest Mode Jangka Pendek (sideways, tahan maks. 3 jam)

Dibuat 4 Nov 2026 17:59 WIB · data candle 1 jam 07 Nov 2025 s/d 04 Nov 2026 · 100 koin (bukan meme) · 240 kombinasi diuji.

Periode 1 (untuk MEMILIH): 07 Nov 2025 – 07 May 2026 · Periode 2 (untuk MENGUJI): 07 May 2026 – 04 Nov 2026.
Hanya trade saat BTC sideways. Bersih = setelah biaya 0,1% beli/jual, pajak jual 0,21%, slippage 0,05%/sisi.

## Pembanding

| Cara | Trade | Menang | Rata-rata bersih | Median | Profit factor | t |
|---|---|---|---|---|---|---|
| Beli di jam acak saat sideways, jual 3 jam kemudian | 24454 | 29.5% | -0.46% | -0.51% | 0.41 | -45.82 |

## Kombinasi terbaik (dipilih di periode 1)

**Syarat masuk:** RSI≤35, posisi≤20%, lebar≥5% · **Jual:** TP +1.0% / SL −1.0% · tutup paksa 3 jam

| Periode | Trade | Menang | Rata-rata bersih | Median | Profit factor | t |
|---|---|---|---|---|---|---|
| Periode 1 (memilih) | 165 | 29.7% | -0.68% | -0.84% | 0.17 | -10.14 |
| Periode 2 (menguji) | 178 | 33.7% | -0.56% | -0.61% | 0.21 | -8.84 |
| Gabungan | 343 | 31.8% | -0.61% | -0.67% | 0.19 | -13.4 |

**Lolos uji (positif di kedua periode): TIDAK ❌**

### Hasil trade (sideways)

kena TP: 100 · kena SL: 138 · waktu habis: 105

Per koin (total): 7 koin untung, 45 koin rugi.

### Kombinasi yang sama di kondisi BTC lain

| Kondisi | Trade | Menang | Rata-rata bersih | Median | Profit factor | t |
|---|---|---|---|---|---|---|
| BTC naik | 741 | 31.7% | -0.52% | -0.49% | 0.21 | -17.93 |
| BTC netral | 343 | 31.8% | -0.61% | -0.67% | 0.19 | -13.4 |
| BTC turun | 938 | 34.5% | -0.53% | -0.53% | 0.23 | -19.49 |

### Per bulan (sideways)

| Bulan | Trade | Menang | Rata-rata bersih | Median | Profit factor | t |
|---|---|---|---|---|---|---|
| 2026-01 | 56 | 23.2% | -0.91% | -1.51% | 0.11 | -8.07 |
| 2026-03 | 90 | 31.1% | -0.59% | -0.52% | 0.2 | -6.64 |
| 2026-04 | 19 | 42.1% | -0.42% | -0.35% | 0.33 | -2.08 |
| 2026-05 | 41 | 43.9% | -0.53% | -0.59% | 0.26 | -3.67 |
| 2026-06 | 7 | 42.9% | -0.32% | -0.06% | 0.39 | -0.94 |
| 2026-07 | 37 | 21.6% | -0.66% | -0.63% | 0.12 | -5.41 |
| 2026-08 | 31 | 22.6% | -0.54% | -0.37% | 0.13 | -4.22 |
| 2026-10 | 34 | 52.9% | -0.27% | +0.49% | 0.49 | -1.75 |
| 2026-11 | 28 | 21.4% | -0.88% | -1.51% | 0.11 | -5.77 |

## 10 kombinasi terbaik di periode 1 — dan hasilnya di periode 2

| Syarat masuk | Jual | P1 trade | P1 rata-rata | P2 trade | P2 rata-rata | P2 menang |
|---|---|---|---|---|---|---|
| RSI≤35, posisi≤20%, lebar≥5% | TP +1.0% / SL −1.0% | 165 | -0.68% | 178 | -0.56% | 33.7% |
| RSI≤35, posisi≤20%, lebar≥3% | TP +1.0% / SL −1.0% | 175 | -0.68% | 216 | -0.56% | 29.2% |
| RSI≤40, posisi≤30%, lebar≥3% | TP +1.0% / SL −1.0% | 395 | -0.69% | 573 | -0.51% | 33.7% |
| RSI≤40, posisi≤30%, lebar≥5% | TP +1.0% / SL −1.0% | 377 | -0.69% | 451 | -0.47% | 39.0% |
| RSI≤40, posisi≤20%, lebar≥5% | TP +1.0% / SL −1.0% | 260 | -0.70% | 289 | -0.53% | 35.6% |
| RSI≤40, posisi≤20%, lebar≥3% | TP +1.0% / SL −1.0% | 275 | -0.71% | 362 | -0.56% | 30.1% |
| RSI≤35, posisi≤30%, lebar≥3% | TP +1.0% / SL −1.0% | 235 | -0.71% | 298 | -0.48% | 33.9% |
| RSI≤35, posisi≤30%, lebar≥5% | TP +1.0% / SL −1.0% | 224 | -0.72% | 247 | -0.47% | 38.1% |
| RSI≤35, posisi≤20%, lebar≥5% | TP +1.0% / SL bawah support | 156 | -0.72% | 167 | -0.57% | 34.7% |
| RSI≤35, posisi≤30%, lebar≥5% | TP +1.0% / SL bawah support | 214 | -0.72% | 235 | -0.49% | 38.7% |

## Keterbatasan

- Masuk di harga penutupan candle 1 jam; bila TP & SL tersentuh di jam yang sama dianggap SL dulu.
- Daftar koin = top CMC saat ini (survivorship bias). Spread & antrian order di bursa Indonesia bisa berbeda.
- Hasil masa lalu tidak menjamin hasil masa depan.
