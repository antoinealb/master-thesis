import unittest
import collections

class RaftState:
    currentTerm = 0
    votedFor = None

    def process(self, request):
        # TODO: deny vote if log is not at least as up to date
        voteGranted  = False
        if request.term > self.currentTerm:
            self.currentTerm = request.term
            self.votedFor = request.candidate
            voteGranted = True
        elif request.term == self.currentTerm and request.candidate == self.votedFor:
            voteGranted = True

        return VoteReply(self.currentTerm, voteGranted)

VoteRequest = collections.namedtuple('VoteRequest', ['term', 'candidate', 'lastLogIndex', 'lastLogTerm'])
VoteReply = collections.namedtuple('VoteReply', ['term', 'voteGranted'])


class RequestVoteTestCase(unittest.TestCase):
    def test_correct_vote(self):
        state = RaftState()
        request = VoteRequest(term=1, candidate=3, lastLogIndex=4, lastLogTerm=0)
        msg = state.process(request)

        self.assertIsInstance(msg, VoteReply)
        self.assertTrue(msg.voteGranted)
        self.assertEqual(msg.term, 1)

    def test_does_not_vote_for_candidate_with_older_term(self):
        state = RaftState()
        state.currentTerm = 12
        request = VoteRequest(term=1, candidate=3, lastLogIndex=4, lastLogTerm=0)
        msg = state.process(request)

        self.assertIsInstance(msg, VoteReply)
        self.assertFalse(msg.voteGranted)

    def test_updates_current_term_after_voting(self):
        state = RaftState()
        state.currentTerm = 12

        request = VoteRequest(term=20, candidate=3, lastLogIndex=4, lastLogTerm=0)
        msg = state.process(request)

        self.assertEqual(state.currentTerm, 20)

    def test_does_vote_again_for_same_candidate(self):
        state = RaftState()
        request = VoteRequest(term=20, candidate=3, lastLogIndex=4, lastLogTerm=0)

        reply1 = state.process(request)
        reply2 = state.process(request)


        self.assertTrue(reply1.voteGranted)
        self.assertTrue(reply2.voteGranted)
