#!/usr/bin/env python3
"""
Tries to do a certain number of writes to the replicated datastore, measuring
the time.
"""

import argparse
import timeit
import time
from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError



def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", help="number of write, default 1k", type=int,
                        default=1000)
    parser.add_argument("--host", help="ZooKeeper host:port, defaults to localhost", default='127.0.0.1:2181')

    return parser.parse_args()

def main():
    args = parse_args()
    zk = KazooClient(hosts=args.host)
    zk.start()

    try:
        zk.create("/bench", b'12')
    except NodeExistsError:
        pass

    start = time.time()
    for i in range(args.n):
        zk.set("/bench", b"foo")
    stop = time.time()

    duration = stop - start

    print("Took {:.3f} seconds to do {:d} writes.".format(duration, args.n))
    print("Thats {:.1f} writes per second.".format(args.n / duration))



if __name__ == '__main__':
    main()
