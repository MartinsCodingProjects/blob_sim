"""
Camera Controller
Handles all camera movement, rotation, and input for the 3D renderer.
"""
from ursina import *
import logging

logger = logging.getLogger("RENDERER_CAMERA")

class CameraController:
    """Manages camera movement, rotation, and input handling"""
    
    def __init__(self, settings=None):
        """Initialize camera controller with settings"""
        self.settings = settings
        
        # Camera movement settings
        self.movement_speed = 20.0
        self.mouse_sensitivity = 100.0
        self.smooth_factor = 0.1
        
        # Camera state
        self.rotation_y = 0
        self.rotation_x = 80
        self.target_position = Vec3(25, 80, 25)  # Default position
        self.target_rotation_x = self.rotation_x
        self.target_rotation_y = self.rotation_y
        
        # Input state
        self.mouse_locked = True
        self.movement_keys = {
            'w': False, 's': False, 'a': False, 'd': False,
            'space': False, 'shift': False
        }
        
        logger.info("Camera Controller initialized")
    
    def initialize(self):
        """Set up initial camera state"""
        # Set initial camera position and rotation
        camera.position = self.target_position
        camera.rotation_x = self.rotation_x
        camera.rotation_y = self.rotation_y
        
        # Enable mouse lock
        mouse.locked = self.mouse_locked
        
        logger.info(f"Camera initialized at position {camera.position}")
    
    def update(self):
        """Update camera position and rotation based on input"""
        # Handle mouse look
        self._update_mouse_look()
        
        # Handle movement
        self._update_movement()
        
        # Apply smooth movement
        self._apply_smooth_movement()
    
    def _update_mouse_look(self):
        """Update camera rotation based on mouse input"""
        if not self.mouse_locked:
            return
        
        # Get mouse movement
        mouse_delta_x = mouse.velocity[0] * self.mouse_sensitivity
        mouse_delta_y = mouse.velocity[1] * self.mouse_sensitivity
        
        # Update target rotation
        self.target_rotation_y += mouse_delta_x
        self.target_rotation_x -= mouse_delta_y
        
        # Clamp vertical rotation to prevent flipping
        self.target_rotation_x = max(-89, min(89, self.target_rotation_x))
    
    def _update_movement(self):
        """Update camera position based on keyboard input"""
        movement_vector = Vec3(0, 0, 0)
        
        # Calculate movement direction based on camera orientation
        if held_keys['w']:
            movement_vector += camera.forward
        if held_keys['s']:
            movement_vector -= camera.forward
        if held_keys['a']:
            movement_vector -= camera.right
        if held_keys['d']:
            movement_vector += camera.right
        if held_keys['space']:
            movement_vector += Vec3(0, 1, 0)  # World up
        if held_keys['shift']:
            movement_vector -= Vec3(0, 1, 0)  # World down
        
        # Apply movement speed and time delta
        if movement_vector.length() > 0:
            movement_vector = movement_vector.normalized() * self.movement_speed * time.dt
            self.target_position += movement_vector
    
    def _apply_smooth_movement(self):
        """Apply smooth interpolation to camera movement and rotation"""
        # Smooth rotation
        camera.rotation_y = lerp(camera.rotation_y, self.target_rotation_y, self.smooth_factor)
        camera.rotation_x = lerp(camera.rotation_x, self.target_rotation_x, self.smooth_factor)
        
        # Smooth position
        camera.position = lerp(camera.position, self.target_position, self.smooth_factor)
        
        # Update internal rotation tracking
        self.rotation_x = camera.rotation_x
        self.rotation_y = camera.rotation_y
    
    def handle_input(self, key):
        """Handle camera-related input events"""
        if key == 'escape':
            self.toggle_mouse_lock()
        elif key == 'r':
            self.reset_to_default_position()
        elif key == 'c':
            self.cycle_camera_mode()
    
    def toggle_mouse_lock(self):
        """Toggle mouse lock state"""
        self.mouse_locked = not self.mouse_locked
        mouse.locked = self.mouse_locked
        logger.info(f"Mouse {'locked' if self.mouse_locked else 'unlocked'}")
    
    def reset_to_default_position(self):
        """Reset camera to default overhead position"""
        self.target_position = Vec3(25, 80, 25)
        self.target_rotation_x = 80
        self.target_rotation_y = 0
        logger.info("Camera reset to default position")
    
    def cycle_camera_mode(self):
        """Cycle between different camera modes (overhead, free, follow, etc.)"""
        # Placeholder for different camera modes
        logger.info("Camera mode cycling not yet implemented")
    
    def set_position(self, position):
        """Set camera position directly"""
        self.target_position = Vec3(position)
    
    def set_rotation(self, rotation_x, rotation_y):
        """Set camera rotation directly"""
        self.target_rotation_x = rotation_x
        self.target_rotation_y = rotation_y
    
    def get_position(self):
        """Get current camera position"""
        return camera.position
    
    def get_rotation(self):
        """Get current camera rotation"""
        return (camera.rotation_x, camera.rotation_y)
    
    def cleanup(self):
        """Clean up camera controller resources"""
        mouse.locked = False
        logger.info("Camera Controller cleanup complete")