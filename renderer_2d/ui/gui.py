import pygame

class GUI:
    def __init__(self, settings, sim_world_data):
        self.settings = settings
        self.sim_world_data = sim_world_data

        # Colors
        self.bg_color = (40, 40, 40)
        self.panel_color = (60, 60, 60)
        self.button_color = (80, 80, 80)
        self.button_hover_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.accent_color = (0, 150, 200)
        
        # Font
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Button states
        self.buttons = []
        self.hovered_button = None
        self.control_buttons = {}  # Store button rectangles for click detection
        # Note: pause state is now stored in self.settings.paused
        
    def calculate_layout(self, screen_width, screen_height):
        """Calculate all panel positions and sizes based on screen dimensions"""
        # Panel widths (percentages of screen width)
        settings_width = int(screen_width * 0.2)  # 20% for settings
        stats_width = int(screen_width * 0.2)     # 20% for stats
        scene_width = screen_width - settings_width - stats_width  # 60% for main scene
        
        # Panel rectangles
        self.settings_panel = pygame.Rect(0, 0, settings_width, screen_height)
        self.scene_panel = pygame.Rect(settings_width, 0, scene_width, screen_height)
        self.stats_panel = pygame.Rect(settings_width + scene_width, 0, stats_width, screen_height)
        
        return self.settings_panel, self.scene_panel, self.stats_panel
        
    def draw_settings_panel(self, screen):
        """Draw the left settings panel"""
        # Draw panel background
        pygame.draw.rect(screen, self.panel_color, self.settings_panel)
        pygame.draw.rect(screen, self.accent_color, self.settings_panel, 2)
        
        # Title
        title = self.font.render("SETTINGS", True, self.text_color)
        title_rect = title.get_rect(centerx=self.settings_panel.centerx, y=self.settings_panel.y + 20)
        screen.blit(title, title_rect)
        
        # Settings buttons and controls
        y_offset = 70
        button_height = 30
        button_margin = 10
        
        # Simulation speed control
        speed_text = self.small_font.render("Sim Speed:", True, self.text_color)
        screen.blit(speed_text, (self.settings_panel.x + 10, self.settings_panel.y + y_offset))
        
        # Speed buttons
        speed_buttons = ["0.5x", "1x", "2x", "5x"]
        for i, speed in enumerate(speed_buttons):
            btn_x = self.settings_panel.x + 10 + i * 40
            btn_y = self.settings_panel.y + y_offset + 25
            btn_rect = pygame.Rect(btn_x, btn_y, 35, 25)
            
            # Button color based on selection (dummy: 1x selected)
            btn_color = self.accent_color if speed == "1x" else self.button_color
            pygame.draw.rect(screen, btn_color, btn_rect)
            pygame.draw.rect(screen, self.text_color, btn_rect, 1)
            
            # Button text
            btn_text = self.small_font.render(speed, True, self.text_color)
            text_rect = btn_text.get_rect(center=btn_rect.center)
            screen.blit(btn_text, text_rect)
        
        y_offset += 80
        
        # Control buttons
        control_buttons = [
            ("Play", "play"),
            ("Pause", "pause"),
            ("Reset", "reset")
        ]
        
        for i, (text, button_id) in enumerate(control_buttons):
            btn_rect = pygame.Rect(
                self.settings_panel.x + 10,
                self.settings_panel.y + y_offset + i * (button_height + button_margin),
                self.settings_panel.width - 20,
                button_height
            )
            
            # Store button rect for click detection
            self.control_buttons[button_id] = btn_rect
            
            # Button color based on current state from settings
            if button_id == "pause" and self.settings.paused:
                color = self.accent_color  # Highlight pause button when paused
            elif button_id == "play" and not self.settings.paused:
                color = self.accent_color  # Highlight play button when playing
            else:
                color = self.button_color
            
            pygame.draw.rect(screen, color, btn_rect)
            pygame.draw.rect(screen, self.text_color, btn_rect, 1)
            
            btn_text = self.font.render(text, True, self.text_color)
            text_rect = btn_text.get_rect(center=btn_rect.center)
            screen.blit(btn_text, text_rect)
        
        y_offset += 130
        
        # Population settings
        pop_text = self.small_font.render("Population:", True, self.text_color)
        screen.blit(pop_text, (self.settings_panel.x + 10, self.settings_panel.y + y_offset))
        
        pop_value = self.small_font.render("1000", True, self.accent_color)
        screen.blit(pop_value, (self.settings_panel.x + 10, self.settings_panel.y + y_offset + 20))
        
    def draw_stats_panel(self, screen):
        """Draw the right stats panel"""
        # Draw panel background
        pygame.draw.rect(screen, self.panel_color, self.stats_panel)
        pygame.draw.rect(screen, self.accent_color, self.stats_panel, 2)
        
        # Title
        title = self.font.render("STATS", True, self.text_color)
        title_rect = title.get_rect(centerx=self.stats_panel.centerx, y=self.stats_panel.y + 20)
        screen.blit(title, title_rect)
        
        # Stats data (dummy values)
        y_offset = 70
        stats_data = [
            ("Sim Time:", "12.5h"),
            ("Real Time:", "2m 34s"),
            ("Population:", "987"),
            ("Births:", "45"),
            ("Deaths:", "12"),
            ("Generation:", "8"),
            ("", ""),  # Spacer
            ("Food Items:", "234"),
            ("Avg Energy:", "67%"),
            ("Max Age:", "24.3h"),
            ("", ""),  # Spacer
            ("FPS:", "60"),
            ("Sim Ticks:", "7524"),
            ("Render Ticks:", "1508")
        ]
        
        for label, value in stats_data:
            if not label:  # Spacer
                y_offset += 15
                continue
                
            # Label
            label_text = self.small_font.render(label, True, self.text_color)
            screen.blit(label_text, (self.stats_panel.x + 10, self.stats_panel.y + y_offset))
            
            # Value
            if value:
                value_text = self.small_font.render(value, True, self.accent_color)
                value_rect = value_text.get_rect(right=self.stats_panel.right - 10, y=self.stats_panel.y + y_offset)
                screen.blit(value_text, value_rect)
            
            y_offset += 25
            
    def draw_scene_area(self, screen):
        """Draw the main scene area (currently just a placeholder)"""
        # Draw scene background
        pygame.draw.rect(screen, (20, 20, 20), self.scene_panel)
        pygame.draw.rect(screen, self.accent_color, self.scene_panel, 2)
        
        # Placeholder text
        placeholder = self.font.render("SIMULATION WORLD", True, (100, 100, 100))
        placeholder_rect = placeholder.get_rect(center=self.scene_panel.center)
        screen.blit(placeholder, placeholder_rect)
        
        # Grid overlay (optional visual aid)
        grid_color = (30, 30, 30)
        grid_size = 50
        
        # Vertical lines
        for x in range(self.scene_panel.x, self.scene_panel.right, grid_size):
            pygame.draw.line(screen, grid_color, (x, self.scene_panel.y), (x, self.scene_panel.bottom))
        
        # Horizontal lines
        for y in range(self.scene_panel.y, self.scene_panel.bottom, grid_size):
            pygame.draw.line(screen, grid_color, (self.scene_panel.x, y), (self.scene_panel.right, y))
    
    def handle_event(self, event):
        """Handle GUI events like button clicks"""
        action = None
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                
                # Check control button clicks
                for button_id, btn_rect in self.control_buttons.items():
                    if btn_rect.collidepoint(mouse_pos):
                        print(f"DEBUG: Button {button_id} clicked at {mouse_pos}")
                        if button_id == "play":
                            action = "play"
                        elif button_id == "pause":
                            action = "pause"
                        elif button_id == "reset":
                            action = "reset"
                        print(f"DEBUG: Action set to {action}")
                        
        elif event.type == pygame.MOUSEMOTION:
            # Handle button hover states here
            pass
            
        return action
    
    def draw(self, screen, screen_width, screen_height):
        """Main draw method"""
        # Calculate layout based on current screen size
        self.calculate_layout(screen_width, screen_height)
        
        # Draw all panels
        self.draw_settings_panel(screen)
        self.draw_scene_area(screen)
        self.draw_stats_panel(screen)

    def _handle_pause_button(self):
        """Handle pause button logic"""
        self.settings.paused = not self.settings.paused