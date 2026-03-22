import socket
import select
import os

HOST = '127.0.0.1'
PORT = 5002
os.makedirs('server_files', exist_ok=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
# Non-blocking untuk server agar select bekerja
server.setblocking(False)

inputs = [server]
print(f"[SELECT SERVER] Berjalan di {HOST}:{PORT}")

def broadcast(pesan, pengirim=None):
    for s in inputs:
        if s is not server and s is not pengirim:
            try: s.sendall(pesan.ljust(1024).encode('utf-8'))
            except: pass

while True:
    readable, _, _ = select.select(inputs, [], [])
    
    for s in readable:
        if s is server:
            conn, addr = s.accept()
            conn.setblocking(False)
            inputs.append(conn)
            print(f"[KONEKSI] {addr} terhubung.")
        else:
            try:
                header_data = s.recv(1024)
                if not header_data:
                    inputs.remove(s)
                    s.close()
                    continue
                
                header = header_data.decode('utf-8').strip()
                
                if header == '/list':
                    files = os.listdir('server_files')
                    s.sendall(f"[SERVER] File: {', '.join(files)}".ljust(1024).encode('utf-8'))
                    
                elif header.startswith('/upload'):
                    parts = header.split(' ')
                    filename, filesize = parts[1], int(parts[2])
                    # Jadikan blocking sementara agar file utuh
                    s.setblocking(True) 
                    with open(os.path.join('server_files', filename), 'wb') as f:
                        bytes_rec = 0
                        while bytes_rec < filesize:
                            chunk = s.recv(min(4096, filesize - bytes_rec))
                            f.write(chunk)
                            bytes_rec += len(chunk)
                    s.setblocking(False)
                    s.sendall(f"[SERVER] Upload {filename} sukses.".ljust(1024).encode('utf-8'))
                    broadcast(f"[SERVER] Klien mengunggah {filename}", s)
                    
                elif header.startswith('/download'):
                    filename = header.split(' ')[1]
                    filepath = os.path.join('server_files', filename)
                    if os.path.exists(filepath):
                        filesize = os.path.getsize(filepath)
                        s.setblocking(True)
                        s.sendall(f"/ready_download {filename} {filesize}".ljust(1024).encode('utf-8'))
                        with open(filepath, 'rb') as f:
                            while True:
                                bytes_read = f.read(4096)
                                if not bytes_read: break
                                s.sendall(bytes_read)
                        s.setblocking(False)
                    else:
                        s.sendall("[SERVER] File tidak ada!".ljust(1024).encode('utf-8'))
                else:
                    broadcast(f"[Pesan]: {header}", s)
            except Exception as e:
                inputs.remove(s)
                s.close()