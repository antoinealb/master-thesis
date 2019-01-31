#!/usr/bin/env python3
"""
Plot latency results from Lancent
"""

import argparse
import lancet
import plottools
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, FuncFormatter

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", "-d",  type=argparse.FileType(), help='Results from Lancets stdout', action='append')
    parser.add_argument("--legend", "-l", action='append', help='Legend, one per data file')
    parser.add_argument("--output", "-o", help='Name of the output figure filename')
    parser.add_argument("--ymax", "-y", help='Max latency on Y coordinate.', default=200, type=int)
    parser.add_argument("--marker", "-m", action='append', help='Matplotlib marker, e.g.: v--')

    return parser.parse_args()

def plot_file(f, markers):
    data = f.read()
    data = lancet.parse_results(data)

    x = [p.rate // 1000 for p in data]
    y = [p.latency_percentiles[99] for p in data]

    plt.plot(x, y, markers)

def main():
    args = parse_args()

    for f, marker in zip(args.data, args.marker):
        plot_file(f, marker)

    plt.xlabel('Throughput (1000 of requests per second)')
    plt.ylabel(r'Latency (99th percentile)')
    plt.ylim(0, args.ymax)
    plt.grid()

    # Set units on Y axis
    plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%d $\mu$s'))

    # Set thousands separator on X axis
    fmt = FuncFormatter(lambda x, loc: "{:,}".format(int(x)))
    plt.gca().xaxis.set_major_formatter(fmt)

    plt.tight_layout()

    if args.legend:
        plt.legend(args.legend, loc='upper left')

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()


if __name__ == '__main__':
    main()
