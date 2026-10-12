import requests

# URL server lokal Anda
url = "http://127.0.0.1:5000/upload"

# Nama file foto sampel yang ada di folder proyek Anda
image_path = "test_lalu_lintas.jpg"

try:
    with open(image_path, 'rb') as f:
        files = {'photo': f}
        print(f"Mengirim file '{image_path}' ke server lokal...")
        response = requests.post(url, files=files)
        
        print(f"Status HTTP: {response.status_code}")
        print(f"Pesan dari Server: {response.text}")
        
except FileNotFoundError:
    print(f"Error: File gambar '{image_path}' tidak ditemukan!")
    print("Pastikan Anda sudah meletakkan satu buah file foto berformat .jpg di dalam folder proyek.")
except Exception as e:
    print(f"Terjadi kesalahan: {e}")