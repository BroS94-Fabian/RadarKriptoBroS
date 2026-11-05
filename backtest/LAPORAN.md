# 🧪 Laporan Backtest Radar Kripto

Dibuat: 5 Nov 2026 09:29 WIB · Periode: 2024-10-29 s/d 2026-10-03 · 125 koin top CMC di Binance · 315 sinyal (261 naik, 54 turun)

Hasil **bersih** per sinyal (sudah dipotong biaya beli 0,1%, jual 0,1%, pajak jual 0,21%). Satu sinyal = satu posisi dengan modal sama.

## 1. Sinyal 🟢 potensi naik — perbandingan aturan jual

| Aturan jual | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| Target & batal pola (tanpa TP1) | 261 | 37.2% | -0.91% | -6.69% | -238.7% | 0.88 | 14.0 |
| Target pola, SL maks −8% | 261 | 29.9% | -0.24% | -8.38% | -63.5% | 0.96 | 8.8 |
| Target pola, SL maks −12% | 261 | 33.7% | -0.75% | -8.56% | -196.7% | 0.89 | 11.1 |
| Target pola, SL maks −15% | 261 | 35.6% | -0.84% | -7.47% | -219.9% | 0.88 | 12.5 |
| 50% di +5%, sisa ke target pola, SL batal pola → impas | 261 | 70.1% | +0.19% | +2.08% | +50.7% | 1.05 | 8.3 |
| 50% di +10%, sisa ke target pola, SL batal pola → impas | 261 | 52.5% | -0.50% | +4.58% | -130.1% | 0.92 | 12.1 |
| 50% di +5%, sisa ke target pola, SL maks −8% → impas | 261 | 59.8% | +0.13% | +2.08% | +34.7% | 1.04 | 5.5 |
| 50% di +5%, sisa ke target pola, SL maks −12% → impas | 261 | 65.9% | +0.12% | +2.08% | +31.9% | 1.04 | 6.8 |
| 50% di +7%, sisa ke target pola, SL maks −12% → impas | 261 | 57.9% | -0.06% | +3.08% | -15.3% | 0.99 | 8.2 |
| TP +3% / SL −3% (jual semua) | 261 | 44.4% | -0.73% | -3.40% | -191.3% | 0.61 | 1.6 |
| TP +5% / SL −5% (jual semua) | 261 | 51.3% | -0.27% | +4.58% | -70.4% | 0.9 | 2.5 |
| TP +8% / SL −4% (jual semua) | 261 | 36.0% | -0.10% | -4.40% | -25.6% | 0.96 | 3.0 |
| TP +10% / SL −5% (jual semua) | 261 | 37.2% | +0.13% | -5.39% | +33.1% | 1.04 | 4.2 |
| TP 2×ATR / SL 1×ATR | 261 | 34.1% | -1.06% | -6.03% | -277.2% | 0.8 | 6.2 |
| TP 3×ATR / SL 1,5×ATR | 261 | 31.8% | -2.71% | -9.38% | -708.0% | 0.66 | 9.8 |
| 50% di +3%, sisa ke target pola, SL −3% → impas | 261 | 44.1% | +0.06% | -3.40% | +14.4% | 1.03 | 3.1 |
| 50% di +5%, sisa ke target pola, SL −5% → impas | 261 | 50.2% | +0.19% | +1.88% | +50.4% | 1.07 | 4.5 |
| 50% di 1,5×ATR, sisa ke target pola, SL 1,5×ATR → impas | 261 | 42.5% | -1.61% | -6.36% | -420.0% | 0.73 | 8.8 |
| Tahan 7 hari (tanpa TP/SL) | 261 | 39.5% | -0.83% | -2.52% | -215.7% | 0.85 | 7.0 |
| Tahan 14 hari (tanpa TP/SL) | 261 | 45.6% | +1.46% | -2.74% | +382.0% | 1.24 | 14.0 |

**Aturan jual terbaik (rata-rata bersih tertinggi): 50% di +5%, sisa ke target pola, SL batal pola → impas**

## 2. Rincian sinyal naik (aturan: 50% di +5%, sisa ke target pola, SL batal pola → impas)

### Kondisi pasar BTC

| Kondisi pasar BTC | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| naik | 127 | 74.8% | +1.88% | +2.08% | +238.2% | 1.59 | 7.9 |
| netral | 39 | 56.4% | -0.41% | +2.08% | -16.1% | 0.91 | 7.5 |
| turun | 95 | 69.5% | -1.80% | +2.08% | -171.4% | 0.59 | 9.2 |

### Meme coin

| Meme coin | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| bukan meme | 244 | 70.9% | +0.51% | +2.08% | +123.6% | 1.14 | 8.6 |
| meme | 17 | 58.8% | -4.29% | +2.08% | -72.9% | 0.3 | 4.9 |

### Status pola

| Status pola | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| breakout | 106 | 74.5% | +0.47% | +2.08% | +49.5% | 1.11 | 9.3 |
| terbentuk | 119 | 66.4% | -0.57% | +2.08% | -67.7% | 0.85 | 7.9 |
| uji | 36 | 69.4% | +1.91% | +2.08% | +68.9% | 1.68 | 6.9 |

### Jenis pola

