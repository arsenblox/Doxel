# DOXEL

**DOXEL** adalah aplikasi todo/task dengan gaya **PIXEL** dan sistem gameplay. Aplikasi ini dibuat untuk membantu mengatur tugas sekolah, pekerjaan, atau aktivitas lain dengan sistem level, EXP, streak, achievement, kalender, riwayat tugas, dan galeri bukti pengerjaan.

---

## Fitur Utama

### 1. Task / Tugas

Pengguna bisa membuat task baru dengan data berikut:

- Nama task
- Deskripsi
- Prioritas: `Low`, `Normal`, `Urgent`
- Tipe pekerjaan: `School`, `Work`, atau `Others`
- Deadline tanggal dan waktu
- Link LMS, bisa menggunakan:
  - Link penuh
  - ID LMS saja
  - Tipe LMS: `Assign` atau `Quiz`

Contoh link LMS yang didukung:

```text
https://mylms.telkomschools.sch.id/mod/assign/view.php?id=135546
https://mylms.telkomschools.sch.id/mod/quiz/view.php?id=135973
```

Jika menggunakan mode ID, cukup masukkan ID seperti:

```text
135546
```

Lalu pilih tipe `Assign` atau `Quiz`.

---

### 2. Sistem Prioritas dan EXP

Setiap task memberi EXP berdasarkan prioritas.

| Prioritas | Base EXP |
|---|---:|
| Low | 40 |
| Normal | 80 |
| Urgent | 120 |

Rumus level:

```text
exp_needed = 100 + (44 * level)
```

Jika task diselesaikan sebelum deadline, EXP dihitung berdasarkan prioritas dan sisa durasi task.

Jika task sudah melewati deadline, EXP yang didapat akan dikurangi sesuai aturan penalti yang dipakai di aplikasi.

---

### 3. Level dan Streak

DOXEL memiliki sistem progression seperti game.

- Menyelesaikan task memberi EXP.
- Jika EXP cukup, level akan naik.
- Jika task selesai sebelum deadline, streak bisa bertambah.
- Jika task melewati deadline, streak bisa hilang.

Saat level naik, aplikasi akan menampilkan animasi dan notifikasi overlay di bagian atas layar.

---

### 4. Complete Task dengan Catatan dan Foto

Saat menekan tombol **Complete**, aplikasi akan membuka form penyelesaian task.

Pengguna bisa menambahkan:

- Catatan penyelesaian
- Foto dari galeri
- Foto langsung dari kamera

Catatan dan foto bersifat opsional.

Maksimal foto yang bisa disimpan untuk satu task:

```text
10 gambar
```

Setelah task selesai, data akan masuk ke halaman History.

---

### 5. History

Halaman History menyimpan task yang sudah selesai.

Di dalam riwayat, pengguna bisa melihat:

- Nama task
- Catatan penyelesaian
- Foto yang disimpan
- EXP yang didapat
- Status selesai tepat waktu atau terlambat
- Tanggal dan waktu penyelesaian

Foto di History bisa ditekan untuk preview fullscreen, zoom, dan swipe antar gambar.

---

### 6. Gallery

Halaman Gallery mengumpulkan gambar dari task yang sudah selesai.

Fitur Gallery:

- Gambar dikelompokkan berdasarkan task
- Gambar bisa ditekan untuk preview fullscreen
- Gambar bisa disimpan ke galeri HP
- Semua gambar bisa disimpan sekaligus
- Bisa membuka link LMS dari task terkait

Flow upload ke LMS:

```text
DOXEL Gallery
→ Save to Gallery
→ Open LMS
→ Choose File
→ Photos & Videos
→ pilih gambar yang sudah disimpan
```

Catatan: Website LMS tidak bisa dipaksa langsung mengambil gambar dari aplikasi karena pembatasan keamanan Android/browser. Cara paling aman adalah menyimpan gambar ke galeri HP terlebih dahulu, lalu memilihnya dari file picker LMS.

---

### 7. Kalender

DOXEL memiliki kalender bulanan.

Fitur kalender:

- Menampilkan tanggal 1 sampai akhir bulan
- Menampilkan nama bulan dan tahun, misalnya `May 2026`
- Bisa melihat bulan sebelumnya dan bulan berikutnya
- Tanggal yang memiliki task akan diberi tanda titik

---

### 8. Sorting dan Favorite

Task bisa diurutkan berdasarkan:

- Highest Priority
- Highest EXP

Task yang diberi tanda favorite akan tetap diprioritaskan di bagian atas daftar, tetapi tidak memengaruhi EXP.

---

### 9. Achievement

DOXEL memiliki sistem achievement untuk membuat pengerjaan task terasa lebih seperti game.

Contoh achievement:

#### Task Achievement

- Task Beginner — menyelesaikan task pertama
- Task Regular — menyelesaikan 5 task
- Task Tracker — menyelesaikan 10 task
- Task Finisher — menyelesaikan 25 task
- Task Veteran — menyelesaikan 50 task
- Task Master — menyelesaikan 100 task

#### Level Achievement

