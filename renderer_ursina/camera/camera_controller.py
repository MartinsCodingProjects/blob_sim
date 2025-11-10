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
        self.movement_speed = self.settings.movement_speed if settings else 20.0
        self.movement_speed_boost = self.movement_speed * (self.settings.movement_speed_boost_factor if settings else 2.0)
        self.mouse_sensitivity = self.settings.mouse_sensitivity if settings else 100.0
        self.smooth_factor = self.settings.smooth_factor if settings else 0.1

        # Camera state
        self.rotation = self.settings.default_camera_rotation if settings else (81.5, 0)
        self.rotation_y = self.rotation[1]
        self.rotation_x = self.rotation[0]
        self.target_position = Vec3(self.settings.default_camera_position)  # Default position
        self.target_rotation_x = self.rotation_x
        self.target_rotation_y = self.rotation_y
        
        # Input state
        self.mouse_locked = False  # Start with mouse unlocked (cursor visible)
        self.mouse_look_active = False  # Only look around when mouse button is held
        self.temp_mouse_locked = False  # Temporarily lock mouse while looking
        self.movement_keys = {
            'w': False, 's': False, 'a': False, 'd': False,
            'space': False, 'shift': False
        }
        
        # Speed boost toggle
        self.speed_boost_active = False
        self.current_speed = self.movement_speed
        
        logger.info("Camera Controller initialized - hold left mouse button to look around")
    
    def initialize(self):
        """Set up initial camera state"""
        # Set initial camera position and rotation
        camera.position = self.target_position
        camera.rotation_x = self.rotation_x
        camera.rotation_y = self.rotation_y
        
        # Start with mouse unlocked (cursor visible)
        mouse.locked = self.mouse_locked
        
        logger.info(f"Camera initialized at position {camera.position} (mouse cursor visible)")
    
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
        # Check if left mouse button is currently held
        left_mouse_held = held_keys['left mouse']
        
        # Two modes: locked (legacy) or left mouse button
        if self.mouse_locked:
            # Legacy mode: mouse is locked, always update rotation
            self.mouse_look_active = True
        else:
            # New mode: only look around when left mouse button is held
            self.mouse_look_active = left_mouse_held
            
            # Handle temporary mouse locking for smooth camera movement
            if left_mouse_held and not self.temp_mouse_locked:
                # Just started holding mouse button - lock cursor temporarily
                mouse.locked = True
                self.temp_mouse_locked = True
                # logger.debug("Mouse temporarily locked for camera look")
            elif not left_mouse_held and self.temp_mouse_locked:
                # Released mouse button - unlock cursor
                mouse.locked = False
                self.temp_mouse_locked = False
                # logger.debug("Mouse unlocked - cursor visible")
        
        # Only update camera rotation if conditions are met
        if not self.mouse_look_active:
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
        
        # Apply movement speed (current speed includes boost if active) and time delta
        if movement_vector.length() > 0:
            movement_vector = movement_vector.normalized() * self.current_speed * time.dt
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
        # Debug: Log camera input to see if keys are reaching the controller
        # logger.debug(f"Camera controller received key: {key}")
        
        if key == 'escape':
            self.toggle_mouse_lock()
        elif key == 'r':
            self.reset_to_default_position()
        elif key == 'c':
            self.cycle_camera_mode()
        elif key == 'tab':
            # Alternative key for mouse lock toggle
            self.toggle_mouse_lock()
        elif key == 'f':  # Use F key for speed boost instead of caps lock
            # logger.debug("F key detected - calling toggle_speed_boost")
            self.toggle_speed_boost()
    
    def toggle_mouse_lock(self):
        """Toggle mouse lock state (for alternative control mode)"""
        self.mouse_locked = not self.mouse_locked
        mouse.locked = self.mouse_locked
        
        if self.mouse_locked:
            logger.info("Mouse locked - move mouse to look around (old style)")
        else:
            logger.info("Mouse unlocked - hold left mouse button to look around (new style)")
    
    def reset_to_default_position(self):
        """Reset camera to default overhead position"""
        self.target_position = Vec3(self.settings.default_camera_position if self.settings else (50, 80, 50))
        self.target_rotation_x = self.settings.default_camera_rotation[0] if self.settings else -45
        self.target_rotation_y = self.settings.default_camera_rotation[1] if self.settings else 0
        logger.info("Camera reset to default position")
    
    def toggle_speed_boost(self):
        """Toggle between normal and boosted movement speed"""
        self.speed_boost_active = not self.speed_boost_active
        
        if self.speed_boost_active:
            self.current_speed = self.movement_speed_boost
            logger.info(f"Speed boost ON - movement speed: {self.current_speed:.1f}")
        else:
            self.current_speed = self.movement_speed
            logger.info(f"Speed boost OFF - movement speed: {self.current_speed:.1f}")
    
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
        self.temp_mouse_locked = False
        logger.info("Camera Controller cleanup complete")