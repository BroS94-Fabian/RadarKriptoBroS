# 🌡️ Model Kondisi Pasar

Dibuat 14 Nov 2026 17:06 WIB · 133 koin · sinyal 2020-09-17 s/d 2026-10-14 · meme coin tidak ikut

## Putusan

**✅ Model BARU dipakai radar** — di luar sampel 2023-01-01 s/d 2026-10-14: BARU +183.9% (maks turun -23.9%, Sharpe 1.04) vs LAMA +131.1% (maks turun -25.4%, Sharpe 0.8).

Model baru = aturan lama (beli hanya saat BTC tren naik, jual dulu hanya saat BTC tidak tren naik) **ditambah batas skor pasar** yang dipilih dari data: beli → BTC tren naik & skor pasar ≤ +4; jual dulu → BTC tidak tren naik (tanpa batas skor).

## Uji portofolio di luar sampel (2023-01-01 s/d 2026-10-14)

Maks 5 posisi sekaligus, tiap posisi = modal ÷ 5, tanpa leverage. Batas skor untuk tiap tahun uji dipilih hanya dari data tahun-tahun sebelumnya (walk-forward). Saat slot penuh, sinyal dipilih acak (median dari 100 urutan; dalam kurung = terendah…tertinggi).

| Susunan | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi | Hari ada posisi |
|---|---|---|---|---|---|---|---|---|
| Model LAMA (aturan tetap BTC MA50) | **+131.1%** (+72…+232) | 2023: +26% · 2024: +21% · 2025: +11% · 2026: +35% | -25.4% | 0.8 | 522 dari 998 | 74.5% | +0.94% | 82% |
| Model BARU (aturan lama + batas skor pasar) | **+183.9%** (+120…+275) | 2023: +26% · 2024: +36% · 2025: +16% · 2026: +38% | -23.9% | 1.04 | 442 dari 843 | 76.1% | +1.32% | 79% |
| Model BARU + strategi pendatang | **+224.6%** (+130…+355) | 2023: +26% · 2024: +51% · 2025: +16% · 2026: +45% | -23.9% | 1.14 | 470 dari 969 | 76.7% | +1.40% | 79% |
| LAMA — hanya beli | **+80.5%** (+34…+137) | 2023: +22% · 2024: +23% · 2025: -2% · 2026: +21% | -24.4% | 0.55 | 427 dari 790 | 72.8% | +0.86% | 54% |
| BARU — hanya beli | **+119.7%** (+72…+168) | 2023: +22% · 2024: +37% · 2025: +2% · 2026: +25% | -23.1% | 0.77 | 348 dari 635 | 74.5% | +1.30% | 51% |
| LAMA — hanya jual dulu (short) | **+27.9%** (+15…+43) | 2023: +4% · 2024: +1% · 2025: +12% · 2026: +10% | -7.4% | 0.89 | 100 dari 208 | 80.8% | +1.33% | 35% |
| BARU — hanya jual dulu (short) | **+27.9%** (+15…+43) | 2023: +4% · 2024: +1% · 2025: +12% · 2026: +10% | -7.4% | 0.89 | 100 dari 208 | 80.8% | +1.33% | 35% |
| Percobaan 1 (ambang skor per strategi, syarat t ≥ 2) — gagal | **-30.7%** (-37…-21) | 2023: +0% · 2024: -30% · 2025: +0% · 2026: -1% | -32.3% | -0.77 | 61 dari 105 | 55.0% | -2.80% | 10% |
| Tanpa filter pasar (3 strategi live, semua kondisi) | **+8.2%** (-20…+82) | 2023: -9% · 2024: +14% · 2025: -17% · 2026: +22% | -41.1% | 0.1 | 716 dari 1514 | 70.7% | +0.19% | 95% |
| Pembanding: beli & tahan BTC | +311.1% | 2023: +154% · 2024: +112% · 2025: -7% · 2026: -23% | -53.0% | 0.81 | - | - | - | 100% |

Perbandingan berpasangan (urutan acak yang sama untuk kedua model, 100 urutan): model baru lebih tinggi total untungnya di **100 dari 100**, Sharpe lebih tinggi di 100, penurunan maksimum lebih kecil di 53; selisih total (median) +48.5 poin.

Dengan maks 3 posisi: Model LAMA +168.6% (maks turun -34.2%, Sharpe 0.83) · Model BARU +242.3% (maks turun -23.2%, Sharpe 1.08)

Dengan maks 10 posisi: Model LAMA +94.9% (maks turun -21.6%, Sharpe 0.74) · Model BARU +111.0% (maks turun -21.6%, Sharpe 0.91) · Model BARU + strategi pendatang +129.0% (maks turun -21.6%, Sharpe 0.99)

