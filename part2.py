import socket

# Constants
HOST = "127.0.0.1"
PORT = 12235
BYTES = 2048

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.bind((HOST, PORT))

while True:
    try:
        connection, client_addr = listener.accept()
        try:
            data = connection.recv(BYTES)
            print(f"Received data from {client_addr}:")
            print(f"Data: {data}")
        finally:
            connection.close()
    except:
        listener.close()
