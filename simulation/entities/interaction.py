import logging

class Interaction:
    """
    Handles interactions between entities in the simulation world.
    
    Supports different interaction types:
    - blob_mutual: Both blobs can see each other
    - blob_one_sided: Only one blob can see the other
    - blob_thing: Blob interacts with a thing/object
    """
    
    def __init__(self, interaction_id, entities, interaction_type="proximity"):
        self.id = interaction_id
        self.entities = entities  # List of participating entities
        self.interaction_type = interaction_type
        self.processed = False
        self.logger = logging.getLogger("INTERACTIONS")

    def process(self):
        """Process the interaction based on type and entities involved."""
        if self.processed:
            return
        
        try:
            if self.interaction_type == "blob_mutual":
                self._handle_blob_mutual_interaction()
            elif self.interaction_type == "blob_one_sided":
                self._handle_blob_one_sided_interaction()
            elif self.interaction_type == "blob_thing":
                self._handle_blob_thing_interaction()
            else:
                self.logger.warning(f"Unknown interaction type: {self.interaction_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing interaction {self.id}: {e}")
        finally:
            self.processed = True

    def _handle_blob_mutual_interaction(self):
        """Handle interaction where both blobs can see each other."""
        if len(self.entities) != 2:
            return
            
        blob_a, blob_b = self.entities
        
        # Both blobs are aware of each other
        self.logger.debug(f"Mutual interaction {self.id}: {blob_a.name} ↔ {blob_b.name}")
        
        # Set interaction duration (example: 2 simulation hours)
        interaction_duration = 2.0
        end_time = blob_a.world.current_sim_time + interaction_duration
        
        # Mark both blobs as occupied to prevent new interactions
        for blob in [blob_a, blob_b]:
            blob.interaction_state = "occupied"
            blob.current_interaction_id = self.id
            blob.interaction_end_time = end_time
        
        # Schedule end of interaction event
        blob_a.world.event_scheduler.schedule_event(
            time=end_time,
            event_type="end_interaction",
            blob_id=blob_a.id,
            data={"blob": blob_a, "interaction_id": self.id, "participants": [blob_a.id, blob_b.id]}
        )
        
        self.logger.info(f"Mutual interaction started: {blob_a.name} ↔ {blob_b.name} (duration: {interaction_duration}h)")
        
        # Apply bidirectional effects here
        # Example: Energy exchange, communication, competition, etc.
        # You can add specific logic here like:
        # - Reproduction attempts
        # - Energy sharing
        # - Information exchange
        # - Territory disputes

    def _handle_blob_one_sided_interaction(self):
        """Handle interaction where only one blob can see the other."""
        if len(self.entities) != 2:
            return
            
        observer_blob, target_blob = self.entities
        
        # Only the observer blob is aware of the target
        self.logger.debug(f"One-sided interaction {self.id}: {observer_blob.name} → {target_blob.name}")
        
        # One-sided interactions are typically immediate (no occupation)
        # The observer reacts, but doesn't become "occupied"
        # This allows for dynamic behaviors like following, avoiding, etc.
        
        self.logger.info(f"One-sided interaction: {observer_blob.name} observes {target_blob.name}")
        
        # Apply one-sided effects here
        # Example: Stalking, following, avoiding, etc.
        # The target blob doesn't know about the observer
        
        # You can add specific logic here like:
        # - Observer changes direction
        # - Observer gains information about target  
        # - Observer decides to approach or avoid
        # - Observer starts following behavior

    def _handle_blob_thing_interaction(self):
        """Handle interaction between a blob and a thing/object."""
        if len(self.entities) != 2:
            return
            
        blob = self.entities[0]
        thing = self.entities[1]
        
        # Blob interacts with a world object
        thing_name = getattr(thing, 'name', f'Thing_{id(thing)}')
        self.logger.debug(f"Blob-Thing interaction {self.id}: {blob.name} → {thing_name}")
        
        # Blob-thing interactions are typically immediate (no long-term occupation)
        # Unless it's something like "eating" which takes time
        
        self.logger.info(f"Blob-Thing interaction: {blob.name} interacts with {thing_name}")
        
        # Apply blob-thing interaction effects here
        # Example: Eating food, avoiding obstacles, collecting resources
        
        # You can add specific logic here like:
        # - Food consumption (increase blob energy, possibly with duration)
        # - Obstacle avoidance (change direction immediately)  
        # - Resource collection (immediate pickup)
        # - Territory marking (immediate action)

    def get_entities_info(self):
        """Get information about entities in this interaction for debugging."""
        info = []
        for entity in self.entities:
            if hasattr(entity, 'name'):
                info.append(f"{entity.name} (ID: {entity.id})")
            else:
                info.append(f"Thing_{id(entity)}")
        return info