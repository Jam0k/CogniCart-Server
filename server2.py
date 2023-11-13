import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import aiohttp
from datetime import datetime, timedelta
import logging
import asyncio
import base64
import os
from threading import Timer
import uuid

app = FastAPI()

# Define and ensure existence of configuration and logs directories
config_dir = 'config'
logs_dir = 'logs'
config_file_path = os.path.join(config_dir, 'config2.json')  # Config file path
log_file_path = os.path.join(logs_dir, 'server.log')  # Log file path

os.makedirs(config_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# Load server configuration from the specified JSON file
try:
    with open(config_file_path) as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise RuntimeError("Config file not found")  # Raise error if config file is missing

# Setup logging to both file and console
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    handlers=[
                        logging.FileHandler(log_file_path),
                        logging.StreamHandler()
                    ])

# Extract Raspberry Pi URLs from the configuration for image capture
raspberry_pis = config.get('raspberry_pis', [])

# Global variable to keep track of the last image capture time
last_capture_time = None

# Global variables for session UUID and a timer to handle session expiration
session_uuid = None
session_timer = None

def reset_session():
    """Resets the current session, logging the end of session and clearing UUID and timer."""
    global session_uuid, session_timer
    logging.info(f"Session ended: {session_uuid}")
    session_uuid = None
    session_timer = None

class ImageData(BaseModel):
    """Pydantic model to define the structure of the image data received."""
    image: str
    client_id: str

@app.post("/api/motion_detected")
async def motion_detected():
    """Handles motion detection events by triggering image capture on Raspberry Pi devices."""
    global last_capture_time, session_uuid, session_timer

    cooldown_period = 1  # Time in seconds before another capture can be triggered
    session_timeout = 3  # Time in seconds for session expiration without new motion

    # Check for cooldown period
    if last_capture_time and datetime.now() - last_capture_time < timedelta(seconds=cooldown_period):
        raise HTTPException(status_code=429, detail="Cooldown period active. Capture not triggered")

    # Reset the session timer if new motion is detected
    if session_timer:
        session_timer.cancel()

    # Create a new session if none exists
    if not session_uuid:
        session_uuid = str(uuid.uuid4())
        logging.info(f"New checkout_session created: {session_uuid}")
        os.makedirs(os.path.join("received_images", session_uuid), exist_ok=True)

    # Reset the session timer for session expiration
    session_timer = Timer(session_timeout, reset_session)
    session_timer.start()

    last_capture_time = datetime.now()
    # Trigger frame capture on all configured Raspberry Pi devices
    await asyncio.gather(*(trigger_frame_capture_async(pi_url) for pi_url in raspberry_pis))
    return {"status": "Frame capture triggered on all clients"}

@app.post("/api/receive_image")
async def receive_image(image_data: ImageData):
    """Receives and saves images sent by Raspberry Pi devices."""
    global session_uuid

    # Create a fallback session if an image is received without an existing session
    if not session_uuid:
        session_uuid = str(uuid.uuid4())

    # Decode the base64 encoded image
    image_bytes = base64.b64decode(image_data.image)
    image_file_path = os.path.join(
        "received_images", 
        session_uuid, 
        f"{image_data.client_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    )

    # Save the image to the file system
    os.makedirs(os.path.dirname(image_file_path), exist_ok=True)
    with open(image_file_path, 'wb') as file:
        file.write(image_bytes)

    return {"status": "Image received and saved", "file_path": image_file_path}

async def trigger_frame_capture_async(pi_url):
    """Triggers a frame capture request to a Raspberry Pi device asynchronously."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{pi_url}/api/take_photo", timeout=10) as response:
                if response.status != 200:
                    logging.error(f"Failed to capture photo from {pi_url}")
        except Exception as e:
            logging.exception(f"Error triggering frame capture on {pi_url}: {str(e)}")

@app.post("/api/trigger_manual_capture")
async def trigger_manual_capture():
    """Endpoint to manually trigger frame capture on all Raspberry Pi devices."""
    await asyncio.gather(*(trigger_frame_capture_async(pi_url) for pi_url in raspberry_pis))
    return {"status": "Manual frame capture triggered on all clients"}

# Dictionary to track client heartbeats
client_heartbeats = {}

@app.post("/heartbeat")
async def handle_heartbeat(request: Request):
    data = await request.json()
    client_id = data.get('client_id', 'unknown_client')
    logging.info(f"Heartbeat received from client ID: {client_id}")
    return {"message": "Success"}

if __name__ == "__main__":
    # Start the FastAPI server with the configuration settings
    import uvicorn
    uvicorn.run(app, host=config.get('host', '0.0.0.0'), port=config.get('port', 5000))