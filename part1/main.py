import socket
import struct
import time

# Constants
# HOST = "attu2.cs.washington.edu"
HOST = "127.0.0.1"
PORT = 12235
STUDENT_ID = 786
HEADERSIZE = 12

def makePacket(payload, secret, step):
    # Align payload to 4-byte boundary
    payload_len = len(payload)
    header = struct.pack('!IIHH', payload_len, secret, step, STUDENT_ID)
    padding = (4 - (payload_len % 4)) % 4
    payload += b'\0' * padding  # Add null byte padding to the message if needed

    # Concatenate header and payload
    return header + payload

def packetToStr(packet):
    s = "+++++++++++++++++++++++++\n"
    for i in range(int(len(packet) / 4)):
        s += str(packet[4*i]) + " "
        s += str(packet[4*i+1]) + " "
        s += str(packet[4*i+2]) + " "
        s += str(packet[4*i+3]) + "\n"
    s += "-------------------------"
    return s


print("Step a1")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)

# Create packet
packet = makePacket(b'hello world\0', 0, 1)

# Send data
socket_address = (HOST, PORT)
sock.sendto(packet, socket_address)
print("Sent packet {} to {}".format(packetToStr(packet), socket_address))
print()


print("Step a2")
try:
    data, server = sock.recvfrom(2048)
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
print()

print("Step b1")
socket_address = (HOST, udp_port)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(.5)

# Sending packets
for packet_id in range(num):
    payload_data = b'\0' * len_
    packet_id_packed = struct.pack('!I', packet_id)  # Packing packet_id into 4 bytes.
    message = packet_id_packed + payload_data  # Concatenating packet_id and payload.

    packet = makePacket(message, secretA, 1)

    # Calculating padding and adding it to the message.
    # padding = (4 - (len(message) % 4)) % 4
    # packet += b'\0' * padding

    # packet = makePacket(message, secretA, 1)

    # Awaiting acknowledgments
    while True:  # Resending logic until ACK is received.
        # Send packet.
        sock.sendto(packet, socket_address)
        print("Sent packet {} to {}".format(packetToStr(packet), socket_address))

        # Wait for ACK.
        try:
            ack_data, server = sock.recvfrom(2048)
            # Extract and validate ACK.
            acked_packet_id, = struct.unpack('!I', ack_data[HEADERSIZE:])  # Assuming header is 12 bytes.
            if acked_packet_id == packet_id:
                print(f"ACK received for packet_id: {packet_id}")
                break  # Exit the loop if correct ACK received.
        except socket.timeout:
            print(f"Timeout. Resending packet_id: {packet_id}")
            # Avoiding network congestion
            time.sleep(0.5)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            exit(1)  # Exit the program if an error occurs.
print()


print("Step b2")
try:
    data, server = sock.recvfrom(2048)
    tcp_port, secretB = struct.unpack('!II', data[HEADERSIZE:])
    print(f"Received TCP port: {tcp_port}, secretB: {secretB}")
except socket.timeout:
    print("Did not receive TCP port and secretB. Exiting.")
finally:
    sock.close()
print()


print("Step c1")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_address = (HOST, tcp_port)
sock.connect(socket_address)
data = sock.recv(2048)
print(f"data: {data}")

print ("Step c2")
num2, len2, secretC, c, _, _, _ = struct.unpack('!IIIcccc', data[HEADERSIZE:])
print(f"num2: {num2}, len2: {len2}, secretC: {secretC}, c: {c}")


print("Step d1")
for _ in range(num2):
    payload = c * len2
    packet = makePacket(payload, secretC, 1)
    sock.send(packet)
    print(f"Sent packet {packetToStr(packet)} to {socket_address}")

print("Step d2")
data = sock.recv(2048)
print(f"data: {data}")
secretD = struct.unpack('!I', data[HEADERSIZE:])[0]
print(f"secretD: {secretD}")

sock.close()
