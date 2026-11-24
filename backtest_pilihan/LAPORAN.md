# 📌 Uji "Pilihan Harian" — minimal 1 koin per hari

Dibuat 24 Nov 2026 10:17 WIB · 128 koin · 178,002 analisa harian · 2020-09-17 s/d 2026-10-24 · latih sebelum 2023-01-01, uji 2023-01-01 dst. · meme coin tidak ikut

## Putusan

- **Beli (saat BTC tren naik): ❌ tidak layak → 👀 Koin pantauan tanpa ajakan masuk** — aturan L1 (Skor beli radar tertinggi); di luar sampel -0.19% · menang 70.6% (717) · acak -0.16% / 70.7%
- **Jual dulu (saat BTC tidak tren naik): ✅ LAYAK → ⚪ Pilihan harian dengan rencana** — aturan S2 (Skor jual tertinggi di Stage 4); di luar sampel +0.44% · menang 75.3% (640) · acak -0.06% / 72.6%

Syarat LAYAK (ditetapkan di muka): rata-rata bersih di luar sampel > 0 dan lebih tinggi dari koin acak di hari yang sama.

### Cara dipasang di radar (diputuskan setelah hasil keluar)

Pilihan hanya dikirim pada hari tanpa sinyal. Pada hari-hari itu hasilnya:
- Beli (L1): -0.65% · menang 67.6% (398) · acak -0.60% / 68.5%
- Jual dulu (S2): +0.04% · menang 73.1% (539) · acak -0.28% / 71.3%

Bila ikut diperdagangkan, portofolio justru turun (lihat tabel portofolio). Karena itu radar memakai bawaan **`pilihan_harian: pantau`**: satu koin per hari dikirim sebagai 👀 pantauan beserta syarat yang membuatnya jadi sinyal sungguhan, tanpa ajakan masuk. `rencana` (dengan TP/SL) bisa dipilih sendiri di config.yaml.

## Semua aturan

Isi sel: rata-rata bersih per pilihan · tingkat menang (jumlah) · pembanding koin acak di hari yang sama.

| Aturan | Arah | Latih (s/d 2022) | Uji (2023 dst.) |
|---|---|---|---|
| L1 Skor beli radar tertinggi | beli | +1.13% · menang 76.8% (328) · acak +0.58% / 74.7% | -0.19% · menang 70.6% (717) · acak -0.16% / 70.7% |
| L2 Skor beli tertinggi di Stage 2 | beli | +0.99% · menang 76.1% (285) · acak +0.55% / 74.4% | -0.22% · menang 69.8% (605) · acak -0.45% / 69.3% |
| L3 Paling kuat vs BTC 30 hari (Stage 2) | beli | +0.21% · menang 71.2% (285) · acak +0.55% / 74.4% | +0.11% · menang 71.4% (605) · acak -0.44% / 69.4% |
| S1 Skor jual radar tertinggi | jual dulu | +0.14% · menang 73.1% (495) · acak +0.09% / 72.5% | +0.29% · menang 74.3% (676) · acak -0.09% / 72.4% |
| S2 Skor jual tertinggi di Stage 4 | jual dulu | +0.16% · menang 73.0% (393) · acak -0.01% / 72.1% | +0.44% · menang 75.3% (640) · acak -0.06% / 72.6% |
| S3 Paling lemah vs BTC 30 hari (Stage 4) | jual dulu | -0.24% · menang 71.0% (396) · acak +0.00% / 72.2% | +0.07% · menang 73.0% (641) · acak -0.05% / 72.6% |

### Per tahun (aturan terpilih)

| Tahun | L1 | S2 |
|---|---|---|
| 2020 | +1.19% · menang 75.7% (74) · acak +1.02% / 77.1% | +0.40% · menang 84.6% (13) · acak -1.36% / 66.2% |
| 2021 | +1.79% · menang 80.6% (206) · acak +0.96% / 76.6% | -0.17% · menang 70.3% (74) · acak -0.36% / 69.7% |
| 2022 | -1.78% · menang 62.5% (48) · acak -1.75% / 62.5% | +0.08% · menang 72.6% (317) · acak +0.02% / 72.4% |
| 2023 | +0.19% · menang 73.7% (232) · acak +0.88% / 76.6% | +0.92% · menang 78.9% (133) · acak +0.32% / 74.7% |
| 2024 | -0.54% · menang 68.5% (200) · acak -0.98% / 66.1% | -0.08% · menang 71.3% (136) · acak -0.73% / 69.3% |
| 2025 | -1.50% · menang 62.4% (149) · acak -1.21% / 65.3% | +0.76% · menang 78.1% (210) · acak +0.13% / 73.1% |
| 2026 | +1.12% · menang 77.2% (136) · acak +0.41% / 73.2% | +0.07% · menang 72.0% (161) · acak -0.05% / 72.8% |

## Seberapa sering radar diam? (2023-01-01 dst.)

Dari 1383 hari, 410 hari ada sinyal 🟢/🟩/🔻 dan **973 hari tanpa sinyal sama sekali** (per tahun: 2023: 223, 2024: 259, 2025: 284, 2026: 207).

Pilihan harian pada hari tanpa sinyal: -0.25% · menang 70.8% (937) · acak -0.41% / 70.1%

- Beli: -0.65% · menang 67.6% (398) · acak -0.60% / 68.5%
- Jual dulu: +0.04% · menang 73.1% (539) · acak -0.28% / 71.3%

| Tahun | Pilihan pada hari tanpa sinyal |
|---|---|
| 2023 | +0.68% · menang 76.2% (223) · acak +0.87% / 76.9% |
| 2024 | -1.15% · menang 65.9% (229) · acak -1.50% / 64.5% |
| 2025 | -0.50% · menang 69.8% (278) · acak -0.73% / 68.5% |
| 2026 | +0.06% · menang 71.5% (207) · acak -0.18% / 71.2% |

## Portofolio di luar sampel (maks 5 posisi, median 100 urutan acak)

| Susunan | Hasil |
|---|---|
| Sistem sekarang | +183.9% · maks turun -23.9% · Sharpe 1.04 · menang 76.1% · 442 transaksi |
| Sistem sekarang + pilihan harian | +2.4% · maks turun -50.5% · Sharpe 0.11 · menang 73.0% · 960 transaksi |
| Sistem sekarang + pilihan jual dulu saja | +118.5% · maks turun -29.7% · Sharpe 0.81 · menang 74.4% · 754 transaksi |
| Pilihan harian saja (hari tanpa sinyal) | -42.7% · maks turun -60.4% · Sharpe -0.47 · menang 71.3% · 746 transaksi |

## Catatan jujur

- Pilihan harian dibuat supaya radar tidak diam; ia BUKAN sinyal yang lolos semua filter. Hari tanpa sinyal biasanya hari ketika pasar sedang tidak mendukung.
- Data koin = koin top CMC saat ini (yang sudah mati tidak ikut) — hasil beli cenderung terlalu bagus, hasil jual dulu terlalu jelek.
- Aturan & syarat ditulis sebelum tahap model dijalankan. Statistik masa lalu, bukan jaminan. Bukan ajakan beli/jual.
