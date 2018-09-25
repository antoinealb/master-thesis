#!/usr/bin/env python3
"""
Demoes leader election in Raft.
"""

import argparse
import yaml
import raft
import zmq
import random
import time
import threading
import logging


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        "-c",
        help="Path to a config file",
        type=argparse.FileType(),
        required=True)
    parser.add_argument(
        "--verbose",
        "-v",
        help="Show debug output",
        action='store_const',
        const=logging.DEBUG,
        default=logging.INFO
    )

    return parser.parse_args()


def create_server(context, port):
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:{}".format(port))

    return socket


def create_peers_socket(context, ports):
    result = {}
    for peer in ports:
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:{}".format(peer))
        result[peer] = socket

    return result

class RandomizedTimer:
    def __init__(self, interval_min, interval_max, function):
        self.function = function
        self.interval_max = interval_max
        self.interval_min = interval_min
        self.timer = threading.Timer

    def _random_time(self):
        return random.random() * (self.interval_max - self.interval_min) + self.interval_min

    def start(self):
        self.timer = threading.Timer(self._random_time(), self.function)
        self.timer.start()

    def reset(self):
        self.timer.cancel()
        self.start()

class ZMQWrapper:
    def __init__(self, socket):
        self.socket = socket
        self.socket.setsockopt(zmq.RCVTIMEO, 50)

    def request(self, request):
        try:
            self.socket.send_pyobj(request)
            return self.socket.recv_pyobj()
        except zmq.ZMQError:
            pass

def main():
    args = parse_args()
    logging.basicConfig(level=args.verbose)

    config = yaml.load(args.config)
    context = zmq.Context()

    server_socket = create_server(context, config['port'])
    peer_sockets = create_peers_socket(context, config['peers'])

    state = raft.RaftState()
    state.lock = threading.Lock()

    # TODO: Peers
    state.peers = [ZMQWrapper(s) for s in peer_sockets.values()]

    def election_timer_timeout():
        with state.lock:
            state.start_election()
            state.election_timeout_timer.reset()

    def heartbeat_timeout():
        with state.lock:
            state.hearbeat_timer_fired()
            timer = threading.Timer(0.1, heartbeat_timeout)
            timer.start()

    election_timer = RandomizedTimer(2, 10, election_timer_timeout)
    state.election_timeout_timer = election_timer
    election_timer.start()

    hb_timer = threading.Timer(0.1, heartbeat_timeout)
    hb_timer.start()

    while True:
        request = server_socket.recv_pyobj()
        with state.lock:
            reply = state.process(request)
            server_socket.send_pyobj(reply)


if __name__ == '__main__':
    main()
