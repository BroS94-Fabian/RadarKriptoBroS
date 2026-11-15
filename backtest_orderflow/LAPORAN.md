# 📊 Uji Order Flow & Market Profile

Dibuat 16 Nov 2026 00:02 WIB · 128 koin · 5,134,855 candle 1 jam (2020-01-01 s/d 2026-11-14) · sinyal 2020-09-17 s/d 2026-10-14 · meme coin tidak ikut

## Putusan

**❌ Tidak dipasang — di luar sampel tidak memenuhi syarat.**

- Dengan konfirmasi (dipilih walk-forward): +162.4% · maks turun -23.9% · Sharpe 0.99 · menang 76.5% · 422 transaksi
- DASAR (model pasar sekarang): +183.9% · maks turun -23.9% · Sharpe 1.04 · menang 76.1% · 442 transaksi
- Syarat pasang (ditetapkan di muka): total > DASAR, Sharpe ≥ DASAR + 0.15, maks turun tidak lebih buruk dari DASAR − 5 poin.
- Stop loss di batas zona nilai: **❌ tidak dipakai** — +132.1% · maks turun -32.2% · Sharpe 0.84 · menang 72.7% · 457 transaksi vs stop loss biasa +183.9% · maks turun -23.9% · Sharpe 1.04 · menang 76.1% · 442 transaksi.

## Yang diuji

Sinyal dan hasilnya sama persis dengan uji model pasar (🟢 radar, 🟩 awal Stage 2, 🔻 jual dulu pantulan Stage 4; rencana jual TP1 5% / SL 12% / maks 30 hari; biaya & pajak sudah dipotong). Bedanya: tiap sinyal diberi fitur dari candle 1 jam sampai penutupan hari sinyal — delta (beli agresif − jual agresif), arah CVD 3 hari, POC dan zona nilai (70% volume) 30 hari sebelumnya.

Sinyal live yang lolos gerbang pasar: 902 · punya fitur lengkap: 100.0%. Cek data: portofolio DASAR di sini +183.9% / Sharpe 1.04 — di laporan model pasar 183.9% / 1.04 → cocok.

| Kode | Konfirmasi | Untuk beli | Untuk jual dulu |
|---|---|---|---|
| va | Tutup di luar zona nilai | harga tutup di atas batas atas zona nilai 30 hari | harga tutup di bawah batas bawah zona nilai 30 hari |
| poc | Tutup melewati POC | harga tutup di atas POC 30 hari | harga tutup di bawah POC 30 hari |
| delta1 | Delta hari sinyal searah | beli agresif > jual agresif di hari sinyal | jual agresif > beli agresif di hari sinyal |
| delta3 | Delta 3 hari searah (CVD) | CVD 3 hari naik | CVD 3 hari turun |
| va_delta1 | Di luar zona nilai + delta hari sinyal | tutup di atas zona nilai DAN delta hari sinyal positif | tutup di bawah zona nilai DAN delta hari sinyal negatif |
| poc_delta3 | Melewati POC + delta 3 hari | tutup di atas POC DAN CVD 3 hari naik | tutup di bawah POC DAN CVD 3 hari turun |
| uji_va_delta1 | Uji zona nilai + delta hari sinyal | 3 hari terakhir menyentuh zona nilai, tutup di atas POC, delta positif | pantulan 3 hari terakhir menyentuh zona nilai, tutup di bawah POC, delta negatif |
| tembus_delta | Delta saat harga di luar zona nilai | tutup di atas zona nilai DAN jam-jam di atasnya didominasi beli agresif | tutup di bawah zona nilai DAN jam-jam di bawahnya didominasi jual agresif |

## Dengan vs tanpa konfirmasi (seluruh data 2020–2026, sinyal live yang lolos gerbang pasar)

Isi sel: rata-rata bersih per transaksi · tingkat menang (jumlah sinyal). p = peluang selisih sebesar itu muncul kebetulan (uji permutasi di dalam bulan yang sama). Ada 24 perbandingan, jadi baru layak disebut nyata bila p < 0.0021.

### 🟢 Sinyal radar (skor ≥55) — semua: +2.36% · menang 74.3% (241)

