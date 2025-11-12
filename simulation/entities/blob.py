import random, math
import numpy as np

import logging
logger = logging.getLogger("BLOB")

class Blob:
    def __init__(self, id, settings, world, location=(0, 0, 0)):
        self.settings = settings
        # init tracking properties
        self.id = id
        self.gender = random.choice(["male", "female", "unisex"])
        self.name = self.generate_name(self.gender)
        self.birth_hour = world.hour
        self.generation = 0
        self.age = 0
        self.alive = True
        self.world = world

        # init properties for lifecycle management
        self.reproduction_state = "asexual"
        self.lifespan = self.settings.BLOB_AVERAGE_LIFESPAN if self.settings else 100
        self.life_stage = "adult"
        self.health = 100

        # init physical properties
        self.radius = self.settings.BLOB_RADIUS if self.settings else 1.0
        self.visual_range = 3.0
        self.color = "blue"
        self.location = location

        # init properties for behavior and interaction
        self.state = "idle"
        self.energy = self.settings.BLOB_INITIAL_ENERGY if self.settings else 100
        self.is_moving = False
        self.walking_speed = self.settings.BLOB_WALKING_SPEED if self.settings else 5  # units per hour - increased for visible movement
        self.direction = (0, 0, 0)
        
        # Interaction state management to prevent infinite loops
        self.interaction_state = "free"  # "free", "occupied", "cooldown"
        self.current_interaction_id = None
        self.interaction_end_time = 0.0

        #print blob creation info
        logger.info(f"Blob created - ID: {self.id}, Name: {self.name}, inital lifespan: {self.lifespan}, energy: {self.energy}")

    def update(self, sim_delta_time):
        """
        Update blob state based on sim_delta_time.
        Handle movement, actions, aging, and energy consumption.
        """
        # Update age
        self.age += sim_delta_time
        if self.age > self.lifespan:
            self.alive = False
        
        # Handle movement
        if self.is_moving:
            direction = list(self.direction)
            while len(direction) < 3:
                direction.append(0.0)
            dx = direction[0] * self.walking_speed * sim_delta_time
            dy = direction[1] * self.walking_speed * sim_delta_time
            dz = direction[2] * self.walking_speed * sim_delta_time
            
            # Debug movement calculation
            #print(f"[MOVEMENT_DEBUG] {self.name} moving from {self.location} by ({dx:.6f}, {dy:.6f}, {dz:.6f}) with direction {direction} speed {self.walking_speed} delta {sim_delta_time}")
            
            new_location = (
                self.location[0] + dx,
                self.location[1] + dy,
                self.location[2] + dz
            )
            #check if new location is within world bounds
            if (0 <= new_location[0] < self.world.length and
                0 <= new_location[1] < self.world.width and
                0 <= new_location[2] < self.world.height):
                self.location = new_location
            else:
                logger.debug(f"Blob {self.name} (ID: {self.id}) attempted to move out of bounds to {new_location}. Movement cancelled.")
                # Reset position to stay within bounds
                new_location = (
                    max(0, min(new_location[0], self.world.length - 1)),
                    max(0, min(new_location[1], self.world.width - 1)),
                    max(0, min(new_location[2], self.world.height - 1))
                )
                self.location = new_location
                # trigger event that ends movement and makes blob idle, wanting new decision next update
                self.is_moving = False
                self.state = "idle"
                self.direction = (0, 0, 0)
                print(f"[BOUNDARY_DEBUG] {self.name} hit boundary, stopped moving")

            # Update global locations array (hybrid approach) - COMMENTED OUT FOR DEBUGGING
            # blob_idx = self.world.population.index(self)
            # self.update_blob_location(blob_idx, new_location)

    def update_blob_location(self, blob_idx, new_location):
        """Update the global blob locations array when a blob moves."""
        if 0 <= blob_idx < len(self.world.blob_locations):
            self.world.blob_locations[blob_idx] = new_location
            
    @staticmethod
    def generate_name(gender):
        # Prefixes and suffixes for male, female, and unisex names
        prefixes = {
            "male": ["Zor", "Blib", "Thra", "Plon", "Snor", "Grak", "Dro", "Klon"],
            "female": ["Glo", "Fla", "Bli", "Tra", "Ila", "Vra", "Sha", "Nia"],
            "unisex": ["Xor", "Quib", "Plo", "Zin", "Cra", "Vex", "Twi", "Lom"]
        }
        suffixes = {
            "male": ["gon", "dor", "zor", "bix", "nak", "tor", "vik", "rax"],
            "female": ["lia", "nia", "sha", "vra", "lix", "ora", "ina", "exa"],
            "unisex": ["blob", "nix", "zor", "rix", "lox", "vor", "pix", "tan"]
        }

        # Select prefixes and suffixes based on gender
        if gender not in prefixes:
            gender = "unisex"  # Default to unisex if gender is invalid

        prefix = random.choice(prefixes[gender])
        suffix = random.choice(suffixes[gender])

        return prefix + suffix
    
    def decide_action(self, world, current_time):
        # Placeholder for decision-making logic

        action_type = random.choice(["start_walk_direction_timed", "start_rest"])

        if action_type == "start_walk_direction":
            # Random direction
            direction = self.random_direction()
            return {
                "action": action_type,
                "direction": direction,
                "speed": self.walking_speed
            }
        elif action_type == "start_walk_direction_timed":
            # Random direction
            direction = self.random_direction()
            # random duration, 2-6 hours for testing (later can be 24-72 for full simulation)
            duration = random.uniform(2, 6)  # duration in hours
            return {
                "action": action_type,
                "direction": direction,
                "speed": self.walking_speed,
                "duration": duration
            }
        elif action_type == "start_rest":
            duration = random.uniform(0.1, 1.0)  # rest duration in hours
            return {
                "action": "start_rest",
                "duration": duration
            }

    def random_direction(self, dimensions=2):
        """Generate a random unit direction vector."""
        if dimensions == 2:
            theta = random.uniform(0, 2 * math.pi)  # Angle in 2D
            return [math.cos(theta), math.sin(theta)]
        elif dimensions == 3:
            # Generate random angles
            theta = random.uniform(0, 2 * math.pi)  # Horizontal angle
            phi = random.uniform(0, math.pi)  # Vertical angle

        dx = math.sin(phi) * math.cos(theta)
        dy = math.sin(phi) * math.sin(theta)
        dz = math.cos(phi)
        
        return [dx, dy, dz]

    def handle_interaction(self, other):
        """Placeholder for interaction logic."""
        other_name = getattr(other, 'name', str(other))
        interaction_logger = logging.getLogger("INTERACTIONS")
        interaction_logger.debug(f"Blob {self.name} (ID: {self.id}) interacts with {other_name}")
        # push events to worlds event scheduler etc based on logics
        # tdb

    def get_blobs_renderer_data(self):
        """Return a dictionary of blob data for rendering."""
        location_converted = self.location.tolist() if hasattr(self.location, 'tolist') else self.location
        direction_converted = self.direction.tolist() if hasattr(self.direction, 'tolist') else self.direction
        
        return {
            "id": self.id,
            "name": self.name,
            "location": location_converted,
            "color": self.color,
            "state": self.state,
            "alive": self.alive,
            "direction": direction_converted,
            "radius": self.radius
        }
