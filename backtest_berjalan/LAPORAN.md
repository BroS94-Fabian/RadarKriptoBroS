# 🕐 Uji "Harian Berjalan" — sinyal harian yang dihitung ulang tiap jam

Dibuat 16 Nov 2026 12:26 WIB · 128 koin · 4,245,888 analisa (tiap koin × tiap jam, ±3.6 jam mesin) · catatan 2020-09-18T01:00 s/d 2026-10-17T02:00 UTC · meme coin tidak ikut

## Putusan

**❌ Tidak dipasang — dihitung tiap jam tidak lebih baik dari sekali sehari.**

- 🟩 & 🔻 dicek tiap jam: +36.1% · maks turun -38.0% · Sharpe 0.33 · menang 73.5% · 540 transaksi
- Hanya dicek 07.00 WIB (sistem sekarang): +156.8% · maks turun -20.2% · Sharpe 0.95 · menang 76.5% · 463 transaksi
- Syarat (ditetapkan di muka): total ≥ pembanding, Sharpe ≥ pembanding, maks turun tidak lebih buruk dari pembanding − 5 poin.

## Yang diuji

Mesin radar harian dijalankan apa adanya di setiap jam pada candle 24 jam berjalan (24 jam terakhir = satu candle, dst.). Tepat jam 07.00 WIB candle berjalan sama dengan candle harian biasa, jadi sistem sekarang adalah bagian darinya. Kedua sistem memakai aturan yang sama: gerbang model pasar, jeda 10 hari per koin & jenis sinyal, masuk di penutupan candle 1 jam berikutnya, rencana jual TP1 5% / SL 12% / maks 30 hari yang disimulasikan pada candle 1 jam, biaya & pajak dipotong.

Cek mesin: dari 744 sinyal radar uji harian, 743 ditemukan mesin berjalan tepat di jam 00.00 UTC (743 dengan skor yang sama persis). Sinyal stage uji harian yang juga muncul di mesin berjalan jam 00.00 UTC: 🟩 908 dari 908, 🔻 424 dari 424 (uji harian menghitung stage dari seluruh riwayat; mesin berjalan & radar live dari 400 candle terakhir).

## Uji portofolio di luar sampel (2023-01-01 s/d 2026-10-14)

Maks 5 posisi, modal dibagi rata, median dari 100 urutan acak (dalam kurung = terendah…tertinggi).

| Sistem | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |
|---|---|---|---|---|---|---|---|
| Hanya 07.00 WIB (sistem sekarang) | **+156.8%** (+100…+232) | 2023: +26% · 2024: +42% · 2025: +18% · 2026: +20% | -20.2% | 0.95 | 463 dari 874 | 76.5% | +1.17% |
| 🟩 & 🔻 tiap jam | **+36.1%** (+14…+60) | 2023: +12% · 2024: +27% · 2025: -24% · 2026: +19% | -38.0% | 0.33 | 540 dari 1067 | 73.5% | +0.43% |
| Semua tiap jam (termasuk 🟢) | **+27.1%** (+6…+52) | 2023: +14% · 2024: +17% · 2025: -22% · 2026: +23% | -40.3% | 0.24 | 641 dari 1953 | 71.8% | +0.33% |
| (acuan) angka uji harian yang sudah terbit — candle harian, tanpa jeda masuk | **+183.9%** (+120…+275) | 2023: +24% · 2024: +38% · 2025: +14% · 2026: +38% | -23.9% | 1.06 | 442 dari 843 | 76.1% | +1.32% |
| (pembanding) hanya 07.00 WIB, masuk tanpa jeda 1 jam | **+168.4%** (+94…+231) | 2023: +24% · 2024: +41% · 2025: +12% · 2026: +32% | -21.2% | 0.98 | 470 dari 874 | 76.5% | +1.19% |
| (pembanding) 🟩 & 🔻 tiap jam, masuk tanpa jeda 1 jam | **+28.2%** (+4…+47) | 2023: +15% · 2024: +28% · 2025: -29% · 2026: +22% | -40.4% | 0.27 | 553 dari 1067 | 72.9% | +0.37% |

Berpasangan (100 urutan acak yang sama): '🟩 & 🔻 tiap jam' lebih tinggi totalnya dari 'hanya 07.00 WIB' di 0 urutan, Sharpe lebih tinggi di 0, penurunan maksimum lebih kecil di 0; selisih total (median) -121.0 poin. 'Semua tiap jam': total lebih tinggi di 0, Sharpe di 0.

### Hasil per jenis sinyal

Isi sel: rata-rata bersih per transaksi · tingkat menang (jumlah sinyal).

| Jenis | Di luar sampel: hanya 07.00 WIB | Di luar sampel: tiap jam | Seluruh data 2020–2026: hanya 07.00 WIB | Seluruh data: tiap jam |
|---|---|---|---|---|
| 🟢 Radar naik | +1.34% · menang 70.5% (234) | +0.85% · menang 67.9% (1120) | +1.61% · menang 72.9% (262) | +0.90% · menang 68.6% (1263) |
| 🟩 Awal Stage 2 | +1.30% · menang 79.2% (424) | +0.59% · menang 75.3% (494) | +1.78% · menang 81.4% (442) | +0.74% · menang 75.7% (572) |
| 🔻 Jual dulu (pantulan Stage 4) | +2.01% · menang 85.2% (216) | +0.48% · menang 77.8% (338) | +2.24% · menang 86.0% (235) | +0.68% · menang 78.2% (377) |

(Untuk 🟢 radar kolom 'tiap jam' berasal dari sistem 'semua tiap jam'; di sistem yang diputuskan 🟢 tetap seperti sekarang.)

### Kapan sinyal 🟩 & 🔻 muncul bila dicek tiap jam (seluruh data)

Tepat jam 07.00 WIB: 12.2% — sisanya tersebar di jam lain.

| Jam WIB | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sinyal | 33 | 34 | 32 | 27 | 34 | 41 | 27 | 116 | 63 | 43 | 42 | 39 | 28 | 38 | 39 | 34 | 36 | 26 | 25 | 26 | 38 | 45 | 37 | 46 |

| Jenis | Sinyal 07.00 WIB | Sudah tertangkap versi tiap jam (≤10 hari sebelumnya) | Lebih awal | Median lebih awal |
|---|---|---|---|---|
| 🟩 Awal Stage 2 | 442 | 442 | 390 | 17.0 jam |
| 🔻 Jual dulu (pantulan Stage 4) | 235 | 235 | 171 | 28.0 jam |

## Catatan jujur

- 'Hanya 07.00 WIB' di sini dihitung ulang dengan cara yang sama dengan versi tiap jam (simulasi pada candle 1 jam, masuk dengan jeda 1 jam, jeda 10 hari setelah gerbang, stage dari 400 candle terakhir seperti radar live), jadi angkanya tidak sama persis dengan angka uji harian yang sudah terbit — baris '(acuan)' di tabel menunjukkan selisihnya.
- Versi tiap jam melihat lebih banyak kesempatan (24 kali sehari), jadi sinyalnya sedikit lebih banyak dan bisa lebih awal maupun lebih lambat daripada versi 07.00 WIB.
- Daftar koin = koin top CMC saat ini (yang sudah mati tidak ikut); untung-rugi dicatat saat posisi ditutup.
- Aturan uji ditulis sebelum data ditarik. Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual.
