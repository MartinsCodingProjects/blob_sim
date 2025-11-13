from .entities import world
from .networking.renderer_communicator import RendererCommunicator
from .networking.data_serializer import DataSerializer

import time
import threading
from queue import Queue

import logging
logger = logging.getLogger("SIM")

class SimEngine:
    def __init__(self, settings):
        logger.info("Simulation engine initialized")
        self.settings = settings
        self.simulation_time = 0.0 # Simulation time in hours
        self.sim_delta_time = 0.0  # Delta time for current sim step
        self.max_simulation_time = settings.SIMULATION_MAX_TIME # Test for 24 simulation hours (1 day)
        self.time_multiplier = settings.SIMULATION_TIME_MULTIPLIER if settings else 1.0  # Real-time to sim-time ratio
        self.last_update_time = time.time()  # for real-time tracking
        self.paused = self.settings.paused  # Simulation paused state

        # for renderer updates
        self.last_renderer_update_time = 0.0
        self.renderer_update_interval = 1.0 / 10.0  # 10 FPS for renderer updates (less aggressive than 60 FPS)
        self.start_paused = False

        # Network thread setup for renderer communication
        self.renderer_data_queue = Queue(maxsize=10)  # Limit queue to 10 items to prevent backlog
        self.network_thread = None
        self.network_running = False

        self.current_realtime = time.time()
        self.starting_realtime = self.current_realtime

        # counters
        self.sim_ticks = 0
        self.renderer_ticks = 0

    def start(self):
        logger.info("Simulation engine started")
        
        # Start network thread for renderer communication
        if self.settings.renderer in ['ursina']:
            self.start_network_thread()
        
        # Check if we should start paused (but don't block initialization)
        if self.start_paused:
            print("DEBUG SIM: Starting in paused mode")
        else:
            print("DEBUG SIM: Starting in running mode")
        
        self.world = world.World(settings=self.settings)
        self.world.create_initial_population()
        self.sim_loop()

    def sim_loop(self):
        logger.info("Simulation Loop started")
        while self.simulation_time < self.max_simulation_time:
            # Check pause state directly from settings every iteration
            if self.settings.paused:
                print(f"DEBUG SIM: Simulation paused, waiting...")
                while self.settings.paused:
                    time.sleep(0.1)  # wait until unpaused
                print(f"DEBUG SIM: Simulation resumed!")

            self.sim_ticks += 1
            
            # handle real life timing and set sim time and deltas accordingly
            self.handle_timings()

            # init world update based on timings
            self.world.update(self.sim_delta_time)

            # Send data to renderer at X FPS based on real-life time
            if self.current_realtime - self.last_renderer_update_time >= self.renderer_update_interval:
                self.update_and_send_renderer_data()

            # Small sleep to prevent 100% CPU usage
            time.sleep(0.001)
        
        logger.info(f"Simulation ended at time {self.simulation_time:.2f} hours")
        
        # Stop network thread
        self.stop_network_thread()

    def handle_timings(self):
        self.current_realtime = time.time()

        real_delta_time = self.current_realtime - self.last_update_time
        
        # Update the last update time AFTER calculating delta
        self.last_update_time = self.current_realtime

        # Cap real delta time to prevent huge jumps for more acurate simulation
        capped_real_delta_time = min(real_delta_time, 0.1) # max delta time jump of 0.1 seconds
        
        # convert to sim time 
        sim_delta_time = capped_real_delta_time * self.time_multiplier
        self.simulation_time += sim_delta_time
        self.sim_delta_time = sim_delta_time

    def prepare_renderer_data(self):
        renderer_data = {}
        renderer_data["sim_data"] = {
            "starting_realtime": self.starting_realtime,
            "current_realtime": self.current_realtime,
            "sim_ticks": self.sim_ticks,
            "renderer_ticks": self.renderer_ticks,
        }
        self.world.update_renderer_world_data()
        renderer_data.update(self.world.renderer_data_world)
        return renderer_data
    
    def update_and_send_renderer_data(self):
        if self.settings.renderer == 'ursina':
            self.renderer_ticks += 1
            renderer_data = self.prepare_renderer_data()
            serialized_data = DataSerializer.serialize_renderer_data(renderer_data)
            
            # Non-blocking: just queue the data for network thread
            try:
                self.renderer_data_queue.put_nowait(serialized_data)
            except:
                # Queue is full - drop oldest data and add new data to prevent backlog
                try:
                    self.renderer_data_queue.get_nowait()  # Remove oldest item
                    self.renderer_data_queue.put_nowait(serialized_data)  # Add newest item
                    #logger.debug("Renderer data queue full, dropped oldest frame")
                except:
                    logger.debug("Renderer data queue full, skipping frame")
            self.last_renderer_update_time = self.current_realtime
        elif self.settings.renderer == 'pygame':
            self.renderer_ticks += 1
            renderer_data = self.prepare_renderer_data()
            
            # Non-blocking: just queue the data for network thread
            try:
                self.renderer_data_queue.put_nowait(renderer_data)
            except:
                # Queue is full - drop oldest data and add new data to prevent backlog
                try:
                    self.renderer_data_queue.get_nowait()  # Remove oldest item
                    self.renderer_data_queue.put_nowait(renderer_data)  # Add newest item
                    #logger.debug("Renderer data queue full, dropped oldest frame")
                except:
                    logger.debug("Renderer data queue full, skipping frame")
            self.last_renderer_update_time = self.current_realtime

    def start_network_thread(self):
        """Start the network thread for renderer communication"""
        self.network_running = True
        self.network_thread = threading.Thread(target=self._network_sender_loop, daemon=True)
        self.network_thread.start()
        logger.info("Network thread started for renderer communication")
    
    def stop_network_thread(self):
        """Stop the network thread"""
        self.network_running = False
        
        # Clear any remaining queue data to prevent renderer from processing old data
        while not self.renderer_data_queue.empty():
            try:
                self.renderer_data_queue.get_nowait()
            except:
                break
        
        if self.network_thread and self.network_thread.is_alive():
            self.network_thread.join(timeout=2.0)
        logger.info("Network thread stopped")
    
    def _network_sender_loop(self):
        """Network thread loop - handles all renderer communication"""
        renderer_communicator = None
        
        try:
            # Initialize renderer communicator in network thread
            renderer_communicator = RendererCommunicator(self.settings.get_network_settings())
            logger.info("Renderer communicator initialized in network thread")
            
            while self.network_running:
                try:
                    # Get data from queue with timeout
                    data = self.renderer_data_queue.get(timeout=1.0)
                    
                    # Send data (this may block, but won't affect simulation)
                    renderer_communicator.send_data(data)
                    
                except:
                    # Timeout or queue empty - continue loop
                    continue
                    
        except Exception as e:
            logger.error(f"Network thread error: {e}")
            # Continue running even if connection fails
            
        finally:
            # Clean up renderer communicator
            if renderer_communicator:
                try:
                    renderer_communicator.close()
                except:
                    pass
            logger.info("Network thread cleanup complete")