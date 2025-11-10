#!/usr/bin/env python3
"""
Ursina Renderer - Entry point for the blob simulation renderer

This runs as a separate process from the main simulation.
It listens for data on localhost:8888 and renders the simulation in 3D.

Usage:
    python renderer_ursina/main.py
"""

import sys
import os
import logging

from renderer_settings import Settings

settings = Settings()

# Add the renderer directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursina_renderer import BlobRenderer

# Set up logging for renderer
def setup_logging():
    """Configure logging for renderer"""
    if settings.debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    
    logging.basicConfig(
        level=logging_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )

def main():
    """Main entry point for the Ursina renderer"""
    # Set up logging first
    setup_logging()
    
    logger = logging.getLogger("RENDERER_MAIN")
    
    network_settings = settings.get_network_settings()
    host = network_settings.get("host", "localhost")
    port = network_settings.get("port", 8888)
    
    logger.info("Starting Ursina Blob Simulation Renderer...")
    logger.info(f"Listening for simulation data on {host}:{port}")
    logger.info("Press Escape or close window to exit")
    
    # Create and start renderer
    renderer = BlobRenderer(settings=settings)
    
    try:
        # Start the renderer (this will block until window is closed)
        renderer.start()
    except KeyboardInterrupt:
        logger.info("Shutting down renderer...")
    except Exception as e:
        logger.error(f"Renderer error: {e}")
    finally:
        # Clean up
        renderer.cleanup()
        logger.info("Renderer stopped")

if __name__ == "__main__":
    main()