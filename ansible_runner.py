import subprocess
import os
import re, time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def check_reachability(inventory_path, config_path):
    count = 0
    while True:
        env = os.environ.copy()
        cmd = ["ansible", "all","--ssh-common-args", f"-F {config_path}", "-i", inventory_path, "-m", "ping"]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
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


def run_ansible_playbook(inventory_path, config_path, playbook_path):
    cmd = ["ansible-playbook", "-i", inventory_path, "--ssh-common-args", f"-F {config_path}", playbook_path]
    subprocess.run(cmd)
    