| Jenis pola | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| Double Bottom | 86 | 69.8% | +1.06% | +2.08% | +91.3% | 1.31 | 7.3 |
| Falling Wedge | 67 | 82.1% | +1.90% | +2.08% | +127.0% | 1.5 | 10.1 |
| Inverse Head and Shoulders | 49 | 59.2% | -2.99% | +2.08% | -146.4% | 0.42 | 10.2 |
| Triple Bottom | 24 | 66.7% | +0.30% | +2.08% | +7.3% | 1.08 | 8.5 |
| Bull Flag (Downward Flag) | 18 | 77.8% | +0.58% | +2.08% | +10.5% | 1.28 | 4.5 |
| Symmetrical Triangle | 10 | 60.0% | -0.42% | +2.08% | -4.2% | 0.75 | 5.1 |
| Ascending Triangle | 3 | 0.0% | -5.61% | -4.54% | -16.8% | 0.0 | 3.0 |
| Bullish Pennant | 2 | 50.0% | -11.04% | -11.04% | -22.1% | 0.09 | 4.5 |
| Cup and Handle | 2 | 100.0% | +2.08% | +2.08% | +4.2% | - | 5.5 |

### Skor naik

| Skor naik | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| 55–59 | 192 | 70.3% | +0.19% | +2.08% | +36.1% | 1.06 | 8.4 |
| 60–64 | 59 | 69.5% | -0.36% | +2.08% | -21.3% | 0.93 | 8.7 |
| 65+ | 10 | 70.0% | +3.58% | +2.08% | +35.8% | 2.67 | 4.3 |

### Peringkat CMC

| Peringkat CMC | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| 1–50 | 55 | 78.2% | +0.82% | +2.08% | +45.2% | 1.33 | 10.9 |
| 51–100 | 58 | 75.9% | +0.54% | +2.08% | +31.1% | 1.17 | 6.7 |
| 101–200 | 148 | 64.9% | -0.17% | +2.08% | -25.7% | 0.96 | 8.0 |

### Posisi zona akumulasi

| Posisi zona akumulasi | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| bawah | 40 | 85.0% | +3.65% | +2.08% | +146.0% | 3.67 | 7.6 |
| dalam-bawah | 122 | 63.1% | -0.89% | +2.08% | -108.9% | 0.82 | 8.0 |
| dalam-atas | 89 | 74.2% | +0.17% | +2.08% | +15.2% | 1.05 | 8.5 |
| atas | 10 | 60.0% | -0.17% | +2.08% | -1.7% | 0.95 | 13.2 |

## 3. Pengaruh filter (sinyal naik)

### Aturan: 50% di +5%, sisa ke target pola, SL batal pola → impas

| Filter | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| tanpa filter | 261 | 70.1% | +0.19% | +2.08% | +50.7% | 1.05 | 8.3 |
| filter pasar BTC | 166 | 70.5% | +1.34% | +2.08% | +222.1% | 1.39 | 7.8 |
| tanpa meme | 244 | 70.9% | +0.51% | +2.08% | +123.6% | 1.14 | 8.6 |
| meme butuh skor ≥60 | 249 | 70.7% | +0.37% | +2.08% | +91.6% | 1.1 | 8.5 |
| hanya breakout | 106 | 74.5% | +0.47% | +2.08% | +49.5% | 1.11 | 9.3 |
| pasar BTC + tanpa meme | 154 | 72.7% | +2.00% | +2.08% | +308.4% | 1.66 | 8.0 |
| pasar BTC + meme ≥60 | 158 | 72.2% | +1.74% | +2.08% | +274.3% | 1.54 | 7.9 |
| pasar BTC naik saja | 127 | 74.8% | +1.88% | +2.08% | +238.2% | 1.59 | 7.9 |
| pasar BTC naik + tanpa meme | 116 | 77.6% | +2.74% | +2.08% | +318.1% | 2.04 | 8.1 |
| pasar BTC + tanpa meme + breakout | 64 | 78.1% | +2.93% | +2.08% | +187.4% | 1.98 | 8.0 |
| skor ≥60 | 69 | 69.6% | +0.21% | +2.08% | +14.6% | 1.04 | 8.0 |
| pasar BTC naik + tanpa meme + skor ≥55 | 116 | 77.6% | +2.74% | +2.08% | +318.1% | 2.04 | 8.1 |
| pasar BTC naik + tanpa meme + breakout | 53 | 83.0% | +3.52% | +2.08% | +186.4% | 2.5 | 7.6 |
| pasar BTC + tanpa meme + skor ≥55 | 154 | 72.7% | +2.00% | +2.08% | +308.4% | 1.66 | 8.0 |

### Aturan: Target & batal pola (tanpa TP1)

| Filter | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| tanpa filter | 261 | 37.2% | -0.91% | -6.69% | -238.7% | 0.88 | 14.0 |
| filter pasar BTC | 166 | 44.0% | +2.70% | -4.96% | +448.9% | 1.43 | 11.7 |
| tanpa meme | 244 | 38.1% | -0.46% | -6.56% | -111.3% | 0.94 | 14.0 |
| meme butuh skor ≥60 | 249 | 37.3% | -0.75% | -6.95% | -186.2% | 0.91 | 13.9 |
| hanya breakout | 106 | 49.1% | +1.02% | -0.99% | +108.5% | 1.13 | 15.1 |
| pasar BTC + tanpa meme | 154 | 46.1% | +3.63% | -4.07% | +558.6% | 1.61 | 12.0 |
| pasar BTC + meme ≥60 | 158 | 44.9% | +3.15% | -4.48% | +497.3% | 1.51 | 11.8 |
| pasar BTC naik saja | 127 | 47.2% | +3.25% | -3.84% | +412.2% | 1.53 | 11.8 |
| pasar BTC naik + tanpa meme | 116 | 50.0% | +4.44% | +0.46% | +515.5% | 1.79 | 12.0 |
| pasar BTC + tanpa meme + breakout | 64 | 65.6% | +7.99% | +10.05% | +511.6% | 2.77 | 11.1 |
| skor ≥60 | 69 | 46.4% | +1.37% | -5.43% | +94.8% | 1.17 | 12.5 |
| pasar BTC naik + tanpa meme + skor ≥55 | 116 | 50.0% | +4.44% | +0.46% | +515.5% | 1.79 | 12.0 |
| pasar BTC naik + tanpa meme + breakout | 53 | 69.8% | +8.70% | +11.06% | +460.9% | 3.1 | 10.8 |
| pasar BTC + tanpa meme + skor ≥55 | 154 | 46.1% | +3.63% | -4.07% | +558.6% | 1.61 | 12.0 |

