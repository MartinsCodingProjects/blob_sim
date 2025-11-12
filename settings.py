class Settings:
    def __init__(self):
        # General Settings
        self.state = "development"
        self.debug = True
        # self.renderer='ursina'
        self.renderer = 'pygame'  # new pygame renderer

        # Simulation Settings
        self.SIMULATION_MAX_TIME = 10000 # hours
        self.SIMULATION_TIME_MULTIPLIER = 5  # 1 real second = 2 sim hours
        self.SIMULATION_FPS = 60  # Frames per second for renderer updates
        
        # Runtime Settings (can be modified during simulation)
        self.paused = True  # Start paused
        self.speed_multiplier = 1.0  # Runtime speed control

        # World Settings
        self.WORLD_NAME = "Blobbington"
        self.WORLD_HOURS_PER_DAY = 10
        self.WORLD_NIGHT_PERCENTAGE = 0.3
        self.WORLD_INITIAL_POPULATION = 4
        self.WORLD_LENGTH = 100
        self.WORLD_WIDTH = 100
        self.WORLD_HEIGHT = 5

        # Blob Settings
        self.BLOB_AVERAGE_LIFESPAN = 100000
        self.BLOB_INITIAL_ENERGY = 100
        self.BLOB_WALKING_SPEED = 5  # units per hour
        self.BLOB_RADIUS = 5.0
    
    def get_network_settings(self):
        return {
            "mode": "socket",
            "host": "localhost",
            "port": 5000
        }