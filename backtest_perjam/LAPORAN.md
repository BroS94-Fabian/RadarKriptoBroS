# ⏱ Uji Sinyal Per Jam

Dibuat 16 Nov 2026 10:00 WIB · 12 koin · 167,706 candle 1 jam dianalisa satu per satu (±0.2 jam mesin) · sinyal 2025-03-17T20:00 s/d 2026-10-16T23:00 UTC · meme coin tidak ikut

## Putusan

**❌ Sinyal per jam TIDAK dipasang — tidak lebih baik dari sistem harian.**

- Harian (sistem sekarang): +183.9% · maks turun -23.9% · Sharpe 1.06 · menang 76.1% · 442 transaksi
- Per jam saja: -7.2% · maks turun -7.2% · Sharpe -0.57 · menang 61.6% · 86 transaksi
- Harian + per jam (5 slot bersama): +158.7% · maks turun -23.9% · Sharpe 0.97 · menang 73.9% · 506 transaksi
- Per jam saja bila bisa masuk TANPA jeda 1 jam (tidak realistis, hanya pembanding): -11.0% · maks turun -11.5% · Sharpe -0.64 · menang 59.3% · 86 transaksi
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
| 🟢 Radar naik | 512 | 0.89 | 188 | 0.33 |
| 🟩 Awal Stage 2 | 817 | 1.41 | 350 | 0.61 |
| 🔻 Jual dulu (pantulan Stage 4) | 288 | 0.5 | 207 | 0.36 |

## Hasil per sinyal (seluruh data, lolos gerbang pasar, masuk dengan jeda 1 jam)

Isi sel: rata-rata bersih per transaksi · tingkat menang (jumlah sinyal).

### 🟢 Radar naik

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.35% · menang 59.6% (188) | -3.54 | -0.53% · menang 59.6% (188) | -0.51% · menang 53.4% (88) | -0.41% · menang 59.6% (512) | 8.6 jam | 2025: -0.2 · 2026: -0.4 |
| B | -0.04% · menang 54.8% (188) | -0.32 | -0.13% · menang 52.7% (188) | -0.41% · menang 45.5% (88) | -0.31% · menang 51.0% (512) | 16.6 jam | 2025: +0.2 · 2026: -0.2 |
| C | -0.23% · menang 43.6% (188) | -0.97 | -0.10% · menang 45.7% (188) | -0.64% · menang 35.2% (88) | -0.41% · menang 42.0% (512) | 25.3 jam | 2025: -0.0 · 2026: -0.4 |
| D | -0.08% · menang 33.5% (188) | -0.24 | +0.02% · menang 34.0% (188) | -0.63% · menang 26.1% (88) | -0.46% · menang 30.3% (512) | 38.4 jam | 2025: +0.4 · 2026: -0.4 |

### 🟩 Awal Stage 2

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.36% · menang 71.4% (350) | -2.61 | -0.45% · menang 69.1% (350) | -0.34% · menang 72.0% (225) | -0.41% · menang 70.3% (817) | 6.8 jam | 2025: -0.3 · 2026: -0.4 |
| B | -0.46% · menang 68.9% (350) | -1.47 | -0.38% · menang 69.7% (350) | -0.37% · menang 69.3% (225) | -0.56% · menang 68.1% (817) | 21.2 jam | 2025: -0.5 · 2026: -0.4 |
| C | -0.60% · menang 68.0% (350) | -1.02 | -0.58% · menang 68.0% (350) | -0.24% · menang 70.2% (225) | -0.75% · menang 66.5% (817) | 44.8 jam | 2025: -1.1 · 2026: -0.2 |
| D | -0.45% · menang 69.1% (350) | -0.42 | -0.37% · menang 70.0% (350) | -0.04% · menang 71.6% (225) | -1.13% · menang 66.1% (817) | 115.5 jam | 2025: -0.9 · 2026: -0.0 |

