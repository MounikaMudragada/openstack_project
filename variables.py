
IMAGE_ID = "c1ed73bf-268c-418f-9a90-c8e6021f75d8"
FLAVOR_ID = " 018fd7b8-2659-4710-a44d-045c9e365b2b"
EXTERNAL_NETWORK_NAME = "ext-net"

HAPROXY_USER_DATA = """#!/bin/bash
apt update
apt install -y nginx haproxy
"""

WEBSERVER_USER_DATA = """#!/bin/bash
apt update
apt install -y python3 python3-pip snmpd python3-flask
"""

