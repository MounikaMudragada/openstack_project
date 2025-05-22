import subprocess
import os
import re, time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def ansible_ping(inventory_path, config_path, hosts = "all"):
    env = os.environ.copy()
    cmd = ["ansible", hosts,"--ssh-common-args", f"-F {config_path}", "-i", inventory_path, "-m", "ping"]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)

def check_reachability(inventory_path, config_path):
    count = 0
    while True:
       
        result = ansible_ping(inventory_path, config_path)
        # print(result)
        reachable = 0
        unreachable = 0

        for line in result.stdout.splitlines():
            if re.search(r"SUCCESS", line):
                reachable += 1
            elif re.search(r"UNREACHABLE", line):
                unreachable += 1
                
        logging.info("Reachable hosts: %d, Unreachable hosts: %d", reachable, unreachable)
        if count > 2 and reachable == 0:
            logging.info("No reachable hosts found. Exiting.")
            return False
            exit(1)
        if unreachable == 0:
            logging.info("All hosts are reachable.")
            return True
            exit(0)
        logging.info("Retrying in 5 seconds...")
        count +=1
        time.sleep(5)


def run_ansible_playbook(inventory_path, config_path, playbook_path, tags = []):
    cmd = ["ansible-playbook", "-i", inventory_path, "--ssh-common-args", f"-F {config_path}", playbook_path]
    if len(tags) > 0:
        cmd += ["--tags", ",".join(tags)]
    subprocess.run(cmd)
    
def check_hosts_status(inventory_path, config_path):
    result = ansible_ping(inventory_path, config_path, hosts="webservers")
    unreachable_hosts = []
    reachable_hosts = []
    for line in result.stdout.splitlines():
        # Match UNREACHABLE lines
        match_unreachable = re.search(r"(.*?) \| UNREACHABLE", line)
        if match_unreachable:
            host = match_unreachable.group(1).strip()
            unreachable_hosts.append(host)

        # Match SUCCESS lines
        match_success = re.search(r"(.*?) \| SUCCESS", line)
        if match_success:
            host = match_success.group(1).strip()
            reachable_hosts.append(host)
    return unreachable_hosts, reachable_hosts