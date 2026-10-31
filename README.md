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

## Mengatur radar (`config.yaml`)
- `skor_min` — naikkan ke 55–60 kalau alert terlalu banyak, turunkan ke 45 kalau terlalu sedikit.
- `kirim_alert_turun: false` — kalau hanya ingin alert potensi naik.
- `syarat_akumulasi` / `maks_naik_7h_persen` — seberapa ketat syarat "akumulasi & masih di bawah".
- `abaikan` — koin yang tidak ingin dipantau.

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
