from .blob import Blob
from ..controllers.events import EventScheduler
from .interaction import Interaction

import random
import math
import numpy as np

import logging
logger = logging.getLogger("WORLD")


class World:
    def __init__(self, settings=None):
        self.settings = settings
        self.world_name = self.settings.WORLD_NAME if settings else "Blobbingen"
        self.initial_population = self.settings.WORLD_INITIAL_POPULATION if settings else 2
        self.blob_count = 0
        self.things = []
        self.population = []
        self.undecided_blobs = []
        # Hybrid solution: Global NumPy array for efficient interaction checks
        self.blob_locations = np.empty((0, 3))  # 3D locations for all blobs
        self.things_locations = np.empty((0, 3))  # 3D locations for all things
        # what is stored in self.blob_locations? -> x,y,z coordinates of each blob in population with same index
        # maybe add another np array for other properties like energy, state, etc. so that we can avoid looping through blobs often
        self.length = self.settings.WORLD_LENGTH if settings else 130
        self.width = self.settings.WORLD_WIDTH if settings else 130
        self.height = self.settings.WORLD_HEIGHT if settings else 10
        self.day_phase = "day"
        self.day = 0.0
        self.hour = 0.0
        self.day_hour = 0.0
        self.hours_per_day = self.settings.WORLD_HOURS_PER_DAY if settings else 10
        self.night_percentage = self.settings.WORLD_NIGHT_PERCENTAGE if settings else 0.3
        
        self.current_sim_time = 0.0
        self.event_scheduler = EventScheduler()
        # print world creation info
        logger.info(f"World '{self.world_name}' created with dimensions ({self.length}, {self.width}, {self.height})")

        self.renderer_data_world = {
            "world_data": {
                "name": self.world_name,
                "dimensions": (self.length, self.width, self.height),
                "day_phase": self.day_phase,
                "day": self.day,
                "hour": self.hour,
                "day_hour": self.day_hour,
                "current_sim_time": self.current_sim_time
            },
            "blobs_data": [],
            "things_data": []
        }

    def update(self, sim_delta_time):
        """Main world update called continuously."""
        old_sim_time = self.current_sim_time
        self.current_sim_time += sim_delta_time
        self.hour = int(math.floor(self.current_sim_time))
        self.day_hour = (self.hour % self.hours_per_day) + 1  # 1-10 within each day
        self.day = (self.hour // self.hours_per_day) + 1      # Day starts at 1
        # if (int(math.floor(old_sim_time)) != int(math.floor(self.current_sim_time))):
            # logger.info(f"--- World Update: Day {self.day}, Hour {self.hour} ---")
        
        # Process events up till current_sim_time
        self.event_scheduler.process_events_until(self.current_sim_time)

        # check if decisions are needed and process them
        self.handle_decisions_events_needed(self.current_sim_time)

        # Update all blob states first (movement, aging, etc.)
        for blob in self.population:
            blob.update(sim_delta_time)

        # Check for interactions after all blobs have moved (optimized world-level approach)
        self.check_all_interactions()

    def check_all_interactions(self):
        """
        Optimized world-level interaction checking using Interaction system.
        
        This method efficiently detects interactions and creates Interaction objects
        to handle them properly without duplicates.
        
        Process:
        1. Calculate all pairwise distances using vectorized operations
        2. Detect interaction types based on visual ranges
        3. Create Interaction objects for each unique interaction
        4. Process all interactions once per frame
        """
        
        # Skip if no blobs or only one blob exists
        if len(self.population) <= 1:
            return
            
        try:
            # Collect all interactions for this frame
            interactions_this_frame = []
            interaction_counter = 0
            
            # STEP 1: Update blob interaction states based on current time
            for blob in self.population:
                if blob.interaction_state == "occupied" and self.current_sim_time >= blob.interaction_end_time:
                    blob.interaction_state = "free"
                    blob.current_interaction_id = None
                    blob.interaction_end_time = 0.0
                    logger.debug(f"Blob {blob.name} returned to free state")
            
            # STEP 2: Calculate all pairwise distances in one vectorized operation
            blob_locations_array = self.blob_locations  # Shape: (N, 3)
            
            # Use broadcasting to calculate all pairwise distances at once
            distances = np.linalg.norm(
                blob_locations_array[:, np.newaxis, :] - blob_locations_array[np.newaxis, :, :], 
                axis=2
            )
            
            # STEP 3: Detect blob-blob interactions with state checking
            for i in range(len(self.population)):
                blob_a = self.population[i]
                if not blob_a.alive:
                    continue
                    
                for j in range(i + 1, len(self.population)):
                    blob_b = self.population[j]
                    if not blob_b.alive:
                        continue
                    
                    # CRITICAL: Skip if BOTH blobs are occupied (prevents infinite loops)
                    # But allow interactions if only ONE is occupied (new arrivals)
                    if blob_a.interaction_state == "occupied" and blob_b.interaction_state == "occupied":
                        continue
                    
                    distance = distances[i, j]
                    
                    # Determine interaction type based on visual ranges
                    a_can_see_b = distance <= blob_a.visual_range
                    b_can_see_a = distance <= blob_b.visual_range
                    
                    if a_can_see_b and b_can_see_a:
                        # Both blobs can see each other - mutual interaction
                        interaction = Interaction(
                            f"blob_mutual_{interaction_counter}",
                            [blob_a, blob_b],
                            "blob_mutual"
                        )
                        interactions_this_frame.append(interaction)
                        interaction_counter += 1
                        
                    elif a_can_see_b and not b_can_see_a:
                        # Only blob_a can see blob_b - one-sided interaction
                        interaction = Interaction(
                            f"blob_one_sided_{interaction_counter}",
                            [blob_a, blob_b],  # Observer first, target second
                            "blob_one_sided"
                        )
                        interactions_this_frame.append(interaction)
                        interaction_counter += 1
                        
                    elif not a_can_see_b and b_can_see_a:
                        # Only blob_b can see blob_a - one-sided interaction
                        interaction = Interaction(
                            f"blob_one_sided_{interaction_counter}",
                            [blob_b, blob_a],  # Observer first, target second
                            "blob_one_sided"
                        )
                        interactions_this_frame.append(interaction)
                        interaction_counter += 1
            
            # STEP 4: Blob-to-Things Interactions
            if len(self.things) > 0 and len(self.things_locations) > 0:
                # Vectorized distance calculation between all blobs and all things
                blob_thing_distances = np.linalg.norm(
                    blob_locations_array[:, np.newaxis, :] - self.things_locations[np.newaxis, :, :],
                    axis=2
                )
                
                # Check each blob against all things
                for i, blob in enumerate(self.population):
                    if not blob.alive:
                        continue
                    
                    # Allow blob-thing interactions even if blob is occupied
                    # (things don't have occupation state)
                        
                    # Find things within blob's visual range
                    thing_indices_in_range = np.where(blob_thing_distances[i, :] <= blob.visual_range)[0]
                    
                    for thing_idx in thing_indices_in_range:
                        thing = self.things[thing_idx]
                        
                        # Create blob-thing interaction
                        interaction = Interaction(
                            f"blob_thing_{interaction_counter}",
                            [blob, thing],
                            "blob_thing"
                        )
                        interactions_this_frame.append(interaction)
                        interaction_counter += 1
            
            # STEP 5: Process all interactions once
            for interaction in interactions_this_frame:
                interaction.process()
                
            # Log interaction summary if any occurred
            if interactions_this_frame:
                logger.debug(f"Processed {len(interactions_this_frame)} interactions this frame")
                        
        except Exception as e:
            logger.error(f"Error in world interaction check: {e}")
            # Log additional debug info
            logger.error(f"Population size: {len(self.population)}, Blob locations shape: {self.blob_locations.shape}")
            logger.error(f"Things count: {len(self.things)}, Things locations shape: {self.things_locations.shape}")
            logger.error(f"Interactions created: {len(interactions_this_frame) if 'interactions_this_frame' in locals() else 0}")

    def handle_decisions_events_needed(self, current_sim_time):
        """ let undecided blobs decide on actions and handle events """
        if len(self.undecided_blobs) > 0:
            logger.info(f"Undecided blobs at time {current_sim_time}: {[blob.id for blob in self.undecided_blobs]}")

        blobs_to_process = self.undecided_blobs.copy()
        for blob in blobs_to_process:
            decision = blob.decide_action(self, current_sim_time)
            if decision is None:
                logger.debug(f"Blob {blob.id} made no decision.")
                continue

            if decision["action"] == "start_walk_direction":
                self.event_scheduler.schedule_event(
                    time = current_sim_time,
                    event_type = "start_walk_direction",
                    blob_id = blob.id,
                    data={"blob": blob, "direction": decision["direction"], "speed": decision["speed"]}
                )
            elif decision["action"] == "start_walk_direction_timed":
                self.event_scheduler.schedule_event(
                    time = current_sim_time,
                    event_type = "start_walk_direction_timed",
                    blob_id = blob.id,
                    data={"blob": blob, "direction": decision["direction"], "speed": decision["speed"], "duration": decision["duration"], "start_time": current_sim_time}
                )
                self.event_scheduler.schedule_event(
                    time = current_sim_time + decision["duration"], # duration in hours
                    event_type = "end_walk_direction_timed",
                    blob_id = blob.id,
                    data={"blob": blob}
                )
            elif decision["action"] == "start_rest":
                self.event_scheduler.schedule_event(
                    time = current_sim_time,
                    event_type = "start_rest",
                    blob_id = blob.id,
                    data={"blob": blob, "duration": decision["duration"], "start_time": current_sim_time}
                )
                self.event_scheduler.schedule_event(
                    time = current_sim_time + decision["duration"], #duration in hours
                    event_type = "end_rest",
                    blob_id = blob.id,
                    data={"blob": blob}
                )
            
            self.undecided_blobs.remove(blob)

    def blob_birth(self):
        self.blob_count += 1
        location = self.get_random_coordinates(dimensions=2) + (0,)  # z=0 for ground level
        new_blob = Blob(self.blob_count, self.settings, self, location)
        self.population.append(new_blob)
        self.undecided_blobs.append(new_blob)

        # Add to global locations array
        self.blob_locations = np.vstack([self.blob_locations, location])

    def create_initial_population(self):
        n = 0
        while n < self.initial_population:
            n += 1
            self.blob_birth()
        logger.info(f"Initial population created: {self.initial_population} blobs")

    def get_random_coordinates(self, dimensions):
        """Generate random coordinates within the world's dimensions."""
        if dimensions == 2:
            return (
                random.randint(0, self.length - 1),
                random.randint(0, self.width - 1),
            )
        elif dimensions == 3:
            return (
                random.randint(0, self.length - 1),
                random.randint(0, self.width - 1),
                random.randint(0, self.height - 1),
            )
        else:
            raise ValueError("Invalid dimensions. Only 2D and 3D coordinates are supported.")

    def update_renderer_world_data(self):
        """Update the world data for the renderer."""
        self.renderer_data_world["world_data"] = {
            "name": self.world_name,
            "dimensions": (self.length, self.width, self.height),
            "day_phase": self.day_phase,
            "day": self.day,
            "hour": self.hour,
            "day_hour": self.day_hour,
            "current_sim_time": self.current_sim_time
        }
        # Update blobs data
        blobs_data = []
        for blob in self.population:
            blob_data = blob.get_blobs_renderer_data()
            blobs_data.append(blob_data)
        self.renderer_data_world["blobs_data"] = blobs_data
        
        # Update things data
        things_data = []
        for thing in self.things:
            thing_data = thing.get_things_renderer_data()
            things_data.append(thing_data)
        self.renderer_data_world["things_data"] = things_data
