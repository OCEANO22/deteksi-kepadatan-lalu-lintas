import os
import requests
import cv2
from flask import Flask, request
from ultralytics import YOLO
from dotenv import load_dotenv

# 1. MEMUAT ENVIRONMENT VARIABLES DARI FILE .env
# Memastikan variabel rahasia terbaca dari file lokal
load_dotenv()

app = Flask(__name__)

# Ambil token dan ID murni dari file .env tanpa fallback hardcode di skrip
BOT_TOKEN = os.getenv('8592180742:AAFf5liqbci2GiyJsEaS4gUIXfBJOqyc1rw')
CHAT_ID = os.getenv('-1003900335127')

# Validasi untuk memastikan .env sudah diatur
if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN atau CHAT_ID tidak ditemukan! Pastikan Anda sudah membuat file .env.")

# 2. INISIALISASI AI YOLO
print("Memuat model AI YOLOv8...")
# Karena dijalankan di server lokal (spesifikasi biasanya lebih tinggi dari free tier cloud),
# Anda bisa menggunakan 'yolov8s.pt' (Small) jika ingin akurasi lebih baik, atau tetap 'yolov8n.pt' (Nano) untuk kecepatan.
model = YOLO('yolov8s.pt')

def send_to_telegram(image_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(image_path, 'rb') as photo:
            payload = {'chat_id': CHAT_ID, 'caption': caption}
            files = {'photo': photo}
            response = requests.post(url, data=payload, files=files)
            if response.status_code == 200:
                print("Laporan berhasil dikirim ke Telegram!")
            else:
                print(f"Gagal kirim ke Telegram: {response.text}")
    except Exception as e:
        print(f"Error kirim Telegram: {e}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'photo' not in request.files:
        return "Tidak ada file photo", 400
    
    # Simpan foto asli dari ESP32-CAM
    file = request.files['photo']
    filename = 'lalu_lintas_terbaru.jpg'
    file.save(filename)
    print("Foto diterima, mulai deteksi kendaraan...")

    # 3. PROSES DETEKSI YOLO
    results = model(filename)
    
    # Pemetaan ID Objek di YOLO (dataset COCO) ke nama kendaraan
    jenis_kendaraan = {
        2: "Mobil 🚗",
        3: "Motor 🏍️",
        5: "Bus 🚌",
        7: "Truk 🚚"
    }
    
    # Inisialisasi tempat menyimpan jumlah per jenis kendaraan
    rekapan_kendaraan = {
        "Mobil 🚗": 0,
        "Motor 🏍️": 0,
        "Bus 🚌": 0,
        "Truk 🚚": 0
    }
    
    jumlah_total = 0
    
    # Menghitung objek yang terdeteksi dan mengelompokkannya
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        if class_id in jenis_kendaraan:
            nama_kendaraan = jenis_kendaraan[class_id]
            rekapan_kendaraan[nama_kendaraan] += 1
            jumlah_total += 1

    # 4. PENENTUAN STATUS KEPADATAN
    # (Batas jumlah kendaraan bisa disesuaikan dengan kebutuhan Anda)
    if jumlah_total < 5:
        status = "Lancar 🟢"
    elif jumlah_total <= 10:
        status = "Ramai 🟡"
    else:
        status = "Macet 🔴"

    # 5. SIMPAN FOTO HASIL DETEKSI
    annotated_frame = results[0].plot()
    hasil_filename = 'hasil_deteksi.jpg'
    cv2.imwrite(hasil_filename, annotated_frame)

    # 6. SIAPKAN PESAN & KIRIM KE TELEGRAM
    pesan = "🚦 LAPORAN LALU LINTAS 🚦\n\n"
    
    pesan += "Rincian Kendaraan:\n"
    # Looping untuk menampilkan setiap jenis dan jumlahnya
    for jenis, jumlah in rekapan_kendaraan.items():
        pesan += f"- {jenis}: {jumlah}\n"
        
    pesan += f"\nTotal Kendaraan: {jumlah_total}\n"
    pesan += f"📊 Status: {status}"

    send_to_telegram(hasil_filename, pesan)

    return "Deteksi Selesai", 200

if __name__ == '__main__':
    # Untuk server lokal, kita tetapkan port secara eksplisit (misal 5000)
    # Debug=True diaktifkan agar error langsung terlihat di terminal saat proses pengembangan
    port = 5000
    print(f"Server LOKAL berjalan di http://0.0.0.0:{port} ... Menunggu kiriman foto dari ESP32-CAM")
    app.run(host='0.0.0.0', port=port, debug=True)