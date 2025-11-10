"""
UI Manager
Manages user interface elements, overlays, and debug information display.
"""
from ursina import *
import logging

logger = logging.getLogger("RENDERER_UI")

class UIManager:
    """Manages all UI elements and overlays for the renderer"""
    
    def __init__(self, settings=None):
        """Initialize UI manager"""
        self.settings = settings
        
        # UI state
        self.debug_panel_visible = True
        self.ui_elements = {}
        
        # Debug panel components
        self.debug_panel = None
        self.debug_background = None
        self.debug_texts = {}
        
        # UI styling
        self.panel_color = color.rgba(0, 0, 0, 180)  # Semi-transparent black
        self.text_color = color.white
        self.font_size = 16
        self.panel_padding = 0.02
        
        logger.info("UI Manager initialized")
    
    def setup_ui(self):
        """Set up all UI elements"""
        # Disable Ursina's default debug UI
        self._disable_default_ui()
        
        # Create custom debug panel
        self._create_debug_panel()
        
        logger.info("UI setup complete")
    
    def _disable_default_ui(self):
        """Disable Ursina's default debug displays"""
        try:
            # Method 1: Direct window attributes
            if hasattr(window, 'fps_counter'):
                window.fps_counter.enabled = False
            if hasattr(window, 'collisions_counter'):
                window.collisions_counter.enabled = False  
            if hasattr(window, 'entity_counter'):
                window.entity_counter.enabled = False
            
            # Method 2: Search for existing UI text entities and disable them
            ui_entities_to_disable = []
            for entity in scene.entities:
                if hasattr(entity, 'text'):
                    text_str = str(entity.text).lower()
                    if any(word in text_str for word in ['fps', 'collision', 'entities', 'ms']):
                        ui_entities_to_disable.append(entity)
            
            for entity in ui_entities_to_disable:
                entity.enabled = False
                logger.debug(f"Disabled default UI entity: {entity.text}")
            
            # Method 3: Disable common Ursina debug features
            window.editor_ui.enabled = False if hasattr(window, 'editor_ui') else None
            
            # Method 4: Check camera.ui children for debug elements
            if hasattr(camera, 'ui') and camera.ui:
                for child in camera.ui.children:
                    if hasattr(child, 'text'):
                        text_str = str(child.text).lower()
                        if any(word in text_str for word in ['fps', 'collision', 'entities']):
                            child.enabled = False
                            logger.debug(f"Disabled camera UI element: {child.text}")
            
            logger.debug("Default Ursina UI elements disabled")
        except Exception as e:
            logger.warning(f"Could not fully disable default UI: {e}")

    def _create_debug_panel(self):
        """Create custom debug information panel"""
        # Create background panel - use 'quad' instead of 'cube' for 2D UI
        self.debug_background = Entity(
            model='quad',
            color=self.panel_color,
            scale=(0.4, 0.75),  # Width, height only (2D)
            origin=(-0.5, 0.5),  # Top-left corner
            position=(-0.85, 0.45, -1),  # Adjusted for top-left corner offset
            parent=camera.ui,
            alpha=0.7  # Make it semi-transparent
        )
        
        # Create text elements for debug info
        # Adjusted positions for text elements relative to the background
        base_y = -0.1  # Start near the top of the background
        line_spacing = 0.08  # Increase spacing for better readability
        text_x = 0.1  # Slightly inset from the left edge of the background

        # FPS
        self.debug_texts['fps'] = Text(
            'FPS: 0',
            position=(text_x, base_y, 0),  # Adjusted relative position
            scale=2.0,
            color=self.text_color,
            parent=self.debug_background
        )

        # Camera Position
        self.debug_texts['camera_pos'] = Text(
            'Camera: (0, 0, 0)',
            position=(text_x, base_y - line_spacing, 0),
            scale=2.0,
            color=self.text_color,
            parent=self.debug_background
        )

        # Camera Rotation
        self.debug_texts['camera_rot'] = Text(
            'Rotation: (0°, 0°)',
            position=(text_x, base_y - line_spacing * 2, 0),
            scale=2.0,
            color=self.text_color,
            parent=self.debug_background
        )

        # Entities Count
        self.debug_texts['entities'] = Text(
            'Entities: 0',
            position=(text_x, base_y - line_spacing * 3, 0),
            scale=2.0,
            color=self.text_color,
            parent=self.debug_background
        )

        # Network Status
        self.debug_texts['network'] = Text(
            'Network: Disconnected',
            position=(text_x, base_y - line_spacing * 4, 0),
            scale=2.0,
            color=self.text_color,
            parent=self.debug_background
        )

        # Movement Speed
        self.debug_texts['speed'] = Text(
            'Speed: Normal',
            position=(text_x, base_y - line_spacing * 5, 0),
            scale=2.0,
            color=self.text_color,
            parent=self.debug_background
        )
        
        logger.debug("Debug panel created")
    
    def update_debug_info(self, camera_controller=None, entity_manager=None, network_manager=None):
        """Update debug information display"""
        if not self.debug_panel_visible or not self.debug_texts:
            return
        
        # Continuously check and disable default UI elements
        # self._continuously_disable_default_ui()
        
        try:
            # Update FPS
            fps = int(1.0 / time.dt) if time.dt > 0 else 0
            self.debug_texts['fps'].text = f'FPS: {fps}'
            
            # Update camera position and rotation
            if camera_controller:
                pos = camera_controller.get_position()
                rot = camera_controller.get_rotation()
                self.debug_texts['camera_pos'].text = f'Pos: ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})'
                self.debug_texts['camera_rot'].text = f'Rot: ({rot[0]:.1f}°, {rot[1]:.1f}°)'
                
                # Update speed info
                speed_text = "Speed: Boost" if camera_controller.speed_boost_active else "Speed: Normal"
                self.debug_texts['speed'].text = speed_text
            
            # Update entity count and show scale factor if available
            if entity_manager:
                counts = entity_manager.get_entity_count()
                total = counts.get('blobs', 0) + counts.get('things', 0)
                
                # Try to get normalization info
                try:
                    norm_info = entity_manager.get_normalization_info()
                    scale = norm_info.get('entity_scale', 1.0)
                    self.debug_texts['entities'].text = f'Entities: {total} (Scale: {scale:.2f}x)'
                except:
                    self.debug_texts['entities'].text = f'Entities: {total} ({counts.get("blobs", 0)}B, {counts.get("things", 0)}T)'
            
            # Update network status
            if network_manager:
                status = network_manager.get_connection_status()
                connected = "Connected" if status.get('connected', False) else "Disconnected"
                updates = status.get('total_updates', 0)
                self.debug_texts['network'].text = f'Net: {connected} ({updates})'
                
        except Exception as e:
            logger.error(f"Error updating debug info: {e}")
    
    def toggle_debug_panel(self):
        """Toggle visibility of debug panel"""
        self.debug_panel_visible = not self.debug_panel_visible
        
        # Toggle background
        if self.debug_background:
            self.debug_background.enabled = self.debug_panel_visible
        
        # Toggle all debug text elements
        for text_element in self.debug_texts.values():
            text_element.enabled = self.debug_panel_visible
        
        status = "shown" if self.debug_panel_visible else "hidden"
        logger.info(f"Debug panel {status}")
    
    def show_message(self, message, duration=3.0):
        """Show a temporary message on screen"""
        # Create temporary message text
        message_text = Text(
            message,
            position=(0, -0.4, -0.05),
            scale=1.5,
            color=color.yellow,
            parent=camera.ui,
            background=True
        )
        
        # Auto-remove after duration
        destroy(message_text, delay=duration)
        
        logger.debug(f"Showing message: {message}")
    
    def cleanup(self):
        """Clean up UI elements"""
        # Destroy debug panel elements
        if self.debug_background:
            destroy(self.debug_background)
        
        for text_element in self.debug_texts.values():
            destroy(text_element)
        
        self.debug_texts.clear()
        
        logger.info("UI Manager cleanup complete")

"""
    def _continuously_disable_default_ui(self):
        #Continuously check and disable any default UI that might appear
        try:
            # Check for new UI entities that might have appeared
            for entity in scene.entities:
                if (hasattr(entity, 'text') and entity.enabled and 
                    hasattr(entity, 'parent') and entity.parent == camera.ui):
                    text_str = str(entity.text).lower()
                    if any(word in text_str for word in ['fps', 'collision', 'entities', 'ms']) and entity not in self.debug_texts.values():
                        entity.enabled = False
        except Exception:
            pass  # Silently ignore errors in continuous checking
    """