| Konfirmasi | Terkonfirmasi | Tidak | Selisih rata-rata | Selisih menang | p | Selisih 2020–22 | Selisih 2023–26 |
|---|---|---|---|---|---|---|---|
| Tutup di luar zona nilai | +1.97% · menang 82.4% (17) | +2.39% · menang 73.7% (224) | -0.42 | +8.7 | 0.802 | -2.59 | -0.12 |
| Tutup melewati POC | +3.09% · menang 81.0% (105) | +1.79% · menang 69.1% (136) | +1.30 | +11.9 | 0.688 | +3.24 | +0.93 |
| Delta hari sinyal searah | +2.01% · menang 77.3% (128) | +2.75% · menang 70.8% (113) | -0.74 | +6.5 | 0.360 | -4.76 | -0.36 |
| Delta 3 hari searah (CVD) | +2.26% · menang 76.2% (101) | +2.43% · menang 72.9% (140) | -0.17 | +3.3 | 0.847 | -6.12 | +0.49 |
| Di luar zona nilai + delta hari sinyal | +2.39% · menang 84.6% (13) | +2.35% · menang 73.7% (228) | +0.04 | +10.9 | 0.980 | -2.59 | +0.45 |
| Melewati POC + delta 3 hari | +3.63% · menang 84.5% (58) | +1.95% · menang 71.0% (183) | +1.68 | +13.5 | 0.432 | -1.11 | +2.03 |
| Uji zona nilai + delta hari sinyal | +3.31% · menang 84.1% (63) | +2.02% · menang 70.8% (178) | +1.29 | +13.3 | 0.609 | -1.39 | +1.59 |
| Delta saat harga di luar zona nilai | +3.93% · menang 90.0% (10) | +2.29% · menang 73.6% (231) | +1.64 | +16.4 | 0.537 | -2.50 | +2.42 |

### 🟩 Awal Stage 2 — semua: +1.81% · menang 80.7% (435)

| Konfirmasi | Terkonfirmasi | Tidak | Selisih rata-rata | Selisih menang | p | Selisih 2020–22 | Selisih 2023–26 |
|---|---|---|---|---|---|---|---|
| Tutup di luar zona nilai | +1.64% · menang 79.2% (231) | +2.00% · menang 82.4% (204) | -0.36 | -3.2 | 0.591 | +1.06 | -0.56 |
| Tutup melewati POC | +1.88% · menang 80.7% (374) | +1.37% · menang 80.3% (61) | +0.51 | +0.4 | 0.636 | +3.77 | -0.36 |
| Delta hari sinyal searah | +1.82% · menang 80.6% (165) | +1.80% · menang 80.7% (270) | +0.02 | -0.1 | 0.984 | +0.84 | -0.24 |
| Delta 3 hari searah (CVD) | +1.79% · menang 80.2% (192) | +1.82% · menang 81.1% (243) | -0.03 | -0.9 | 0.969 | -0.42 | -0.07 |
| Di luar zona nilai + delta hari sinyal | +1.46% · menang 78.2% (110) | +1.92% · menang 81.5% (325) | -0.46 | -3.3 | 0.591 | +0.54 | -0.68 |
| Melewati POC + delta 3 hari | +1.83% · menang 80.0% (170) | +1.79% · menang 81.1% (265) | +0.04 | -1.1 | 0.957 | +0.84 | -0.18 |
| Uji zona nilai + delta hari sinyal | +1.83% · menang 80.3% (127) | +1.80% · menang 80.8% (308) | +0.03 | -0.5 | 0.968 | +2.11 | -0.41 |
| Delta saat harga di luar zona nilai | +1.67% · menang 79.3% (116) | +1.86% · menang 81.2% (319) | -0.19 | -1.9 | 0.806 | +0.75 | -0.40 |

### 🔻 Pantulan Stage 4 ke Fibonacci — semua: +2.75% · menang 86.7% (226)

