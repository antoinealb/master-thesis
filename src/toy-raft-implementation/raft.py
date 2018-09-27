from collections import namedtuple
import logging
from enum import Enum

class NodeState(Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3

class RaftState:
    currentTerm = 0
    votedFor = None
    state = NodeState.FOLLOWER
    def __init__(self, id=0, peers=None, logger=None):
        self.id = id
        self.peers = peers or []
        self.logger = logger or logging.getLogger('RaftState')

    def process(self, msg):
        processors = {
            VoteRequest: self._process_vote_request,
            VoteReply: self._process_vote_reply,
            Heartbeat: self._process_heartbeat
        }

        for t, processor in processors.items():
            if isinstance(msg, t):
                return processor(msg)

    def _process_vote_request(self, request):
        self.logger.debug('Got a voting request')
        # TODO: deny vote if log is not at least as up to date
        voteGranted = False
        if request.term > self.currentTerm:
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
                self.logger.info('became leader')
                self.state = NodeState.LEADER
        elif reply.term > self.currentTerm:
            self.currentTerm = reply.term

    def _process_heartbeat(self, request):
        self.logger.debug('Got a heartbeat')
        self.election_timeout_timer.reset()

    def start_election(self):
        self.votes = set()
        if self.state == NodeState.LEADER:
            return

        self.logger.info('starting election process...')
        self.votedFor = self.id
        self.state = NodeState.CANDIDATE
        self.currentTerm += 1

        request = VoteRequest(
            self.currentTerm, self.id, lastLogIndex=0, lastLogTerm=0)

        votes = 0

        for p in self.peers:
            p.request(request)

    def hearbeat_timer_fired(self):
        if self.state != NodeState.LEADER:
            return

        self.logger.debug('sending heartbeat')
        request = Heartbeat(term=self.currentTerm)
        for p in self.peers:
            p.request(request)


VoteRequest = namedtuple('VoteRequest',
                         ['term', 'candidate', 'lastLogIndex', 'lastLogTerm'])
VoteReply = namedtuple('VoteReply', ['term', 'voteGranted', 'fromId'])
LogEntry = namedtuple('LogEntry', ['term', 'index', 'command'])
AppendEntriesRequest = namedtuple(
    'AppendEntriesRequest',
    ['term', 'prevLogIndex', 'prevLogTerm', 'entries', 'leaderCommit'])
AppendEntriesReply = namedtuple('AppendEntriesReply',
                                ['success', 'fromId', 'lastIndex'])