### Aturan yang terpilih tiap tahun uji

| Tahun uji | Sisi | Batas terpilih dari data sebelumnya | Sharpe latih tiap batas | Hasil di tahun uji (model baru) | Bila tanpa batas (aturan lama) | Pendatang yang masuk |
|---|---|---|---|---|---|---|
| 2023 | beli | BTC tren naik (tanpa batas skor) | tanpa: 2.12 · ≤+5: 2.19 · ≤+4: 1.99 · ≤+3: 2.16 · ≤+2: 1.97 | -0.02% (267, menang 70.0%) | -0.02% (267, menang 70.0%) | - |
| 2023 | jual dulu | BTC tidak tren naik (tanpa batas skor) | data latih kurang | +1.79% (13, menang 92.3%) | +1.79% (13, menang 92.3%) | - |
| 2024 | beli | BTC tren naik & skor pasar ≤ +4 | tanpa: 1.45 · ≤+5: 1.54 · ≤+4: 1.59 · ≤+3: 1.67 · ≤+2: 1.67 · ≤+1: 1.07 | +3.77% (194, menang 84.0%) | +2.84% (252, menang 81.0%) | Tembus atap dasar + volume |
| 2024 | jual dulu | BTC tidak tren naik (tanpa batas skor) | tanpa: 1.69 · ≤+1: 1.69 · ≤-1: 1.55 | +1.13% (23, menang 73.9%) | +1.13% (23, menang 73.9%) | - |
| 2025 | beli | BTC tren naik & skor pasar ≤ +3 | tanpa: 1.19 · ≤+5: 1.24 · ≤+4: 1.33 · ≤+3: 1.47 · ≤+2: 1.37 · ≤+1: 1.06 | -1.55% (73, menang 63.0%) | -1.55% (105, menang 63.8%) | - |
| 2025 | jual dulu | BTC tidak tren naik (tanpa batas skor) | tanpa: 1.15 · ≤+1: 1.15 · ≤-1: 0.78 · ≤-2: 0.64 · ≤-3: 0.78 | +3.57% (133, menang 91.7%) | +3.57% (133, menang 91.7%) | - |
| 2026 | beli | BTC tren naik & skor pasar ≤ +4 | tanpa: 1.03 · ≤+5: 1.05 · ≤+4: 1.17 · ≤+3: 1.27 · ≤+2: 1.23 · ≤+1: 0.94 | +2.60% (101, menang 80.2%) | +1.78% (166, menang 76.5%) | Tembus atap dasar + volume |
| 2026 | jual dulu | BTC tidak tren naik (tanpa batas skor) | tanpa: 1.07 · ≤+1: 1.03 · ≤-1: 0.78 · ≤-2: 0.62 · ≤-3: 0.97 | +0.06% (39, menang 71.8%) | +0.06% (39, menang 71.8%) | - |

### Uji kepekaan: batas beli dipasang tetap sepanjang 2023–2026 (BUKAN walk-forward)

Untuk melihat apakah hasil bergantung pada satu angka batas saja. Sisi jual dulu memakai aturan lama.

| Beli hanya bila skor pasar | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |
|---|---|---|---|---|---|---|---|
| tanpa batas (= model lama) | +131.1% | 2023: +26% · 2024: +21% · 2025: +11% · 2026: +35% | -25.4% | 0.8 | 522 | 74.5% | +0.94% |
| ≤ +5 | +144.7% | 2023: +29% · 2024: +22% · 2025: +11% · 2026: +37% | -24.0% | 0.86 | 518 | 74.6% | +1.01% |
| ≤ +4 | +189.6% | 2023: +31% · 2024: +36% · 2025: +17% · 2026: +38% | -20.5% | 1.12 | 425 | 76.5% | +1.40% |
| ≤ +3 | +195.8% | 2023: +38% · 2024: +36% · 2025: +16% · 2026: +34% | -13.2% | 1.27 | 349 | 77.9% | +1.69% |
| ≤ +2 | +159.5% | 2023: +26% · 2024: +19% · 2025: +25% · 2026: +37% | -12.2% | 1.51 | 269 | 79.2% | +1.91% |
| ≤ +1 | +101.7% | 2023: +14% · 2024: +14% · 2025: +23% · 2026: +26% | -15.9% | 1.21 | 228 | 77.7% | +1.67% |

## Kenapa: hasil sinyal menurut kondisi pasar (seluruh data 2020–2026)

Sinyal beli live (🟢 radar + 🟩 awal Stage 2) **saat BTC tren naik**, dan sinyal 🔻 jual dulu **saat BTC tidak tren naik**:

