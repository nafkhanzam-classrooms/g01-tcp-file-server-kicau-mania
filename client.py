import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 5004

os.makedirs('client_files', exist_ok=True)

def receive_messages(sock):
    while True:
        try:
            header_data = sock.recv(1024)
            if not header_data: break
            header = header_data.decode('utf-8').strip()
            
            #PROSES DOWNLOAD DARI SERVER
            if header.startswith('/ready_download'):
                parts = header.split(' ')
                filename = parts[1]
                filesize = int(parts[2])
                
                print(f"\n[Mendownload {filename} ({filesize} bytes)...]")
                filepath = os.path.join('client_files', filename)
                
                with open(filepath, 'wb') as f:
                    bytes_received = 0
                    while bytes_received < filesize:
                        chunk = sock.recv(min(4096, filesize - bytes_received))
                        if not chunk: break
                        f.write(chunk)
                        bytes_received += len(chunk)
                print(f"\n[SUKSES] File {filename} tersimpan di folder 'client_files'\n> ", end="")
            
            #CHAT / PESAN BIASA
            else:
                print(f"\n{header}\n> ", end="")
        except Exception as e:
            print(f"\nTerputus dari server.")
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
    except:
        print("Gagal terhubung. Pastikan server sudah berjalan.")
        return
        
    thread = threading.Thread(target=receive_messages, args=(client,))
    thread.daemon = True
    thread.start()

    print("=== MULTI-CLIENT TCP APP ===")
    print("Perintah: /list | /upload <file> | /download <file> | <ketik pesan>\n")
    
    while True:
        pesan = input("> ")
        if pesan.lower() == 'exit':
            break
            
        #PROSES UPLOAD KE SERVER
        if pesan.startswith('/upload'):
            parts = pesan.split(' ', 1)
            if len(parts) < 2: 
                print("Format: /upload namafile.ext")
                continue
            
            filename = parts[1]
            if os.path.exists(filename):
                filesize = os.path.getsize(filename)
                client.sendall(f"/upload {filename} {filesize}".ljust(1024).encode('utf-8'))
                
                print(f"Mengunggah {filename}...")
                with open(filename, 'rb') as f:
                    while True:
                        bytes_read = f.read(4096)
                        if not bytes_read: break
                        client.sendall(bytes_read)
            else:
                print("File tidak ditemukan di lokal!")
                
        else:
            client.sendall(pesan.ljust(1024).encode('utf-8'))

    client.close()

if __name__ == "__main__":
    start_client()