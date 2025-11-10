"""
Blob Entity
Represents a single blob in the 3D renderer with visual representation and animations.
"""
from ursina import *
import logging

logger = logging.getLogger("RENDERER_BLOB")

class BlobEntity:
    """3D representation of a simulation blob"""
    
    def __init__(self, blob_id, blob_data, settings=None):
        """Initialize blob entity from simulation data"""
        self.blob_id = blob_id
        self.settings = settings
        
        # Extract data from simulation
        self.name = blob_data.get('name', f'Blob_{blob_id}')
        self.location = blob_data.get('location', [0, 0, 0])
        self.state = blob_data.get('state', 'idle')
        self.direction = blob_data.get('direction', [0, 0, 0])
        self.color_data = blob_data.get('color', None)
        self.alive = blob_data.get('alive', True)
        
        # 3D entity
        self.entity = None
        self.scale = 0.5  # Default blob size
        
        # Animation properties
        self.target_position = Vec3(self.location[0], self.location[2], self.location[1])
        self.animation_speed = 5.0  # How fast to interpolate to target position
        
        # State colors
        self.state_colors = {
            'idle': color.blue,
            'walking': color.red,
            'walking_timed': color.orange,
            'resting': color.green,
            'dead': color.gray
        }
        
        # Create the 3D entity
        self._create_entity()
        
        logger.debug(f"Created blob entity {self.name} (ID: {blob_id})")
    
    def _create_entity(self):
        """Create the 3D Ursina entity for this blob"""
        # Determine initial color
        entity_color = self._get_state_color()
        
        # Create sphere entity
        self.entity = Entity(
            model='sphere',
            color=entity_color,
            scale=self.scale,
            position=self.target_position
        )
        
        # Optional: Add name label (can be toggled)
        # self._create_name_label()
    
    def _create_name_label(self):
        """Create floating name label above blob (optional)"""
        # This could be used for debugging or identification
        pass
    
    def update_from_data(self, blob_data):
        """Update blob entity from new simulation data"""
        # Update position
        new_location = blob_data.get('location', self.location)
        if new_location != self.location:
            self.location = new_location
            self.target_position = Vec3(new_location[0], new_location[2], new_location[1])
        
        # Update state
        new_state = blob_data.get('state', self.state)
        if new_state != self.state:
            self.state = new_state
            self._update_color()
        
        # Update direction
        self.direction = blob_data.get('direction', self.direction)
        
        # Update alive status
        new_alive = blob_data.get('alive', self.alive)
        if new_alive != self.alive:
            self.alive = new_alive
            self._update_visual_state()
    
    def update(self):
        """Update blob entity (called each frame)"""
        if not self.entity:
            return
        
        # Smooth position interpolation
        self._update_position()
        
        # Update animations based on state
        self._update_animations()
        
        # Handle death state
        if not self.alive:
            self._handle_death_visual()
    
    def _update_position(self):
        """Smoothly interpolate to target position"""
        if self.entity.position != self.target_position:
            # Use lerp for smooth movement
            lerp_factor = self.animation_speed * time.dt
            self.entity.position = lerp(self.entity.position, self.target_position, lerp_factor)
    
    def _update_animations(self):
        """Update visual animations based on current state"""
        if self.state == 'walking' or self.state == 'walking_timed':
            # Slight bobbing animation for walking
            self._animate_walking()
        elif self.state == 'resting':
            # Gentle pulsing for resting
            self._animate_resting()
        else:
            # Idle - no special animation
            pass
    
    def _animate_walking(self):
        """Animate walking state with slight bobbing"""
        # Simple bobbing effect
        bob_amount = 0.1
        bob_speed = 8.0
        base_y = self.target_position.y
        self.entity.y = base_y + sin(time.time() * bob_speed) * bob_amount
    
    def _animate_resting(self):
        """Animate resting state with gentle pulsing"""
        # Gentle scale pulsing
        pulse_amount = 0.1
        pulse_speed = 2.0
        base_scale = self.scale
        scale_modifier = 1 + sin(time.time() * pulse_speed) * pulse_amount
        self.entity.scale = base_scale * scale_modifier
    
    def _update_color(self):
        """Update entity color based on current state"""
        if self.entity:
            self.entity.color = self._get_state_color()
    
    def _get_state_color(self):
        """Get color based on current state"""
        if not self.alive:
            return self.state_colors['dead']
        
        # Use custom color if provided, otherwise use state color
        if self.color_data:
            # Convert color data to Ursina color if needed
            return self._convert_color_data(self.color_data)
        
        return self.state_colors.get(self.state, color.white)
    
    def _convert_color_data(self, color_data):
        """Convert simulation color data to Ursina color"""
        # Handle different color formats from simulation
        if isinstance(color_data, (list, tuple)) and len(color_data) >= 3:
            # RGB or RGBA
            if len(color_data) == 3:
                return color.rgb(*color_data)
            else:
                return color.rgba(*color_data)
        elif isinstance(color_data, str):
            # Color name or hex
            return getattr(color, color_data, color.white)
        else:
            return color.white
    
    def _update_visual_state(self):
        """Update visual representation based on alive status"""
        if not self.alive:
            # Make blob semi-transparent and gray when dead
            if self.entity:
                self.entity.color = color.rgba(128, 128, 128, 100)
                self.entity.scale = self.scale * 0.8  # Slightly smaller
    
    def _handle_death_visual(self):
        """Handle visual effects for dead blobs"""
        # Could add particle effects, fading, etc.
        pass
    
    def get_position(self):
        """Get current 3D position"""
        return self.entity.position if self.entity else Vec3(0, 0, 0)
    
    def get_world_position(self):
        """Get position in world coordinates"""
        return self.location
    
    def set_visibility(self, visible):
        """Set blob visibility"""
        if self.entity:
            self.entity.visible = visible
    
    def highlight(self, highlight_color=color.yellow):
        """Temporarily highlight this blob"""
        if self.entity:
            # Store original color and apply highlight
            self.entity.color = highlight_color
            # Could add timer to restore original color
    
    def destroy(self):
        """Clean up and destroy the blob entity"""
        if self.entity:
            destroy(self.entity)
            self.entity = None
        
        logger.debug(f"Destroyed blob entity {self.name} (ID: {self.blob_id})")