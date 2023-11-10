import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiohttp
from datetime import datetime, timedelta
import logging
import asyncio
import base64
import os

app = FastAPI()

# Define paths for configuration and logs directories
config_dir = 'config'
logs_dir = 'logs'
config_file_path = os.path.join(config_dir, 'config.json')
log_file_path = os.path.join(logs_dir, 'server.log')

# Ensure the config and logs directories exist
os.makedirs(config_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# Load configuration from config.json
try:
    with open(config_file_path) as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise RuntimeError("Config file not found")

# Set up logging to file and console
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    handlers=[
                        logging.FileHandler(log_file_path),
                        logging.StreamHandler()
                    ])

# Use the Raspberry Pi URLs from the configuration
raspberry_pis = config.get('raspberry_pis', [])

# Global variable to keep track of the last capture time
last_capture_time = None

class ImageData(BaseModel):
    image: str
    client_id: str

@app.post("/api/receive_image")
async def receive_image(image_data: ImageData):
    image_bytes = base64.b64decode(image_data.image)
    image_file = os.path.join(
        "received_images", 
        f"{image_data.client_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    )

    os.makedirs(os.path.dirname(image_file), exist_ok=True)
    with open(image_file, 'wb') as file:
        file.write(image_bytes)

    return {"status": "Image received and saved", "file_path": image_file}

@app.post("/api/motion_detected")
async def motion_detected():
    global last_capture_time
    cooldown_period = 1  # 10 seconds cooldown

    if last_capture_time and datetime.now() - last_capture_time < timedelta(seconds=cooldown_period):
        raise HTTPException(status_code=429, detail="Cooldown period active. Capture not triggered")

    last_capture_time = datetime.now()
    await asyncio.gather(*(trigger_frame_capture_async(pi_url) for pi_url in raspberry_pis))
    return {"status": "Frame capture triggered on all clients"}

async def trigger_frame_capture_async(pi_url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{pi_url}/api/take_photo", timeout=5) as response:
                if response.status != 200:
                    logging.error(f"Failed to capture photo from {pi_url}")
        except Exception as e:
            logging.exception(f"Error triggering frame capture on {pi_url}: {str(e)}")

# ... Add other endpoints as needed ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.get('host', '0.0.0.0'), port=config.get('port', 5000))
