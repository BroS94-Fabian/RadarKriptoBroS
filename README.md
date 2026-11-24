# 📡 Radar Kripto — Analisa Teknikal Top 200 CoinMarketCap (gratis & otomatis)

Tiap jam radar ini menganalisa koin **200 terbesar di CoinMarketCap** (data candle dari Binance, cadangan OKX), lalu:

- mengirim **alert + grafik ke Telegram** untuk koin yang masuk kategori 🟢 atau 🔴,
- memperbarui **dashboard web** berisi data seluruh koin (GitHub Pages, gratis).

| Kategori | Syarat |
|---|---|
| 🟢 **Potensi naik** | Sedang **diakumulasi** (OBV naik / CMF positif / beli agresif), harga **masih di bawah** (di dalam/di bawah zona akumulasi, belum naik >20% dalam 7 hari), dan skor naik ≥ 50 serta unggul ≥ 15 dari skor turun |
| 🔴 **Potensi turun** | Skor turun ≥ 50 dan unggul ≥ 15: distribusi, pola bearish, momentum melemah |
| 🟡 **Pantau** | Hampir memenuhi syarat (skor ≥ 40) — hanya tampil di dashboard |

### Analisa yang dipakai
1. **Trend line** — garis support & resistance dari titik balik harga; uptrend/downtrend/sideways, breakout garis tren.
2. **Moving Average** — MA20, MA50, MA200, golden cross / death cross, posisi harga terhadap MA.
3. **Bollinger Bands** (20,2) — posisi %B, *squeeze* (volatilitas menyempit → siap bergerak besar).
4. **Candlestick** — Hammer, Inverted Hammer, Shooting Star, Hanging Man, Bullish/Bearish Engulfing, Piercing Line, Dark Cloud Cover, Morning/Evening Star, Three White Soldiers, Three Black Crows, Doji.
5. **Chart pattern** (sesuai gambar) — Double/Triple Top & Bottom, Head and Shoulders & Inverse, Rising/Falling Wedge, Ascending/Descending/Symmetrical Triangle, Bull Flag (*Downward Flag*), Bear Flag (*Upward Flag*), Bullish/Bearish Pennant, Cup and Handle.
6. **MACD** (12,26,9) — cross naik/turun, kekuatan histogram.
7. **RSI** (14) — overbought >70, oversold <30, divergensi.
8. **Stochastic** (14,3,3) — cross di area <20 / >80.
9. **Elliott Wave** — perkiraan otomatis posisi gelombang (akhir gelombang 2, gelombang 3, impuls 5 selesai, koreksi A-B-C).
10. **Akumulasi volume** — OBV, CMF, porsi beli agresif, lonjakan volume, profil volume (zona akumulasi & POC).
11. **Siklus 4 stage** (Weinstein / *Super Trader Analysis*) — tiap koin dipetakan ke 🟦 Stage 1 Dasar, 🟩 Stage 2 Naik,
    🟨 Stage 3 Puncak, atau 🟥 Stage 4 Turun memakai MA200 harian (±30 minggu): arah MA, posisi harga, posisi di kisaran
    1 tahun, low/high baru. Fase: akhir dasar, *baru tembus dari dasar (1→2)*, awal naik, jenuh, rawan jebol, *baru jebol (3→4)*.
    Ditambah **checklist** Siklus → Tren → Support & Resistance → Pola → Candlestick → Volume, **volume konfirmasi/anomali**
    (*bell ringing*), dan **zona pullback Fibonacci 0,382–0,618** untuk koin Stage 2. Lihat tab 🔄 Siklus di dashboard.

