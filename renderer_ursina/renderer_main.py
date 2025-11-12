#!/usr/bin/env python3
"""
Refactored Ursina Renderer - Entry point with modular architecture

This runs as a separate process from the main simulation.
It uses a modular OOP architecture for maintainability and extensibility.

Usage:
    python renderer_ursina/renderer_main_new.py
"""

import sys
import os
import logging

from renderer_settings import Settings

settings = Settings()

# Add the renderer directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.application import RendererApplication

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
    """Main entry point for the refactored Ursina renderer"""
    # Set up logging first
    setup_logging()
    
    logger = logging.getLogger("RENDERER_MAIN")
    
    network_settings = settings.get_network_settings()
    host = network_settings.get("host", "localhost")
    port = network_settings.get("port", 8888)
    
    logger.info("=" * 60)
    logger.info("Starting Refactored Ursina Blob Simulation Renderer")
    logger.info("=" * 60)
    logger.info(f"Listening for simulation data on {host}:{port}")
    logger.info("Controls:")
    logger.info("  WASD + Mouse - Camera movement")
    logger.info("  ESC - Toggle mouse lock")
    logger.info("  R - Reset camera")
    logger.info("  F1 - Toggle debug info")
    logger.info("  F5 - Manual scene reset")
    logger.info("  F11 - Toggle fullscreen")
    logger.info("  Close window or Ctrl+C to exit")
    logger.info("=" * 60)
    
    # Create and start renderer application
    renderer_app = RendererApplication(settings=settings)
    
    try:
        # Start the renderer (this will block until window is closed)
        renderer_app.start()
    except KeyboardInterrupt:
        logger.info("Shutting down renderer...")
    except Exception as e:
        logger.error(f"Renderer error: {e}")
        logger.exception("Full error details:")
    finally:
        # Clean up
        renderer_app.cleanup()
        logger.info("Renderer stopped")

if __name__ == "__main__":
    main()