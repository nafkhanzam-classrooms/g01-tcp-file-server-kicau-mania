import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 5001
os.makedirs('server_files', exist_ok=True)
clients = []

def broadcast(pesan, pengirim=None):
    for c in clients:
        if c != pengirim:
            try: c.sendall(pesan.ljust(1024).encode('utf-8'))
            except: pass

def handle_client(conn, addr):
    clients.append(conn)
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
                        f.write(chunk)
                        bytes_rec += len(chunk)
                conn.sendall(f"[SERVER] Upload {filename} sukses.".ljust(1024).encode('utf-8'))
                broadcast(f"[SERVER] Klien {addr[1]} mengunggah {filename}", conn)
                
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
                broadcast(f"[{addr[1]}]: {header}", conn)
        except:
            break
            
    clients.remove(conn)
    conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
print(f"[THREAD SERVER] Berjalan di {HOST}:{PORT}")

while True:
    conn, addr = server.accept()
    print(f"[KONEKSI] {addr} terhubung.")
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()