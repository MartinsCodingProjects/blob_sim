class Entity:
    def __init__(self, entity_data):
        self.entity_data = entity_data
        self.id = entity_data.get("id", None)
        self.name = entity_data.get("name", "Unnamed")
        self.position = entity_data.get("location", (0, 0))
        self.radius = entity_data.get("radius", 5.0)  # Default radius
        
    def get_world_position_2d(self):
        """Extract 2D world position from potentially 3D position"""
        if len(self.position) == 3:
            return self.position[0], self.position[1]  # Use x,y and ignore z
        else:
            return self.position
            
    def get_screen_position_and_radius(self, scene_rect, world_to_screen_func):
        """Convert world position to screen position and scale radius"""
        world_x, world_y = self.get_world_position_2d()
        screen_x, screen_y, screen_radius = world_to_screen_func(world_x, world_y, scene_rect, self.radius)
        return screen_x, screen_y, screen_radius
        
    def is_visible_on_screen(self, screen_x, screen_y, scene_rect):
        """Check if entity is visible within the scene rectangle"""
        return (scene_rect.left <= screen_x <= scene_rect.right and 
                scene_rect.top <= screen_y <= scene_rect.bottom)
                
    def draw(self, screen, scene_rect, world_to_screen_func, zoom):
        """Base draw method - should be overridden by subclasses"""
        pass