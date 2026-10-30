# 🛰 Radar Whale Kripto — gratis & jalan otomatis

Tiap jam radar ini memindai ±250 koin USDT di Binance (cadangan: OKX), lalu
mengirim **alert + grafik ke Telegram** kalau ada koin yang:

| Sinyal | Artinya | Cara hitung |
|---|---|---|
| ⚡ **Whale masuk (1 jam)** | Ada pembelian besar mendadak | Volume 1 jam ≥ 4x rata-rata 48 jam, dan ≥ 58% adalah *market buy* (beli agresif) |
| 🐋 **Lonjakan volume harian** | Uang besar mulai masuk | Volume 24 jam ≥ 3x rata-rata 20 hari, dominasi beli |
| 🧲 **Akumulasi diam-diam** | Koin dikumpulkan sebelum harga bergerak | OBV naik + CMF positif, tapi harga 20 hari masih datar (±12%) |
| 🚀 **Breakout zona akumulasi** | Harga keluar dari zona tempat koin dikumpulkan | Harga di atas zona akumulasi & di atas high 20 hari, volume ≥ 1,5x |
| 🔻 Tekanan jual besar | Kemungkinan whale **keluar** | Volume ≥ 2x tapi didominasi jual (hanya muncul di ringkasan, bukan alert beli) |

Setiap koin diberi **skor 0–100**. Alert dikirim bila skor ≥ 45 (bisa diubah).
Koin yang sama tidak dikirim ulang selama 12 jam kecuali muncul sinyal baru.
Setiap hari jam 08.00 WIB dikirim **ringkasan harian** 10 koin skor tertinggi.

### Cara membaca grafik alert
- **Area biru muda = zona akumulasi**: kisaran harga tempat 70% volume 30 hari terakhir terjadi — di sinilah investor paling banyak mengumpulkan koin.
- **Garis putus-putus biru = POC**: satu level harga dengan volume terbesar (harga "favorit" para pengumpul). Sering jadi support saat harga turun.
- **Panel kanan**: volume per level harga. Batang paling panjang = POC.
- **Batang oranye di panel volume**: hari dengan volume > 2x rata-rata.
- **Garis OBV naik** sementara harga datar = koin sedang dikumpulkan.
- Candle **berongga = naik**, **terisi = turun**.

---

## Setup (±15 menit, sekali saja, semua gratis)

### 1. Buat bot Telegram
1. Buka Telegram, cari **@BotFather** → kirim `/newbot` → ikuti instruksinya.
2. Simpan **token** yang diberikan (bentuknya `123456789:AAH...`).
3. Buka chat dengan bot baru Anda, tekan **Start**, kirim pesan apa saja (misal `halo`).
4. Buka di browser: `https://api.telegram.org/bot<TOKEN>/getUpdates` (ganti `<TOKEN>`).
   Cari `"chat":{"id":123456789` → angka itu adalah **Chat ID** Anda.
   *Mau kirim ke grup? Masukkan bot ke grup, kirim pesan di grup, ulangi langkah ini (ID grup diawali tanda minus).*

### 2. Buat repository GitHub
1. Daftar/masuk di **github.com** (gratis).
2. Klik **+** → **New repository** → nama: `crypto-whale-radar` → pilih **Public** → **Create repository**.
   > Public = menit GitHub Actions **gratis tanpa batas**. Token Telegram tetap rahasia karena disimpan di *Secrets*, bukan di file.
   > Kalau pilih Private, kuota gratis 2.000 menit/bulan — cukup untuk jalan tiap jam (±1.400 menit/bulan), tapi jangan dipercepat.
3. Klik **uploading an existing file** → seret file `scanner.py`, `config.yaml`, `requirements.txt`, `README.md` → **Commit changes**.
4. Klik **Add file → Create new file**. Di kolom nama ketik persis:
   `.github/workflows/radar.yml`
   lalu salin-tempel seluruh isi file `radar.yml` → **Commit changes**.

### 3. Simpan token sebagai rahasia
**Settings → Secrets and variables → Actions → New repository secret**, buat dua:
- Name `TELEGRAM_BOT_TOKEN` → isi token bot
- Name `TELEGRAM_CHAT_ID` → isi Chat ID (bisa beberapa, pisahkan koma: `111,-100222`)

Lalu **Settings → Actions → General → Workflow permissions** → pilih **Read and write permissions** → **Save**.

### 4. Nyalakan & tes
1. Buka tab **Actions** → kalau ada tombol hijau "I understand my workflows…", klik.
2. Pilih **Radar Whale Kripto** → **Run workflow** → mode **tes-telegram** → Run. Telegram harus menerima "✅ Radar Whale tersambung!".
3. Jalankan lagi dengan mode **demo** → Anda menerima contoh alert + grafik (data simulasi) untuk melihat tampilannya.
4. Selesai. Mulai sekarang radar jalan sendiri **tiap jam** (menit ke-7). Hasil lengkap tiap putaran (tabel 30 koin teratas) bisa dilihat di tab **Actions → klik salah satu run → Summary**.

---

## Mengatur radar
Edit `config.yaml` langsung di GitHub (ikon pensil). Yang paling sering diubah:
- `skor_min_alert` — naikkan ke 55–60 kalau alert terlalu banyak.
- `min_volume_24j_usd` — turunkan untuk ikut memantau koin kecil (lebih berisiko dimanipulasi).
- `pantau_khusus` — koin yang selalu dipantau, misal `[BTC, ETH, SOL]`.
- `cooldown_jam` — jeda sebelum koin yang sama boleh di-alert lagi.

Mengubah frekuensi: edit baris `cron` di `.github/workflows/radar.yml`
(`7 * * * *` = tiap jam; `7,37 * * * *` = tiap 30 menit — hanya untuk repo Public).

## Hal yang perlu diketahui
- **Bukan nasihat investasi.** Volume tinggi ≠ harga pasti naik. Whale juga bisa sengaja memancing pembeli lalu jual (*pump & dump*), terutama di koin kecil.
- Radar membaca **data transaksi di bursa**, bukan dompet on-chain. Transfer whale antar-dompet tidak terlihat.
- Volume sebagian bursa bisa digelembungkan (*wash trading*); karena itu koin dengan volume < $2 juta diabaikan.
- Jadwal GitHub kadang telat beberapa menit saat server ramai.
- GitHub otomatis mematikan jadwal di repo publik yang tidak ada aktivitas 60 hari. Radar ini menyimpan `state.json` setiap hari (ringkasan harian), jadi tetap aktif. Kalau suatu saat berhenti, buka tab Actions → **Enable workflow**.
- Kalau Binance & OKX sama-sama gagal diakses, Anda akan menerima pesan ⚠️ di Telegram (maks. sekali per 6 jam).

## Coba di komputer sendiri (opsional)
```
pip install -r requirements.txt
python scanner.py --mode demo        # grafik contoh tersimpan di folder out/
```
