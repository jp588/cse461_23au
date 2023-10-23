import socket
import struct
import random

# Constants
HOST = "127.0.0.1"
PORT = 12235
BYTES = 2048
HEADERSIZE = 12
TIMEOUT = 3
PROBABILITY = 80  # Stage B
STUDENT_ID = 786    # Remove later
received_packets = set()  # Stage B

def makePacket(payload, secret, step, student_id):
    # Align payload to 4-byte boundary
    payload_len = len(payload)
    header = struct.pack('!IIHH', payload_len, secret, step, student_id)
    padding = (4 - (payload_len % 4)) % 4
    payload += b'\0' * padding  # Add null byte padding to the message if needed

    # Concatenate header and payload
    return header + payload

def checkZero(data, payload_len):
    # The initial 4 bytes are the packet_id, so we start checking from byte 5
    remaining_payload = data[HEADERSIZE + 4:HEADERSIZE + payload_len]
    for byte in remaining_payload:
        if byte != 0:
            return False
    return True

def randomResponse(data, client_addr):
    i = random.randint(0, 100)
    if i < PROBABILITY:
        # Extract packet ID and send acknowledgment
        packet_id, = struct.unpack('!I', data[HEADERSIZE:HEADERSIZE+4])
        ack_payload = struct.pack('!I', packet_id)
        ack_packet = makePacket(ack_payload, secretA, 2, STUDENT_ID)
        listener.sendto(ack_packet, client_addr)
        print(f"Sent ACK for packet {packet_id} to {client_addr}")
        received_packets.add(packet_id)
    else:
        print(f"Did not send ACK to {client_addr}")

listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP
listener.bind((HOST, PORT))
print(f"Server started on {HOST}:{PORT}")

print("Stage A")
while True:
    try:
        # Setting the 3-second timeout
        listener.settimeout(TIMEOUT)  # 30 for now

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
            num = random.randint(1, 20)
            len_ = random.randint(1, 100)
            udp_port = random.randint(1024, 65535)
            secretA = random.randint(0, 1000)

            payload = struct.pack('!IIII', num, len_, udp_port, secretA)
            packet = makePacket(payload, secret, 2, student_id)
            listener.sendto(packet, client_addr)
            print(f"Sent response to {client_addr}")

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
    finally:
        print("Stage A done.")
        listener.close()
        break

print("Stage B")

listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP
listener.bind((HOST, udp_port))

while True:
    try:
        if len(received_packets) == num:
            break
        listener.settimeout(TIMEOUT)
        data, client_addr = listener.recvfrom(BYTES)
        payload_len, secret, step, student_id = struct.unpack('!IIHH', data[:HEADERSIZE])

        # Check the header
        if step != 1:
            print(f"Invalid step: {step} from {client_addr}")
            listener.close()
            break

        if secret != secretA:
            print(f"Invalid secret: {secret} from {client_addr}")
            listener.close()
            break

        if (len(data) - HEADERSIZE) % 4 != 0:
            print(f"Received invalid data length from {client_addr}: {len(data)-HEADERSIZE}")
            print(len(data))
            listener.close()
            break

        if not checkZero(data, payload_len):  # Only for stage B
            print(f"Invalid payload from {client_addr}. Non-zero bytes found after payload_len.")
            listener.close()
            break

        packet_id, = struct.unpack('!I', data[HEADERSIZE:HEADERSIZE+4])

        if packet_id not in received_packets:
            if randomResponse(data, client_addr):
                received_packets.add(packet_id)
        else:
            # This handles retransmission. If the packet is received again, acknowledge without the randomness.
            randomResponse(data, client_addr)

    except socket.timeout:
        print(f"Did not receive any packets for {TIMEOUT} seconds. Closing connection to {client_addr}")
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

tcp_port = random.randint(1024, 65535)
secretB = 100

payload = struct.pack('!II', tcp_port, secretB)
packet = makePacket(payload, secretA, 2, student_id)
listener.sendto(packet, client_addr)
print(f"Sent response (b2) to {client_addr}")
print("Stage B done.")

print("Stage C")
tcp_port = 47241
secretB = 100

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Use TCP
listener.bind((HOST, tcp_port))
print(f"Server started on {HOST}:{tcp_port}")

listener.listen()
conn, client_addr = listener.accept()
with conn:
    print(f"Connected with {client_addr}")
    data = conn.recv(BYTES)  # TODO: verify payload from client

    num2 = random.randint(1, 100)
    len2 = random.randint(1, 100)
    secretC = random.randint(0, 1000)
    c = random.randint(1, 256).to_bytes(1, 'big')
    payload = struct.pack('!IIIc', num2, len2, secretC, c)
    packet = makePacket(payload, secretC, 1, STUDENT_ID)  # TODO: Change step?
    conn.send(packet)


print("Stage D")

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Use TCP
listener.bind((HOST, tcp_port))  # TODO: Change port
print(f"Server started on {HOST}:{tcp_port}")

listener.listen()
conn, client_addr = listener.accept()
with conn:
    print(f"Connected with {client_addr}")
    data = conn.recv(BYTES)  # TODO: Maybe num2 * len2?
    # TODO: Verify payload from client

    secretD = random.randint(0, 1000)
    payload = struct.pack('!I', secretD)
    packet = makePacket(payload, secretD, 1, STUDENT_ID)  # TODO: Change step?
    conn.send(packet)
