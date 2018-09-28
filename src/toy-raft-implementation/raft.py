from collections import namedtuple
import logging
from enum import Enum


class NodeState(Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3


class RaftState:
    def __init__(self, id=0, peers=None, logger=None):
        self.id = id
        self.peers = peers or []
        self.logger = logger or logging.getLogger('RaftState')
        self.log = []
        self.logIndex = 0
        self.state = NodeState.FOLLOWER
        self.votedFor = None
        self.currentTerm = 0
        self.commitIndex = 0

    def process(self, msg):
        processors = {
            VoteRequest: self._process_vote_request,
            VoteReply: self._process_vote_reply,
            AppendEntriesRequest: self._process_append_entries_request,
            AppendEntriesReply: self._process_append_entries_reply,
        }

        for t, processor in processors.items():
            if isinstance(msg, t):
                return processor(msg)

    def _process_vote_request(self, request):
        self.logger.debug('Got a voting request')
        voteGranted = False
        if request.term > self.currentTerm and \
           self._last_log_index() <= request.lastLogIndex and \
           self._last_log_term() <= request.lastLogTerm:
            self.currentTerm = request.term
            self.votedFor = request.candidate
            voteGranted = True
        elif request.term == self.currentTerm and request.candidate == self.votedFor:
            voteGranted = True

        result = VoteReply(self.currentTerm, voteGranted, self.id)
        self.logger.debug('Voting reply: %s', result)

        return result

    def _process_vote_reply(self, reply):
        if self.state != NodeState.CANDIDATE:
            return

        if reply.voteGranted:
            self.logger.debug('Got a vote for ourselves')
            self.votes.add(reply)
            if 2 * len(self.votes) > len(self.peers):
                self.become_leader()
        elif reply.term > self.currentTerm:
            self.currentTerm = reply.term
            self.election_timeout_timer.reset()
            self.state = NodeState.FOLLOWER
            self.votedFor = None
            self.votes = set()

    def _process_append_entries_request(self, request):
        self.logger.debug('Got an append request: %s', request)
        if request.term < self.currentTerm:
            return AppendEntriesReply(
                success=False, lastIndex=None, fromId=self.id)

        try:
            self.election_timeout_timer.reset()
        # TODO: Ugly workaround for tests
        except AttributeError:
            pass

        # Check that we can find the entry described by previouslog
        if request.prevLogTerm > 0 and request.prevLogIndex > 0:
            for entry in self.log:
                if entry.term == request.prevLogTerm and \
                   entry.index == request.prevLogIndex:
                    break
            else:
                return AppendEntriesReply(
                    success=False, lastIndex=None, fromId=self.id)

        # Checks for conflicting entries, which have the same index but not the
        # same term
        for i, entry in enumerate(self.log):
            for new_entry in request.entries:
                if entry.index == new_entry.index and entry.term < new_entry.term:
                    del self.log[i:]
                    break

        self.log = merge_log(self.log, request.entries)

        if request.leaderCommit > self.commitIndex:
            self.commitIndex = min(request.leaderCommit, self._last_log_index())

        return AppendEntriesReply(
            success=True, lastIndex=self._last_log_index(), fromId=self.id)

    def _process_append_entries_reply(self, request):
        self.logger.debug('Got a append entries reply: %s', request)

        peer = next(s for s in self.next_index.keys() if s.id == request.fromId)
        if request.success:
            self.match_index[peer] = request.lastIndex
            self.next_index[peer] = request.lastIndex + 1
        else:
            self.logger.debug("Got a failure from %s, decreasing next_index", peer.id)
            self.next_index[peer] -= 1

        # Update commit index to the lastest index that was replicated on a
        # majority of node.
        n = sorted(self.match_index.values())[len(self.peers) // 2]
        if n > self.commitIndex:
            entry_N = next(e for e in self.log if e.index == n)
            if entry_N.term == self.currentTerm:
                self.commitIndex = n


    def _last_log_index(self):
        try:
            return self.log[-1].index
        except IndexError:
            return 0

    def _last_log_term(self):
        try:
            return self.log[-1].term
        except IndexError:
            return 0

    def start_election(self):
        self.votes = set()
        if self.state == NodeState.LEADER:
            return

        self.logger.info('starting election process...')
        self.votedFor = self.id
        self.state = NodeState.CANDIDATE
        self.currentTerm += 1

        request = VoteRequest(
            self.currentTerm,
            self.id,
            lastLogIndex=self._last_log_index(),
            lastLogTerm=self._last_log_term())

        votes = 0

        for p in self.peers:
            p.request(request)

    def become_leader(self):
        self.logger.info('became leader')
        self.state = NodeState.LEADER
        self.match_index = {p: 0 for p in self.peers}
        max_index = self._last_log_index()
        self.next_index = {p: max_index for p in self.peers}

    def hearbeat_timer_fired(self):
        if self.state != NodeState.LEADER:
            return

        self.logger.debug('sending heartbeat')
        self.logger.debug('next_index = %s', self.next_index)
        for p in self.peers:
            next_index = self.next_index[p]
            prevLogIndex = 0
            prevLogTerm = 0
            entries = []
            for i, entry in enumerate(self.log):
                if entry.index >= next_index:
                    entries = self.log[i:]
                    break
                prevLogIndex = entry.index
                prevLogTerm = entry.term

            request = AppendEntriesRequest(
                term=self.currentTerm,
                prevLogIndex=prevLogIndex,
                prevLogTerm=prevLogTerm,
                entries=entries,
                leaderCommit=self.commitIndex)
            p.request(request)

    def replicate(self, command):
        """
        Appends the given command to the replicated finite state machine.

        The commands can be anything, as long as they can be serialized by the
        chosen transport protocol.
        """
        entry = LogEntry(self.currentTerm, self._last_log_index() + 1, command)
        self.log.append(entry)

        request = AppendEntriesRequest(
            term=self.currentTerm,
            prevLogTerm=0,
            prevLogIndex=0,
            entries=self.log,
            leaderCommit=self.commitIndex)



def merge_log(existing_log, new_entries):
    # Find the last entry in new_entries that is already in the log
    try:
        oldest_index = existing_log[-1].index
    except IndexError:
        oldest_index = 0

    valid_new_entries = []
    for i, entry in enumerate(new_entries):
        if entry.index > oldest_index:
            valid_new_entries.append(entry)

    return existing_log + valid_new_entries


VoteRequest = namedtuple('VoteRequest',
                         ['term', 'candidate', 'lastLogIndex', 'lastLogTerm'])
VoteReply = namedtuple('VoteReply', ['term', 'voteGranted', 'fromId'])
LogEntry = namedtuple('LogEntry', ['term', 'index', 'command'])
AppendEntriesRequest = namedtuple(
    'AppendEntriesRequest',
    ['term', 'prevLogIndex', 'prevLogTerm', 'entries', 'leaderCommit'])
AppendEntriesReply = namedtuple('AppendEntriesReply',
                                ['success', 'fromId', 'lastIndex'])
