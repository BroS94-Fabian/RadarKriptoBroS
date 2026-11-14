# 🌡️ Model Kondisi Pasar

Dibuat 14 Nov 2026 16:43 WIB · 133 koin · sinyal 2020-09-17 s/d 2026-10-14 · meme coin tidak ikut

## Putusan

**❌ Model BARU tidak dipakai (radar tetap memakai aturan lama)** — di luar sampel 2023-01-01–2026-10-14: BARU -29.9% (maks turun -30.6%, Sharpe -0.78) vs LAMA +134.8% (maks turun -24.9%, Sharpe 0.83).

## Uji portofolio di luar sampel (2023-01-01 s/d 2026-10-14)

Maks 5 posisi sekaligus, tiap posisi = modal ÷ 5, tanpa leverage. Aturan model baru untuk tiap tahun dipilih hanya dari data tahun-tahun sebelumnya. Saat slot penuh, sinyal dipilih acak (median dari 20 urutan).

| Susunan | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi | Hari ada posisi |
|---|---|---|---|---|---|---|---|---|
| Model LAMA (aturan tetap BTC MA50) | **+134.8%** (+94…+187) | 2023: +31% · 2024: +20% · 2025: +12% · 2026: +36% | -24.9% | 0.83 | 519 dari 998 | 74.5% | +0.97% | 82% |
| Model BARU (mengikuti skor pasar) | **-29.9%** (-35…-24) | 2023: +0% · 2024: -30% · 2025: +0% · 2026: -1% | -30.6% | -0.78 | 61 dari 105 | 55.7% | -2.71% | 10% |
| LAMA — hanya beli | **+76.2%** (+40…+126) | 2023: +28% · 2024: +22% · 2025: -3% · 2026: +21% | -24.0% | 0.56 | 428 dari 790 | 72.7% | +0.83% | 54% |
| BARU — hanya beli | **-29.4%** (-35…-23) | 2023: +0% · 2024: -30% · 2025: +0% · 2026: +0% | -30.6% | -0.76 | 60 dari 104 | 56.7% | -2.69% | 8% |
| LAMA — hanya jual dulu (short) | **+27.8%** (+14…+36) | 2023: +4% · 2024: +1% · 2025: +11% · 2026: +10% | -7.4% | 0.94 | 100 dari 208 | 81.0% | +1.29% | 35% |
| BARU — hanya jual dulu (short) | **-0.7%** (-1…-1) | 2023: +0% · 2024: +0% · 2025: +0% · 2026: -1% | -0.7% | -0.51 | 1 dari 1 | 0.0% | -3.47% | 2% |
| Tanpa filter pasar (3 strategi live, semua kondisi) | **+9.4%** (-10…+48) | 2023: -12% · 2024: +17% · 2025: -16% · 2026: +25% | -40.8% | 0.13 | 714 dari 1514 | 70.6% | +0.19% | 95% |
| Pembanding: beli & tahan BTC | +311.1% | 2023: +154% · 2024: +112% · 2025: -7% · 2026: -23% | -53.0% | 0.81 | - | - | - | 100% |

Dengan maks 10 posisi: Model LAMA +98.0% (maks turun -21.6%) · Model BARU -30.6% (maks turun -30.6%)

### Per sinyal di luar sampel (tanpa batas slot)

| Strategi | Model baru | Model lama | Semua sinyal (tanpa filter) |
|---|---|---|---|
| 🟢 Sinyal radar (skor ≥55) (beli) | - | +1.70% (238, menang 70.6%) | +0.37% (452, menang 66.2%) |
| 🟩 Awal Stage 2 (beli) | - | +0.80% (552, menang 75.5%) | +0.56% (686, menang 74.5%) |
| Tembus atap dasar + volume (beli) | -0.08% (23, menang 73.9%) | - | +0.85% (298, menang 75.5%) |
| Pullback Stage 2 ke Fibonacci (beli) | -6.39% (81, menang 34.6%) | - | -0.78% (626, menang 68.2%) |
| 🔻 Pantulan Stage 4 ke Fibonacci (jual dulu) | -3.47% (1, menang 0.0%) | +2.53% (208, menang 86.1%) | -0.75% (376, menang 69.4%) |
| Awal Stage 4 (jual dulu) | - | - | -0.62% (1200, menang 70.2%) |
| Jebol lantai puncak + volume (jual dulu) | - | - | -0.38% (64, menang 71.9%) |
| 🔴 Sinyal radar turun (jual dulu) | - | - | -1.31% (87, menang 58.6%) |

## Aturan yang terpilih tiap tahun uji (walk-forward)

