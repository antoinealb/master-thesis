* how does raft work ?
* what are our log entries ?
* multi value consensus vs single value

* illustrate log replication

1. intro:
    - motivation (why does consensus matter in dc systems)
    - prob. statement (what if consensus was in the transport instead of the application?)
    - hint of the solution (consensus as part of the transport for rpcs)
    - enumerate contributions (bullet points really)
    - killer numbers (speedups, latency, etc.)
    - skeleton of the thesis
2. background
    - Consensus (basic algorithms, 2n + 1 reliability)
    - Raft specifically
    - Transports (specifically R2P2, incl implementation things)
    - Kernel bypass
3. Design
    - Describe what I wanna do
    - Message types that I introduced for Raft support
    - All messages in a typical consensus interaction (**FIGURE**, maybe **PSEUDOCODE**)
4. Implementation
    - DPDK
    - Client / server code
    - Router that listens to the leader election messages
    - Timers
    - The log
    - Linux userland compat
5. Evaluation
    - describe experiments
    - describe the infra
    - results (one per experiment)
    - comparison with kernel paxos
6. Related work
    - Marios can help with that
7. Future work
    - Rust / Ixy
8. Conclusion

break ideas into paragraphs, with a few keywords per paragraph
then only starts writing

above 30 pages is a reasonable goal

# Title ideas

key themes:

- RPC
- Transport Protocols
- Kernel Bypass
- Consensus

* kernel bypass for fast replicated RPC
* Replicating Remote Procedure Calls at the Transport Layer
* Bringing Distributed Consensus to the Transport Layer
* Fast, Replicated Remote Procedure Calls
* Adding some consensus in your transport protocol
