"""
Thing Entity
Represents simulation objects/things in the 3D renderer.
"""
from ursina import *
import logging

logger = logging.getLogger("RENDERER_THING")

class ThingEntity:
    """3D representation of a simulation thing/object"""
    
    def __init__(self, thing_id, thing_data, settings=None):
        """Initialize thing entity from simulation data"""
        self.thing_id = thing_id
        self.settings = settings
        
        # Extract data from simulation
        self.name = thing_data.get('name', f'Thing_{thing_id}')
        self.location = thing_data.get('location', [0, 0, 0])
        self.thing_type = thing_data.get('type', 'unknown')
        self.properties = thing_data.get('properties', {})
        
        # 3D entity
        self.entity = None
        
        # Visual properties based on type
        self.visual_config = self._get_visual_config_for_type(self.thing_type)
        
        # Create the 3D entity
        self._create_entity()
        
        logger.debug(f"Created thing entity {self.name} (ID: {thing_id}, Type: {self.thing_type})")
    
    def _get_visual_config_for_type(self, thing_type):
        """Get visual configuration based on thing type"""
        configs = {
            'food': {
                'model': 'sphere',
                'color': color.green,
                'scale': 0.3
            },
            'water': {
                'model': 'cube',
                'color': color.blue,
                'scale': 0.4
            },
            'obstacle': {
                'model': 'cube',
                'color': color.brown,
                'scale': 1.0
            },
            'shelter': {
                'model': 'cube',
                'color': color.wood,
                'scale': (2.0, 1.5, 2.0)
            },
            'unknown': {
                'model': 'cube',
                'color': color.gray,
                'scale': 0.5
            }
        }
        
        return configs.get(thing_type, configs['unknown'])
    
    def _create_entity(self):
        """Create the 3D Ursina entity for this thing"""
        config = self.visual_config
        
        # Convert location to Ursina coordinates (x, z, y mapping)
        position = Vec3(self.location[0], self.location[2], self.location[1])
        
        # Create entity
        self.entity = Entity(
            model=config['model'],
            color=config['color'],
            scale=config['scale'],
            position=position
        )
        
        # Apply any special properties
        self._apply_special_properties()
    
    def _apply_special_properties(self):
        """Apply special visual properties based on thing properties"""
        # Handle transparency
        if 'transparency' in self.properties:
            transparency = self.properties['transparency']
            if self.entity and hasattr(self.entity, 'color'):
                # Apply transparency to color
                current_color = self.entity.color
                self.entity.color = color.rgba(
                    current_color.r * 255,
                    current_color.g * 255,
                    current_color.b * 255,
                    int(255 * (1 - transparency))
                )
        
        # Handle size modifier
        if 'size_modifier' in self.properties:
            size_mod = self.properties['size_modifier']
            if self.entity:
                self.entity.scale *= size_mod
        
        # Handle rotation
        if 'rotation' in self.properties:
            rotation = self.properties['rotation']
            if self.entity and isinstance(rotation, (list, tuple)) and len(rotation) >= 3:
                self.entity.rotation = Vec3(rotation[0], rotation[1], rotation[2])
    
    def update_from_data(self, thing_data):
        """Update thing entity from new simulation data"""
        # Update location
        new_location = thing_data.get('location', self.location)
        if new_location != self.location:
            self.location = new_location
            if self.entity:
                self.entity.position = Vec3(new_location[0], new_location[2], new_location[1])
        
        # Update properties
        new_properties = thing_data.get('properties', self.properties)
        if new_properties != self.properties:
            self.properties = new_properties
            self._apply_special_properties()
        
        # Update type if changed (rare but possible)
        new_type = thing_data.get('type', self.thing_type)
        if new_type != self.thing_type:
            self.thing_type = new_type
            self._recreate_entity()
    
    def _recreate_entity(self):
        """Recreate entity with new type configuration"""
        # Destroy old entity
        if self.entity:
            destroy(self.entity)
        
        # Update visual config
        self.visual_config = self._get_visual_config_for_type(self.thing_type)
        
        # Create new entity
        self._create_entity()
    
    def update(self):
        """Update thing entity (called each frame)"""
        # Things are usually static, but could have animations
        self._update_animations()
    
    def _update_animations(self):
        """Update any animations for this thing type"""
        if self.thing_type == 'water':
            # Gentle bobbing for water
            self._animate_water()
        elif self.thing_type == 'food':
            # Slight rotation for food items
            self._animate_food()
        # Add more animations as needed
    
    def _animate_water(self):
        """Animate water with gentle bobbing"""
        if self.entity:
            bob_amount = 0.05
            bob_speed = 3.0
            base_y = self.location[2]  # Use original Y position
            self.entity.y = base_y + sin(time.time() * bob_speed) * bob_amount
    
    def _animate_food(self):
        """Animate food with slow rotation"""
        if self.entity:
            rotation_speed = 30  # degrees per second
            self.entity.rotation_y += rotation_speed * time.dt
    
    def get_position(self):
        """Get current 3D position"""
        return self.entity.position if self.entity else Vec3(0, 0, 0)
    
    def get_world_position(self):
        """Get position in world coordinates"""
        return self.location
    
    def set_visibility(self, visible):
        """Set thing visibility"""
        if self.entity:
            self.entity.visible = visible
    
    def highlight(self, highlight_color=color.yellow):
        """Temporarily highlight this thing"""
        if self.entity:
            # Store original color and apply highlight
            original_color = self.entity.color
            self.entity.color = highlight_color
            # Could add timer to restore original color
    
    def destroy(self):
        """Clean up and destroy the thing entity"""
        if self.entity:
            destroy(self.entity)
            self.entity = None
        
        logger.debug(f"Destroyed thing entity {self.name} (ID: {self.thing_id})")