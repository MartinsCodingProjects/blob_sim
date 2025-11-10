from simulation.sim_engine import SimEngine
import logging
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

def start_sim(settings=settings):
    simulation = SimEngine(settings=settings)
    simulation.start()
    return

def start_renderer(settings=settings):
    if settings.renderer == 'ursina':
        import subprocess
        import sys

        # Start the renderer as a separate process
        renderer_process = subprocess.Popen(
            [sys.executable, "renderer_ursina/renderer_main.py"],
            cwd=".",  # or the path to your project root
        )
        return renderer_process


if __name__ == "__main__":
    start_sim()
    # start_renderer()