### Aturan: Target pola, SL maks −12%

| Filter | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| tanpa filter | 261 | 33.7% | -0.75% | -8.56% | -196.7% | 0.89 | 11.1 |
| filter pasar BTC | 166 | 39.2% | +1.59% | -6.56% | +263.5% | 1.26 | 9.2 |
| tanpa meme | 244 | 34.4% | -0.36% | -8.16% | -88.7% | 0.95 | 11.2 |
| meme butuh skor ≥60 | 249 | 33.7% | -0.59% | -8.59% | -147.1% | 0.91 | 11.1 |
| hanya breakout | 106 | 44.3% | +1.52% | -6.14% | +160.7% | 1.25 | 11.4 |
| pasar BTC + tanpa meme | 154 | 40.9% | +2.22% | -6.35% | +342.3% | 1.37 | 9.5 |
| pasar BTC + meme ≥60 | 158 | 39.9% | +1.88% | -6.56% | +296.4% | 1.31 | 9.4 |
| pasar BTC naik saja | 127 | 44.9% | +3.45% | -5.68% | +438.5% | 1.61 | 9.4 |
| pasar BTC naik + tanpa meme | 116 | 47.4% | +4.40% | -4.48% | +510.9% | 1.82 | 9.8 |
| pasar BTC + tanpa meme + breakout | 64 | 59.4% | +6.16% | +9.07% | +394.5% | 2.39 | 9.0 |
| skor ≥60 | 69 | 43.5% | +1.93% | -5.68% | +133.2% | 1.33 | 10.5 |
| pasar BTC naik + tanpa meme + skor ≥55 | 116 | 47.4% | +4.40% | -4.48% | +510.9% | 1.82 | 9.8 |
| pasar BTC naik + tanpa meme + breakout | 53 | 66.0% | +8.43% | +10.45% | +446.5% | 3.23 | 9.0 |
| pasar BTC + tanpa meme + skor ≥55 | 154 | 40.9% | +2.22% | -6.35% | +342.3% | 1.37 | 9.5 |

### Aturan: 50% di +5%, sisa ke target pola, SL maks −12% → impas

| Filter | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| tanpa filter | 261 | 65.9% | +0.12% | +2.08% | +31.9% | 1.04 | 6.8 |
| filter pasar BTC | 166 | 64.5% | +0.55% | +2.08% | +91.7% | 1.15 | 6.1 |
| tanpa meme | 244 | 66.4% | +0.31% | +2.08% | +75.8% | 1.09 | 7.1 |
| meme butuh skor ≥60 | 249 | 66.3% | +0.23% | +2.08% | +57.3% | 1.07 | 7.1 |
| hanya breakout | 106 | 70.8% | +0.77% | +2.08% | +81.8% | 1.24 | 7.4 |
| pasar BTC + tanpa meme | 154 | 66.2% | +0.97% | +2.08% | +149.0% | 1.28 | 6.4 |
| pasar BTC + meme ≥60 | 158 | 65.8% | +0.81% | +2.08% | +128.4% | 1.23 | 6.3 |
| pasar BTC naik saja | 127 | 70.1% | +1.63% | +2.08% | +207.5% | 1.51 | 6.1 |
| pasar BTC naik + tanpa meme | 116 | 72.4% | +2.23% | +2.08% | +258.3% | 1.77 | 6.4 |
| pasar BTC + tanpa meme + breakout | 64 | 71.9% | +1.63% | +2.08% | +104.2% | 1.51 | 6.2 |
| skor ≥60 | 69 | 66.7% | +0.74% | +2.08% | +51.0% | 1.2 | 6.9 |
| pasar BTC naik + tanpa meme + skor ≥55 | 116 | 72.4% | +2.23% | +2.08% | +258.3% | 1.77 | 6.4 |
| pasar BTC naik + tanpa meme + breakout | 53 | 79.2% | +3.12% | +2.08% | +165.4% | 2.31 | 6.1 |
| pasar BTC + tanpa meme + skor ≥55 | 154 | 66.2% | +0.97% | +2.08% | +149.0% | 1.28 | 6.4 |

### Aturan: 50% di +5%, sisa ke target pola, SL maks −8% → impas

