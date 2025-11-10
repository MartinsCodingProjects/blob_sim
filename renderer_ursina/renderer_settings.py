class Settings:
    def __init__(self):
        self.state = "development"
        self.debug = True
        self.renderer='ursina'

    def get_network_settings(self):
            return {
                "mode": "socket",
                "host": "localhost",
                "port": 5000
            }