### beli acak

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.59% · menang 65.8% (524) | -5.52 | -0.50% · menang 68.9% (524) | -0.60% · menang 65.7% (204) | -0.45% · menang 69.6% (1445) | 7.4 jam | 2025: -0.8 · 2026: -0.5 |
| B | -0.74% · menang 65.3% (524) | -2.94 | -0.47% · menang 68.5% (524) | -0.66% · menang 65.7% (204) | -0.64% · menang 66.4% (1445) | 24.8 jam | 2025: -0.9 · 2026: -0.6 |
| C | -0.36% · menang 69.5% (524) | -0.88 | -0.19% · menang 71.8% (524) | -0.60% · menang 69.6% (204) | -0.67% · menang 67.3% (1445) | 55.8 jam | 2025: -0.3 · 2026: -0.4 |
| D | +0.07% · menang 71.0% (524) | 0.07 | +0.09% · menang 71.4% (524) | -0.02% · menang 71.1% (204) | -1.04% · menang 65.7% (1445) | 130.0 jam | 2025: -0.1 · 2026: +0.3 |

### 🔻 Jual dulu (pantulan Stage 4)

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.27% · menang 72.5% (207) | -2.44 | -0.22% · menang 72.9% (207) | -0.23% · menang 74.1% (143) | -0.23% · menang 73.3% (288) | 9.8 jam | 2025: -0.3 · 2026: -0.2 |
| B | -0.30% · menang 62.3% (207) | -1.15 | -0.26% · menang 63.8% (207) | -0.24% · menang 65.0% (143) | -0.25% · menang 63.2% (288) | 21.9 jam | 2025: -0.2 · 2026: -0.3 |
| C | -0.25% · menang 56.5% (207) | -0.78 | -0.31% · menang 55.1% (207) | -0.10% · menang 60.1% (143) | -0.30% · menang 55.6% (288) | 31.9 jam | 2025: -0.3 · 2026: -0.2 |
| D | -0.15% · menang 43.5% (207) | -0.38 | -0.07% · menang 44.9% (207) | +0.00% · menang 46.2% (143) | -0.32% · menang 41.7% (288) | 52.3 jam | 2025: -0.6 · 2026: +0.2 |

### short acak

| Rencana | Jeda 1 jam | t | Tanpa jeda | + BTC per jam searah | Tanpa gerbang pasar | Lama posisi | Per tahun (rata-rata) |
|---|---|---|---|---|---|---|---|
| A | -0.50% · menang 68.7% (830) | -4.8 | -0.28% · menang 74.5% (830) | -0.44% · menang 70.3% (464) | -0.42% · menang 70.2% (1445) | 7.6 jam | 2025: -0.5 · 2026: -0.5 |
| B | -0.35% · menang 71.4% (830) | -1.47 | -0.41% · menang 70.5% (830) | -0.08% · menang 75.6% (464) | -0.26% · menang 72.7% (1445) | 23.4 jam | 2025: -0.5 · 2026: -0.2 |
| C | -0.09% · menang 73.7% (830) | -0.32 | -0.00% · menang 74.6% (830) | +0.14% · menang 76.5% (464) | -0.24% · menang 72.7% (1445) | 49.9 jam | 2025: -0.0 · 2026: -0.1 |
| D | +0.26% · menang 74.5% (830) | 0.55 | +0.39% · menang 75.2% (830) | -0.04% · menang 73.9% (464) | -0.09% · menang 73.4% (1445) | 138.7 jam | 2025: +0.9 · 2026: -0.3 |

## Uji portofolio di luar sampel (2023-01-01 s/d 2026-10-14)

Maks 5 posisi, modal dibagi rata, median dari 100 urutan acak (dalam kurung = terendah…tertinggi).

