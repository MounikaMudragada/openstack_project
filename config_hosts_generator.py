def write_ansible_and_ssh_config(hosts_dict, tag, identity_file_path):
    bastion_key = f"{tag}_bastion"
    haproxy_key = f"{tag}_haproxy"
    dev_keys = [f"{tag}_dev{i}" for i in range(1, 4)]

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
