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

To make DPDK work on real NIC, you need to remove the `--vdev '...'` option from above command.
Make sure that the NIC is correctly bound to DPDK via the setup script.
You can now run `set fwd icmp_echo` and `start` commands.
DPDK should now answer to pings (`ping 10.0.100.2` in the VM).

To run NetBricks on pcap do the following (`--dur 5` means it will exit after 5 seconds).

```
./build.sh run macswap -p dpdk:eth_pcap0,rx_pcap=/src/test.pcap,tx_pcap=/src/out.pcap -c 1 --dur 5
```

# Week 8 (November 12th - November 18th)

Protocol used by the KV store:

```
???\r\n
???\r\n
{get|set}\r\n
???\r\n
key\r\n
value
```

I spent the beginning of this week trying to get Ogiers thesis to work.
It appears to have strange bugs with regards to memory management.
If I comment out the freeing of mbufs, it works fine.
Some notes in Ogier's thesis let me to believe he was aware of it.

We discussed this with Marios and we both agree that switching to C might be easier.
A few weeks ago I started working on a raft implementation in C++, I spent a few days finishing it this week.
It is currently capable of leader election and log replication.
Its architecture is event driven, meaning it should be relatively easy to add to the r2p2 protocol.

One big question remains: how do we introduce the notion of time?
Indeed, Raft requires a way to know that timeout elapsed to be able to send heartbeat and start elections.
This does not play well with DPDK's model of polling the NIC; I will have to find something.
However in the meantime I think I can get it to work using a new type of packets for ticks, and an external service that sends ticks.
Not very clean architecture.
Another option would be to have a thread dedicated to running timers, but I am not sure how well this would work.

Another important remaining question is log compaction.
In "normal" raft applications there is a mechanism to prevent the replicated log to grow indefinitely.
Basically the idea is to snapshot the replicated FSM from time to time and to replace the log up to point N with a snapshot taken at point N.
However, since we are using raft as a transport protocol and we do not know anything about the machine running on top (especially we don't know what a meaningful snapshot could be), this technique cannot be used!
This means the log can grow indefinitely; quite problematic.
In practice a first version can simply assume the log never gets too big, but we would have to find something for the longer term.
An idea that I had was that we could simply assume that once an entry is commited on everyone, we would discard it from the log.
This has the following issues:

- What if a node stays down?
    Then we will never be able to discard entries past its last commit.
- What if a node dies then goes back online?
    This means the application has to presist the replicated log / snapshots itself somehow.
    Which might be slow if implemented in a dumb way.

But just how big would that replicated log be in our experiment?
Kernel paxos cites figures between 30k to 100k messages per second.
Each log entry would be around 64 bytes, the size of a small r2p2 request.
This means our log is growing at about 6.4 MB/s.
It is too much for a long running application but appears to be OK for "small" experiments: 1 min would be around 400 MB of log.

# Week 9 (November 19th - November 25th)

Wrote a new backend for r2p2 based on libuv.
It allows me to write my code and test it on OSX/Windows/Linux using the correct backend everytime (kqueues, epoll, and whatever it is on Windows).
I need to finish some memory management code for it, but then I am confident it can be a nice addition to r2p2.
Plus, it only took me a day or so to implement, libuv is quite easier than the underlying syscalls.
Maybe it can replace the linux backend ?

I started integrating raft in r2p2, so far the only modification of the platform code was the addition of a periodic timer.
This is needed to handle the various timeouts used by Raft.
However I am not sure how this can be done in DPDK, it is only implemented in the libuv backend so far.
As of wednesday leader election is working using a very hacky transport (basically dumping the c++ struct in an R2P2 packet).
I am pretty sure the log replication works (the Raft code for it is tested), I just don't have any R2P2 implementation

On the debugging side I wrote some ScaPy decoders for R2P2 and raft, which are very helpful to debug.

On Thursday I tested that log replication worked.
I also fixed the memory management code for the libuv backend.
So now I have a server implementation that keeps a rast cluster alive and can still respond to normal r2p2 requests.

things left to be done:

1. serialize raft::Message properly
2. add a replicated policy for r2p2 in which requests are appended to the log and sent to the application on commit
    This might be challenging from a memory management point of view.
3. Non leaders should forward requests to the leader.
