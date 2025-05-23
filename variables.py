
IMAGE_NAME = "Ubuntu 20.04 Focal Fossa x86_64"
FLAVOR_NAME = "1C-4GB-100GB"
EXTERNAL_NETWORK_NAME = "ext-net"

HAPROXY_USER_DATA = """#!/bin/bash
apt update
apt install -y nginx haproxy
"""

WEBSERVER_USER_DATA = """#!/bin/bash
apt update
apt install -y python3 python3-pip snmpd python3-flask
"""

