from ursina import *
from data_receiver import DataReceiver
import time
import logging

# Set up logging for renderer
logger = logging.getLogger("RENDERER")

class BlobRenderer:
    def __init__(self, settings=None):
        # Initialize Ursina app
        self.app = Ursina()
        
        # Basic scene setup
        self.setup_scene()
        
        # Set up camera controls
        self.setup_camera_controls()
        
        # Data receiver for getting simulation data
        network_settings = settings.get_network_settings() if settings else {}
        self.data_receiver = DataReceiver(network_settings=network_settings)

        # Store current simulation data
        self.current_data = None
        
        # Dictionary to track rendered blobs
        self.blob_entities = {}
        
        logger.info("Blob Renderer initialized")
        
    def setup_scene(self):
        """Set up the basic 3D scene"""
        # Set up camera - high above to see the full world (50x50) plus edges
        camera.position = (25, 80, 25)  # Center of 50x50 world, high up
        camera.rotation_x = 80  # Look almost straight down
        
        # Add some basic lighting
        DirectionalLight().look_at(Vec3(1, -1, -1))
        
        # Semi-transparent ground
        ground = Entity(
            model='cube',
            color=color.rgba(50, 50, 50, 150),  # dark gray with alpha
            scale=(50, 0.1, 50),
            position=(25, -0.5, 25)
        )

        # Draw thick lines for cube edges (skeleton)
        edge_color = color.white
        thickness = 0.2
        # Four vertical edges
        for x in [0, 50]:
            for z in [0, 50]:
                Entity(model='cube', color=edge_color, scale=(thickness, 1, thickness), position=(x, 0, z))
        # Four horizontal edges (X axis)
        for z in [0, 50]:
            Entity(model='cube', color=edge_color, scale=(50, thickness, thickness), position=(25, 0, z))
        # Four horizontal edges (Z axis)
        for x in [0, 50]:
            Entity(model='cube', color=edge_color, scale=(thickness, thickness, 50), position=(x, 0, 25))

        # Add sky
        Sky()
        
        logger.info("Scene setup complete - camera positioned to view full 50x50 world")
    
    def setup_camera_controls(self):
        """Set up WASD movement and mouse look controls"""
        # Camera movement speed
        self.camera_speed = 20
        self.mouse_sensitivity = 100
        
        # Enable mouse look
        mouse.locked = True
        
        # Camera movement variables
        self.camera_rotation_y = 0
        self.camera_rotation_x = 80
        
        # Set initial camera rotation
        camera.rotation_x = self.camera_rotation_x
        camera.rotation_y = self.camera_rotation_y
        
        logger.info("Camera controls initialized - WASD to move, mouse to look, ESC to unlock mouse")
        
    def update_camera(self):
        """Update camera position and rotation based on input"""
        # Mouse look
        if mouse.locked:
            self.camera_rotation_y += mouse.velocity[0] * self.mouse_sensitivity
            self.camera_rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
            
            # Clamp vertical rotation to prevent flipping
            self.camera_rotation_x = max(-89, min(89, self.camera_rotation_x))
            
            camera.rotation_y = self.camera_rotation_y
            camera.rotation_x = self.camera_rotation_x
        
        # WASD movement
        move_vector = Vec3(0, 0, 0)
        
        if held_keys['w']:
            move_vector += camera.forward
        if held_keys['s']:
            move_vector -= camera.forward
        if held_keys['a']:
            move_vector -= camera.right
        if held_keys['d']:
            move_vector += camera.right
        if held_keys['space']:
            move_vector += camera.up
        if held_keys['shift']:
            move_vector -= camera.up
            
        # Apply movement
        if move_vector.length() > 0:
            move_vector = move_vector.normalized() * self.camera_speed * time.dt
            camera.position += move_vector
        
    def input(self, key):
        """Handle input events"""
        if key == 'escape':
            mouse.locked = not mouse.locked
            logger.info(f"Mouse {'locked' if mouse.locked else 'unlocked'}")
        
    def start(self):
        """Start the renderer and data receiver"""
        # Start data receiver server
        self.data_receiver.start_server()
        
        # Set up Ursina update function
        self.app.taskMgr.doMethodLater(0.016, self.update_scene, 'update_scene')  # ~60 FPS
        
        logger.info("Renderer started")
        
        # Run Ursina app (this blocks until app closes)
        self.app.run()
        
    def update_scene(self, task):
        """Update the 3D scene based on latest simulation data"""
        # Update camera controls
        self.update_camera()
        
        # Only process data if we have new data available
        if self.data_receiver.has_data():
            new_data = self.data_receiver.get_latest_data()
            if new_data:
                self.current_data = new_data
                self.process_simulation_data(self.current_data)
            
        # Continue the task
        return task.again
        
    def process_simulation_data(self, data):
        """Process simulation data and update 3D objects"""
        if not data:
            return
            
        # Debug: Log that we received data
        queue_size = self.data_receiver.get_queue_size()
        connected = self.data_receiver.is_connected()
        logger.debug(f"Processing simulation data with keys: {list(data.keys())} (queue: {queue_size}, connected: {connected})")
            
        # Extract blob data if present
        blobs = data.get('blobs_data', [])
        logger.debug(f"Found {len(blobs)} blobs to render")
        
        # Update or create blob entities
        current_blob_ids = set()
        
        for blob_data in blobs:
            blob_id = blob_data.get('id')
            position = blob_data.get('location', [0, 0, 0])  # Fixed: was 'position', should be 'location'
            state = blob_data.get('state', 'idle')
            
            logger.debug(f"Processing blob {blob_id} at position {position} with state {state}")
            current_blob_ids.add(blob_id)
            
            # Create or update blob entity
            if blob_id not in self.blob_entities:
                logger.debug(f"Creating new blob entity for ID {blob_id}")
                self.create_blob_entity(blob_id, position, state)
            else:
                logger.debug(f"Updating existing blob entity for ID {blob_id}")
                self.update_blob_entity(blob_id, position, state)
                
        # Remove blobs that no longer exist
        blob_ids_to_remove = set(self.blob_entities.keys()) - current_blob_ids
        for blob_id in blob_ids_to_remove:
            self.remove_blob_entity(blob_id)
            
    def create_blob_entity(self, blob_id, position, state):
        """Create a new 3D entity for a blob"""
        logger.debug(f"Creating blob entity for ID {blob_id}, position {position}, state {state}")
        
        # Choose color based on state
        blob_color = self.get_blob_color(state)
        logger.debug(f"Blob {blob_id} color will be {blob_color}")
        
        # Create 3D entity (sphere for blob)
        blob_entity = Entity(
            model='sphere',
            color=blob_color,
            scale=0.5,
            position=Vec3(position[0], position[2], position[1])  # x, z, y mapping
        )
        
        self.blob_entities[blob_id] = blob_entity
        logger.info(f"Successfully created blob entity {blob_id} at position {position} with color {blob_color}")
        logger.info(f"Total blob entities now: {len(self.blob_entities)}")
        
    def update_blob_entity(self, blob_id, position, state):
        """Update an existing blob entity"""
        blob_entity = self.blob_entities.get(blob_id)
        if blob_entity:
            # Update position
            blob_entity.position = Vec3(position[0], position[2], position[1])
            
            # Update color based on state
            blob_entity.color = self.get_blob_color(state)
            
    def remove_blob_entity(self, blob_id):
        """Remove a blob entity that no longer exists"""
        blob_entity = self.blob_entities.get(blob_id)
        if blob_entity:
            destroy(blob_entity)
            del self.blob_entities[blob_id]
            logger.debug(f"Removed blob {blob_id}")
            
    def get_blob_color(self, state):
        """Get color based on blob state"""
        state_colors = {
            'idle': color.blue,
            'walking': color.red,
            'walking_timed': color.orange,
            'resting': color.green
        }
        return state_colors.get(state, color.white)
        
    def cleanup(self):
        """Clean up resources"""
        self.data_receiver.stop_server()
        logger.info("Renderer cleanup complete")