| Filter | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| tanpa filter | 261 | 59.8% | +0.13% | +2.08% | +34.7% | 1.04 | 5.5 |
| filter pasar BTC | 166 | 59.0% | +0.56% | +2.08% | +93.5% | 1.18 | 5.1 |
| tanpa meme | 244 | 59.8% | +0.24% | +2.08% | +58.7% | 1.08 | 5.7 |
| meme butuh skor ≥60 | 249 | 59.8% | +0.19% | +2.08% | +48.2% | 1.06 | 5.7 |
| hanya breakout | 106 | 63.2% | +0.83% | +2.08% | +88.4% | 1.28 | 6.0 |
| pasar BTC + tanpa meme | 154 | 60.4% | +0.85% | +2.08% | +130.9% | 1.27 | 5.3 |
| pasar BTC + meme ≥60 | 158 | 60.1% | +0.75% | +2.08% | +118.3% | 1.24 | 5.3 |
| pasar BTC naik saja | 127 | 66.1% | +1.87% | +2.08% | +237.5% | 1.69 | 5.2 |
| pasar BTC naik + tanpa meme | 116 | 68.1% | +2.31% | +2.08% | +268.4% | 1.91 | 5.4 |
| pasar BTC + tanpa meme + breakout | 64 | 67.2% | +1.97% | +2.08% | +125.9% | 1.73 | 5.4 |
| skor ≥60 | 69 | 58.0% | +0.43% | +2.08% | +29.7% | 1.13 | 5.6 |
| pasar BTC naik + tanpa meme + skor ≥55 | 116 | 68.1% | +2.31% | +2.08% | +268.4% | 1.91 | 5.4 |
| pasar BTC naik + tanpa meme + breakout | 53 | 75.5% | +3.41% | +2.08% | +181.0% | 2.7 | 5.3 |
| pasar BTC + tanpa meme + skor ≥55 | 154 | 60.4% | +0.85% | +2.08% | +130.9% | 1.27 | 5.3 |

**Kombinasi terbaik:** pasar BTC naik + tanpa meme + breakout + Target & batal pola (tanpa TP1) → 53 sinyal, menang 69.8%, rata-rata bersih +8.70% per sinyal.

## 4. Sinyal 🔴 potensi turun (sebagai posisi short)

| Aturan jual | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| Target & batal pola (tanpa TP1) | 54 | 38.9% | -2.65% | -9.98% | -142.9% | 0.74 | 14.7 |
| Target pola, SL maks −8% | 54 | 14.8% | -3.61% | -8.38% | -194.8% | 0.49 | 7.2 |
| Target pola, SL maks −12% | 54 | 22.2% | -4.58% | -12.37% | -247.1% | 0.5 | 10.8 |
| Target pola, SL maks −15% | 54 | 31.5% | -2.40% | -10.45% | -129.6% | 0.72 | 12.8 |
| 50% di +5%, sisa ke target pola, SL batal pola → impas | 54 | 57.4% | -3.46% | +2.08% | -186.8% | 0.46 | 8.1 |
| 50% di +10%, sisa ke target pola, SL batal pola → impas | 54 | 46.3% | -3.29% | -7.15% | -177.7% | 0.59 | 12.9 |
| 50% di +5%, sisa ke target pola, SL maks −8% → impas | 54 | 44.4% | -2.01% | -8.38% | -108.6% | 0.57 | 5.8 |
| 50% di +5%, sisa ke target pola, SL maks −12% → impas | 54 | 50.0% | -2.97% | -3.34% | -160.2% | 0.48 | 7.3 |
| 50% di +7%, sisa ke target pola, SL maks −12% → impas | 54 | 38.9% | -4.08% | -10.28% | -220.2% | 0.42 | 8.7 |
| TP +3% / SL −3% (jual semua) | 54 | 42.6% | -0.85% | -3.40% | -46.1% | 0.56 | 1.4 |
| TP +5% / SL −5% (jual semua) | 54 | 37.0% | -1.70% | -5.39% | -91.9% | 0.5 | 2.9 |
| TP +8% / SL −4% (jual semua) | 54 | 20.4% | -1.96% | -4.40% | -105.9% | 0.44 | 3.2 |
| TP +10% / SL −5% (jual semua) | 54 | 24.1% | -1.79% | -5.39% | -96.9% | 0.56 | 4.1 |
| TP 2×ATR / SL 1×ATR | 54 | 14.8% | -4.86% | -6.60% | -262.3% | 0.32 | 6.4 |
| TP 3×ATR / SL 1,5×ATR | 54 | 33.3% | -1.32% | -7.61% | -71.2% | 0.83 | 11.5 |
| 50% di +3%, sisa ke target pola, SL −3% → impas | 54 | 42.6% | -0.32% | -3.40% | -17.5% | 0.83 | 2.8 |
| 50% di +5%, sisa ke target pola, SL −5% → impas | 54 | 37.0% | -1.04% | -5.39% | -56.0% | 0.69 | 4.5 |
| 50% di 1,5×ATR, sisa ke target pola, SL 1,5×ATR → impas | 54 | 35.2% | -2.11% | -7.52% | -113.9% | 0.71 | 10.4 |
| Tahan 7 hari (tanpa TP/SL) | 54 | 31.5% | -4.88% | -2.22% | -263.7% | 0.35 | 7.0 |
| Tahan 14 hari (tanpa TP/SL) | 54 | 40.7% | -5.44% | -3.77% | -293.7% | 0.47 | 14.0 |

Dengan filter pasar BTC (tidak short saat BTC tren naik):

| Filter | Sinyal | Menang | Rata-rata bersih | Median | Total | Profit factor | Hari |
|---|---|---|---|---|---|---|---|
| tanpa filter | 54 | 57.4% | -3.46% | +2.08% | -186.8% | 0.46 | 8.1 |
| filter pasar BTC | 26 | 73.1% | -2.52% | +2.08% | -65.5% | 0.43 | 6.9 |

## 5. Dibanding BTC (tahan 7 hari)

Rata-rata koin sinyal naik dalam 7 hari: -0.42% · BTC di periode yang sama: +1.35% · lebih baik dari BTC: 30.3% sinyal.

## 6. Siklus 4 stage (Stage 1 Dasar → 2 Naik → 3 Puncak → 4 Turun)

Periode 1 = 2024-10-29 – 2025-10-16 · Periode 2 = 2025-10-16 – 2026-10-03. Filter yang baik harus positif di **kedua** periode.

