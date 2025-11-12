# create Blob class inheriting from Entity
import pygame
from renderer_2d.entity.entity import Entity


class Blob(Entity):
    def __init__(self, entity_data):
        super().__init__(entity_data)
        # Blob-specific properties
        self.color = entity_data.get("color", (255, 100, 100))
        # Note: radius is handled by parent Entity class
    
    def draw(self, screen, scene_rect, world_to_screen_func, zoom):
        """Draw the blob on screen"""
        # Use parent class methods for common functionality
        screen_x, screen_y, screen_radius = self.get_screen_position_and_radius(scene_rect, world_to_screen_func)
        
        # Only draw if visible on screen
        if self.is_visible_on_screen(screen_x, screen_y, scene_rect):
            # Blob-specific rendering
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), screen_radius)
            
            # Optional: Draw ID text for debugging
            if zoom > 0.5:  # Only show text when zoomed in enough
                font = pygame.font.Font(None, max(12, int(16 * zoom)))
                text = font.render(str(self.id), True, (255, 255, 255))
                text_rect = text.get_rect(center=(int(screen_x), int(screen_y)))
                screen.blit(text, text_rect)