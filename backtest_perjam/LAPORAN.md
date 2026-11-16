# ⏱ Uji Sinyal Per Jam

Dibuat 16 Nov 2026 10:46 WIB · 128 koin · 5,136,135 candle 1 jam dianalisa satu per satu (±3.5 jam mesin) · sinyal 2020-01-17T17:00 s/d 2026-10-17T01:00 UTC · meme coin tidak ikut

## Putusan

**❌ Sinyal per jam TIDAK dipasang — tidak lebih baik dari sistem harian.**

- Harian (sistem sekarang): +183.9% · maks turun -23.9% · Sharpe 1.06 · menang 76.1% · 442 transaksi
- Per jam saja: +11.4% · maks turun -46.9% · Sharpe 0.06 · menang 62.0% · 789 transaksi
- Harian + per jam (5 slot bersama): +109.9% · maks turun -33.7% · Sharpe 0.56 · menang 66.5% · 813 transaksi
- Per jam saja bila bisa masuk TANPA jeda 1 jam (tidak realistis, hanya pembanding): -10.8% · maks turun -48.2% · Sharpe -0.08 · menang 60.2% · 797 transaksi
- Syarat (ditetapkan di muka): total > harian, Sharpe ≥ harian + 0.15, maks turun tidak lebih buruk dari harian − 5 poin.

## Yang diuji

Mesin radar yang sama dijalankan di setiap jam pada 400 candle 1 jam terakhir. Karena gerak 1 jam ±1/5 gerak harian, candle diperbesar √24× dulu supaya semua ambang persen (pola, stage, Fibonacci, skor) sepadan; target & batal dikembalikan ke harga asli. Sinyal: 🟢 radar naik, 🟩 awal Stage 2, 🔻 jual dulu (pantulan Stage 4) — koin & jenis yang sama paling banyak sekali per 24 jam. Masuk di penutupan candle 1 jam berikutnya (jeda 1 jam untuk keterlambatan jadwal & pasang order manual). Gerbang pasar sama dengan sistem harian (arah BTC harian + skor pasar). Biaya & pajak sudah dipotong.

Cek simulator: portofolio sinyal harian di sini +183.9% / Sharpe 1.04 / maks turun -23.9% — simulator model pasar +183.9% / 1.04 / -23.9% → cocok.

| Rencana | Isi |
|---|---|
| A | TP1 +1% · SL −2,5% · maks 30 jam (skala penuh dari rencana harian) |
| B | TP1 +2% · SL −5% · maks 3 hari |
| C | TP1 +3% · SL −7,5% · maks 7 hari |
| D | TP1 +5% · SL −12% · maks 30 hari (rencana harian, masuknya saja per jam) |

## Berapa banyak sinyal per jam?

| Sinyal | Semua (2020–2026) | Per hari | Lolos gerbang pasar | Per hari |
|---|---|---|---|---|
| 🟢 Radar naik | 17,359 | 7.05 | 6,731 | 2.73 |
| 🟩 Awal Stage 2 | 28,378 | 11.52 | 11,997 | 4.87 |
| 🔻 Jual dulu (pantulan Stage 4) | 8,757 | 3.55 | 5,583 | 2.27 |

## Hasil per sinyal (seluruh data, lolos gerbang pasar, masuk dengan jeda 1 jam)

Isi sel: rata-rata bersih per transaksi · tingkat menang (jumlah sinyal).

