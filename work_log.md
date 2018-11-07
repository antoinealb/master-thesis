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
- Tail-Latency-Tolerant Load Balancing of Microsecond-scale RPCs (unpublished yet).
    Paper suggesting a new transport mechanism for RPCs that stay inside a typical datacenter network.
    The atributes of DC-internal networks (with very little packet loss and low latency) allow us to drop TCP in favor of UDP.
    In addition to this, R2P2 implements a queue management system at the protocol level, which allows load balancers to know how many requests are queued at each backend worker.
    This allow the load balance to choose optimal load balancing strategies that minimise latency.
    I will use this paper for the transport protocol of my implementation (without the load balancing part).
    It seems pretty easy to implement a small client for it, if needed and there is a previous master thesis discussing it.

# Week 6 (October 29th-November 4th)

- Netbricks: Taking the V out of NFV (2016).
    This paper proposes a novel way to implement network functions such as routing and load balancing on commodity hardware.
    Previous work in this area used heavyweight isolation mechanism such as process boundaries, containers or VM.
    This work presents a new way to do it using the Rust programming language and static checking of safety properties.
    It also exposes interesting bindings for DPDK on Rust.
    Unfortunately for me, the project appears to not be maintained anymore.


## Notes on setting up DPDK
tested on Ubuntu 18.04 (bionic) with Linux 4.15 running in Virtualbox.
The setup has two emulated NICs ([qemu e1000 / Intel 82540](https://doc.dpdk.org/guides-16.07/nics/e1000em.html)).
The one used for DPDK is on a host only network and initially has IP 10.0.100.2/24.

`dpdk_setup.sh` seems to work:
    - select x86_64-native-linuxapp-gcc
    - insert IGB UIO
    - setup hugepages for non NUMA (make sure to allocate at least 512 MB of memory -> 256 page)
    - ip link set dev enp0s8 down
    - bind the PCI dev to IGB UIO
    - check ethernet status, should be under "network devices using dpdk compatible driver"
    - Run testpmd app, using a core mask of 3 (for both cores).
    - In testpmd app you can run "show port xstats all" to get RX/TX counters.
    - On the host run "ping 10.0.100.2".
        Since no IP stack is running on the DPDK card yet, it will show as unavailable.
        However you should see the counters increasing on testpmd.
        I am not sure how this interacts with ARP, maybe ping it once before giving the card to DPDK.

# Week 7 (November 5th - November 11th)

Working DPDK test command to send into a pcap:

```
sudo ./3rdparty/dpdk/build/app/testpmd -c 3 -n 3 -m 64 --vdev 'net_pcap0,rx_pcap=test.pcap,tx_pcap=out.pcap' -- --mbuf-size=2048 --total-num-mbufs=2048 --port-topology=chained -i --no-flush-rx
```

This week we discussed the feasability of including Raft inside the transport protol.
That means that a new policy would be introduced (replicated).
In this mode the application would get the request callback only when the request has been correctly replicated on all nodes, and that all nodes in the cluster would see it in the same order.
One leftover question is who answers the request; while it is clear that the request must be adressed to the leader, it is not clear if the leader only should respond or if all nodes should respond.
If we make the assumption of very little loss of messages (underlying r2p2 assumption in a DC) and that the leader has little chances of crashing, it makes sense to only send them at the leader.
