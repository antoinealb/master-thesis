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

        result =  VoteReply(self.currentTerm, voteGranted)
        logging.debug('Voting reply: %s', result)

        return result


    def _process_heartbeat(self, request):
        logging.debug('Got a heartbeat')
        self.election_timeout_timer.reset()

    def start_election(self):
        if self.state == NodeState.LEADER:
            return

        logging.info('Starting election proces...')
        self.state = NodeState.CANDIDATE
        self.currentTerm += 1

        request = VoteRequest(self.currentTerm, self.id, lastLogIndex=0, lastLogTerm=0)

        votes = 0

        logging.info('Casting votes')
        for p in self.peers:
            reply = p.request(request)

            if not reply:
                continue

            if reply.voteGranted:
                votes += 1

        if len(self.peers) < 2 * votes:
            logging.info('Became leader')
            self.state = NodeState.LEADER

    def hearbeat_timer_fired(self):
        if self.state != NodeState.LEADER:
            return

        logging.debug('Sending heartbeat')
        request = Heartbeat(term=self.currentTerm)
        for p in self.peers:
            p.request(request)


VoteRequest = collections.namedtuple('VoteRequest', ['term', 'candidate', 'lastLogIndex', 'lastLogTerm'])
VoteReply = collections.namedtuple('VoteReply', ['term', 'voteGranted'])
Heartbeat = collections.namedtuple('Heartbeat', ['term'])

