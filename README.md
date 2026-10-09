# Prototipe Verifikasi Ijazah

## Deskripsi

Proyek ini merupakan prototipe pengolahan citra digital untuk membaca nomor ijazah menggunakan OCR (*Optical Character Recognition*) dan mendeteksi keberadaan tanda tangan pada area tertentu.

Program membandingkan beberapa metode peningkatan citra berdasarkan Character Error Rate (CER).

## Struktur Folder

verifikasi-ijazah/
├── images/
│   └── ijazah 01.jpg
├── output/
├── main.py
├── requirements.txt
└── README.md

## Teknologi

* Python
* OpenCV
* NumPy
* pytesseract
* Tesseract OCR

## Instalasi

Pasang pustaka Python melalui terminal:

py -m pip install -r requirements.txt
```

Tesseract OCR juga harus terpasang secara terpisah. Jika lokasinya berbeda, sesuaikan `tesseract_cmd` di `main.py`.

## Cara Menjalankan

Letakkan gambar ijazah di folder `images` dengan nama `ijazah 01.jpg`, kemudian jalankan:


Hasil pengolahan citra akan disimpan di folder `output`.

## Tahapan Pengolahan Citra

1. **Grayscale:** mengubah citra berwarna menjadi skala abu-abu.
2. **CLAHE:** meningkatkan kontras lokal agar karakter lebih terlihat.
3. **Sharpening:** menajamkan tepi karakter.
4. **Otsu thresholding:** mengubah citra menjadi hitam-putih dengan ambang otomatis.
5. **Adaptive thresholding:** menentukan ambang berdasarkan area lokal.
6. **OCR:** membaca nomor ijazah dari area yang dipotong.
7. **Morfologi:** membersihkan noise pada citra tanda tangan menggunakan operasi opening dan closing.

## Evaluasi OCR

CER (*Character Error Rate*) digunakan untuk menghitung kesalahan karakter pada hasil OCR.

Rumus:

CER = (S + D + I) / N

Keterangan:

* S adalah jumlah karakter yang salah diganti.
* D adalah jumlah karakter yang hilang.
* I adalah jumlah karakter tambahan.
* N adalah jumlah karakter pada teks referensi.

Semakin kecil CER, semakin dekat hasil OCR dengan nomor referensi. CER 0% berarti semua karakter cocok.

Nomor referensi pada contoh ini adalah `571012022000056`. Pastikan nomor referensi sesuai dengan gambar yang diuji.

## Deteksi Tanda Tangan

Program memotong area tanda tangan pemilik ijazah, mengubahnya menjadi citra biner, melakukan operasi morfologi, lalu menghitung rasio piksel foreground.

Rasio tersebut dibandingkan dengan ambang untuk menghasilkan status PRESENT atau ABSENT.

Metode ini merupakan deteksi sederhana, bukan verifikasi keaslian tanda tangan. Area ROI dan ambang perlu diuji menggunakan contoh gambar dengan dan tanpa tanda tangan.

## Berkas Keluaran

* `number_crop.png`: potongan area nomor ijazah.
* `number_grayscale.png`: citra grayscale.
* `number_clahe.png`: hasil CLAHE.
* `number_sharpening.png`: hasil sharpening.
* `number_otsu.png`: hasil Otsu thresholding.
* `number_adaptive.png`: hasil adaptive thresholding.
* `signature_crop.png`: potongan area tanda tangan.
* `signature_threshold.png`: hasil thresholding tanda tangan.
* `signature_morphology.png`: hasil operasi morfologi.

## Batasan

Hasil OCR dan deteksi tanda tangan dipengaruhi kualitas gambar, posisi ROI, pencahayaan, dan ambang yang digunakan. Pengujian pada satu gambar belum cukup untuk menyimpulkan performa metode secara umum.

## Privasi

Gambar ijazah dapat memuat informasi pribadi. Pastikan memiliki izin sebelum mengunggah gambar ke repositori publik. Gunakan gambar yang telah disamarkan jika diperlukan.
