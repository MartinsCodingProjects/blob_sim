"""
Core Application Manager
Manages the main Ursina application lifecycle and coordinates all subsystems.
"""
from ursina import *
import logging
from camera.camera_controller import CameraController
from scene.scene_manager import SceneManager
from entities.entity_manager import EntityManager
from networking.network_manager import NetworkManager
from ui.ui_manager import UIManager

logger = logging.getLogger("RENDERER_APP")

class RendererApplication:
    """Main application class that coordinates all renderer subsystems"""
    
    def __init__(self, settings=None):
        """Initialize the renderer application with all subsystems"""
        logger.info("Initializing Renderer Application...")
        
        # Store settings
        self.settings = settings
        
        # Initialize Ursina app with custom blob simulation icon
        self.app = Ursina(icon='textures/blob_sim.ico')
        
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
        
        # Network manager for communication
        network_settings = self.settings.get_network_settings() if self.settings else {}
        self.data_manager = NetworkManager(network_settings)
        
        # UI manager for overlays and debug info
        self.ui_manager = UIManager(self.settings)
        
        logger.info("All subsystems initialized")
    
    def start(self):
        """Start the renderer application"""
        logger.info("Starting Renderer Application...")
        
        # Start subsystems
        self.scene_manager.setup_scene()
        self.camera_controller.initialize()
        self.data_manager.start()
        self.ui_manager.setup_ui()
        
        # Set up input handling - make this instance the global input handler
        self._setup_input_handling()
        
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
    
    def _setup_input_handling(self):
        """Set up Ursina input handling to route to this class"""
        # Create an invisible entity that handles input
        class InputHandler(Entity):
            def __init__(self, app_instance):
                super().__init__()
                self.app_instance = app_instance
            
            def input(self, key):
                self.app_instance.input(key)
        
        # Create the input handler entity
        self.input_handler = InputHandler(self)
        
        logger.debug("Input handling set up - key presses will be routed to RendererApplication")
    
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
        
        # Update UI with current information
        self.ui_manager.update_debug_info(
            camera_controller=self.camera_controller,
            entity_manager=self.entity_manager, 
            network_manager=self.data_manager
        )
        
        # Continue the task
        return task.again
    
    def input(self, key):
        """Handle global input events"""
        # Debug: Log all key presses to see if input system is working
        # logger.debug(f"Key pressed: {key}")
        
        # Delegate input to appropriate subsystems
        self.camera_controller.handle_input(key)
        
        # Global application inputs
        if key == 'f1':
            self._toggle_debug_info()
        elif key == 'f11':
            self._toggle_fullscreen()
    
    def _toggle_debug_info(self):
        """Toggle debug information display"""
        self.ui_manager.toggle_debug_panel()
        logger.info("Debug panel toggled")
    
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
        
        if hasattr(self, 'ui_manager'):
            self.ui_manager.cleanup()
        
        if hasattr(self, 'input_handler'):
            destroy(self.input_handler)
        
        logger.info("Renderer Application cleanup complete")