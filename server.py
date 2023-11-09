import io
import os
import json
import logging
from flask import Flask, jsonify, render_template, send_file, request
import requests
from datetime import datetime
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
    # This endpoint will be hit by the client Raspberry Pi when motion is detected
    data = request.json
    logging.info(f"Motion detected on Client {data['client_id']}. Triggering frame capture on all clients.")

    # Trigger frame capture on all Raspberry Pi devices
    threads = []
    for pi in raspberry_pis:
        thread = Thread(target=trigger_frame_capture, args=(pi,))
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



if __name__ == '__main__':
    # Use the host and port from the configuration
    app.run(host=config.get('host', default_config['host']),
            port=config.get('port', default_config['port']))