import struct
from constants import PKT_CONNECT

def unpack_response(response):
    """
    Unpacks a response from the server. Extracts the status and message.
    """
    if len(response) < 2:
        raise ValueError("Invalid response length")
    status = struct.unpack("!B", response[0:1])[0]
    message_length = struct.unpack("!B", response[1:2])[0]
    message = response[2:2 + message_length].decode()
    return status, message

def pack_credentials(username, password, auth_max_length):
    """
    Packs user credentials into a structured format for authentication.
    """
    username_bytes = username.encode('utf-8')[:auth_max_length]
    password_bytes = password.encode('utf-8')[:auth_max_length]
    username_length = len(username_bytes)
    password_length = len(password_bytes)
    packed_data = struct.pack(
        f"!B{auth_max_length}sB{auth_max_length}s",
        username_length,
        username_bytes.ljust(auth_max_length, b'\x00'),
        password_length,
        password_bytes.ljust(auth_max_length, b'\x00')
    )
    return struct.pack("!B", PKT_CONNECT) + packed_data
