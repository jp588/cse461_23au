import socket
import struct

HOST = "attu2.cs.washington.edu"  # The server's hostname or IP address
PORT = 12235  # The port used by the server

step = 1  # Step a1
student_id = 786  # Last 3 digits of your student number
message = 'hello world'  # Message to send
payload_len = len(message)

padding = (4 - (payload_len % 4)) % 4
message += '\0' * padding  # Add null byte padding to the message if needed
payload_len += padding

# psecret for stage a
psecret = 0

# Construct header
header = struct.pack('!IIH H', payload_len, psecret, step, student_id)

# Concatenate header and payload
packet = header + message.encode('utf-8')



# UDP socket
server_address = (HOST, PORT)  # IP and port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)

try:
    # Send data
    sock.sendto(packet, server_address)

    data, server = sock.recvfrom(2048)
    num, len_, udp_port, secretA = struct.unpack('!IIII', data)

    print(f"Received data from {server}:")
    print(f"num: {num}, len: {len_}, udp_port: {udp_port}, secretA: {secretA}")
except socket.timeout:
    print("Request timed out")
except struct.error:
    print("Received data could not be unpacked. Possible incorrect format.")
finally:
    # Close the socket
    sock.close()
