"""
Entity Manager
Manages all simulation entities (blobs, things, etc.) in the 3D renderer.
"""
from ursina import *
import logging
from .blob_entity import BlobEntity
from .thing_entity import ThingEntity

logger = logging.getLogger("RENDERER_ENTITIES")

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
        
        logger.info("Entity Manager initialized")
    
    def update_from_simulation_data(self, simulation_data):
        """Update all entities based on new simulation data"""
        if not simulation_data:
            return
        
        # Update blobs
        blobs_data = simulation_data.get('blobs_data', [])
        self._update_blobs(blobs_data)
        
        # Update things
        things_data = simulation_data.get('things_data', [])
        self._update_things(things_data)
        
        # Log update stats
        logger.debug(f"Updated {len(self.blob_entities)} blobs, {len(self.thing_entities)} things")
    
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
            blob_entity = BlobEntity(blob_id, blob_data, self.settings)
            self.blob_entities[blob_id] = blob_entity
            
            logger.debug(f"Created blob entity {blob_id} at {blob_data.get('location', [0,0,0])}")
        except Exception as e:
            logger.error(f"Failed to create blob entity {blob_id}: {e}")
    
    def _update_blob_entity(self, blob_id, blob_data):
        """Update an existing blob entity"""
        blob_entity = self.blob_entities.get(blob_id)
        if blob_entity:
            try:
                blob_entity.update_from_data(blob_data)
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
            thing_entity = ThingEntity(thing_id, thing_data, self.settings)
            self.thing_entities[thing_id] = thing_entity
            
            logger.debug(f"Created thing entity {thing_id}")
        except Exception as e:
            logger.error(f"Failed to create thing entity {thing_id}: {e}")
    
    def _update_thing_entity(self, thing_id, thing_data):
        """Update an existing thing entity"""
        thing_entity = self.thing_entities.get(thing_id)
        if thing_entity:
            try:
                thing_entity.update_from_data(thing_data)
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