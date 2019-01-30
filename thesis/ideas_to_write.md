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
- Performance

* kernel bypass for fast replicated RPC
* Replicating Remote Procedure Calls at the Transport Layer
* Bringing Distributed Consensus to the Transport Layer
* Fast, Replicated Remote Procedure Calls
* Adding some consensus in your transport protocol
* Fast, Replicated RPCs using Kernel Bypass
* Getting there, faster: Distributed Consensus and Kernel Bypassing
* REPLICATED_ROUTE: Distributed Consensus at the Transport Layer
* R3P2: Replicated Request-Response Pair Protocol

## Feedback from marios

1. [done] Add consensus somehow in the title
2. Add an abstract
    Write it at the end
3. [done] The intro should be longer and serve as an overview of what is coming next. Mention r2p2, mention some killer numbers from the eval etc.
    Should really be high level overview, can be a repetition from a detailed stuff later.
4. [done] Design: Consider adding a table with the necessary message types or policies that you added. They are in the text but it would be clearer if they are in a table too.
    Add the encoding as well (no need for byte level or stuff like that).
5. [done] I think you need a state machine that combines the r2p2 server state machine with what you added for consensus. For example, what happens with multi-packet requests?
    Just mention that arrwos in Figure 3.2 (lifecycle) are complete R2P2 messages, which means in multi datagrams we wait for a request to be complete before replicating it.
6. [done] Remove Rust from the implementation section. I expect the section to be a bit longer as well. Mention lines of code added, where you added that code etc.
7. Add a related work section. I can send you a few papers that you can cite as well.
8. [done] In the implementation as well, add a "layers" view from DPDK all the way to the application.
    Put it at the beginning of the implementation chapter.

possible structure for related work:

* Kernel Bypass, papers that use that
* How do people use consensus?

Take that from bibliography.
Compare my work to other people's.

to add: appendix with how to run my code
