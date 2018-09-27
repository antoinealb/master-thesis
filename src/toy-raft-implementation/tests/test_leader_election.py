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

    def test_does_not_vote_for_a_candidate_with_shorter_log(self):
        """
        In order to not loose state machine command, Raft uses the voting
        process to prevent a candidate from winning an election if it does not
        contain all the committed entries. To implement this behaviour, nodes
        must refuse to vote for candidates with smaller logs as themselves.

        See section 5.4.1 of the raft paper for details
        """
        state = RaftState()
        state.log = [LogEntry(term=1, index=1, command=None)]
        request = VoteRequest(term=20, candidate=3, lastLogIndex=0, lastLogTerm=1)
        reply = state.process(request)
        self.assertFalse(reply.voteGranted)

    def test_does_not_vote_for_a_candidate_with_an_older_log(self):
        """
        In order to implement section 5.4.1 nodes must also refuse candidates
        who have a smaller term in the last item of their log.
        """
        state = RaftState()
        state.log = [LogEntry(term=2, index=1, command=None)]
        request = VoteRequest(term=20, candidate=3, lastLogIndex=1, lastLogTerm=1)
        reply = state.process(request)
        self.assertFalse(reply.voteGranted)


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
        state = RaftState(id=42, peers=[Mock(), Mock()])
        state.start_election()

        request = VoteRequest(term=1, candidate=42, lastLogIndex=0, lastLogTerm=0)

        state.peers[0].request.assert_any_call(request)
        state.peers[1].request.assert_any_call(request)

    def test_do_not_cast_votes_if_already_leader(self):
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers)
        state.state = NodeState.LEADER
        state.start_election()

        for p in state.peers:
            p.request.assert_not_called()

    def test_is_elected_if_majority(self):
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers)

        state.start_election()
        state.process(VoteReply(term=1, voteGranted=True, fromId=12))
        state.process(VoteReply(term=1, voteGranted=True, fromId=13))

        self.assertEqual(state.state, NodeState.LEADER)

    def test_restart_voting_process(self):
        """
        Checks that restarting the election process truly restarts the vote count.
        """
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers)

        state.start_election()
        state.process(VoteReply(term=1, voteGranted=True, fromId=12))

        state.start_election()
        state.process(VoteReply(term=1, voteGranted=True, fromId=13))

        self.assertEqual(state.state, NodeState.CANDIDATE)

    def test_denied_votes_are_not_counted(self):
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers)

        state.start_election()
        state.process(VoteReply(term=1, voteGranted=True, fromId=12))
        state.process(VoteReply(term=1, voteGranted=False, fromId=13))
        self.assertEqual(state.state, NodeState.CANDIDATE)

    def test_not_elected_if_majority_is_not_reached(self):
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers)
        state.start_election()
        state.process(VoteReply(term=1, voteGranted=True, fromId=12))
        self.assertEqual(state.state, NodeState.CANDIDATE)

    def test_timeouts_are_ignored(self):
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers)
        for p in state.peers:
            p.request.return_value = None
        state.start_election()
        self.assertEqual(state.state, NodeState.CANDIDATE)

    def test_includes_log_index_and_term_in_election_request(self):
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers, id=42)
        state.log = [LogEntry(index=10, term=5, command=None)]
        state.currentTerm = 6
        state.start_election()

        request = VoteRequest(term=7, candidate=42, lastLogIndex=10, lastLogTerm=5)
        state.peers[0].request.assert_any_call(request)



class HeartBeatReception(unittest.TestCase):
    def test_can_process_heartbeat(self):
        state = RaftState()
        state.election_timeout_timer = Mock()
        hb = AppendEntriesRequest(term=1, prevLogIndex=0, prevLogTerm=0, entries=[], leaderCommit=0)
        state.process(hb)

        state.election_timeout_timer.reset.assert_any_call()

class HeartbeatEmission(unittest.TestCase):
    def test_leader_sends_heartbeats(self):
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers)
        state.become_leader()

        state.state = NodeState.LEADER
        state.hearbeat_timer_fired()

        request = AppendEntriesRequest(term=0, prevLogIndex=0, prevLogTerm=0, entries=[], leaderCommit=0)
        for p in state.peers:
            p.request.assert_any_call(request)

    def test_followers_do_not_send_heartbeat(self):
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers)
        state.state = NodeState.FOLLOWER

        state.hearbeat_timer_fired()
        for p in state.peers:
            p.request.assert_not_called()
