from abc import ABC, abstractmethod

import logging
logger = logging.getLogger("BLOB_ACTION")

class BlobAction(ABC):
    def __init__(self, blob, parameters=None):
        self.blob = blob
        self.parameters = parameters or {}

    # add method for old child-classes, that handles blobs going idle
    def go_idle(self):
        self.blob.state = "idle"
        self.blob.is_moving = False
        self.blob.direction = (0, 0, 0)
        # Keep walking_speed as blob's constant property - don't reset to 0
        self.blob.action_end_time = None
        self.blob.world.undecided_blobs.append(self.blob)
    
    @abstractmethod
    def execute(self):
        pass

class StartWalkDirectionAction(BlobAction):
    def execute(self):
        if not self.blob.alive:
            logger.debug(f"Current_time: {round(self.blob.world.current_sim_time, 3)} - At {self.blob.location} {self.blob.name} cannot walk - not alive")
            return
        
        # ALL the walking logic is HERE, not in blob
        direction = self.parameters.get("direction", [1, 0, 0])
        speed = self.parameters.get("speed", 1.0)
        
        # Directly modify blob state
        self.blob.state = "walking"
        self.blob.is_moving = True
        self.blob.direction = direction
        self.blob.walking_speed = speed
        
        logger.debug(f"Current_time: {round(self.blob.world.current_sim_time, 3)} - At {self.blob.location} {self.blob.name} starts walking in direction {direction} at speed {speed}")

class StartWalkDirectionTimedAction(BlobAction):
    def execute(self):
        if not self.blob.alive:
            return
        
        # ALL the timed walking logic is HERE
        direction = self.parameters.get("direction", [1, 0, 0])
        speed = self.parameters.get("speed", 1.0)
        duration = self.parameters.get("duration", 1.0)
        
        # Directly modify blob state
        self.blob.state = "walking_timed"
        self.blob.is_moving = True
        self.blob.direction = direction
        self.blob.walking_speed = speed
        # Store when this action should end
        self.blob.action_end_time = self.parameters.get("start_time", 0) + duration
        
        logger.debug(f"Current_time: {round(self.blob.world.current_sim_time, 3)} - At {self.blob.location} {self.blob.name} starts walking for {duration} hours")

class EndWalkDirectionTimedAction(BlobAction):
    def execute(self):
        # ALL the "go idle" logic is HERE
        self.go_idle()
        # direction is already set to (0,0,0) in go_idle()
        # walking_speed should remain the blob's constant property
        # action_end_time is already set to None in go_idle()
        
        logger.debug(f"Current_time: {round(self.blob.world.current_sim_time, 3)} - At {self.blob.location} {self.blob.name} stops walking and goes idle")

class StartRestAction(BlobAction):
    def execute(self):
        if not self.blob.alive:
            return
        
        # ALL the rest logic is HERE
        duration = self.parameters.get("duration", 0.5)
        
        # Directly modify blob state
        self.blob.state = "resting"
        self.blob.energy += 10  # Resting restores energy
        self.blob.action_end_time = self.parameters.get("start_time", 0) + duration
        
        logger.debug(f"Current_time: {round(self.blob.world.current_sim_time, 3)} - At {self.blob.location} {self.blob.name} starts resting for {duration} hours")

class EndRestAction(BlobAction):
    def execute(self):
        # ALL the "end rest" logic is HERE
        self.go_idle()
        self.blob.action_end_time = None
        
        logger.debug(f"Current_time: {round(self.blob.world.current_sim_time, 3)} - At {self.blob.location} {self.blob.name} finishes resting")

class EndInteractionAction(BlobAction):
    def execute(self):
        # Handle end of interaction - free up blob states
        interaction_id = self.parameters.get("interaction_id")
        participant_ids = self.parameters.get("participants", [])
        
        # Find all participant blobs and free them
        for participant_id in participant_ids:
            for blob in self.blob.world.population:
                if blob.id == participant_id and blob.current_interaction_id == interaction_id:
                    blob.interaction_state = "free" 
                    blob.current_interaction_id = None
                    blob.interaction_end_time = 0.0
                    logger.debug(f"Current_time: {round(self.blob.world.current_sim_time, 3)} - {blob.name} freed from interaction {interaction_id}")

# Factory stays the same
class BlobActionFactory:
    _action_mapping = {
        "start_walk_direction": StartWalkDirectionAction,
        "start_walk_direction_timed": StartWalkDirectionTimedAction,
        "end_walk_direction_timed": EndWalkDirectionTimedAction,
        "start_rest": StartRestAction,
        "end_rest": EndRestAction,
        "end_interaction": EndInteractionAction,
    }
    
    @classmethod
    def create_action(cls, event_type, blob, parameters=None):
        action_class = cls._action_mapping.get(event_type)
        if action_class is None:
            raise ValueError(f"Unknown event type: {event_type}")
        return action_class(blob, parameters)