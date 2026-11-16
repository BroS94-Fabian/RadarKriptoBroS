# 🕐 Uji "Harian Berjalan" — sinyal harian yang dihitung ulang tiap jam

Dibuat 16 Nov 2026 11:32 WIB · 12 koin · 31,140 analisa (tiap koin × tiap jam, ±0.0 jam mesin) · catatan 2026-07-01T00:00 s/d 2026-10-12T15:00 UTC · meme coin tidak ikut

## Putusan

**❌ Tidak dipasang — dihitung tiap jam tidak lebih baik dari sekali sehari.**

- 🟩 & 🔻 dicek tiap jam: -4.5% · maks turun -5.7% · Sharpe -0.67 · menang 62.5% · 8 transaksi
- Hanya dicek 07.00 WIB (sistem sekarang): -2.7% · maks turun -3.9% · Sharpe -0.5 · menang 75.0% · 8 transaksi
- Syarat (ditetapkan di muka): total ≥ pembanding, Sharpe ≥ pembanding, maks turun tidak lebih buruk dari pembanding − 5 poin.

## Yang diuji

Mesin radar harian dijalankan apa adanya di setiap jam pada candle 24 jam berjalan (24 jam terakhir = satu candle, dst.). Tepat jam 07.00 WIB candle berjalan sama dengan candle harian biasa, jadi sistem sekarang adalah bagian darinya. Kedua sistem memakai aturan yang sama: gerbang model pasar, jeda 10 hari per koin & jenis sinyal, masuk di penutupan candle 1 jam berikutnya, rencana jual TP1 5% / SL 12% / maks 30 hari yang disimulasikan pada candle 1 jam, biaya & pajak dipotong.

Cek mesin: dari 4 sinyal radar uji harian, 4 ditemukan mesin berjalan tepat di jam 00.00 UTC (4 dengan skor yang sama persis). Sinyal stage uji harian yang juga muncul di mesin berjalan jam 00.00 UTC: 🟩 13 dari 13, 🔻 2 dari 2 (uji harian menghitung stage dari seluruh riwayat; mesin berjalan & radar live dari 400 candle terakhir).

## Uji portofolio di luar sampel (2023-01-01 s/d 2026-10-12)

Maks 5 posisi, modal dibagi rata, median dari 100 urutan acak (dalam kurung = terendah…tertinggi).

| Sistem | Total | Per tahun | Maks turun | Sharpe | Transaksi | Menang | Rata-rata/transaksi |
|---|---|---|---|---|---|---|---|
| Hanya 07.00 WIB (sistem sekarang) | **-2.7%** (-3…-3) | 2023: +0% · 2024: +0% · 2025: +0% · 2026: -3% | -3.9% | -0.5 | 8 dari 8 | 75.0% | -1.66% |
| 🟩 & 🔻 tiap jam | **-4.5%** (-4…-4) | 2023: +0% · 2024: +0% · 2025: +0% · 2026: -4% | -5.7% | -0.67 | 8 dari 8 | 62.5% | -2.85% |
| Semua tiap jam (termasuk 🟢) | **+4.7%** (+5…+5) | 2023: +0% · 2024: +0% · 2025: +0% · 2026: +5% | -5.7% | 0.4 | 15 dari 17 | 66.7% | +1.58% |
| (acuan) angka uji harian yang sudah terbit — candle harian, tanpa jeda masuk | **+183.9%** (+120…+275) | 2023: +24% · 2024: +38% · 2025: +14% · 2026: +38% | -23.9% | 1.06 | 442 dari 843 | 76.1% | +1.32% |
| (pembanding) hanya 07.00 WIB, masuk tanpa jeda 1 jam | **-4.5%** (-4…-4) | 2023: +0% · 2024: +0% · 2025: +0% · 2026: -4% | -5.8% | -0.66 | 8 dari 8 | 62.5% | -2.82% |
| (pembanding) 🟩 & 🔻 tiap jam, masuk tanpa jeda 1 jam | **-3.5%** (-4…-4) | 2023: +0% · 2024: +0% · 2025: +0% · 2026: -4% | -5.7% | -0.7 | 8 dari 8 | 62.5% | -2.21% |

Berpasangan (100 urutan acak yang sama): '🟩 & 🔻 tiap jam' lebih tinggi totalnya dari 'hanya 07.00 WIB' di 0 urutan, Sharpe lebih tinggi di 0, penurunan maksimum lebih kecil di 0; selisih total (median) -1.8 poin. 'Semua tiap jam': total lebih tinggi di 100, Sharpe di 100.

### Hasil per jenis sinyal

Isi sel: rata-rata bersih per transaksi · tingkat menang (jumlah sinyal).

| Jenis | Di luar sampel: hanya 07.00 WIB | Di luar sampel: tiap jam | Seluruh data 2020–2026: hanya 07.00 WIB | Seluruh data: tiap jam |
|---|---|---|---|---|
| 🟢 Radar naik | - | +5.15% · menang 66.7% (9) | - | +5.15% · menang 66.7% (9) |
| 🟩 Awal Stage 2 | -0.33% · menang 83.3% (6) | -1.91% · menang 66.7% (6) | -0.33% · menang 83.3% (6) | -1.91% · menang 66.7% (6) |
| 🔻 Jual dulu (pantulan Stage 4) | -5.65% · menang 50.0% (2) | -5.69% · menang 50.0% (2) | -5.65% · menang 50.0% (2) | -5.69% · menang 50.0% (2) |

(Untuk 🟢 radar kolom 'tiap jam' berasal dari sistem 'semua tiap jam'; di sistem yang diputuskan 🟢 tetap seperti sekarang.)

### Kapan sinyal 🟩 & 🔻 muncul bila dicek tiap jam (seluruh data)

Tepat jam 07.00 WIB: 25.0% — sisanya tersebar di jam lain.

| Jam WIB | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sinyal | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 2 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |

| Jenis | Sinyal 07.00 WIB | Sudah tertangkap versi tiap jam (≤10 hari sebelumnya) | Lebih awal | Median lebih awal |
|---|---|---|---|---|
| 🟩 Awal Stage 2 | 6 | 6 | 5 | 20.0 jam |
| 🔻 Jual dulu (pantulan Stage 4) | 2 | 2 | 1 | 77.0 jam |

## Catatan jujur

- 'Hanya 07.00 WIB' di sini dihitung ulang dengan cara yang sama dengan versi tiap jam (simulasi pada candle 1 jam, masuk dengan jeda 1 jam, jeda 10 hari setelah gerbang, stage dari 400 candle terakhir seperti radar live), jadi angkanya tidak sama persis dengan angka uji harian yang sudah terbit — baris '(acuan)' di tabel menunjukkan selisihnya.
- Versi tiap jam melihat lebih banyak kesempatan (24 kali sehari), jadi sinyalnya sedikit lebih banyak dan bisa lebih awal maupun lebih lambat daripada versi 07.00 WIB.
- Daftar koin = koin top CMC saat ini (yang sudah mati tidak ikut); untung-rugi dicatat saat posisi ditutup.
- Aturan uji ditulis sebelum data ditarik. Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual.
