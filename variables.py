
IMAGE_ID = "c1ed73bf-268c-418f-9a90-c8e6021f75d8"
FLAVOR_ID = " 018fd7b8-2659-4710-a44d-045c9e365b2b"
EXTERNAL_NETWORK_NAME = "ext-net"
DEFAULT_USER_DATA = """#!/bin/bash
sudo apt update
sudo apt install -y nginx
"""

# Default availability zone (if needed)
AVAILABILITY_ZONE = None  # or "nova"
