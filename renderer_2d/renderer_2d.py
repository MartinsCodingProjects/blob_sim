import pygame
from .ui.gui import GUI
from .ui.scene import Scene
import json


class Renderer2d():
    def __init__(self, settings):
        self.sim_world_data = None  # Store the latest simulation world data
        self.settings = settings
        self.viewport_width = 800
        self.viewport_height = 600
        self.action_callback = None  # Callback function for communicating actions back to main thread
        
        # Initialize UI components
        self.gui = GUI(settings, self.sim_world_data)
        self.scene = Scene(settings, self.sim_world_data)
        
    def set_action_callback(self, callback):
        """Set callback function for handling GUI actions"""
        self.action_callback = callback

    def start(self):
        # pygame setup
        pygame.init()
        self.screen = pygame.display.set_mode((self.viewport_width, self.viewport_height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Start render loop
        self.render_loop()

        # Cleanup, after loop ends
        pygame.quit()

    def render_loop(self):
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.viewport_width, self.viewport_height = event.size
                    self.screen = pygame.display.set_mode((self.viewport_width, self.viewport_height), pygame.RESIZABLE)
                
                # Pass events to GUI and Scene, handle any actions returned
                gui_action = self.gui.handle_event(event)
                if gui_action:
                    print(f"DEBUG: GUI returned action: {gui_action}")
                    if self.action_callback:
                        print(f"DEBUG: Calling action callback with {gui_action}")
                        self.action_callback(gui_action)
                    else:
                        print("DEBUG: No action callback set!")
                
                # Calculate scene rect for scene input handling
                _, scene_rect, _ = self.gui.calculate_layout(self.viewport_width, self.viewport_height)
                self.scene.handle_input(event, scene_rect)

            # Clear screen
            self.screen.fill((30, 30, 30))
            
            # Get current window size
            win_w, win_h = self.screen.get_size()
            
            # Update GUI and Scene with latest sim world data (only if data changed)
            self.gui.sim_world_data = self.sim_world_data
            self.scene.sim_world_data = self.sim_world_data
            # print(" DEBUG SIMWORLD DATA IN RENDERER_2D:", self.sim_world_data)

            # Draw GUI (this includes all panels)
            self.gui.draw(self.screen, win_w, win_h)
            
            # Draw scene content (this will draw inside the scene panel)
            _, scene_rect, _ = self.gui.calculate_layout(win_w, win_h)
            self.scene.draw(self.screen, scene_rect)

            # Update display
            pygame.display.flip()
            self.clock.tick(60)

    def update_sim_world_data(self, new_data):
        """Update the simulation world data used by the renderer."""
        if new_data and 'blobs_data' in new_data:
            blob_count = len(new_data.get('blobs_data', []))
            first_blob = new_data['blobs_data'][0] if blob_count > 0 else None
            if first_blob:
                location = first_blob.get('location', [0, 0, 0])
                state = first_blob.get('state', 'unknown')
                print(f"DEBUG RENDERER: Received data with {blob_count} blobs, first blob at {location} state: {state}")
        self.sim_world_data = new_data