| Konfirmasi | Terkonfirmasi | Tidak | Selisih rata-rata | Selisih menang | p | Selisih 2020–22 | Selisih 2023–26 |
|---|---|---|---|---|---|---|---|
| Tutup di luar zona nilai | +2.34% · menang 86.5% (74) | +2.95% · menang 86.8% (152) | -0.61 | -0.3 | 0.816 | +5.87 | -0.93 |
| Tutup melewati POC | +2.92% · menang 89.3% (131) | +2.51% · menang 83.2% (95) | +0.41 | +6.1 | 0.788 | +0.75 | +0.52 |
| Delta hari sinyal searah | +2.23% · menang 86.7% (166) | +4.19% · menang 86.7% (60) | -1.96 | +0.0 | 0.148 | -3.57 | -1.57 |
| Delta 3 hari searah (CVD) | +2.40% · menang 87.2% (133) | +3.25% · menang 86.0% (93) | -0.85 | +1.2 | 0.357 | -2.89 | -0.46 |
| Di luar zona nilai + delta hari sinyal | +2.03% · menang 89.1% (55) | +2.98% · menang 86.0% (171) | -0.95 | +3.1 | 0.409 | -2.61 | -0.71 |
| Melewati POC + delta 3 hari | +1.79% · menang 87.4% (87) | +3.35% · menang 86.3% (139) | -1.56 | +1.1 | 0.081 | -3.63 | -1.29 |
| Uji zona nilai + delta hari sinyal | +2.33% · menang 92.5% (67) | +2.93% · menang 84.3% (159) | -0.60 | +8.2 | 0.596 | -3.79 | -0.27 |
| Delta saat harga di luar zona nilai | +2.46% · menang 88.9% (54) | +2.84% · menang 86.0% (172) | -0.38 | +2.9 | 0.814 | +5.98 | -0.70 |

Pembanding — beli / short di hari ACAK pada kondisi pasar yang sama (apakah konfirmasi itu memang menandai hari yang lebih baik?):

| Konfirmasi | Beli acak: terkonfirmasi | tidak | Short acak: terkonfirmasi | tidak |
|---|---|---|---|---|
| Tutup di luar zona nilai | +0.65% · menang 75.4% (2812) | +0.04% · menang 71.7% (9553) | -0.38% · menang 71.0% (7815) | +0.25% · menang 73.8% (10211) |
| Tutup melewati POC | +0.69% · menang 75.4% (6588) | -0.40% · menang 69.3% (5777) | -0.22% · menang 71.7% (13452) | +0.55% · menang 75.2% (4574) |
| Delta hari sinyal searah | +0.37% · menang 73.5% (4781) | +0.06% · menang 71.9% (7584) | -0.07% · menang 72.2% (10982) | +0.05% · menang 73.1% (7044) |
| Delta 3 hari searah (CVD) | +0.43% · menang 74.0% (4249) | +0.05% · menang 71.8% (8116) | +0.05% · menang 72.8% (11790) | -0.16% · menang 72.1% (6236) |
| Di luar zona nilai + delta hari sinyal | +0.54% · menang 74.8% (1335) | +0.14% · menang 72.3% (11030) | -0.50% · menang 70.3% (5035) | +0.16% · menang 73.4% (12991) |
| Melewati POC + delta 3 hari | +0.78% · menang 75.7% (2661) | +0.02% · menang 71.7% (9704) | -0.19% · menang 71.7% (9232) | +0.15% · menang 73.5% (8794) |
| Uji zona nilai + delta hari sinyal | +0.73% · menang 75.4% (2542) | +0.04% · menang 71.8% (9823) | -0.05% · menang 72.2% (5999) | -0.01% · menang 72.8% (12027) |
| Delta saat harga di luar zona nilai | +0.56% · menang 74.8% (1409) | +0.13% · menang 72.3% (10956) | -0.49% · menang 70.3% (5063) | +0.16% · menang 73.4% (12963) |

## Uji portofolio di luar sampel (2023-01-01 s/d 2026-10-14)

Maks 5 posisi, modal dibagi rata, median dari 100 urutan acak (dalam kurung = terendah…tertinggi).

| Susunan | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |
|---|---|---|---|---|---|---|---|
| DASAR (model pasar sekarang) | **+183.9%** (+120…+275) | 2023: +26% · 2024: +36% · 2025: +16% · 2026: +38% | -23.9% | 1.04 | 442 dari 843 | 76.1% | +1.32% |
| DASAR + konfirmasi order flow / market profile (walk-forward) | **+162.4%** (+110…+237) | 2023: +26% · 2024: +28% · 2025: +16% · 2026: +38% | -23.9% | 0.99 | 422 dari 795 | 76.5% | +1.30% |

Perbandingan berpasangan (100 urutan acak yang sama): dengan konfirmasi lebih tinggi totalnya di 2, Sharpe lebih tinggi di 0, penurunan maksimum lebih kecil di 0; selisih total (median) -18.1 poin.

### Konfirmasi yang terpilih tiap tahun uji (hanya dari data sebelum tahun itu)

