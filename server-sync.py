import socket
import os

HOST = '127.0.0.1'
PORT = 5000

os.makedirs('server_files', exist_ok=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print(f"[SYNC SERVER] Berjalan di {HOST}:{PORT}")
print("Server ini hanya bisa melayani 1 client dalam 1 waktu.")

while True:
    print("\nMenunggu client...")
    conn, addr = server.accept()
    print(f"[KONEKSI] Client {addr} terhubung.")
    
    while True:
        try:
            header_data = conn.recv(1024)
            if not header_data: break
            header = header_data.decode('utf-8').strip()
            
            if header == '/list':
                files = os.listdir('server_files')
                pesan = f"[SERVER] File: {', '.join(files) if files else 'Kosong'}"
                conn.sendall(pesan.ljust(1024).encode('utf-8'))
                
            elif header.startswith('/upload'):
                parts = header.split(' ')
                filename, filesize = parts[1], int(parts[2])
                with open(os.path.join('server_files', filename), 'wb') as f:
                    bytes_rec = 0
                    while bytes_rec < filesize:
                        chunk = conn.recv(min(4096, filesize - bytes_rec))
                        if not chunk: break
                        f.write(chunk)
                        bytes_rec += len(chunk)
                conn.sendall(f"[SERVER] Upload {filename} sukses.".ljust(1024).encode('utf-8'))
                
            elif header.startswith('/download'):
                filename = header.split(' ')[1]
                filepath = os.path.join('server_files', filename)
                if os.path.exists(filepath):
                    filesize = os.path.getsize(filepath)
                    conn.sendall(f"/ready_download {filename} {filesize}".ljust(1024).encode('utf-8'))
                    with open(filepath, 'rb') as f:
                        while True:
                            bytes_read = f.read(4096)
                            if not bytes_read: break
                            conn.sendall(bytes_read)
                else:
                    conn.sendall("[SERVER] File tidak ada!".ljust(1024).encode('utf-8'))
            else:
                conn.sendall(f"[SERVER Echo]: {header}".ljust(1024).encode('utf-8'))
        except:
            break
            
    conn.close()
    print(f"[DISCONNECT] Client {addr} terputus.")