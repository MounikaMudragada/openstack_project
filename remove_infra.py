import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
def delete_security_groups(tag, conn):
    """
    Delete bastion, haproxy, and webservers security groups for a given tag.
    """
    sg_names = [
        f"{tag}-webservers-sg",
        f"{tag}-haproxy-sg",
        f"{tag}-bastion-sg"
    ]

    for name in sg_names:
        sg = conn.network.find_security_group(name)
        if sg:
            try:
                conn.network.delete_security_group(sg)
                logging.info(f"Deleted security group '{name}'.")
            except Exception as e:
                logging.error(f"Error deleting security group '{name}': {e}")
        else:
            logging.info(f"Security group '{name}' not found. Skipping deletion.")

# Delete router interface & router
def delete_router(tag, conn):
    router_name = f"{tag}router"
    router = conn.network.find_router(router_name)
    if router:
        subnet_name = f"{tag}subnet"
        subnet = conn.network.find_subnet(subnet_name)
        if subnet:
            try:
                conn.network.remove_interface_from_router(router, subnet_id=subnet.id)
                logging.info(f"Removed interface from router '{router_name}'.")
            except Exception as e:
                logging.error(f"Error removing interface from router '{router_name}': {e}")
        try:
            conn.network.delete_router(router, ignore_missing=True)
            logging.info(f"Deleted router '{router_name}'.")
        except Exception as e:
            logging.error(f"Error deleting router '{router_name}': {e}")
    else:
        logging.info(f"Router '{router_name}' not found.")

# Delete subnet
def delete_subnet(tag, conn):
    subnet_name = f"{tag}subnet"
    subnet = conn.network.find_subnet(subnet_name)
    if subnet:
        try:
            conn.network.delete_subnet(subnet, ignore_missing=True)
            logging.info(f"Deleted subnet '{subnet_name}'.")
        except Exception as e:
            logging.error(f"Error deleting subnet '{subnet_name}': {e}")
    else:
        logging.info(f"Subnet '{subnet_name}' not found.")


# Delete network
def delete_network(tag, conn):
    network_name = f"{tag}network"
    network = conn.network.find_network(network_name)
    if network:
        try:
            conn.network.delete_network(network, ignore_missing=True)
            logging.info(f"Deleted network '{network_name}'.")
        except Exception as e:
            logging.error(f"Error deleting network '{network_name}': {e}")
    else:
        logging.info(f"Network '{network_name}' not found.")

# Delete keypair
def delete_keypair(tag, conn):
    keypair_name = f"{tag}keypair"
    keypair = conn.compute.find_keypair(keypair_name)
    if keypair:
        try:
            conn.compute.delete_keypair(keypair, ignore_missing=True)
            logging.info(f"Deleted keypair '{keypair_name}'.")
        except Exception as e:
            logging.error(f"Error deleting keypair '{keypair_name}': {e}")
    else:
        logging.info(f"Keypair '{keypair_name}' not found.")
        

def delete_servers_by_tag(conn, tag):
    for server in conn.compute.servers():
        if tag in server.name:
            logging.info(f"Deleting server: {server.name}")
            # Delete the server
            conn.compute.delete_server(server.id, ignore_missing=True)
    logging.info(f"Deleted all servers with tag '{tag}'.")

def delete_floating_ips(conn):
    # List all floating IPs
    floating_ips = conn.network.ips()
    unattached_fips = [fip for fip in floating_ips if fip.port_id is None]
    # Iterate through each floating IP
    for fip in unattached_fips:
        try:
            # Delete the floating IP
            conn.network.delete_ip(fip)
            logging.info(f"Deleted floating IP {fip.floating_ip_address}.")
        except Exception as e:
            logging.error(f"Error deleting floating IP {fip.floating_ip_address}: {e}")