| Susunan | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |
|---|---|---|---|---|---|---|---|
| Harian (sistem sekarang) | **+183.9%** (+120…+275) | 2023: +24% · 2024: +38% · 2025: +14% · 2026: +38% | -23.9% | 1.06 | 442 dari 843 | 76.1% | +1.32% |
| Per jam saja | **-7.2%** (-7…-7) | 2023: +0% · 2024: +0% · 2025: +0% · 2026: -7% | -7.2% | -0.57 | 86 dari 86 | 61.6% | -0.42% |
| Harian + per jam (5 slot bersama) | **+158.7%** (+99…+243) | 2023: +24% · 2024: +38% · 2025: +14% · 2026: +28% | -23.9% | 0.97 | 506 dari 929 | 73.9% | +1.07% |

Berpasangan (100 urutan acak): per jam saja lebih tinggi dari harian di 0 urutan (Sharpe 0, penurunan lebih kecil 100); gabungan lebih tinggi dari harian di 1 (Sharpe 0, penurunan lebih kecil 0).

### Pilihan tiap tahun uji (hanya dari data sebelum tahun itu)

| Tahun uji | Sisi | Batas skor pasar | Rencana | + BTC per jam | Latih: Sharpe · total (sinyal) | Hasil uji |
|---|---|---|---|---|---|---|
| 2023 | Beli | ≤ +6 | - | - | sinyal latih kurang | - |
| 2023 | Jual dulu | ≤ +6 | - | - | sinyal latih kurang | - |
| 2024 | Beli | ≤ +4 | - | - | sinyal latih kurang | - |
| 2024 | Jual dulu | ≤ +6 | - | - | sinyal latih kurang | - |
| 2025 | Beli | ≤ +3 | - | - | sinyal latih kurang | - |
| 2025 | Jual dulu | ≤ +6 | - | - | sinyal latih kurang | - |
| 2026 | Beli | ≤ +4 | D | tidak | -0.01 · -3% (235) | tidak aktif (hasil latih terbaik pun tidak untung) |
| 2026 | Jual dulu | ≤ +6 | B | ya | 0.02 · +0% (57) | 🔻 -0.42% · menang 61.6% (86) |

### Bila satu rencana dipasang tetap sepanjang 2023–2026 (melihat ke belakang, hanya untuk penjelasan)

| Rencana | Total | Maks turun | Sharpe | Menang | Semua sinyal | Beli | Jual dulu |
|---|---|---|---|---|---|---|---|
| A | -37.5% | -38.5% | -1.47 | 68.5% | -0.36% · menang 67.9% (689) | -0.40% · menang 66.0% (482) | -0.27% · menang 72.5% (207) |
| B | -33.5% | -36.2% | -0.95 | 63.5% | -0.36% · menang 62.6% (689) | -0.38% · menang 62.7% (482) | -0.30% · menang 62.3% (207) |
| C | -22.8% | -26.9% | -0.51 | 60.2% | -0.47% · menang 57.5% (689) | -0.57% · menang 57.9% (482) | -0.25% · menang 56.5% (207) |
| D | -17.0% | -36.3% | -0.18 | 52.0% | -0.21% · menang 52.5% (689) | -0.24% · menang 56.4% (482) | -0.15% · menang 43.5% (207) |

## Catatan jujur

- Biaya & pajak ±0,41% per transaksi sama besarnya di candle 1 jam maupun harian, padahal gerak yang dikejar di candle 1 jam jauh lebih kecil — itu sebabnya rencana A (skala penuh) paling berat menanggung biaya.
- Jeda 1 jam adalah perkiraan: alert bisa datang 10–30 menit setelah candle tutup, lalu order dipasang manual.
- 'Diperbesar √24×' adalah cara menyamakan skala, bukan satu-satunya cara membaca candle 1 jam.
- Daftar koin = koin top CMC saat ini (yang sudah mati tidak ikut); untung-rugi dicatat saat posisi ditutup.
- Aturan uji ditulis sebelum data ditarik. Tabel 'dipasang tetap' melihat ke belakang dan tidak dipakai untuk memutuskan.
- Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual.
