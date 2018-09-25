# Toy Raft implementation in Python

This folder contains the source code of a prototype implementation of Raft in Python.
The goal was to get familiar with the algorithm by implementing a simple
version of it. It also allowed me to test the architecture of the code in an
easier language than Rust before moving to a real implementation.

## Leader election demo

`./demo_leader_election.py` implements a simple leader election demo, without replicating any state machine.
The nodes live in separate processes but are expected to all be on the same machine.
Messages are exchanged via UDP.
For working configuration files, see `scripts/toy-raft/config*.yml`.

