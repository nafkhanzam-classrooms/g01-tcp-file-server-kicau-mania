[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mRmkZGKe)
# Network Programming - Assignment G01

## Anggota Kelompok
| Nama           | NRP        | Kelas     |
| ---            | ---        | ----------|
| Ageng Prayogo | 5025241225 | D |
| Shafa Maulana Efendi | 5025241227 | D |

## Link Youtube (Unlisted)
Link ditaruh di bawah ini
```
https://youtu.be/Fyn59hWw8Ck
```

## Penjelasan Program
### 1. Klien (`client.py`) - Arsitektur Asynchronous Full-Duplex
Program klien dituntut untuk dapat melakukan komunikasi *Full-Duplex* (mengirim dan menerima secara bersamaan). Masalah utamanya adalah fungsi `input()` dari keyboard dan fungsi `recv()` dari socket jaringan sama-sama bersifat *Blocking* (menghentikan sementara eksekusi program). Jika keduanya diletakkan dalam satu *while loop* sekuensial, terminal klien akan membeku (*freeze*) dan tidak bisa menerima pesan saat sedang menunggu input pengguna.

Solusinya adalah menerapkan **Multithreading**. Program memecah siklus *looping* menjadi dua jalur yang berjalan paralel:
1. **Daemon Thread:** Menjalankan *loop* khusus untuk mengeksekusi `recv()`. Proses ini selalu mendengarkan jaringan secara asinkron tanpa mengganggu layar utama.
2. **Main Thread:** Menjalankan *loop* khusus untuk menangani `input()` dan memanggil `sendall()`.

**Potongan Kode Inti:**
```python
import threading

def receive_messages(sock):
    while True:
        header = sock.recv(1024)
        if not header: break

client.connect((HOST, PORT))

threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

while True:
    pesan = input("> ")
    client.sendall(pesan.ljust(1024).encode('utf-8'))
```

---

### 2. Server Sync (`server-sync.py`) - Arsitektur Single-Threaded Blocking
Server menggunakan metode **Loop Bersarang (Nested Loop)** yang menjadi akar permasalahan *blocking*. Saat program memanggil `accept()` di *loop* luar, koneksi klien pertama diterima. Program kemudian turun dan terjebak di dalam *loop* bagian dalam untuk melayani I/O (`recv()`) dari klien tersebut. Karena program tertahan di *loop* dalam, server tidak bisa mengeksekusi kembali perintah `accept()`. Akibatnya, koneksi dari klien-klien berikutnya hanya akan menumpuk di dalam antrean Sistem Operasi (*TCP Backlog*) dan tidak dilayani sampai klien pertama memutus koneksi.

**Potongan Kode Inti:**
```python
while True:
    conn, addr = server.accept() 
    

    while True: 
        data = conn.recv(1024)
        if not data: 
            break
            
```

---

### 3. Server Thread (`server-thread.py`) - Arsitektur Thread-Per-Connection
Arsitektur *Concurrent Server* menyelesaikan masalah antrean pada Server Sync dengan memecah *Nested Loop* menggunakan abstraksi OS. *Loop* utama murni hanya untuk mengeksekusi perintah `accept()`. Setiap kali ada koneksi baru yang masuk, socket tersebut langsung didelegasikan ke dalam sebuah **OS Thread baru** yang berisi *loop* `recv()` miliknya sendiri. Dengan isolasi memori ini, *loop* utama dapat langsung berputar kembali dengan sangat cepat untuk menerima klien berikutnya. Kelemahan arsitektur ini adalah *overhead* komputasi; jika ada puluhan ribu klien, sistem operasi akan kewalahan melakukan *Context Switching* untuk mengelola puluhan ribu *thread* secara bersamaan.

**Potongan Kode Inti:**
```python
import threading

def handle_client(conn):
    while True:
        data = conn.recv(1024) 
        if not data: break

while True:
    conn, addr = server.accept()
    
    threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
```

---

### 4. Server Select (`server-select.py`) - Arsitektur I/O Multiplexing (User-Space)
Beroperasi dengan model **Single-Threaded Non-Blocking** untuk menghemat memori. Alih-alih membuat banyak *thread*, seluruh socket (termasuk server utama dan klien) diatur menjadi *non-blocking* dan dimasukkan ke dalam sebuah list (`inputs`). Fungsi `select()` digunakan untuk menahan eksekusi program (menghemat CPU), dan HANYA akan melepas blokade jika OS mendeteksi adanya transisi state menjadi *Readable* (ada koneksi/data masuk). Meskipun efisien secara memori, arsitektur ini memiliki batasan pada kompleksitas waktu **$O(N)$**. Ketika OS melaporkan adanya aktivitas, program harus melakukan iterasi linier (mengecek ulang seluruh list menggunakan *for-loop*) untuk memvalidasi socket mana yang sebenarnya aktif.

**Potongan Kode Inti:**
```python
import select

server.setblocking(False) 
inputs = [server]         
while True:
    readable, _, _ = select.select(inputs, [], [])
    
    for s in readable:
        if s is server:
            conn, addr = s.accept()
            conn.setblocking(False)
            inputs.append(conn)
        else:
            data = s.recv(1024)
            if not data:
                inputs.remove(s)
```

---

### 5. Server Poll (`server-poll.py`) - Arsitektur Kernel-Level Multiplexing
Sistem operasi berbasis POSIX (Linux/macOS). Mendelegasikan pengecekan array di level aplikasi, program ini memanfaatkan fungsi `poll()` untuk mendaftarkan *File Descriptor* (ID Socket) dan *Event Mask* secara langsung ke dalam memori **Kernel Sistem Operasi**. Saat terjadi lalu lintas jaringan, *Event Loop* memanggil `poller.poll()`. Kernel OS secara instan mengembalikan ID spesifik dari socket yang berstatus aktif saja. Hal ini menghasilkan efisiensi waktu pemrosesan **$O(1)$ (*direct lookup*)**, di mana server tidak perlu membuang *clock cycle* untuk memvalidasi ratusan atau ribuan socket lain yang sedang dalam keadaan *idle*.

**Potongan Kode Inti:**
```python
import select

poller = select.poll()
poller.register(server, select.POLLIN)
fd_to_socket = {server.fileno(): server}

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
            else:
                data = s.recv(1024)
```
## Screenshot Hasil

![image](https://github.com/user-attachments/assets/912d0d50-29d1-4129-8efb-7530799305d9)
![image](https://github.com/user-attachments/assets/0c2d3cbe-9453-4db1-82f6-46ad4d5a671c)
![image](https://github.com/user-attachments/assets/3494990e-673f-425a-9547-79bd1e1cc3d2)
![image](https://github.com/user-attachments/assets/076efeee-d806-471f-bbe9-dde7dad4f3f4)
![image](https://github.com/user-attachments/assets/51d30d76-c5e4-4fef-823f-21d4b165b03c)
![image](https://github.com/user-attachments/assets/6f85ee7c-3086-4938-8a8f-8ea0c25231a0)


