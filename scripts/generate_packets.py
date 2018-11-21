#!/usr/bin/env python3
"""
Generates a test pcap file for use with DPDK / NetBricks key value store.
"""

import argparse
from scapy.all import *
from r2p2 import *

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "-o", required=True)

    return parser.parse_args()

def set_request(key, value):
    data = [""] * 10
    data[2] = "SET"
    data[4] = key
    data[6] = value
    data = "\r\n".join(data)

    return data.encode()

def set_packet(key, value):
    DST = "00:00:00:01:02:03"

    return Ether(dst=DST) / \
           IP(dst="10.90.44.214") / \
           UDP(sport=12, dport=9000) / \
           R2P2(state=2, request_id=42, packet_id=1) / \
           set_request(key, value)

def get_request(key):
    data = [""] * 6
    data[2] = "GET"
    data[4] = key
    return "\r\n".join(data).encode()

def get_packet(key):
    DST = "00:00:00:01:02:03"

    return Ether(dst=DST) / \
           IP(dst="10.90.44.214") / \
           UDP(sport=12, dport=9000) / \
           R2P2(state=2, request_id=43, packet_id=1) / \
           get_request(key)

def main():
    args = parse_args()

    a = set_packet("hello", "world")
    b = get_packet("hello")

    b.show2()

    wrpcap(args.output, [a, b])

if __name__ == '__main__':
    main()
