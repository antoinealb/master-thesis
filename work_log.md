# Week 1 (September 24th-30th)

Started reading on the problem of distributed consensus:

- Kernel Paxos: Paper that presents a new approach to speed up consensus (Paxos specifically).
    They are not proposing a new algorithm that takes domain knowledge into account like some Paxos variant.
    Rather it focuses on speeding up the consensus itself by lowering RPC latency.
    In order to do so they implemented Paxos as a kernel module, which cuts kernel <-> userland cost.
    This can run on hardware, contrasting with other who implemented Paxos on dedicated hardware.
    __This is probably the benchmark to beat.__
- ZooKeeper: Paper presenting a distributed database.
    Better performance than Paxos based systems (like Chubby) but relaxed consistency guarantees (reads are served locally -> stale reads can occur).
    One of the most widely used consistency server, but fully userland + java -> should be possible to beat.
    The have an interesting benchmarking suite available.
- In search of understandable consensus:
    Introduces Raft, a new consensus protocol which offers similar functionality as Paxos.
    However, was made with understandability and ease of implementation in mind.
    More recent than paxos (2015 vs 1980s).
    Was used in industry (kubernete's etcd for example, TiKV for another example).
    For now, I think it might be a good idea to use this rather than Paxos for our candidate system.
    Note: Raft has good implementations in both Rust and Go.
- The Chubby lock service for loosely-coupled distributed systems:
    Old (2006) paper about how google used Paxos to build a distributed lock service with basic data storage capabilities.
    Based on Paxos but uses a modified (slower) version of the protocol.
    Performance number might be hard to use as is, but the ZooKeeper paper compares ZK's performance with Chubby, allowing us to compare our implementation with ZK and then to Chubby itself.

From the coding point of view, I started looking at DPDK's documentation.
I did not write any DPDK code yet, as it seem quite hard to get started.
I also looked at the Rust bindings and most seemed outdated, might required doing our own.

I also wrote a simple Raft implementation in Python.
This version implements leader election and log replication.
It does not implement log cleaning and cluster membership.
It is quite small (< 300 lines of Python), which is encouraging; I might build my own Raft implementation if need be.

Looking at consensus protocol implementations by myself, it appears that there is a good amount of existing libraries.
Interesting ones I saw:

- LibPaxos (the one used in Kernel Paxos), in C
- TiKV, implemented in Rust
- etcd's Raft, unfortunately in go, which makes interop with Rust hard.

An interesting tool I stumbled upon is [Jepsen](https://jepsen.io) which is a framework used to test the consistency of distributed systems.
Maybe it is worth it to use it on our end code to see if there is any issue.

# Week 2 (October 1st-7th)

Not in the lab, attended IROS

# Week 3 (October 8th-14th)

Worked on ZooKeeper.
Brushed up on Rust.
Did not do much because of injury.

# Week 4 (October 15th-21st)

* Got a working ZK cluster
* Still trying to get kernel paxos to work.
    Apparently each machine can only have one role in the Paxos protocol (Learner, Proposer xor Acceptor).
    I think I need to read more on how Paxos works in order to understand this better.

# Week 5 (October 22nd-28th)

- Paxos Made Live - An Engineering Perspective (2006)
    Experience of a group of Googlers deploying Paxos to build a fault tolerant database.
    Mixes algorithmic concerns (how to agree on a stream of value rather than a single one?) with practical considerations (how do you handle hard drive failures?).
    For me it appears that a lot of Paxos' problems are solved by raft (snapshotting, Multi Paxos, cluster membership).
    Presents an interesting primitive called MultiOp for implementation of more complex atomic operations.
    Another interesting remark is the fact that they developped a special language to describe state machines and reason about them.
    Might be doable with Rust?
    Finally, the paper provides some performance measurements, but on very (12 years) old hardware, so it might be hard to make it relevant.
- Spanner, TrueTime and the CAP Theorem (2017)
    Whitepaper showing why it is possible to have systems that are CA in practice.
    Basically the assumption is that most of the time partition tolerance does not matter, and that you only have to choose between C and A during one of those partitions.
    Google explored the history of failures of the Spanner and Chubby services and arrived at the conclusion that network partitions are extremely rare.
    Therefore they designed their system to operate in a globally CA way, while falling down to CP if needed.
    TrueTime is a clock synchronization service that they use as an optimization in some cases.