### 🟢 Radar naik

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.37% · menang 62.1% (6731) | -9.56 | -0.39% · menang 63.4% (6731) | -0.45% · menang 59.7% (3430) | -0.43% · menang 60.9% (17359) | 8.7 jam | 2020: -0.3 · 2021: -0.2 · 2022: -0.4 · 2023: -0.4 · 2024: -0.4 · 2025: -0.4 · 2026: -0.4 |
| B | -0.30% · menang 53.5% (6731) | -3.85 | -0.32% · menang 53.2% (6731) | -0.34% · menang 52.0% (3430) | -0.42% · menang 51.1% (17359) | 15.8 jam | 2020: -0.2 · 2021: -0.0 · 2022: -0.4 · 2023: -0.2 · 2024: -0.5 · 2025: -0.4 · 2026: -0.2 |
| C | -0.23% · menang 46.1% (6731) | -2.19 | -0.23% · menang 45.8% (6731) | -0.30% · menang 43.9% (3430) | -0.39% · menang 43.6% (17359) | 22.3 jam | 2020: -0.1 · 2021: +0.1 · 2022: -0.3 · 2023: -0.1 · 2024: -0.4 · 2025: -0.4 · 2026: -0.2 |
| D | -0.10% · menang 36.5% (6731) | -0.62 | -0.10% · menang 35.7% (6731) | -0.18% · menang 34.4% (3430) | -0.39% · menang 33.3% (17359) | 34.7 jam | 2020: +0.1 · 2021: +0.2 · 2022: -0.3 · 2023: +0.1 · 2024: -0.3 · 2025: -0.4 · 2026: -0.1 |

### 🟩 Awal Stage 2

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.38% · menang 70.8% (11997) | -10.96 | -0.39% · menang 70.7% (11997) | -0.40% · menang 70.5% (8214) | -0.41% · menang 69.9% (28378) | 6.3 jam | 2020: -0.4 · 2021: -0.5 · 2022: -0.4 · 2023: -0.3 · 2024: -0.3 · 2025: -0.4 · 2026: -0.4 |
| B | -0.19% · menang 72.2% (11997) | -1.93 | -0.23% · menang 71.9% (11997) | -0.20% · menang 72.1% (8214) | -0.34% · menang 70.4% (28378) | 19.4 jam | 2020: -0.2 · 2021: -0.1 · 2022: -0.3 · 2023: -0.1 · 2024: -0.0 · 2025: -0.4 · 2026: -0.3 |
| C | -0.01% · menang 73.3% (11997) | -0.03 | -0.05% · menang 72.7% (11997) | +0.06% · menang 73.8% (8214) | -0.32% · menang 70.5% (28378) | 41.0 jam | 2020: -0.0 · 2021: +0.3 · 2022: -0.4 · 2023: +0.4 · 2024: +0.1 · 2025: -0.8 · 2026: +0.0 |
| D | +0.43% · menang 74.6% (11997) | 0.9 | +0.38% · menang 74.2% (11997) | +0.56% · menang 75.3% (8214) | -0.24% · menang 70.9% (28378) | 104.1 jam | 2020: +0.7 · 2021: +1.1 · 2022: -0.9 · 2023: +1.5 · 2024: +0.4 · 2025: -1.2 · 2026: +1.0 |

### beli acak

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.42% · menang 69.4% (17493) | -10.44 | -0.45% · menang 68.6% (17493) | -0.39% · menang 70.4% (8576) | -0.46% · menang 68.2% (48343) | 7.0 jam | 2020: -0.5 · 2021: -0.4 · 2022: -0.5 · 2023: -0.4 · 2024: -0.5 · 2025: -0.5 · 2026: -0.2 |
| B | -0.35% · menang 69.8% (17493) | -3.24 | -0.40% · menang 69.2% (17493) | -0.25% · menang 71.3% (8576) | -0.47% · menang 68.3% (48343) | 21.3 jam | 2020: -0.0 · 2021: -0.2 · 2022: -1.2 · 2023: +0.0 · 2024: -0.6 · 2025: -0.8 · 2026: -0.1 |
| C | -0.21% · menang 71.3% (17493) | -0.99 | -0.29% · menang 70.6% (17493) | -0.06% · menang 72.7% (8576) | -0.48% · menang 68.9% (48343) | 44.9 jam | 2020: +0.3 · 2021: +0.1 · 2022: -1.7 · 2023: +0.4 · 2024: -0.6 · 2025: -0.8 · 2026: +0.1 |
| D | +0.06% · menang 72.4% (17493) | 0.12 | +0.02% · menang 72.1% (17493) | +0.35% · menang 74.0% (8576) | -0.38% · menang 70.1% (48343) | 111.0 jam | 2020: +1.0 · 2021: +0.8 · 2022: -3.3 · 2023: +1.0 · 2024: -0.6 · 2025: -1.1 · 2026: +1.1 |

