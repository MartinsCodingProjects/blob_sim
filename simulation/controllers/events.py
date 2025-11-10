import heapq
from dataclasses import dataclass
from typing import Any

from .blob_action import BlobActionFactory

import logging
logger = logging.getLogger("EVENTS")

@dataclass
class Event():
    time: float          # At what simulation time (in hours) the event occurs
    event_type: str      # What kind of event ("move", "interact", etc.)
    blob_id: int         # Which blob is involved
    data: Any = None     # Extra information

    def __lt__(self, other):
        return self.time < other.time

class EventScheduler():
    def __init__(self):
        self.events = []  # Min-heap based on event time

    def schedule_event(self, time, event_type, blob_id, data=None):
        """Schedule an event to happen at a specific time within the hour."""
        event = Event(time, event_type, blob_id, data)
        heapq.heappush(self.events, event)

    def process_events_until(self, current_sim_time):
        """Process all events up until the current time."""
        while self.events and self.events[0].time <= current_sim_time:
            event = heapq.heappop(self.events)
            self.handle_event(event)
    
  
    def handle_event(self, event):
        """Handle specific event using Action Factory - NO if/elif chains!"""
        blob = event.data["blob"]
        
        try:
            # Factory creates the right action with ALL the logic
            action = BlobActionFactory.create_action(
                event.event_type,
                blob,
                event.data
            )
            action.execute()
            
        except ValueError as e:
            logger.error(f"Unknown event type {event.event_type}: {e}")
        except Exception as e:
            logger.error(f"Error executing {event.event_type} for {blob.name}: {e}")

    def clear(self):
        """Clear all events (call at end of each hour)."""
        self.events.clear()