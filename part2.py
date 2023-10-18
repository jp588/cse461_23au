import socket
import struct
import random

# Constants
HOST = "127.0.0.1"
PORT = 12235
BYTES = 2048
HEADERSIZE = 12

listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP
listener.bind((HOST, PORT))
print(f"Server started on {HOST}:{PORT}")

while True:
    try:
        # Setting the 3-second timeout
        listener.settimeout(30)  # 30 for now

        data, client_addr = listener.recvfrom(BYTES)
        print(f"Received {data} from {client_addr}")

        payload_len, secret, step, student_id = struct.unpack('!IIHH', data[:HEADERSIZE])

        if secret != 0:
            print(f"Invalid secret: {secret} from {client_addr}")
            listener.close()
            break

        if len(data) % 4 != 0:
            print(f"Invalid buffer length: {len(data)} from {client_addr}")
            listener.close()
            break

        if payload_len != 12 or len(data) - HEADERSIZE != payload_len:  # Not sure
            print(f"Invalid payload_len: {payload_len} or mismatched packet length from {client_addr}")
            listener.close()
            break

        if step != 1:
            print(f"Invalid step: {step} from {client_addr}")
            listener.close()
            break

        if data[HEADERSIZE:HEADERSIZE+payload_len] == b'hello world\0':  # Only for stage A
            print(f"Received 'hello world' from {client_addr}")

            # Make a header
            header = struct.pack('!IIHH', payload_len, secret, step + 1, student_id)

            # Generate random response data as per specification
            # Not sure about the range
            num = random.randint(1, 100)
            len_ = random.randint(1, 100)
            udp_port = random.randint(1024, 65535)
            secretA = random.randint(0, 1000)

            response = struct.pack('!IIII', num, len_, udp_port, secretA)

            padding = (4 - (payload_len % 4)) % 4
            response += b'\0' * padding  # Add null byte padding to the message if needed

            packet = header + response

            listener.sendto(packet, client_addr)
            print(f"Sent response to {client_addr}")

    except socket.timeout:
        print("Did not receive any packets for 3 seconds. Closing connection.")
        listener.close()
        break
    except Exception as e:
        print(f"Error: {e}")