- Getting Started — mencapai level 2
- Intermediate Learner — mencapai level 5
- Pro Learner — mencapai level 10
- Level 25 Reached
- Level 50 Reached
- DOXEL FINAL BOSS — mencapai level 100

#### Streak Achievement

- 1 Streak
- 5 Streak
- 10 Streak
- 15 Streak
- 30 Streak
- 60 Streak
- STREAK GOD — mencapai 100 streak

#### Misc Achievement

- Menyelesaikan task kurang dari 24 jam sebelum deadline
- Kehilangan streak untuk pertama kali
- Melewati deadline task untuk pertama kali
- Menyelesaikan task dengan gambar
- Menyelesaikan task dengan catatan
- Menyelesaikan urgent task tepat waktu

Achievement yang terbuka akan memunculkan overlay notification.

---

### 10. Overlay Notification

Aplikasi memiliki notifikasi overlay di bagian atas layar.

Overlay digunakan untuk:

- Task berhasil dibuat
- Task selesai
- Level up
- Achievement didapatkan
- Deadline hampir datang
- Deadline terlewat
- Error input form

Overlay memiliki animasi masuk dan keluar agar terasa lebih hidup.

---

### 11. Reminder Deadline

Pengguna bisa memilih reminder untuk deadline.

Pilihan reminder:

- 15 hari sebelum deadline
- 10 hari sebelum deadline
- 5 hari sebelum deadline
- 3 hari sebelum deadline
- 1 hari sebelum deadline
- 12 jam sebelum deadline
- 6 jam sebelum deadline
- 3 jam sebelum deadline
- 1 jam sebelum deadline
- 30 menit sebelum deadline

Catatan: Untuk saat ini reminder utama berjalan sebagai in-app alert saat aplikasi terbuka. Background notification Android membutuhkan setup tambahan.

---

### 12. Settings

Halaman Settings menyediakan beberapa opsi:

- Bahasa: English / Indonesia
- Theme: Dark / Light
- Font: Visitor TT2 / Classic
- Reset data aplikasi

UI Design compact sudah dihapus. Aplikasi sekarang menggunakan Simple UI sebagai tampilan utama.

---

## Tampilan UI

DOXEL menggunakan gaya visual:

- Dark soft pixel style
- Rounded card
- Pixel font
- Donut chart untuk progress
- Floating create button
- Overlay notification bergaya pixel card

Pada dark theme, desain mengikuti konsep dashboard yang sudah dibuat dari mockup awal.

---

## Cara Menjalankan Project

Pastikan Flutter sudah terinstall.

Cek Flutter:

```bash
flutter doctor
```

Install dependency:

```bash
flutter pub get
```

Jalankan aplikasi:

```bash
flutter run
```

Jika ada error cache:

```bash
flutter clean
flutter pub get
flutter run
```

Jika masih bermasalah di Windows, hapus lock file lalu ulangi:

```bash
del pubspec.lock
flutter pub get
flutter run
```

---

## Struktur Folder Utama

```text
lib/
  main.dart
  src/
    app.dart
    app_controller.dart
    app_theme.dart
    models.dart
    i18n.dart
    home_page.dart
    history_page.dart
    settings_page.dart
    create_quest_sheet.dart
    complete_quest_sheet.dart
    gallery_page.dart
    achievements_page.dart
    pixel_widgets.dart
    helpers.dart
```

Catatan: Beberapa nama file/class internal masih memakai nama `Quest` agar tidak merusak struktur kode lama, tetapi di UI pengguna istilah yang dipakai adalah **Task**.

---

## Catatan Penting

### LMS Upload

Aplikasi tidak bisa otomatis memasukkan gambar langsung ke input file website LMS karena batasan keamanan Android dan browser.

Solusi yang digunakan:

1. Simpan gambar dari DOXEL ke galeri HP.
2. Buka LMS dari aplikasi.
3. Tekan `Choose File` di LMS.
4. Pilih `Photos & Videos`.
5. Pilih gambar yang sudah disimpan.

### Notification Background

Overlay notification sudah tersedia di dalam aplikasi. Untuk notifikasi yang tetap muncul saat aplikasi ditutup, perlu implementasi tambahan menggunakan local notification plugin.

### Mini Game Bonus EXP

Ide mini game yang cocok untuk versi berikutnya:

```text
Timing Bar Minigame
```

Cara kerja:

- Bar bergerak kiri-kanan.
- Pemain menekan tombol saat cursor berada di zona hijau.
- Perfect memberi bonus EXP lebih besar.
- Good memberi bonus EXP kecil.
- Miss tidak memberi bonus EXP.

Contoh bonus:

| Hasil | Bonus EXP |
|---|---:|
| Perfect | +25% |
| Good | +15% |
| Miss | +0% |

Mini game ini cocok karena cepat, simpel, dan tidak mengganggu tujuan utama aplikasi sebagai task manager.

---

## Nama Aplikasi

Nama aplikasi saat ini:

```text
DOXEL
```

Makna nama:

```text
Do + Pixel = Doxel
```

Nama ini menggambarkan aplikasi todo/task dengan gaya pixel dan sistem gameplay.
