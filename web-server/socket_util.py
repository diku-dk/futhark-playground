import json
import socket

def get_byte_length(i):
    length = 1
    while(i>>(length<<3) > 0):
        length+=1
    return length

def bytes_to_int(b):
    i = b[0]
    for idx in range(1, len(b)):
        i = i << 8
        i = i | b[idx]
    return i

def int_to_bytes(i, length=0):
    if (length == 0):
        length = get_byte_length(i)
    b = []
    for idx in range(1, length+1):
        b.append((i >> ((length<<3) - (idx<<3))) & 0b11111111)
    return bytes(b)

def encode_length_of_bytes(value_bytes: bytes):
    # length is encoded the same way as length in asn1
    # https://www.oss.com/asn1/resources/asn1-made-simple/asn1-quick-reference/basic-encoding-rules.html#Lengths
    length = 0
    for byte in value_bytes:
        length += 1
    if length < 128:
        return int_to_bytes(length, 1)
    
    length_bytes = 0
    for i in range(length):
        if (length>>(i<<3) <= 0):
            break
        length_bytes+=1
    return int_to_bytes((((0b1 << 7) | length_bytes) << (length_bytes<<3)) | length, length_bytes + 1)

def read_incoming(socket: socket.socket):
    size = bytes_to_int(socket.recv(1))
    if size >= 128:
        size = bytes_to_int(socket.recv(size & 0b01111111))
    buffer = b''
    while len(buffer) < size:
        buffer += socket.recv(4096) 
    return buffer
    

def send_body(socket: socket.socket, body: dict, error=""):
    body = json.dumps({"body": body, "error": error}).encode("utf-8")
    size = encode_length_of_bytes(body)
    socket.send(size + body)