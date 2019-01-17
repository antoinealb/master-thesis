#!/usr/bin/env python3
"""
Plot latency results from Lancent
"""

import argparse
import lancet
import plottools
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", "-d",  type=argparse.FileType(), help='Results from Lancets stdout', action='append')
    parser.add_argument("--legend", "-l", action='append', help='Legend, one per data file')
    parser.add_argument("--output", "-o", help='Name of the output figure filename')

    return parser.parse_args()

def plot_file(f, markers):
    data = f.read()
    data = lancet.parse_results(data)

    x = [p.rate for p in data]
    y = [p.latency_percentiles[99] for p in data]

    plt.plot(x, y, markers)

def main():
    args = parse_args()

    markers = ['x-', 'o-', 'v-']

    for f, marker in zip(args.data, markers):
        plot_file(f, marker)

    plt.xlabel('Load (Request per second)')
    plt.ylabel(r'Latency ($\mu$s)')
    plt.ylim(0, 200)
    plt.grid()

    plt.legend(args.legend)

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()


if __name__ == '__main__':
    main()
