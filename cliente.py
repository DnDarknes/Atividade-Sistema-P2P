import socket
import threading
import os

SERVER_IP = '127.0.0.1'
SERVER_PORT = 1234
CLIENT_PORT = 1235
PUBLIC_FOLDER = "./public"

def connect_to_server():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, SERVER_PORT))
        ip = socket.gethostbyname(socket.gethostname())
        client.sendall(f"JOIN {ip}\n".encode())
        print(client.recv(1024).decode())

        for filename in os.listdir(PUBLIC_FOLDER):
            path = os.path.join(PUBLIC_FOLDER, filename)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                client.sendall(f"CREATEFILE {filename} {size}\n".encode())
                print(client.recv(1024).decode())
        return client
    except Exception as e:
        print(f"[ERRO] Falha ao conectar com o servidor: {e}")
        return None

def listen_for_downloads():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', CLIENT_PORT))
        server.listen()
        print(f"[DOWNLOAD] Aguardando requisições na porta {CLIENT_PORT}...")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_download_request, args=(conn, addr)).start()
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar servidor de download: {e}")

def handle_download_request(conn, addr):
    try:
        msg = conn.recv(1024).decode().strip()
        print(f"[DOWNLOAD] Pedido de {addr[0]}: {msg}")
        parts = msg.split()

        if parts[0] == "GET":
            filename = parts[1]
            offset = int(parts[2].split('-')[0])
            filepath = os.path.join(PUBLIC_FOLDER, filename)

            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    f.seek(offset)
                    conn.sendall(f.read())
            else:
                print(f"[ERRO] Arquivo {filename} não encontrado na pasta /public.")
                conn.sendall(b"")

    except Exception as e:
        print(f"[ERRO] Erro ao enviar arquivo: {e}")
    finally:
        conn.close()

def search_file(client, pattern):
    try:
        client.sendall(f"SEARCH {pattern}\n".encode())
        response = client.recv(4096).decode()
        print("[RESULTADOS DA BUSCA]")
        print(response)
    except Exception as e:
        print(f"[ERRO] Falha na busca: {e}")

def download_file(ip, filename):
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((ip, CLIENT_PORT))
        conn.sendall(f"GET {filename} 0-\n".encode())

        os.makedirs("./downloads", exist_ok=True)
        path = os.path.join("./downloads", filename)

        with open(path, "wb") as f:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                f.write(data)

        print(f"[DOWNLOAD COMPLETO] Arquivo salvo em ./downloads/{filename}")
        conn.close()
    except Exception as e:
        print(f"[ERRO] Falha ao fazer download do arquivo: {e}")

def delete_file(client, filename):
    try:
        path = os.path.join(PUBLIC_FOLDER, filename)
        if os.path.isfile(path):
            os.remove(path)
            print(f"[ARQUIVO] {filename} removido da pasta pública.")
        else:
            print(f"[AVISO] Arquivo {filename} não encontrado na pasta pública.")

        client.sendall(f"DELETEFILE {filename}\n".encode())
        resposta = client.recv(1024).decode()
        print(resposta)
    except Exception as e:
        print(f"[ERRO] Falha ao deletar arquivo: {e}")

def start_client():
    client = connect_to_server()
    if not client:
        return

    threading.Thread(target=listen_for_downloads, daemon=True).start()

    while True:
        cmd = input("Comando (search, download, delete, leave): ").strip()

        if cmd.startswith("search"):
            _, pattern = cmd.split(maxsplit=1)
            search_file(client, pattern)

        elif cmd.startswith("download"):
            try:
                _, ip, filename = cmd.split(maxsplit=2)
                download_file(ip, filename)
            except ValueError:
                print("[ERRO] Uso correto: download <ip> <arquivo>")

        elif cmd.startswith("delete"):
            try:
                _, filename = cmd.split(maxsplit=1)
                delete_file(client, filename)
            except ValueError:
                print("[ERRO] Uso correto: delete <arquivo>")

        elif cmd == "leave":
            try:
                client.sendall("LEAVE\n".encode())
                print(client.recv(1024).decode())
                break
            except:
                print("[ERRO] Falha ao sair do servidor.")
                break

        else:
            print("[ERRO] Comando inválido.")

    client.close()

if __name__ == "__main__":
    start_client()