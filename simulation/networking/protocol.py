class NetworkProtocol:
    """
    Currently unused.

    Could later be used instead of the:
            renderer_data["sim_data"] = {
            "starting_realtime": self.starting_realtime,
            "current_realtime": self.current_realtime,
            "sim_ticks": self.sim_ticks,
            "renderer_ticks": self.renderer_ticks,
        }
    part of SimEngine.prepare_renderer_data() method.
    for wrapping world/entity/blob/thing data into standardized messages
    add meta-data to messages, timestamps, data types, version etc.
    """
    @staticmethod
    def create_message(data_type, payload):
        # Create standardized message format
        pass
        
    @staticmethod
    def parse_message(raw_message):
        # Parse incoming messages
        pass