### 6a. Sinyal 🟢 radar + filter stage — Rencana bawaan (50% di +5%, sisa ke target, SL −12%)

Dengan filter bawaan (BTC tren naik + bukan meme):

| Filter stage | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| tanpa filter stage | 116 | 72.4% | +2.23% | 1.77 | 2.44 | +2.04% (80, menang 70.0%) | +2.63% (36, menang 77.8%) |
| Stage 1 atau 2 | 73 | 64.4% | -0.03% | 0.99 | -0.02 | -1.15% (48, menang 56.2%) | +2.12% (25, menang 80.0%) |
| Stage 2 saja | 28 | 71.4% | +0.53% | 1.19 | 0.32 | -0.55% (15, menang 60.0%) | +1.78% (13, menang 84.6%) |
| Stage 1 saja | 45 | 60.0% | -0.38% | 0.91 | -0.24 | -1.42% (33, menang 54.5%) | +2.50% (12, menang 75.0%) |
| bukan Stage 4 | 77 | 63.6% | -0.03% | 0.99 | -0.02 | -0.89% (51, menang 56.9%) | +1.67% (26, menang 76.9%) |
| bukan Stage 3/4 | 73 | 64.4% | -0.03% | 0.99 | -0.02 | -1.15% (48, menang 56.2%) | +2.12% (25, menang 80.0%) |
| fase ideal (akhir dasar, 1→2, awal/tengah naik) | 58 | 62.1% | -0.89% | 0.78 | -0.73 | -1.95% (39, menang 53.8%) | +1.28% (19, menang 78.9%) |
| checklist ≥4/6 | 49 | 67.3% | +0.26% | 1.07 | 0.18 | -1.93% (27, menang 55.6%) | +2.95% (22, menang 81.8%) |
| checklist ≥5/6 | 15 | 73.3% | +0.82% | 1.27 | 0.35 | -0.32% (10, menang 70.0%) | +3.10% (5, menang 80.0%) |
| volume tidak berlawanan | 88 | 73.9% | +1.87% | 1.68 | 1.92 | +1.85% (58, menang 72.4%) | +1.90% (30, menang 76.7%) |
| Stage 1/2 + checklist ≥4 | 43 | 69.8% | +0.07% | 1.02 | 0.05 | -2.04% (24, menang 58.3%) | +2.73% (19, menang 84.2%) |

Semua sinyal naik (tanpa filter pasar/meme):

| Filter stage | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| tanpa filter stage | 261 | 65.9% | +0.12% | 1.04 | 0.22 | +0.07% (160, menang 66.2%) | +0.21% (101, menang 65.3%) |
| Stage 1 atau 2 | 128 | 60.2% | -0.76% | 0.81 | -0.94 | -1.30% (90, menang 57.8%) | +0.52% (38, menang 65.8%) |
| Stage 2 saja | 35 | 68.6% | +0.06% | 1.02 | 0.04 | -0.61% (20, menang 65.0%) | +0.95% (15, menang 73.3%) |
| Stage 1 saja | 93 | 57.0% | -1.07% | 0.76 | -1.08 | -1.50% (70, menang 55.7%) | +0.24% (23, menang 60.9%) |
| bukan Stage 4 | 149 | 59.7% | -0.97% | 0.76 | -1.32 | -1.48% (104, menang 57.7%) | +0.20% (45, menang 64.4%) |
| bukan Stage 3/4 | 128 | 60.2% | -0.76% | 0.81 | -0.94 | -1.30% (90, menang 57.8%) | +0.52% (38, menang 65.8%) |
| fase ideal (akhir dasar, 1→2, awal/tengah naik) | 96 | 56.2% | -1.51% | 0.65 | -1.68 | -1.93% (69, menang 53.6%) | -0.46% (27, menang 63.0%) |
| checklist ≥4/6 | 91 | 62.6% | -1.00% | 0.73 | -1.1 | -2.74% (52, menang 53.8%) | +1.33% (39, menang 74.4%) |
| checklist ≥5/6 | 29 | 58.6% | -1.74% | 0.58 | -1.13 | -1.96% (18, menang 61.1%) | -1.38% (11, menang 54.5%) |
| volume tidak berlawanan | 205 | 64.4% | -0.44% | 0.88 | -0.74 | -0.71% (116, menang 63.8%) | -0.09% (89, menang 65.2%) |
| Stage 1/2 + checklist ≥4 | 66 | 60.6% | -1.37% | 0.65 | -1.31 | -2.58% (43, menang 55.8%) | +0.88% (23, menang 69.6%) |

### 6a. Sinyal 🟢 radar + filter stage — Target pola, SL −12%

Dengan filter bawaan (BTC tren naik + bukan meme):

