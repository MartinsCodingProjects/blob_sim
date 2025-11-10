"""
Entity Manager
Manages all simulation entities (blobs, things, etc.) in the 3D renderer.
"""
from ursina import *
import logging
from entities.blob_entity import BlobEntity
from entities.thing_entity import ThingEntity

logger = logging.getLogger("RENDERER_ENTITIES")

class CoordinateNormalizer:
    """Handles coordinate normalization between simulation and renderer space"""
    
    def __init__(self, renderer_size=100):
        self.renderer_size = renderer_size
        self.sim_size_x = 500  # Default fallback
        self.sim_size_y = 500  # Default fallback
        self.scale_factor_x = 1.0
        self.scale_factor_y = 1.0
        self.entity_scale_factor = 1.0
        
    def update_sim_world_size(self, sim_width, sim_height):
        """Update simulation world size and recalculate scale factors"""
        self.sim_size_x = sim_width
        self.sim_size_y = sim_height
        
        # Calculate scale factors
        self.scale_factor_x = self.renderer_size / sim_width
        self.scale_factor_y = self.renderer_size / sim_height
        
        # Use the smaller scale factor to maintain aspect ratio
        self.entity_scale_factor = min(self.scale_factor_x, self.scale_factor_y)
        
        logger.info(f"Updated normalization: sim({sim_width}x{sim_height}) -> renderer({self.renderer_size}x{self.renderer_size})")
        logger.info(f"Scale factors: X={self.scale_factor_x:.3f}, Y={self.scale_factor_y:.3f}, Entity={self.entity_scale_factor:.3f}")
    
    def normalize_position(self, sim_position):
        """Convert simulation coordinates to renderer coordinates"""
        if len(sim_position) >= 3:
            x, y, z = sim_position[0], sim_position[1], sim_position[2]
            print(f"HIIIIIIIIIIIIIINT: {x}, {y}, {z}")
        elif len(sim_position) >= 2:
            x, y, z = sim_position[0], sim_position[1], 0
        else:
            return Vec3(0, 0, 0)
        
        # Normalize to renderer space (keep 0-100 range to match scene)
        # Try swapping the coordinate mapping - maybe sim Y should map to renderer X
        renderer_x = y * self.scale_factor_y  # Sim Y -> Renderer X  
        renderer_z = x * self.scale_factor_x  # Sim X -> Renderer Z   
        renderer_y = -0.4  # Place blobs slightly above ground plane (which is at Y = -0.5)
        
        # Debug logging for coordinate mapping
        if hasattr(self, '_debug_count') and self._debug_count < 10:
            logger.info(f"Coordinate mapping: sim({x:.1f}, {y:.1f}, {z:.1f}) -> renderer({renderer_x:.1f}, {renderer_y:.1f}, {renderer_z:.1f})")
            logger.info(f"Scale factors: X={self.scale_factor_x:.3f}, Y={self.scale_factor_y:.3f}")
            logger.info(f"Ground plane covers X:0-100, Z:0-100 at Y=-0.5")
            self._debug_count += 1
        elif not hasattr(self, '_debug_count'):
            self._debug_count = 1
        
        return Vec3(renderer_x, renderer_y, renderer_z)
    
    def normalize_radius(self, sim_radius):
        """Convert simulation radius to renderer radius"""
        return sim_radius * self.entity_scale_factor
    
    def get_scale_info(self):
        """Get current scale information for debugging"""
        return {
            'sim_size': (self.sim_size_x, self.sim_size_y),
            'renderer_size': self.renderer_size,
            'scale_factor_x': self.scale_factor_x,
            'scale_factor_y': self.scale_factor_y,
            'entity_scale': self.entity_scale_factor
        }

