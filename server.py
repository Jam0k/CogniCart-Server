import io
import os
import json
import logging
from flask import Flask, jsonify, render_template, send_file, request
import requests
from datetime import datetime, timedelta
from threading import Thread
import base64

app = Flask(__name__)

# Define paths for configuration and logs directories
config_dir = 'config'
logs_dir = 'logs'
config_file_path = os.path.join(config_dir, 'config.json')
log_file_path = os.path.join(logs_dir, 'server.log')

# Ensure the config and logs directories exist
os.makedirs(config_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# Default configuration
default_config = {
    "host": "0.0.0.0",
    "port": 5000,
    "raspberry_pis": [
        "http://86.8.33.63:5004",
        "http://localhost:5002",
        "http://localhost:5003",
    ]
}

# Check if config.json exists, if not, create it with default values
if not os.path.isfile(config_file_path):
    with open(config_file_path, 'w') as config_file:
        json.dump(default_config, config_file, indent=4)

# Load configuration from config.json
with open(config_file_path) as config_file:
    config = json.load(config_file)

# Set up logging to file and console
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    handlers=[
                        logging.FileHandler(log_file_path),
                        logging.StreamHandler()
                    ])

# Use the Raspberry Pi URLs from the configuration
raspberry_pis = config.get('raspberry_pis', default_config['raspberry_pis'])

# Global variable to keep track of the last capture time
last_capture_time = None

@app.route('/')
def dashboard():
    # Render the dashboard page
    return render_template('dashboard.html')

# Function to fetch data from Raspberry Pis. Abstracting this into a separate function avoids code repetition.
def fetch_from_pi(device_id, endpoint):
    try:
        # Validate device_id
        if 0 < device_id <= len(raspberry_pis):
            pi_url = raspberry_pis[device_id-1]
            response = requests.get(f"{pi_url}/api/{endpoint}", timeout=5)
            data = response.json()
            data['client_id'] = f"Client {device_id}"
        else:
            data = {"error": "Invalid device_id"}
    except requests.exceptions.RequestException:
        data = {"client_id": f"Client {device_id}", "status": "Offline"}
    return jsonify(data)

@app.route('/api/health/<int:device_id>', methods=['GET'])
def get_health(device_id):
    # Fetch health data from the Raspberry Pi
    return fetch_from_pi(device_id, 'health')

@app.route('/api/network_settings/<int:device_id>', methods=['GET'])
def get_network_settings(device_id):
    # Fetch network settings from the Raspberry Pi
    return fetch_from_pi(device_id, 'network_settings')

@app.route('/api/ntp_check/<int:device_id>', methods=['GET'])
def ntp_check(device_id):
    # Fetch NTP check data from the Raspberry Pi
    return fetch_from_pi(device_id, 'ntp_check')

@app.route('/api/camera_check/<int:device_id>', methods=['GET'])
def camera_check(device_id):
    # Fetch camera data from the Raspberry Pi
    return fetch_from_pi(device_id, 'camera_check')

@app.route('/api/take_photo/<int:device_id>', methods=['GET'])
def take_photo(device_id):
    try:
        pi_url = raspberry_pis[device_id-1]
        response = requests.get(f"{pi_url}/api/take_photo")

        if response.status_code == 200:
            photo_data = response.json().get('image')
            # Handle the received image data (e.g., save to file, display on web interface)
            
            return jsonify({"status": "success", "photo": photo_data})
        else:
            return jsonify({"error": "Failed to capture photo, invalid status code."})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to capture photo: {str(e)}"})
    



    
@app.route('/api/motion_detected', methods=['POST'])
def motion_detected():
    global last_capture_time
    cooldown_period = 10  # 10 seconds cooldown

    if last_capture_time and datetime.now() - last_capture_time < timedelta(seconds=cooldown_period):
        # If the last capture was within the cooldown period, do not trigger a new capture
        return jsonify({"status": "Cooldown period active. Capture not triggered"}), 429

    # Update the last capture time
    last_capture_time = datetime.now()

    # Trigger frame capture on all Raspberry Pi devices
    threads = []
    for pi_url in raspberry_pis:
        thread = Thread(target=trigger_frame_capture, args=(pi_url,))
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return jsonify({"status": "Frame capture triggered on all clients"}), 200

def trigger_frame_capture(pi_url):
    try:
        # Sending a GET request to the client to take a photo
        response = requests.get(f"{pi_url}/api/take_photo", timeout=5)
        if response.status_code != 200:
            logging.error(f"Failed to capture photo from {pi_url}")
    except requests.exceptions.RequestException as e:
        logging.exception(f"Error triggering frame capture on {pi_url}: {str(e)}")


@app.route('/api/receive_image', methods=['POST'])
def receive_image():
    data = request.json
    image_data = data.get('image')
    client_id = data.get('client_id', 'UnknownClient')

    if image_data:
        image_file = os.path.join(
            "received_images", 
            f"{client_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        )

        # Decode and save the image
        image_bytes = base64.b64decode(image_data)
        os.makedirs(os.path.dirname(image_file), exist_ok=True)
        with open(image_file, 'wb') as file:
            file.write(image_bytes)

        return jsonify({"status": "Image received and saved", "file_path": image_file}), 200
    else:
        return jsonify({"status": "No image data received"}), 400




if __name__ == '__main__':
    # Use the host and port from the configuration
    app.run(host=config.get('host', default_config['host']),
            port=config.get('port', default_config['port']))