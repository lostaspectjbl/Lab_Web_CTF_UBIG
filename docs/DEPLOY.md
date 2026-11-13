# Panduan Deploy di aaPanel

Panduan ini memasang enam lab sebagai enam container Docker di server aaPanel.
Contoh lokasi proyek: `/www/ctf-labs`, port host `8011`-`8016`.

## 1. Prasyarat

- aaPanel sudah terpasang dan server dapat diakses.
- Docker sudah terpasang dari **App Store** aaPanel (cari "Docker" lalu install).
- Repo proyek bersifat **private** di GitHub (atau Git provider lain).
- Port `8011`-`8016` belum dipakai aplikasi lain.

Cek Docker di server:

```bash
docker --version
docker compose version
```

Jika `docker compose` tidak tersedia, gunakan `docker-compose` pada semua
perintah di bawah.

## 2. Push Proyek dari Komputer Lokal

Jalankan di folder proyek:

```bash
git init
git add .
git commit -m "Enam lab CTF web"
git branch -M main
git remote add origin https://github.com/<USERNAME>/<REPO>.git
git push -u origin main
```

Saat diminta password, gunakan **Personal Access Token** GitHub, bukan password
akun. Pastikan `.env` tidak ikut ter-commit (sudah ada di `.gitignore`).

## 3. Clone dan Isi Environment di Server

Login SSH ke server, lalu:

```bash
cd /www
git clone https://<USERNAME>:<TOKEN>@github.com/<USERNAME>/<REPO>.git ctf-labs
cd /www/ctf-labs
cp .env.example .env
```

Buat enam secret acak:

```bash
for i in 1 2 3 4 5 6; do openssl rand -hex 16; done
```

Buka `.env` (misalnya dengan editor aaPanel atau `nano .env`), lalu isi
`SECRET_KEY_1` sampai `SECRET_KEY_6` dengan hasil di atas. Isi juga
`FLAG_1` sampai `FLAG_6` dengan flag asli lomba, contoh format
`CTF{...}`. Jangan memakai flag contoh dari `.env.example`.

Amankan file:

```bash
chmod 600 .env
```

## 4. Build dan Jalankan

```bash
docker compose up -d --build
```

Perintah ini membangun satu image lalu menjalankan enam container:
`ctf-lab1` sampai `ctf-lab6`. Tidak ada volume, jadi database SQLite di dalam
container akan dibuat ulang saat container restart.

Cek status:

```bash
docker compose ps
```

Semua service harus berstatus `running`.

## 5. Verifikasi Cepat

```bash
curl -I http://127.0.0.1:8011
```

Harus menghasilkan `302` dengan `Location: /lab1`. Ulangi untuk port `8012`
sampai `8016` dan sesuaikan nomor lab.

Uji bahwa flag terbaca (ganti dengan flag asli di `.env`):

```bash
curl -s "http://127.0.0.1:8011/lab1?category=Gifts%27%20OR%201%3D1--" \
  | grep -o 'CTF{[^}]*}'
```

Jika perintah menghasilkan flag, aplikasi dan environment sudah benar.

## 6. Membuka Akses dari Luar

### Opsi A - Buka Port Langsung

1. Di aaPanel: **Security** → izinkan port `8011`-`8016` (TCP).
2. Di firewall penyedia cloud (AWS Security Group, GCP Firewall, dll.),
   izinkan port yang sama.
3. Akses `http://IP-SERVER:8011` sampai `http://IP-SERVER:8016`.

Cara ini paling cepat, tetapi setiap lab memakai port berbeda.

### Opsi B - Reverse Proxy per Subdomain (Disarankan)

Gunakan satu subdomain per lab, misalnya `lab1.domainkamu.com` sampai
`lab6.domainkamu.com`.

1. Ubah bagian `ports` di `docker-compose.yml` agar hanya listen di localhost:

   ```yaml
   ports:
     - "127.0.0.1:8011:5000"
   ```

   Lakukan untuk semua service, lalu jalankan ulang:

   ```bash
   docker compose up -d
   ```

2. Buat DNS tipe `A` untuk setiap subdomain ke IP server.
3. Di aaPanel: **Website** → **Add site**, isi domain `lab1.domainkamu.com`,
   tanpa PHP/database.
4. Buka pengaturan site → **Reverse Proxy** → **Add reverse proxy**:
   - Target URL: `http://127.0.0.1:8011`
   - Kirim header `Host` asli.
5. Ulangi untuk lab 2-6 dengan port `8012`-`8016`.
6. Aktifkan **SSL** → **Let's Encrypt** untuk setiap site agar memakai HTTPS.

Jangan membuka port `8011`-`8016` ke publik jika memakai Opsi B.

## 7. Update Aplikasi

```bash
cd /www/ctf-labs
git pull
docker compose up -d --build
```

Lihat log satu lab:

```bash
docker compose logs -f lab1
```

Restart, hentikan, atau hapus:

```bash
docker compose restart lab1
docker compose stop
docker compose down
```

## 8. Troubleshooting

- **Compose berhenti dengan pesan `SECRET_KEY_n wajib diisi`**: `.env` belum
  ada atau variabelnya kosong. Salin dari `.env.example` dan isi.
- **Port sudah dipakai**: cek dengan `ss -lntp | grep 801`, lalu hentikan
  aplikasi yang memakai port tersebut atau ubah port host di compose.
- **Halaman 502 dari reverse proxy**: pastikan container berjalan
  (`docker compose ps`) dan target proxy memakai port host yang benar.
- **Perubahan `.env` tidak terbaca**: jalankan `docker compose up -d` agar
  container dibuat ulang dengan environment baru.
- **Ingin mengosongkan database/keranjang peserta**: restart container lab
  tersebut; database dibuat ulang saat start.
- **Docker tidak berjalan**: buka App Store aaPanel → Docker → start service.

## 9. Pengamanan

- Simpan repo sebagai private dan batasi akses SSH.
- Jangan commit `.env`; file itu berisi flag dan secret.
- Jalankan lab hanya untuk peserta lomba, lalu matikan container setelah acara.
- Flag di CTFd harus sama dengan `FLAG_n` di `.env`.
- Panduan membuat challenge di CTFd ada di [CTFD.md](CTFD.md).