class EntityManager:
    """Manages all simulation entities and their 3D representations"""
    
    def __init__(self, settings=None):
        """Initialize entity manager"""
        self.settings = settings
        
        # Entity storage
        self.blob_entities = {}  # blob_id -> BlobEntity
        self.thing_entities = {}  # thing_id -> ThingEntity
        
        # Entity pools for performance (optional future optimization)
        self.blob_pool = []
        self.thing_pool = []
        
        # Animation and state management
        self.update_interval = 0.016  # ~60 FPS
        self.last_update_time = 0
        
        # Coordinate normalization
        renderer_size = settings.RENDERER_WORLD_SIZE if settings else 100
        self.normalizer = CoordinateNormalizer(renderer_size)
        self.sim_world_initialized = False
        
        logger.info("Entity Manager initialized with coordinate normalization")
    
    def update_from_simulation_data(self, simulation_data):
        """Update all entities based on new simulation data"""
        if not simulation_data:
            return
        
        # Check for world size information and update normalizer
        self._update_world_normalization(simulation_data)
        
        # Update blobs
        blobs_data = simulation_data.get('blobs_data', [])
        self._update_blobs(blobs_data)
        
        # Update things
        things_data = simulation_data.get('things_data', [])
        self._update_things(things_data)
        
        # Log update stats
        logger.debug(f"Updated {len(self.blob_entities)} blobs, {len(self.thing_entities)} things")
    
    def _update_world_normalization(self, simulation_data):
        """Update coordinate normalization based on simulation world info"""
        # Check for world size in simulation data (matches sim-side structure)
        world_data = simulation_data.get('world_data', {})
        if world_data and not self.sim_world_initialized:
            # Extract dimensions tuple: (length, width, height)
            dimensions = world_data.get('dimensions')
            if dimensions and len(dimensions) >= 2:
                sim_length = dimensions[0]  # X dimension
                sim_width = dimensions[1]   # Y dimension
                
                # Update normalizer with actual simulation world size
                self.normalizer.update_sim_world_size(sim_length, sim_width)
                self.sim_world_initialized = True
                
                logger.info(f"Initialized world normalization from sim world_data: {sim_length}x{sim_width} -> {self.normalizer.renderer_size}x{self.normalizer.renderer_size}")
            else:
                # Fallback to settings if dimensions not available
                sim_length = self.settings.SIM_WORLD_LENGTH if self.settings else 500
                sim_width = self.settings.SIM_WORLD_WIDTH if self.settings else 500
                self.normalizer.update_sim_world_size(sim_length, sim_width)
                self.sim_world_initialized = True
                logger.info(f"Initialized world normalization from fallback settings: {sim_length}x{sim_width}")
    
    def _update_blobs(self, blobs_data):
        """Update blob entities from simulation data"""
        current_blob_ids = set()
        
        for blob_data in blobs_data:
            blob_id = blob_data.get('id')
            if blob_id is None:
                continue
            
            current_blob_ids.add(blob_id)
            
            # Create or update blob entity
            if blob_id not in self.blob_entities:
                self._create_blob_entity(blob_id, blob_data)
            else:
                self._update_blob_entity(blob_id, blob_data)
        
        # Remove blobs that no longer exist
        blob_ids_to_remove = set(self.blob_entities.keys()) - current_blob_ids
        for blob_id in blob_ids_to_remove:
            self._remove_blob_entity(blob_id)
    
    def _create_blob_entity(self, blob_id, blob_data):
        """Create a new blob entity"""
        try:
            # Normalize blob data coordinates and scale
            normalized_data = self._normalize_entity_data(blob_data)
            blob_entity = BlobEntity(blob_id, normalized_data, self.settings)
            self.blob_entities[blob_id] = blob_entity
            
            orig_pos = blob_data.get('location', [0,0,0])
            norm_pos = normalized_data.get('location', [0,0,0])
            logger.debug(f"Created blob entity {blob_id}: {orig_pos} -> {norm_pos}")
        except Exception as e:
            logger.error(f"Failed to create blob entity {blob_id}: {e}")
    
    def _update_blob_entity(self, blob_id, blob_data):
        """Update an existing blob entity"""
        blob_entity = self.blob_entities.get(blob_id)
        if blob_entity:
            try:
                # Normalize blob data coordinates and scale
                normalized_data = self._normalize_entity_data(blob_data)
                blob_entity.update_from_data(normalized_data)
            except Exception as e:
                logger.error(f"Failed to update blob entity {blob_id}: {e}")
    
    def _remove_blob_entity(self, blob_id):
        """Remove a blob entity"""
        blob_entity = self.blob_entities.get(blob_id)
        if blob_entity:
            try:
                blob_entity.destroy()
                del self.blob_entities[blob_id]
                logger.debug(f"Removed blob entity {blob_id}")
            except Exception as e:
                logger.error(f"Failed to remove blob entity {blob_id}: {e}")
    
    def _update_things(self, things_data):
        """Update thing entities from simulation data"""
        current_thing_ids = set()
        
        for thing_data in things_data:
            thing_id = thing_data.get('id')
            if thing_id is None:
                continue
            
            current_thing_ids.add(thing_id)
            
            # Create or update thing entity
            if thing_id not in self.thing_entities:
                self._create_thing_entity(thing_id, thing_data)
            else:
                self._update_thing_entity(thing_id, thing_data)
        
        # Remove things that no longer exist
        thing_ids_to_remove = set(self.thing_entities.keys()) - current_thing_ids
        for thing_id in thing_ids_to_remove:
            self._remove_thing_entity(thing_id)
    
    def _create_thing_entity(self, thing_id, thing_data):
        """Create a new thing entity"""
        try:
            # Normalize thing data coordinates and scale
            normalized_data = self._normalize_entity_data(thing_data)
            thing_entity = ThingEntity(thing_id, normalized_data, self.settings)
            self.thing_entities[thing_id] = thing_entity
            
            logger.debug(f"Created thing entity {thing_id}")
        except Exception as e:
            logger.error(f"Failed to create thing entity {thing_id}: {e}")
    
    def _update_thing_entity(self, thing_id, thing_data):
        """Update an existing thing entity"""
        thing_entity = self.thing_entities.get(thing_id)
        if thing_entity:
            try:
                # Normalize thing data coordinates and scale
                normalized_data = self._normalize_entity_data(thing_data)
                thing_entity.update_from_data(normalized_data)
            except Exception as e:
                logger.error(f"Failed to update thing entity {thing_id}: {e}")
    
    def _remove_thing_entity(self, thing_id):
        """Remove a thing entity"""
        thing_entity = self.thing_entities.get(thing_id)
        if thing_entity:
            try:
                thing_entity.destroy()
                del self.thing_entities[thing_id]
                logger.debug(f"Removed thing entity {thing_id}")
            except Exception as e:
                logger.error(f"Failed to remove thing entity {thing_id}: {e}")
    
    def update(self):
        """Update all entities (animations, states, etc.)"""
        current_time = time.time()
        
        # Throttle updates to avoid performance issues
        if current_time - self.last_update_time < self.update_interval:
            return
        
        # Update all blob entities
        for blob_entity in self.blob_entities.values():
            blob_entity.update()
        
        # Update all thing entities
        for thing_entity in self.thing_entities.values():
            thing_entity.update()
        
        self.last_update_time = current_time
    
    def _normalize_entity_data(self, entity_data):
        """Normalize entity coordinates and scale for renderer space"""
        normalized_data = entity_data.copy()
        
        # Normalize position coordinates
        if 'location' in entity_data:
            sim_position = entity_data['location']
            normalized_position = self.normalizer.normalize_position(sim_position)
            normalized_data['location'] = [normalized_position.x, normalized_position.y, normalized_position.z]
        
        # Normalize radius/size
        if 'radius' in entity_data:
            sim_radius = entity_data['radius']
            normalized_radius = self.normalizer.normalize_radius(sim_radius)
            normalized_data['radius'] = normalized_radius
        
        # Normalize size (alternative to radius)
        if 'size' in entity_data:
            sim_size = entity_data['size']
            normalized_size = self.normalizer.normalize_radius(sim_size)
            normalized_data['size'] = normalized_size
        
        return normalized_data
    
    def get_normalization_info(self):
        """Get current normalization information for debugging"""
        return self.normalizer.get_scale_info()
    
    def get_entity_count(self):
        """Get current entity counts"""
        return {
            'blobs': len(self.blob_entities),
            'things': len(self.thing_entities)
        }
    
    def get_blob_entity(self, blob_id):
        """Get a specific blob entity by ID"""
        return self.blob_entities.get(blob_id)
    
    def get_thing_entity(self, thing_id):
        """Get a specific thing entity by ID"""
        return self.thing_entities.get(thing_id)
    
    def cleanup(self):
        """Clean up all entities"""
        # Clean up blobs
        for blob_entity in list(self.blob_entities.values()):
            blob_entity.destroy()
        self.blob_entities.clear()
        
        # Clean up things
        for thing_entity in list(self.thing_entities.values()):
            thing_entity.destroy()
        self.thing_entities.clear()
        
        logger.info("Entity Manager cleanup complete")