### Cara menghitung persentase naik/turun
| Pola | Target | Batal jika |
|---|---|---|
| Double/Triple Bottom | neckline + (neckline − dasar) | tembus di bawah dasar |
| Double/Triple Top | neckline − (puncak − neckline) | tembus di atas puncak |
| Inverse Head and Shoulders | neckline + (neckline − kepala) | di bawah bahu kanan |
| Head and Shoulders | neckline − (kepala − neckline) | di atas bahu kanan |
| Ascending / Descending Triangle | atap + tinggi segitiga / lantai − tinggi segitiga | jebol sisi lawan |
| Symmetrical Triangle | titik breakout ± tinggi segitiga | jebol sisi lawan |
| Falling / Rising Wedge | kembali ke awal baji | jebol sisi lawan |
| Flag / Pennant | titik breakout ± panjang tiang | jebol sisi lawan |
| Cup and Handle | bibir cangkir + kedalaman cangkir | di bawah dasar gagang |

Kalau tidak ada pola: dipakai target Elliott Wave, atau resistance/support terdekat (garis tren, Bollinger, MA, zona akumulasi, high/low terakhir).
**Rasio** = potensi ÷ jarak ke level batal.

---

## Upgrade dari versi sebelumnya (repo yang sudah ada)
1. **Upload file baru** — di halaman repo: **Add file → Upload files**, seret 6 file ini sekaligus:
   `scanner.py`, `analisa.py`, `grafik.py`, `dashboard.html`, `config.yaml`, `README.md` → **Commit changes**.
   (File dengan nama sama otomatis diganti.)
2. **Ganti jadwal** — buka `.github/workflows/radar.yml` → ikon pensil ✏️ → hapus semua isinya → tempel isi `radar.yml` yang baru → **Commit changes**.
3. **API key CoinMarketCap (gratis)** — daftar di **pro.coinmarketcap.com** → paket *Basic (Free)* → salin *API Key*.
   Di GitHub: **Settings → Secrets and variables → Actions → New repository secret** → Name `CMC_API_KEY` → isi key → **Add secret**.
   > Tanpa key, radar tetap jalan memakai daftar top 200 dari CoinGecko (hasilnya hampir sama).
4. **Aktifkan dashboard** — **Settings → Pages** → bagian *Build and deployment* → *Source*: pilih **GitHub Actions**.
5. **Jalankan** — **Actions → Radar Whale Kripto → Run workflow → normal**.
   Setelah selesai, dashboard ada di: `https://<username-kecil>.github.io/<nama-repo>/`
   (contoh: `https://bros94-fabian.github.io/RadarKriptoBroS/`). Link juga muncul di pesan Telegram.

## Setup dari nol
1. Buat bot Telegram lewat **@BotFather** (`/newbot`), simpan token. Kirim pesan ke bot, lalu buka
   `https://api.telegram.org/bot<TOKEN>/getUpdates` untuk melihat **Chat ID**.
2. Buat repo **Public** di GitHub, upload semua file, dan buat `.github/workflows/radar.yml`.
3. Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `CMC_API_KEY`.
4. **Settings → Actions → General → Workflow permissions → Read and write permissions**.
5. **Settings → Pages → Source: GitHub Actions**.
6. **Actions → Run workflow**: `tes-telegram` → `demo` (contoh tampilan) → `normal`.
   Pilihan `ringkasan` = jalan normal + kirim ringkasan harian saat itu juga (biasanya sekali sehari jam 08 WIB).

## Mengatur radar (`config.yaml`)
- `skor_min` — naikkan ke 55–60 kalau alert terlalu banyak, turunkan ke 45 kalau terlalu sedikit.
- `kirim_alert_turun: false` — kalau hanya ingin alert potensi naik.
- `syarat_akumulasi` / `maks_naik_7h_persen` — seberapa ketat syarat "akumulasi & masih di bawah".
- `abaikan` — koin yang tidak ingin dipantau.

## Filter sinyal, rencana jual & rekam jejak
- **Filter pasar BTC** (`filter_pasar`): sinyal naik ditahan saat BTC tren turun (di bawah MA50 & MA50 menurun).
  Pilihan `ketat` = sinyal naik hanya saat BTC tren naik.
