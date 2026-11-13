# 🔴 Backtest Short Selling

Dibuat 13 Nov 2026 18:48 WIB · 127 koin · 2020-09-17 s/d 2026-10-13 · periode 1 < 2023-09-30 ≤ periode 2

Biaya konservatif: fee buka 0.1% + pajak 0.21% + fee tutup 0.1% + funding 0.03%/hari. Kolom 'Futures murah' = 0,05% + 0,05% tanpa pajak & funding.

Syarat lolos: ≥30 sinyal, ≥15 per periode, rata-rata positif di KEDUA periode, dan lebih baik dari short acak di minggu yang sama.

## Strategi yang lolos

- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · bukan meme · Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari)** → 225 sinyal, menang 56.4%, rata-rata +8.21% (P1 +4.53% (27, menang 66.7%) · P2 +8.71% (198, menang 55.1%)) · lebih baik dari acak +5.44% (t 4.58)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · termasuk meme · Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari)** → 244 sinyal, menang 57.0%, rata-rata +8.21% (P1 +4.53% (27, menang 66.7%) · P2 +8.67% (217, menang 55.8%)) · lebih baik dari acak +5.02% (t 4.42)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · bukan meme · TP1 −5% (tutup 50%), TP2 target/−10%, SL +12%** → 225 sinyal, menang 86.7%, rata-rata +2.65% (P1 +3.20% (27, menang 92.6%) · P2 +2.58% (198, menang 85.9%)) · lebih baik dari acak +1.65% (t 3.47)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · termasuk meme · TP1 −5% (tutup 50%), TP2 target/−10%, SL +12%** → 244 sinyal, menang 86.1%, rata-rata +2.60% (P1 +3.20% (27, menang 92.6%) · P2 +2.52% (217, menang 85.3%)) · lebih baik dari acak +1.58% (t 3.44)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · termasuk meme · TP1 −5% (tutup 50%), TP2 target/−10%, SL +8%** → 244 sinyal, menang 78.3%, rata-rata +2.17% (P1 +2.64% (27, menang 85.2%) · P2 +2.11% (217, menang 77.4%)) · lebih baik dari acak +1.74% (t 3.8)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · bukan meme · TP1 −5% (tutup 50%), TP2 target/−10%, SL +8%** → 225 sinyal, menang 78.2%, rata-rata +2.11% (P1 +2.64% (27, menang 85.2%) · P2 +2.04% (198, menang 77.3%)) · lebih baik dari acak +1.73% (t 3.61)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tren turun · bukan meme · TP1 −5% (tutup 50%), TP2 target/−10%, SL +12%** → 162 sinyal, menang 85.8%, rata-rata +2.01% (P1 +2.23% (22, menang 90.9%) · P2 +1.97% (140, menang 85.0%)) · lebih baik dari acak +1.62% (t 2.96)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tren turun · termasuk meme · TP1 −5% (tutup 50%), TP2 target/−10%, SL +12%** → 173 sinyal, menang 85.5%, rata-rata +2.00% (P1 +2.23% (22, menang 90.9%) · P2 +1.97% (151, menang 84.8%)) · lebih baik dari acak +1.63% (t 3.04)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tren turun · bukan meme · Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari)** → 162 sinyal, menang 54.9%, rata-rata +7.98% (P1 +1.78% (22, menang 63.6%) · P2 +8.95% (140, menang 53.6%)) · lebih baik dari acak +5.33% (t 3.73)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tren turun · termasuk meme · Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari)** → 173 sinyal, menang 55.5%, rata-rata +7.92% (P1 +1.78% (22, menang 63.6%) · P2 +8.81% (151, menang 54.3%)) · lebih baik dari acak +4.77% (t 3.45)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tren turun · termasuk meme · TP1 −5% (tutup 50%), TP2 target/−10%, SL +8%** → 173 sinyal, menang 75.1%, rata-rata +1.29% (P1 +1.54% (22, menang 81.8%) · P2 +1.26% (151, menang 74.2%)) · lebih baik dari acak +1.80% (t 3.38)
- **Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · termasuk meme · TP −5% / SL +5% (tutup semua)** → 244 sinyal, menang 66.8%, rata-rata +1.20% (P1 +1.17% (27, menang 66.7%) · P2 +1.20% (217, menang 66.8%)) · lebih baik dari acak +1.21% (t 4.19)

