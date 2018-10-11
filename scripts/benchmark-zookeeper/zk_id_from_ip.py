#!/usr/bin/env python3
"""
Finds the zookeper ID from the last digit of the IP address
"""

import argparse
import re
import subprocess
import sys



def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", "-i", help="interface to use", default="enp0s8")

    return parser.parse_args()

def main():
    args = parse_args()
    cmd = "ip addr show dev {}".format(args.interface)
    output = subprocess.check_output(cmd.split()).decode()

    match = re.search("inet ([0-9.]+)", output)

    if not match:
        sys.exit(1)

    print(match.group(1).split(".")[-1])




if __name__ == '__main__':
    main()
