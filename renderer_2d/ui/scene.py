import pygame

class Scene:
    def __init__(self, settings, sim_world_data):
        self.settings = settings
        self.sim_world_data = sim_world_data

        # Scene properties
        self.zoom = 1.0
        self.camera_x = 0
        self.camera_y = 0
        self.world_width = 1000  # World coordinate system
        self.world_height = 1000
        
    def screen_to_world(self, screen_x, screen_y, scene_rect):
        """Convert screen coordinates to world coordinates"""
        # Account for scene panel offset
        scene_x = screen_x - scene_rect.x
        scene_y = screen_y - scene_rect.y
        
        # Convert to world coordinates
        world_x = (scene_x / self.zoom) + self.camera_x
        world_y = (scene_y / self.zoom) + self.camera_y
        
        return world_x, world_y
    
    def world_to_screen(self, world_x, world_y, scene_rect, world_radius=None):
        """Convert world coordinates to screen coordinates and optionally scale radius"""
        world_dims = self._get_world_dimensions()
        sim_area = self._calculate_simulation_area(scene_rect, world_dims)
        
        # Apply radius constraints if needed
        constrained_coords = self._constrain_coordinates_by_radius(
            world_x, world_y, world_dims, world_radius
        )
        
        # Transform to screen coordinates
        screen_coords = self._transform_to_screen_coordinates(
            constrained_coords, world_dims, sim_area
        )
        
        # Scale radius if provided
        if world_radius is not None:
            screen_radius = self._calculate_screen_radius(world_radius, sim_area)
            return screen_coords[0], screen_coords[1], screen_radius
        
        return screen_coords[0], screen_coords[1]

    def _get_world_dimensions(self):
        """Extract world dimensions from simulation data"""
        if self.sim_world_data and 'world_data' in self.sim_world_data:
            world_data = self.sim_world_data['world_data']
            width = world_data.get('dimensions', [100, 100, 5])[0]
            height = world_data.get('dimensions', [100, 100, 5])[1]
            return width, height
        return 100, 100  # Default

    def _calculate_simulation_area(self, scene_rect, world_dims):
        """Calculate the simulation area with zoom and camera applied"""
        world_width, world_height = world_dims
        
        # Calculate base area (90% of available space)
        margin = 0.9
        available_width = scene_rect.width * margin
        available_height = scene_rect.height * margin
        base_size = int(min(available_width, available_height))
        
        # Apply zoom
        zoomed_size = int(base_size * self.zoom)
        
        # Calculate camera offset
        base_scale_factor = base_size / world_width
        camera_offset_x = -self.camera_x * base_scale_factor * self.zoom
        camera_offset_y = -self.camera_y * base_scale_factor * self.zoom
        
        # Center with camera offset
        area_x = scene_rect.x + (scene_rect.width - zoomed_size) // 2 + camera_offset_x
        area_y = scene_rect.y + (scene_rect.height - zoomed_size) // 2 + camera_offset_y
        
        return {
            'x': area_x,
            'y': area_y, 
            'width': zoomed_size,
            'height': zoomed_size,
            'scale_factor': zoomed_size / world_width
        }

    def _constrain_coordinates_by_radius(self, world_x, world_y, world_dims, world_radius):
        """Constrain coordinates so entity edges stay within world boundaries"""
        if world_radius is None:
            return world_x, world_y
            
        world_width, world_height = world_dims
        
        min_x = world_radius
        max_x = world_width - world_radius
        min_y = world_radius  
        max_y = world_height - world_radius
        
        constrained_x = max(min_x, min(world_x, max_x))
        constrained_y = max(min_y, min(world_y, max_y))
        
        return constrained_x, constrained_y

    def _transform_to_screen_coordinates(self, world_coords, world_dims, sim_area):
        """Transform world coordinates to screen coordinates"""
        world_x, world_y = world_coords
        world_width, world_height = world_dims
        
        # Normalize to simulation area
        norm_x = (world_x / world_width) * sim_area['width']
        norm_y = (world_y / world_height) * sim_area['height']
        
        # Convert to screen coordinates
        screen_x = sim_area['x'] + norm_x
        screen_y = sim_area['y'] + norm_y
        
        return screen_x, screen_y

    def _calculate_screen_radius(self, world_radius, sim_area):
        """Calculate the screen radius based on world radius and current scale"""
        return max(1, int(world_radius * sim_area['scale_factor']))
    
    def handle_input(self, event, scene_rect):
        """Handle scene-specific input (zoom, pan, etc.)"""
        if event.type == pygame.MOUSEWHEEL:
            # Zoom with mouse wheel
            if scene_rect.collidepoint(pygame.mouse.get_pos()):
                zoom_factor = 1.1 if event.y > 0 else 0.9
                self.zoom *= zoom_factor
                self.zoom = max(0.1, min(5.0, self.zoom))  # Clamp zoom

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # Middle mouse button for panning
                self.panning = True
                self.pan_start = pygame.mouse.get_pos()
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self.panning = False
        
        elif event.type == pygame.MOUSEMOTION:
            if hasattr(self, 'panning') and self.panning:
                # Pan the camera
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = (mouse_x - self.pan_start[0]) / self.zoom
                dy = (mouse_y - self.pan_start[1]) / self.zoom
                
                self.camera_x -= dx
                self.camera_y -= dy
                
                self.pan_start = (mouse_x, mouse_y)
    
    def draw_world_content(self, screen, scene_rect):
        """Draw the actual simulation content within the scene"""
        from ..entity.blob import Blob
        
        # Create some example blob objects with different properties
        test_blobs = []
        
        # Check if sim world data is available
        if self.sim_world_data is None:
            # No simulation data yet, show placeholder or empty scene
            return
            
        for blob in self.sim_world_data.get('blobs_data', []):
            location = blob.get('location', 'Unknown')
            state = blob.get('state', 'Unknown')
            print(f"DEBUG SCENE: Creating blob entity for {blob.get('name', 'Unknown')} at {location} state: {state}")
            test_blobs.append(
                Blob(
                    entity_data=blob
                )
            )
        
        print(f"DEBUG SCENE: Created {len(test_blobs)} blob entities for rendering")
        
        # Draw each blob using OOP approach - each blob draws itself
        for blob in test_blobs:
            blob.draw(screen, scene_rect, self.world_to_screen, self.zoom)
    
    def draw(self, screen, scene_rect):
        """Draw the scene within the given rectangle"""
        # Clip drawing to scene area
        screen.set_clip(scene_rect)
        
        # Draw background
        pygame.draw.rect(screen, (20, 20, 20), scene_rect)
        
        # Draw world (grey area) - pass zoom and camera info for proper scaling
        self.world = World()
        self.world.draw(screen, scene_rect, zoom=self.zoom, camera_x=self.camera_x, camera_y=self.camera_y, sim_world_data=self.sim_world_data)

        # Draw world content
        self.draw_world_content(screen, scene_rect)
        
        # Draw scene info overlay
        font = pygame.font.Font(None, 20)
        info_text = f"Zoom: {self.zoom:.2f} | Camera: ({self.camera_x:.0f}, {self.camera_y:.0f})"
        info_surface = font.render(info_text, True, (150, 150, 150))
        screen.blit(info_surface, (scene_rect.x + 10, scene_rect.y + 10))
        
        # Remove clipping
        screen.set_clip(None)
        
        # Draw border
        pygame.draw.rect(screen, (0, 150, 200), scene_rect, 2)