| Tahun uji | Strategi | Aturan dari data sebelumnya | Hasil latih | Hasil di tahun uji |
|---|---|---|---|---|
| 2023 | 🟢 Sinyal radar (skor ≥55) | ✖ tidak aktif (t 1.55 < 2.0) | +2.24% (79, menang 79.7%) | - |
| 2023 | 🟩 Awal Stage 2 | ✖ tidak aktif (t 1.44 < 2.0) | +1.15% (156, menang 75.6%) | - |
| 2023 | Tembus atap dasar + volume | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2023 | Pullback Stage 2 ke Fibonacci | ✖ tidak aktif (t 1.43 < 2.0) | +2.19% (189, menang 77.2%) | - |
| 2023 | 🔻 Pantulan Stage 4 ke Fibonacci | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2023 | Awal Stage 4 | ✖ tidak aktif (t 1.4 < 2.0) | +1.01% (287, menang 79.1%) | - |
| 2023 | Jebol lantai puncak + volume | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2023 | 🔴 Sinyal radar turun | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2024 | 🟢 Sinyal radar (skor ≥55) | ✖ tidak aktif (t 1.24 < 2.0) | +1.28% (153, menang 71.9%) | - |
| 2024 | 🟩 Awal Stage 2 | ✖ tidak aktif (t 0.07 < 2.0) | +0.04% (362, menang 71.3%) | - |
| 2024 | Tembus atap dasar + volume | skor pasar ≥ -4 + koin lebih kuat dari BTC | +2.00% (62, menang 82.3%) · t 2.34 | -0.08% (23, menang 73.9%) |
| 2024 | Pullback Stage 2 ke Fibonacci | skor pasar ≥ +4 | +2.54% (124, menang 83.1%) · t 3.12 | -6.39% (81, menang 34.6%) |
| 2024 | 🔻 Pantulan Stage 4 ke Fibonacci | ✖ tidak aktif (t 0.07 < 2.0) | +0.12% (55, menang 74.5%) | - |
| 2024 | Awal Stage 4 | ✖ tidak aktif (t 0.94 < 2.0) | +0.53% (566, menang 77.2%) | - |
| 2024 | Jebol lantai puncak + volume | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2024 | 🔴 Sinyal radar turun | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2025 | 🟢 Sinyal radar (skor ≥55) | ✖ tidak aktif (t 1.56 < 2.0) | +1.97% (294, menang 73.8%) | - |
| 2025 | 🟩 Awal Stage 2 | ✖ tidak aktif (t 0.62 < 2.0) | +0.41% (605, menang 73.2%) | - |
| 2025 | Tembus atap dasar + volume | ✖ tidak aktif (t 1.86 < 2.0) | +1.29% (183, menang 77.6%) | - |
| 2025 | Pullback Stage 2 ke Fibonacci | ✖ tidak aktif (t 0.04 < 2.0) | +0.05% (463, menang 70.2%) | - |
| 2025 | 🔻 Pantulan Stage 4 ke Fibonacci | ✖ tidak aktif (t 1.71 < 2.0) | +1.86% (45, menang 84.4%) | - |
| 2025 | Awal Stage 4 | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2025 | Jebol lantai puncak + volume | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2025 | 🔴 Sinyal radar turun | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2026 | 🟢 Sinyal radar (skor ≥55) | ✖ tidak aktif (t 0.8 < 2.0) | +0.88% (394, menang 70.1%) | - |
| 2026 | 🟩 Awal Stage 2 | ✖ tidak aktif (t 0.5 < 2.0) | +0.29% (714, menang 72.8%) | - |
| 2026 | Tembus atap dasar + volume | ✖ tidak aktif (t 1.87 < 2.0) | +1.16% (214, menang 77.1%) | - |
| 2026 | Pullback Stage 2 ke Fibonacci | ✖ tidak aktif (t 0.09 < 2.0) | +0.09% (470, menang 71.1%) | - |
| 2026 | 🔻 Pantulan Stage 4 ke Fibonacci | skor pasar ≤ -2 + koin lebih lemah dari BTC | +3.89% (132, menang 91.7%) · t 13.34 | -3.47% (1, menang 0.0%) |
| 2026 | Awal Stage 4 | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2026 | Jebol lantai puncak + volume | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - |
| 2026 | 🔴 Sinyal radar turun | ✖ tidak aktif (t 0.1 < 2.0) | +0.10% (95, menang 68.4%) | - |

## Model akhir (dilatih dari semua data, dipakai radar bila putusan ✅)

| Strategi | Sisi | Aturan | Sinyal | Menang | Rata-rata | t (kluster bulan) |
|---|---|---|---|---|---|---|
| 🟢 Sinyal radar (skor ≥55) | beli | ✖ tidak aktif (t 0.95 < 2.0) | 440 | - | - | 0.95 |
| 🟩 Awal Stage 2 | beli | ✖ tidak aktif (t 1.05 < 2.0) | 862 | - | - | 1.05 |
| Tembus atap dasar + volume | beli | ✖ tidak aktif (t 1.65 < 2.0) | 315 | - | - | 1.65 |
| Pullback Stage 2 ke Fibonacci | beli | ✖ tidak aktif (t 0.24 < 2.0) | 602 | - | - | 0.24 |
| 🔻 Pantulan Stage 4 ke Fibonacci | jual dulu | skor pasar ≤ -2 + koin lebih lemah dari BTC | 133 | 91.0% | +3.84% | 12.19 |
| Awal Stage 4 | jual dulu | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - | - | - |
| Jebol lantai puncak + volume | jual dulu | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - | - | - |
| 🔴 Sinyal radar turun | jual dulu | ✖ tidak aktif (sinyal latih kurang / rata-rata tidak positif) | - | - | - | - |

