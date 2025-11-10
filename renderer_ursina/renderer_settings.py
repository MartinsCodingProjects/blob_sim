class Settings:
    def __init__(self):
        self.state = "development"
        self.debug = True
        self.renderer='ursina'

        # Renderer Settings
        self.movement_speed = 20.0
        self.movement_speed_boost_factor = 10.0
        self.mouse_sensitivity = 100.0
        self.smooth_factor = 0.1

        self.default_camera_position = (65, -141.5, 133.7)  # Adjusted for 100x100 normalized world
        self.default_camera_rotation = (-55.7, 180)

        # Normalized renderer world (fixed size for consistent scene)
        self.RENDERER_WORLD_SIZE = 100  # Fixed renderer world size (100x100)
        self.RENDERER_WORLD_HEIGHT = 5  # Fixed height
        
        # Simulation world size (will be received from simulation)
        self.SIM_WORLD_LENGTH = 500  # Default/fallback values
        self.SIM_WORLD_WIDTH = 500   # Will be updated from simulation data
        self.SIM_WORLD_HEIGHT = 5
        
        # Normalization settings
        self.auto_normalize_coordinates = True
        self.min_entity_scale = 0.1  # Minimum scale factor for entities
        self.max_entity_scale = 10.0  # Maximum scale factor for entities

    def get_network_settings(self):
            return {
                "mode": "socket",
                "host": "localhost",
                "port": 5000
            }