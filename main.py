from simulation.sim_engine import SimEngine
import logging
import threading
import queue
import time
from settings import Settings

settings = Settings()


if settings.debug:
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO


logging.basicConfig(
    level=logging_level,
    format='[%(name)s] %(asctime)s %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
simulation = SimEngine(settings=settings)

def start_simulation_and_renderer():
    """Start simulation and renderer based on settings"""
    if settings.renderer == 'ursina':
        # Start ursina renderer as separate process
        import subprocess
        import sys
        renderer_process = subprocess.Popen(
            [sys.executable, "renderer_ursina/renderer_main.py"],
            cwd=".",
        )
        # Start simulation in main thread
        simulation.start()
        # Wait for renderer process to finish
        renderer_process.wait()
        
    elif settings.renderer == 'pygame':
        simulation.start_paused = True
        simulation.paused = True
        
        # Action handler for GUI buttons
        def handle_gui_action(action):
            """Handle actions from the GUI using shared settings object"""
            print(f"GUI Action: {action}")
            if action == "play":
                settings.paused = False
                simulation.paused = False
                print("Simulation resumed")
            elif action == "pause":
                settings.paused = True
                simulation.paused = True
                print("Simulation paused")
            elif action == "reset":
                # Add reset functionality later
                print("Reset requested (not implemented yet)")
        
        # Start pygame renderer in separate thread
        from renderer_2d.renderer_2d import Renderer2d
        renderer = Renderer2d(settings)
        renderer.set_action_callback(handle_gui_action)
        renderer_thread = threading.Thread(target=renderer.start, daemon=True)
        renderer_thread.start()
        
        # Start simulation in separate thread (not main thread)
        simulation_thread = threading.Thread(target=simulation.start, daemon=True)
        simulation_thread.start()
        
        # Main thread handles data transfer between simulation and renderer
        try:
            while renderer_thread.is_alive() and simulation_thread.is_alive():
                # Fetch latest data from simulation queue
                try:
                    # Get latest data from queue (non-blocking)
                    sim_data = simulation.renderer_data_queue.get(timeout=0.1)
                    # Update renderer with new data
                    renderer.update_sim_world_data(sim_data)
                except queue.Empty:
                    # No new data available, continue
                    pass
                except Exception as e:
                    print(f"Error transferring data: {e}")
                
                # Small sleep to prevent excessive CPU usage
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("Main thread received keyboard interrupt")
            renderer.running = False
            
        # Wait for threads to finish
        renderer_thread.join()
        simulation_thread.join()
        
    else:
        # No renderer, just run simulation
        simulation.start()

if __name__ == "__main__":
    start_simulation_and_renderer()