### 🔻 Jual dulu (pantulan Stage 4)

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.49% · menang 66.3% (5583) | -9.76 | -0.47% · menang 68.5% (5583) | -0.44% · menang 67.9% (3709) | -0.44% · menang 67.7% (8757) | 9.9 jam | 2020: -0.7 · 2021: -0.5 · 2022: -0.5 · 2023: -0.3 · 2024: -0.6 · 2025: -0.5 · 2026: -0.4 |
| B | -0.54% · menang 58.8% (5583) | -4.8 | -0.51% · menang 60.8% (5583) | -0.47% · menang 60.8% (3709) | -0.49% · menang 60.0% (8757) | 21.7 jam | 2020: -0.9 · 2021: -0.3 · 2022: -0.7 · 2023: -0.3 · 2024: -0.7 · 2025: -0.7 · 2026: -0.3 |
| C | -0.61% · menang 51.2% (5583) | -4.28 | -0.59% · menang 51.9% (5583) | -0.47% · menang 53.9% (3709) | -0.59% · menang 51.7% (8757) | 31.8 jam | 2020: -1.4 · 2021: -0.3 · 2022: -0.8 · 2023: -0.3 · 2024: -0.8 · 2025: -0.8 · 2026: -0.2 |
| D | -0.73% · menang 39.3% (5583) | -3.91 | -0.70% · menang 39.9% (5583) | -0.54% · menang 42.1% (3709) | -0.68% · menang 39.9% (8757) | 50.0 jam | 2020: -1.9 · 2021: -0.1 · 2022: -0.9 · 2023: -0.5 · 2024: -1.1 · 2025: -0.9 · 2026: -0.2 |

### short acak

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.41% · menang 69.8% (26350) | -16.41 | -0.42% · menang 69.4% (26350) | -0.41% · menang 69.5% (16784) | -0.42% · menang 69.5% (48343) | 7.2 jam | 2020: -0.5 · 2021: -0.3 · 2022: -0.5 · 2023: -0.3 · 2024: -0.4 · 2025: -0.5 · 2026: -0.4 |
| B | -0.36% · menang 69.8% (26350) | -5.9 | -0.36% · menang 69.7% (26350) | -0.34% · menang 70.0% (16784) | -0.42% · menang 69.3% (48343) | 21.8 jam | 2020: -0.6 · 2021: -0.2 · 2022: -0.4 · 2023: -0.4 · 2024: -0.3 · 2025: -0.4 · 2026: -0.2 |
| C | -0.31% · menang 71.1% (26350) | -2.78 | -0.31% · menang 71.1% (26350) | -0.29% · menang 71.2% (16784) | -0.47% · menang 69.9% (48343) | 45.8 jam | 2020: -0.7 · 2021: -0.2 · 2022: -0.4 · 2023: -0.2 · 2024: -0.4 · 2025: -0.3 · 2026: -0.2 |
| D | -0.24% · menang 71.7% (26350) | -0.97 | -0.26% · menang 71.6% (26350) | -0.22% · menang 71.8% (16784) | -0.63% · menang 69.6% (48343) | 121.0 jam | 2020: -1.2 · 2021: +0.1 · 2022: -0.1 · 2023: -0.1 · 2024: -0.9 · 2025: +0.0 · 2026: -0.1 |

## Uji portofolio di luar sampel (2023-01-01 s/d 2026-10-14)

Maks 5 posisi, modal dibagi rata, median dari 100 urutan acak (dalam kurung = terendah…tertinggi).

| Susunan | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |
|---|---|---|---|---|---|---|---|
| Harian (sistem sekarang) | **+183.9%** (+120…+275) | 2023: +24% · 2024: +38% · 2025: +14% · 2026: +38% | -23.9% | 1.06 | 442 dari 843 | 76.1% | +1.32% |
| Per jam saja | **+11.4%** (-18…+59) | 2023: +36% · 2024: +8% · 2025: -32% · 2026: +13% | -46.9% | 0.06 | 789 dari 9183 | 62.0% | +0.19% |
| Harian + per jam (5 slot bersama) | **+109.9%** (+49…+197) | 2023: +66% · 2024: +13% · 2025: -11% · 2026: +22% | -33.7% | 0.56 | 813 dari 10026 | 66.5% | +0.58% |

