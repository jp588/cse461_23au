import socket
import struct
import random

# Constants
HOST = "127.0.0.1"
PORT = 12235
BYTES = 2048
HEADERSIZE = 12

STUDENT_ID = 786    # Remove later


def makePacket(payload, secret, step, student_id):
    # Align payload to 4-byte boundary
    payload_len = len(payload)
    header = struct.pack('!IIHH', payload_len, secret, step, student_id)
    padding = (4 - (payload_len % 4)) % 4
    payload += b'\0' * padding  # Add null byte padding to the message if needed

    # Concatenate header and payload
    return header + payload


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

            payload = struct.pack('!IIII', num, len_, udp_port, secretA)
            packet = makePacket(payload, secret, 2, student_id)
            listener.sendto(packet, client_addr)
            print(f"Sent response to {client_addr}")

        """
        # STAGE B2
        tcp_port = random.randint(1024, 65535)
        secretB = 100

        payload = struct.pack('!II', tcp_port, secretB)
        packet = makePacket(payload, secretA, 2, student_id)
        listener.sendto(packet, client_addr)
        print(f"Sent response (b2) to {client_addr}")
        """

    except socket.timeout:
        print("Did not receive any packets for 3 seconds. Closing connection.")
        listener.close()
        break
    except struct.error:
        print("Received data could not be unpacked. Possible incorrect format.")
        listener.close()
        break
    except Exception as e:
        print(f"Unexpected Error: {e}")
        listener.close()
        break


"""
# STAGE C

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Use TCP
listener.bind((HOST, tcp_port))
print(f"Server started on {HOST}:{tcp_port}")

listener.listen()
conn, client_addr = listener.accept()
with conn:
    print(f"Connected with {client_addr}")
    num2 = random.randint(1, 100)
    len2 = random.randint(1, 100)
    secretC = random.randint(0, 1000)
    c = random.randint(1, 256).to_bytes(1, 'big')
    payload = struct.pack('!IIIc', num2, len2, secretC, c)
    packet = makePacket(payload, secretB, 1, STUDENT_ID)
    conn.send(packet)
"""