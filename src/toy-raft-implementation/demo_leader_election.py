#!/usr/bin/env python3
"""
Demoes leader election in Raft.
"""

import argparse
import yaml
import raft
import socket
import random
import time
import threading
import logging
import pickle
from termcolor import cprint


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
        default=logging.INFO)

    return parser.parse_args()


def create_server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', port))

    return s


def create_peers_socket(ports):
    result = {}
    for peer in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        result[peer] = s

    return result

def interact(state):
    while True:
        s = input()
        with state.lock:
            state.replicate(s)


class RandomizedTimer:
    def __init__(self, interval_min, interval_max, function):
        self.function = function
        self.interval_max = interval_max
        self.interval_min = interval_min
        self.timer = threading.Timer

    def _random_time(self):
        interval_width =  self.interval_max - self.interval_min
        return random.random() * interval_width + self.interval_min

    def start(self):
        self.timer = threading.Timer(self._random_time(), self.function)
        self.timer.start()

    def reset(self):
        self.timer.cancel()
        self.start()


class UDPPickleTransport:
    def __init__(self, socket, src, port):
        self.socket = socket
        self.port = port
        self.src = src
        self.id = port

    def request(self, request):
        logging.debug('Sending %s to %s', request, self.port)
        request = pickle._dumps((self.src, request))
        self.socket.sendto(request, ('localhost', self.port))

    def __str__(self):
        return "UDPPickleTransport(peer={})".format(self.id)


def main():
    args = parse_args()
    logging.basicConfig(level=args.verbose)

    config = yaml.load(args.config)

    server_socket = create_server(config['port'])
    peer_sockets = create_peers_socket(config['peers'])

    peers = [
        UDPPickleTransport(socket, config['port'], port)
        for port, socket in peer_sockets.items()
    ]

    state = raft.RaftState(id=config['port'], peers=peers)
    state.lock = threading.Lock()


    def election_timer_timeout():
        with state.lock:
            state.start_election()
            state.election_timeout_timer.reset()

    def heartbeat_timeout():
        with state.lock:
            state.hearbeat_timer_fired()
            timer = threading.Timer(0.1, heartbeat_timeout)
            timer.start()

    election_timer = RandomizedTimer(1, 5, election_timer_timeout)
    state.election_timeout_timer = election_timer
    election_timer.start()

    hb_timer = threading.Timer(0.1, heartbeat_timeout)
    hb_timer.start()

    was_leader = False

    while True:
        request, addr = server_socket.recvfrom(1024)
        port, request = pickle.loads(request)
        logging.debug('Received %s from %s', request, port)
        with state.lock:
            reply = state.process(request)

            if state.state == raft.NodeState.LEADER and not was_leader:
                state.replicate(state.id)
                was_leader = True
                threading.Thread(target=interact, args=(state, )).start()


        print("{}: {}".format(state.id, state.commitIndex), end='')
        cprint(",".join(str(s.command) for s in state.log if s.index <= state.commitIndex), "green", end='')
        cprint(",".join(str(s.command) for s in state.log if s.index > state.commitIndex), "yellow")

        if reply:
            reply = pickle.dumps((state.id, reply))
            server_socket.sendto(reply, ('localhost', port))


if __name__ == '__main__':
    main()