Berpasangan (100 urutan acak): per jam saja lebih tinggi dari harian di 0 urutan (Sharpe 0, penurunan lebih kecil 0); gabungan lebih tinggi dari harian di 2 (Sharpe 0, penurunan lebih kecil 0).

### Pilihan tiap tahun uji (hanya dari data sebelum tahun itu)

| Tahun uji | Sisi | Batas skor pasar | Rencana | + BTC per jam | Latih: Sharpe · total (sinyal) | Hasil uji |
|---|---|---|---|---|---|---|
| 2023 | Beli | ≤ +6 | D | ya | 1.1 · +158% (3763) | 🟢 -0.11% · menang 31.9% (878) · 🟩 +1.44% · menang 80.2% (2186) |
| 2023 | Jual dulu | ≤ +6 | D | ya | -0.42 · -27% (1127) | tidak aktif (hasil latih terbaik pun tidak untung) |
| 2024 | Beli | ≤ +4 | D | ya | 1.04 · +208% (5264) | 🟢 +0.02% · menang 37.5% (690) · 🟩 +0.61% · menang 75.8% (1662) |
| 2024 | Jual dulu | ≤ +6 | D | ya | -0.35 · -28% (1588) | tidak aktif (hasil latih terbaik pun tidak untung) |
| 2025 | Beli | ≤ +3 | D | ya | 0.85 · +217% (5791) | 🟢 -0.96% · menang 25.5% (580) · 🟩 -1.55% · menang 63.3% (1476) |
| 2025 | Jual dulu | ≤ +6 | D | ya | -0.7 · -51% (2167) | tidak aktif (hasil latih terbaik pun tidak untung) |
| 2026 | Beli | ≤ +4 | D | ya | 0.62 · +153% (9933) | 🟢 -0.05% · menang 33.8% (550) · 🟩 +1.60% · menang 79.8% (1161) |
| 2026 | Jual dulu | ≤ +6 | D | ya | -0.94 · -67% (2958) | tidak aktif (hasil latih terbaik pun tidak untung) |

### Bila satu rencana dipasang tetap sepanjang 2023–2026 (melihat ke belakang, hanya untuk penjelasan)

| Rencana | Total | Maks turun | Sharpe | Menang | Semua sinyal | Beli | Jual dulu |
|---|---|---|---|---|---|---|---|
| A | -99.9% | -99.9% | -6.41 | 66.5% | -0.41% · menang 66.8% (18834) | -0.39% · menang 66.9% (14970) | -0.47% · menang 66.4% (3864) |
| B | -97.8% | -98.3% | -3.1 | 61.5% | -0.34% · menang 62.7% (18834) | -0.30% · menang 63.8% (14970) | -0.51% · menang 58.5% (3864) |
| C | -90.4% | -93.2% | -1.58 | 57.4% | -0.26% · menang 59.5% (18834) | -0.18% · menang 61.6% (14970) | -0.56% · menang 51.1% (3864) |
| D | -72.3% | -86.2% | -0.7 | 49.6% | -0.01% · menang 55.2% (18834) | +0.17% · menang 59.4% (14970) | -0.70% · menang 39.1% (3864) |

## Catatan jujur

- Biaya & pajak ±0,41% per transaksi sama besarnya di candle 1 jam maupun harian, padahal gerak yang dikejar di candle 1 jam jauh lebih kecil — itu sebabnya rencana A (skala penuh) paling berat menanggung biaya.
- Jeda 1 jam adalah perkiraan: alert bisa datang 10–30 menit setelah candle tutup, lalu order dipasang manual.
- 'Diperbesar √24×' adalah cara menyamakan skala, bukan satu-satunya cara membaca candle 1 jam.
- Daftar koin = koin top CMC saat ini (yang sudah mati tidak ikut); untung-rugi dicatat saat posisi ditutup.
- Aturan uji ditulis sebelum data ditarik. Tabel 'dipasang tetap' melihat ke belakang dan tidak dipakai untuk memutuskan.
- Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual.
