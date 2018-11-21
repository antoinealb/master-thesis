#!/usr/bin/env python3
"""
Reads a pcap file and analyses its content (r2p2 supported).
"""

import argparse
from scapy.all import *
from r2p2 import *



def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=argparse.FileType('rb'))

    return parser.parse_args()

def main():
    args = parse_args()

    packets = rdpcap(args.input)
    for p in packets:
        if not "R2P2" in p:
            continue
        p.show()


if __name__ == '__main__':
    main()
