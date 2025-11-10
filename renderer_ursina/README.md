# Ursina Renderer

This is the Ursina-based 3D renderer for the blob simulation. It runs as a separate process and receives simulation data over TCP sockets.

## Files

- `main.py` - Entry point to start the renderer
- `ursina_renderer.py` - Main renderer class with Ursina app and 3D scene
- `data_receiver.py` - Socket server that receives data from the simulation

## Usage

1. **Install Ursina** (if not already installed):
   ```bash
   pip install ursina
   ```

2. **Start the renderer** (in a separate terminal):
   ```bash
   python renderer_ursina/main.py
   ```

3. **Run the simulation** (in another terminal):
   ```bash
   python main.py
   ```

## How it works

1. The renderer starts a TCP server listening on `localhost:8888`
2. The simulation sends JSON data to this address every 60 FPS
3. The renderer receives the data, parses it, and updates the 3D scene
4. Blobs are rendered as colored spheres with different colors based on their state:
   - Blue: idle
   - Red: walking
   - Orange: walking_timed
   - Green: resting

## Controls

- Mouse: Look around
- WASD: Move camera (if enabled)
- Escape: Exit renderer

## Architecture

This renderer is designed to be modular and replaceable. The simulation communicates via a simple JSON protocol over TCP sockets, making it easy to swap out this Ursina renderer for other visualization technologies (web-based, Godot, etc.) later.