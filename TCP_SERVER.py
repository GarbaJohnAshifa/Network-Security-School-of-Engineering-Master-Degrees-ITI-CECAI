import socket

HOST = "10.8.0.3"
PORT = 9001
import threading

store = {}
store_lock = threading.Lock()



def handle_client(conn, addr):
    print(f"Connection from {addr} has been established!")

    with conn:
        buffer = b""

        while True:
            data = conn.recv(1024)
            if not data:
                break

            buffer += data

            # Process every complete newline-terminated command
            while b"\n" in buffer:
                raw_command, buffer = buffer.split(b"\n", 1)

                try:
                    command = raw_command.decode("ascii")
                except UnicodeDecodeError:
                    response = "ERR"
                else:
                    if command.endswith("\r"):
                      command = command[:-1]

                    if not command.isprintable():
                      response = "ERR"
                    elif command == "PING":
                        response = "PONG"

                    elif command.startswith("ECHO "):
                        response = command.split(" ", 1)[1]

                    elif command.startswith("SET "):
                        parts = command.split(" ", maxsplit=2)

                        if len(parts) == 3 and parts[1] != "" and parts[2] != "":
                            key = parts[1]
                            value = parts[2]

                            with store_lock:
                                store[key] = value

                            response = "OK"
                        else:
                            response = "ERR"

                    elif command.startswith("GET "):
                        parts = command.split()

                        if len(parts) == 2:
                            key = parts[1]

                            with store_lock:
                                response = store.get(key, "NOT_FOUND")
                        else:
                            response = "ERR"

                    else:
                        response = "ERR"

                conn.sendall((response + "\n").encode("ascii"))

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        
        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True,
            )
            client_thread.start()


if __name__ == "__main__":
    main()