| | sangat lemah (≤−4) | lemah (−3…−2) | campuran (−1…+1) | kuat (+2…+3) | sangat kuat (≥+4) |
|---|---|---|---|---|---|
| Sinyal beli | - | +4.10% (35, menang 71.4%) | +2.86% (145, menang 80.7%) | +2.15% (277, menang 80.1%) | +0.27% (510, menang 71.4%) |
| ↳ pembanding: beli acak | +3.42% (31, menang 90.3%) | +1.04% (1478, menang 76.3%) | +0.22% (4114, menang 72.3%) | +0.14% (4445, menang 72.7%) | -0.74% (5341, menang 67.9%) |
| ↳ jumlah hari | 3 | 70 | 287 | 332 | 445 |
| Sinyal jual dulu | +1.54% (131, menang 81.7%) | +4.20% (75, menang 93.3%) | +5.85% (17, menang 94.1%) | +1.95% (3, menang 100.0%) | - |
| ↳ pembanding: short acak | -0.48% (9901, menang 70.5%) | +0.58% (4931, menang 75.4%) | +0.24% (2643, menang 73.7%) | +1.66% (457, menang 79.9%) | +0.58% (94, menang 75.5%) |
| ↳ jumlah hari | 638 | 382 | 273 | 63 | 16 |

## Model akhir (dilatih dari semua data)

- **Beli** boleh jalan saat: BTC tren naik & skor pasar ≤ +4
- **Jual dulu** boleh jalan saat: BTC tidak tren naik (tanpa batas skor)

| Strategi | Sisi | Status | Sinyal di kondisi yang diizinkan | Menang | Rata-rata bersih |
|---|---|---|---|---|---|
| 🟢 Sinyal radar (skor ≥55) | beli | ✅ aktif | 241 | 74.3% | +2.36% |
| 🟩 Awal Stage 2 | beli | ✅ aktif | 435 | 80.7% | +1.81% |
| Tembus atap dasar + volume | beli | ✖ tidak aktif | 208 | 78.4% | +1.62% |
| Pullback Stage 2 ke Fibonacci | beli | ✖ tidak aktif | 438 | 71.2% | +0.20% |
| 🔻 Pantulan Stage 4 ke Fibonacci | jual dulu | ✅ aktif | 226 | 86.7% | +2.75% |
| Awal Stage 4 | jual dulu | ✖ tidak aktif | 1156 | 73.5% | -0.05% |
| Jebol lantai puncak + volume | jual dulu | ✖ tidak aktif | 60 | 71.7% | -1.00% |
| 🔴 Sinyal radar turun | jual dulu | ✖ tidak aktif | 71 | 64.8% | -1.70% |

## Hasil tiap strategi menurut kondisi pasar (semua arah BTC, deskriptif)

Jumlah hari per kondisi: sangat lemah (≤−4) 641 · lemah (−3…−2) 452 · campuran (−1…+1) 560 · kuat (+2…+3) 395 · sangat kuat (≥+4) 461

| Strategi | sangat lemah (≤−4) | lemah (−3…−2) | campuran (−1…+1) | kuat (+2…+3) | sangat kuat (≥+4) | Semua |
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

2026-11-13: skor **-5** (🔴🔴 SANGAT LEMAH) · BTC turun · koin di atas MA50 3% · Stage 2 3% · Stage 4 23%

## Catatan jujur

- **Percobaan 1 gagal.** Rancangan pertama (tiap strategi boleh jalan mulai skor tertentu, dengan syarat statistik ketat) hampir tidak pernah bertransaksi dan rugi; hasilnya tetap dicantumkan di tabel. Model versi 2 dirancang SETELAH melihat hasil itu, jadi angka ujinya tidak sebersih uji buta. Pegangannya: batas dipilih walk-forward, hasilnya mirip untuk batas +2, +3 dan +4, dan polanya sama di data 2020–2022 yang tidak dipakai sebagai tahun uji.
- Skor pasar memakai ambang bulat yang ditetapkan di muka; yang dipilih dari data hanya batas skor per sisi.
- Model lama disetel memakai data 2024–2026 (beli) dan 2020–2026 (short), jadi di uji ini model lama diuntungkan.
- Daftar koin = top CMC saat ini (koin yang sudah mati tidak ikut): hasil beli cenderung terlalu bagus, hasil short terlalu jelek.
- Untung-rugi dicatat saat posisi ditutup; penurunan sementara di tengah posisi tidak terlihat di 'maks turun'.
- Biaya: beli/jual 0,1% + pajak jual 0,21%; short 0,1% + 0,1% + pajak 0,21% + funding 0,03%/hari.
- Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual.
