import socket
import threading

HOST = '0.0.0.0'
PORT = 1234

all_files = {}

def handle_client(conn, addr):
    ip_address = addr[0]
    print(f"Novo cliente conectado: {ip_address}")

    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            print(f"[{ip_address}] > {data}")
            parts = data.split()

            if parts[0] == "JOIN":
                conn.sendall("CONFIRMJOIN\n".encode())
                all_files[ip_address] = []

            elif parts[0] == "CREATEFILE":
                filename = parts[1]
                size = int(parts[2])
                file_info = {"filename": filename, "size": size}
                if ip_address not in all_files:
                    all_files[ip_address] = []
                all_files[ip_address].append(file_info)
                conn.sendall(f"CONFIRMCREATEFILE {filename}\n".encode())

            elif parts[0] == "DELETEFILE":
                filename = parts[1]
                if ip_address in all_files:
                    all_files[ip_address] = [
                        f for f in all_files[ip_address] if f["filename"] != filename
                    ]
                conn.sendall(f"CONFIRMDELETEFILE {filename}\n".encode())

            elif parts[0] == "SEARCH":
                pattern = parts[1]
                result = []
                for ip, files in all_files.items():
                    for f in files:
                        if pattern in f["filename"]:
                            result.append(f"FILE {f['filename']} {ip} {f['size']}")
                response = "\n".join(result) + "\n"
                conn.sendall(response.encode())

            elif parts[0] == "LEAVE":
                if ip_address in all_files:
                    del all_files[ip_address]
                conn.sendall("CONFIRMLEAVE\n".encode())
                break

    except Exception as e:
        print(f"[ERRO] Problema com o cliente {ip_address}: {e}")

    finally:
        conn.close()
        print(f"Cliente desconectado: {ip_address}")
        if ip_address in all_files:
            del all_files[ip_address]

def start_server():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen()
        print(f"Servidor P2P ouvindo na porta {PORT}...")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar servidor: {e}")

if __name__ == "__main__":
    start_server()