import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
def create_bastion_security_group(tag, conn):
    """
    Create a simple security group for a bastion host that allows only SSH (port 22) from any IP.
    """
    sg_name = f"{tag}-bastion-sg"
    
    # Check if the security group already exists
    sg = conn.network.find_security_group(sg_name)
    if sg:
        logging.info(f"Security group '{sg_name}' already exists.")
        return sg

    # Create the security group
    sg = conn.network.create_security_group(
        name=sg_name, 
        description="Security group for bastion host allowing SSH"
    )
    logging.info(f"Created security group '{sg_name}'.")

    # Add SSH rule
    conn.network.create_security_group_rule(
        security_group_id=sg.id,
        direction='ingress',
        protocol='tcp',
        port_range_min=22,
        port_range_max=22,
        remote_ip_prefix='0.0.0.0/0',
        ethertype='IPv4'
    )

    return sg

def create_haproxy_security_group(tag, conn):
    """
    Create a security group for HAProxy:
    - Allow TCP port 5000 from anywhere
    - Allow UDP port 6000 from anywhere
    - Allow SSH (port 22) only from bastion security group
    """
    sg_name = f"{tag}-haproxy-sg"
    
    # Check if already exists
    sg = conn.network.find_security_group(sg_name)
    if sg:
        logging.info(f"Security group '{sg_name}' already exists.")
        return sg

    # Create the security group
    sg = conn.network.create_security_group(
        name=sg_name, 
        description="HAProxy security group with TCP/UDP and restricted SSH access"
    )
    logging.info(f"Created security group '{sg_name}'.")

    # Allow TCP 5000 from anywhere
    conn.network.create_security_group_rule(
        security_group_id=sg.id,
        direction='ingress',
        protocol='tcp',
        port_range_min=5000,
        port_range_max=5000,
        remote_ip_prefix='0.0.0.0/0',
        ethertype='IPv4'
    )

    # Allow UDP 6000 from anywhere
    conn.network.create_security_group_rule(
        security_group_id=sg.id,
        direction='ingress',
        protocol='udp',
        port_range_min=6000,
        port_range_max=6000,
        remote_ip_prefix='0.0.0.0/0',
        ethertype='IPv4'
    )

    # Allow SSH (22) only from bastion SG
    bastion_sg = conn.network.find_security_group(f"{tag}-bastion-sg")
    if bastion_sg:
        conn.network.create_security_group_rule(
            security_group_id=sg.id,
            direction='ingress',
            protocol='tcp',
            port_range_min=22,
            port_range_max=22,
            remote_group_id=bastion_sg.id,
            ethertype='IPv4'
        )
    else:
        logging.raiseExceptions(f"Bastion security group '{tag}-bastion-sg' not found. Skipping SSH rule.")

    return sg


def create_webservers_security_group(tag, conn):
    """
    Create a security group for web servers:
    - Allow UDP 161 from HAProxy security group
    - Allow TCP 5000 from HAProxy security group
    - Allow SSH (22) from Bastion security group
    """
    sg_name = f"{tag}-webservers-sg"

    # Check if security group already exists
    sg = conn.network.find_security_group(sg_name)
    if sg:
        logging.info(f"Security group '{sg_name}' already exists.")
        return sg

    # Create the security group
    sg = conn.network.create_security_group(
        name=sg_name,
        description="Security group for web servers with HAProxy and Bastion access"
    )
    logging.info(f"Created security group '{sg_name}'.")

    # Get HAProxy SG
    haproxy_sg = conn.network.find_security_group(f"{tag}-haproxy-sg")
    if not haproxy_sg:
        logging.error(f"HAProxy security group '{tag}-haproxy-sg' not found. Skipping HAProxy rules.")
    else:
        # Allow UDP 161 from HAProxy SG
        conn.network.create_security_group_rule(
            security_group_id=sg.id,
            direction='ingress',
            protocol='udp',
            port_range_min=161,
            port_range_max=161,
            remote_group_id=haproxy_sg.id,
            ethertype='IPv4'
        )
        
        # Allow TCP 5000 from HAProxy SG
        conn.network.create_security_group_rule(
            security_group_id=sg.id,
            direction='ingress',
            protocol='tcp',
            port_range_min=5000,
            port_range_max=5000,
            remote_group_id=haproxy_sg.id,
            ethertype='IPv4'
        )
        
    # Get Bastion SG
    bastion_sg = conn.network.find_security_group(f"{tag}-bastion-sg")
    if not bastion_sg:
        logging.error(f"Bastion security group '{tag}-bastion-sg' not found. Skipping SSH rule.")
    else:
        # Allow SSH from Bastion SG
        conn.network.create_security_group_rule(
            security_group_id=sg.id,
            direction='ingress',
            protocol='tcp',
            port_range_min=22,
            port_range_max=22,
            remote_group_id=bastion_sg.id,
            ethertype='IPv4'
        )

    return sg