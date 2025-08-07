import socket  # noqa: F401


PONG = b'+PONG\r\n'

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")
    
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    client_conn, _ = server_socket.accept() # wait for client

    while True: 
        request: bytes = client_conn.recv(512)
        data: str = request.decode()

        if 'ping' in data.lower():
            client_conn.sendall(PONG)

    


if __name__ == "__main__":
    main()