| Filter stage | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| tanpa filter stage | 116 | 47.4% | +4.40% | 1.82 | 2.68 | +4.37% (80, menang 48.8%) | +4.49% (36, menang 44.4%) |
| Stage 1 atau 2 | 73 | 28.8% | -0.95% | 0.87 | -0.48 | -2.61% (48, menang 25.0%) | +2.24% (25, menang 36.0%) |
| Stage 2 saja | 28 | 25.0% | -2.30% | 0.71 | -0.73 | -3.66% (15, menang 20.0%) | -0.73% (13, menang 30.8%) |
| Stage 1 saja | 45 | 31.1% | -0.11% | 0.98 | -0.04 | -2.13% (33, menang 27.3%) | +5.46% (12, menang 41.7%) |
| bukan Stage 4 | 77 | 29.9% | -0.73% | 0.9 | -0.38 | -2.02% (51, menang 27.5%) | +1.78% (26, menang 34.6%) |
| bukan Stage 3/4 | 73 | 28.8% | -0.95% | 0.87 | -0.48 | -2.61% (48, menang 25.0%) | +2.24% (25, menang 36.0%) |
| fase ideal (akhir dasar, 1→2, awal/tengah naik) | 58 | 25.9% | -2.34% | 0.7 | -1.12 | -4.25% (39, menang 20.5%) | +1.59% (19, menang 36.8%) |
| checklist ≥4/6 | 49 | 24.5% | -1.09% | 0.86 | -0.43 | -4.74% (27, menang 14.8%) | +3.39% (22, menang 36.4%) |
| checklist ≥5/6 | 15 | 26.7% | -2.55% | 0.66 | -0.67 | -4.66% (10, menang 20.0%) | +1.69% (5, menang 40.0%) |
| volume tidak berlawanan | 88 | 43.2% | +2.18% | 1.38 | 1.25 | +1.95% (58, menang 44.8%) | +2.62% (30, menang 40.0%) |
| Stage 1/2 + checklist ≥4 | 43 | 20.9% | -2.12% | 0.73 | -0.8 | -5.90% (24, menang 12.5%) | +2.66% (19, menang 31.6%) |

Semua sinyal naik (tanpa filter pasar/meme):

| Filter stage | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| tanpa filter stage | 261 | 33.7% | -0.75% | 0.89 | -0.8 | -1.22% (160, menang 31.9%) | -0.01% (101, menang 36.6%) |
| Stage 1 atau 2 | 128 | 25.0% | -2.57% | 0.66 | -1.94 | -3.82% (90, menang 22.2%) | +0.41% (38, menang 31.6%) |
| Stage 2 saja | 35 | 20.0% | -3.75% | 0.54 | -1.45 | -5.64% (20, menang 15.0%) | -1.23% (15, menang 26.7%) |
| Stage 1 saja | 93 | 26.9% | -2.12% | 0.71 | -1.38 | -3.31% (70, menang 24.3%) | +1.47% (23, menang 34.8%) |
| bukan Stage 4 | 149 | 25.5% | -2.75% | 0.64 | -2.32 | -4.01% (104, menang 22.1%) | +0.16% (45, menang 33.3%) |
| bukan Stage 3/4 | 128 | 25.0% | -2.57% | 0.66 | -1.94 | -3.82% (90, menang 22.2%) | +0.41% (38, menang 31.6%) |
| fase ideal (akhir dasar, 1→2, awal/tengah naik) | 96 | 21.9% | -3.61% | 0.54 | -2.54 | -4.82% (69, menang 18.8%) | -0.52% (27, menang 29.6%) |
| checklist ≥4/6 | 91 | 20.9% | -3.25% | 0.58 | -2.09 | -6.84% (52, menang 9.6%) | +1.53% (39, menang 35.9%) |
| checklist ≥5/6 | 29 | 17.2% | -4.29% | 0.46 | -1.79 | -6.86% (18, menang 11.1%) | -0.10% (11, menang 27.3%) |
| volume tidak berlawanan | 205 | 30.2% | -2.09% | 0.71 | -2.13 | -3.21% (116, menang 25.9%) | -0.62% (89, menang 36.0%) |
| Stage 1/2 + checklist ≥4 | 66 | 13.6% | -4.67% | 0.45 | -2.61 | -7.61% (43, menang 7.0%) | +0.83% (23, menang 26.1%) |

### 6b. Sinyal 🟢 radar per stage (semua sinyal, rencana bawaan)

| Stage | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| Stage 1 | 93 | 57.0% | -1.07% | 0.76 | -1.08 | -1.50% (70, menang 55.7%) | +0.24% (23, menang 60.9%) |
| Stage 2 | 35 | 68.6% | +0.06% | 1.02 | 0.04 | -0.61% (20, menang 65.0%) | +0.95% (15, menang 73.3%) |
| Stage 3 | 21 | 57.1% | -2.29% | 0.49 | -1.29 | -2.66% (14, menang 57.1%) | -1.54% (7, menang 57.1%) |
| Stage 4 | 112 | 74.1% | +1.58% | 1.59 | 1.94 | +2.95% (56, menang 82.1%) | +0.21% (56, menang 66.1%) |

Per fase:

| Fase | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| 1 | 30 | 70.0% | +1.47% | 1.46 | 0.78 | +0.69% (20, menang 70.0%) | +3.01% (10, menang 70.0%) |
| 1-akhir | 63 | 50.8% | -2.27% | 0.55 | -2.01 | -2.37% (50, menang 50.0%) | -1.89% (13, menang 53.8%) |
| 1→2 | 19 | 63.2% | +0.21% | 1.07 | 0.1 | -0.90% (9, menang 55.6%) | +1.22% (10, menang 70.0%) |
| 2 | 1 | 100.0% | +2.08% | - | - | +2.08% (1, menang 100.0%) | - |
| 2-awal | 13 | 69.2% | -0.64% | 0.77 | -0.35 | -0.92% (9, menang 66.7%) | -0.00% (4, menang 75.0%) |
| 2-jenuh | 2 | 100.0% | +2.08% | - | - | +2.08% (1, menang 100.0%) | +2.08% (1, menang 100.0%) |
| 3 | 20 | 55.0% | -2.51% | 0.47 | -1.36 | -3.03% (13, menang 53.8%) | -1.54% (7, menang 57.1%) |
| 3-akhir | 1 | 100.0% | +2.08% | - | - | +2.08% (1, menang 100.0%) | - |
| 3→4 | 3 | 33.3% | -6.99% | 0.09 | -1.53 | -5.15% (2, menang 50.0%) | -10.68% (1, menang 0.0%) |
| 4 | 35 | 60.0% | -0.07% | 0.98 | -0.05 | -0.81% (5, menang 80.0%) | +0.05% (30, menang 56.7%) |
| 4-awal | 74 | 82.4% | +2.71% | 2.43 | 2.95 | +3.66% (49, menang 83.7%) | +0.85% (25, menang 80.0%) |

