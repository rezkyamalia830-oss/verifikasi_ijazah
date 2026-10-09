import cv2
import numpy as np
import pytesseract
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "images" / "ijazah 01.jpg"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ROI dibuat dalam bentuk proporsi (0 sampai 1), sehingga bisa
# menyesuaikan gambar beresolusi berbeda dengan rasio yang sama.
# Berdasarkan contoh ijazah yang diberikan:
# nomor berada di kiri bawah; tanda tangan pemilik di bawah foto.
ROI_NOMOR_PROP = (0.055, 0.905, 0.255, 0.065)
ROI_TTD_PROP = (0.435, 0.835, 0.105, 0.095)

GROUND_TRUTH = "571012022000056"

# Sesuaikan lokasi ini jika Tesseract terpasang di folder berbeda.
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def crop_proportional(image, roi_prop):
    """Memotong gambar menggunakan (x, y, lebar, tinggi) proporsional."""
    height, width = image.shape[:2]
    px, py, pw, ph = roi_prop
    x = int(px * width)
    y = int(py * height)
    w = int(pw * width)
    h = int(ph * height)

    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    w = max(1, min(w, width - x))
    h = max(1, min(h, height - y))
    return image[y:y + h, x:x + w]


def enhance_images(gray):
    """Menghasilkan beberapa versi gambar untuk perbandingan OCR."""
    clahe = cv2.createCLAHE(
        clipLimit=2.0, tileGridSize=(8, 8)
    ).apply(gray)

    blur = cv2.GaussianBlur(clahe, (3, 3), 0)
    sharpen_kernel = np.array(
        [[0, -1, 0], [-1, 5, -1], [0, -1, 0]],
        dtype=np.float32
    )
    sharpened = cv2.filter2D(clahe, -1, sharpen_kernel)

    _, otsu = cv2.threshold(
        clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    adaptive = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 11
    )

    return {
        "grayscale": gray,
        "clahe": clahe,
        "sharpening": sharpened,
        "otsu": otsu,
        "adaptive": adaptive,
    }


def read_number(image):
    """OCR khusus nomor ijazah yang hanya berisi angka."""
    enlarged = cv2.resize(
        image, None, fx=4, fy=4,
        interpolation=cv2.INTER_CUBIC
    )
    if len(enlarged.shape) == 3:
        gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
    else:
        gray = enlarged

    # Nomor tercetak gelap pada kertas terang.
    _, binary = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    config = (
        "--oem 3 --psm 7 "
        "-c tessedit_char_whitelist=0123456789"
    )
    text = pytesseract.image_to_string(
        binary, config=config, lang="eng"
    )
    return re.sub(r"\D", "", text)


def calculate_cer(reference, prediction):
    """Character Error Rate berdasarkan jarak edit Levenshtein."""
    reference = re.sub(r"\s+", "", reference).upper()
    prediction = re.sub(r"\s+", "", prediction).upper()
    if not reference:
        return None

    previous = list(range(len(prediction) + 1))
    for i, ref_char in enumerate(reference, start=1):
        current = [i]
        for j, pred_char in enumerate(prediction, start=1):
            cost = 0 if ref_char == pred_char else 1
            current.append(min(
                current[j - 1] + 1,       # insertion
                previous[j] + 1,           # deletion
                previous[j - 1] + cost     # substitution
            ))
        previous = current

    return previous[-1] / len(reference)


def detect_signature(signature_crop):
    """
    Deteksi sederhana berbasis threshold dan morfologi.
    ROI harus mencakup tanda tangan pemilik, bukan tanda tangan Rektor/Dekan.
    """
    gray = cv2.cvtColor(signature_crop, cv2.COLOR_BGR2GRAY)
    enlarged = cv2.resize(
        gray, None, fx=2, fy=2,
        interpolation=cv2.INTER_CUBIC
    )
    _, binary = cv2.threshold(
        enlarged, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN, kernel
    )
    cleaned = cv2.morphologyEx(
        cleaned, cv2.MORPH_CLOSE, kernel
    )

    foreground_ratio = cv2.countNonZero(cleaned) / cleaned.size

    # Nilai awal; mungkin perlu disesuaikan untuk gambar lain.
    threshold_ratio = 0.015
    result = "PRESENT" if foreground_ratio >= threshold_ratio else "ABSENT"

    cv2.imwrite(str(OUTPUT_DIR / "signature_crop.png"), signature_crop)
    cv2.imwrite(str(OUTPUT_DIR / "signature_threshold.png"), binary)
    cv2.imwrite(str(OUTPUT_DIR / "signature_morphology.png"), cleaned)
    return result, foreground_ratio


def main():
    image = cv2.imread(str(IMAGE_PATH))
    if image is None:
        print("Gambar tidak ditemukan:")
        print(IMAGE_PATH)
        print("Pastikan file ada di folder images dan namanya tepat.")
        return

    print("=== INFORMASI GAMBAR ===")
    print(f"File           : {IMAGE_PATH.name}")
    print(f"Ukuran gambar  : {image.shape[1]} x {image.shape[0]} px")

    # Nomor ijazah
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    number_crop = crop_proportional(gray, ROI_NOMOR_PROP)
    cv2.imwrite(str(OUTPUT_DIR / "number_crop.png"), number_crop)

    methods = enhance_images(number_crop)
    results = {}

    print("\n=== PERBANDINGAN OCR ===")
    for method_name, processed in methods.items():
        output_path = OUTPUT_DIR / f"number_{method_name}.png"
        cv2.imwrite(str(output_path), processed)

        recognized = read_number(processed)
        cer = calculate_cer(GROUND_TRUTH, recognized)
        results[method_name] = (recognized, cer)

        cer_text = "Tidak dihitung" if cer is None else f"{cer * 100:.2f}%"
        print(f"{method_name:12} | OCR: {recognized or 'Tidak terbaca'} | CER: {cer_text}")

    valid_results = [
        (name, text, cer)
        for name, (text, cer) in results.items()
        if cer is not None
    ]
    if valid_results:
        best_method, best_number, best_cer = min(
            valid_results, key=lambda item: item[2]
        )
    else:
        best_method, best_number, best_cer = "clahe", "", None

    # Deteksi tanda tangan pemilik
    signature_crop = crop_proportional(image, ROI_TTD_PROP)
    signature_result, foreground_ratio = detect_signature(signature_crop)

    print("\n=== HASIL VERIFIKASI ===")
    print(f"File           : {IMAGE_PATH.name}")
    print(f"Nomor benar    : {GROUND_TRUTH}")
    print(f"Nomor terbaca  : {best_number or 'Tidak terbaca'}")
    print(f"Tanda tangan   : {signature_result}")
    print(f"Metode OCR     : {best_method}")
    print(
        "CER terbaik    : "
        + ("Tidak dapat dihitung" if best_cer is None else f"{best_cer * 100:.2f}%")
    )
    print(f"Foreground     : {foreground_ratio:.4f}")
    print(f"Output         : {OUTPUT_DIR}")
    print("\nPeriksa number_crop.png dan signature_crop.png di folder output.")
    print("Jika potongan belum tepat, sesuaikan ROI_NOMOR_PROP dan ROI_TTD_PROP.")


if __name__ == "__main__":
    main()
