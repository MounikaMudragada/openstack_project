import re

def write_ansible_and_ssh_config(hosts_dict, tag, identity_file_path):
    bastion_key = f"{tag}_bastion"
    haproxy_key = f"{tag}_haproxy"
    # Match keys like "mytag_dev1", "mytag_dev2", etc.
    dev_pattern = re.compile(rf"^{tag}_dev\d+$")
    dev_keys = [key for key in hosts_dict if dev_pattern.match(key)]


    # === Ansible Hosts File ===
    hosts_file_content = f"""[Bastion]
{bastion_key}

[haproxy]
{haproxy_key}

[webservers]
{chr(10).join(dev_keys)}

[all:vars]
ansible_user=ubuntu
"""

    with open("hosts", "w") as f:
        f.write(hosts_file_content)

    # === SSH Config File ===
    config_file_content = f"""Host *
    Port 22
    User ubuntu
    IdentityFile {identity_file_path}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    PasswordAuthentication no
    ForwardAgent yes

Host {bastion_key}
    HostName {hosts_dict[bastion_key]}
"""

    # Add dev servers
    for dev_key in dev_keys:
        config_file_content += f"""
Host {dev_key}
    HostName {hosts_dict[dev_key]}
    ProxyJump {bastion_key}
"""

    # Add haproxy
    config_file_content += f"""
Host {haproxy_key}
    HostName {hosts_dict[haproxy_key]}
    ProxyJump {bastion_key}
"""

    with open(f"{tag}_config", "w") as f:
        f.write(config_file_content)

    print(f"Files written: 'hosts' and '{tag}_config'")


def extract_names_ips_from_server(total_servers, tag):
    server_dict = {}

    for server in total_servers:
        addresses = server.addresses.get(f"{tag}network", [])
        
        if server.name == f"{tag}_bastion":
            # Extract floating IPv4 address
            ip = next(
                (addr["addr"] for addr in addresses if addr["version"] == 4 and addr["OS-EXT-IPS:type"] == "floating"),
                None
            )
        else:
            # Extract fixed IPv4 address
            ip = next(
                (addr["addr"] for addr in addresses if addr["version"] == 4 and addr["OS-EXT-IPS:type"] == "fixed"),
                None
            )
        
        server_dict[server.name] = ip

    return server_dict