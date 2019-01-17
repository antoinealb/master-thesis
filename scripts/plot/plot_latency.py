#!/usr/bin/env python3
"""
Plots latency from antoinealb's simple raft_latency_measurement format.
"""

import argparse
import struct
import os
import matplotlib.pyplot as plt
import numpy as np

import plottools


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=argparse.FileType('rb'))
    parser.add_argument("--output", "-o")

    return parser.parse_args()

def main():
    args = parse_args()

    file_size = args.input.seek(0, os.SEEK_END)
    args.input.seek(0)

    record_count = file_size // struct.calcsize('l')

    data = args.input.read()
    data = np.array([s for s in struct.unpack('l' * record_count, data) if s < 1e9])
    data = data / 1e6

    print("I have {}k record".format(len(data)//1000))


    latency_tail = np.percentile(data, 99)
    start = np.percentile(data, 1)
    print(latency_tail)
    plt.hist(data, bins=100, range=(start, latency_tail))

    plt.xlabel("Time [ms]")
    plt.title("Median latency {:.3f} ms, 99%: {:.3f} ms".format(np.median(data), latency_tail))

    min_latency = np.percentile(data, 1)
    print("min latency: {:.3} us".format(min_latency * 1000))

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()




if __name__ == '__main__':
    main()