### Per tahun — Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · bukan meme · Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari)

| Tahun | Sinyal | Menang | Rata-rata |
|---|---|---|---|
| 2021 | 1 | 100.0% | +41.82% |
| 2022 | 16 | 75.0% | +5.92% |
| 2023 | 13 | 61.5% | -0.41% |
| 2024 | 23 | 39.1% | -2.30% |
| 2025 | 133 | 60.9% | +13.71% |
| 2026 | 39 | 41.0% | -1.41% |

Aktif di 36 bulan · maks 102 sinyal sebulan · 3 bulan terbaik menyumbang 103.3% total untung

### Per tahun — Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · bukan meme · TP1 −5% (tutup 50%), TP2 target/−10%, SL +12%

| Tahun | Sinyal | Menang | Rata-rata |
|---|---|---|---|
| 2021 | 1 | 100.0% | +13.63% |
| 2022 | 16 | 93.8% | +3.56% |
| 2023 | 13 | 92.3% | +1.79% |
| 2024 | 23 | 73.9% | +1.13% |
| 2025 | 133 | 91.7% | +3.57% |
| 2026 | 39 | 71.8% | +0.06% |

Aktif di 36 bulan · maks 102 sinyal sebulan · 3 bulan terbaik menyumbang 87.1% total untung

### Per tahun — Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah · BTC tidak tren naik · termasuk meme · TP1 −5% (tutup 50%), TP2 target/−10%, SL +12%

| Tahun | Sinyal | Menang | Rata-rata |
|---|---|---|---|
| 2021 | 1 | 100.0% | +13.63% |
| 2022 | 16 | 93.8% | +3.56% |
| 2023 | 13 | 92.3% | +1.79% |
| 2024 | 24 | 75.0% | +1.15% |
| 2025 | 149 | 89.9% | +3.32% |
| 2026 | 41 | 73.2% | +0.44% |

Aktif di 36 bulan · maks 115 sinyal sebulan · 3 bulan terbaik menyumbang 84.5% total untung

## Semua kombinasi