## Hasil tiap strategi menurut kondisi pasar (seluruh data, deskriptif)

Jumlah hari per kondisi: bear (≤−4) 641 · turun (−3…−2) 452 · netral (−1…+1) 560 · naik (+2…+3) 395 · bull (≥+4) 461

| Strategi | bear (≤−4) | turun (−3…−2) | netral (−1…+1) | naik (+2…+3) | bull (≥+4) | Semua |
|---|---|---|---|---|---|---|
| 🟢 Sinyal radar (skor ≥55) | -1.55% (139, menang 59.7%) | +1.20% (121, menang 72.7%) | +0.89% (136, menang 69.1%) | +1.35% (113, menang 72.6%) | +0.08% (70, menang 61.4%) | +0.36% (579, menang 67.4%) |
| 🟩 Awal Stage 2 | -0.01% (53, menang 71.7%) | -1.27% (44, menang 65.9%) | +1.01% (118, menang 76.3%) | +1.61% (201, menang 79.1%) | +0.14% (446, menang 72.0%) | +0.52% (862, menang 73.9%) |
| Tembus atap dasar + volume | -5.35% (11, menang 45.5%) | +5.74% (11, menang 90.9%) | +2.96% (39, menang 84.6%) | +1.62% (98, menang 79.6%) | -0.07% (156, menang 71.8%) | +0.85% (315, menang 75.6%) |
| Pullback Stage 2 ke Fibonacci | -1.26% (57, menang 68.4%) | +0.15% (92, menang 73.9%) | -0.65% (223, menang 66.8%) | +1.75% (188, menang 79.8%) | -0.84% (264, menang 65.2%) | -0.11% (824, menang 70.1%) |
| 🔻 Pantulan Stage 4 ke Fibonacci | +1.54% (131, menang 81.7%) | +4.21% (83, menang 94.0%) | -2.64% (59, menang 57.6%) | -5.43% (104, menang 44.2%) | -0.89% (24, menang 75.0%) | -0.48% (401, menang 70.6%) |
| Awal Stage 4 | -0.83% (748, menang 68.4%) | +0.58% (521, menang 78.5%) | -1.08% (250, menang 66.8%) | -0.14% (34, menang 70.6%) | +1.65% (26, menang 84.6%) | -0.35% (1579, menang 71.8%) |
| Jebol lantai puncak + volume | +0.07% (27, menang 74.1%) | -0.83% (10, menang 70.0%) | -0.24% (32, menang 75.0%) | +2.03% (1, menang 100.0%) | - | -0.17% (70, menang 74.3%) |
| 🔴 Sinyal radar turun | -2.71% (44, menang 59.1%) | -2.15% (27, menang 51.9%) | -0.40% (34, menang 64.7%) | -0.98% (14, menang 57.1%) | +1.87% (16, menang 75.0%) | -1.29% (135, menang 60.7%) |
| Pembanding: beli acak | -0.51% (9932, menang 68.9%) | -0.86% (6409, menang 66.7%) | -0.23% (6757, menang 70.1%) | -0.20% (4902, menang 70.8%) | -0.78% (5435, menang 67.7%) | -0.52% (33435, menang 68.8%) |
| Pembanding: short acak | -0.50% (9932, menang 70.4%) | -0.21% (6409, menang 71.3%) | -0.83% (6757, menang 68.2%) | -1.24% (4902, menang 65.6%) | -0.10% (5435, menang 73.0%) | -0.55% (33435, menang 69.9%) |

## Kondisi pasar pada akhir data

2026-11-13: skor **-5** (🔴🔴 BEAR KUAT) · koin di atas MA50 3% · Stage 2 3% · Stage 4 23%

## Catatan

- Skor pasar memakai ambang bulat yang ditetapkan di muka; yang dipilih dari data hanya batas skor tiap strategi.
- Model lama disetel memakai data 2024–2026 (beli) dan 2020–2026 (short), jadi di uji ini model lama diuntungkan.
- Daftar koin = top CMC saat ini (koin yang sudah mati tidak ikut): hasil beli cenderung terlalu bagus, hasil short terlalu jelek.
- Untung-rugi dicatat saat posisi ditutup; penurunan sementara di tengah posisi tidak terlihat di 'maks turun'.
- Biaya: beli/jual 0,1% + pajak jual 0,21%; short 0,1% + 0,1% + pajak 0,21% + funding 0,03%/hari.
- Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual.
