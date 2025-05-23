import subprocess
import os
import logging


from variables import (
    IMAGE_ID,
    FLAVOR_ID,     
    EXTERNAL_NETWORK_NAME,  
)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_openrc(openrc_path):
    """
    Load environment variables from an OpenStack openrc file into the Python environment.
    """
    command = ['bash', '-c', f"source {openrc_path} && env"]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
    
    for line in proc.stdout:
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()

    proc.communicate()
    

def create_or_get_keypair(tag, public_key_path, conn, log=True):
    key_name = f"{tag}keypair"
    with open(public_key_path, 'r') as pubkey_file:
        public_key = pubkey_file.read().strip()
        
    existing = conn.compute.find_keypair(key_name)
    if existing:
        if log:
            logging.info(f"Keypair '{key_name}' already exists.")
        return existing

    keypair = conn.compute.create_keypair(
        name=key_name,
        public_key=public_key
    )
    if log:
        logging.info(f"Keypair '{key_name}' created.")
    return keypair

def create_or_get_network(tag, conn, log=True):
    """
    Create a full network setup: network + subnet + router (with gateway and interface).
    Returns (network, subnet, router)
    """
    network_name = f"{tag}network"
    subnet_name = f"{tag}subnet"
    router_name = f"{tag}router"
    cidr = f"192.168.0.0/24"
    gateway_ip = f"192.168.0.1"

    # NETWORK
    network = conn.network.find_network(network_name)
    if not network:
        network = conn.network.create_network(name=network_name)
        if log:
            logging.info(f"Network '{network_name}' created.")
    else:
        if log:
            logging.info(f"Network '{network_name}' already exists.")

    # SUBNET
    subnet = conn.network.find_subnet(subnet_name)
    if not subnet:
        subnet = conn.network.create_subnet(
            name=subnet_name,
            network_id=network.id,
            ip_version=4,
            cidr=cidr,
            gateway_ip=gateway_ip,
            dns_nameservers=["8.8.8.8"]
        )
        if log:
            logging.info(f"Subnet '{subnet_name}' created.")
    else:
        if log:
            logging.info(f"Subnet '{subnet_name}' already exists.")

    # ROUTER
    router = conn.network.find_router(router_name)
    if not router:
        router = conn.network.create_router(name=router_name)
        if log:
            logging.info(f"Router '{router_name}' created.")

        # Connect to external network if available
        ext_net = conn.network.find_network(EXTERNAL_NETWORK_NAME)
        if ext_net:
            conn.network.update_router(
                router,
                external_gateway_info={"network_id": ext_net.id}
            )
            logging.info(f"Router '{router_name}' connected to external network '{EXTERNAL_NETWORK_NAME}'.")

        # Add router interface to subnet
        conn.network.add_interface_to_router(router, subnet_id=subnet.id)
        if log:
            logging.info(f"Router '{router_name}' interface added to subnet '{subnet_name}'.")
    else:
        if log:
            logging.info(f"Router '{router_name}' already exists.")

    return network, subnet, router

def create_or_get_server(conn, name, tag, network, key_name, security_groups, user_data=None):
    """
    Create a virtual server in OpenStack.
    """
    # Check if server already exists
    server = conn.compute.find_server(name)
    if server:
        logging.info(f"Server '{name}' already exists.")
        return server

    if not user_data:
        user_data = ""
    sec_groups = [{"name": security_groups.name}]
    # Create the server
    server = conn.compute.create_server(
        name=name,
        image_id=IMAGE_ID,
        flavor_id=FLAVOR_ID,
        networks=[{"uuid": network.id}],
        key_name=key_name.id,
        security_groups=sec_groups,
        user_data=user_data
    )

    # Wait for the server to become ACTIVE
    server = conn.compute.wait_for_server(server)
    logging.info(f"Server '{name}' created.")
    return server


def assign_or_get_floating_ip(conn, server):
    """
    Assigns a floating IP to the bastion server. If no available floating IPs exist, creates one.
    Also ensures the floating IP is associated with the server's port.
    """
    server_ports = list(conn.network.ports(device_id=server.id))
    if not server_ports:
        raise Exception("No ports found on server.")
    port = server_ports[0]
    
    # Check if a floating IP is already associated with the port
    for fip in conn.network.ips():
        if fip.port_id == port.id:
            logging.info(f"Floating IP {fip.floating_ip_address} already associated with port of {server.name}.")
            return fip.floating_ip_address
        
    floating_ip = None
    for fip in conn.network.ips():
        if not fip.port_id:
            floating_ip = fip
            logging.info(f"Reusing existing floating IP {floating_ip.floating_ip_address} port of {server.name}.")
            break

    if not floating_ip:
        floating_ip = conn.network.create_ip(floating_network_id=conn.network.find_network(EXTERNAL_NETWORK_NAME).id)
        logging.info(f"Created new floating IP {floating_ip.floating_ip_address}.")

    update_ip = conn.network.update_ip(floating_ip, port_id=port.id)
    logging.info(f"Assigned floating IP {update_ip.floating_ip_address} to port of {server.name}.")

    return floating_ip.floating_ip_address


def abs_path(relative_path):
    """
    Return the absolute path of a file or directory.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

def give_server_name_to_create(number_of_servers, reachable_hosts, tag):
    """
    Generate server names based on the number of servers and reachable hosts.
    """
    server_names = []
    created_servers = 0
    required_servers = number_of_servers - len(reachable_hosts)
    for i in range(number_of_servers):
        server_name = f"{tag}_dev{i+1}"
        if server_name not in reachable_hosts:
            server_names.append(server_name)
            created_servers += 1
            if created_servers == required_servers:
                break
    return server_names

def get_floating_ip_for_server(conn, server_name):
    """
    Get the floating IP(s) associated with the given server name.

    Args:
        conn (openstack.connection.Connection): Authenticated OpenStack connection.
        server_name (str): Name of the server (e.g., "{tag}_haproxy").

    Returns:
        list of floating IP strings or empty list if none found.
    """
    
    # Find the server by name
    server = conn.compute.find_server(server_name)

    floating_ips = []
    # Get ports attached to the server
    ports = list(conn.network.ports(device_id=server.id))
    for port in ports:
        # For each port, check if there's a floating IP associated
        fips = list(conn.network.ips(port_id=port.id))
        for fip in fips:
            if fip.floating_ip_address:
                floating_ips.append(fip.floating_ip_address)

    return floating_ips

if __name__ == "__main__":
    # Example usage
    openrc_path = abs_path("./openrc.sh")
    print(f"Loading OpenStack RC file from: {openrc_path}")
    # Assuming `conn` is an established OpenStack connection
    # conn = establish_connection()  # Replace with actual connection code
    # create_network("example_tag", conn)