### 6c. Sinyal 🔴 radar (short) per stage

| Stage | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| Stage 1 | 31 | 61.3% | -0.19% | 0.96 | -0.09 | +6.21% (9, menang 88.9%) | -2.81% (22, menang 50.0%) |
| Stage 2 | 10 | 70.0% | -1.83% | 0.49 | -0.81 | +2.92% (4, menang 100.0%) | -4.99% (6, menang 50.0%) |
| Stage 3 | 3 | 33.3% | -7.55% | 0.08 | -1.57 | +2.08% (1, menang 100.0%) | -12.37% (2, menang 0.0%) |
| Stage 4 | 10 | 0.0% | -11.34% | 0.0 | -28.55 | -12.37% (2, menang 0.0%) | -11.08% (8, menang 0.0%) |

### 6d. Beli di hari acak menurut stage (pembanding, bukan meme)

Apakah stage saja sudah membedakan hasil? Rencana bawaan:

| Stage | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| Stage 1 | 5197 | 68.6% | -0.55% | 0.86 | -4.85 | -1.10% (2650, menang 66.5%) | +0.02% (2547, menang 70.7%) |
| Stage 2 | 1757 | 70.6% | -0.26% | 0.93 | -1.39 | -0.33% (1099, menang 70.4%) | -0.15% (658, menang 71.0%) |
| Stage 3 | 1182 | 62.4% | -1.66% | 0.63 | -6.92 | -1.72% (770, menang 63.1%) | -1.53% (412, menang 60.9%) |
| Stage 4 | 5897 | 71.8% | +0.02% | 1.01 | 0.24 | +0.96% (1982, menang 76.7%) | -0.45% (3915, menang 69.3%) |

Aturan *ikuti siklus* (jual saat tutup di bawah MA50 atau SL −12%, maks 180 hari):

| Stage | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| Stage 1 | 5197 | 27.9% | -1.11% | 0.8 | -2.84 | -2.94% (2650, menang 22.5%) | +0.80% (2547, menang 33.5%) |
| Stage 2 | 1757 | 25.0% | -1.13% | 0.85 | -1.2 | -0.19% (1099, menang 23.9%) | -2.71% (658, menang 26.9%) |
| Stage 3 | 1182 | 30.2% | -2.11% | 0.55 | -6.13 | -3.09% (770, menang 28.2%) | -0.29% (412, menang 34.0%) |
| Stage 4 | 5897 | 39.7% | +0.09% | 1.03 | 0.42 | +1.33% (1982, menang 42.9%) | -0.53% (3915, menang 38.2%) |

### 6e. Strategi siklus murni (tanpa skor radar, bukan meme)

