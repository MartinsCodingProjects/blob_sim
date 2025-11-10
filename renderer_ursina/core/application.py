"""
Core Application Manager
Manages the main Ursina application lifecycle and coordinates all subsystems.
"""
from ursina import *
import logging
from ..camera.camera_controller import CameraController
from ..scene.scene_manager import SceneManager
from ..entities.entity_manager import EntityManager
from ..networking.data_manager import DataManager

logger = logging.getLogger("RENDERER_APP")

class RendererApplication:
    """Main application class that coordinates all renderer subsystems"""
    
    def __init__(self, settings=None):
        """Initialize the renderer application with all subsystems"""
        logger.info("Initializing Renderer Application...")
        
        # Store settings
        self.settings = settings
        
        # Initialize Ursina app
        self.app = Ursina()
        
        # Initialize subsystems
        self._initialize_subsystems()
        
        # Application state
        self.running = False
        
        logger.info("Renderer Application initialized successfully")
    
    def _initialize_subsystems(self):
        """Initialize all renderer subsystems in proper order"""
        # Scene must be initialized first
        self.scene_manager = SceneManager(self.settings)
        
        # Camera controller
        self.camera_controller = CameraController(self.settings)
        
        # Entity manager for handling simulation objects
        self.entity_manager = EntityManager(self.settings)
        
        # Data manager for network communication
        network_settings = self.settings.get_network_settings() if self.settings else {}
        self.data_manager = DataManager(network_settings)
        
        logger.info("All subsystems initialized")
    
    def start(self):
        """Start the renderer application"""
        logger.info("Starting Renderer Application...")
        
        # Start subsystems
        self.scene_manager.setup_scene()
        self.camera_controller.initialize()
        self.data_manager.start()
        
        # Set up main update loop
        self.app.taskMgr.doMethodLater(0.016, self._update_loop, 'main_update')  # ~60 FPS
        
        self.running = True
        logger.info("Renderer Application started - entering main loop")
        
        # Run Ursina app (blocks until window is closed)
        try:
            self.app.run()
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        finally:
            self.cleanup()
    
    def _update_loop(self, task):
        """Main update loop - coordinates all subsystem updates"""
        if not self.running:
            return task.done
        
        # Update camera
        self.camera_controller.update()
        
        # Check for new simulation data
        if self.data_manager.has_new_data():
            simulation_data = self.data_manager.get_latest_data()
            if simulation_data:
                # Update entities based on simulation data
                self.entity_manager.update_from_simulation_data(simulation_data)
        
        # Update entity animations/states
        self.entity_manager.update()
        
        # Continue the task
        return task.again
    
    def input(self, key):
        """Handle global input events"""
        # Delegate input to appropriate subsystems
        self.camera_controller.handle_input(key)
        
        # Global application inputs
        if key == 'f1':
            self._toggle_debug_info()
        elif key == 'f11':
            self._toggle_fullscreen()
    
    def _toggle_debug_info(self):
        """Toggle debug information display"""
        # Implementation for debug overlay
        logger.info("Debug info toggled")
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        # Implementation for fullscreen toggle
        logger.info("Fullscreen toggled")
    
    def cleanup(self):
        """Clean up all resources and stop subsystems"""
        logger.info("Cleaning up Renderer Application...")
        
        self.running = False
        
        # Stop subsystems in reverse order
        if hasattr(self, 'data_manager'):
            self.data_manager.stop()
        
        if hasattr(self, 'entity_manager'):
            self.entity_manager.cleanup()
        
        if hasattr(self, 'scene_manager'):
            self.scene_manager.cleanup()
        
        if hasattr(self, 'camera_controller'):
            self.camera_controller.cleanup()
        
        logger.info("Renderer Application cleanup complete")