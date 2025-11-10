"""
Network Manager
Unified networking module handling both low-level TCP communication 
and high-level data management for the renderer.

Combines socket handling, data reception, processing, and statistics.
"""
import socket
import json
import threading
import time
from queue import Queue
import logging

logger = logging.getLogger("RENDERER_NETWORK")

# ==============================================================================
# LOW-LEVEL NETWORKING LAYER
# ==============================================================================

class NetworkReceiver:
    """
    Low-level TCP socket handler for receiving simulation data.
    Handles connection management, length-prefixed messaging, and JSON parsing.
    """
    
    def __init__(self, host="localhost", port=8888):
        """Initialize network receiver with connection settings"""
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.data_queue = Queue(maxsize=5)  # Small queue to prevent backlog
        self.server_thread = None
        self.connection_retry_delay = 1.0  # seconds
        self.socket_timeout = 1.0  # seconds
        self.client_connected = False  # Track connection state
        
    def start_server(self):
        """Start the TCP server in a separate thread"""
        self.running = True
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()
        logger.info(f"Network receiver started on {self.host}:{self.port}")
        
    def stop_server(self):
        """Stop the TCP server gracefully"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2.0)
        
        logger.info("Network receiver stopped")
        
    def _server_loop(self):
        """Main server loop with robust retry logic"""
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
        self.socket.settimeout(self.socket_timeout)
        
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
                    self._clear_queue()
                    logger.info("Client disconnected, queue cleared")
                except socket.timeout:
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
        """Handle incoming data with length-prefixed messaging"""
        client_socket.settimeout(self.socket_timeout)
        
        try:
            while self.running:
                try:
                    # Read 4-byte length header
                    length_data = self._recv_exact(client_socket, 4)
                    if not length_data:
                        logger.info("Client disconnected (no length header)")
                        break
                    
                    # Parse message length
                    message_length = int.from_bytes(length_data, byteorder='big')
                    
                    # Read exact message
                    message_data = self._recv_exact(client_socket, message_length)
                    if not message_data:
                        logger.warning("Client disconnected while reading message")
                        break
                        
                    # Parse JSON
                    try:
                        json_string = message_data.decode("utf-8")
                        parsed_data = json.loads(json_string)
                        
                        # Queue management - non-blocking
                        try:
                            self.data_queue.put_nowait(parsed_data)
                        except:
                            # Replace oldest data if queue full
                            try:
                                self.data_queue.get_nowait()
                                self.data_queue.put_nowait(parsed_data)
                                logger.debug("Queue full, replaced oldest data")
                            except:
                                logger.debug("Queue management failed, skipping frame")
                                
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.warning(f"Error parsing data: {e}")
                        
                except socket.timeout:
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
    
    def _recv_exact(self, sock, num_bytes):
        """Receive exactly num_bytes from socket"""
        data = b''
        while len(data) < num_bytes:
            try:
                chunk = sock.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data += chunk
            except socket.timeout:
                if not data:
                    raise
                sock.settimeout(None)
                continue
        return data
    
    def get_raw_data(self):
        """Get raw data from network queue"""
        try:
            return self.data_queue.get_nowait()
        except:
            return None
    
    def has_raw_data(self):
        """Check if raw data is available"""
        return not self.data_queue.empty()
    
    def get_queue_size(self):
        """Get current queue size"""
        return self.data_queue.qsize()
    
    def _clear_queue(self):
        """Clear all data from queue"""
        try:
            while not self.data_queue.empty():
                self.data_queue.get_nowait()
        except:
            pass
    
    def is_connected(self):
        """Check if client is connected"""
        return self.client_connected


# ==============================================================================
# HIGH-LEVEL DATA MANAGEMENT LAYER
# ==============================================================================

class NetworkManager:
    """
    High-level network data manager for the renderer.
    Manages data reception, processing, validation, statistics, and history.
    """
    
    def __init__(self, network_settings=None):
        """Initialize network manager with settings"""
        self.network_settings = network_settings or {}
        
        # Extract connection settings
        host = self.network_settings.get("host", "localhost")
        port = self.network_settings.get("port", 8888)
        
        # Initialize low-level network receiver
        self.receiver = NetworkReceiver(host=host, port=port)
        
        # High-level data management
        self.latest_data = None
        self.data_history = []
        self.max_history_size = 100
        
        # Statistics and monitoring
        self.total_updates_received = 0
        self.last_update_time = None
        self.start_time = None
        
        # Data validation
        self.expected_keys = ['sim_data', 'world_data', 'blobs_data', 'things_data']
        
        logger.info("Network Manager initialized")
    
    def start(self):
        """Start the network manager"""
        try:
            self.receiver.start_server()
            self.start_time = time.time()
            logger.info("Network Manager started - ready for simulation data")
        except Exception as e:
            logger.error(f"Failed to start network manager: {e}")
            raise
    
    def stop(self):
        """Stop the network manager"""
        try:
            self.receiver.stop_server()
            logger.info("Network Manager stopped")
        except Exception as e:
            logger.error(f"Error stopping network manager: {e}")
    
    def has_new_data(self):
        """Check if new simulation data is available"""
        return self.receiver.has_raw_data()
    
    def get_latest_data(self):
        """Get and process the latest simulation data"""
        if not self.has_new_data():
            return None
        
        try:
            # Get raw data from network layer
            raw_data = self.receiver.get_raw_data()
            if not raw_data:
                return None
            
            # Validate and process data
            processed_data = self._process_simulation_data(raw_data)
            if not processed_data:
                return None
            
            # Update statistics
            self.total_updates_received += 1
            self.last_update_time = time.time()
            
            # Store as latest data
            self.latest_data = processed_data
            
            # Add to history
            self._add_to_history(processed_data)
            
            # Log reception
            self._log_data_reception(processed_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing simulation data: {e}")
            return None
    
    def _process_simulation_data(self, raw_data):
        """Process and validate simulation data"""
        if not isinstance(raw_data, dict):
            logger.warning("Received non-dict data, skipping")
            return None
        
        # Basic validation
        missing_keys = [key for key in self.expected_keys if key not in raw_data]
        if missing_keys:
            logger.debug(f"Missing expected keys: {missing_keys}")
        
        # Data enrichment/processing can be added here
        processed_data = raw_data.copy()
        
        # Add processing timestamp
        processed_data['_processed_time'] = time.time()
        
        return processed_data
    
    def _add_to_history(self, data):
        """Add data to history buffer"""
        if len(self.data_history) >= self.max_history_size:
            self.data_history.pop(0)
        
        self.data_history.append({
            'timestamp': time.time(),
            'data': data
        })
    
    def _log_data_reception(self, data):
        """Log information about received data"""
        blobs_count = len(data.get('blobs_data', []))
        things_count = len(data.get('things_data', []))
        
        sim_data = data.get('sim_data', {})
        world_data = data.get('world_data', {})
        
        logger.debug(f"Update #{self.total_updates_received}: "
                    f"{blobs_count} blobs, {things_count} things, "
                    f"sim_time={world_data.get('current_sim_time', '?')}, "
                    f"day={world_data.get('day', '?')}, "
                    f"hour={world_data.get('hour', '?')}")
    
    def get_connection_status(self):
        """Get current connection and performance status"""
        return {
            'connected': self.receiver.is_connected(),
            'queue_size': self.receiver.get_queue_size(),
            'total_updates': self.total_updates_received,
            'last_update_time': self.last_update_time,
            'uptime_seconds': time.time() - self.start_time if self.start_time else 0
        }
    
    def get_statistics(self):
        """Get detailed network and data statistics"""
        status = self.get_connection_status()
        
        # Calculate update rate
        update_rate = 0
        if len(self.data_history) >= 2:
            time_span = self.data_history[-1]['timestamp'] - self.data_history[0]['timestamp']
            if time_span > 0:
                update_rate = len(self.data_history) / time_span
        
        return {
            **status,
            'history_size': len(self.data_history),
            'update_rate_hz': update_rate,
            'network_settings': self.network_settings,
            'expected_keys': self.expected_keys
        }
    
    def clear_history(self):
        """Clear the data history buffer"""
        self.data_history.clear()
        logger.debug("Data history cleared")
    
    def get_latest_simulation_time(self):
        """Get latest simulation time from received data"""
        if self.latest_data and 'world_data' in self.latest_data:
            return self.latest_data['world_data'].get('current_sim_time')
        return None
    
    def get_latest_world_state(self):
        """Get latest world state from received data"""
        if self.latest_data and 'world_data' in self.latest_data:
            return self.latest_data['world_data']
        return None
    
    def get_latest_blobs_data(self):
        """Get latest blobs data"""
        if self.latest_data and 'blobs_data' in self.latest_data:
            return self.latest_data['blobs_data']
        return []
    
    def get_latest_things_data(self):
        """Get latest things data"""
        if self.latest_data and 'things_data' in self.latest_data:
            return self.latest_data['things_data']
        return []


# ==============================================================================
# BACKWARDS COMPATIBILITY ALIASES
# ==============================================================================

# For any existing code that might import the old class name
DataManager = NetworkManager
DataReceiver = NetworkReceiver