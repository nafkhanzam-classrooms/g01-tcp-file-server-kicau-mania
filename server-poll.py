import socket
import select
import os
import sys

if not hasattr(select, 'poll'):
    print("Sistem OS Anda (Windows) tidak mendukung select.poll(). Gunakan WSL/Linux.")
    sys.exit()

HOST = '127.0.0.1'
PORT = 5003
os.makedirs('server_files', exist_ok=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
server.setblocking(False)

poller = select.poll()
poller.register(server, select.POLLIN)
fd_to_socket = {server.fileno(): server}

print(f"[POLL SERVER] Berjalan di {HOST}:{PORT}")

def broadcast(pesan, pengirim_fd=None):
    for fd, s in fd_to_socket.items():
        if s is not server and fd != pengirim_fd:
            try: s.sendall(pesan.ljust(1024).encode('utf-8'))
            except: pass

while True:
    events = poller.poll()
    
    for fd, flag in events:
        s = fd_to_socket[fd]
        
        if flag & select.POLLIN:
            if s is server:
                conn, addr = s.accept()
                conn.setblocking(False)
                poller.register(conn, select.POLLIN)
                fd_to_socket[conn.fileno()] = conn
                print(f"[KONEKSI] {addr} terhubung.")
            else:
                try:
                    header_data = s.recv(1024)
                    if not header_data:
                        poller.unregister(s)
                        del fd_to_socket[fd]
                        s.close()
                        continue
                    
                    header = header_data.decode('utf-8').strip()
                    
                    if header == '/list':
                        files = os.listdir('server_files')
                        s.sendall(f"[SERVER] File: {', '.join(files)}".ljust(1024).encode('utf-8'))
                        
                    elif header.startswith('/upload'):
                        parts = header.split(' ')
                        filename, filesize = parts[1], int(parts[2])
                        s.setblocking(True)
                        with open(os.path.join('server_files', filename), 'wb') as f:
                            bytes_rec = 0
                            while bytes_rec < filesize:
                                chunk = s.recv(min(4096, filesize - bytes_rec))
                                f.write(chunk)
                                bytes_rec += len(chunk)
                        s.setblocking(False)
                        s.sendall(f"[SERVER] Upload {filename} sukses.".ljust(1024).encode('utf-8'))
                        broadcast(f"[SERVER] Klien mengunggah {filename}", fd)
                        
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
                        broadcast(f"[Pesan]: {header}", fd)
                except:
                    poller.unregister(s)
                    del fd_to_socket[fd]
                    s.close()