| Strategi | Pasar | Meme | Aturan | Sinyal | Menang | Rata-rata | PF | Periode 1 | Periode 2 | vs acak | Futures murah |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Hari pertama Stage 4 terkonfirmasi | BTC tren turun | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 823 | 70.6% | -0.51% | 0.86 | +0.56% (361, menang 76.7%) | -1.34% (462, menang 65.8%) | -0.51% | -0.04% |
| Hari pertama Stage 4 terkonfirmasi | BTC tren turun | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 823 | 63.1% | -0.31% | 0.9 | +0.47% (361, menang 68.7%) | -0.92% (462, menang 58.7%) | -0.29% | +0.12% |
| Hari pertama Stage 4 terkonfirmasi | BTC tren turun | bukan meme | TP −5% / SL +5% (tutup semua) | 823 | 53.3% | -0.14% | 0.95 | +0.20% (361, menang 56.8%) | -0.40% (462, menang 50.6%) | +0.05% | +0.24% |
| Hari pertama Stage 4 terkonfirmasi | BTC tren turun | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 823 | 28.7% | -2.17% | 0.71 | -3.03% (361, menang 23.8%) | -1.49% (462, menang 32.5%) | -0.27% | -1.07% |
| Hari pertama Stage 4 terkonfirmasi | BTC tidak tren naik | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 1138 | 73.6% | -0.04% | 0.99 | +0.98% (486, menang 79.8%) | -0.80% (652, menang 68.9%) | -0.50% | +0.43% |
| Hari pertama Stage 4 terkonfirmasi | BTC tidak tren naik | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 1138 | 66.5% | +0.11% | 1.04 | +0.80% (486, menang 72.0%) | -0.40% (652, menang 62.4%) | -0.21% | +0.55% |
| Hari pertama Stage 4 terkonfirmasi | BTC tidak tren naik | bukan meme | TP −5% / SL +5% (tutup semua) | 1138 | 55.3% | +0.05% | 1.02 | +0.55% (486, menang 60.3%) | -0.32% (652, menang 51.5%) | +0.00% | +0.43% |
| Hari pertama Stage 4 terkonfirmasi | BTC tidak tren naik | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 1138 | 31.6% | -0.72% | 0.9 | -0.55% (486, menang 30.0%) | -0.85% (652, menang 32.8%) | +0.10% | +0.44% |
| Hari pertama Stage 4 terkonfirmasi | semua kondisi | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 1556 | 71.9% | -0.34% | 0.9 | +0.87% (539, menang 79.2%) | -0.99% (1017, menang 67.9%) | -0.84% | +0.13% |
| Hari pertama Stage 4 terkonfirmasi | semua kondisi | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 1556 | 64.1% | -0.22% | 0.93 | +0.64% (539, menang 70.9%) | -0.68% (1017, menang 60.5%) | -0.65% | +0.22% |
| Hari pertama Stage 4 terkonfirmasi | semua kondisi | bukan meme | TP −5% / SL +5% (tutup semua) | 1556 | 50.8% | -0.40% | 0.85 | +0.42% (539, menang 59.0%) | -0.84% (1017, menang 46.4%) | -0.50% | -0.02% |
| Hari pertama Stage 4 terkonfirmasi | semua kondisi | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 1556 | 29.6% | -1.03% | 0.85 | -0.39% (539, menang 30.1%) | -1.37% (1017, menang 29.4%) | -0.79% | +0.09% |
| Hari pertama Stage 4 terkonfirmasi | BTC tren turun | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 872 | 70.6% | -0.46% | 0.87 | +0.60% (372, menang 76.9%) | -1.24% (500, menang 66.0%) | -0.48% | +0.01% |
| Hari pertama Stage 4 terkonfirmasi | BTC tren turun | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 872 | 63.3% | -0.23% | 0.93 | +0.51% (372, menang 68.8%) | -0.78% (500, menang 59.2%) | -0.21% | +0.20% |
| Hari pertama Stage 4 terkonfirmasi | BTC tren turun | termasuk meme | TP −5% / SL +5% (tutup semua) | 872 | 53.2% | -0.15% | 0.94 | +0.17% (372, menang 56.5%) | -0.38% (500, menang 50.8%) | +0.02% | +0.23% |
| Hari pertama Stage 4 terkonfirmasi | BTC tren turun | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 872 | 29.7% | -1.97% | 0.73 | -2.78% (372, menang 24.7%) | -1.36% (500, menang 33.4%) | -0.22% | -0.86% |
| Hari pertama Stage 4 terkonfirmasi | BTC tidak tren naik | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 1195 | 73.6% | -0.02% | 0.99 | +1.00% (499, menang 80.0%) | -0.75% (696, menang 69.0%) | -0.51% | +0.45% |
| Hari pertama Stage 4 terkonfirmasi | BTC tidak tren naik | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 1195 | 66.7% | +0.16% | 1.06 | +0.82% (499, menang 72.1%) | -0.32% (696, menang 62.8%) | -0.18% | +0.60% |
| Hari pertama Stage 4 terkonfirmasi | BTC tidak tren naik | termasuk meme | TP −5% / SL +5% (tutup semua) | 1195 | 55.2% | +0.05% | 1.02 | +0.53% (499, menang 60.1%) | -0.30% (696, menang 51.7%) | -0.03% | +0.43% |
| Hari pertama Stage 4 terkonfirmasi | BTC tidak tren naik | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 1195 | 32.5% | -0.60% | 0.91 | -0.36% (499, menang 30.9%) | -0.77% (696, menang 33.6%) | +0.09% | +0.57% |
| Hari pertama Stage 4 terkonfirmasi | semua kondisi | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 1634 | 71.9% | -0.31% | 0.91 | +0.90% (553, menang 79.4%) | -0.92% (1081, menang 68.1%) | -0.83% | +0.17% |
| Hari pertama Stage 4 terkonfirmasi | semua kondisi | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 1634 | 64.3% | -0.16% | 0.95 | +0.68% (553, menang 71.1%) | -0.59% (1081, menang 60.9%) | -0.61% | +0.28% |
| Hari pertama Stage 4 terkonfirmasi | semua kondisi | termasuk meme | TP −5% / SL +5% (tutup semua) | 1634 | 50.8% | -0.40% | 0.85 | +0.41% (553, menang 59.0%) | -0.82% (1081, menang 46.6%) | -0.51% | -0.02% |
| Hari pertama Stage 4 terkonfirmasi | semua kondisi | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 1634 | 30.4% | -0.90% | 0.87 | -0.23% (553, menang 30.7%) | -1.24% (1081, menang 30.2%) | -0.78% | +0.24% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tren turun | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 31 | 74.2% | +0.06% | 1.02 | +1.32% (16, menang 81.2%) | -1.30% (15, menang 66.7%) | -2.31% | +0.71% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tren turun | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 31 | 61.3% | -0.74% | 0.78 | -0.40% (16, menang 62.5%) | -1.10% (15, menang 60.0%) | -2.87% | -0.20% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tren turun | bukan meme | TP −5% / SL +5% (tutup semua) | 31 | 48.4% | -0.66% | 0.77 | -1.15% (16, menang 43.8%) | -0.14% (15, menang 53.3%) | -1.94% | -0.26% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tren turun | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 31 | 32.3% | -3.64% | 0.46 | -5.15% (16, menang 18.8%) | -2.03% (15, menang 46.7%) | -3.46% | -2.40% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tidak tren naik | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 59 | 72.9% | -0.80% | 0.75 | +1.35% (17, menang 82.4%) | -1.68% (42, menang 69.0%) | -1.65% | -0.19% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tidak tren naik | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 59 | 54.2% | -1.97% | 0.5 | -0.27% (17, menang 64.7%) | -2.65% (42, menang 50.0%) | -2.49% | -1.45% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tidak tren naik | bukan meme | TP −5% / SL +5% (tutup semua) | 59 | 35.6% | -1.93% | 0.45 | -0.82% (17, menang 47.1%) | -2.39% (42, menang 31.0%) | -1.96% | -1.54% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tidak tren naik | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 59 | 28.8% | -3.14% | 0.57 | -4.06% (17, menang 23.5%) | -2.77% (42, menang 31.0%) | -2.04% | -1.91% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | semua kondisi | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 69 | 75.4% | +0.01% | 1.0 | +1.35% (17, menang 82.4%) | -0.44% (52, menang 73.1%) | -2.19% | +0.63% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | semua kondisi | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 69 | 59.4% | -0.93% | 0.73 | -0.27% (17, menang 64.7%) | -1.15% (52, menang 57.7%) | -2.62% | -0.39% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | semua kondisi | bukan meme | TP −5% / SL +5% (tutup semua) | 69 | 42.0% | -1.29% | 0.6 | -0.82% (17, menang 47.1%) | -1.45% (52, menang 40.4%) | -2.15% | -0.90% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | semua kondisi | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 69 | 29.0% | -2.24% | 0.68 | -4.06% (17, menang 23.5%) | -1.64% (52, menang 30.8%) | -4.85% | -1.01% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tren turun | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 32 | 75.0% | +0.12% | 1.04 | +1.32% (16, menang 81.2%) | -1.09% (16, menang 68.8%) | -2.22% | +0.76% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tren turun | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 32 | 62.5% | -0.65% | 0.8 | -0.40% (16, menang 62.5%) | -0.91% (16, menang 62.5%) | -2.73% | -0.12% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tren turun | termasuk meme | TP −5% / SL +5% (tutup semua) | 32 | 50.0% | -0.50% | 0.82 | -1.15% (16, menang 43.8%) | +0.15% (16, menang 56.2%) | -1.72% | -0.10% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tren turun | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 32 | 31.2% | -3.92% | 0.43 | -5.15% (16, menang 18.8%) | -2.70% (16, menang 43.8%) | -3.66% | -2.70% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tidak tren naik | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 61 | 72.1% | -0.95% | 0.71 | +1.35% (17, menang 82.4%) | -1.84% (44, menang 68.2%) | -1.64% | -0.34% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tidak tren naik | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 61 | 54.1% | -2.01% | 0.49 | -0.27% (17, menang 64.7%) | -2.68% (44, menang 50.0%) | -2.47% | -1.50% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tidak tren naik | termasuk meme | TP −5% / SL +5% (tutup semua) | 61 | 36.1% | -1.89% | 0.46 | -0.82% (17, menang 47.1%) | -2.30% (44, menang 31.8%) | -1.83% | -1.49% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | BTC tidak tren naik | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 61 | 27.9% | -3.45% | 0.54 | -4.06% (17, menang 23.5%) | -3.21% (44, menang 29.5%) | -2.17% | -2.25% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | semua kondisi | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 71 | 74.6% | -0.14% | 0.95 | +1.35% (17, menang 82.4%) | -0.61% (54, menang 72.2%) | -2.33% | +0.48% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | semua kondisi | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 71 | 59.2% | -0.99% | 0.72 | -0.27% (17, menang 64.7%) | -1.22% (54, menang 57.4%) | -2.71% | -0.46% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | semua kondisi | termasuk meme | TP −5% / SL +5% (tutup semua) | 71 | 42.3% | -1.27% | 0.6 | -0.82% (17, menang 47.1%) | -1.41% (54, menang 40.7%) | -2.09% | -0.88% |
| Jebol lantai puncak (Stage 3→4) + volume ≥1,5× | semua kondisi | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 71 | 28.2% | -2.53% | 0.65 | -4.06% (17, menang 23.5%) | -2.05% (54, menang 29.6%) | -5.20% | -1.32% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tren turun | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 162 | 85.8% | +2.01% | 2.27 | +2.23% (22, menang 90.9%) | +1.97% (140, menang 85.0%) | +1.62% | +2.68% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tren turun | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 162 | 74.7% | +1.20% | 1.56 | +1.54% (22, menang 81.8%) | +1.15% (140, menang 73.6%) | +1.71% | +1.83% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tren turun | bukan meme | TP −5% / SL +5% (tutup semua) | 162 | 61.7% | +0.69% | 1.33 | +0.86% (22, menang 63.6%) | +0.67% (140, menang 61.4%) | +1.65% | +1.06% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tren turun | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 162 | 54.9% | +7.98% | 2.98 | +1.78% (22, menang 63.6%) | +8.95% (140, menang 53.6%) | +5.33% | +9.36% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tidak tren naik | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 225 | 86.7% | +2.65% | 2.77 | +3.20% (27, menang 92.6%) | +2.58% (198, menang 85.9%) | +1.65% | +3.34% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tidak tren naik | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 225 | 78.2% | +2.11% | 2.15 | +2.64% (27, menang 85.2%) | +2.04% (198, menang 77.3%) | +1.73% | +2.76% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tidak tren naik | bukan meme | TP −5% / SL +5% (tutup semua) | 225 | 65.8% | +1.10% | 1.59 | +1.17% (27, menang 66.7%) | +1.09% (198, menang 65.7%) | +1.17% | +1.47% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tidak tren naik | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 225 | 56.4% | +8.21% | 3.16 | +4.53% (27, menang 66.7%) | +8.71% (198, menang 55.1%) | +5.44% | +9.53% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | semua kondisi | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 397 | 70.8% | -0.50% | 0.85 | -0.70% (71, menang 73.2%) | -0.45% (326, menang 70.2%) | +0.54% | +0.12% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | semua kondisi | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 397 | 62.2% | -0.54% | 0.83 | -1.47% (71, menang 59.2%) | -0.34% (326, menang 62.9%) | +0.47% | +0.03% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | semua kondisi | bukan meme | TP −5% / SL +5% (tutup semua) | 397 | 52.6% | -0.21% | 0.92 | -0.83% (71, menang 46.5%) | -0.08% (326, menang 54.0%) | +0.76% | +0.16% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | semua kondisi | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 397 | 43.1% | +3.00% | 1.66 | -0.94% (71, menang 43.7%) | +3.85% (326, menang 42.9%) | +3.10% | +3.95% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tren turun | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 173 | 85.5% | +2.00% | 2.23 | +2.23% (22, menang 90.9%) | +1.97% (151, menang 84.8%) | +1.63% | +2.67% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tren turun | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 173 | 75.1% | +1.29% | 1.62 | +1.54% (22, menang 81.8%) | +1.26% (151, menang 74.2%) | +1.80% | +1.92% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tren turun | termasuk meme | TP −5% / SL +5% (tutup semua) | 173 | 63.0% | +0.82% | 1.41 | +0.86% (22, menang 63.6%) | +0.81% (151, menang 62.9%) | +1.77% | +1.19% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tren turun | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 173 | 55.5% | +7.92% | 2.95 | +1.78% (22, menang 63.6%) | +8.81% (151, menang 54.3%) | +4.77% | +9.30% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tidak tren naik | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 244 | 86.1% | +2.60% | 2.64 | +3.20% (27, menang 92.6%) | +2.52% (217, menang 85.3%) | +1.58% | +3.29% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tidak tren naik | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 244 | 78.3% | +2.17% | 2.18 | +2.64% (27, menang 85.2%) | +2.11% (217, menang 77.4%) | +1.74% | +2.82% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tidak tren naik | termasuk meme | TP −5% / SL +5% (tutup semua) | 244 | 66.8% | +1.20% | 1.66 | +1.17% (27, menang 66.7%) | +1.20% (217, menang 66.8%) | +1.21% | +1.58% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | BTC tidak tren naik | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 244 | 57.0% | +8.21% | 3.12 | +4.53% (27, menang 66.7%) | +8.67% (217, menang 55.8%) | +5.02% | +9.53% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | semua kondisi | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 420 | 70.7% | -0.47% | 0.86 | -0.70% (71, menang 73.2%) | -0.42% (349, menang 70.2%) | +0.50% | +0.16% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | semua kondisi | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 420 | 62.6% | -0.44% | 0.86 | -1.47% (71, menang 59.2%) | -0.23% (349, menang 63.3%) | +0.50% | +0.13% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | semua kondisi | termasuk meme | TP −5% / SL +5% (tutup semua) | 420 | 53.6% | -0.12% | 0.95 | -0.83% (71, menang 46.5%) | +0.03% (349, menang 55.0%) | +0.79% | +0.25% |
| Pantulan Stage 4 ke Fibonacci 0,382–0,618 + candle merah | semua kondisi | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 420 | 43.6% | +3.17% | 1.7 | -0.94% (71, menang 43.7%) | +4.01% (349, menang 43.6%) | +2.90% | +4.14% |
| Short hari acak (pembanding) | BTC tren turun | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 12187 | 70.9% | -0.34% | 0.91 | -0.02% (5731, menang 72.3%) | -0.62% (6456, menang 69.7%) | +0.00% | +0.15% |
| Short hari acak (pembanding) | BTC tren turun | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 12187 | 61.6% | -0.43% | 0.87 | -0.11% (5731, menang 63.3%) | -0.70% (6456, menang 60.1%) | +0.00% | +0.02% |
| Short hari acak (pembanding) | BTC tren turun | bukan meme | TP −5% / SL +5% (tutup semua) | 12187 | 49.4% | -0.55% | 0.8 | -0.46% (5731, menang 50.2%) | -0.62% (6456, menang 48.6%) | +0.00% | -0.16% |
| Short hari acak (pembanding) | BTC tren turun | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 12187 | 30.3% | -2.53% | 0.63 | -2.01% (5731, menang 31.9%) | -2.98% (6456, menang 29.0%) | +0.00% | -1.57% |
| Short hari acak (pembanding) | BTC tidak tren naik | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 17796 | 72.6% | -0.02% | 0.99 | +0.20% (7456, menang 73.3%) | -0.18% (10340, menang 72.0%) | +0.00% | +0.46% |
| Short hari acak (pembanding) | BTC tidak tren naik | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 17796 | 63.5% | -0.13% | 0.96 | +0.04% (7456, menang 64.0%) | -0.25% (10340, menang 63.2%) | +0.00% | +0.32% |
| Short hari acak (pembanding) | BTC tidak tren naik | bukan meme | TP −5% / SL +5% (tutup semua) | 17796 | 51.2% | -0.36% | 0.86 | -0.35% (7456, menang 51.3%) | -0.37% (10340, menang 51.2%) | +0.00% | +0.03% |
| Short hari acak (pembanding) | BTC tidak tren naik | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 17796 | 32.2% | -1.76% | 0.72 | -1.23% (7456, menang 34.2%) | -2.13% (10340, menang 30.8%) | +0.00% | -0.82% |
| Short hari acak (pembanding) | semua kondisi | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 32975 | 69.8% | -0.55% | 0.85 | -0.38% (12320, menang 70.4%) | -0.65% (20655, menang 69.5%) | +0.00% | -0.07% |
| Short hari acak (pembanding) | semua kondisi | bukan meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 32975 | 60.9% | -0.52% | 0.84 | -0.38% (12320, menang 61.4%) | -0.60% (20655, menang 60.6%) | +0.00% | -0.07% |
| Short hari acak (pembanding) | semua kondisi | bukan meme | TP −5% / SL +5% (tutup semua) | 32975 | 48.8% | -0.60% | 0.79 | -0.58% (12320, menang 49.0%) | -0.61% (20655, menang 48.7%) | +0.00% | -0.21% |
| Short hari acak (pembanding) | semua kondisi | bukan meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 32975 | 33.7% | -1.54% | 0.73 | -1.58% (12320, menang 34.1%) | -1.52% (20655, menang 33.4%) | +0.00% | -0.75% |
| Short hari acak (pembanding) | BTC tren turun | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 12892 | 70.8% | -0.35% | 0.9 | -0.02% (5915, menang 72.3%) | -0.64% (6977, menang 69.6%) | +0.00% | +0.13% |
| Short hari acak (pembanding) | BTC tren turun | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 12892 | 61.6% | -0.42% | 0.87 | -0.10% (5915, menang 63.3%) | -0.70% (6977, menang 60.1%) | +0.00% | +0.03% |
| Short hari acak (pembanding) | BTC tren turun | termasuk meme | TP −5% / SL +5% (tutup semua) | 12892 | 49.5% | -0.53% | 0.81 | -0.46% (5915, menang 50.3%) | -0.60% (6977, menang 48.8%) | +0.00% | -0.15% |
| Short hari acak (pembanding) | BTC tren turun | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 12892 | 30.3% | -2.54% | 0.63 | -1.98% (5915, menang 32.0%) | -3.02% (6977, menang 28.9%) | +0.00% | -1.59% |
| Short hari acak (pembanding) | BTC tidak tren naik | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 18830 | 72.5% | -0.04% | 0.99 | +0.20% (7692, menang 73.3%) | -0.21% (11138, menang 71.9%) | +0.00% | +0.44% |
| Short hari acak (pembanding) | BTC tidak tren naik | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 18830 | 63.5% | -0.14% | 0.96 | +0.04% (7692, menang 64.0%) | -0.26% (11138, menang 63.1%) | +0.00% | +0.31% |
| Short hari acak (pembanding) | BTC tidak tren naik | termasuk meme | TP −5% / SL +5% (tutup semua) | 18830 | 51.2% | -0.36% | 0.87 | -0.35% (7692, menang 51.3%) | -0.37% (11138, menang 51.2%) | +0.00% | +0.03% |
| Short hari acak (pembanding) | BTC tidak tren naik | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 18830 | 32.2% | -1.78% | 0.72 | -1.21% (7692, menang 34.4%) | -2.18% (11138, menang 30.7%) | +0.00% | -0.84% |
| Short hari acak (pembanding) | semua kondisi | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +12% | 34930 | 69.8% | -0.56% | 0.85 | -0.39% (12726, menang 70.4%) | -0.66% (22204, menang 69.4%) | +0.00% | -0.08% |
| Short hari acak (pembanding) | semua kondisi | termasuk meme | TP1 −5% (tutup 50%), TP2 target/−10%, SL +8% | 34930 | 60.9% | -0.52% | 0.84 | -0.38% (12726, menang 61.4%) | -0.60% (22204, menang 60.6%) | +0.00% | -0.07% |
| Short hari acak (pembanding) | semua kondisi | termasuk meme | TP −5% / SL +5% (tutup semua) | 34930 | 48.9% | -0.59% | 0.79 | -0.57% (12726, menang 49.1%) | -0.61% (22204, menang 48.7%) | +0.00% | -0.21% |
| Short hari acak (pembanding) | semua kondisi | termasuk meme | Ikuti siklus: tutup saat di atas MA50 atau SL +12% (maks 180 hari) | 34930 | 33.8% | -1.50% | 0.74 | -1.56% (12726, menang 34.2%) | -1.47% (22204, menang 33.6%) | +0.00% | -0.71% |

