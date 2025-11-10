"""
Data Manager
Manages network communication and data flow from simulation to renderer.
"""
import logging
import time
from ..data_receiver import DataReceiver

logger = logging.getLogger("RENDERER_DATA")

class DataManager:
    """Manages data reception and processing from the simulation"""
    
    def __init__(self, network_settings=None):
        """Initialize data manager with network settings"""
        self.network_settings = network_settings or {}
        
        # Data receiver for network communication
        self.data_receiver = DataReceiver(network_settings=self.network_settings)
        
        # Data state
        self.latest_data = None
        self.data_history = []  # Optional: keep history for analysis
        self.max_history_size = 100  # Limit history to prevent memory issues
        
        # Statistics
        self.total_updates_received = 0
        self.last_update_time = None
        
        logger.info("Data Manager initialized")
    
    def start(self):
        """Start the data receiver"""
        try:
            self.data_receiver.start_server()
            logger.info("Data Manager started - listening for simulation data")
        except Exception as e:
            logger.error(f"Failed to start data receiver: {e}")
            raise
    
    def stop(self):
        """Stop the data receiver"""
        try:
            self.data_receiver.stop_server()
            logger.info("Data Manager stopped")
        except Exception as e:
            logger.error(f"Error stopping data receiver: {e}")
    
    def has_new_data(self):
        """Check if new data is available"""
        return self.data_receiver.has_data()
    
    def get_latest_data(self):
        """Get the most recent data from simulation"""
        if not self.has_new_data():
            return None
        
        try:
            # Get new data
            new_data = self.data_receiver.get_latest_data()
            
            if new_data:
                # Update statistics
                self.total_updates_received += 1
                self.last_update_time = time.time()
                
                # Store as latest data
                self.latest_data = new_data
                
                # Add to history (optional)
                self._add_to_history(new_data)
                
                # Log data reception
                self._log_data_reception(new_data)
                
                return new_data
            
        except Exception as e:
            logger.error(f"Error processing received data: {e}")
            return None
        
        return None
    
    def _add_to_history(self, data):
        """Add data to history buffer"""
        if len(self.data_history) >= self.max_history_size:
            # Remove oldest entry
            self.data_history.pop(0)
        
        # Add new entry with timestamp
        self.data_history.append({
            'timestamp': time.time(),
            'data': data
        })
    
    def _log_data_reception(self, data):
        """Log information about received data"""
        if not data:
            return
        
        # Extract key information for logging
        blobs_count = len(data.get('blobs_data', []))
        things_count = len(data.get('things_data', []))
        
        # Get simulation time if available
        sim_data = data.get('sim_data', {})
        sim_time = sim_data.get('current_sim_time', 'unknown')
        
        # Get world info if available
        world_data = data.get('world_data', {})
        day = world_data.get('day', '?')
        hour = world_data.get('hour', '?')
        
        logger.debug(f"Received update #{self.total_updates_received}: "
                    f"{blobs_count} blobs, {things_count} things, "
                    f"sim_time={sim_time}, day={day}, hour={hour}")
    
    def get_connection_status(self):
        """Get current connection status"""
        return {
            'connected': self.data_receiver.is_connected(),
            'queue_size': self.data_receiver.get_queue_size(),
            'total_updates': self.total_updates_received,
            'last_update_time': self.last_update_time
        }
    
    def get_statistics(self):
        """Get detailed statistics about data reception"""
        status = self.get_connection_status()
        
        # Add more detailed stats
        stats = {
            **status,
            'history_size': len(self.data_history),
            'network_settings': self.network_settings
        }
        
        # Calculate update rate if we have enough history
        if len(self.data_history) >= 2:
            first_time = self.data_history[0]['timestamp']
            last_time = self.data_history[-1]['timestamp']
            time_span = last_time - first_time
            update_rate = len(self.data_history) / time_span if time_span > 0 else 0
            stats['update_rate_hz'] = update_rate
        
        return stats
    
    def clear_history(self):
        """Clear the data history buffer"""
        self.data_history.clear()
        logger.debug("Data history cleared")
    
    def get_latest_simulation_time(self):
        """Get the latest simulation time from received data"""
        if self.latest_data and 'sim_data' in self.latest_data:
            return self.latest_data['sim_data'].get('current_sim_time')
        return None
    
    def get_latest_world_state(self):
        """Get the latest world state from received data"""
        if self.latest_data and 'world_data' in self.latest_data:
            return self.latest_data['world_data']
        return None