| Tahun uji | Strategi | Terpilih | Sharpe latih: tanpa → terbaik | Hasil uji DASAR | Hasil uji dengan pilihan |
|---|---|---|---|---|---|
| 2023 | 🟢 Sinyal radar (skor ≥55) | tanpa konfirmasi | data latih kurang | +1.04% · menang 70.7% (75) | +1.04% · menang 70.7% (75) |
| 2023 | 🟩 Awal Stage 2 | tanpa konfirmasi | 2.12 → 2.09 (Tutup melewati POC, 119 sinyal) | -0.43% · menang 69.8% (192) | -0.43% · menang 69.8% (192) |
| 2023 | 🔻 Pantulan Stage 4 ke Fibonacci | tanpa konfirmasi | data latih kurang | +1.79% · menang 92.3% (13) | +1.79% · menang 92.3% (13) |
| 2024 | 🟢 Sinyal radar (skor ≥55) | Tutup melewati POC | 1.59 → 1.82 (Tutup melewati POC, 45 sinyal) | +5.51% · menang 82.4% (74) | +6.49% · menang 92.3% (26) |
| 2024 | 🟩 Awal Stage 2 | tanpa konfirmasi | 1.82 → 1.74 (Tutup melewati POC, 170 sinyal) | +2.70% · menang 85.0% (120) | +2.70% · menang 85.0% (120) |
| 2024 | 🔻 Pantulan Stage 4 ke Fibonacci | tanpa konfirmasi | data latih kurang | +1.13% · menang 73.9% (23) | +1.13% · menang 73.9% (23) |
| 2025 | 🟢 Sinyal radar (skor ≥55) | tanpa konfirmasi | 1.47 → 1.46 (Tutup melewati POC, 56 sinyal) | -3.89% · menang 48.6% (37) | -3.89% · menang 48.6% (37) |
| 2025 | 🟩 Awal Stage 2 | tanpa konfirmasi | 1.47 → 1.48 (Tutup melewati POC, 143 sinyal) | +0.86% · menang 77.8% (36) | +0.86% · menang 77.8% (36) |
| 2025 | 🔻 Pantulan Stage 4 ke Fibonacci | tanpa konfirmasi | 1.15 → 0.53 (Delta hari sinyal searah, 38 sinyal) | +3.57% · menang 91.7% (133) | +3.57% · menang 91.7% (133) |
| 2026 | 🟢 Sinyal radar (skor ≥55) | tanpa konfirmasi | 1.17 → 1.24 (Tutup melewati POC, 88 sinyal) | +3.35% · menang 74.2% (31) | +3.35% · menang 74.2% (31) |
| 2026 | 🟩 Awal Stage 2 | tanpa konfirmasi | 1.17 → 1.07 (Tutup melewati POC, 315 sinyal) | +2.27% · menang 82.9% (70) | +2.27% · menang 82.9% (70) |
| 2026 | 🔻 Pantulan Stage 4 ke Fibonacci | tanpa konfirmasi | 1.07 → 0.86 (Delta 3 hari searah (CVD), 119 sinyal) | +0.06% · menang 71.8% (39) | +0.06% · menang 71.8% (39) |

### Bila satu konfirmasi dipasang tetap sepanjang 2023–2026 (BUKAN walk-forward — melihat ke belakang, hanya untuk penjelasan)

Tiap baris: konfirmasi itu dipasang pada SATU strategi, sisanya seperti DASAR. DASAR: +183.9% · maks turun -23.9% · Sharpe 1.04 · menang 76.1% · 442 transaksi.

