import socket
import struct
import time

HOST = "attu2.cs.washington.edu"
PORT = 12235

step = 1  # Step a1
student_id = 786  # Last 3 digits of your student number
message = b'hello world'  # Message to send
payload_len = len(message)

padding = (4 - (payload_len % 4)) % 4
message += b'\0' * padding  # Add null byte padding to the message if needed
payload_len += padding

# psecret for stage a
psecret = 0

# Construct header
header = struct.pack('!IIH H', payload_len, psecret, step, student_id)

# Concatenate header and payload
packet = header + message
print(packet)


def makePacket(payload, secret, step):

    # Align payload to 4-byte boundary
    payload_len = len(payload)
    padding = (4 - (payload_len % 4)) % 4
    payload += b'\0' * padding  # Add null byte padding to the message if needed
    payload_len += + padding

    # Construct header
    header = struct.pack('!IIHH', payload_len, secret, step, STUDENT_ID)

    # Concatenate header and payload
    packet = header + payload
    print(packet)
    return packet



# UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)

try:
    # Send data
    sock.sendto(packet, (HOST, PORT))

    data, server = sock.recvfrom(2048)
    HEADERSIZE = 12
    num, len_, udp_port, secretA = struct.unpack('!IIII', data[HEADERSIZE:])

    print(f"Received data from {server}:")
    print(f"num: {num}, len: {len_}, udp_port: {udp_port}, secretA: {secretA}")
except socket.timeout:
    print("Request timed out")
except struct.error:
    print("Received data could not be unpacked. Possible incorrect format.")
finally:
    # Close the socket
    sock.close()




# Step b1
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)

acknowledged_packets = set()
while len(acknowledged_packets) < num:
    # Sending packets
    for packet_id in range(num):
        if packet_id not in acknowledged_packets:
            # Construct packet with packet_id and len_ zeros as payload
            packet_data = struct.pack('!I', packet_id) + b'\0' * len_
            sock.sendto(packet_data, (HOST, udp_port))
            print(f"Sent packet {packet_id} to {(HOST, udp_port)}")

    # Awaiting acknowledgments
    try:
        data, server = sock.recvfrom(2048)
        acked_packet_id, = struct.unpack('!I', data)
        acknowledged_packets.add(acked_packet_id)
        print(f"Received acknowledgment for packet {acked_packet_id}")
    except socket.timeout:
        print("Acknowledgment not received. Resending packets...")

    # Avoiding network congestion
    time.sleep(0.5)

# Step b2
try:
    data, server = sock.recvfrom(2048)
    tcp_port, secretB = struct.unpack('!II', data)
    print(f"Received TCP port: {tcp_port}, secretB: {secretB}")
except socket.timeout:
    print("Did not receive TCP port and secretB. Exiting.")
finally:
    sock.close()
