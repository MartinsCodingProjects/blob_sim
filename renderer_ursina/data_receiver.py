import socket
import json
import threading
import time
from queue import Queue
import logging

# Set up logging for renderer
logger = logging.getLogger("RENDERER_NET")

class DataReceiver:
    def __init__(self, network_settings=None):
        if network_settings is None:
            network_settings = {}
        self.host = network_settings.get("host", "localhost")
        self.port = network_settings.get("port", 8888)
        self.socket = None
        self.running = False
        self.data_queue = Queue(maxsize=5)  # Small queue to prevent backlog
        self.server_thread = None
        self.connection_retry_delay = 1.0  # seconds
        self.socket_timeout = 1.0  # seconds
        self.client_connected = False  # Track connection state
        
    def start_server(self):
        """Start the socket server in a separate thread"""
        self.running = True
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()
        logger.info(f"Data receiver started on {self.host}:{self.port}")
        
    def stop_server(self):
        """Stop the socket server gracefully"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2.0)
        
        logger.info("Data receiver stopped")
        
    def _server_loop(self):
        """Main server loop running in separate thread - robust with retry logic"""
        while self.running:
            try:
                self._setup_and_run_server()
            except Exception as e:
                if self.running:
                    logger.error(f"Server loop error: {e}")
                    logger.info(f"Retrying connection in {self.connection_retry_delay} seconds...")
                    time.sleep(self.connection_retry_delay)
                else:
                    break
        
        logger.info("Server loop ended")
    
    def _setup_and_run_server(self):
        """Set up and run server with proper error handling"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(self.socket_timeout)  # Non-blocking with timeout
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            logger.info(f"Listening for connections on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    logger.info(f"Connection from {address}")
                    self.client_connected = True
                    self._handle_client(client_socket)
                    self.client_connected = False
                    # Clear queue when client disconnects to prevent stale data processing
                    self._clear_queue()
                    logger.info("Cleared queue after client disconnect")
                except socket.timeout:
                    # Timeout is normal - just continue loop to check if still running
                    continue
                except socket.error as e:
                    if self.running:
                        logger.warning(f"Accept error: {e}")
                    break
                    
        except Exception as e:
            if self.running:
                logger.error(f"Server setup error: {e}")
            raise
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            self.socket = None
                
    def _handle_client(self, client_socket):
        """Handle incoming data from a client - robust with length-prefixed messages"""
        client_socket.settimeout(self.socket_timeout)
        
        try:
            while self.running:
                try:
                    # First, read the 4-byte length header
                    length_data = self._recv_exact(client_socket, 4)
                    if not length_data:
                        logger.info("Client disconnected (no length header)")
                        break
                    
                    # Parse the message length (4 bytes, big-endian)
                    message_length = int.from_bytes(length_data, byteorder='big')
                    
                    # Now read the exact message
                    message_data = self._recv_exact(client_socket, message_length)
                    if not message_data:
                        logger.warning("Client disconnected while reading message")
                        break
                        
                    # Decode and parse JSON
                    try:
                        # Parse the JSON message
                        json_string = message_data.decode("utf-8")
                        parsed_data = json.loads(json_string)
                        

                        # Non-blocking queue put
                        try:
                            self.data_queue.put_nowait(parsed_data)
                        except:
                            # Queue is full - remove oldest data and add new
                            try:
                                self.data_queue.get_nowait()  # Remove oldest
                                self.data_queue.put_nowait(parsed_data)  # Add new
                                logger.debug("Queue was full, replaced oldest data")
                            except:
                                logger.debug("Queue management failed, skipping frame")
                                
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.warning(f"Error parsing data: {e}")
                        
                except socket.timeout:
                    # Timeout is normal - continue loop to check if still running
                    continue
                except socket.error as e:
                    logger.warning(f"Client receive error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Client handling error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            logger.info("Client disconnected")
    
    def _recv_exact(self, sock, num_bytes):
        """Receive exactly num_bytes from socket, handling partial receives"""
        data = b''
        while len(data) < num_bytes:
            try:
                chunk = sock.recv(num_bytes - len(data))
                if not chunk:
                    return None  # Connection closed
                data += chunk
            except socket.timeout:
                # For timeout, continue trying if we haven't received any data yet
                # But if we've started receiving a message, we need to complete it
                if not data:
                    raise  # Re-raise timeout to continue main loop
                # If we have partial data, keep trying without timeout
                sock.settimeout(None)  # Remove timeout temporarily
                continue
        return data
            
    def get_latest_data(self):
        """Get the most recent data from the queue - non-blocking"""
        latest_data = None
        try:
            # Only get one item at a time to avoid draining entire queue
            latest_data = self.data_queue.get_nowait()
        except:
            # No data available
            pass
        
        return latest_data
        
    def has_data(self):
        """Check if there's data available"""
        return not self.data_queue.empty()
        
    def get_queue_size(self):
        """Get current queue size for debugging"""
        return self.data_queue.qsize()
        
    def _clear_queue(self):
        """Clear all data from queue"""
        try:
            while not self.data_queue.empty():
                self.data_queue.get_nowait()
        except:
            pass
            
    def is_connected(self):
        """Check if client is currently connected"""
        return self.client_connected