- **Filter meme coin** (`filter_meme`): `ketat` = meme coin butuh skor lebih tinggi, `abaikan` = tidak pernah jadi sinyal naik.
- **Rencana jual** (`rencana`): tiap sinyal diberi TP1 (jual sebagian, lalu stop loss pindah ke harga beli), TP2 (target pola) dan SL.
- Sinyal yang tertahan filter tetap terlihat di tab 🟡 Pantau dengan keterangan alasannya.
- **Rekam jejak** (tab 📈): setiap alert dicatat harganya, lalu tiap jam dihitung hasilnya: perubahan, kena target/batal,
  hasil bila mengikuti rencana jual (bersih setelah biaya & pajak), dan perubahan BTC di periode yang sama.

## Model kondisi pasar (🌡️ skor pasar)
Setiap hari pasar diberi **skor −6 … +6** dari 6 suara: BTC vs MA50, BTC vs MA200, % koin di atas MA50,
jumlah koin Stage 2 vs Stage 4, arah lebar pasar 10 hari, dan altcoin vs BTC 30 hari (`pasar.py`).
Skor tinggi bukan berarti "waktunya beli": sinyal beli terbaik muncul saat BTC baru tren naik tetapi pasar luas
belum ikut naik; saat hampir semua sudah hijau (skor +5/+6, pasar kepanasan) sinyal beli baru nyaris tidak untung.

**Model pasar** = aturan lama + batas skor: *beli* hanya saat BTC tren naik **dan** skor pasar ≤ batas beli;
*jual dulu* hanya saat BTC tidak tren naik **dan** skor pasar ≤ batas jual. `backtest_pasar.py` menguji semua
strategi pada data harian sejak 2020, memilih batas itu secara walk-forward (batas tiap tahun hanya dipilih dari
data tahun-tahun sebelumnya), lalu membandingkan portofolio (maks 5 posisi) model lama vs baru di luar sampel.
Hasil: `model_pasar/LAPORAN.md`, `model_pasar/model.json` dan tab 🌡️ Model pasar di dashboard.
Radar membaca `model.json`; dengan `model_pasar: auto` (bawaan) batas skor hanya dipakai bila model baru menang di uji itu.
Jalankan ulang: **Actions → Model Kondisi Pasar → Run workflow** (otomatis tiap tanggal 1).

## 👀 Koin pantauan harian (minimal 1 koin per hari)
Kalau 24 jam terakhir tidak ada sinyal 🟢/🟩/🔻/🔴 sama sekali, mulai jam 08.00 WIB radar mengirim **satu koin per hari**
yang paling menonjol sesuai arah pasar (`pilihan.py`): BTC tren naik → skor beli radar tertinggi; selain itu → skor jual
tertinggi di antara koin Stage 4, beserta zona pantulan yang membuatnya jadi sinyal 🔻 sungguhan. Koin yang sama tidak
dipilih lagi selama 10 hari.
`backtest_pilihan.py` menguji 6 aturan pemilihan pada 178 ribu analisa harian (2020–2026). Hasil 24 Nov 2026: pada hari
tanpa sinyal rata-ratanya ±0% per transaksi (beli −0,65%, jual dulu +0,04%) dan bila ikut diperdagangkan portofolio turun
(+184% → +119%). Karena itu bawaannya **pantauan, bukan sinyal masuk** (`pilihan_harian: pantau`); `rencana` menambahkan
TP/SL, `false` mematikannya. Rincian: `backtest_pilihan/LAPORAN.md`.

## Uji "harian berjalan" (sinyal harian dicek tiap jam)
`backtest_berjalan.py` menguji apakah 🟩 awal Stage 2 dan 🔻 jual dulu sebaiknya dicek tiap jam, bukan hanya saat candle harian
tutup (07.00 WIB): mesin radar harian dijalankan apa adanya di setiap jam pada candle 24 jam berjalan (`berjalan.py`; tepat jam
07.00 WIB hasilnya identik dengan radar harian). Kedua sistem memakai aturan yang sama (gerbang model pasar, jeda 10 hari, masuk
1 jam setelah sinyal). Aturan lulus ditulis sebelum data ditarik.
Hasil 16 Nov 2026: **tidak dipasang** — dicek tiap jam +36% (penurunan terdalam −38%) vs hanya 07.00 WIB +157% (−20%) di
2023–Okt 2026. Rinciannya di `backtest_berjalan/LAPORAN.md` dan tab 🌡️ Model pasar.
Jalankan ulang: **Actions → Uji Harian Berjalan → Run workflow** (6 mesin × ±40 menit; catatan mentah di cabang `data-berjalan`).

