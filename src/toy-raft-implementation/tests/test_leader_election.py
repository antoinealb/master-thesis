import unittest
from raft import *
from unittest.mock import Mock


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

class ElectionLogic(unittest.TestCase):
    def test_state_starts_at_follower(self):
        state = RaftState()
        self.assertEqual(state.state, NodeState.FOLLOWER)

    def test_starting_election_transitions_into_candidate(self):
        state = RaftState()
        state.start_election()
        self.assertEqual(state.state, NodeState.CANDIDATE)

    def test_starting_election_increments_current_term(self):
        state = RaftState()
        state.currentTerm = 10
        state.start_election()
        self.assertEqual(state.currentTerm, 11)

    def test_election_votes_are_cast(self):
        state = RaftState()
        state.peers = [Mock(), Mock()]
        state.start_election()

        request = VoteRequest(term=1, candidate=42, lastLogIndex=0, lastLogTerm=0)

        state.peers[0].request.assert_any_call(request)
        state.peers[1].request.assert_any_call(request)

    def test_do_not_cast_votes_if_already_leader(self):
        state = RaftState()
        state.state = NodeState.LEADER
        state.peers = [Mock(), Mock()]
        state.start_election()

        for p in state.peers:
            p.request.assert_not_called()

    def test_is_elected_if_majority(self):
        state = RaftState()
        state.peers = [Mock(), Mock()]

        # TODO: what happens if a message gets duplicated ?
        for p in state.peers:
            p.request.return_value = VoteReply(term = 1, voteGranted=True)

        state.start_election()

        self.assertEqual(state.state, NodeState.LEADER)

    def test_timeouts_are_ignored(self):
        state = RaftState()
        state.peers = [Mock(), Mock()]
        for p in state.peers:
            p.request.return_value = None
        state.start_election()
        self.assertEqual(state.state, NodeState.CANDIDATE)


class HeartBeatReception(unittest.TestCase):
    def test_can_process_heartbeat(self):
        state = RaftState()
        state.election_timeout_timer = Mock()
        hb = Heartbeat(term=1)
        state.process(hb)

        state.election_timeout_timer.reset.assert_any_call()

class HeartbeatEmission(unittest.TestCase):
    def test_leader_sends_heartbeats(self):
        state = RaftState()
        state.peers = [Mock(), Mock()]

        state.state = NodeState.LEADER
        state.hearbeat_timer_fired()

        request = Heartbeat(term=0)
        for p in state.peers:
            p.request.assert_any_call(request)

    def test_followers_do_not_send_heartbeat(self):
        state = RaftState()
        state.peers = [Mock(), Mock()]
        state.state = NodeState.FOLLOWER

        state.hearbeat_timer_fired()
        for p in state.peers:
            p.request.assert_not_called()
