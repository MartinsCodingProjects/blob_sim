"""
Scene Manager
Manages the 3D scene setup, lighting, environment, and world geometry.
"""
from ursina import *
import logging

logger = logging.getLogger("RENDERER_SCENE")

class SceneManager:
    """Manages the 3D scene environment and world setup"""
    
    def __init__(self, settings=None):
        """Initialize scene manager with settings"""
        self.settings = settings
        
        # Use fixed renderer world dimensions (normalized space)
        if settings:
            self.world_length = settings.RENDERER_WORLD_SIZE if hasattr(settings, 'RENDERER_WORLD_SIZE') else 100
            self.world_width = settings.RENDERER_WORLD_SIZE if hasattr(settings, 'RENDERER_WORLD_SIZE') else 100
            self.world_height = settings.RENDERER_WORLD_HEIGHT if hasattr(settings, 'RENDERER_WORLD_HEIGHT') else 5
        else:
            self.world_length = 100  # Fixed renderer size
            self.world_width = 100   # Fixed renderer size
            self.world_height = 5
        
        # Scene entities
        self.ground_entity = None
        self.boundary_entities = []
        self.lighting_entities = []
        
        logger.info(f"Scene Manager initialized for world {self.world_length}x{self.world_width}x{self.world_height}")
    
    def setup_scene(self):
        """Set up the complete 3D scene"""
        logger.info("Setting up 3D scene...")
        
        # Set up lighting
        self._setup_lighting()
        
        # Create ground plane
        self._create_ground()
        
        # Create world boundaries
        self._create_boundaries()
        
        # Add sky
        self._setup_sky()
        
        logger.info("Scene setup complete")
    
    def _setup_lighting(self):
        """Set up scene lighting"""
        # Main directional light (sun)
        main_light = DirectionalLight()
        main_light.look_at(Vec3(1, -1, -1))
        main_light.color = color.white
        self.lighting_entities.append(main_light)
        
        # Ambient lighting
        ambient_light = AmbientLight(color=color.rgba(255, 255, 255, 20))
        self.lighting_entities.append(ambient_light)
        
        logger.debug("Lighting setup complete")
    
    def _create_ground(self):
        """Create the main ground plane"""
        # Semi-transparent ground with mesh structure  
        # Try different ground orientation if coordinate mapping doesn't work
        self.ground_entity = Entity(
            model='cube',
            color=color.rgba(50, 0, 0, 100),  # Semi-transparent dark red
            scale=(self.world_length, self.world_width, 0.1),
            position=(self.world_length / 2, self.world_width / 2, -0.5),
            # rotation=(0, 0, 0)  # Could rotate ground plane if needed
        )
        
        logger.info(f"Ground plane created: {self.world_length}x{self.world_width} at position ({self.world_length / 2}, -0.5, {self.world_width / 2})")
    
    def _create_boundaries(self):
        """Create visible world boundaries and grid lines"""
        edge_color = color.white
        thickness = 0.2
        
        # Create boundary frame (skeleton structure)
        # Four corner vertical edges
        for x in [0, self.world_length]:
            for z in [0, self.world_width]:
                edge = Entity(
                    model='cube',
                    color=edge_color,
                    scale=(thickness, thickness, 1),
                    position=(x, z, 0)
                )
                self.boundary_entities.append(edge)
        
        # Four horizontal edges (X axis)
        for z in [0, self.world_width]:
            edge = Entity(
                model='cube',
                color=edge_color,
                scale=(self.world_length, thickness, thickness),
                position=(self.world_length / 2, z, 0)
            )
            self.boundary_entities.append(edge)
        
        # Four horizontal edges (Z axis)
        for x in [0, self.world_length]:
            edge = Entity(
                model='cube',
                color=edge_color,
                scale=(thickness, self.world_width, thickness),
                position=(x, self.world_width / 2, 0)
            )
            self.boundary_entities.append(edge)
        
        # Optional: Add grid lines for better spatial reference
        self._create_grid_lines()
        
        logger.debug(f"Created {len(self.boundary_entities)} boundary entities")
    
    def _create_grid_lines(self):
        """Create optional grid lines for spatial reference"""
        grid_color = color.rgba(255, 255, 255, 50)  # Very faint white
        grid_spacing = 50  # Grid every 50 units
        line_thickness = 0.05
        
        # Vertical grid lines (parallel to Z axis)
        for x in range(0, self.world_length + 1, grid_spacing):
            if x != 0 and x != self.world_length:  # Don't duplicate boundary lines
                grid_line = Entity(
                    model='cube',
                    color=grid_color,
                    scale=(line_thickness, self.world_width, 0.1, ),
                    position=(x, self.world_width / 2, 0)
                )
                self.boundary_entities.append(grid_line)
        
        # Horizontal grid lines (parallel to X axis)
        for z in range(0, self.world_width + 1, grid_spacing):
            if z != 0 and z != self.world_width:  # Don't duplicate boundary lines
                grid_line = Entity(
                    model='cube',
                    color=grid_color,
                    scale=(self.world_length, line_thickness, 0.1),
                    position=(self.world_length / 2, z, 0)
                )
                self.boundary_entities.append(grid_line)
        
        logger.debug("Grid lines created")
    
    def _setup_sky(self):
        """Set up sky/background"""
        Sky()
        logger.debug("Sky setup complete")
    
    def update_world_state(self, world_data):
        """Update scene based on world state (day/night, weather, etc.)"""
        if not world_data:
            return
        
        # Handle day/night cycle
        day_phase = world_data.get('day_phase', 'day')
        self._update_lighting_for_time(day_phase)
        
        # Handle other world state changes
        # (weather, seasons, etc. can be added here)
    
    def _update_lighting_for_time(self, day_phase):
        """Update lighting based on day/night cycle"""
        # Placeholder for day/night lighting changes
        if day_phase == 'night':
            # Darker lighting
            pass
        else:
            # Normal lighting
            pass
    
    def get_world_bounds(self):
        """Get world boundary information"""
        return {
            'min_x': 0,
            'max_x': self.world_length,
            'min_z': 0,
            'max_z': self.world_width,
            'min_y': 0,
            'max_y': self.world_height
        }
    
    def cleanup(self):
        """Clean up scene resources"""
        # Destroy ground
        if self.ground_entity:
            destroy(self.ground_entity)
        
        # Destroy boundaries
        for entity in self.boundary_entities:
            destroy(entity)
        self.boundary_entities.clear()
        
        # Clean up lighting
        for light in self.lighting_entities:
            destroy(light)
        self.lighting_entities.clear()
        
        logger.info("Scene Manager cleanup complete")