## Uji sinyal per jam
`backtest_perjam.py` menguji apakah sinyal layak dihitung dari candle 1 jam: mesin radar yang sama (`perjam.py`) dijalankan di
setiap jam sejak 2020 pada 400 candle 1 jam terakhir (candle diperbesar √24× supaya ambang persennya sepadan), masuk dengan jeda
1 jam, rencana jual & gerbang dipilih walk-forward, lalu portofolionya dibandingkan dengan sistem harian. Aturan lulus ditulis
sebelum data ditarik.
Hasil 16 Nov 2026: **tidak dipasang** — per jam saja +11% (penurunan terdalam −47%) vs harian +184% (−24%); setelah biaya & pajak
±0,41% per transaksi, sinyal per jam nyaris sama dengan masuk di jam acak. Rinciannya di `backtest_perjam/LAPORAN.md` dan tab
🌡️ Model pasar. Jalankan ulang:
**Actions → Uji Sinyal Per Jam → Run workflow** (berat: 6 mesin × ±40 menit; sinyal mentah disimpan di cabang `data-perjam`).

## Uji order flow & market profile
`backtest_orderflow.py` menguji apakah konfirmasi dari candle 1 jam — delta (beli agresif − jual agresif), arah CVD 3 hari,
POC dan zona nilai 30 hari (`orderflow.py`) — memperbaiki hasil sinyal live. Sinyal dan hasilnya sama persis dengan uji
model pasar; konfirmasi dipilih walk-forward dan hanya dipasang bila di luar sampel total > dasar, Sharpe ≥ dasar + 0,15 dan
penurunan maksimum tidak lebih buruk dari 5 poin (aturan ini ditulis sebelum data ditarik).
Hasil 16 Nov 2026: **tidak dipasang** — tidak ada konfirmasi yang selisihnya bisa dibedakan dari kebetulan, dan sebagai saringan
total portofolio justru turun. Rinciannya di `backtest_orderflow/LAPORAN.md` dan di bagian bawah tab 🌡️ Model pasar.
Jalankan ulang: **Actions → Uji Order Flow & Market Profile → Run workflow** (berkas fitur ±12 MB disimpan di cabang `data-orderflow`).

## Backtest
Menguji mesin analisa yang sama pada data harian ±2,7 tahun (top 200 CMC di Binance), membandingkan 12 aturan jual
dan efek tiap filter. Jalankan: **Actions → Backtest Radar → Run workflow**. Hasil: `backtest/LAPORAN.md`
dan tab 🧪 Backtest di dashboard. Keterbatasan: tanpa data per jam, daftar koin = top 200 saat ini (survivorship bias).

## Hal yang perlu diketahui
- **Bukan nasihat investasi.** Pola grafik adalah probabilitas, bukan kepastian — banyak pola gagal. Selalu pakai level *batal* untuk membatasi rugi.
- Analisa memakai candle **harian** yang sudah tutup; sinyal bisa berubah setelah candle hari ini tutup (07.00 WIB).
- Elliott Wave otomatis sifatnya perkiraan kasar; hitungan gelombang bisa berbeda antar-analis.
- Beberapa koin top 200 tidak diperdagangkan di Binance/OKX (mis. token bursa lain) — daftarnya tampil di bawah dashboard.
- Paket gratis CoinMarketCap: 15.000 kredit/bulan; radar hanya memakai ±120/bulan (daftar diperbarui tiap 6 jam).

## Coba di komputer sendiri (opsional)
```
pip install -r requirements.txt
python scanner.py --mode demo     # grafik contoh di folder out/, dashboard di folder site/
```
