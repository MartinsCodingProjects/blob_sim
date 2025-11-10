import socket

class RendererCommunicator:
    def __init__(self, network_settings):
        self.network_settings = network_settings
        self.mode = network_settings.get("mode", "socket")
        self.host = network_settings.get("host", "localhost")
        self.port = network_settings.get("port", 8888)
        if self.mode == "socket":
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
        
    def send_data(self, data_bytes):
        # Expects bytes, not JSON string
        if self.mode == "socket":
            # Send message length (4 bytes, big-endian) followed by the data
            message_length = len(data_bytes)
            length_header = message_length.to_bytes(4, byteorder='big')
            self.sock.sendall(length_header + data_bytes)
        
    def close(self):
        if self.mode == "socket":
            self.sock.close()