| Strategi | Konfirmasi | Total | Maks turun | Sharpe | Sinyal strategi itu (rata-rata · menang · jumlah) |
|---|---|---|---|---|---|
| 🟢 Sinyal radar (skor ≥55) | Tutup di luar zona nilai | +113.9% | -25.4% | 0.91 | +2.13% · menang 75.0% (16) |
| 🟢 Sinyal radar (skor ≥55) | Tutup melewati POC | +146.4% | -22.6% | 0.95 | +2.29% · menang 75.3% (93) |
| 🟢 Sinyal radar (skor ≥55) | Delta hari sinyal searah | +130.1% | -23.9% | 0.88 | +1.65% · menang 73.9% (111) |
| 🟢 Sinyal radar (skor ≥55) | Delta 3 hari searah (CVD) | +127.3% | -24.6% | 0.84 | +2.46% · menang 75.0% (84) |
| 🟢 Sinyal radar (skor ≥55) | Di luar zona nilai + delta hari sinyal | +111.7% | -25.4% | 0.92 | +1.95% · menang 72.7% (11) |
| 🟢 Sinyal radar (skor ≥55) | Melewati POC + delta 3 hari | +134.2% | -22.6% | 0.93 | +3.48% · menang 79.6% (49) |
| 🟢 Sinyal radar (skor ≥55) | Uji zona nilai + delta hari sinyal | +134.6% | -24.8% | 0.91 | +2.98% · menang 77.8% (54) |
| 🟢 Sinyal radar (skor ≥55) | Delta saat harga di luar zona nilai | +120.3% | -25.4% | 0.96 | +4.19% · menang 80.0% (10) |
| 🟩 Awal Stage 2 | Tutup di luar zona nilai | +113.6% | -31.6% | 0.86 | +0.77% · menang 75.0% (220) |
| 🟩 Awal Stage 2 | Tutup melewati POC | +146.1% | -27.9% | 0.92 | +0.97% · menang 76.7% (365) |
| 🟩 Awal Stage 2 | Delta hari sinyal searah | +109.1% | -20.1% | 0.94 | +0.79% · menang 74.8% (151) |
| 🟩 Awal Stage 2 | Delta 3 hari searah (CVD) | +118.6% | -24.7% | 0.91 | +1.10% · menang 76.0% (171) |
| 🟩 Awal Stage 2 | Di luar zona nilai + delta hari sinyal | +90.6% | -22.8% | 0.84 | +0.39% · menang 72.4% (98) |
| 🟩 Awal Stage 2 | Melewati POC + delta 3 hari | +120.0% | -28.5% | 0.91 | +1.14% · menang 76.1% (155) |
| 🟩 Awal Stage 2 | Uji zona nilai + delta hari sinyal | +79.2% | -22.9% | 0.76 | +0.46% · menang 73.0% (122) |
| 🟩 Awal Stage 2 | Delta saat harga di luar zona nilai | +103.0% | -22.8% | 0.89 | +0.61% · menang 73.8% (103) |
| 🔻 Pantulan Stage 4 ke Fibonacci | Tutup di luar zona nilai | +127.0% | -22.3% | 0.8 | +1.91% · menang 87.1% (70) |
| 🔻 Pantulan Stage 4 ke Fibonacci | Tutup melewati POC | +149.6% | -22.3% | 0.9 | +2.74% · menang 89.4% (123) |
| 🔻 Pantulan Stage 4 ke Fibonacci | Delta hari sinyal searah | +143.4% | -24.2% | 0.92 | +2.14% · menang 86.5% (156) |
| 🔻 Pantulan Stage 4 ke Fibonacci | Delta 3 hari searah (CVD) | +136.6% | -22.6% | 0.85 | +2.35% · menang 87.4% (127) |
| 🔻 Pantulan Stage 4 ke Fibonacci | Di luar zona nilai + delta hari sinyal | +133.4% | -22.3% | 0.84 | +2.00% · menang 90.6% (53) |
| 🔻 Pantulan Stage 4 ke Fibonacci | Melewati POC + delta 3 hari | +128.0% | -22.9% | 0.81 | +1.75% · menang 88.0% (83) |
| 🔻 Pantulan Stage 4 ke Fibonacci | Uji zona nilai + delta hari sinyal | +143.6% | -22.3% | 0.89 | +2.34% · menang 92.3% (65) |
| 🔻 Pantulan Stage 4 ke Fibonacci | Delta saat harga di luar zona nilai | +132.5% | -22.3% | 0.83 | +2.00% · menang 90.2% (51) |

Varian level (konfirmasi berbasis level dihitung dari profil lain):

