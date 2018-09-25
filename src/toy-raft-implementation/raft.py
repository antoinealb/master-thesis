import collections
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
    peers = []
    id = 42
    logger = logging.getLogger('RaftState')

    def process(self, request):
        if isinstance(request, VoteRequest):
            return self._process_vote_request(request)
        elif isinstance(request, VoteReply):
            return self._process_vote_reply(request)
        elif isinstance(request, Heartbeat):
            return self._process_heartbeat(request)

    def _process_vote_request(self, request):
        logging.debug('Got a voting request')
        # TODO: deny vote if log is not at least as up to date
        voteGranted  = False
        if request.term > self.currentTerm:
            self.currentTerm = request.term
            self.votedFor = request.candidate
            voteGranted = True
        elif request.term == self.currentTerm and request.candidate == self.votedFor:
            voteGranted = True

        # TODO: Real ID
        result =  VoteReply(self.currentTerm, voteGranted, self.id)
        logging.debug('Voting reply: %s', result)

        return result

    def _process_vote_reply(self, reply):
        if reply.voteGranted:
            logging.debug('Got a vote for ourselves')
            self.votes.add(reply)
            if 2 * len(self.votes) > len(self.peers):
                logging.info('became leader')
                self.state = NodeState.LEADER
        elif reply.term > self.currentTerm:
            self.currentTerm = reply.term

    def _process_heartbeat(self, request):
        logging.debug('Got a heartbeat')
        self.election_timeout_timer.reset()

    def start_election(self):
        self.votes = set()
        if self.state == NodeState.LEADER:
            return

        logging.info('Starting election proces...')
        self.state = NodeState.CANDIDATE
        self.currentTerm += 1

        request = VoteRequest(self.currentTerm, self.id, lastLogIndex=0, lastLogTerm=0)

        votes = 0

        logging.info('Casting votes')
        for p in self.peers:
            p.request(request)

    def hearbeat_timer_fired(self):
        if self.state != NodeState.LEADER:
            return

        logging.debug('Sending heartbeat')
        request = Heartbeat(term=self.currentTerm)
        for p in self.peers:
            p.request(request)


VoteRequest = collections.namedtuple('VoteRequest', ['term', 'candidate', 'lastLogIndex', 'lastLogTerm'])
VoteReply = collections.namedtuple('VoteReply', ['term', 'voteGranted', 'fromId'])
Heartbeat = collections.namedtuple('Heartbeat', ['term'])