## Sinyal 🔴 radar sebagai short (Okt 2024–Okt 2026, biaya konservatif)

| Aturan | Pasar | Meme | Sinyal | Menang | Rata-rata | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| pola_tp5_sl12 | BTC tren turun | bukan meme | 10 | 60.0% | -3.75% | +2.03% (1, menang 100.0%) | -4.39% (9, menang 55.6%) |
| pola_tp5_sl12 | BTC tidak tren naik | bukan meme | 25 | 64.0% | -2.64% | -0.74% (9, menang 77.8%) | -3.71% (16, menang 56.2%) |
| pola_tp5_sl12 | semua kondisi | bukan meme | 52 | 50.0% | -3.12% | +2.68% (15, menang 80.0%) | -5.47% (37, menang 37.8%) |
| pola_tp5_sl12 | BTC tren turun | termasuk meme | 11 | 54.5% | -4.54% | +2.03% (1, menang 100.0%) | -5.20% (10, menang 50.0%) |
| pola_tp5_sl12 | BTC tidak tren naik | termasuk meme | 26 | 61.5% | -3.02% | -0.74% (9, menang 77.8%) | -4.23% (17, menang 52.9%) |
| pola_tp5_sl12 | semua kondisi | termasuk meme | 54 | 50.0% | -3.20% | +2.64% (16, menang 81.2%) | -5.65% (38, menang 36.8%) |
| pola_sl12 | BTC tren turun | bukan meme | 10 | 20.0% | -8.87% | -10.61% (1, menang 0.0%) | -8.67% (9, menang 22.2%) |
| pola_sl12 | BTC tidak tren naik | bukan meme | 25 | 20.0% | -8.38% | -8.06% (9, menang 22.2%) | -8.55% (16, menang 18.8%) |
| pola_sl12 | semua kondisi | bukan meme | 52 | 21.2% | -5.38% | -1.49% (15, menang 26.7%) | -6.96% (37, menang 18.9%) |
| pola_sl12 | BTC tren turun | termasuk meme | 11 | 18.2% | -9.20% | -10.61% (1, menang 0.0%) | -9.06% (10, menang 20.0%) |
| pola_sl12 | BTC tidak tren naik | termasuk meme | 26 | 19.2% | -8.54% | -8.06% (9, menang 22.2%) | -8.79% (17, menang 17.6%) |
| pola_sl12 | semua kondisi | termasuk meme | 54 | 22.2% | -4.92% | +0.28% (16, menang 31.2%) | -7.11% (38, menang 18.4%) |
| tetap_5_5 | BTC tren turun | bukan meme | 10 | 50.0% | -0.46% | +4.57% (1, menang 100.0%) | -1.02% (9, menang 44.4%) |
| tetap_5_5 | BTC tidak tren naik | bukan meme | 25 | 40.0% | -1.51% | -1.06% (9, menang 44.4%) | -1.76% (16, menang 37.5%) |
| tetap_5_5 | semua kondisi | bukan meme | 52 | 36.5% | -1.85% | -0.15% (15, menang 53.3%) | -2.53% (37, menang 29.7%) |
| tetap_5_5 | BTC tren turun | termasuk meme | 11 | 45.5% | -0.91% | +4.57% (1, menang 100.0%) | -1.46% (10, menang 40.0%) |
| tetap_5_5 | BTC tidak tren naik | termasuk meme | 26 | 38.5% | -1.66% | -1.06% (9, menang 44.4%) | -1.98% (17, menang 35.3%) |
| tetap_5_5 | semua kondisi | termasuk meme | 54 | 37.0% | -1.79% | +0.14% (16, menang 56.2%) | -2.61% (38, menang 28.9%) |
| pola_tp5 | BTC tren turun | bukan meme | 10 | 70.0% | -5.63% | +2.03% (1, menang 100.0%) | -6.48% (9, menang 66.7%) |
| pola_tp5 | BTC tidak tren naik | bukan meme | 25 | 72.0% | -2.92% | +0.85% (9, menang 88.9%) | -5.04% (16, menang 62.5%) |
| pola_tp5 | semua kondisi | bukan meme | 52 | 55.8% | -3.93% | +3.60% (15, menang 86.7%) | -6.99% (37, menang 43.2%) |
| pola_tp5 | BTC tren turun | termasuk meme | 11 | 72.7% | -4.95% | +2.03% (1, menang 100.0%) | -5.64% (10, menang 70.0%) |
| pola_tp5 | BTC tidak tren naik | termasuk meme | 26 | 73.1% | -2.73% | +0.85% (9, menang 88.9%) | -4.63% (17, menang 64.7%) |
| pola_tp5 | semua kondisi | termasuk meme | 54 | 57.4% | -3.72% | +3.50% (16, menang 87.5%) | -6.76% (38, menang 44.7%) |

## Catatan

- Koin = top CMC saat ini. Koin yang sudah mati tidak ikut, padahal itu short terbaik → hasil short cenderung terlalu jelek, bukan terlalu bagus.
- Funding futures bisa menguntungkan short (saat pasar optimis) atau membebani (saat pasar takut). Di sini dianggap selalu biaya.
- Short memakai leverage berisiko likuidasi. Hasil di atas tanpa leverage (1×).
