import socket
import threading

# เปิดพอร์ตจำลองที่เครื่องหลักเพื่อรอรับข้อมูลจาก Docker
LOCAL_PORT = 5430  
REMOTE_HOST = "db.vcmiglzjvckjjyiivwys.supabase.co"
REMOTE_PORT = 5432

def handle_client(client_socket):
    try:
        # เชื่อมต่อไปยัง Supabase ผ่าน IPv6 (AF_INET6)
        remote_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        remote_socket.connect((REMOTE_HOST, REMOTE_PORT))
    except Exception as e:
        print(f"[-] Failed to connect to Supabase: {e}")
        client_socket.close()
        return

    def forward(src, dst):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                dst.sendall(data)
        except Exception:
            pass
        finally:
            src.close()
            dst.close()

    # รับส่งข้อมูลสองฝั่งพร้อมกัน
    threading.Thread(target=forward, args=(client_socket, remote_socket), daemon=True).start()
    threading.Thread(target=forward, args=(remote_socket, client_socket), daemon=True).start()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", LOCAL_PORT))
    server.listen(5)
    print(f"[+] Local DB Proxy is running on port {LOCAL_PORT} -> {REMOTE_HOST}:{REMOTE_PORT} (IPv6)")
    try:
        while True:
            client_sock, addr = server.accept()
            handle_client(client_sock)
    except KeyboardInterrupt:
        print("\n[!] Shutting down proxy.")
    finally:
        server.close()

if __name__ == "__main__":
    main()