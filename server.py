from flask import Flask, request
import requests
import cv2
from ultralytics import YOLO

app = Flask(__name__)

# -------------------------------------------------------------
# 1. MASUKKAN TOKEN DAN CHAT ID TELEGRAM KAMU DI SINI
BOT_TOKEN = "8592180742:AAFf5liqbci2GiyJsEaS4gUIXfBJOqyc1rw"
CHAT_ID = -1003900335127
# -------------------------------------------------------------

# 2. INISIALISASI AI YOLO
print("Memuat model AI YOLOv8...")
model = YOLO('yolov8s.pt') # 'n' artinya Nano (versi paling ringan & cepat untuk laptop)

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
    
    # ID Objek di YOLO: 2=Mobil, 3=Motor, 5=Bus, 7=Truk
    vehicle_classes = [2, 3, 5, 7]
    jumlah_kendaraan = 0
    
    # Menghitung objek yang terdeteksi
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        if class_id in vehicle_classes:
            jumlah_kendaraan += 1

    # 4. PENENTUAN STATUS KEPADATAN
    if jumlah_kendaraan < 5:
        status = "Lancar 🟢"
    elif jumlah_kendaraan <= 10:
        status = "Ramai 🟡"
    else:
        status = "Macet 🔴"

    # 5. SIMPAN FOTO HASIL DETEKSI (Berisi kotak-kotak penanda objek)
    annotated_frame = results[0].plot()
    hasil_filename = 'hasil_deteksi.jpg'
    cv2.imwrite(hasil_filename, annotated_frame)

    # 6. SIAPKAN PESAN & KIRIM KE TELEGRAM
    pesan = f"🚦 LAPORAN LALU LINTAS 🚦\n\n"
    pesan += f"🚗 Jumlah Kendaraan: {jumlah_kendaraan}\n"
    pesan += f"📊 Status: {status}"

    send_to_telegram(hasil_filename, pesan)

    return "Deteksi Selesai", 200

if __name__ == '__main__':
    print("Server berjalan... Menunggu kiriman foto dari ESP32-CAM")
    app.run(host='0.0.0.0', port=5000)