class World:
    def __init__(self, sim_world_data=None):
        self.scale_factor = 1.0  # World scale factor
        self.world_base_position = (0, 0)
        self.sim_area_width = None
        self.sim_area_height = None
        self.sim_area_x = None
        self.sim_area_y = None
        self.sim_world_data = sim_world_data.get('world_data', {}) if sim_world_data else {}

    def draw(self, screen, scene_rect, zoom=1.0, camera_x=0, camera_y=0, sim_world_data=None):
        # Get world dimensions
        world_dims = self._get_world_dimensions_from_data(sim_world_data)
        
        # Calculate simulation area with zoom and camera
        sim_area = self._calculate_world_simulation_area(scene_rect, world_dims, zoom, camera_x, camera_y)
        
        # Store for other methods
        self.sim_area_width = sim_area['width']
        self.sim_area_height = sim_area['height']  
        self.sim_area_x = sim_area['x']
        self.sim_area_y = sim_area['y']
        
        # Draw the simulation area
        self._draw_simulation_area(screen, sim_area, zoom)

    def _get_world_dimensions_from_data(self, sim_world_data):
        """Extract world dimensions from simulation data"""
        if sim_world_data and 'world_data' in sim_world_data:
            world_data = sim_world_data['world_data']
            width = world_data.get('dimensions', [100, 100, 5])[0]
            height = world_data.get('dimensions', [100, 100, 5])[1]
            return width, height
        return 100, 100  # Default

    def _calculate_world_simulation_area(self, scene_rect, world_dims, zoom, camera_x, camera_y):
        """Calculate the simulation area with zoom and camera applied"""
        world_width, world_height = world_dims
        
        # Calculate base area (90% of available space)
        margin = 0.9
        available_width = scene_rect.width * margin
        available_height = scene_rect.height * margin
        base_size = int(min(available_width, available_height))
        
        # Apply zoom
        zoomed_size = int(base_size * zoom)
        
        # Calculate camera offset
        base_scale_factor = base_size / world_width
        camera_offset_x = -camera_x * base_scale_factor * zoom
        camera_offset_y = -camera_y * base_scale_factor * zoom
        
        # Center with camera offset
        area_x = scene_rect.x + (scene_rect.width - zoomed_size) // 2 + camera_offset_x
        area_y = scene_rect.y + (scene_rect.height - zoomed_size) // 2 + camera_offset_y
        
        return {
            'x': area_x,
            'y': area_y,
            'width': zoomed_size, 
            'height': zoomed_size
        }

    def _draw_simulation_area(self, screen, sim_area, zoom):
        """Draw the grey simulation area background and border"""
        sim_area_rect = pygame.Rect(sim_area['x'], sim_area['y'], sim_area['width'], sim_area['height'])
        pygame.draw.rect(screen, (80, 80, 80), sim_area_rect)  # Grey background
        pygame.draw.rect(screen, (120, 120, 120), sim_area_rect, max(1, int(2 * zoom)))  # Zoom-scaled border
    
    def update_world(self, new_data):
        """Update the simulation world data used by the world."""
        self.sim_world_data = new_data.get('world_data', {})
        # calculate scale factor and base postition based on current Worlds Size and position
        self.scale_factor = self.calculate_scale_factor(self.sim_world_data)
        self.world_base_position = self.get_world_base_position()

    def calculate_scale_factor(self, world_data):
        sim_world_width = world_data.get('width', 100)
        #sim_world_height = world_data.get('height', 100)

        self.scale_factor = self.sim_area_width / sim_world_width
        return self.scale_factor

    def get_world_base_position(self):
        return (self.sim_area_x, self.sim_area_y)
    
    def normalize_world_content(self, sim_world_data=None):
        """Normalize world content positions based on scale factor and base position"""
        if sim_world_data is None:
            sim_world_data = self.sim_world_data
        
        for blob in sim_world_data.get('blobs_data', []):
            self.normalize_postion(blob)
            self.normalize_radius(blob)

        for thing in sim_world_data.get('things_data', []):
            self.normalize_postion(thing)
            

    def normalize_postion(self, entity):
        """Normalize a single entity's position"""
        if 'location' in entity:
            sim_x, sim_y = entity['location']
            norm_x = self.world_base_position[0] + sim_x * self.scale_factor
            norm_y = self.world_base_position[1] + sim_y * self.scale_factor
            entity['location'] = (norm_x, norm_y)