| Profil | Strategi | Konfirmasi | Total | Maks turun | Sharpe | Sinyal strategi itu |
|---|---|---|---|---|---|---|
| profil waktu (TPO) 30 hari | 🟢 Sinyal radar (skor ≥55) | Tutup di luar zona nilai | +101.3% | -26.6% | 0.81 | +1.83% · menang 74.2% (31) |
| profil waktu (TPO) 30 hari | 🟩 Awal Stage 2 | Tutup di luar zona nilai | +114.3% | -23.4% | 0.81 | +1.14% · menang 77.3% (309) |
| profil waktu (TPO) 30 hari | 🔻 Pantulan Stage 4 ke Fibonacci | Tutup di luar zona nilai | +134.3% | -22.3% | 0.83 | +2.27% · menang 88.7% (71) |
| profil waktu (TPO) 30 hari | 🟢 Sinyal radar (skor ≥55) | Tutup melewati POC | +153.2% | -20.4% | 0.99 | +1.97% · menang 74.1% (116) |
| profil waktu (TPO) 30 hari | 🟩 Awal Stage 2 | Tutup melewati POC | +145.8% | -27.7% | 0.91 | +0.98% · menang 76.5% (395) |
| profil waktu (TPO) 30 hari | 🔻 Pantulan Stage 4 ke Fibonacci | Tutup melewati POC | +143.8% | -22.3% | 0.9 | +2.81% · menang 88.9% (117) |
| profil volume 90 hari | 🟢 Sinyal radar (skor ≥55) | Tutup di luar zona nilai | +127.2% | -25.4% | 0.98 | +2.53% · menang 80.0% (20) |
| profil volume 90 hari | 🟩 Awal Stage 2 | Tutup di luar zona nilai | +141.6% | -20.7% | 1.02 | +1.32% · menang 78.5% (260) |
| profil volume 90 hari | 🔻 Pantulan Stage 4 ke Fibonacci | Tutup di luar zona nilai | +134.4% | -22.6% | 0.87 | +3.46% · menang 90.5% (126) |
| profil volume 90 hari | 🟢 Sinyal radar (skor ≥55) | Tutup melewati POC | +138.4% | -22.3% | 0.96 | +2.60% · menang 76.6% (111) |
| profil volume 90 hari | 🟩 Awal Stage 2 | Tutup melewati POC | +183.9% | -22.8% | 1.08 | +1.04% · menang 77.0% (383) |
| profil volume 90 hari | 🔻 Pantulan Stage 4 ke Fibonacci | Tutup melewati POC | +166.8% | -22.0% | 0.98 | +2.85% · menang 87.8% (180) |

## Uji tambahan: stop loss di batas zona nilai

Beli: stop loss 1% di bawah batas bawah zona nilai; jual dulu: 1% di atas batas atas. Hanya dipakai bila jaraknya 3–12% dari harga masuk dan lebih dekat daripada stop loss biasa. Cek simulasi ulang: 100.0% sinyal hasilnya sama dengan data tersimpan (selisih rata-rata 0.002 poin).

| Strategi | Sinyal | Stop loss berubah | Semua sinyal: SL biasa | Semua sinyal: SL zona nilai | Yang berubah saja: SL biasa | SL zona nilai |
|---|---|---|---|---|---|---|
| 🟢 Sinyal radar (skor ≥55) | 241 | 111 | +2.36% · menang 74.3% (241) | +2.01% · menang 68.5% (241) | +3.35% · menang 81.1% (111) | +2.59% · menang 68.5% (111) |
| 🟩 Awal Stage 2 | 435 | 77 | +1.81% · menang 80.7% (435) | +1.81% · menang 79.5% (435) | +1.09% · menang 76.6% (77) | +1.11% · menang 70.1% (77) |
| 🔻 Pantulan Stage 4 ke Fibonacci | 226 | 31 | +2.75% · menang 86.7% (226) | +2.73% · menang 85.4% (226) | +1.43% · menang 74.2% (31) | +1.31% · menang 64.5% (31) |

Portofolio di luar sampel — SL biasa: +183.9% · maks turun -23.9% · Sharpe 1.04 · menang 76.1% · 442 transaksi

Portofolio di luar sampel — SL zona nilai: +132.1% · maks turun -32.2% · Sharpe 0.84 · menang 72.7% · 457 transaksi

Berpasangan: SL zona nilai lebih tinggi totalnya di 0 dari 100 urutan, Sharpe lebih tinggi di 0, penurunan maksimum lebih kecil di 0.

## Catatan jujur

- Ini bukan order flow penuh. Data gratis hanya memberi volume beli/jual agresif per candle 1 jam; order book, footprint per harga, absorption dan iceberg tidak ada datanya, jadi tidak diuji.
- Zona nilai memakai rumus yang sama dengan zona akumulasi radar (48 tingkat harga, 70% volume di sekitar POC), dari 30 hari sebelum hari sinyal.
- Radar 🟢 sudah memakai porsi beli agresif 24 jam dan posisi harga terhadap zona akumulasi di dalam skornya, jadi untuk sinyal 🟢 sebagian informasi ini sudah terpakai.
- Daftar konfirmasi, cara memilih dan syarat pasang ditulis sebelum data per jam ditarik. Tabel 'dipasang tetap' melihat ke belakang dan tidak dipakai untuk memutuskan.
- Daftar koin = koin top CMC saat ini (yang sudah mati tidak ikut); untung-rugi dicatat saat posisi ditutup.
- Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual.
