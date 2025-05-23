import subprocess
import time
import re
from configparser import ConfigParser

def normalize_host(hostname):
    return hostname.replace('-', '_')

def check_reachability_via_haproxy(haproxy_ip, haproxy_port, inventory_file, group_name="webservers"):
    # Helper to parse inventory and get hosts of the group
    def get_expected_hosts(inventory_file, group_name):
        config = ConfigParser(allow_no_value=True, delimiters=("="))
        config.optionxform = str
        config.read(inventory_file)
        if group_name not in config:
            raise ValueError(f"Group '{group_name}' not found in inventory")
        return list(config[group_name].keys())

    # Curl HAProxy and detect reachable hosts via round-robin repeat detection
    def get_reachable_hosts_via_roundrobin(url):
        seen_hosts = []
        pattern = re.compile(r"Serving from (\S+)")
        # print(f"Starting to curl HAProxy at {url}...")
        while True:
            try:
                result = subprocess.run(
                    ["curl", "-s", url],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                match = pattern.search(result.stdout)
                
                if match:
                    host = match.group(1) 
                    if host in seen_hosts:
                        break
                    seen_hosts.append(host)
                else:
                    pass
            except subprocess.TimeoutExpired:
                pass
            time.sleep(0.5)
        return set(seen_hosts)

    url = f"http://{haproxy_ip}:{haproxy_port}"

    expected_hosts = set(normalize_host(h) for h in get_expected_hosts(inventory_file, group_name))
    reachable_hosts = set(normalize_host(h) for h in get_reachable_hosts_via_roundrobin(url))

    unreachable_hosts = set(expected_hosts) - reachable_hosts

    return reachable_hosts, unreachable_hosts

if __name__ == "__main__":
    # Example usage
    # Replace with your actual HAProxy IP, port, and inventory file path
    reachable_hosts, unreachable_hosts = check_reachability_via_haproxy(
                "8.8.8.8",
                5000, 
                "./hosts")
    print("Reachable hosts:", reachable_hosts, "Unreachable hosts:", unreachable_hosts)