| Strategi · pasar · aturan jual | Sinyal | Menang | Rata-rata bersih | Profit factor | t | Periode 1 | Periode 2 |
|---|---|---|---|---|---|---|---|
| Tembus atap dasar (Stage 1→2) + volume ≥1,5× · semua kondisi · rencana bawaan | 185 | 75.1% | +0.96% | 1.32 | 1.47 | +1.75% (86, menang 77.9%) | +0.27% (99, menang 72.7%) |
| Tembus atap dasar (Stage 1→2) + volume ≥1,5× · semua kondisi · ikuti siklus (MA50) | 185 | 36.2% | +8.97% | 2.26 | 1.81 | +15.95% (86, menang 39.5%) | +2.91% (99, menang 33.3%) |
| Tembus atap dasar (Stage 1→2) + volume ≥1,5× · BTC tidak tren turun · rencana bawaan | 179 | 74.3% | +0.92% | 1.29 | 1.36 | +1.73% (82, menang 76.8%) | +0.24% (97, menang 72.2%) |
| Tembus atap dasar (Stage 1→2) + volume ≥1,5× · BTC tidak tren turun · ikuti siklus (MA50) | 179 | 36.9% | +5.10% | 1.72 | 2.01 | +7.33% (82, menang 40.2%) | +3.22% (97, menang 34.0%) |
| Tembus atap dasar (Stage 1→2) + volume ≥1,5× · BTC tren naik · rencana bawaan | 166 | 75.3% | +1.12% | 1.37 | 1.6 | +1.75% (72, menang 76.4%) | +0.64% (94, menang 74.5%) |
| Tembus atap dasar (Stage 1→2) + volume ≥1,5× · BTC tren naik · ikuti siklus (MA50) | 166 | 38.6% | +5.63% | 1.82 | 2.11 | +8.13% (72, menang 43.1%) | +3.72% (94, menang 35.1%) |
| Hari pertama Stage 2 terkonfirmasi · semua kondisi · rencana bawaan | 329 | 79.0% | +1.45% | 1.57 | 3.58 | +1.16% (179, menang 78.2%) | +1.80% (150, menang 80.0%) |
| Hari pertama Stage 2 terkonfirmasi · semua kondisi · ikuti siklus (MA50) | 329 | 30.7% | +3.85% | 1.56 | 1.38 | +4.72% (179, menang 26.8%) | +2.83% (150, menang 35.3%) |
| Hari pertama Stage 2 terkonfirmasi · BTC tidak tren turun · rencana bawaan | 293 | 78.8% | +1.44% | 1.56 | 3.33 | +1.15% (170, menang 78.2%) | +1.84% (123, menang 79.7%) |
| Hari pertama Stage 2 terkonfirmasi · BTC tidak tren turun · ikuti siklus (MA50) | 293 | 31.1% | +1.95% | 1.29 | 1.27 | +0.54% (170, menang 26.5%) | +3.91% (123, menang 37.4%) |
| Hari pertama Stage 2 terkonfirmasi · BTC tren naik · rencana bawaan | 260 | 80.8% | +1.85% | 1.8 | 4.16 | +1.80% (141, menang 81.6%) | +1.91% (119, menang 79.8%) |
| Hari pertama Stage 2 terkonfirmasi · BTC tren naik · ikuti siklus (MA50) | 260 | 34.6% | +3.01% | 1.46 | 1.78 | +1.90% (141, menang 31.2%) | +4.32% (119, menang 38.7%) |
| Pullback Stage 2 ke zona Fibonacci 0,382–0,618 + candle hijau · semua kondisi · rencana bawaan | 243 | 79.8% | +0.74% | 1.31 | 1.47 | +0.27% (160, menang 83.1%) | +1.66% (83, menang 73.5%) |
| Pullback Stage 2 ke zona Fibonacci 0,382–0,618 + candle hijau · semua kondisi · ikuti siklus (MA50) | 243 | 35.0% | +0.73% | 1.16 | 0.64 | -0.66% (160, menang 32.5%) | +3.41% (83, menang 39.8%) |
| Pullback Stage 2 ke zona Fibonacci 0,382–0,618 + candle hijau · BTC tidak tren turun · rencana bawaan | 189 | 81.5% | +1.31% | 1.57 | 2.2 | +0.01% (138, menang 81.2%) | +4.83% (51, menang 82.4%) |
| Pullback Stage 2 ke zona Fibonacci 0,382–0,618 + candle hijau · BTC tidak tren turun · ikuti siklus (MA50) | 189 | 36.5% | +1.56% | 1.33 | 1.1 | -0.74% (138, menang 31.2%) | +7.79% (51, menang 51.0%) |
| Pullback Stage 2 ke zona Fibonacci 0,382–0,618 + candle hijau · BTC tren naik · rencana bawaan | 150 | 81.3% | +1.54% | 1.67 | 2.24 | -0.13% (105, menang 80.0%) | +5.41% (45, menang 84.4%) |
| Pullback Stage 2 ke zona Fibonacci 0,382–0,618 + candle hijau · BTC tren naik · ikuti siklus (MA50) | 150 | 38.7% | +2.48% | 1.53 | 1.44 | -0.58% (105, menang 31.4%) | +9.62% (45, menang 55.6%) |
| Beli hari acak (pembanding) · semua kondisi · rencana bawaan | 14033 | 69.7% | -0.36% | 0.9 | -5.37 | -0.41% (6501, menang 69.9%) | -0.32% (7532, menang 69.5%) |
| Beli hari acak (pembanding) · semua kondisi · ikuti siklus (MA50) | 14033 | 32.7% | -0.69% | 0.86 | -3.26 | -1.19% (6501, menang 29.6%) | -0.26% (7532, menang 35.4%) |
| Beli hari acak (pembanding) · BTC tidak tren turun · rencana bawaan | 8842 | 69.0% | -0.47% | 0.87 | -5.43 | -0.74% (5031, menang 68.0%) | -0.11% (3811, menang 70.3%) |
| Beli hari acak (pembanding) · BTC tidak tren turun · ikuti siklus (MA50) | 8842 | 27.6% | -0.83% | 0.85 | -3.01 | -1.60% (5031, menang 25.0%) | +0.20% (3811, menang 31.2%) |
| Beli hari acak (pembanding) · BTC tren naik · rencana bawaan | 6619 | 72.8% | +0.18% | 1.06 | 1.9 | -0.29% (3995, menang 70.8%) | +0.90% (2624, menang 75.8%) |
| Beli hari acak (pembanding) · BTC tren naik · ikuti siklus (MA50) | 6619 | 28.4% | -0.81% | 0.86 | -3.11 | -2.17% (3995, menang 24.7%) | +1.27% (2624, menang 34.2%) |

**Strategi siklus murni yang positif di kedua periode (≥15 sinyal per periode):** Tembus atap dasar (Stage 1→2) + volume ≥1,5× · BTC tren naik · ikuti siklus (MA50) → +5.63% (166 sinyal); Tembus atap dasar (Stage 1→2) + volume ≥1,5× · BTC tidak tren turun · ikuti siklus (MA50) → +5.10% (179 sinyal); Tembus atap dasar (Stage 1→2) + volume ≥1,5× · semua kondisi · ikuti siklus (MA50) → +8.97% (185 sinyal); Hari pertama Stage 2 terkonfirmasi · semua kondisi · ikuti siklus (MA50) → +3.85% (329 sinyal); Hari pertama Stage 2 terkonfirmasi · BTC tren naik · ikuti siklus (MA50) → +3.01% (260 sinyal)


## Keterbatasan

- Data per jam tidak dipakai: zona akumulasi & porsi beli agresif dihitung dari candle harian; jejak whale 1 jam tidak ikut.
- Daftar koin = top 200 saat ini (survivorship bias) → hasil cenderung sedikit terlalu bagus.
- Masuk di harga penutupan hari sinyal; bila SL & TP tersentuh di candle yang sama dianggap SL dulu.
- Hasil masa lalu tidak menjamin hasil masa depan.
